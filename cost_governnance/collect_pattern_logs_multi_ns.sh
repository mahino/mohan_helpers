#!/bin/bash

set -o pipefail

# ============================================================
# Collect logs from pods matching name patterns across namespaces
# Pod name patterns: temp, defe
# Output: multi namespace folder -> namespace subfolders -> pod logs
# ============================================================

POD_NAME_PATTERN_REGEX="temp|defe"
BASE_OUTPUT_DIR="multi_pattern_logs"
TAIL_LINES=""
SINCE=""

usage() {
    cat <<'EOF'
Usage:
  collect_pattern_logs_multi_ns.sh [-l output_dir] [-t tail_lines] [-s since]

Options:
  -l  Base output directory name (default: multi_pattern_logs)
  -t  Tail N lines from each pod log before filtering
  -s  Logs since duration (e.g. 30m, 1h, 24h)
  -h  Show help

Examples:
  ./collect_pattern_logs_multi_ns.sh
  ./collect_pattern_logs_multi_ns.sh -s 1h
  ./collect_pattern_logs_multi_ns.sh -t 2000 -l my_multi_logs
EOF
}

while getopts "l:t:s:h" opt; do
    case "$opt" in
        l) BASE_OUTPUT_DIR="$OPTARG" ;;
        t) TAIL_LINES="$OPTARG" ;;
        s) SINCE="$OPTARG" ;;
        h)
            usage
            exit 0
            ;;
        \?)
            echo "[ERROR] Invalid option: -$OPTARG" >&2
            usage
            exit 1
            ;;
    esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${BLUE}[SUCCESS]${NC} $1"; }

if ! command -v kubectl >/dev/null 2>&1; then
    log_error "kubectl not found."
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="${BASE_OUTPUT_DIR}_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

log_info "Collecting logs across all namespaces"
log_info "Pod name patterns: $POD_NAME_PATTERN_REGEX"
log_info "Output folder: $OUTPUT_DIR"

KUBECTL_FLAGS="--all-containers=true"
if [[ -n "$TAIL_LINES" ]]; then
    KUBECTL_FLAGS="$KUBECTL_FLAGS --tail=$TAIL_LINES"
    log_info "Tail lines: $TAIL_LINES"
fi
if [[ -n "$SINCE" ]]; then
    KUBECTL_FLAGS="$KUBECTL_FLAGS --since=$SINCE"
    log_info "Since: $SINCE"
fi

POD_ENTRIES=$(kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"|"}{.metadata.name}{"\n"}{end}')
if [[ -z "$POD_ENTRIES" ]]; then
    log_error "No pods found."
    exit 1
fi

TOTAL_PODS=0
MATCHED_PODS=0
FAILED_PODS=0
SKIPPED_PODS=0

while IFS="|" read -r POD_NS POD_NAME; do
    [[ -z "$POD_NS" || -z "$POD_NAME" ]] && continue
    TOTAL_PODS=$((TOTAL_PODS + 1))

    # Filter by pod name pattern.
    if ! echo "$POD_NAME" | grep -Ei -q "$POD_NAME_PATTERN_REGEX"; then
        SKIPPED_PODS=$((SKIPPED_PODS + 1))
        continue
    fi

    NS_DIR="$OUTPUT_DIR/$POD_NS"
    mkdir -p "$NS_DIR"
    OUT_FILE="$NS_DIR/${POD_NAME}.log"

    RAW_LOGS=$(kubectl logs -n "$POD_NS" "$POD_NAME" $KUBECTL_FLAGS 2>&1)
    CMD_EXIT=$?

    if [[ $CMD_EXIT -ne 0 ]]; then
        FAILED_PODS=$((FAILED_PODS + 1))
        log_warn "Failed: $POD_NS/$POD_NAME"
        continue
    fi

    {
        echo "========================================"
        echo "Namespace: $POD_NS"
        echo "Pod: $POD_NAME"
        echo "Matched pod name by: $POD_NAME_PATTERN_REGEX"
        echo "Collected at: $(date)"
        echo "========================================"
        echo ""
        echo "$RAW_LOGS"
    } > "$OUT_FILE"

    LINES=$(wc -l < "$OUT_FILE" | tr -d ' ')
    MATCHED_PODS=$((MATCHED_PODS + 1))
    printf "  ${GREEN}✓${NC} %-55s %6s lines\n" "$POD_NS/$POD_NAME" "$LINES"
done <<< "$POD_ENTRIES"

echo ""
log_success "Completed pattern log collection"
echo "============================================"
echo "Output directory : $OUTPUT_DIR"
echo "Pods scanned     : $TOTAL_PODS"
echo "Pods matched     : $MATCHED_PODS (name pattern)"
echo "Pods skipped     : $SKIPPED_PODS"
echo "Pods failed      : $FAILED_PODS"
echo "============================================"

if [[ $MATCHED_PODS -eq 0 ]]; then
    log_warn "No pod names matched pattern: $POD_NAME_PATTERN_REGEX"
fi

