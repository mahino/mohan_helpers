#!/bin/bash
################################################################################
# Test script to verify connectivity and requirements for PC log fetcher
#
# Usage:
#   ./test_pc_connection.sh <pc_ip> [password]
################################################################################

PC_IP="${1}"
PC_PASSWORD="${2}"
PC_USER="${PC_USER:-nutanix}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    echo -n "  Testing $1... "
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}"
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}"
    if [ -n "$1" ]; then
        echo "    $1"
    fi
}

print_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}"
    if [ -n "$1" ]; then
        echo "    $1"
    fi
}

if [ -z "$PC_IP" ]; then
    echo -e "${RED}Error: PC IP required${NC}"
    echo "Usage: $0 <pc_ip> [password]"
    exit 1
fi

echo "================================================================================"
echo -e "${BLUE}Prism Central Connection Test${NC}"
echo "================================================================================"
echo "PC IP:   $PC_IP"
echo "User:    $PC_USER"
echo "================================================================================"
echo ""

echo "1. Local Requirements:"
echo "----------------------------------------"

# Check kubectl
print_test "kubectl"
if command -v kubectl &> /dev/null; then
    version=$(kubectl version --client --short 2>/dev/null | head -1)
    print_pass
    echo "    Version: $version"
else
    print_fail "kubectl not installed"
    echo "    Install: https://kubernetes.io/docs/tasks/tools/"
fi

# Check ssh
print_test "ssh"
if command -v ssh &> /dev/null; then
    version=$(ssh -V 2>&1 | head -1)
    print_pass
    echo "    Version: $version"
else
    print_fail "ssh not installed"
fi

# Check sshpass
print_test "sshpass"
if command -v sshpass &> /dev/null; then
    print_pass
    echo "    Available for automated authentication"
else
    print_warn "Not installed (optional)"
    echo "    Manual password entry will be required"
fi

echo ""
echo "2. Network Connectivity:"
echo "----------------------------------------"

# Ping test
print_test "Ping PC"
if ping -c 1 -W 2 "$PC_IP" &> /dev/null; then
    print_pass
else
    print_fail "Cannot reach $PC_IP"
fi

# SSH port test
print_test "SSH Port (22)"
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$PC_IP/22" 2>/dev/null; then
    print_pass
else
    print_fail "SSH port not reachable"
fi

# HTTPS port test
print_test "HTTPS Port (9440)"
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$PC_IP/9440" 2>/dev/null; then
    print_pass
else
    print_warn "HTTPS port not reachable (may be normal for internal K8s)"
fi

echo ""
echo "3. SSH Authentication:"
echo "----------------------------------------"

# Build SSH command
SSH_CMD="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -o LogLevel=ERROR"
if [ -n "$PC_PASSWORD" ] && command -v sshpass &> /dev/null; then
    SSH_CMD="sshpass -p '$PC_PASSWORD' $SSH_CMD"
fi

# Test SSH connection
print_test "SSH Authentication"
if eval "$SSH_CMD ${PC_USER}@${PC_IP} 'echo OK'" &> /dev/null; then
    print_pass
else
    print_fail "Cannot authenticate"
    if [ -z "$PC_PASSWORD" ]; then
        echo "    Tip: Provide password as second argument or set PC_PASSWORD"
    fi
fi

# Test mspctl command
print_test "mspctl command"
if eval "$SSH_CMD ${PC_USER}@${PC_IP} 'which /usr/local/nutanix/cluster/bin/mspctl'" &> /dev/null; then
    print_pass
else
    print_fail "mspctl not found"
fi

echo ""
echo "4. Kubeconfig Test:"
echo "----------------------------------------"

# Try to fetch kubeconfig
print_test "Fetch kubeconfig"
TEST_KUBECONFIG="/tmp/test_kubeconfig_$$"
if eval "$SSH_CMD ${PC_USER}@${PC_IP} '/usr/local/nutanix/cluster/bin/mspctl cls kubeconfig nc'" > "$TEST_KUBECONFIG" 2>/dev/null; then
    if [ -s "$TEST_KUBECONFIG" ]; then
        print_pass
        
        # Test kubeconfig validity
        print_test "Verify kubeconfig"
        if kubectl --kubeconfig="$TEST_KUBECONFIG" cluster-info &> /dev/null; then
            print_pass
            cluster_info=$(kubectl --kubeconfig="$TEST_KUBECONFIG" cluster-info 2>/dev/null | head -1)
            echo "    $cluster_info"
        else
            print_warn "Kubeconfig fetched but cluster not reachable"
        fi
        
        # Test pod access
        print_test "List pods"
        if kubectl --kubeconfig="$TEST_KUBECONFIG" get pods -n ntnx-system &> /dev/null; then
            print_pass
            pod_count=$(kubectl --kubeconfig="$TEST_KUBECONFIG" get pods -n ntnx-system --no-headers 2>/dev/null | wc -l)
            echo "    Found $pod_count pods in ntnx-system"
        else
            print_fail "Cannot list pods"
        fi
        
        # Check fluentd pod
        print_test "Fluentd pod"
        if kubectl --kubeconfig="$TEST_KUBECONFIG" get pod fluentd-aggregator-0 -n ntnx-system &> /dev/null; then
            status=$(kubectl --kubeconfig="$TEST_KUBECONFIG" get pod fluentd-aggregator-0 -n ntnx-system -o jsonpath='{.status.phase}' 2>/dev/null)
            if [ "$status" == "Running" ]; then
                print_pass
                echo "    Status: $status"
            else
                print_warn "Pod found but not running"
                echo "    Status: $status"
            fi
        else
            print_fail "fluentd-aggregator-0 pod not found"
        fi
        
        rm -f "$TEST_KUBECONFIG"
    else
        print_fail "Kubeconfig file is empty"
    fi
else
    print_fail "Cannot fetch kubeconfig"
fi

echo ""
echo "================================================================================"
echo -e "${BLUE}Test Complete${NC}"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  If all tests passed, you can run:"
echo "    ./fetch_pc_logs_auto.sh $PC_IP"
echo ""
echo "  If SSH authentication failed:"
echo "    ./fetch_pc_logs_auto.sh $PC_IP <password>"
echo ""
echo "  For batch processing:"
echo "    Create pc_list.txt and run:"
echo "    ./fetch_multiple_pc_logs.sh pc_list.txt"
echo ""
