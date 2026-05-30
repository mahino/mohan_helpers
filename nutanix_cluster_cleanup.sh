#!/bin/bash

# Nutanix Cluster Cleanup Script
# This script automates the process of cleaning up cluster registration via SSH

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default SSH credentials
SSH_USER="nutanix"
SSH_PASS="RDMCluster.123"

# Default behavior - auto proceed without confirmation
REQUIRE_CONFIRMATION=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to execute command via SSH
ssh_exec() {
    local pe_ip=$1
    local command=$2
    local description=${3:-"Executing command"}
    
    print_status "$description on PE: $pe_ip"
    print_status "Command: $command"
    
    # Execute command and capture output
    output=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$pe_ip" "$command" 2>&1)
    local exit_code=$?
    
    # Display output
    if [ -n "$output" ]; then
        echo "$output"
    fi
    
    return $exit_code
}

# Function to get cluster information (UUID and External IP)
get_cluster_info() {
    local pe_ip=$1
    
    # Run the command via SSH and capture both stdout and stderr
    cluster_info=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$pe_ip" "~/prism/cli/ncli multicluster get-cluster-state 2>&1")
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        return 1
    fi
    
    if [ -z "$cluster_info" ]; then
        return 1
    fi
    
    # Check if output contains error messages
    if echo "$cluster_info" | grep -i "error\|failed\|not found" > /dev/null; then
        return 1
    fi
    
    # Extract UUID from the output
    uuid=$(echo "$cluster_info" | grep "Cluster Id" | awk -F': ' '{print $2}' | tr -d ' ')
    
    if [ -z "$uuid" ]; then
        # Try alternative patterns
        uuid=$(echo "$cluster_info" | grep -i "cluster.*id" | awk -F': ' '{print $2}' | tr -d ' ')
        if [ -z "$uuid" ]; then
            return 1
        fi
    fi
    
    # Extract External IP from the output
    external_ip=$(echo "$cluster_info" | grep "External or Masqueradi" | awk -F': ' '{print $2}' | tr -d ' []')
    
    if [ -z "$external_ip" ]; then
        # Try alternative patterns
        external_ip=$(echo "$cluster_info" | grep -i "external" | awk -F': ' '{print $2}' | tr -d ' []')
        if [ -z "$external_ip" ]; then
            external_ip=$pe_ip
        fi
    fi
    
    # Return both values separated by a pipe (no debug output)
    echo "$uuid|$external_ip"
}

# Function to delete cluster state
remove_from_multicluster() {
    local pe_ip=$1
    local external_ip=$2
    
    print_status "Removing from multicluster using external IP: $external_ip"
    
    # Build command step by step to avoid issues
    local cmd_base="~/prism/cli/ncli multicluster remove-from-multicluster"
    local cmd_params="username=admin password=Nutanix.123 force=true"
    local cmd_ip="external-ip-address-or-svm-ips=$external_ip"
    local cmd_local="local_only=true"
    
    local full_cmd="$cmd_base $cmd_params $cmd_ip $cmd_local"
    
    print_status "Executing command on PE $pe_ip:"
    echo "  $full_cmd"
    echo
    
    # Execute the command
    print_status "Executing..."
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$pe_ip" "$full_cmd"
    local exit_code=$?
    
    echo
    print_status "Command completed with exit code: $exit_code"
    
    if [ $exit_code -eq 0 ]; then
        print_success "Successfully removed from multicluster"
    else
        print_error "Failed to remove from multicluster (exit code: $exit_code)"
        return 1
    fi
}

# Function to run unregistration cleanup
run_unregistration_cleanup() {
    local pe_ip=$1
    local uuid=$2
    print_status "Running unregistration cleanup script for UUID: $uuid"
    
    cleanup_script="/home/nutanix/bin/unregistration_cleanup.py"
    
    # Check if script exists
    if ! ssh_exec "$pe_ip" "test -f $cleanup_script" "Checking for cleanup script"; then
        print_error "Unregistration cleanup script not found at: $cleanup_script"
        return 1
    fi
    
    if ssh_exec "$pe_ip" "python $cleanup_script $uuid" "Running unregistration cleanup"; then
        print_success "Unregistration cleanup completed successfully"
    else
        print_error "Unregistration cleanup failed"
        return 1
    fi
}

