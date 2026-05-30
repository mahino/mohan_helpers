#!/bin/bash

# Quick script to check progress of running nutanix password reset
TEMP_DIR_PATTERN="/tmp/nutanix_reset_*"

echo "========================================"
echo "  Nutanix Password Reset Progress Check"
echo "  $(date)"
echo "========================================"

# Find active temp directories
temp_dirs=($(ls -d $TEMP_DIR_PATTERN 2>/dev/null))

if [ ${#temp_dirs[@]} -eq 0 ]; then
    echo "[INFO] No active nutanix password reset sessions found."
    exit 0
fi

for temp_dir in "${temp_dirs[@]}"; do
    echo
    echo "Session: $temp_dir"
    echo "----------------------------------------"
    
    # Count log files
    log_files=($(ls "$temp_dir"/*.log 2>/dev/null))
    result_files=($(ls "$temp_dir"/*.result 2>/dev/null))
    
    total_jobs=${#log_files[@]}
    completed_jobs=${#result_files[@]}
    in_progress=$((total_jobs - completed_jobs))
    
    echo "Total PEs: $total_jobs"
    echo "Completed: $completed_jobs"
    echo "In Progress: $in_progress"
    
    if [ $completed_jobs -gt 0 ]; then
        echo
        echo "Completed Results:"
        for result_file in "${result_files[@]}"; do
            pe_info=$(basename "$result_file" .log.result | sed 's/pe_[0-9]*_//; s/_/./g')
            result_line=$(cat "$result_file" 2>/dev/null)
            if [[ "$result_line" == RESULT:SUCCESS:* ]]; then
                echo "  ✅ $pe_info: SUCCESS"
            else
                echo "  ❌ $pe_info: FAILED"
            fi
        done
    fi
    
    if [ $in_progress -gt 0 ]; then
        echo
        echo "Still Running:"
        for log_file in "${log_files[@]}"; do
            result_file="$log_file.result"
            if [ ! -f "$result_file" ]; then
                pe_info=$(basename "$log_file" .log | sed 's/pe_[0-9]*_//; s/_/./g')
                if [ -f "$log_file" ]; then
                    last_line=$(tail -1 "$log_file" 2>/dev/null)
                    echo "  🔄 $pe_info: $last_line"
                else
                    echo "  ⏳ $pe_info: Starting..."
                fi
            fi
        done
    fi
done

echo
echo "========================================"

# Show running background jobs
running_jobs=$(jobs -r 2>/dev/null | wc -l)
if [ $running_jobs -gt 0 ]; then
    echo "Active background jobs: $running_jobs"
    jobs -r 2>/dev/null
else
    echo "No active background jobs found."
fi

echo "========================================"