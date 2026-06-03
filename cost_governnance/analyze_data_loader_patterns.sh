#!/bin/bash

set -o pipefail

# ============================================================
# Data Loader Log Pattern Checker
# - Does NOT trigger jobs
# - Only checks patterns in an existing log file
# ============================================================

# Completion patterns (all expected for full completion)
COMPLETION_PATTERNS=(
    "CLUSTER_CONFIG completed successfully"
    "CATEGORIES_CONFIG completed successfully"
    "VM_CONFIG completed successfully"
    "CLUSTER_HARDWARE_CONFIG completed successfully"
    "Updating service backfill status for Service :\\[CLUSTER_CONFIG\\]"
    "Updating service backfill status for Service :\\[NX_ROUTINE_WORKFLOW\\]"
    "Updating service backfill status for Service :\\[CATEGORIES_CONFIG\\]"
    "Updating service backfill status for Service :\\[VM_CONFIG\\]"
    "Updating service backfill status for Service :\\[CLUSTER_HARDWARE_CONFIG\\]"
)

JOB_TYPES=("CLUSTER_CONFIG" "CATEGORIES_CONFIG" "VM_CONFIG" "CLUSTER_HARDWARE_CONFIG" "NX_ROUTINE_WORKFLOW")

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    cat <<'EOF'
Usage:
  check_data_loader_patterns.sh [--watch] [--interval <sec>] [--quiet] [--file <log_file>]

Options:
  --file <path>      Optional override log file path
  --watch            Re-check continuously until Ctrl+C
  --interval <sec>   Watch interval in seconds (default: 15)
  --quiet            Print compact output only
  -h, --help         Show this help

Examples:
  ./check_data_loader_patterns.sh
  ./check_data_loader_patterns.sh --watch --interval 10
EOF
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

DEFAULT_LOG_FILE="/Users/mohan.as1/workspace/mohan_helpers/cost_governnance/data-loader-log-fil.txt"
LOG_FILE="$DEFAULT_LOG_FILE"
WATCH_MODE=false
INTERVAL=15
QUIET=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --file)
            LOG_FILE="$2"
            shift 2
            ;;
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
done

if [[ ! -f "$LOG_FILE" ]]; then
    log_error "Log file not found: $LOG_FILE"
    exit 1
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || [[ "$INTERVAL" -le 0 ]]; then
    log_error "--interval must be a positive integer"
    exit 1
fi

analyze_once() {
    local logs
    logs="$(<"$LOG_FILE")"

    local matched=0
    local total=${#COMPLETION_PATTERNS[@]}

    local completed_jobs=()
    local pending_jobs=()

    if [[ "$QUIET" = false ]]; then
        print_section "Pattern Analysis: $LOG_FILE"
        echo "Checked at: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "Completion patterns:"
    fi

    for pattern in "${COMPLETION_PATTERNS[@]}"; do
        if grep -q "$pattern" <<< "$logs"; then
            ((matched++))
            [[ "$QUIET" = false ]] && echo -e "  ${GREEN}✓${NC} $pattern"
        else
            [[ "$QUIET" = false ]] && echo -e "  ${RED}✗${NC} $pattern"
        fi
    done

    for job in "${JOB_TYPES[@]}"; do
        if grep -q "$job completed successfully" <<< "$logs" || \
           ([[ "$job" = "NX_ROUTINE_WORKFLOW" ]] && grep -q "Updating service backfill status for Service :\\[$job\\]" <<< "$logs"); then
            completed_jobs+=("$job")
        else
            pending_jobs+=("$job")
        fi
    done

    if [[ "$QUIET" = false ]]; then
        echo ""
        echo "Job completion summary:"
        echo -e "  ${GREEN}Completed (${#completed_jobs[@]}):${NC} ${completed_jobs[*]:-none}"
        echo -e "  ${YELLOW}Pending (${#pending_jobs[@]}):${NC} ${pending_jobs[*]:-none}"

        echo ""
        echo "Milestones:"
        local backfill_count
        backfill_count="$(grep "Number of backfill jobs to process in workflow:" <<< "$logs" | sed -n 's/.*workflow: \([0-9][0-9]*\).*/\1/p' | head -1)"
        if [[ -n "$backfill_count" ]]; then
            echo -e "  ${GREEN}✓${NC} Backfill jobs count seen: $backfill_count"
        else
            echo -e "  ${YELLOW}~${NC} Backfill jobs count not found"
        fi
    fi

    local percent=$((matched * 100 / total))
    if [[ "$QUIET" = false ]]; then
        echo ""
    fi

    if [[ "$matched" -eq "$total" ]]; then
        echo -e "${GREEN}RESULT:${NC} COMPLETE ($matched/$total patterns, ${percent}%)"
        return 0
    fi

    echo -e "${YELLOW}RESULT:${NC} INCOMPLETE ($matched/$total patterns, ${percent}%)"
    return 2
}

if [[ "$WATCH_MODE" = true ]]; then
    log_info "Watch mode enabled. File: $LOG_FILE | Interval: ${INTERVAL}s"
    while true; do
        clear
        analyze_once
        sleep "$INTERVAL"
    done
else
    analyze_once
    exit $?
fi

