#!/bin/bash

# Configuration
NAMESPACE="ncm-cg"
DURATION=1200  # 20 minutes in seconds
LOG_DIR="pod-logs"
TIMESTAMP_FORMAT="[%Y-%m-%d %H:%M:%S]"
CONTAINER=""  # Optional: specific container name (empty = default container)

# Parse command line arguments
while getopts "n:d:l:c:h" opt; do
    case $opt in
        n) NAMESPACE="$OPTARG" ;;
        d) DURATION="$OPTARG" ;;
        l) LOG_DIR="$OPTARG" ;;
        c) CONTAINER="$OPTARG" ;;
        h)
            echo "Usage: $0 [-n namespace] [-d duration] [-l log_dir] [-c container]"
            echo "  -n  Namespace (default: ncm-cg)"
            echo "  -d  Duration in seconds (default: 1200)"
            echo "  -l  Log directory (default: pod-logs)"
            echo "  -c  Container name (default: first container in pod)"
            echo "  -h  Show this help"
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

# Cleanup function
cleanup() {
    log_info "Stopping log streams..."
    
    # Kill all background jobs
    jobs -p | while read pid; do
        kill "$pid" 2>/dev/null
    done
    
    # Wait for jobs to finish
    wait 2>/dev/null
    
    log_success "All log streams stopped."
    
    # Delete empty log files
    local empty_count=0
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ] && [ ! -s "$log_file" ]; then
            rm -f "$log_file"
            empty_count=$((empty_count + 1))
        fi
    done
    
    if [ $empty_count -gt 0 ]; then
        log_info "Deleted $empty_count empty log files"
    fi
    
    # Print summary (only non-empty files)
    echo ""
    log_info "Log Summary:"
    echo "============================================"
    local file_count=0
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            lines=$(wc -l < "$log_file")
            size=$(du -h "$log_file" | cut -f1)
            echo "  $(basename "$log_file"): $lines lines, $size"
            file_count=$((file_count + 1))
        fi
    done
    
    if [ $file_count -eq 0 ]; then
        echo "  (No logs collected)"
    fi
    echo "============================================"
    
    exit 0
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Check if kubectl is available
if ! command -v kubectl &>/dev/null; then
    log_error "kubectl not found. Please install kubectl."
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    log_error "Namespace '$NAMESPACE' does not exist."
    exit 1
fi

# Create log directory
mkdir -p "$LOG_DIR"
log_info "Created log directory: $LOG_DIR"

# Check for 'ts' command (from moreutils)
if ! command -v ts &>/dev/null; then
    log_warn "'ts' command not found. Using awk for timestamping."
    log_warn "Install moreutils for better performance: sudo yum install moreutils"
    USE_AWK=true
else
    log_info "Using 'ts' command for timestamping."
    USE_AWK=false
fi

# Get all pods in the namespace
log_info "Fetching pods from namespace: $NAMESPACE"
PODS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

if [ -z "$PODS" ]; then
    log_error "No pods found in namespace '$NAMESPACE'."
    exit 1
fi

# Count pods
POD_COUNT=$(echo "$PODS" | wc -w)
log_info "Found $POD_COUNT pod(s) in namespace '$NAMESPACE'"

# Build container flag if specified
CONTAINER_FLAG=""
if [ -n "$CONTAINER" ]; then
    CONTAINER_FLAG="-c $CONTAINER"
    log_info "Using container: $CONTAINER"
else
    log_info "Using default container for each pod"
fi

# Start streaming logs for each pod
STARTED_COUNT=0
for pod in $PODS; do
    log_info "Starting log stream for pod: $pod"
    
    # Check if pod is running
    POD_STATUS=$(kubectl get pod -n "$NAMESPACE" "$pod" -o jsonpath='{.status.phase}' 2>/dev/null)
    
    if [ "$POD_STATUS" != "Running" ]; then
        log_warn "Pod '$pod' is not running (status: $POD_STATUS). Skipping..."
        continue
    fi
    
    # If container specified, check if it exists in the pod
    if [ -n "$CONTAINER" ]; then
        CONTAINERS=$(kubectl get pod -n "$NAMESPACE" "$pod" -o jsonpath='{.spec.containers[*].name}' 2>/dev/null)
        if ! echo "$CONTAINERS" | grep -qw "$CONTAINER"; then
            log_warn "Container '$CONTAINER' not found in pod '$pod'. Available: $CONTAINERS. Skipping..."
            continue
        fi
    fi
    
    LOG_FILE="$LOG_DIR/${pod}.log"
    
    # Stream logs with timestamp
    if [ "$USE_AWK" = true ]; then
        kubectl logs -n "$NAMESPACE" -f "$pod" $CONTAINER_FLAG --tail=0 2>&1 | \
            awk -v pod="$pod" '{ print strftime("[%Y-%m-%d %H:%M:%S]"), "['"$pod"']", $0; fflush(); }' >> "$LOG_FILE" &
    else
        kubectl logs -n "$NAMESPACE" -f "$pod" $CONTAINER_FLAG --tail=0 2>&1 | \
            ts "$TIMESTAMP_FORMAT" | \
            sed "s/^/[$pod] /" >> "$LOG_FILE" &
    fi
    
    STARTED_COUNT=$((STARTED_COUNT + 1))
done

if [ $STARTED_COUNT -eq 0 ]; then
    log_error "No pods were started for log streaming."
    exit 1
fi

log_success "Started streaming logs for $STARTED_COUNT pod(s)"
log_info "Logs will be collected for $((DURATION / 60)) minutes ($DURATION seconds)"
log_info "Press Ctrl+C to stop early"

# Show progress bar
INTERVAL=10
ELAPSED=0
while [ $ELAPSED -lt $DURATION ]; do
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    REMAINING=$((DURATION - ELAPSED))
    PERCENT=$((ELAPSED * 100 / DURATION))
    
    # Create progress bar
    BAR_LENGTH=50
    FILLED=$((PERCENT * BAR_LENGTH / 100))
    EMPTY=$((BAR_LENGTH - FILLED))
    
    printf "\r${GREEN}Progress:${NC} ["
    printf "%${FILLED}s" | tr ' ' '='
    printf "%${EMPTY}s" | tr ' ' '-'
    printf "] %3d%% | Elapsed: %dm%ds | Remaining: %dm%ds" \
        $PERCENT \
        $((ELAPSED / 60)) $((ELAPSED % 60)) \
        $((REMAINING / 60)) $((REMAINING % 60))
done

echo ""
log_success "Log collection completed!"

# Cleanup will be called by trap

