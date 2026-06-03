#!/bin/bash
################################################################################
# Enhanced script to fetch PC logs and upload to filer
#
# Usage:
#   ./fetch_and_upload_pc_logs.sh <pc_ip> [password] [bug_folder] [output_dir]
#
# Example:
#   ./fetch_and_upload_pc_logs.sh 10.114.55.128
#   ./fetch_and_upload_pc_logs.sh 10.114.55.128 custom_pass ENG-937578
#   ./fetch_and_upload_pc_logs.sh 10.114.55.128 nutanix/4u ENG-937578 /tmp/logs
#
# Note: Default password is 'nutanix/4u' if not provided
#
# Environment Variables:
#   PC_PASSWORD      - Default password for PC SSH
#   PC_USER          - SSH user for PC (default: nutanix)
#   FILER_HOST       - Filer server IP (default: 10.46.1.165)
#   FILER_USER       - Filer SSH user (default: nutanix)
#   FILER_PASSWORD   - Filer SSH password
#   FILER_BASE_PATH  - Base path on filer (default: /home/nutanix/data/bugs/MA/NCM2_1)
################################################################################

set -e

# Configuration
PC_IP="${1}"
PC_PASSWORD="${2:-${PC_PASSWORD:-nutanix/4u}}"
BUG_FOLDER="${3}"
OUTPUT_DIR="${4:-./pc_logs}"
PC_USER="${PC_USER:-nutanix}"
KUBECONFIG_DIR="./kubeconfigs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Filer configuration
FILER_HOST="${FILER_HOST:-10.46.1.165}"
FILER_USER="${FILER_USER:-nutanix}"
FILER_PASSWORD="${FILER_PASSWORD:-nutanix/4u}"
FILER_BASE_PATH="${FILER_BASE_PATH:-/home/nutanix/data/bugs/MA/NCM2_1}"

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
MAGENTA='\033[0;35m'
NC='\033[0m'

################################################################################
# Functions
################################################################################

print_header() {
    echo "================================================================================"
    echo -e "${BLUE}$1${NC}"
    echo "================================================================================"
}

print_section() {
    echo ""
    echo "--------------------------------------------------------------------------------"
    echo -e "${CYAN}$1${NC}"
    echo "--------------------------------------------------------------------------------"
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
    
    for cmd in kubectl ssh scp; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd is not installed"
            missing=1
        fi
    done
    
    if [ -n "$PC_PASSWORD" ] && ! command -v sshpass &> /dev/null; then
        print_warning "sshpass not installed - will require manual password entry for PC"
    fi
    
    if [ -n "$FILER_PASSWORD" ] && ! command -v sshpass &> /dev/null; then
        print_warning "sshpass not installed - will require manual password entry for filer"
    fi
    
    return $missing
}

ssh_exec() {
    local host=$1
    local user=$2
    local password=$3
    shift 3
    local cmd="$@"
    
    local ssh_cmd="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
    
    if [ -n "$password" ] && command -v sshpass &> /dev/null; then
        ssh_cmd="sshpass -p '$password' $ssh_cmd"
    fi
    
    eval "$ssh_cmd ${user}@${host} '$cmd'"
}

scp_upload() {
    local source=$1
    local host=$2
    local user=$3
    local password=$4
    local dest=$5
    
    local scp_cmd="scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -r"
    
    if [ -n "$password" ] && command -v sshpass &> /dev/null; then
        scp_cmd="sshpass -p '$password' $scp_cmd"
    fi
    
    eval "$scp_cmd '$source' ${user}@${host}:'$dest/'"
}

