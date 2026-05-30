#!/bin/bash

# Configuration
NAMESPACE="ncm-cg"
LOG_DIR="pod-logs"
TAIL_LINES=""  # Optional: limit lines (empty = all logs)
SINCE=""       # Optional: time duration (e.g., "1h", "30m", "24h")
CONTAINER=""   # Optional: specific container name (empty = default container)

# Parse command line arguments
while getopts "n:l:t:s:c:h" opt; do
    case $opt in
        n) NAMESPACE="$OPTARG" ;;
        l) LOG_DIR="$OPTARG" ;;
        t) TAIL_LINES="$OPTARG" ;;
        s) SINCE="$OPTARG" ;;
        c) CONTAINER="$OPTARG" ;;
        h)
            echo "Usage: $0 [-n namespace] [-l log_dir] [-t tail_lines] [-s since] [-c container]"
            echo "  -n  Namespace (default: ncm-cg, use 'all' for all namespaces)"
            echo "  -l  Log directory (default: pod-logs)"
            echo "  -t  Number of lines from end (e.g., 1000)"
            echo "  -s  Logs since duration (e.g., 1h, 30m, 24h)"
            echo "  -c  Container name (default: all containers)"
            echo "  -h  Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 -n kube-system -t 500           # Last 500 lines from each pod"
            echo "  $0 -n ncm-cg -s 1h                 # Logs from last 1 hour"
            echo "  $0 -n ncm-cg -s 30m -c mycontainer # Last 30 min from specific container"
            echo "  $0 -n all -t 100                   # Last 100 lines from ALL pods in ALL namespaces"
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${BLUE}[SUCCESS]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &>/dev/null; then
    log_error "kubectl not found. Please install kubectl."
    exit 1
fi

# Handle 'all' namespace option
ALL_NAMESPACES=false
if [ "$NAMESPACE" = "all" ] || [ "$NAMESPACE" = "ALL" ]; then
    ALL_NAMESPACES=true
    log_info "Collecting logs from ALL namespaces"
else
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        log_error "Namespace '$NAMESPACE' does not exist."
        exit 1
    fi
fi

# Create log directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="${LOG_DIR}_${TIMESTAMP}"
mkdir -p "$LOG_DIR"
log_info "Created log directory: $LOG_DIR"

# Get all pods
if [ "$ALL_NAMESPACES" = true ]; then
    log_info "Fetching pods from all namespaces..."
    # Get pods with namespace info: namespace/podname
    POD_DATA=$(kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name} {end}')
else
    log_info "Fetching pods from namespace: $NAMESPACE"
    POD_DATA=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name} {end}')
fi

if [ -z "$POD_DATA" ]; then
    if [ "$ALL_NAMESPACES" = true ]; then
        log_error "No pods found in the cluster."
    else
        log_error "No pods found in namespace '$NAMESPACE'."
    fi
    exit 1
fi

# Count pods
POD_COUNT=$(echo "$POD_DATA" | wc -w)
if [ "$ALL_NAMESPACES" = true ]; then
    NS_COUNT=$(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}' | wc -w)
    log_info "Found $POD_COUNT pod(s) across $NS_COUNT namespace(s)"
else
    log_info "Found $POD_COUNT pod(s) in namespace '$NAMESPACE'"
fi

# Build kubectl flags
KUBECTL_FLAGS=""
if [ -n "$TAIL_LINES" ]; then
    KUBECTL_FLAGS="$KUBECTL_FLAGS --tail=$TAIL_LINES"
    log_info "Limiting to last $TAIL_LINES lines"
fi

if [ -n "$SINCE" ]; then
    KUBECTL_FLAGS="$KUBECTL_FLAGS --since=$SINCE"
    log_info "Collecting logs since: $SINCE"
fi

if [ -n "$CONTAINER" ]; then
    KUBECTL_FLAGS="$KUBECTL_FLAGS -c $CONTAINER"
    log_info "Using container: $CONTAINER"
else
    KUBECTL_FLAGS="$KUBECTL_FLAGS --all-containers=true"
    log_info "Collecting logs from all containers"
fi

# Collect logs for each pod
COLLECTED_COUNT=0
FAILED_COUNT=0
TOTAL_LINES=0
TOTAL_SIZE=0

echo ""
log_info "Starting log collection..."
echo "============================================"

