#!/bin/bash

# Nutanix Password Reset Script - Parallel Processing Version
# This script resets admin password using multiple password attempts in parallel

# Configuration
SSH_USER="nutanix"
SSH_PASS="RDMCluster.123"
MAX_PARALLEL_JOBS=5  # Maximum number of PEs to process simultaneously
TEMP_DIR="/tmp/nutanix_reset_$$"

# Password list to try
PASSWORDS=(
    "Nuteanix.1234"
    "Nu2tanix.234"
    "Nut2anix.345"
    "Nutfanix.456"
    "Nutanix.123"
)

# Function to reset password on a single PE (runs in parallel)
reset_password_pe() {
    local PE_IP="$1"
    local pe_number="$2"
    local total_pes="$3"
    local log_file="$4"
    
    # Redirect all output to log file
    exec > "$log_file" 2>&1
    
    echo "========================================"
    echo "  Processing PE $pe_number/$total_pes"
    echo "  PE IP: $PE_IP"
    echo "  Started at: $(date)"
    echo "========================================"
    echo
    
    # Use local error handling for this function
    set +e
    
    # Test connection with timeout
    echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Testing connection..."
    if ! timeout 30 sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$PE_IP" "echo 'Connection successful'" 2>/dev/null; then
        echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): Failed to connect (timeout or connection refused)"
        echo "RESULT:FAILED:CONNECTION_FAILED" >> "$log_file.result"
        return 1
    fi
    echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): Connection successful"
    echo
    
    # Try each password
    local success_count=0
    local first_success_password=""
    for i in "${!PASSWORDS[@]}"; do
        local password="${PASSWORDS[$i]}"
        local attempt=$((i + 1))
        
        echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Password reset attempt $attempt/6"
        echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Trying password: ${password}"
        
        # Execute password reset command with timeout
        reset_cmd="~/prism/cli/ncli user reset-password user-name=admin password=\"$password\""
        echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Command: ncli user reset-password user-name=admin password=***"
        
        reset_output=$(timeout 60 sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_USER@$PE_IP" "$reset_cmd" 2>&1)
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): ✅ Password reset successful with attempt $attempt"
            echo "Output: $reset_output"
            ((success_count++))
            if [ -z "$first_success_password" ]; then
                first_success_password="$password"
            fi
        else
            echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): ❌ Password reset failed with attempt $attempt"
            echo "Error: $reset_output"
        fi
        
        echo
        
    done
    
    echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Password reset summary: $success_count/6 attempts successful"
    echo "Completed at: $(date)"
    echo "================================================================"
    echo
    
    # Write result to result file
    if [ $success_count -gt 0 ]; then
        echo "RESULT:SUCCESS:$success_count:$first_success_password" >> "$log_file.result"
        return 0
    else
        echo "RESULT:FAILED:NO_PASSWORDS_WORKED" >> "$log_file.result"
        return 1
    fi
}

# Function to check job progress by examining log files
check_job_progress() {
    local total_pes="$1"
    local completed=0
    local in_progress=0
    local not_started=0
    
    for i in $(seq 1 $total_pes); do
        local pe_ip="${PE_LIST[$((i-1))]}"
        local log_file="$TEMP_DIR/pe_${i}_${pe_ip//\./_}.log"
        local result_file="$log_file.result"
        
        if [ -f "$result_file" ]; then
            ((completed++))
        elif [ -f "$log_file" ] && [ -s "$log_file" ]; then
            ((in_progress++))
        else
            ((not_started++))
        fi
    done
    
    local total_elapsed=$(($(date +%s) - start_time))
    local total_minutes=$((total_elapsed / 60))
    local total_seconds=$((total_elapsed % 60))
    
    echo
    echo "[INFO] ✅ All parallel jobs completed in ${total_minutes}m ${total_seconds}s"
    echo
}

# Cleanup function
cleanup() {
    echo
    echo "[INFO] 🧹 Cleaning up temporary files..."
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
    # Kill any remaining background jobs
    jobs -p | xargs -r kill 2>/dev/null
}

# Set trap for cleanup on exit
trap cleanup EXIT INT TERM

