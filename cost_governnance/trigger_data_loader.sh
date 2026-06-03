#!/bin/bash

set -o pipefail  # Exit on pipe failures

# ============================================
# Configuration
# ============================================
NAMESPACE="ncm-cg"
DATASTORE_NAMESPACE="ntnx-ncm-datastore"
PG_POD="cg-pg-1"
DATABASE="cg_nx"
CRONJOB_NAME="cron-nx-cg-data-loader"
DATA_LOADER_DEPLOYMENT="nx-cg-data-loader"
ITERATIONS=20
SLEEP_DURATION=10800  # 180 minutes (3 hours)
BACKFILL_HOURS=8      # Hours to backfill
WAIT_AFTER_COMPLETION=300  # 5 minutes after job completion
LOG_CHECK_INTERVAL=15  # Check logs every 15 seconds for more responsive updates

# Completion patterns to monitor (all must be present for job to be considered complete)
# These patterns indicate the final stages of each job type
COMPLETION_PATTERNS=(
    # Job completion messages
    "CLUSTER_CONFIG completed successfully"
    "CATEGORIES_CONFIG completed successfully"
    "VM_CONFIG completed successfully"
    "CLUSTER_HARDWARE_CONFIG completed successfully"
    # Backfill status updates (indicates data persisted)
    "Updating service backfill status for Service :\[CLUSTER_CONFIG\]"
    "Updating service backfill status for Service :\[NX_ROUTINE_WORKFLOW\]"
    "Updating service backfill status for Service :\[CATEGORIES_CONFIG\]"
    "Updating service backfill status for Service :\[VM_CONFIG\]"
    "Updating service backfill status for Service :\[CLUSTER_HARDWARE_CONFIG\]"
    # # Temp file cleanup (indicates job finished processing)
    # "temp file for executor CATEGORIES_CONFIG deleted successfully"
    # "temp file for executor VM_CONFIG deleted successfully"
    # "temp file for executor CLUSTER_HARDWARE_CONFIG deleted successfully"
    # "temp file for executor CLUSTER_CONFIG deleted successfully"
)

# Global variable to store job start timestamp (ISO 8601 format for --since-time)
JOB_START_TIMESTAMP=""

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
    
    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        log_error "Namespace '$NAMESPACE' does not exist."
        exit 1
    fi
    
    if ! kubectl get namespace "$DATASTORE_NAMESPACE" &>/dev/null; then
        log_error "Namespace '$DATASTORE_NAMESPACE' does not exist."
        exit 1
    fi
    
    if ! kubectl get pod -n "$DATASTORE_NAMESPACE" "$PG_POD" &>/dev/null; then
        log_error "PostgreSQL pod '$PG_POD' not found in namespace '$DATASTORE_NAMESPACE'."
        exit 1
    fi
    
    if ! kubectl get cronjob -n "$NAMESPACE" "$CRONJOB_NAME" &>/dev/null; then
        log_error "CronJob '$CRONJOB_NAME' not found in namespace '$NAMESPACE'."
        exit 1
    fi
    
    log_success "All prerequisites met."
}

# Execute SQL query
execute_sql() {
    local query="$1"
    local description="$2"
    
    if [ -n "$description" ]; then
        log_info "$description"
    fi
    
    kubectl exec -n "$DATASTORE_NAMESPACE" "$PG_POD" -- \
        psql -d "$DATABASE" -c "$query" 2>&1
    
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "SQL query failed with exit code $exit_code"
        return 1
    fi
    return 0
}

# Query backfill status
query_backfill_status() {
    execute_sql "SELECT * FROM nutanix_backfill_job_run_status;" "Querying backfill status..."
}

# Update backfill status
update_backfill_status() {
    local epoch_ms=$1
    
    log_info "Updating backfill status to epoch: $epoch_ms"
    
    execute_sql "UPDATE nutanix_backfill_job_run_status SET is_completed = false, last_persisted_epoch = $epoch_ms, last_completed_date = $epoch_ms;" \
        "Updating nutanix_backfill_job_run_status..."
    
    if [ $? -eq 0 ]; then
        log_success "Backfill status updated successfully."
        return 0
    else
        log_error "Failed to update backfill status."
        return 1
    fi
}