for pod_entry in $POD_DATA; do
    # Parse namespace and pod name
    if [ "$ALL_NAMESPACES" = true ]; then
        POD_NS=$(echo "$pod_entry" | cut -d'/' -f1)
        POD_NAME=$(echo "$pod_entry" | cut -d'/' -f2)
    else
        POD_NS="$NAMESPACE"
        POD_NAME="$pod_entry"
    fi
    
    # Check if pod exists and get status
    POD_STATUS=$(kubectl get pod -n "$POD_NS" "$POD_NAME" -o jsonpath='{.status.phase}' 2>/dev/null)
    
    if [ -z "$POD_STATUS" ]; then
        log_warn "Pod '$POD_NAME' in namespace '$POD_NS' not found. Skipping..."
        ((FAILED_COUNT++))
        continue
    fi
    
    # Get containers in pod
    CONTAINERS=$(kubectl get pod -n "$POD_NS" "$POD_NAME" -o jsonpath='{.spec.containers[*].name}' 2>/dev/null)
    
    # Create namespace subdirectory for 'all' mode
    if [ "$ALL_NAMESPACES" = true ]; then
        mkdir -p "$LOG_DIR/$POD_NS"
        LOG_FILE="$LOG_DIR/$POD_NS/${POD_NAME}.log"
        DISPLAY_NAME="$POD_NS/$POD_NAME"
    else
        LOG_FILE="$LOG_DIR/${POD_NAME}.log"
        DISPLAY_NAME="$POD_NAME"
    fi
    
    # Add header to log file
    {
        echo "========================================"
        echo "Pod: $POD_NAME"
        echo "Namespace: $POD_NS"
        echo "Status: $POD_STATUS"
        echo "Containers: $CONTAINERS"
        echo "Collected at: $(date)"
        echo "========================================"
        echo ""
    } > "$LOG_FILE"
    
    # Collect logs
    if kubectl logs -n "$POD_NS" "$POD_NAME" $KUBECTL_FLAGS >> "$LOG_FILE" 2>&1; then
        LINES=$(wc -l < "$LOG_FILE")
        SIZE=$(du -h "$LOG_FILE" | cut -f1)
        TOTAL_LINES=$((TOTAL_LINES + LINES))
        
        printf "  ${GREEN}✓${NC} %-60s %8s lines  %8s\n" "$DISPLAY_NAME" "$LINES" "$SIZE"
        ((COLLECTED_COUNT++))
    else
        log_warn "Failed to collect logs from pod '$DISPLAY_NAME'"
        echo "ERROR: Failed to collect logs" >> "$LOG_FILE"
        ((FAILED_COUNT++))
    fi
done

echo "============================================"
echo ""

# Print summary
log_success "Log collection completed!"
echo ""
log_info "Summary:"
echo "============================================"
if [ "$ALL_NAMESPACES" = true ]; then
    echo "  Namespace:     ALL"
else
    echo "  Namespace:     $NAMESPACE"
fi
echo "  Log Directory: $LOG_DIR"
echo "  Pods Found:    $POD_COUNT"
echo "  Collected:     $COLLECTED_COUNT"
echo "  Failed:        $FAILED_COUNT"
echo "  Total Lines:   $TOTAL_LINES"
echo "============================================"

# Calculate total size
TOTAL_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
echo "  Total Size:    $TOTAL_SIZE"
echo "============================================"

# List all log files
echo ""
log_info "Log Files:"
echo "--------------------------------------------"
if [ "$ALL_NAMESPACES" = true ]; then
    # List files with namespace subdirectories
    find "$LOG_DIR" -name "*.log" -type f | sort | while read -r log_file; do
        if [ -f "$log_file" ]; then
            lines=$(wc -l < "$log_file")
            size=$(du -h "$log_file" | cut -f1)
            rel_path="${log_file#$LOG_DIR/}"
            printf "  %-60s %6d lines  %6s\n" "$rel_path" "$lines" "$size"
        fi
    done
else
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            lines=$(wc -l < "$log_file")
            size=$(du -h "$log_file" | cut -f1)
            printf "  %-60s %6d lines  %6s\n" "$(basename "$log_file")" "$lines" "$size"
        fi
    done
fi
echo "--------------------------------------------"

log_success "Done! Logs saved to: $LOG_DIR"

