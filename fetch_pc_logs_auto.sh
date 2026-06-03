#!/bin/bash
################################################################################
# Script to automatically fetch kubeconfig and fluentd logs from Prism Central
# with automated authentication using sshpass
#
# Usage:
#   ./fetch_pc_logs_auto.sh <pc_ip> [password] [output_dir]
#
# Example:
#   ./fetch_pc_logs_auto.sh 10.114.55.128
#   ./fetch_pc_logs_auto.sh 10.114.55.128 nutanix/4u
#   ./fetch_pc_logs_auto.sh 10.114.55.128 nutanix/4u /tmp/logs
#
# Environment Variables:
#   PC_PASSWORD - Default password if not provided as argument
#   PC_USER     - SSH user (default: nutanix)
################################################################################

set -e

# Configuration
PC_IP="${1}"
PC_PASSWORD="${2:-${PC_PASSWORD}}"
OUTPUT_DIR="${3:-./pc_logs}"
PC_USER="${PC_USER:-nutanix}"
KUBECONFIG_DIR="./kubeconfigs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Pod and namespace configuration
POD_NAME="fluentd-aggregator-0"
NAMESPACE="ntnx-system"
SOURCE_PATH="/fluentd/data/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

################################################################################
# Functions
################################################################################

print_header() {
    echo "================================================================================"
    echo -e "${BLUE}$1${NC}"
    echo "================================================================================"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_requirements() {
    local missing=0
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        missing=1
    fi
    
    if ! command -v ssh &> /dev/null; then
        print_error "ssh is not installed"
        missing=1
    fi
    
    if [ -n "$PC_PASSWORD" ] && ! command -v sshpass &> /dev/null; then
        print_warning "sshpass not installed - will require manual password entry"
    fi
    
    return $missing
}

fetch_kubeconfig() {
    local pc_ip=$1
    local output_file=$2
    
    # Build SSH command
    local ssh_cmd="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
    
    if [ -n "$PC_PASSWORD" ] && command -v sshpass &> /dev/null; then
        ssh_cmd="sshpass -p '$PC_PASSWORD' $ssh_cmd"
    fi
    
    # Execute SSH command
    eval "$ssh_cmd ${PC_USER}@${pc_ip} '/usr/local/nutanix/cluster/bin/mspctl cls kubeconfig nc'" > "$output_file" 2>/dev/null
    
    return $?
}

verify_kubeconfig() {
    local kubeconfig_file=$1
    
    if [ ! -s "$kubeconfig_file" ]; then
        return 1
    fi
    
    kubectl --kubeconfig="$kubeconfig_file" cluster-info &> /dev/null
    return $?
}

copy_pod_logs() {
    local kubeconfig_file=$1
    local output_dir=$2
    
    kubectl --kubeconfig="$kubeconfig_file" cp \
        -n "$NAMESPACE" \
        "${POD_NAME}:${SOURCE_PATH}" \
        "$output_dir/" \
        2>&1 | grep -v "Defaulted container" | grep -v "tar: removing leading" || true
    
    return ${PIPESTATUS[0]}
}

get_log_stats() {
    local log_dir=$1
    
    if [ -d "$log_dir/logs" ]; then
        local count=$(find "$log_dir/logs" -type f 2>/dev/null | wc -l)
        local size=$(du -sh "$log_dir/logs" 2>/dev/null | cut -f1)
        echo "$count:$size"
    else
        echo "0:0"
    fi
}

################################################################################
# Main Script
################################################################################

# Check arguments
if [ -z "$PC_IP" ]; then
    echo -e "${RED}Error: PC IP address required${NC}"
    echo ""
    echo "Usage: $0 <pc_ip> [password] [output_dir]"
    echo ""
    echo "Examples:"
    echo "  $0 10.114.55.128"
    echo "  $0 10.114.55.128 nutanix/4u"
    echo "  $0 10.114.55.128 nutanix/4u /tmp/logs"
    echo ""
    echo "Environment Variables:"
    echo "  PC_PASSWORD - Default password if not provided"
    echo "  PC_USER     - SSH user (default: nutanix)"
    exit 1
fi

print_header "Prism Central Automated Log Fetcher"
echo "PC IP:          $PC_IP"
echo "User:           $PC_USER"
echo "Password:       $([ -n "$PC_PASSWORD" ] && echo "***" || echo "not provided (manual entry required)")"
echo "Output Dir:     $OUTPUT_DIR"
echo "Kubeconfig Dir: $KUBECONFIG_DIR"
echo "Timestamp:      $TIMESTAMP"
echo "Pod:            $NAMESPACE/$POD_NAME"
echo "Source Path:    $SOURCE_PATH"
echo ""

# Check requirements
if ! check_requirements; then
    exit 1
fi

# Create directories
mkdir -p "$KUBECONFIG_DIR"
mkdir -p "$OUTPUT_DIR"

KUBECONFIG_FILE="$KUBECONFIG_DIR/${PC_IP}_kubeconfig_${TIMESTAMP}"
LOG_OUTPUT_DIR="$OUTPUT_DIR/${PC_IP}_${TIMESTAMP}"
LATEST_LINK="$KUBECONFIG_DIR/${PC_IP}_kubeconfig_latest"

# Step 1: Fetch kubeconfig
print_header "Step 1/3: Fetching Kubeconfig"
print_info "Connecting to ${PC_USER}@${PC_IP}..."

if fetch_kubeconfig "$PC_IP" "$KUBECONFIG_FILE"; then
    print_success "Kubeconfig fetched successfully"
    print_info "Saved to: ${KUBECONFIG_FILE}"
    
    # Create symlink to latest
    ln -sf "$(basename "$KUBECONFIG_FILE")" "$LATEST_LINK"
    print_info "Latest link: ${LATEST_LINK}"
else
    print_error "Failed to fetch kubeconfig"
    exit 1
fi
echo ""

# Step 2: Verify kubeconfig
print_header "Step 2/3: Verifying Kubeconfig"
if verify_kubeconfig "$KUBECONFIG_FILE"; then
    print_success "Kubeconfig is valid and cluster is reachable"
else
    print_error "Kubeconfig validation failed"
    exit 1
fi
echo ""

# Step 3: Copy logs
print_header "Step 3/3: Copying Fluentd Logs"
print_info "Creating output directory: ${LOG_OUTPUT_DIR}"
mkdir -p "$LOG_OUTPUT_DIR"

print_info "Copying logs from ${POD_NAME}:${SOURCE_PATH}..."
if copy_pod_logs "$KUBECONFIG_FILE" "$LOG_OUTPUT_DIR"; then
    print_success "Logs copied successfully"
else
    print_error "Failed to copy logs"
    exit 1
fi
echo ""

# Summary
print_header "Summary"
print_success "All operations completed successfully"
echo ""
echo "📁 Files:"
echo "  Kubeconfig:  ${KUBECONFIG_FILE}"
echo "  Latest Link: ${LATEST_LINK}"
echo "  Logs:        ${LOG_OUTPUT_DIR}/"
echo ""

# Log statistics
stats=$(get_log_stats "$LOG_OUTPUT_DIR")
count=$(echo "$stats" | cut -d: -f1)
size=$(echo "$stats" | cut -d: -f2)

if [ "$count" -gt 0 ]; then
    echo "📊 Statistics:"
    echo "  Files:       $count"
    echo "  Total Size:  $size"
    echo ""
    
    echo "📄 Latest Files:"
    find "$LOG_OUTPUT_DIR/logs" -type f -printf '%T@ %p\n' 2>/dev/null | \
        sort -rn | head -10 | while read -r timestamp filepath; do
        filename=$(basename "$filepath")
        filesize=$(du -h "$filepath" 2>/dev/null | cut -f1)
        echo "  - $filename ($filesize)"
    done
fi

print_header "✅ Done"