# Check if any data loader jobs are currently running
# Returns 0 if a job is running, 1 if no jobs are running
check_running_jobs() {
    local running_jobs=""
    local running_pods=""
    
    # Check for active jobs created from the cronjob (manual triggers or scheduled)
    running_jobs=$(kubectl get jobs -n "$NAMESPACE" \
        -o jsonpath='{range .items[?(@.status.active>0)]}{.metadata.name}{"\n"}{end}' 2>/dev/null \
        | grep -E "cron-nx-cg-data-loader|nx-cg-data-loader" || true)
    
    # Also check for running pods with the data loader pattern
    running_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null \
        | tr ' ' '\n' | grep -E "nx-cg-data-loader|cron-nx-cg-data-loader" || true)
    
    if [ -n "$running_jobs" ] || [ -n "$running_pods" ]; then
        if [ -n "$running_jobs" ]; then
            echo "$running_jobs"
        fi
        if [ -n "$running_pods" ]; then
            echo "$running_pods"
        fi
        return 0
    fi
    
    return 1
}

# Wait for any existing running jobs to complete before starting a new one
wait_for_existing_jobs() {
    local max_wait=${1:-$SLEEP_DURATION}  # Default to SLEEP_DURATION if not specified
    local check_interval=30  # Check every 30 seconds
    local elapsed=0
    local start_time=$(date +%s)
    
    log_section "Checking for Running Jobs"
    
    # First check if anything is running
    local running_items
    running_items=$(check_running_jobs)
    
    if [ -z "$running_items" ]; then
        log_success "No existing data loader jobs are running. Safe to proceed."
        return 0
    fi
    
    log_warn "Found running data loader job(s):"
    echo "$running_items" | while read -r item; do
        if [ -n "$item" ]; then
            echo -e "  ${YELLOW}→${NC} $item"
        fi
    done
    
    log_info "Waiting for existing job(s) to complete before starting new one..."
    log_info "Max wait time: $max_wait seconds ($((max_wait / 60)) minutes)"
    echo ""
    
    # Reset milestone tracking for monitoring existing job
    unset LOGGED_MILESTONES
    declare -gA LOGGED_MILESTONES
    
    # Set timestamp to now for log monitoring
    JOB_START_TIMESTAMP=$(date -u -d "1 hour ago" +"%Y-%m-%dT%H:%M:%SZ")
    
    while [ $elapsed -lt $max_wait ]; do
        local current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        local remaining=$((max_wait - elapsed))
        
        # Check if jobs are still running
        running_items=$(check_running_jobs)
        
        if [ -z "$running_items" ]; then
            echo ""
            log_success "All existing jobs have completed!"
            log_info "Waited for $elapsed seconds ($((elapsed / 60)) min) for existing jobs."
            
            # Wait a brief moment to ensure cleanup is done
            log_info "Waiting 30 seconds for post-job cleanup..."
            sleep 30
            return 0
        fi
        
        # Show progress milestones for the running job
        local pod_name=$(get_data_loader_pod)
        if [ -n "$pod_name" ]; then
            display_job_progress "$pod_name"
            
            # Also check completion status
            if check_job_completion "$pod_name" 2>/dev/null; then
                echo ""
                log_success "Existing job appears to have completed based on log patterns!"
                sleep 30
                return 0
            fi
        fi
        
        # Show timer every minute
        if [ $((elapsed % 60)) -lt $check_interval ]; then
            printf "\r  ${CYAN}⏳ Waiting for existing job:${NC} Elapsed: %dm%ds | Remaining: %dm%ds     " \
                $((elapsed / 60)) $((elapsed % 60)) \
                $((remaining / 60)) $((remaining % 60))
        fi
        
        sleep $check_interval
    done
    
    echo ""
    log_warn "Timeout reached waiting for existing jobs. They may still be running."
    log_warn "Currently running:"
    running_items=$(check_running_jobs)
    echo "$running_items" | while read -r item; do
        if [ -n "$item" ]; then
            echo -e "  ${YELLOW}→${NC} $item"
        fi
    done
    
    # Ask whether to proceed or abort
    log_warn "Proceeding anyway. This may cause conflicts if multiple jobs run simultaneously."
    return 0
}

