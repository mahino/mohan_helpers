#!/bin/bash

# Simple Nutanix Cluster Cleanup Script
# Note: Not using 'set -e' to allow individual PE failures without stopping the entire script

# Configuration
SSH_USER="nutanix"
# SSH_PASS="RDMCluster.123"
SSH_PASS="nutanix/4u"

# Function to process a single PE
process_pe() {
    local PE_IP="$1"
    local pe_number="$2"
    local total_pes="$3"
    
    echo "========================================"
    echo "  Processing PE $pe_number/$total_pes"
    echo "  PE IP: $PE_IP"
    echo "========================================"
    echo
    
    # Use local error handling for this function
    set +e  # Disable exit on error for this function

# Test connection
echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Testing connection..."
if ! sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "echo 'Connection successful'" 2>/dev/null; then
    echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): Failed to connect"
    return 1
fi
echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): Connection successful"
echo

# Get cluster information
echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Getting cluster information..."
cluster_output=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "~/prism/cli/ncli multicluster get-cluster-state" 2>/dev/null)
if [ $? -ne 0 ] || [ -z "$cluster_output" ]; then
    echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): Failed to get cluster information"
    return 1
fi
echo "$cluster_output"
echo

# Check if cluster is registered
if echo "$cluster_output" | grep -q "Registered Cluster Count: 0"; then
    echo "[WARNING] PE $pe_number/$total_pes ($PE_IP): No clusters registered - skipping cleanup"
    echo "[INFO] PE $pe_number/$total_pes ($PE_IP): This PE is already unregistered"
    return 0
fi

# Extract UUID and External IP
uuid=$(echo "$cluster_output" | grep "Cluster Id" | awk -F': ' '{print $2}' | tr -d ' ')
external_ip=$(echo "$cluster_output" | grep "External or Masqueradi" | awk -F': ' '{print $2}' | tr -d ' []')

# Validate extracted values
if [ -z "$uuid" ] || [ -z "$external_ip" ]; then
    echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): Failed to extract UUID or External IP"
    echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): UUID='$uuid', External IP='$external_ip'"
    return 1
fi

echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Extracted UUID: $uuid"
echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Extracted External IP: $external_ip"
echo

# Execute remove-from-multicluster command
echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Executing remove-from-multicluster command..."
remove_cmd="~/prism/cli/ncli multicluster remove-from-multicluster username=admin password=Nutanix.123 force=true external-ip-address-or-svm-ips=$external_ip local_only=true"

echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Command: $remove_cmd"
echo

remove_output=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "$remove_cmd")
echo "$remove_output"
echo

# Extract task UUID from output
task_uuid=$(echo "$remove_output" | grep "taskUuid" | awk -F': ' '{print $2}' | tr -d ' ')

if [ -n "$task_uuid" ]; then
    echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Task UUID: $task_uuid"
    echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Checking task status..."
    
    # Monitor task status
    for i in {1..30}; do
        echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Checking task status (attempt $i/30)..."
        task_status=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "/usr/local/nutanix/bin/ecli task.get $task_uuid" 2>/dev/null || echo "")
        
        if [ -n "$task_status" ]; then
            echo "$task_status"
            
            # Check if task is completed
            if echo "$task_status" | grep -i "succeeded\|completed\|success" > /dev/null; then
                echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): Task completed successfully!"
                break
            elif echo "$task_status" | grep -i "failed\|error" > /dev/null; then
                echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): Task failed!"
                break
            else
                echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Task still in progress, waiting 10 seconds..."
                sleep 10
            fi
        else
            echo "[WARNING] PE $pe_number/$total_pes ($PE_IP): Could not get task status"
            sleep 5
        fi
    done
    echo
else
    echo "[WARNING] PE $pe_number/$total_pes ($PE_IP): Could not extract task UUID from output"
fi

echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): Remove-from-multicluster command completed!"
echo

# Step 3: Monitor task completion
if [ -n "$task_uuid" ]; then
    echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Step 3 - Monitoring task completion..."
    echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Task UUID: $task_uuid"
    echo
    
    for i in {1..10}; do
        echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Checking task status (attempt $i/10)..."
        task_status=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "/usr/local/nutanix/bin/ecli task.get $task_uuid" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$task_status" ]; then
            # Show key status information
            percentage=$(echo "$task_status" | grep -i "percentageComplete" | awk -F': ' '{print $2}' | tr -d ' ')
            status=$(echo "$task_status" | grep -i "operationState" | awk -F': ' '{print $2}' | tr -d ' ')
            
            if [ -n "$percentage" ]; then
                echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Progress: $percentage%"
            fi
            if [ -n "$status" ]; then
                echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Status: $status"
            fi
            
            # Check if task is completed
            if echo "$task_status" | grep -i "succeeded\|kSucceeded" > /dev/null; then
                echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): ✅ Task completed successfully!"
                break
            elif echo "$task_status" | grep -i "failed\|kFailed\|error" > /dev/null; then
                echo "[ERROR] PE $pe_number/$total_pes ($PE_IP): ❌ Task failed!"
                echo "Task details:"
                echo "$task_status" | head -20
                break
            else
                echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Task still in progress, waiting 20 seconds..."
                sleep 20
            fi
        else
            echo "[WARNING] PE $pe_number/$total_pes ($PE_IP): Could not get task status, continuing with next steps..."
            break
        fi
    done
    echo
