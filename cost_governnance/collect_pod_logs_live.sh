#!/bin/bash

# Live stream pod logs for a fixed duration.
# Unlike snapshot collection, this script follows logs in real time.

set -u

# Defaults
NAMESPACE="ncm-cg"          # use "all" for all namespaces
LOG_DIR="pod-logs-live"
DURATION="30m"              # stream duration (e.g., 30m, 10m, 1h)
CONTAINER=""                # optional specific container
START_FROM_NOW=true         # if true, stream only from script start time

while getopts "n:l:d:c:Sh" opt; do
    case "$opt" in
        n) NAMESPACE="$OPTARG" ;;
        l) LOG_DIR="$OPTARG" ;;
        d) DURATION="$OPTARG" ;;
        c) CONTAINER="$OPTARG" ;;
        S) START_FROM_NOW=false ;; # include existing logs + follow
        h)
            echo "Usage: $0 [-n namespace] [-l log_dir] [-d duration] [-c container] [-S]"
            echo "  -n  Namespace (default: ncm-cg, use 'all' for all namespaces)"
            echo "  -l  Output directory prefix (default: pod-logs-live)"
            echo "  -d  Live stream duration (default: 30m; examples: 10m, 1h)"
            echo "  -c  Specific container name (default: all containers)"
            echo "  -S  Include existing logs before streaming (no since-time filter)"
            echo "  -h  Show help"
            echo ""
            echo "Examples:"
            echo "  $0 -n ncm-cg -d 30m"
            echo "  $0 -n all -d 20m"
            echo "  $0 -n nc-system -c iam-proxy -d 45m"
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${BLUE}[SUCCESS]${NC} $1"; }

if ! command -v kubectl >/dev/null 2>&1; then
    log_error "kubectl not found. Please install kubectl."
    exit 1
fi

if ! command -v timeout >/dev/null 2>&1; then
    log_error "'timeout' command not found. Install coreutils."
    exit 1
fi

ALL_NAMESPACES=false
if [ "$NAMESPACE" = "all" ] || [ "$NAMESPACE" = "ALL" ]; then
    ALL_NAMESPACES=true
    log_info "Streaming logs from ALL namespaces"
else
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log_error "Namespace '$NAMESPACE' does not exist."
        exit 1
    fi
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_DIR="${LOG_DIR}_${TIMESTAMP}"
mkdir -p "$RUN_DIR"

# Use UTC RFC3339 for kubectl --since-time
STREAM_START_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ "$ALL_NAMESPACES" = true ]; then
    POD_DATA=$(kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{"\n"}{end}')
else
    POD_DATA=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')
fi

if [ -z "$POD_DATA" ]; then
    log_error "No pods found."
    exit 1
fi

POD_COUNT=$(echo "$POD_DATA" | sed '/^$/d' | wc -l | tr -d '[:space:]')
log_info "Output directory: $RUN_DIR"
log_info "Pods to stream: $POD_COUNT"
log_info "Duration: $DURATION"
if [ "$START_FROM_NOW" = true ]; then
    log_info "Mode: live-only (since-time=$STREAM_START_UTC)"
else
    log_info "Mode: include existing logs + live follow"
fi
echo ""

declare -a PID_LIST=()
declare -a NAME_LIST=()
STARTED=0
FAILED_START=0

for pod_entry in $POD_DATA; do
    if [ "$ALL_NAMESPACES" = true ]; then
        POD_NS="${pod_entry%%/*}"
        POD_NAME="${pod_entry#*/}"
    else
        POD_NS="$NAMESPACE"
        POD_NAME="$pod_entry"
    fi

    [ -z "$POD_NAME" ] && continue

    if ! kubectl get pod -n "$POD_NS" "$POD_NAME" >/dev/null 2>&1; then
        log_warn "Pod not found (probably restarted): $POD_NS/$POD_NAME"
        FAILED_START=$((FAILED_START + 1))
        continue
    fi

    mkdir -p "$RUN_DIR/$POD_NS"
    LOG_FILE="$RUN_DIR/$POD_NS/${POD_NAME}.log"

    {
        echo "========================================"
        echo "Pod: $POD_NAME"
        echo "Namespace: $POD_NS"
        echo "Started at: $(date)"
        echo "Stream duration: $DURATION"
        echo "Start-from-now: $START_FROM_NOW"
        echo "========================================"
        echo ""
    } > "$LOG_FILE"

    KFLAGS=(logs -f -n "$POD_NS" "$POD_NAME" --timestamps=true)
    if [ -n "$CONTAINER" ]; then
        KFLAGS+=(-c "$CONTAINER")
    else
        KFLAGS+=(--all-containers=true)
    fi
    if [ "$START_FROM_NOW" = true ]; then
        KFLAGS+=(--since-time="$STREAM_START_UTC")
    fi

    timeout "$DURATION" kubectl "${KFLAGS[@]}" >> "$LOG_FILE" 2>&1 &
    pid=$!

    PID_LIST+=("$pid")
    NAME_LIST+=("$POD_NS/$POD_NAME")
    STARTED=$((STARTED + 1))
    printf "  ${GREEN}▶${NC} %-60s pid=%s\n" "$POD_NS/$POD_NAME" "$pid"
done

echo ""
log_info "Started $STARTED stream(s); waiting up to $DURATION..."
echo ""

DONE_OK=0
DONE_ERR=0

for i in "${!PID_LIST[@]}"; do
    pid="${PID_LIST[$i]}"
    name="${NAME_LIST[$i]}"
    if wait "$pid"; then
        DONE_OK=$((DONE_OK + 1))
        printf "  ${GREEN}✓${NC} %-60s completed\n" "$name"
    else
        rc=$?
        # timeout returns 124 when duration expires (expected)
        if [ "$rc" -eq 124 ]; then
            DONE_OK=$((DONE_OK + 1))
            printf "  ${GREEN}✓${NC} %-60s timed out as expected\n" "$name"
        else
            DONE_ERR=$((DONE_ERR + 1))
            printf "  ${RED}✗${NC} %-60s exit=%s\n" "$name" "$rc"
        fi
    fi
done

TOTAL_SIZE=$(du -sh "$RUN_DIR" 2>/dev/null | cut -f1)
TOTAL_FILES=$(find "$RUN_DIR" -type f -name "*.log" | wc -l | tr -d '[:space:]')

echo ""
log_success "Live log collection completed."
echo "============================================"
echo "  Output Directory: $RUN_DIR"
echo "  Streams Started:  $STARTED"
echo "  Start Failures:   $FAILED_START"
echo "  Completed OK:     $DONE_OK"
echo "  Completed Error:  $DONE_ERR"
echo "  Log Files:        $TOTAL_FILES"
echo "  Total Size:       $TOTAL_SIZE"
echo "============================================"