# Create and monitor job
create_data_loader_job() {
    local iteration=$1
    local job_name="cron-nx-cg-data-loader-manual-trigger-${iteration}-$(date +%Y-%m-%d-%H-%M-%S)"
    
    log_info "Creating job: $job_name"
    
    if kubectl create job --from=cronjob/"$CRONJOB_NAME" "$job_name" -n "$NAMESPACE" 2>&1; then
        log_success "Job '$job_name' created successfully."
        
        # Wait a few seconds for job to start
        sleep 5
        
        # Check job status
        local job_status=$(kubectl get job -n "$NAMESPACE" "$job_name" -o jsonpath='{.status.conditions[0].type}' 2>/dev/null)
        log_info "Job status: ${job_status:-Pending}"
        
        # Get pod name for the job
        local pod_name=$(kubectl get pods -n "$NAMESPACE" -l job-name="$job_name" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        if [ -n "$pod_name" ]; then
            log_info "Job pod: $pod_name"
        fi
        
        return 0
    else
        log_error "Failed to create job '$job_name'."
        return 1
    fi
}

# Sleep with progress indicator
sleep_with_progress() {
    local total_seconds=$1
    local interval=100
    local iterations=$((total_seconds / interval))
    local remaining=$((total_seconds % interval))
    
    log_info "Sleeping for $total_seconds seconds ($((total_seconds / 60)) minutes)..."
    
    for j in $(seq 1 $iterations); do
        local elapsed=$((j * interval))
        local remaining_time=$((total_seconds - elapsed))
        local percent=$((elapsed * 100 / total_seconds))
        
        printf "\r${GREEN}Progress:${NC} %3d%% | Elapsed: %dm%ds | Remaining: %dm%ds" \
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

# Get the data loader pod name (try multiple methods)
get_data_loader_pod() {
    local pod_name=""
    
    # Method 1: Try by pod name pattern for deployment pods (nx-cg-data-loader-*)
    # Look for Running pods first
    pod_name=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | tr ' ' '\n' | grep "^nx-cg-data-loader-" | head -1)
    
    # Method 2: If no running pod, try any pod with that name (might be starting up)
    if [ -z "$pod_name" ]; then
        pod_name=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | tr ' ' '\n' | grep "^nx-cg-data-loader-" | head -1)
    fi
    
    # Method 3: Try deployment label selector
    if [ -z "$pod_name" ]; then
        pod_name=$(kubectl get pods -n "$NAMESPACE" -l app="$DATA_LOADER_DEPLOYMENT" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    fi
    
    # Method 4: Try cronjob pod name pattern
    if [ -z "$pod_name" ]; then
        pod_name=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null | tr ' ' '\n' | grep "cron-nx-cg-data-loader" | head -1)
    fi
    
    echo "$pod_name"
}