# Function to remove zookeeper entries
remove_zk_entries() {
    local pe_ip=$1
    print_status "Removing zookeeper blacklist entries..."
    
    # Remove blacklisted entry
    if ssh_exec "$pe_ip" "zkrm /appliance/physical/blacklisted" "Removing blacklisted entry"; then
        print_success "Removed /appliance/physical/blacklisted"
    else
        print_warning "Could not remove /appliance/physical/blacklisted (may not exist)"
    fi
    
    # Remove blacklist entry
    if ssh_exec "$pe_ip" "zkrm /appliance/physical/blacklist" "Removing blacklist entry"; then
        print_success "Removed /appliance/physical/blacklist"
    else
        print_warning "Could not remove /appliance/physical/blacklist (may not exist)"
    fi
}

# Function to display current cluster state
show_cluster_state() {
    local pe_ip=$1
    print_status "Current cluster state on PE: $pe_ip"
    echo "----------------------------------------"
    
    print_status "Executing: ~/prism/cli/ncli multicluster get-cluster-state"
    cluster_state=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$pe_ip" "~/prism/cli/ncli multicluster get-cluster-state 2>&1")
    local exit_code=$?
    
    print_status "Command exit code: $exit_code"
    
    if [ $exit_code -eq 0 ] && [ -n "$cluster_state" ]; then
        echo "$cluster_state"
    else
        print_warning "Could not retrieve cluster state (exit code: $exit_code)"
        if [ -n "$cluster_state" ]; then
            print_warning "Error output: $cluster_state"
        fi
    fi
    echo "----------------------------------------"
}

# Function to validate PE IP and check available commands
validate_pe_ip() {
    local pe_ip=$1
    
    print_status "Validating connection to PE: $pe_ip"
    
    if ssh_exec "$pe_ip" "echo 'Connection test successful'" "Testing SSH connection"; then
        print_success "Successfully connected to PE: $pe_ip"
        
        # Check ncli availability and commands
        print_status "Checking available ncli commands..."
        ncli_help=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$pe_ip" "~/prism/cli/ncli --help 2>&1" || true)
        
        if echo "$ncli_help" | grep -i "multicluster" > /dev/null; then
            print_success "multicluster command is available"
        else
            print_warning "multicluster command may not be available"
            print_status "Available ncli commands:"
            echo "$ncli_help" | grep -E "^\s+[a-z]" | head -10
        fi
        
        return 0
    else
        print_error "Failed to connect to PE: $pe_ip"
        print_error "Please check:"
        print_error "  - PE IP address is correct"
        print_error "  - PE is reachable from this machine"
        print_error "  - SSH credentials are correct"
        return 1
    fi
}

