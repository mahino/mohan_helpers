# VM Recovery Points Analysis Script

## Overview

This script analyzes VM recovery points across a Nutanix Prism Central cluster and calculates reclaimable space at both VM and cluster levels.

## Features

✅ **Complete Recovery Point Discovery**
- Lists all VMs with recovery points using v3 groups API
- Fetches detailed recovery point information for each VM using v4 data protection API

✅ **Space Analysis**
- Calculates total reclaimable space per VM
- Provides cluster-level total reclaimable space
- Formats output in human-readable units (B, KiB, MiB, GiB, TiB)

✅ **Comprehensive Reporting**
- Total VMs with recovery points
- Total number of recovery points (snapshots)
- Total reclaimable space across the cluster
- Top VMs by reclaimable space
- Statistical analysis (averages, maximums)

✅ **JSON Export**
- Exports complete analysis to JSON file
- Includes all VM details and recovery point metadata
- Timestamped filename for historical tracking

## Prerequisites

```bash
# Python 3.6 or higher
python3 --version

# Required packages
pip3 install requests urllib3
```

## Configuration

Edit the script and update these variables:

```python
# Basic Configuration
PRISM_IP = "10.114.55.128"          # Your Prism Central IP
PRISM_PORT = "9440"                  # Default: 9440
USERNAME = "admin"                   # Prism admin username
PASSWORD = "Nutanix.123"             # Prism admin password

# Pagination settings
GROUPS_PAGE_SIZE = 60                # VMs per page for groups API
RECOVERY_POINTS_PAGE_SIZE = 100      # Recovery points per page

# Output settings
EXPORT_TO_JSON = True                # Export results to JSON file
JSON_OUTPUT_FILE = "recovery_points_analysis_{timestamp}.json"
```

## Usage

### Basic Usage

```bash
cd /home/mohan.as1/mohan_helpers
python3 analyze_recovery_points.py
```

### Output Example

```
[2026-05-27 21:50:00] [INFO] ================================================================================
[2026-05-27 21:50:00] [INFO] VM RECOVERY POINTS ANALYSIS
[2026-05-27 21:50:00] [INFO] ================================================================================
[2026-05-27 21:50:00] [INFO] Prism Central: 10.114.55.128
[2026-05-27 21:50:00] [INFO] ================================================================================
[2026-05-27 21:50:00] [INFO] 
[2026-05-27 21:50:00] [INFO] Fetching VMs with recovery points using v3 groups API...
[2026-05-27 21:50:02] [INFO]   Fetched 60 VMs (offset: 0)
[2026-05-27 21:50:04] [INFO]   Fetched 60 VMs (offset: 60)
[2026-05-27 21:50:06] [INFO]   Completed fetching all 120 VMs
[2026-05-27 21:50:06] [INFO] Found 120 VMs with recovery points
[2026-05-27 21:50:06] [INFO] 
[2026-05-27 21:50:06] [INFO] Fetching detailed recovery points for each VM...
[2026-05-27 21:50:06] [INFO] 
[2026-05-27 21:50:06] [INFO] [1/120] Processing VM: 007b3889... (Expected: 6 recovery points)
[2026-05-27 21:50:08] [INFO]   ✓ VM: ahv_ins_delete-0-260514-180402
[2026-05-27 21:50:08] [INFO]     Recovery Points: 6
[2026-05-27 21:50:08] [INFO]     Total Reclaimable Space: 2.52 GiB
[2026-05-27 21:50:08] [INFO] 
[2026-05-27 21:50:08] [INFO] [2/120] Processing VM: 08d05b91... (Expected: 2 recovery points)
[2026-05-27 21:50:10] [INFO]   ✓ VM: vm-177-260519-075323
[2026-05-27 21:50:10] [INFO]     Recovery Points: 2
[2026-05-27 21:50:10] [INFO]     Total Reclaimable Space: 512.00 MiB
...

[2026-05-27 21:55:30] [INFO] ================================================================================
[2026-05-27 21:55:30] [INFO] CLUSTER-LEVEL SUMMARY
[2026-05-27 21:55:30] [INFO] ================================================================================
[2026-05-27 21:55:30] [INFO] Total VMs with Recovery Points: 120
[2026-05-27 21:55:30] [INFO] Total Recovery Points (Snapshots): 456
[2026-05-27 21:55:30] [INFO] Total Reclaimable Space: 1.24 TiB (1,367,891,283,968 bytes)
[2026-05-27 21:55:30] [INFO] ================================================================================

[2026-05-27 21:55:30] [INFO] ================================================================================
[2026-05-27 21:55:30] [INFO] TOP 10 VMS BY RECLAIMABLE SPACE
[2026-05-27 21:55:30] [INFO] ================================================================================
[2026-05-27 21:55:30] [INFO] 1. prod-database-server-01
[2026-05-27 21:55:30] [INFO]    Recovery Points: 15
[2026-05-27 21:55:30] [INFO]    Reclaimable Space: 256.78 GiB
[2026-05-27 21:55:30] [INFO] 
[2026-05-27 21:55:30] [INFO] 2. prod-app-server-03
[2026-05-27 21:55:30] [INFO]    Recovery Points: 12
[2026-05-27 21:55:30] [INFO]    Reclaimable Space: 189.45 GiB
...

[2026-05-27 21:55:30] [INFO] ================================================================================
[2026-05-27 21:55:30] [INFO] STATISTICS
[2026-05-27 21:55:30] [INFO] ================================================================================
[2026-05-27 21:55:30] [INFO] Average Reclaimable Space per VM: 10.57 GiB
[2026-05-27 21:55:30] [INFO] Average Recovery Points per VM: 3.8
[2026-05-27 21:55:30] [INFO] 
[2026-05-27 21:55:30] [INFO] VM with Most Reclaimable Space:
[2026-05-27 21:55:30] [INFO]   prod-database-server-01: 256.78 GiB
[2026-05-27 21:55:30] [INFO] 
[2026-05-27 21:55:30] [INFO] VM with Most Recovery Points:
[2026-05-27 21:55:30] [INFO]   test-vm-continuous-backup: 24 recovery points
[2026-05-27 21:55:30] [INFO] ================================================================================

[2026-05-27 21:55:30] [SUCCESS] Analysis exported to: recovery_points_analysis_20260527_215530.json
```

