#!/bin/bash
################################################################################
# Batch script to fetch logs from multiple Prism Central instances
#
# Usage:
#   ./fetch_multiple_pc_logs.sh <pc_list_file>
#
# PC List File Format (one per line):
#   <ip_address> [password] [custom_name]
#
# Example pc_list.txt:
#   10.114.55.128 nutanix/4u PC1
#   10.114.55.129 nutanix/4u PC2
#   10.114.55.130
#
# Environment Variables:
#   PC_PASSWORD - Default password for all PCs if not specified per PC
#   PC_USER     - SSH user (default: nutanix)
################################################################################

set -e

PC_LIST_FILE="${1}"
OUTPUT_BASE_DIR="./pc_logs_batch_$(date +%Y%m%d_%H%M%S)"
KUBECONFIG_BASE_DIR="./kubeconfigs_batch_$(date +%Y%m%d_%H%M%S)"
PC_USER="${PC_USER:-nutanix}"
DEFAULT_PASSWORD="${PC_PASSWORD}"

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
    
    local pc_output_dir="$OUTPUT_BASE_DIR/${custom_name:-$pc_ip}"
    local pc_kubeconfig_dir="$KUBECONFIG_BASE_DIR/${custom_name:-$pc_ip}"
    
    print_section "[$index/$total] Processing PC: ${custom_name:-$pc_ip} ($pc_ip)"
    
    # Set environment for subprocess
    export PC_PASSWORD="$password"
    export PC_USER="$PC_USER"
    
    # Call the main fetcher script
    if bash "$(dirname "$0")/fetch_pc_logs_auto.sh" "$pc_ip" "$password" "$pc_output_dir"; then
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
if [ -z "$PC_LIST_FILE" ]; then
    echo -e "${RED}Error: PC list file required${NC}"
    echo ""
    echo "Usage: $0 <pc_list_file>"
    echo ""
    echo "PC List File Format (one per line):"
    echo "  <ip_address> [password] [custom_name]"
    echo ""
    echo "Example pc_list.txt:"
    echo "  10.114.55.128 nutanix/4u PC1"
    echo "  10.114.55.129 nutanix/4u PC2"
    echo "  10.114.55.130"
    exit 1
fi

if [ ! -f "$PC_LIST_FILE" ]; then
    echo -e "${RED}Error: File not found: $PC_LIST_FILE${NC}"
    exit 1
fi

# Check if helper script exists
HELPER_SCRIPT="$(dirname "$0")/fetch_pc_logs_auto.sh"
if [ ! -f "$HELPER_SCRIPT" ]; then
    echo -e "${RED}Error: Helper script not found: $HELPER_SCRIPT${NC}"
    exit 1
fi

print_banner "Batch Prism Central Log Fetcher"
echo "PC List:        $PC_LIST_FILE"
echo "Output Dir:     $OUTPUT_BASE_DIR"
echo "Kubeconfig Dir: $KUBECONFIG_BASE_DIR"
echo "User:           $PC_USER"
echo "Default Pass:   $([ -n "$DEFAULT_PASSWORD" ] && echo "***" || echo "not set")"
echo ""

# Create base directories
mkdir -p "$OUTPUT_BASE_DIR"
mkdir -p "$KUBECONFIG_BASE_DIR"

# Read PC list and count
total_pcs=$(grep -v '^#' "$PC_LIST_FILE" | grep -v '^[[:space:]]*$' | wc -l)
print_info "Total PCs to process: $total_pcs"
echo ""

# Process each PC
success_count=0
fail_count=0
index=0

while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$line" ]] && continue
    
    index=$((index + 1))
    
    # Parse line
    read -r pc_ip password custom_name <<< "$line"
    
    # Use default password if not specified
    if [ -z "$password" ] || [ "$password" == "-" ]; then
        password="$DEFAULT_PASSWORD"
    fi
    
    # Process this PC
    if fetch_single_pc "$pc_ip" "$password" "$custom_name" "$index" "$total_pcs"; then
        success_count=$((success_count + 1))
    else
        fail_count=$((fail_count + 1))
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
echo "📁 Output:"
echo "  Logs:         $OUTPUT_BASE_DIR/"
echo "  Kubeconfigs:  $KUBECONFIG_BASE_DIR/"
echo ""

# List all log directories
echo "📂 Log Directories:"
for dir in "$OUTPUT_BASE_DIR"/*; do
    if [ -d "$dir" ]; then
        pc_name=$(basename "$dir")
        if [ -d "$dir/logs" ]; then
            file_count=$(find "$dir/logs" -type f 2>/dev/null | wc -l)
            dir_size=$(du -sh "$dir/logs" 2>/dev/null | cut -f1)
            echo "  ✓ $pc_name: $file_count files, $dir_size"
        else
            echo "  ✗ $pc_name: No logs found"
        fi
    fi
done
echo ""

if [ $fail_count -eq 0 ]; then
    print_success "All PCs processed successfully!"
    exit 0
else
    print_error "Some PCs failed to process"
    exit 1
fi