# Main execution function
main() {
    local pe_ip=$1
    
    if [ -z "$pe_ip" ]; then
        print_error "PE IP address is required"
        echo "Usage: $0 <PE_IP> [OPTIONS]"
        exit 1
    fi
    
    echo "======================================"
    echo "  Nutanix Cluster Cleanup Script"
    echo "======================================"
    echo "PE IP: $pe_ip"
    echo "SSH User: $SSH_USER"
    echo
    
    # Validate connection first
    if ! validate_pe_ip "$pe_ip"; then
        exit 1
    fi
    echo
    
    # Show initial state
    show_cluster_state "$pe_ip"
    echo
    
    # Get cluster information (UUID and External IP)
    print_status "Step 1: Getting cluster information..."
    
    # Show the cluster state first
    print_status "Executing: ~/prism/cli/ncli multicluster get-cluster-state"
    cluster_info=$(sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$pe_ip" "~/prism/cli/ncli multicluster get-cluster-state 2>&1")
    local exit_code=$?
    
    print_status "Command exit code: $exit_code"
    print_status "Command output:"
    echo "$cluster_info"
    
    # Now get the parsed data
    cluster_data=$(get_cluster_info "$pe_ip")
    if [ $? -ne 0 ]; then
        print_error "Failed to get cluster information. Exiting."
        exit 1
    fi
    
    # Parse the returned data
    uuid=$(echo "$cluster_data" | cut -d'|' -f1)
    external_ip=$(echo "$cluster_data" | cut -d'|' -f2)
    
    print_success "Found cluster UUID: $uuid"
    print_success "Found external IP: $external_ip"
    echo
    
    # Check if confirmation is required
    if [ "$REQUIRE_CONFIRMATION" = true ]; then
        read -p "Do you want to proceed with cleanup for cluster UUID: $uuid (external IP: $external_ip) on PE $pe_ip? (y/N): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            print_warning "Cleanup cancelled by user"
            exit 0
        fi
    else
        print_status "Auto-proceeding with cleanup for cluster UUID: $uuid (external IP: $external_ip) on PE $pe_ip"
    fi
    
    echo
    
    # Step 2: Remove from multicluster
    print_status "Step 2: Removing from multicluster..."
    remove_from_multicluster "$pe_ip" "$external_ip"
    echo
    
    # Step 3: Run unregistration cleanup
    print_status "Step 3: Running unregistration cleanup..."
    run_unregistration_cleanup "$pe_ip" "$uuid"
    echo
    
    # Step 4: Remove zookeeper entries
    print_status "Step 4: Removing zookeeper blacklist entries..."
    remove_zk_entries "$pe_ip"
    echo
    
    # Show final state
    print_status "Final cluster state:"
    show_cluster_state "$pe_ip"
    
    print_success "Cluster cleanup completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 <PE_IP> [OPTIONS]"
        echo
        echo "Arguments:"
        echo "  PE_IP          IP address of the Prism Element cluster"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --dry-run      Show what would be done without executing"
        echo "  --uuid UUID    Use specific UUID instead of auto-detection"
        echo "  --user USER    SSH username (default: nutanix)"
        echo "  --pass PASS    SSH password (default: nutanix/4u)"
        echo "  --confirm      Ask for confirmation before proceeding (default: auto-proceed)"
        echo
        echo "Examples:"
        echo "  $0 10.1.1.100"
        echo "  $0 10.1.1.100 --dry-run"
        echo "  $0 10.1.1.100 --uuid 12345678-1234-1234-1234-123456789abc"
        echo
        echo "This script performs the following steps via SSH:"
        echo "1. Gets cluster info using '~/prism/cli/ncli multicluster get-cluster-state'"
        echo "2. Removes from multicluster using '~/prism/cli/ncli multicluster remove-from-multicluster'"
        echo "3. Runs unregistration cleanup script"
        echo "4. Removes zookeeper blacklist entries"
        exit 0
        ;;
    --dry-run)
        pe_ip=$2
        if [ -z "$pe_ip" ]; then
            print_error "PE IP address is required for dry run"
            echo "Usage: $0 <PE_IP> --dry-run"
            exit 1
        fi
        
        echo "DRY RUN MODE - No changes will be made"
        echo "PE IP: $pe_ip"
        echo
        
        if validate_pe_ip "$pe_ip"; then
            cluster_data=$(get_cluster_info "$pe_ip")
            if [ $? -eq 0 ]; then
                uuid=$(echo "$cluster_data" | cut -d'|' -f1)
                external_ip=$(echo "$cluster_data" | cut -d'|' -f2)
                echo "Would cleanup cluster with UUID: $uuid"
                echo "External IP: $external_ip"
                echo
                echo "SSH commands that would be executed on $pe_ip:"
                echo "1. sshpass -p '$SSH_PASS' ssh $SSH_USER@$pe_ip '~/prism/cli/ncli multicluster remove-from-multicluster username=admin password=Nutanix.123 force=true external-ip-address-or-svm-ips=$external_ip local_only=true'"
                echo "2. sshpass -p '$SSH_PASS' ssh $SSH_USER@$pe_ip 'python /home/nutanix/bin/unregistration_cleanup.py $uuid'"
                echo "3. sshpass -p '$SSH_PASS' ssh $SSH_USER@$pe_ip 'zkrm /appliance/physical/blacklisted'"
                echo "4. sshpass -p '$SSH_PASS' ssh $SSH_USER@$pe_ip 'zkrm /appliance/physical/blacklist'"
            fi
        fi
        exit 0
        ;;
    --uuid)
        pe_ip=$2
        custom_uuid=$3
        custom_external_ip=$4
        if [ -z "$pe_ip" ] || [ -z "$custom_uuid" ]; then
            print_error "PE IP and UUID are required with --uuid option"
            echo "Usage: $0 <PE_IP> --uuid <UUID> [EXTERNAL_IP]"
            exit 1
        fi
        # Use PE IP as external IP if not provided
        if [ -z "$custom_external_ip" ]; then
            custom_external_ip=$pe_ip
        fi
        # Override the get_cluster_info function to return the provided values
        get_cluster_info() {
            echo "$custom_uuid|$custom_external_ip"
        }
        main "$pe_ip"
        ;;
    --user)
        SSH_USER=$2
        shift 2
        main "$@"
        ;;
    --pass)
        SSH_PASS=$2
        shift 2
        main "$@"
        ;;
    --confirm)
        REQUIRE_CONFIRMATION=true
        shift
        main "$@"
        ;;
    "")
        print_error "PE IP address is required"
        echo "Usage: $0 <PE_IP> [OPTIONS]"
        echo "Use --help for more information"
        exit 1
        ;;
    *)
        # Check if first argument looks like an IP address
        if [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            main "$@"
        else
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
        fi
        ;;
esac