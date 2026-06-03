#!/bin/bash
################################################################################
# Batch script to fetch logs from multiple PCs and upload to filer
#
# Usage:
#   ./fetch_and_upload_multiple_pcs.sh <pc_list_file> <bug_folder>
#
# PC List File Format (one per line):
#   <ip_address> [password] [custom_name]
#
# Example:
#   ./fetch_and_upload_multiple_pcs.sh pc_list.txt ENG-937578
#
# Environment Variables:
#   PC_PASSWORD      - Default password for all PCs
#   FILER_PASSWORD   - Password for filer
################################################################################

set -e

PC_LIST_FILE="${1}"
BUG_FOLDER="${2}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

print_banner() {
    echo "================================================================================"
    echo -e "${MAGENTA}$1${NC}"
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

fetch_single_pc() {
    local pc_ip=$1
    local password=$2
    local custom_name=$3
    local index=$4
    local total=$5
    
    print_section "[$index/$total] Processing PC: ${custom_name:-$pc_ip} ($pc_ip)"
    
    # Set environment for subprocess
    export PC_PASSWORD="$password"
    export FILER_PASSWORD="${FILER_PASSWORD}"
    
    # Call the main fetcher script
    if bash "$(dirname "$0")/fetch_and_upload_pc_logs.sh" "$pc_ip" "$password" "$BUG_FOLDER"; then
        print_success "Completed: ${custom_name:-$pc_ip}"
        return 0
    else
        print_error "Failed: ${custom_name:-$pc_ip}"
        return 1
    fi
}

################################################################################
# Main Script
################################################################################

# Check arguments
if [ -z "$PC_LIST_FILE" ] || [ -z "$BUG_FOLDER" ]; then
    echo -e "${RED}Error: PC list file and bug folder required${NC}"
    echo ""
    echo "Usage: $0 <pc_list_file> <bug_folder>"
    echo ""
    echo "Example:"
    echo "  $0 pc_list.txt ENG-937578"
    echo ""
    echo "PC List File Format (one per line):"
    echo "  <ip_address> [password] [custom_name]"
    exit 1
fi

if [ ! -f "$PC_LIST_FILE" ]; then
    echo -e "${RED}Error: File not found: $PC_LIST_FILE${NC}"
    exit 1
fi

# Check if helper script exists
HELPER_SCRIPT="$(dirname "$0")/fetch_and_upload_pc_logs.sh"
if [ ! -f "$HELPER_SCRIPT" ]; then
    echo -e "${RED}Error: Helper script not found: $HELPER_SCRIPT${NC}"
    exit 1
fi

print_banner "Batch PC Log Fetcher with Filer Upload"
echo "PC List:     $PC_LIST_FILE"
echo "Bug Folder:  $BUG_FOLDER"
echo "Timestamp:   $TIMESTAMP"
echo ""

# Read PC list and count
total_pcs=$(grep -v '^#' "$PC_LIST_FILE" | grep -v '^[[:space:]]*$' | wc -l)
print_info "Total PCs to process: $total_pcs"
echo ""

# Process each PC
success_count=0
fail_count=0
index=0
success_list=()
fail_list=()

while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$line" ]] && continue
    
    index=$((index + 1))
    
    # Parse line
    read -r pc_ip password custom_name <<< "$line"
    
    # Use default password if not specified
    if [ -z "$password" ] || [ "$password" == "-" ]; then
        password="$PC_PASSWORD"
    fi
    
    # Process this PC
    if fetch_single_pc "$pc_ip" "$password" "$custom_name" "$index" "$total_pcs"; then
        success_count=$((success_count + 1))
        success_list+=("${custom_name:-$pc_ip}")
    else
        fail_count=$((fail_count + 1))
        fail_list+=("${custom_name:-$pc_ip}")
    fi
    
    # Add separator between PCs
    if [ $index -lt $total_pcs ]; then
        echo ""
        echo "################################################################################"
        echo ""
    fi
    
done < "$PC_LIST_FILE"

# Final summary
echo ""
print_banner "Batch Processing Complete"
echo ""
echo "📊 Results:"
echo "  Total PCs:    $total_pcs"
echo "  Successful:   $success_count"
echo "  Failed:       $fail_count"
echo ""

if [ $success_count -gt 0 ]; then
    echo "✅ Successfully Processed:"
    for pc in "${success_list[@]}"; do
        echo "  • $pc"
    done
    echo ""
fi

if [ $fail_count -gt 0 ]; then
    echo "❌ Failed:"
    for pc in "${fail_list[@]}"; do
        echo "  • $pc"
    done
    echo ""
fi

echo "🌐 Access logs at:"
echo "  http://10.46.1.165/bugs/MA/NCM2_1/$BUG_FOLDER/"
echo ""

if [ $fail_count -eq 0 ]; then
    print_success "All PCs processed and uploaded successfully!"
    exit 0
else
    print_error "Some PCs failed to process"
    exit 1
fi