else
    echo "[WARNING] PE $pe_number/$total_pes ($PE_IP): No task UUID found, skipping task monitoring"
    echo
fi

# Step 4: Run unregistration cleanup
echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Step 4 - Running unregistration cleanup..."
cleanup_cmd="python /home/nutanix/bin/unregistration_cleanup.py $uuid"
echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Command: $cleanup_cmd"

sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "$cleanup_cmd"
echo

echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): Unregistration cleanup completed!"
echo

# Step 5: Remove zookeeper entries
echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Step 5 - Removing zookeeper blacklist entries..."

echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Removing /appliance/physical/blacklisted"
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "/usr/local/nutanix/cluster/bin/zkrm /appliance/physical/blacklisted" || echo "[WARNING] PE $pe_number/$total_pes ($PE_IP): Could not remove blacklisted entry"

echo "[INFO] PE $pe_number/$total_pes ($PE_IP): Removing /appliance/physical/blacklist"
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$PE_IP" "/usr/local/nutanix/cluster/bin/zkrm /appliance/physical/blacklist" || echo "[WARNING] PE $pe_number/$total_pes ($PE_IP): Could not remove blacklist entry"

echo
echo "[SUCCESS] PE $pe_number/$total_pes ($PE_IP): ✅ Cluster cleanup completed successfully!"
echo "================================================================"
echo

# Return success
return 0
}

# Main script logic
if [ $# -eq 0 ]; then
    echo "Usage: $0 <PE_IP1> [PE_IP2] [PE_IP3] ..."
    echo "   or: $0 \"10.122.27.47 10.122.27.76 10.122.27.128\""
    echo
    echo "Examples:"
    echo "  $0 10.122.27.88"
    echo "  $0 10.122.27.47 10.122.27.76 10.122.27.128"
    echo "  $0 \"10.122.27.47 10.122.27.76 10.122.27.128 10.122.27.140\""
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

echo "========================================"
echo "  Nutanix Cluster Cleanup Script"
echo "  Started at: $(date)"
echo "========================================"
echo "DEBUG: Number of arguments received: $#"
echo "DEBUG: All arguments: $*"
echo "Total PEs to process: $total_pes"
echo "PE List: ${PE_LIST[*]}"
echo "========================================"
echo

# Process each PE
success_count=0
failed_count=0
failed_pes=()

for i in "${!PE_LIST[@]}"; do
    PE_IP="${PE_LIST[$i]}"
    pe_number=$((i + 1))
    
    echo "[INFO] ⏳ Starting cleanup for PE $pe_number/$total_pes: $PE_IP"
    
    if process_pe "$PE_IP" "$pe_number" "$total_pes"; then
        echo "[SUCCESS] ✅ PE $pe_number/$total_pes ($PE_IP) completed successfully"
        ((success_count++))
    else
        echo "[ERROR] ❌ PE $pe_number/$total_pes ($PE_IP) failed"
        ((failed_count++))
        failed_pes+=("$PE_IP")
    fi
    
    # Add delay between PEs to avoid overwhelming
    if [ $pe_number -lt $total_pes ]; then
        echo "[INFO] ⏸️  Waiting 10 seconds before processing next PE..."
        sleep 10
        echo
    fi
done

# Final summary
echo "========================================"
echo "  FINAL SUMMARY"
echo "  Completed at: $(date)"
echo "========================================"
echo "Total PEs processed: $total_pes"
echo "Successful: $success_count"
echo "Failed: $failed_count"

if [ $failed_count -gt 0 ]; then
    echo
    echo "Failed PEs:"
    for failed_pe in "${failed_pes[@]}"; do
        echo "  - $failed_pe"
    done
fi

echo "========================================"

if [ $failed_count -eq 0 ]; then
    echo "[SUCCESS] 🎉 All PEs processed successfully!"
    echo "========================================"
    echo "SCRIPT COMPLETED - EXITING"
    echo "========================================"
    exit 0
else
    echo "[WARNING] ⚠️  Some PEs failed. Check logs above."
    echo "========================================"
    echo "SCRIPT COMPLETED WITH ERRORS - EXITING"
    echo "========================================"
    exit 1
fi