## JSON Output Format

The script exports a JSON file with the following structure:

```json
{
  "cluster_summary": {
    "total_vms": 120,
    "total_recovery_points": 456,
    "total_reclaimable_space_bytes": 1367891283968,
    "total_reclaimable_space_human": "1.24 TiB",
    "prism_central": "10.114.55.128",
    "analysis_timestamp": "2026-05-27T21:55:30.123456"
  },
  "vms": [
    {
      "vm_uuid": "007b3889-7667-4a07-6d78-53fc2e60b124",
      "vm_name": "ahv_ins_delete-0-260514-180402",
      "recovery_point_count": 6,
      "total_reclaimable_space_bytes": 2704154746,
      "total_reclaimable_space_human": "2.52 GiB",
      "recovery_points": [
        {
          "extId": "b1bdfba4-fba5-4adc-9409-edf0985d6e9c",
          "name": "bulk_2026-05-26_063112_23",
          "creationTime": "2026-05-26T06:31:42.494788Z",
          "expirationTime": "2026-06-25T06:31:12Z",
          "totalExclusiveUsageBytes": 0,
          "recoveryPointType": "CRASH_CONSISTENT",
          "status": "COMPLETE",
          "ownerExtId": "00000000-0000-0000-0000-000000000000"
        }
        // ... more recovery points
      ]
    }
    // ... more VMs
  ]
}
```

## How It Works

### Step 1: Discover VMs with Recovery Points

Uses v3 Groups API to get all VMs that have recovery points:
- **Endpoint:** `POST /api/nutanix/v3/groups`
- **Entity Type:** `vm_recovery_point`
- **Grouping:** By VM UUID (`entity_uuid`)
- **Result:** List of VM UUIDs with recovery point counts

### Step 2: Fetch Recovery Point Details

For each VM, fetches detailed recovery point information:
- **Endpoint:** `GET /api/dataprotection/v4.3/config/recovery-points`
- **Filter:** `vmRecoveryPoints/any(a:a/vmExtId eq '{vm_uuid}')`
- **Result:** Detailed list of recovery points with metadata

### Step 3: Calculate Reclaimable Space

For each VM:
- Sums up `totalExclusiveUsageBytes` from all recovery points
- Converts to human-readable format
- Stores in per-VM details

### Step 4: Aggregate Cluster Totals

- Total number of VMs with recovery points
- Total number of recovery points (snapshots)
- Total reclaimable space across all VMs

### Step 5: Generate Reports

- Console output with formatted results
- Top VMs by reclaimable space
- Statistical analysis
- JSON export for further processing

## APIs Used