# Check if all completion patterns are found in logs since job started
check_job_completion() {
    local pod_name=$1
    
    if [ -z "$pod_name" ]; then
        log_warn "Data loader pod not found"
        return 1
    fi
    
    if [ -z "$JOB_START_TIMESTAMP" ]; then
        log_warn "Job start timestamp not set"
        return 1
    fi
    
    # Get logs since the job started (using --since-time for fresh logs per cronjob)
    local logs
    logs=$(kubectl logs -n "$NAMESPACE" "$pod_name" --since-time="$JOB_START_TIMESTAMP" 2>/dev/null)
    
    if [ -z "$logs" ]; then
        return 1
    fi
    
    # Job types to track for completion status
    local job_types=("CLUSTER_CONFIG" "CATEGORIES_CONFIG" "VM_CONFIG" "CLUSTER_HARDWARE_CONFIG" "NX_ROUTINE_WORKFLOW")
    local completed_jobs=()
    local pending_jobs=()
    
    # Check each job type for completion
    for job_type in "${job_types[@]}"; do
        if grep -q "$job_type completed successfully" <<< "$logs" || \
           ([ "$job_type" = "NX_ROUTINE_WORKFLOW" ] && grep -q "Updating service backfill status for Service :\[NX_ROUTINE_WORKFLOW\]" <<< "$logs"); then
            completed_jobs+=("$job_type")
            
            # Log completion message only once
            local completion_msg_key="${job_type}_completion_msg"
            if [ -z "${LOGGED_MILESTONES[$completion_msg_key]}" ]; then
                echo -e "  ${GREEN}✓ $job_type is completed${NC}"
                LOGGED_MILESTONES[$completion_msg_key]=1
            fi
        else
            pending_jobs+=("$job_type")
        fi
    done
    
    # Show progress: completed/total (only show if there's progress)
    local completed_count=${#completed_jobs[@]}
    local total_jobs=${#job_types[@]}
    
    if [ $completed_count -gt 0 ]; then
        log_info "Job Progress: $completed_count/$total_jobs jobs completed"
    else
        log_info "Waiting for job completion..."
    fi
    
    # Show pending/missed jobs at the bottom (only if there are some)
    if [ ${#pending_jobs[@]} -gt 0 ] && [ ${#pending_jobs[@]} -lt $total_jobs ]; then
        echo -e "  ${YELLOW}⏳ Pending:${NC} ${pending_jobs[*]}"
    fi
    
    # All completed if no pending jobs
    if [ ${#pending_jobs[@]} -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Track which milestones have been logged to avoid duplicates
declare -A LOGGED_MILESTONES

# Parse and display job progress milestones from logs
display_job_progress() {
    local pod_name=$1
    
    if [ -z "$pod_name" ] || [ -z "$JOB_START_TIMESTAMP" ]; then
        return
    fi
    
    local logs
    logs=$(kubectl logs -n "$NAMESPACE" "$pod_name" --since-time="$JOB_START_TIMESTAMP" 2>/dev/null)
    
    if [ -z "$logs" ]; then
        return
    fi
    
    # Job types to track
    local job_types=("CATEGORIES_CONFIG" "VM_CONFIG" "CLUSTER_HARDWARE_CONFIG" "CLUSTER_CONFIG")
    
    for job_type in "${job_types[@]}"; do
        # Milestone 1: Processing job started (Pattern: "Processing job: CATEGORIES_CONFIG")
        local processing_key="${job_type}_processing"
        if [ -z "${LOGGED_MILESTONES[$processing_key]}" ]; then
            if grep -q "Processing job: $job_type" <<< "$logs"; then
                echo -e "  ${CYAN}▶${NC} Started processing: ${YELLOW}$job_type${NC}"
                LOGGED_MILESTONES[$processing_key]=1
            fi
        fi
        
        # Milestone 2: Fetching data for dates (Pattern: "Fetching data for date: 2025-12-21 for : CATEGORIES_CONFIG")
        local fetching_key="${job_type}_fetching"
        if [ -z "${LOGGED_MILESTONES[$fetching_key]}" ]; then
            local dates=$(grep "Fetching data for date:.*for : $job_type" <<< "$logs" | sed 's/.*Fetching data for date: \([0-9-]*\) for.*/\1/' | sort -u | tr '\n' ',' | sed 's/,$//')
            if [ -n "$dates" ]; then
                echo -e "  ${CYAN}📅${NC} $job_type fetching dates: ${GREEN}$dates${NC}"
                LOGGED_MILESTONES[$fetching_key]=1
            fi
        fi
        
        # Milestone 3: Dropping partition data (Pattern: "dropping partition data for backfill job [CATEGORIES_CONFIG]")
        local dropping_key="${job_type}_dropping"
        if [ -z "${LOGGED_MILESTONES[$dropping_key]}" ]; then
            if grep -q "dropping partition data for backfill job \[$job_type\]" <<< "$logs"; then
                echo -e "  ${CYAN}🗑${NC}  $job_type: Dropping partition data"
                LOGGED_MILESTONES[$dropping_key]=1
            fi
        fi
        
        # Milestone 4: Start writing to tables
        local writing_key="${job_type}_writing"
        if [ -z "${LOGGED_MILESTONES[$writing_key]}" ]; then
            local write_pattern=""
            case "$job_type" in
                "CATEGORIES_CONFIG") write_pattern="Start writing to Category Metrics Tables" ;;
                "VM_CONFIG") write_pattern="Start writing to Vm Metrics Tables" ;;
                "CLUSTER_HARDWARE_CONFIG") write_pattern="Start writing to Cluster Hardware Metrics Tables" ;;
                "CLUSTER_CONFIG") write_pattern="Start writing to Cluster Metrics Tables" ;;
            esac
            if grep -q "$write_pattern" <<< "$logs"; then
                echo -e "  ${CYAN}✍${NC}  $job_type: Writing to ClickHouse tables"
                LOGGED_MILESTONES[$writing_key]=1
            fi
        fi
        
        # Milestone 5: Written to ClickHouse (Pattern: "Written 25781464 to clickhouse")
        local written_key="${job_type}_written"
        if [ -z "${LOGGED_MILESTONES[$written_key]}" ] && [ -n "${LOGGED_MILESTONES[${job_type}_writing]}" ]; then
            local write_pattern=""
            case "$job_type" in
                "CATEGORIES_CONFIG") write_pattern="Start writing to Category Metrics Tables" ;;
                "VM_CONFIG") write_pattern="Start writing to Vm Metrics Tables" ;;
                "CLUSTER_HARDWARE_CONFIG") write_pattern="Start writing to Cluster Hardware Metrics Tables" ;;
                "CLUSTER_CONFIG") write_pattern="Start writing to Cluster Metrics Tables" ;;
            esac
            # Look for the Written line after the Start writing line
            local written_count=$(grep -A10 "$write_pattern" <<< "$logs" | grep "Written.*to clickhouse" | head -1 | sed 's/.*Written \([0-9]*\) to clickhouse.*/\1/')
            if [ -n "$written_count" ] && [ "$written_count" -gt 0 ] 2>/dev/null; then
                echo -e "  ${CYAN}💾${NC} $job_type: Written ${GREEN}$(printf "%'d" $written_count)${NC} records to ClickHouse"
                LOGGED_MILESTONES[$written_key]=1
            fi
        fi
        
        # Milestone 6: Marked as completed in PG (Pattern: "Updating service backfill status for Service :[CATEGORIES_CONFIG]")
        local completed_key="${job_type}_pg_completed"
        if [ -z "${LOGGED_MILESTONES[$completed_key]}" ]; then
            if grep -q "Updating service backfill status for Service :\[$job_type\]" <<< "$logs"; then
                echo -e "  ${CYAN}✅${NC} $job_type: Backfill status updated in PG"
                LOGGED_MILESTONES[$completed_key]=1
            fi
        fi
        
        # Milestone 7: Marked as completed (Pattern: "1 marked as completed updated in PG")
        local marked_key="${job_type}_marked"
        if [ -z "${LOGGED_MILESTONES[$marked_key]}" ] && [ -n "${LOGGED_MILESTONES[${job_type}_pg_completed]}" ]; then
            if grep -q "marked as completed updated in PG" <<< "$logs"; then
                echo -e "  ${CYAN}📝${NC} $job_type: Marked as completed in PG"
                LOGGED_MILESTONES[$marked_key]=1
            fi
        fi
        
        # Milestone 8: Temp file deleted (Pattern: "temp file for executor CATEGORIES_CONFIG deleted successfully")
        local cleanup_key="${job_type}_cleanup"
        if [ -z "${LOGGED_MILESTONES[$cleanup_key]}" ]; then
            if grep -q "temp file for executor $job_type deleted successfully" <<< "$logs"; then
                echo -e "  ${CYAN}🧹${NC} $job_type: Cleanup complete"
                LOGGED_MILESTONES[$cleanup_key]=1
            fi
        fi
        
    done
    
    # Track NX_ROUTINE_WORKFLOW milestones separately (it's a special job type)
    local nx_routine_key="NX_ROUTINE_WORKFLOW_processing"
    if [ -z "${LOGGED_MILESTONES[$nx_routine_key]}" ]; then
        if grep -q "Processing job: NX_ROUTINE_WORKFLOW\|Starting NX_ROUTINE_WORKFLOW" <<< "$logs"; then
            echo -e "  ${CYAN}▶${NC} Started processing: ${YELLOW}NX_ROUTINE_WORKFLOW${NC}"
            LOGGED_MILESTONES[$nx_routine_key]=1
        fi
    fi
    
    # Also track Number of backfill jobs
    local backfill_jobs_key="backfill_jobs_count"
    if [ -z "${LOGGED_MILESTONES[$backfill_jobs_key]}" ]; then
        local job_count=$(grep "Number of backfill jobs to process in workflow:" <<< "$logs" | sed 's/.*workflow: \([0-9]*\).*/\1/' | head -1)
        if [ -n "$job_count" ] && [ "$job_count" != "0" ]; then
            echo -e "  ${CYAN}📋${NC} Backfill jobs to process: ${YELLOW}$job_count${NC}"
            LOGGED_MILESTONES[$backfill_jobs_key]=1
        fi
    fi
}

