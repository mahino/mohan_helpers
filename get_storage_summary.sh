#!/bin/bash
#
# Script to fetch storage summary from Nutanix Prism Element using 3 specific APIs
# Usage: ./get_storage_summary.sh <PE_IP> <USERNAME> <PASSWORD>
#

set -e

# Check arguments
if [ $# -ne 3 ]; then
    echo "Usage: $0 <PE_IP> <USERNAME> <PASSWORD>"
    echo "Example: $0 10.46.117.165 admin 'nutanix/4u'"
    exit 1
fi

PE_IP="$1"
USER="$2"
PASS="$3"

echo "============================================================"
echo "STORAGE SUMMARY - $PE_IP"
echo "============================================================"
echo ""

# Step 1: Get cluster UUID
echo "[INFO] Fetching cluster UUID..."
CLUSTER_UUID=$(curl -k -s -X GET \
  "https://$PE_IP:9440/PrismGateway/services/rest/v1/clusters" \
  -u "$USER:$PASS" | jq -r '.entities[0].uuid')

if [ -z "$CLUSTER_UUID" ] || [ "$CLUSTER_UUID" = "null" ]; then
    echo "[ERROR] Failed to get cluster UUID"
    exit 1
fi

echo "Cluster UUID: $CLUSTER_UUID"
echo ""

# Step 2: Fetch the 3 storage metrics
echo "[INFO] Fetching API 1: storage.capacity_bytes..."
CAPACITY=$(curl -k -s -X GET \
  "https://$PE_IP:9440/PrismGateway/services/rest/v1/clusters/$CLUSTER_UUID/stats?metrics=storage.capacity_bytes" \
  -u "$USER:$PASS" | jq '.statsSpecificResponses[0].values[0]')

echo "[INFO] Fetching API 2: storage.usage_bytes..."
USAGE=$(curl -k -s -X GET \
  "https://$PE_IP:9440/PrismGateway/services/rest/v1/clusters/$CLUSTER_UUID/stats?metrics=storage.usage_bytes" \
  -u "$USER:$PASS" | jq '.statsSpecificResponses[0].values[0]')

echo "[INFO] Fetching API 3: storage.snapshot_reclaimable_bytes..."
RECOVERY=$(curl -k -s -X GET \
  "https://$PE_IP:9440/PrismGateway/services/rest/v1/clusters/$CLUSTER_UUID/stats?metrics=storage.snapshot_reclaimable_bytes" \
  -u "$USER:$PASS" | jq '.statsSpecificResponses[0].values[0]')

# Check if any metric failed
if [ -z "$CAPACITY" ] || [ "$CAPACITY" = "null" ]; then
    echo "[ERROR] Failed to fetch capacity metric"
    exit 1
fi

if [ -z "$USAGE" ] || [ "$USAGE" = "null" ]; then
    echo "[ERROR] Failed to fetch usage metric"
    exit 1
fi

if [ -z "$RECOVERY" ] || [ "$RECOVERY" = "null" ]; then
    echo "[ERROR] Failed to fetch recovery metric"
    exit 1
fi

echo ""
echo "============================================================"
echo "RESULTS"
echo "============================================================"
echo ""

# Convert to human-readable format
# Note: bc might not be available, using awk instead
CAPACITY_TIB=$(echo "$CAPACITY" | awk '{printf "%.2f", $1 / 1099511627776}')
USAGE_TIB=$(echo "$USAGE" | awk '{printf "%.2f", $1 / 1099511627776}')
RECOVERY_GIB=$(echo "$RECOVERY" | awk '{printf "%.2f", $1 / 1073741824}')
FREE=$((CAPACITY - USAGE))
FREE_TIB=$(echo "$FREE" | awk '{printf "%.2f", $1 / 1099511627776}')
USAGE_PCT=$(echo "$CAPACITY $USAGE" | awk '{printf "%.2f", ($2 / $1) * 100}')

# Display results
echo "1. Total Capacity:   $CAPACITY_TIB TiB"
printf "                     (%'d bytes)\n" "$CAPACITY"
echo ""

echo "2. Total Usage:      $USAGE_TIB TiB"
printf "                     (%'d bytes)\n" "$USAGE"
echo ""

echo "3. Recovery Points:  $RECOVERY_GIB GiB"
printf "                     (%'d bytes)\n" "$RECOVERY"
echo ""

echo "------------------------------------------------------------"
echo "Calculated:"
echo "  Free Space:        $FREE_TIB TiB"
printf "                     (%'d bytes)\n" "$FREE"
echo "  Usage Percentage:  $USAGE_PCT%"
echo ""

# Visual usage bar
BAR_LENGTH=50
FILLED=$(echo "$USAGE_PCT" | awk -v len=$BAR_LENGTH '{printf "%d", ($1 / 100) * len}')
EMPTY=$((BAR_LENGTH - FILLED))

printf "  ["
for ((i=0; i<FILLED; i++)); do printf "█"; done
for ((i=0; i<EMPTY; i++)); do printf "░"; done
printf "]\n"

echo ""
echo "============================================================"
