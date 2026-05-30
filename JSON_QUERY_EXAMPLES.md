# JSON Query Examples for Recovery Points Analysis

This document shows how to query the `recovery_points_analysis_*.json` file using `jq` (JSON processor).

## Basic Queries

### 1. Get Cluster Summary
```bash
cat recovery_points_analysis_*.json | jq '.cluster_summary'
```

**Output:**
```json
{
  "total_vms": 2164,
  "total_recovery_points": 6138,
  "total_reclaimable_space_bytes": 145110794240,
  "total_reclaimable_space_human": "135.14 GiB",
  "prism_central": "10.114.55.128",
  "analysis_timestamp": "2026-05-27T17:56:13.824166"
}
```

### 2. Get Total Reclaimable Space (Human Readable)
```bash
cat recovery_points_analysis_*.json | jq -r '.cluster_summary.total_reclaimable_space_human'
```

**Output:**
```
135.14 GiB
```

### 3. Count Total VMs
```bash
cat recovery_points_analysis_*.json | jq '.cluster_summary.total_vms'
```

**Output:**
```
2164
```

## VM-Level Queries

### 4. List All VM Names
```bash
cat recovery_points_analysis_*.json | jq -r '.vms[].vm_name'
```

### 5. Get Top 10 VMs by Reclaimable Space
```bash
cat recovery_points_analysis_*.json | jq '.vms | sort_by(.total_reclaimable_space_bytes) | reverse | .[0:10] | .[] | {vm_name, recovery_point_count, total_reclaimable_space_human}'
```

**Output:**
```json
{
  "vm_name": "nc-2056cb-default-1",
  "recovery_point_count": 5,
  "total_reclaimable_space_human": "23.12 GiB"
}
{
  "vm_name": "nc-2056cb-default-2",
  "recovery_point_count": 5,
  "total_reclaimable_space_human": "19.33 GiB"
}
...
```

### 6. Get VMs with More Than 5 Recovery Points
```bash
cat recovery_points_analysis_*.json | jq '.vms[] | select(.recovery_point_count > 5) | {vm_name, recovery_point_count, total_reclaimable_space_human}'
```

### 7. Get VMs with More Than 1 GiB Reclaimable Space
```bash
cat recovery_points_analysis_*.json | jq '.vms[] | select(.total_reclaimable_space_bytes > 1073741824) | {vm_name, total_reclaimable_space_human, recovery_point_count}'
```

### 8. Search for a Specific VM by Name
```bash
cat recovery_points_analysis_*.json | jq '.vms[] | select(.vm_name | contains("nc-2056cb"))'
```

### 9. Get VM Details by UUID
```bash
VM_UUID="000468b4-a1e9-43e6-7ffc-9f658a0320bd"
cat recovery_points_analysis_*.json | jq --arg uuid "$VM_UUID" '.vms[] | select(.vm_uuid == $uuid)'
```

## Statistical Queries

### 10. Count VMs by Recovery Point Count
```bash
cat recovery_points_analysis_*.json | jq '[.vms[] | .recovery_point_count] | group_by(.) | map({count: .[0], vms: length}) | sort_by(.count)'
```

**Output:**
```json
[
  {"count": 1, "vms": 219},
  {"count": 2, "vms": 470},
  {"count": 3, "vms": 1099},
  {"count": 4, "vms": 217},
  {"count": 5, "vms": 96},
  {"count": 6, "vms": 54},
  {"count": 7, "vms": 9}
]
```

### 11. Calculate Average Recovery Points per VM
```bash
cat recovery_points_analysis_*.json | jq '[.vms[] | .recovery_point_count] | add / length'
```

**Output:**
```
2.8364197530864196
```

### 12. Calculate Average Reclaimable Space per VM
```bash
cat recovery_points_analysis_*.json | jq '[.vms[] | .total_reclaimable_space_bytes] | add / length / 1024 / 1024 | "\\(.)"'
```

### 13. Get Space Distribution
```bash
cat recovery_points_analysis_*.json | jq '
  .vms | 
  map(
    if .total_reclaimable_space_bytes < 1048576 then "0-1 MiB"
    elif .total_reclaimable_space_bytes < 10485760 then "1-10 MiB"
    elif .total_reclaimable_space_bytes < 104857600 then "10-100 MiB"
    elif .total_reclaimable_space_bytes < 1073741824 then "100MiB-1GiB"
    elif .total_reclaimable_space_bytes < 10737418240 then "1-10 GiB"
    else "10+ GiB"
    end
  ) | 
  group_by(.) | 
  map({range: .[0], count: length})'
```

## Recovery Point Details

### 14. Get All Recovery Points for a Specific VM
```bash
VM_NAME="nc-2056cb-default-1"
cat recovery_points_analysis_*.json | jq --arg name "$VM_NAME" '.vms[] | select(.vm_name == $name) | .recovery_points[]'
```

### 15. List Recovery Point Names for All VMs
```bash
cat recovery_points_analysis_*.json | jq '.vms[] | {vm_name, recovery_point_names: [.recovery_points[].name]}'
```

### 16. Find Recovery Points Created on a Specific Date
```bash
DATE="2026-05-26"
cat recovery_points_analysis_*.json | jq --arg date "$DATE" '.vms[] | {vm_name, recovery_points: [.recovery_points[] | select(.creationTime | startswith($date))]} | select(.recovery_points | length > 0)'
```