# Monitor logs and wait for completion or timeout
wait_for_job_completion() {
    local start_time=$(date +%s)
    local elapsed=0
    local pod_name
    local last_progress_time=0
    
    log_section "Monitoring Data Loader Job"
    
    # Reset milestone tracking for this new job iteration
    unset LOGGED_MILESTONES
    declare -gA LOGGED_MILESTONES
    
    # Set the job start timestamp for fresh log retrieval (ISO 8601 format)
    JOB_START_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    log_info "Job start timestamp: $JOB_START_TIMESTAMP"
    
    # Wait for pod to be ready (with retries)
    log_info "Waiting for data loader pod to be ready..."
    local max_pod_wait=120  # Wait up to 2 minutes for pod
    local pod_wait_elapsed=0
    
    while [ $pod_wait_elapsed -lt $max_pod_wait ]; do
        sleep 10
        pod_wait_elapsed=$((pod_wait_elapsed + 10))
        
        pod_name=$(get_data_loader_pod)
        if [ -n "$pod_name" ]; then
            break
        fi
        
        log_info "Waiting for pod... ($pod_wait_elapsed/$max_pod_wait seconds)"
        
        # Debug: Show available pods in namespace
        if [ $pod_wait_elapsed -ge 30 ]; then
            log_info "Available pods in $NAMESPACE:"
            kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | head -5 | while read line; do
                echo "    $line"
            done
        fi
    done
    
    if [ -z "$pod_name" ]; then
        log_warn "Could not find data loader pod after ${max_pod_wait}s. Will use timeout-based waiting."
        log_info "Available pods:"
        kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | while read line; do
            echo "    $line"
        done
        sleep_with_progress $SLEEP_DURATION
        return 0
    fi
    
    log_info "Monitoring pod: $pod_name"
    log_info "Looking for ${#COMPLETION_PATTERNS[@]} completion patterns"
    log_info "Checking every $LOG_CHECK_INTERVAL seconds"
    log_info "Max wait time: $SLEEP_DURATION seconds ($((SLEEP_DURATION / 60)) minutes)"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  JOB PROGRESS${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    
    # Monitor logs
    while [ $elapsed -lt $SLEEP_DURATION ]; do
        # Calculate time since job started
        local current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        local remaining=$((SLEEP_DURATION - elapsed))
        
        # Re-fetch pod name in case it changed
        pod_name=$(get_data_loader_pod)
        
        if [ -z "$pod_name" ]; then
            log_warn "Data loader pod not found. Waiting..."
            sleep $LOG_CHECK_INTERVAL
            continue
        fi
        
        # Display job progress milestones (only new ones will be shown)
        display_job_progress "$pod_name"
        
        # Check if all jobs completed (using fresh logs since JOB_START_TIMESTAMP)
        if check_job_completion "$pod_name"; then
            echo ""
            echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
            log_success "All data loader jobs completed successfully!"
            echo ""
            log_info "Waiting $WAIT_AFTER_COMPLETION seconds ($(( WAIT_AFTER_COMPLETION / 60 )) min) before next iteration..."
            sleep $WAIT_AFTER_COMPLETION
            return 0
        fi
        
        # Show progress timer (less frequently to avoid clutter)
        if [ $((elapsed - last_progress_time)) -ge 60 ]; then
            echo ""
            printf "  ${CYAN}⏱️  Elapsed:${NC} %dm%ds | ${CYAN}Remaining:${NC} %dm%ds\n" \
                $((elapsed / 60)) $((elapsed % 60)) \
                $((remaining / 60)) $((remaining % 60))
            last_progress_time=$elapsed
        fi
        
        sleep $LOG_CHECK_INTERVAL
    done
    
    echo ""
    log_warn "Timeout reached ($SLEEP_DURATION seconds). Proceeding to next iteration."
    return 0
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
LOG_FILE="data_loader_$(date +%Y-%m-%d_%H-%M-%S).log"

# Redirect all output (stdout + stderr) to log file AND console
exec > >(tee -a "$LOG_FILE") 2>&1

log_section "Starting Data Loader Script"
log_info "Logs will be saved to: $LOG_FILE"
log_info "Configuration:"
echo "  - Namespace: $NAMESPACE"
echo "  - Datastore Namespace: $DATASTORE_NAMESPACE"
echo "  - PostgreSQL Pod: $PG_POD"
echo "  - Database: $DATABASE"
echo "  - CronJob: $CRONJOB_NAME"
echo "  - Data Loader Deployment: $DATA_LOADER_DEPLOYMENT"
echo "  - Iterations: $ITERATIONS"
echo "  - Max Wait Duration: $SLEEP_DURATION seconds ($((SLEEP_DURATION / 60)) minutes)"
echo "  - Wait After Completion: $WAIT_AFTER_COMPLETION seconds ($((WAIT_AFTER_COMPLETION / 60)) minutes)"
echo "  - Log Check Interval: $LOG_CHECK_INTERVAL seconds"
echo "  - Backfill Hours: $BACKFILL_HOURS"
echo "  - Completion Patterns:"
for pattern in "${COMPLETION_PATTERNS[@]}"; do
    echo "    * $pattern"
done

# Check prerequisites
check_prerequisites

# Check for any running jobs on startup
log_section "Initial Job Status Check"
if check_running_jobs >/dev/null 2>&1; then
    log_warn "Detected running data loader job(s) on startup!"
    running_items=$(check_running_jobs)
    echo "$running_items" | while read -r item; do
        if [ -n "$item" ]; then
            echo -e "  ${YELLOW}→${NC} $item"
        fi
    done
    log_info "Will wait for existing job(s) to complete before starting first iteration."
else
    log_success "No running jobs detected. Ready to start."
fi

# Statistics
SUCCESS_COUNT=0
FAILURE_COUNT=0
START_TIME=$(date +%s)

# Check for and wait for any existing running jobs before starting
# wait_for_existing_jobs

# Main loop
for i in $(seq 1 $ITERATIONS); do
    log_section "Iteration $i of $ITERATIONS"
    ITERATION_START=$(date +%s)
    
    # Query initial status
    if ! query_backfill_status; then
        log_error "Failed to query initial backfill status."
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        continue
    fi
    
    # Calculate epoch time (8 hours ago in milliseconds)
    BACKFILL_MS=$((BACKFILL_HOURS * 3600 * 1000))
    EPOCH_MS=$(($(date +%s%3N) - BACKFILL_MS))
    log_info "Calculated backfill epoch: $EPOCH_MS ($(date -d @$((EPOCH_MS / 1000)) '+%Y-%m-%d %H:%M:%S'))"
    
    # Check if last_persisted_epoch or last_completed_date is already older than 8 hours
    log_info "Checking if backfill status already needs updating..."
    CURRENT_LAST_PERSISTED=$(kubectl exec -n "$DATASTORE_NAMESPACE" "$PG_POD" -- \
        psql -d "$DATABASE" -t -c "SELECT last_persisted_epoch FROM nutanix_backfill_job_run_status LIMIT 1;" 2>&1 | tr -d ' ')
    CURRENT_LAST_COMPLETED=$(kubectl exec -n "$DATASTORE_NAMESPACE" "$PG_POD" -- \
        psql -d "$DATABASE" -t -c "SELECT last_completed_date FROM nutanix_backfill_job_run_status LIMIT 1;" 2>&1 | tr -d ' ')
    
    # Check if values are valid numbers
    if [[ "$CURRENT_LAST_PERSISTED" =~ ^[0-9]+$ ]] && [[ "$CURRENT_LAST_COMPLETED" =~ ^[0-9]+$ ]]; then
        log_info "Current last_persisted_epoch: $CURRENT_LAST_PERSISTED ($(date -d @$((CURRENT_LAST_PERSISTED / 1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'invalid date'))"
        log_info "Current last_completed_date: $CURRENT_LAST_COMPLETED ($(date -d @$((CURRENT_LAST_COMPLETED / 1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'invalid date'))"
        
        # Check if either value is already older than 8 hours (less than EPOCH_MS)
        if [ "$CURRENT_LAST_PERSISTED" -le "$EPOCH_MS" ] || [ "$CURRENT_LAST_COMPLETED" -le "$EPOCH_MS" ]; then
            log_warn "Backfill status is already older than $BACKFILL_HOURS hours. Skipping update."
            log_info "Current values are already at or before the target backfill time."
        else
            # Update backfill status
            if ! update_backfill_status "$EPOCH_MS"; then
                log_error "Failed to update backfill status. Skipping this iteration."
                FAILURE_COUNT=$((FAILURE_COUNT + 1))
                continue
            fi
        fi
    else
        log_warn "Could not retrieve valid current backfill values. Proceeding with update."
        # Update backfill status
        if ! update_backfill_status "$EPOCH_MS"; then
            log_error "Failed to update backfill status. Skipping this iteration."
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
            continue
        fi
    fi
    
    # Create data loader job
    if ! create_data_loader_job "$i"; then
        log_error "Failed to create data loader job. Skipping this iteration."
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
        continue
    fi
    
    # Query status after job creation
    log_info "Checking backfill status after job creation..."
    query_backfill_status
    
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    
    ITERATION_END=$(date +%s)
    ITERATION_DURATION=$((ITERATION_END - ITERATION_START))
    log_success "Iteration $i job triggered in $ITERATION_DURATION seconds."
    
    # Wait for job completion or timeout (skip on last iteration)
    if [ $i -lt $ITERATIONS ]; then
        wait_for_job_completion
    fi
done

# ============================================
# Final Summary
# ============================================

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

log_section "Data Loader Script Completed"
log_info "Summary:"
echo "  - Total Iterations: $ITERATIONS"
echo "  - Successful: $SUCCESS_COUNT"
echo "  - Failed: $FAILURE_COUNT"
echo "  - Total Duration: $((TOTAL_DURATION / 60)) minutes ($TOTAL_DURATION seconds)"
echo "  - Average per Iteration: $((TOTAL_DURATION / ITERATIONS)) seconds"
echo "  - Log File: $LOG_FILE"

if [ $FAILURE_COUNT -eq 0 ]; then
    log_success "All iterations completed successfully!"
    exit 0
else
    log_warn "$FAILURE_COUNT iteration(s) failed. Check logs for details."
    exit 1
fi