### 1. v3 Groups API (VM Discovery)
```
POST https://10.114.55.128:9440/api/nutanix/v3/groups

Payload:
{
  "entity_type": "vm_recovery_point",
  "group_count": 60,
  "group_offset": 0,
  "grouping_attribute": "entity_uuid",
  "filter_criteria": "snapshot_type!=LIVE"
}
```

### 2. v4 Data Protection API (Recovery Point Details)
```
GET https://10.114.55.128:9440/api/dataprotection/v4.3/config/recovery-points

Parameters:
- $page=0
- $limit=100
- $filter=vmRecoveryPoints/any(a:a/vmExtId eq '{vm_uuid}')
- $orderby=creationTime desc
- $select=*
```

### 3. v3 VMs API (VM Name Resolution)
```
GET https://10.114.55.128:9440/api/nutanix/v3/vms/{vm_uuid}
```

## Use Cases

### 1. Capacity Planning
- Identify how much space can be reclaimed by deleting old recovery points
- Prioritize VMs with the most reclaimable space

### 2. Cost Optimization
- Find VMs with excessive recovery points
- Implement retention policies based on actual space usage

### 3. Compliance & Auditing
- Track total number of recovery points across the cluster
- Export historical snapshots of recovery point usage

### 4. Troubleshooting
- Identify VMs with unusual recovery point patterns
- Investigate VMs consuming excessive snapshot storage

## Performance Considerations

- **Execution Time:** Approximately 5-10 seconds per VM
  - 10 VMs: ~1-2 minutes
  - 100 VMs: ~8-17 minutes
  - 500 VMs: ~40-85 minutes

- **API Rate Limiting:** The script includes proper error handling for rate limits

- **Memory Usage:** Minimal - processes VMs sequentially

## Troubleshooting

### No VMs Found
```
[WARNING] No VMs with recovery points found!
```
**Solution:** 
- Verify that VMs have recovery points in Prism Central
- Check credentials and network connectivity
- Verify the cluster has data protection configured

### Authentication Error
```
[ERROR] Error fetching VMs: 401 Unauthorized
```
**Solution:** Verify `USERNAME` and `PASSWORD` in script

### Connection Error
```
[ERROR] Error fetching VMs: Connection refused
```
**Solution:** Verify `PRISM_IP` and `PRISM_PORT`, check network connectivity

### Empty Recovery Points for a VM
```
[WARNING] No detailed recovery points found for VM vm-name
```
**Solution:** 
- The v4 API may not return recovery points that are still being created
- Check the VM's recovery points in the Prism UI

## Advanced Usage

### Export Only (No Console Output)

Redirect stdout to suppress logs:

```bash
python3 analyze_recovery_points.py > /dev/null
# JSON file will still be created
```

### Filter VMs by Name Pattern

Modify the script to add filtering in `get_vm_name()` or after VM discovery.

### Schedule Regular Analysis

```bash
# Add to crontab for weekly analysis
0 2 * * 0 /usr/bin/python3 /home/mohan.as1/mohan_helpers/analyze_recovery_points.py >> /var/log/recovery_points_analysis.log 2>&1
```

### Process JSON Output with jq

```bash
# Get total reclaimable space
cat recovery_points_analysis_*.json | jq '.cluster_summary.total_reclaimable_space_human'

# List top 5 VMs by space
cat recovery_points_analysis_*.json | jq '.vms | sort_by(.total_reclaimable_space_bytes) | reverse | .[:5] | .[] | {vm_name, total_reclaimable_space_human}'

# Count VMs with more than 10 recovery points
cat recovery_points_analysis_*.json | jq '[.vms[] | select(.recovery_point_count > 10)] | length'
```

## Related Documentation

- [VM_RECOVERY_POINTS_API_ANALYSIS.md](VM_RECOVERY_POINTS_API_ANALYSIS.md) - API details for VM list
- [VM_RECOVERY_POINTS_DETAIL_API_ANALYSIS.md](VM_RECOVERY_POINTS_DETAIL_API_ANALYSIS.md) - API details for recovery point details

## Support

For issues or questions:
1. Check Nutanix API documentation
2. Verify Prism Central version compatibility
3. Review API responses in browser developer tools
4. Check Prism Central logs for API errors

## Disclaimer

⚠️ **WARNING**: This script is read-only and does not modify or delete any recovery points. It only analyzes and reports on existing data.

- Always test in a non-production environment first
- Verify credentials and permissions
- Monitor API rate limits during execution
- Review output for accuracy before taking action