fetch_kubeconfig() {
    local pc_ip=$1
    local output_file=$2
    
    ssh_exec "$pc_ip" "$PC_USER" "$PC_PASSWORD" \
        '/usr/local/nutanix/cluster/bin/mspctl cls kubeconfig nc' > "$output_file" 2>/dev/null
    
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

create_filer_folder() {
    local folder_path=$1
    
    print_info "Creating folder on filer: $folder_path"
    
    if ssh_exec "$FILER_HOST" "$FILER_USER" "$FILER_PASSWORD" "mkdir -p '$folder_path'" 2>/dev/null; then
        print_success "Folder created on filer"
        return 0
    else
        print_error "Failed to create folder on filer"
        return 1
    fi
}

upload_to_filer() {
    local local_path=$1
    local filer_path=$2
    
    print_info "Uploading logs to filer..."
    print_info "  Source: $local_path"
    print_info "  Destination: ${FILER_HOST}:${filer_path}"
    
    if scp_upload "$local_path" "$FILER_HOST" "$FILER_USER" "$FILER_PASSWORD" "$filer_path"; then
        print_success "Logs uploaded to filer successfully"
        return 0
    else
        print_error "Failed to upload logs to filer"
        return 1
    fi
}

verify_filer_upload() {
    local filer_path=$1
    local folder_name=$2
    
    print_info "Verifying upload on filer..."
    
    local file_count=$(ssh_exec "$FILER_HOST" "$FILER_USER" "$FILER_PASSWORD" \
        "find '$filer_path/$folder_name' -type f 2>/dev/null | wc -l" 2>/dev/null || echo "0")
    
    if [ "$file_count" -gt 0 ]; then
        print_success "Verified: $file_count files uploaded"
        
        local size=$(ssh_exec "$FILER_HOST" "$FILER_USER" "$FILER_PASSWORD" \
            "du -sh '$filer_path/$folder_name' 2>/dev/null | cut -f1" 2>/dev/null || echo "unknown")
        print_info "Total size on filer: $size"
        
        return 0
    else
        print_error "Upload verification failed"
        return 1
    fi
}

get_filer_url() {
    local relative_path=$1
    echo "http://${FILER_HOST}/bugs/MA/NCM2_1/${relative_path}"
}

################################################################################
# Main Script
################################################################################

# Check arguments
if [ -z "$PC_IP" ]; then
    echo -e "${RED}Error: PC IP address required${NC}"
    echo ""
    echo "Usage: $0 <pc_ip> [password] [bug_folder] [output_dir]"
    echo ""
    echo "Examples:"
    echo "  $0 10.114.55.128 nutanix/4u ENG-937578"
    echo "  $0 10.114.55.128 nutanix/4u ENG-937578 /tmp/logs"
    echo ""
    echo "Environment Variables:"
    echo "  PC_PASSWORD      - Default password for PC"
    echo "  FILER_PASSWORD   - Password for filer upload"
    echo "  FILER_HOST       - Filer server (default: 10.46.1.165)"
    echo "  FILER_BASE_PATH  - Base path on filer (default: /home/nutanix/data/bugs/MA/NCM2_1)"
    exit 1
fi

# Generate bug folder name if not provided
if [ -z "$BUG_FOLDER" ]; then
    BUG_FOLDER="temp_${PC_IP}_${TIMESTAMP}"
    print_warning "No bug folder specified, using: $BUG_FOLDER"
fi

print_header "PC Log Fetcher with Filer Upload"
echo "PC IP:           $PC_IP"
echo "User:            $PC_USER"
echo "PC Password:     $([ -n "$PC_PASSWORD" ] && echo "***" || echo "not provided")"
echo "Bug Folder:      $BUG_FOLDER"
echo "Output Dir:      $OUTPUT_DIR"
echo "Kubeconfig Dir:  $KUBECONFIG_DIR"
echo "Timestamp:       $TIMESTAMP"
echo "Pod:             $NAMESPACE/$POD_NAME"
echo "Source Path:     $SOURCE_PATH"
echo ""
echo "Filer Settings:"
echo "  Host:          $FILER_HOST"
echo "  User:          $FILER_USER"
echo "  Password:      $([ -n "$FILER_PASSWORD" ] && echo "***" || echo "not provided")"
echo "  Base Path:     $FILER_BASE_PATH"
echo "  Target Folder: $FILER_BASE_PATH/$BUG_FOLDER"
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
LOG_FOLDER_NAME=$(basename "$LOG_OUTPUT_DIR")

# Step 1: Fetch kubeconfig
print_header "Step 1/6: Fetching Kubeconfig"
print_info "Connecting to ${PC_USER}@${PC_IP}..."

if fetch_kubeconfig "$PC_IP" "$KUBECONFIG_FILE"; then
    print_success "Kubeconfig fetched successfully"
    print_info "Saved to: ${KUBECONFIG_FILE}"
else
    print_error "Failed to fetch kubeconfig"
    exit 1
fi
echo ""

# Step 2: Verify kubeconfig
print_header "Step 2/6: Verifying Kubeconfig"
if verify_kubeconfig "$KUBECONFIG_FILE"; then
    print_success "Kubeconfig is valid and cluster is reachable"
else
    print_error "Kubeconfig validation failed"
    exit 1
fi
echo ""

# Step 3: Copy logs from pod
print_header "Step 3/6: Copying Fluentd Logs from Pod"
print_info "Creating output directory: ${LOG_OUTPUT_DIR}"
mkdir -p "$LOG_OUTPUT_DIR"

print_info "Copying logs from ${POD_NAME}:${SOURCE_PATH}..."
if copy_pod_logs "$KUBECONFIG_FILE" "$LOG_OUTPUT_DIR"; then
    print_success "Logs copied successfully from pod"
    
    # Show log stats
    if [ -d "$LOG_OUTPUT_DIR/logs" ]; then
        file_count=$(find "$LOG_OUTPUT_DIR/logs" -type f 2>/dev/null | wc -l)
        log_size=$(du -sh "$LOG_OUTPUT_DIR/logs" 2>/dev/null | cut -f1)
        print_info "Local logs: $file_count files, $log_size"
    fi
else
    print_error "Failed to copy logs from pod"
    exit 1
fi
echo ""

# Step 4: Create folder on filer
print_header "Step 4/6: Creating Folder on Filer"
FILER_TARGET_PATH="$FILER_BASE_PATH/$BUG_FOLDER"

if ! create_filer_folder "$FILER_TARGET_PATH"; then
    print_error "Cannot proceed with upload"
    print_warning "Local logs are available at: $LOG_OUTPUT_DIR"
    exit 1
fi
echo ""

# Step 5: Upload logs to filer
print_header "Step 5/6: Uploading Logs to Filer"

if upload_to_filer "$LOG_OUTPUT_DIR" "$FILER_TARGET_PATH"; then
    print_success "Upload completed"
else
    print_error "Upload failed"
    print_warning "Local logs preserved at: $LOG_OUTPUT_DIR"
    exit 1
fi
echo ""

# Step 6: Verify and cleanup
print_header "Step 6/6: Verification and Cleanup"

if verify_filer_upload "$FILER_TARGET_PATH" "$LOG_FOLDER_NAME"; then
    print_success "Upload verified successfully"
    
    # Only delete local logs after successful upload
    print_info "Cleaning up local logs..."
    if rm -rf "$LOG_OUTPUT_DIR"; then
        print_success "Local logs deleted"
    else
        print_warning "Could not delete local logs at: $LOG_OUTPUT_DIR"
    fi
else
    print_error "Upload verification failed"
    print_warning "Local logs preserved at: $LOG_OUTPUT_DIR"
    exit 1
fi
echo ""

# Final summary
print_header "✅ Success - All Operations Completed"
echo ""
echo "📁 Files:"
echo "  Kubeconfig:      ${KUBECONFIG_FILE}"
echo "  Filer Location:  ${FILER_HOST}:${FILER_TARGET_PATH}/${LOG_FOLDER_NAME}"
echo ""
echo "🌐 Access URL:"
FILER_URL=$(get_filer_url "$BUG_FOLDER/$LOG_FOLDER_NAME")
echo "  ${FILER_URL}"
echo ""
echo "📊 Summary:"
echo "  ✓ Kubeconfig fetched from PC"
echo "  ✓ Logs copied from fluentd pod"
echo "  ✓ Logs uploaded to filer"
echo "  ✓ Upload verified"
echo "  ✓ Local logs cleaned up"
echo ""
print_header "Done"
