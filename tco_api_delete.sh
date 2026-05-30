#!/bin/bash

# TCO API Direct Cost Configuration Deletion Wrapper Script
# This script provides easy shortcuts for common TCO API operations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/delete_tco_direct_cost_api.py"
CONFIG_FILE="$SCRIPT_DIR/tco_api_config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to get base URL from config
get_base_url() {
    if [[ -f "$CONFIG_FILE" ]]; then
        python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['base_url'])" 2>/dev/null
    else
        echo "https://ncm.services.nconprem-10-53-55-93.ccpnx.com"
    fi
}

# Function to show usage
show_usage() {
    echo "TCO API Direct Cost Configuration Deletion Tool"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  list              - List all TCO direct cost configurations"
    echo "  list-test         - List test TCO configurations only"
    echo "  list-custom       - List custom TCO configurations only"
    echo "  list-nutanix      - List Nutanix hardware configurations only"
    echo "  list-inactive     - List inactive configurations only"
    echo "  preview           - Preview what would be deleted (dry-run)"
    echo "  delete            - Delete TCO configurations with confirmation"
    echo "  delete-test       - Delete test configurations only"
    echo "  delete-custom     - Delete custom configurations only"
    echo "  delete-inactive   - Delete inactive configurations only"
    echo "  force-delete      - Delete without confirmation"
    echo "  help              - Show this help message"
    echo ""
    echo "Options:"
    echo "  --url URL         - Override base URL"
    echo "  --username USER   - Username for authentication"
    echo "  --password PASS   - Password for authentication"
    echo "  --batch-size N    - Batch size for deletions (default: 10)"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 list-test"
    echo "  $0 preview --username admin"
    echo "  $0 delete-test --username admin --password mypass"
    echo "  $0 delete --url https://custom.ncm.com --username admin"
    echo ""
}

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    print_color $RED "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Parse arguments
COMMAND=""
BASE_URL=""
USERNAME=""
PASSWORD=""
BATCH_SIZE=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            BASE_URL="$2"
            shift 2
            ;;
        --username)
            USERNAME="$2"
            shift 2
            ;;
        --password)
            PASSWORD="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        help|-h|--help)
            show_usage
            exit 0
            ;;
        *)
            if [[ -z "$COMMAND" ]]; then
                COMMAND="$1"
            else
                EXTRA_ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

# Set default command
if [[ -z "$COMMAND" ]]; then
    COMMAND="help"
fi

# Get base URL
if [[ -z "$BASE_URL" ]]; then
    BASE_URL=$(get_base_url)
fi

# Build common arguments
COMMON_ARGS=("--base-url" "$BASE_URL")

if [[ -n "$USERNAME" ]]; then
    COMMON_ARGS+=("--username" "$USERNAME")
fi

if [[ -n "$PASSWORD" ]]; then
    COMMON_ARGS+=("--password" "$PASSWORD")
fi

if [[ -n "$BATCH_SIZE" ]]; then
    COMMON_ARGS+=("--batch-size" "$BATCH_SIZE")
fi

# Execute commands
case "$COMMAND" in
    "list")
        print_color $BLUE "Listing all TCO direct cost configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --list "${EXTRA_ARGS[@]}"
        ;;
    
    "list-test")
        print_color $BLUE "Listing test TCO configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --list --description-contains "test_tco_config" "${EXTRA_ARGS[@]}"
        ;;
    
    "list-custom")
        print_color $BLUE "Listing custom TCO configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --list --cost-type "CUSTOM" "${EXTRA_ARGS[@]}"
        ;;
    
    "list-nutanix")
        print_color $BLUE "Listing Nutanix hardware configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --list --cost-type "NUTANIX" --cost-head "HARDWARE" "${EXTRA_ARGS[@]}"
        ;;
    
    "list-inactive")
        print_color $BLUE "Listing inactive configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --list --inactive-only "${EXTRA_ARGS[@]}"
        ;;
    
    "preview"|"dry-run")
        print_color $BLUE "Preview mode - showing what would be deleted..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --dry-run "${EXTRA_ARGS[@]}"
        ;;
    
    "delete")
        print_color $YELLOW "Deleting TCO configurations with confirmation..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" "${EXTRA_ARGS[@]}"
        ;;
    
    "delete-test")
        print_color $YELLOW "Deleting test TCO configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --description-contains "test_tco_config" "${EXTRA_ARGS[@]}"
        ;;
    
    "delete-custom")
        print_color $YELLOW "Deleting custom TCO configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --cost-type "CUSTOM" "${EXTRA_ARGS[@]}"
        ;;
    
    "delete-inactive")
        print_color $YELLOW "Deleting inactive TCO configurations..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --inactive-only "${EXTRA_ARGS[@]}"
        ;;
    
    "force-delete")
        print_color $RED "Force deleting TCO configurations without confirmation..."
        python3 "$PYTHON_SCRIPT" "${COMMON_ARGS[@]}" --no-confirm "${EXTRA_ARGS[@]}"
        ;;
    
    *)
        print_color $RED "Unknown command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac