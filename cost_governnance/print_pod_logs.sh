#!/bin/bash

set -o pipefail  # Exit on pipe failures

# ============================================
# Configuration
# ============================================
DEFAULT_NAMESPACE="ncm-cg"
DEFAULT_DURATION=1200  # 20 minutes in seconds
LOG_DIR="pod-logs"
TIMESTAMP_FORMAT="[%Y-%m-%d %H:%M:%S]"
TAIL_LINES=0  # 0 = only new logs, -1 = all logs

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================
# Functions
# ============================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${BLUE}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

show_usage() {
    cat << EOF
${CYAN}Pod Log Streaming Script${NC}

Usage: $0 [OPTIONS]

Options:
    -n, --namespace NAMESPACE    Kubernetes namespace (default: $DEFAULT_NAMESPACE)
                                 Can be specified multiple times for multiple namespaces
    -p, --pod POD_NAME          Specific pod name or pattern (supports wildcards)
                                 Can be specified multiple times
    -d, --duration SECONDS      Duration to stream logs (default: $DEFAULT_DURATION)
    -t, --tail LINES            Number of existing log lines to include (default: $TAIL_LINES)
                                 Use -1 for all existing logs
    -o, --output-dir DIR        Output directory for logs (default: $LOG_DIR)
    -a, --all-namespaces        Stream logs from all namespaces
    -A, --all                   Stream logs from all pods in all namespaces
    -l, --label SELECTOR        Label selector (e.g., app=myapp)
    -h, --help                  Show this help message

Examples:
    # Stream logs from default namespace for 20 minutes
    $0

    # Stream logs from specific namespace
    $0 -n ncm-cg

    # Stream logs from multiple namespaces
    $0 -n ncm-cg -n ntnx-ncm-datastore

    # Stream logs from specific pods
    $0 -n ncm-cg -p cg-api-server -p cg-worker

    # Stream logs with pattern matching
    $0 -n ncm-cg -p "cg-api-*"

    # Stream logs from all namespaces for 30 minutes
    $0 -a -d 1800

    # Stream logs from ALL pods in ALL namespaces
    $0 -A

    # Stream logs with label selector
    $0 -n ncm-cg -l app=cg-api

    # Include last 100 lines of existing logs
    $0 -n ncm-cg -t 100

EOF
}

# Cleanup function
cleanup() {
    echo ""
    log_info "Stopping log streams..."
    
    # Kill all background jobs
    jobs -p | while read pid; do
        kill "$pid" 2>/dev/null
    done
    
    # Wait for jobs to finish
    wait 2>/dev/null
    
    log_success "All log streams stopped."
    
    # Print summary
    echo ""
    log_info "Cleaning up empty log files..."
    
    local deleted_count=0
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            # Check if file is empty or only contains header (less than 10 lines)
            lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
            size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo "0")
            
            # Delete if file is empty or very small (< 100 bytes, likely just header)
            if [ "$size" -lt 100 ] || [ "$lines" -lt 8 ]; then
                log_info "Deleting empty log file: $(basename "$log_file")"
                rm -f "$log_file"
                deleted_count=$((deleted_count + 1))
            fi
        fi
    done
    
    if [ $deleted_count -gt 0 ]; then
        log_success "Deleted $deleted_count empty log file(s)"
    fi
    
    echo ""
    log_info "Log Summary:"
    echo "============================================"
    
    local total_lines=0
    local total_size=0
    local file_count=0
    
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            lines=$(wc -l < "$log_file")
            size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
            size_human=$(numfmt --to=iec-i --suffix=B "$size" 2>/dev/null || echo "${size}B")
            
            echo "  $(basename "$log_file"): $lines lines, $size_human"
            
            total_lines=$((total_lines + lines))
            total_size=$((total_size + size))
            file_count=$((file_count + 1))
        fi
    done
    
    if [ $file_count -gt 0 ]; then
        total_size_human=$(numfmt --to=iec-i --suffix=B "$total_size" 2>/dev/null || echo "${total_size}B")
        echo "============================================"
        echo "  Total: $file_count files, $total_lines lines, $total_size_human"
    else
        echo "  No log files created."
    fi
    echo "============================================"
    
    exit 0
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Stream logs for a pod
stream_pod_logs() {
    local namespace=$1
    local pod=$2
    local use_awk=$3
    
    # Check if pod exists and is ready
    local pod_status=$(kubectl get pod -n "$namespace" "$pod" -o jsonpath='{.status.phase}' 2>/dev/null)
    
    if [ -z "$pod_status" ]; then
        log_warn "Pod '$pod' not found in namespace '$namespace'. Skipping..."
        return 1
    fi
    
    # Only stream logs from pods in Running state
    if [ "$pod_status" != "Running" ]; then
        log_warn "Pod '$pod' is not running (Status: $pod_status). Skipping..."
        return 1
    fi
    
    log_info "Starting log stream for pod: $namespace/$pod (Status: $pod_status)"
    
    local log_file="$LOG_DIR/${namespace}_${pod}.log"
    
    # Create log file with header
    {
        echo "============================================"
        echo "Pod: $pod"
        echo "Namespace: $namespace"
        echo "Status: $pod_status"
        echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "============================================"
        echo ""
    } > "$log_file"
    
    # Stream logs with timestamp
    if [ "$use_awk" = true ]; then
        kubectl logs -n "$namespace" -f "$pod" --tail="$TAIL_LINES" 2>&1 | \
            awk -v pod="$pod" '{ print strftime("[%Y-%m-%d %H:%M:%S]"), $0; fflush(); }' >> "$log_file" &
    else
        kubectl logs -n "$namespace" -f "$pod" --tail="$TAIL_LINES" 2>&1 | \
            ts "$TIMESTAMP_FORMAT" >> "$log_file" &
    fi
    
    return 0
}

