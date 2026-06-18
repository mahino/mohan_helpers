#!/bin/bash
# Example wrapper script to clean up dummy files on multiple Prism Element clusters

# Configuration
PE_CLUSTERS=(
    "10.46.117.165"
    # "10.46.117.166"
    # "10.46.117.167"
)
PE_USER="admin"
PE_PASS="nutanix/4u"  # Change this to your PE password

# Script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup_vm_dummy_files.py"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================================================="
echo "Multi-PE VM Dummy Files Cleanup"
echo "=============================================================================="
echo "Total PE Clusters: ${#PE_CLUSTERS[@]}"
echo "PE User: $PE_USER"
echo "VM SSH User: root"
echo "VM SSH Password: nutanix/4u"
echo "=============================================================================="
echo ""

# Check if script exists
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo -e "${RED}❌ Error: Script not found at $CLEANUP_SCRIPT${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 is not installed${NC}"
    exit 1
fi

# Check if sshpass is available
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: sshpass is not installed. Installing...${NC}"
    echo ""
    echo "Please run one of these commands:"
    echo "  Ubuntu/Debian: sudo apt-get install sshpass"
    echo "  CentOS/RHEL:   sudo yum install sshpass"
    exit 1
fi

# Process each PE cluster
TOTAL_SUCCESS=0
TOTAL_FAILED=0

for pe_ip in "${PE_CLUSTERS[@]}"; do
    echo ""
    echo "=============================================================================="
    echo -e "${GREEN}Processing PE: $pe_ip${NC}"
    echo "=============================================================================="
    
    # Run cleanup script
    python3 "$CLEANUP_SCRIPT" "$pe_ip" "$PE_USER" "$PE_PASS"
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        TOTAL_SUCCESS=$((TOTAL_SUCCESS + 1))
        echo -e "${GREEN}✅ PE $pe_ip: Completed successfully${NC}"
    else
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
        echo -e "${RED}❌ PE $pe_ip: Failed with exit code $EXIT_CODE${NC}"
    fi
    
    echo ""
done

# Final summary
echo "=============================================================================="
echo "FINAL SUMMARY - All PE Clusters"
echo "=============================================================================="
echo "Total PE Clusters: ${#PE_CLUSTERS[@]}"
echo -e "${GREEN}✅ Successful: $TOTAL_SUCCESS${NC}"
echo -e "${RED}❌ Failed:     $TOTAL_FAILED${NC}"
echo "=============================================================================="

exit $TOTAL_FAILED
