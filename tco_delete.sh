#!/bin/bash

# TCO Direct Cost File Deletion Wrapper Script
# This script provides easy shortcuts for common operations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/delete_tco_direct_cost_files.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    echo "TCO Direct Cost File Deletion Tool"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  list      - List all TCO direct cost files"
    echo "  preview   - Preview what would be deleted (dry-run)"
    echo "  delete    - Delete TCO files with backup and confirmation"
    echo "  force     - Delete TCO files without confirmation (still creates backup)"
    echo "  no-backup - Delete TCO files without backup or confirmation"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 preview"
    echo "  $0 delete"
    echo "  $0 force"
    echo ""
}

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    print_color $RED "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Parse command
case "${1:-help}" in
    "list"|"-l"|"--list")
        print_color $BLUE "Listing TCO direct cost files..."
        python3 "$PYTHON_SCRIPT" --list
        ;;
    
    "preview"|"dry-run"|"--dry-run")
        print_color $BLUE "Preview mode - showing what would be deleted..."
        python3 "$PYTHON_SCRIPT" --dry-run
        ;;
    
    "delete"|"del")
        print_color $YELLOW "Deleting TCO files with backup and confirmation..."
        python3 "$PYTHON_SCRIPT"
        ;;
    
    "force"|"--force")
        print_color $YELLOW "Deleting TCO files with backup but no confirmation..."
        python3 "$PYTHON_SCRIPT" --no-confirm
        ;;
    
    "no-backup"|"--no-backup")
        print_color $RED "WARNING: Deleting TCO files without backup!"
        echo "Are you sure you want to proceed without backup? (type 'yes' to continue)"
        read -r confirmation
        if [[ "$confirmation" == "yes" ]]; then
            python3 "$PYTHON_SCRIPT" --no-backup --no-confirm
        else
            print_color $GREEN "Operation cancelled."
        fi
        ;;
    
    "help"|"-h"|"--help"|*)
        show_usage
        ;;
esac