# Get pods from namespace
get_pods_from_namespace() {
    local namespace=$1
    local pod_pattern=$2
    local label_selector=$3
    
    local kubectl_cmd="kubectl get pods -n $namespace"
    
    # Add label selector if provided
    if [ -n "$label_selector" ]; then
        kubectl_cmd="$kubectl_cmd -l $label_selector"
    fi
    
    kubectl_cmd="$kubectl_cmd -o jsonpath='{.items[*].metadata.name}'"
    
    local all_pods=$(eval $kubectl_cmd 2>/dev/null)
    
    if [ -z "$all_pods" ]; then
        return 1
    fi
    
    # Filter by pattern if provided
    if [ -n "$pod_pattern" ]; then
        echo "$all_pods" | tr ' ' '\n' | grep -E "$pod_pattern"
    else
        echo "$all_pods" | tr ' ' '\n'
    fi
}

# ============================================
# Parse Arguments
# ============================================

NAMESPACES=()
POD_PATTERNS=()
DURATION=$DEFAULT_DURATION
ALL_NAMESPACES=false
ALL_PODS=false
LABEL_SELECTOR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACES+=("$2")
            shift 2
            ;;
        -p|--pod)
            POD_PATTERNS+=("$2")
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -t|--tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        -o|--output-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -a|--all-namespaces)
            ALL_NAMESPACES=true
            shift
            ;;
        -A|--all)
            ALL_NAMESPACES=true
            ALL_PODS=true
            shift
            ;;
        -l|--label)
            LABEL_SELECTOR="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# ============================================
# Main Script
# ============================================

log_info "Pod Log Streaming Script"
echo "============================================"

# Check if kubectl is available
if ! command -v kubectl &>/dev/null; then
    log_error "kubectl not found. Please install kubectl."
    exit 1
fi

# Set default namespace if none specified and not all-namespaces
if [ ${#NAMESPACES[@]} -eq 0 ] && [ "$ALL_NAMESPACES" = false ]; then
    NAMESPACES=("$DEFAULT_NAMESPACE")
fi

# Get all namespaces if requested
if [ "$ALL_NAMESPACES" = true ]; then
    log_info "Fetching all namespaces..."
    mapfile -t NAMESPACES < <(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n')
    log_info "Found ${#NAMESPACES[@]} namespace(s)"
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

# Display configuration
log_info "Configuration:"
if [ "$ALL_PODS" = true ]; then
    echo "  - Mode: All pods in all namespaces"
fi
echo "  - Namespaces: ${NAMESPACES[*]}"
if [ ${#POD_PATTERNS[@]} -gt 0 ]; then
    echo "  - Pod Patterns: ${POD_PATTERNS[*]}"
fi
if [ -n "$LABEL_SELECTOR" ]; then
    echo "  - Label Selector: $LABEL_SELECTOR"
fi
echo "  - Duration: $DURATION seconds ($((DURATION / 60)) minutes)"
echo "  - Tail Lines: $TAIL_LINES"
echo "  - Output Directory: $LOG_DIR"
echo "============================================"

# Collect all pods to stream
declare -A PODS_TO_STREAM

for namespace in "${NAMESPACES[@]}"; do
    log_info "Processing namespace: $namespace"
    
    # Check if namespace exists
    if ! kubectl get namespace "$namespace" &>/dev/null; then
        log_warn "Namespace '$namespace' does not exist. Skipping..."
        continue
    fi
    
    # Get pods based on patterns or all pods
    if [ ${#POD_PATTERNS[@]} -gt 0 ]; then
        local pods_found=0
        for pattern in "${POD_PATTERNS[@]}"; do
            while IFS= read -r pod; do
                [ -n "$pod" ] && PODS_TO_STREAM["$namespace:$pod"]=1 && pods_found=$((pods_found + 1))
            done < <(get_pods_from_namespace "$namespace" "$pattern" "$LABEL_SELECTOR")
        done
        
        # If no pods matched the pattern, get all pods from this namespace
        if [ $pods_found -eq 0 ]; then
            log_info "No pods matched pattern in $namespace, getting all pods..."
            while IFS= read -r pod; do
                [ -n "$pod" ] && PODS_TO_STREAM["$namespace:$pod"]=1
            done < <(get_pods_from_namespace "$namespace" "" "$LABEL_SELECTOR")
        fi
    else
        while IFS= read -r pod; do
            [ -n "$pod" ] && PODS_TO_STREAM["$namespace:$pod"]=1
        done < <(get_pods_from_namespace "$namespace" "" "$LABEL_SELECTOR")
    fi
done

# Check if any pods found
if [ ${#PODS_TO_STREAM[@]} -eq 0 ]; then
    log_error "No pods found matching the criteria."
    exit 1
fi

log_success "Found ${#PODS_TO_STREAM[@]} pod(s) to stream"

# Start streaming logs for each pod
STARTED_COUNT=0
for pod_key in "${!PODS_TO_STREAM[@]}"; do
    namespace="${pod_key%%:*}"
    pod="${pod_key#*:}"
    
    if stream_pod_logs "$namespace" "$pod" "$USE_AWK"; then
        STARTED_COUNT=$((STARTED_COUNT + 1))
    fi
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
    printf "] %3d%% | Elapsed: %dm%ds | Remaining: %dm%ds | Streaming: %d pods" \
        $PERCENT \
        $((ELAPSED / 60)) $((ELAPSED % 60)) \
        $((REMAINING / 60)) $((REMAINING % 60)) \
        $STARTED_COUNT
done

echo ""
log_success "Log collection completed!"

# Cleanup will be called by trap