# Main script logic
if [ $# -eq 0 ]; then
    echo "Usage: $0 <PE_IP1> [PE_IP2] [PE_IP3] ..."
    echo "   or: $0 \"10.122.27.47 10.122.27.76 10.122.27.128\""
    echo
    echo "Examples:"
    echo "  $0 10.122.27.88"
    echo "  $0 10.122.27.47 10.122.27.76 10.122.27.128"
    echo "  $0 \"10.122.27.47 10.122.27.76 10.122.27.128 10.122.27.140\""
    echo
    echo "Configuration:"
    echo "  Max parallel jobs: $MAX_PARALLEL_JOBS"
    echo "  Passwords to try: 6"
    for i in "${!PASSWORDS[@]}"; do
        local password="${PASSWORDS[$i]}"
        echo "    $((i + 1)). ${password:0:3}***"
    done
    exit 1
fi

# Handle space-separated IPs in a single argument
if [ $# -eq 1 ] && [[ "$1" == *" "* ]]; then
    # Split space-separated string into array
    read -ra PE_LIST <<< "$1"
else
    # Use all arguments as separate IPs
    PE_LIST=("$@")
fi

total_pes=${#PE_LIST[@]}

# Create temporary directory for logs
mkdir -p "$TEMP_DIR"

echo "========================================"
echo "  Nutanix Password Reset Script - PARALLEL"
echo "  Started at: $(date)"
echo "========================================"
echo "DEBUG: Number of arguments received: $#"
echo "DEBUG: All arguments: $*"
echo "Total PEs to process: $total_pes"
echo "PE List: ${PE_LIST[*]}"
echo "Max parallel jobs: $MAX_PARALLEL_JOBS"
echo "Password attempts per PE: 6"
echo "Temporary logs: $TEMP_DIR"
echo "========================================"
echo

# Start parallel processing
echo "[INFO] 🚀 Starting parallel password reset for $total_pes PEs..."
echo "[INFO] 📊 Processing up to $MAX_PARALLEL_JOBS PEs simultaneously"
echo

job_count=0
started_jobs=0
completed_jobs=0

for i in "${!PE_LIST[@]}"; do
    PE_IP="${PE_LIST[$i]}"
    pe_number=$((i + 1))
    log_file="$TEMP_DIR/pe_${pe_number}_${PE_IP//\./_}.log"
    
    echo "[INFO] 🔄 Starting PE $pe_number/$total_pes: $PE_IP (background job)"
    
    # Start background job
    reset_password_pe "$PE_IP" "$pe_number" "$total_pes" "$log_file" &
    ((job_count++))
    ((started_jobs++))
    
    # Limit concurrent jobs
    if [ $job_count -ge $MAX_PARALLEL_JOBS ]; then
        echo "[INFO] ⏸️  Reached max parallel jobs ($MAX_PARALLEL_JOBS), waiting for any to complete..."
        
        # Wait for any job to complete with timeout and progress
        wait_count=0
        while [ $(jobs -r | wc -l) -ge $MAX_PARALLEL_JOBS ] && [ $wait_count -lt 300 ]; do
            sleep 2
            ((wait_count++))
            if [ $((wait_count % 15)) -eq 0 ]; then  # Every 30 seconds
                running_jobs_now=$(jobs -r | wc -l)
                completed_now=$((started_jobs - running_jobs_now))
                echo "[INFO] 📊 Progress: $completed_now/$started_jobs jobs completed, $running_jobs_now still running..."
            fi
        done
        
        # Update job count
        job_count=$(jobs -r | wc -l)
        echo "[INFO] ✅ Job slot available, continuing... (Active jobs: $job_count)"
    fi
    
    # Small delay to avoid overwhelming SSH connections
    sleep 1
done

# Monitor remaining jobs with better feedback
echo "[INFO] 🔄 All jobs started ($started_jobs/$total_pes), waiting for completion..."
wait_start=$(date +%s)
last_update=0

while [ $(jobs -r | wc -l) -gt 0 ]; do
    running_jobs=$(jobs -r | wc -l)
    completed_jobs=$((total_pes - running_jobs))
    elapsed=$(($(date +%s) - wait_start))
    
    # Update every 10 seconds
    if [ $((elapsed - last_update)) -ge 10 ]; then
        minutes=$((elapsed / 60))
        seconds=$((elapsed % 60))
        echo "[INFO] 📊 Progress: $completed_jobs/$total_pes completed, $running_jobs running | Elapsed: ${minutes}m ${seconds}s"
        last_update=$elapsed
        
        # Show some job details every 30 seconds
        if [ $((elapsed % 30)) -eq 0 ] && [ $elapsed -gt 0 ]; then
            echo "[INFO] 🔍 Active jobs: $(jobs -r | wc -l) background processes"
        fi
    fi
    
    sleep 5
done

total_elapsed=$(($(date +%s) - wait_start))
total_minutes=$((total_elapsed / 60))
total_seconds=$((total_elapsed % 60))
echo "[INFO] ✅ All parallel jobs completed in ${total_minutes}m ${total_seconds}s"

echo "[INFO] 📋 Processing results from all PEs..."
echo

# Process results
success_count=0
failed_count=0
failed_pes=()
successful_pes=()

for i in "${!PE_LIST[@]}"; do
    PE_IP="${PE_LIST[$i]}"
    pe_number=$((i + 1))
    log_file="$TEMP_DIR/pe_${pe_number}_${PE_IP//\./_}.log"
    result_file="$log_file.result"
    
    echo "========================================"
    echo "  RESULTS FOR PE $pe_number/$total_pes: $PE_IP"
    echo "========================================"
    
    if [ -f "$result_file" ]; then
        result_line=$(cat "$result_file")
        if [[ "$result_line" == RESULT:SUCCESS:* ]]; then
            IFS=':' read -ra RESULT_PARTS <<< "$result_line"
            success_attempts="${RESULT_PARTS[2]}"
            first_password="${RESULT_PARTS[3]}"
            echo "[SUCCESS] ✅ PE $pe_number/$total_pes ($PE_IP): $success_attempts/6 passwords worked"
            echo "[INFO] 🔑 First successful password: $first_password"
            ((success_count++))
            successful_pes+=("$PE_IP")
        else
            echo "[ERROR] ❌ PE $pe_number/$total_pes ($PE_IP): Failed - $result_line"
            ((failed_count++))
            failed_pes+=("$PE_IP")
        fi
    else
        echo "[ERROR] ❌ PE $pe_number/$total_pes ($PE_IP): No result file found (job may have crashed)"
        ((failed_count++))
        failed_pes+=("$PE_IP")
    fi
    
    # Show last few lines of log for context
    if [ -f "$log_file" ]; then
        echo "[INFO] 📄 Last 3 lines from log:"
        tail -3 "$log_file" | sed 's/^/    /'
    fi
    echo
done

# Final summary
echo "========================================"
echo "  FINAL SUMMARY - PARALLEL EXECUTION"
echo "  Completed at: $(date)"
echo "========================================"
echo "Total PEs processed: $total_pes"
echo "Successful: $success_count"
echo "Failed: $failed_count"

if [ $success_count -gt 0 ]; then
    echo
    echo "✅ Successful PEs:"
    for successful_pe in "${successful_pes[@]}"; do
        echo "  - $successful_pe"
    done
fi

if [ $failed_count -gt 0 ]; then
    echo
    echo "❌ Failed PEs:"
    for failed_pe in "${failed_pes[@]}"; do
        echo "  - $failed_pe"
    done
    echo
    echo "💡 Check individual logs in: $TEMP_DIR"
fi

echo "========================================"

if [ $failed_count -eq 0 ]; then
    echo "[SUCCESS] 🎉 All PEs processed successfully in parallel!"
    echo "========================================"
    echo "SCRIPT COMPLETED - EXITING"
    echo "========================================"
    exit 0
else
    echo "[WARNING] ⚠️  Some PEs failed. Check individual logs for details."
    echo "========================================"
    echo "SCRIPT COMPLETED WITH ERRORS - EXITING"
    echo "========================================"
    exit 1
fi