### 17. Get Recovery Points Expiring Soon (Next 7 Days)
```bash
# Note: Requires date calculation in jq (complex)
cat recovery_points_analysis_*.json | jq '.vms[] | {vm_name, expiring_soon: [.recovery_points[] | select(.expirationTime | . < "2026-06-04")]} | select(.expiring_soon | length > 0)'
```

## Export Formats

### 18. Export to CSV (VM Summary)
```bash
cat recovery_points_analysis_*.json | jq -r '.vms[] | [.vm_name, .recovery_point_count, .total_reclaimable_space_bytes, .total_reclaimable_space_human] | @csv' > vm_summary.csv
```

### 19. Export Top 20 to CSV
```bash
cat recovery_points_analysis_*.json | jq -r '["VM Name","Recovery Points","Reclaimable Space (Bytes)","Reclaimable Space"], (.vms | sort_by(.total_reclaimable_space_bytes) | reverse | .[0:20][] | [.vm_name, .recovery_point_count, .total_reclaimable_space_bytes, .total_reclaimable_space_human]) | @csv' > top20_vms.csv
```

### 20. Export to HTML Table
```bash
cat recovery_points_analysis_*.json | jq -r '.vms | sort_by(.total_reclaimable_space_bytes) | reverse | .[0:10][] | "<tr><td>\\(.vm_name)</td><td>\\(.recovery_point_count)</td><td>\\(.total_reclaimable_space_human)</td></tr>"' > table_rows.html
```

## Advanced Queries

### 21. Find VMs with Unusual Patterns (Many RPs, Little Space)
```bash
cat recovery_points_analysis_*.json | jq '.vms[] | select(.recovery_point_count > 5 and .total_reclaimable_space_bytes < 10485760) | {vm_name, recovery_point_count, total_reclaimable_space_human}'
```

### 22. Get VMs with 0 Reclaimable Space (Perfect Deduplication)
```bash
cat recovery_points_analysis_*.json | jq '.vms[] | select(.total_reclaimable_space_bytes == 0) | {vm_name, recovery_point_count}'
```

### 23. Calculate Pareto Analysis (80/20 Rule)
```bash
cat recovery_points_analysis_*.json | jq '
  .vms | 
  sort_by(.total_reclaimable_space_bytes) | 
  reverse | 
  to_entries | 
  map({
    rank: .key + 1, 
    vm_name: .value.vm_name, 
    space: .value.total_reclaimable_space_bytes,
    space_human: .value.total_reclaimable_space_human
  }) | 
  .[0:20]'
```

### 24. Group VMs by Name Pattern
```bash
cat recovery_points_analysis_*.json | jq '
  [.vms[] | 
    if .vm_name | startswith("nc-") then "nc-vms"
    elif .vm_name | startswith("ahv_ins_delete") then "test-vms"
    else "other-vms"
    end
  ] | 
  group_by(.) | 
  map({pattern: .[0], count: length})'
```

### 25. Calculate Total Space by VM Pattern
```bash
cat recovery_points_analysis_*.json | jq '
  .vms | 
  group_by(
    if .vm_name | startswith("nc-") then "nc-vms"
    elif .vm_name | startswith("ahv_ins_delete") then "test-vms"
    else "other-vms"
    end
  ) | 
  map({
    pattern: .[0].vm_name[:3],
    count: length,
    total_space_bytes: (map(.total_reclaimable_space_bytes) | add),
    total_space_gb: ((map(.total_reclaimable_space_bytes) | add) / 1073741824 | round)
  })'
```

## Python Script Examples

### 26. Python: Load and Query JSON
```python
import json

# Load the JSON file
with open('recovery_points_analysis_20260527_163121.json', 'r') as f:
    data = json.load(f)

# Get cluster summary
summary = data['cluster_summary']
print(f"Total VMs: {summary['total_vms']}")
print(f"Total Space: {summary['total_reclaimable_space_human']}")

# Get top 10 VMs
vms = sorted(data['vms'], key=lambda x: x['total_reclaimable_space_bytes'], reverse=True)
for i, vm in enumerate(vms[:10], 1):
    print(f"{i}. {vm['vm_name']}: {vm['total_reclaimable_space_human']}")
```

### 27. Python: Generate Custom Report
```python
import json
from collections import Counter

with open('recovery_points_analysis_20260527_163121.json', 'r') as f:
    data = json.load(f)

# Count recovery points distribution
rp_counts = [vm['recovery_point_count'] for vm in data['vms']]
distribution = Counter(rp_counts)

for count in sorted(distribution.keys()):
    print(f"{count} recovery points: {distribution[count]} VMs")
```

## Tips

1. **Install jq if not available:**
   ```bash
   sudo yum install jq  # RHEL/CentOS
   sudo apt-get install jq  # Ubuntu/Debian
   ```

2. **Pretty Print JSON:**
   ```bash
   cat recovery_points_analysis_*.json | jq '.' | less
   ```

3. **Save Query Results:**
   ```bash
   cat recovery_points_analysis_*.json | jq '.query' > output.json
   ```

4. **Combine Multiple Queries:**
   ```bash
   cat recovery_points_analysis_*.json | jq '{
     total_vms: .cluster_summary.total_vms,
     top_vm: (.vms | sort_by(.total_reclaimable_space_bytes) | reverse | .[0].vm_name),
     avg_recovery_points: ([.vms[] | .recovery_point_count] | add / length)
   }'
   ```

## References

- jq Manual: https://stedolan.github.io/jq/manual/
- JSON File: `recovery_points_analysis_20260527_163121.json`
- Main Script: `analyze_recovery_points.py`
