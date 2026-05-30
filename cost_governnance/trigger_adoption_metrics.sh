#!/bin/bash

set -o pipefail  # Exit on pipe failures

# ============================================
# Configuration
# ============================================
NAMESPACE="ncm-cg"
CRONJOB_NAME="cron-cg-adoption-metrics-ingestion"
ITERATIONS=20
SLEEP_DURATION=3600  # 60 minutes (1 hour)

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

log_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Check if required commands exist
check_prerequisites() {
    log_info "Checking prerequisites..."
    xq
    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        log_error "Namespace '$NAMESPACE' does not exist."
        exit 1
    fi
    
    if ! kubectl get cronjob -n "$NAMESPACE" "$CRONJOB_NAME" &>/dev/null; then
        log_error "CronJob '$CRONJOB_NAME' not found in namespace '$NAMESPACE'."
        exit 1
    fi
    
    log_success "All prerequisites met."
}

# Get job pod logs
get_job_logs() {
    local job_name=$1
    local max_wait=60  # Wait up to 60 seconds for pod to be ready
    local wait_count=0
    
    log_info "Waiting for job pod to be ready..."
    
    while [ $wait_count -lt $max_wait ]; do
        local pod_name=$(kubectl get pods -n "$NAMESPACE" -l job-name="$job_name" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        
        if [ -n "$pod_name" ]; then
            local pod_status=$(kubectl get pod -n "$NAMESPACE" "$pod_name" -o jsonpath='{.status.phase}' 2>/dev/null)
            log_info "Pod: $pod_name | Status: $pod_status"
            
            if [ "$pod_status" = "Running" ] || [ "$pod_status" = "Succeeded" ] || [ "$pod_status" = "Failed" ]; then
                log_info "Fetching pod logs..."
                kubectl logs -n "$NAMESPACE" "$pod_name" --tail=50 2>&1 | head -20
                return 0
            fi
        fi
        
        sleep 2
        wait_count=$((wait_count + 2))
    done
    
    log_warn "Pod not ready after $max_wait seconds."
    return 1
}

# Monitor job completion
monitor_job() {
    local job_name=$1
    local timeout=600  # 10 minutes timeout
    local elapsed=0
    local check_interval=10
    
    log_info "Monitoring job: $job_name"
    
    while [ $elapsed -lt $timeout ]; do
        local job_status=$(kubectl get job -n "$NAMESPACE" "$job_name" -o jsonpath='{.status.conditions[0].type}' 2>/dev/null)
        local active=$(kubectl get job -n "$NAMESPACE" "$job_name" -o jsonpath='{.status.active}' 2>/dev/null)
        local succeeded=$(kubectl get job -n "$NAMESPACE" "$job_name" -o jsonpath='{.status.succeeded}' 2>/dev/null)
        local failed=$(kubectl get job -n "$NAMESPACE" "$job_name" -o jsonpath='{.status.failed}' 2>/dev/null)
        
        if [ "$job_status" = "Complete" ] || [ "$succeeded" = "1" ]; then
            log_success "Job completed successfully!"
            return 0
        elif [ "$job_status" = "Failed" ] || [ "$failed" = "1" ]; then
            log_error "Job failed!"
            get_job_logs "$job_name"
            return 1
        else
            printf "\r${GREEN}Monitoring:${NC} Active: ${active:-0} | Succeeded: ${succeeded:-0} | Failed: ${failed:-0} | Elapsed: ${elapsed}s"
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    echo ""
    log_warn "Job monitoring timed out after $timeout seconds."
    return 1
}

# Create and monitor job
create_adoption_metrics_job() {
    local iteration=$1
    local job_name="cron-cg-adoption-metrics-manual-trigger-${iteration}-$(date +%Y-%m-%d-%H-%M-%S)"
    
    log_info "Creating job: $job_name"
    
    if kubectl create job --from=cronjob/"$CRONJOB_NAME" "$job_name" -n "$NAMESPACE" 2>&1; then
        log_success "Job '$job_name' created successfully."
        
        # Wait a few seconds for job to initialize
        sleep 5
        
        # Get pod name for the job
        local pod_name=$(kubectl get pods -n "$NAMESPACE" -l job-name="$job_name" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        if [ -n "$pod_name" ]; then
            log_info "Job pod: $pod_name"
        fi
        
        # Monitor job completion
        if monitor_job "$job_name"; then
            return 0
        else
            return 1
        fi
    else
        log_error "Failed to create job '$job_name'."
        return 1
    fi
}

# Sleep with progress indicator
sleep_with_progress() {
    local total_seconds=$1
    local interval=30
    local iterations=$((total_seconds / interval))
    local remaining=$((total_seconds % interval))
    
    log_info "Sleeping for $total_seconds seconds ($((total_seconds / 60)) minutes)..."
    
    for j in $(seq 1 $iterations); do
        local elapsed=$((j * interval))
        local remaining_time=$((total_seconds - elapsed))
        local percent=$((elapsed * 100 / total_seconds))
        
        # Create progress bar
        local bar_length=40
        local filled=$((percent * bar_length / 100))
        local empty=$((bar_length - filled))
        
        printf "\r${GREEN}Progress:${NC} ["
        printf "%${filled}s" | tr ' ' '='
        printf "%${empty}s" | tr ' ' '-'
        printf "] %3d%% | Elapsed: %dm%ds | Remaining: %dm%ds" \
            $percent \
            $((elapsed / 60)) $((elapsed % 60)) \
            $((remaining_time / 60)) $((remaining_time % 60))
        
        sleep $interval
    done
    
    # Sleep remaining time
    if [ $remaining -gt 0 ]; then
        sleep $remaining
    fi
    
    echo ""
    log_success "Sleep completed."
}

# Cleanup function
cleanup() {
    log_section "Script Interrupted"
    log_warn "Cleaning up..."
    exit 130
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# ============================================
# Main Script
# ============================================

# Set log file path (with timestamp)
LOG_FILE="adoption_metrics_$(date +%Y-%m-%d_%H-%M-%S).log"

# Redirect all output (stdout + stderr) to log file AND console
exec > >(tee -a "$LOG_FILE") 2>&1

log_section "Starting Adoption Metrics Ingestion Script"
log_info "Logs will be saved to: $LOG_FILE"
log_info "Configuration:"
echo "  - Namespace: $NAMESPACE"
echo "  - CronJob: $CRONJOB_NAME"
echo "  - Iterations: $ITERATIONS"
echo "  - Sleep Duration: $SLEEP_DURATION seconds ($((SLEEP_DURATION / 60)) minutes)"

# Check prerequisites
check_prerequisites

# Get cronjob details
log_info "CronJob Details:"
kubectl get cronjob -n "$NAMESPACE" "$CRONJOB_NAME" -o wide 2>&1 | grep -v "^$"

# Statistics
SUCCESS_COUNT=0
FAILURE_COUNT=0
START_TIME=$(date +%s)
declare -a FAILED_ITERATIONS

# Main loop
for i in $(seq 1 $ITERATIONS); do
    log_section "Iteration $i of $ITERATIONS"
    ITERATION_START=$(date +%s)
    
    # Create adoption metrics job
    if create_adoption_metrics_job "$i"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        log_error "Failed to complete adoption metrics job."
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        FAILED_ITERATIONS+=($i)
    fi
    
    ITERATION_END=$(date +%s)
    ITERATION_DURATION=$((ITERATION_END - ITERATION_START))
    log_success "Iteration $i completed in $ITERATION_DURATION seconds."
    
    # Sleep before next iteration (skip on last iteration)
    if [ $i -lt $ITERATIONS ]; then
        log_info "Waiting before next iteration..."
        sleep_with_progress $SLEEP_DURATION
    fi
done

# ============================================
# Final Summary
# ============================================

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

log_section "Adoption Metrics Ingestion Script Completed"
log_info "Summary:"
echo "  - Total Iterations: $ITERATIONS"
echo "  - Successful: $SUCCESS_COUNT"
echo "  - Failed: $FAILURE_COUNT"
if [ $FAILURE_COUNT -gt 0 ]; then
    echo "  - Failed Iterations: ${FAILED_ITERATIONS[*]}"
fi
echo "  - Total Duration: $((TOTAL_DURATION / 60)) minutes ($TOTAL_DURATION seconds)"
echo "  - Average per Iteration: $((TOTAL_DURATION / ITERATIONS)) seconds"
echo "  - Success Rate: $((SUCCESS_COUNT * 100 / ITERATIONS))%"
echo "  - Log File: $LOG_FILE"

# List all created jobs
log_info "Jobs created in this run:"
kubectl get jobs -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp | grep "cron-cg-adoption-metrics-manual-trigger" | tail -$ITERATIONS

if [ $FAILURE_COUNT -eq 0 ]; then
    log_success "All iterations completed successfully!"
    exit 0
else
    log_warn "$FAILURE_COUNT iteration(s) failed. Check logs for details."
    exit 1
fi

