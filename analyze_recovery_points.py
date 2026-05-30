#!/usr/bin/env python3
"""
Script to analyze VM Recovery Points and calculate reclaimable space.

Features:
- Lists all VMs with recovery points using v3 groups API
- Fetches detailed recovery points for each VM using v4 data protection API
- Calculates total reclaimable space per VM
- Provides cluster-level summary (total space, VMs, snapshots)
"""

import requests
import json
import urllib3
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================== CONFIGURATION ==========================
PRISM_IP = "10.114.55.128"
PRISM_PORT = "9440"
USERNAME = "admin"
PASSWORD = "Nutanix.123"

# API endpoints
BASE_URL = f"https://{PRISM_IP}:{PRISM_PORT}"
V3_GROUPS_URL = f"{BASE_URL}/api/nutanix/v3/groups"
V4_RECOVERY_POINTS_URL = f"{BASE_URL}/api/dataprotection/v4.3/config/recovery-points"

# Pagination settings
GROUPS_PAGE_SIZE = 60  # VMs per page for groups API
RECOVERY_POINTS_PAGE_SIZE = 100  # Recovery points per page

# Output settings
EXPORT_TO_JSON = True
JSON_OUTPUT_FILE = f"recovery_points_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# ===================================================================


def log(message, level="INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def make_auth_header():
    """Create basic auth header."""
    import base64
    credentials = f"{USERNAME}:{PASSWORD}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {b64_credentials}"


def format_bytes(bytes_value):
    """Convert bytes to human-readable format."""
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    k = 1024
    
    for i, unit in enumerate(units):
        if bytes_value < k ** (i + 1) or i == len(units) - 1:
            value = bytes_value / (k ** i)
            return f"{value:.2f} {unit}"
    
    return f"{bytes_value} B"


def get_all_vms_with_recovery_points():
    """
    Get all VMs with recovery points using v3 groups API.
    Returns list of VMs with their recovery point counts.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    all_vms = []
    offset = 0
    
    log("Fetching VMs with recovery points using v3 groups API...")
    
    while True:
        payload = {
            "entity_type": "vm_recovery_point",
            "group_count": GROUPS_PAGE_SIZE,
            "group_offset": offset,
            "grouping_attribute": "entity_uuid",
            "group_sort_attribute": "entity_uuid",
            "group_sort_order": "ASCENDING",
            "group_member_count": 0,
            "filter_criteria": "snapshot_type!=LIVE"
        }
        
        try:
            response = requests.post(
                V3_GROUPS_URL,
                headers=headers,
                data=json.dumps(payload),
                verify=False,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            group_results = data.get('group_results', [])
            if not group_results:
                break
            
            log(f"  Fetched {len(group_results)} VMs (offset: {offset})")
            
            for group in group_results:
                vm_uuid = group.get('group_by_column_value')
                recovery_point_count = group.get('total_entity_count', 0)
                
                all_vms.append({
                    'vm_uuid': vm_uuid,
                    'recovery_point_count': recovery_point_count
                })
            
            # Check if we've fetched all VMs
            filtered_group_count = data.get('filtered_group_count', 0)
            if offset + len(group_results) >= filtered_group_count:
                log(f"  Completed fetching all {filtered_group_count} VMs")
                break
            
            offset += GROUPS_PAGE_SIZE
            
        except requests.exceptions.RequestException as e:
            log(f"Error fetching VMs: {e}", "ERROR")
            if hasattr(e, 'response') and e.response:
                log(f"Response: {e.response.text}", "ERROR")
            break
    
    return all_vms


def get_vm_recovery_points_details(vm_uuid):
    """
    Get detailed recovery points for a specific VM using v4 data protection API.
    Returns list of recovery points with their metadata.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    all_recovery_points = []
    page = 0
    
    while True:
        # Build OData query parameters
        params = {
            '$page': page,
            '$limit': RECOVERY_POINTS_PAGE_SIZE,
            '$filter': f"vmRecoveryPoints/any(a:a/vmExtId eq '{vm_uuid}')",
            '$orderby': 'creationTime desc',
            '$select': '*'
        }
        
        try:
            response = requests.get(
                V4_RECOVERY_POINTS_URL,
                headers=headers,
                params=params,
                verify=False,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            recovery_points = data.get('data', [])
            if not recovery_points:
                break
            
            for rp in recovery_points:
                all_recovery_points.append({
                    'extId': rp.get('extId'),
                    'name': rp.get('name'),
                    'creationTime': rp.get('creationTime'),
                    'expirationTime': rp.get('expirationTime'),
                    'totalExclusiveUsageBytes': rp.get('totalExclusiveUsageBytes', 0),
                    'recoveryPointType': rp.get('recoveryPointType'),
                    'status': rp.get('status'),
                    'ownerExtId': rp.get('ownerExtId')
                })
            
            # Check if we've fetched all recovery points
            metadata = data.get('metadata', {})
            total_available = metadata.get('totalAvailableResults', 0)
            
            if (page + 1) * RECOVERY_POINTS_PAGE_SIZE >= total_available:
                break
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            log(f"  Error fetching recovery points for VM {vm_uuid}: {e}", "ERROR")
            break
    
    return all_recovery_points


def get_vm_name(vm_uuid):
    """
    Get VM name from UUID using v3 API.
    Returns VM name or UUID if name not found.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/nutanix/v3/vms/{vm_uuid}",
            headers=headers,
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        vm_name = data.get('spec', {}).get('name') or data.get('status', {}).get('name')
        return vm_name if vm_name else vm_uuid[:8]
        
    except requests.exceptions.RequestException:
        return vm_uuid[:8]  # Return truncated UUID if name fetch fails


def analyze_recovery_points():
    """
    Main function to analyze recovery points.
    Returns cluster-level summary and per-VM details.
    """
    log("=" * 80)
    log("VM RECOVERY POINTS ANALYSIS")
    log("=" * 80)
    log(f"Prism Central: {PRISM_IP}")
    log("=" * 80)
    log("")
    
    # Step 1: Get all VMs with recovery points
    vms = get_all_vms_with_recovery_points()
    
    if not vms:
        log("No VMs with recovery points found!", "WARNING")
        return None
    
    log(f"Found {len(vms)} VMs with recovery points")
    log("")
    
    # Step 2: Process each VM to get detailed recovery points
    log("Fetching detailed recovery points for each VM...")
    log("")
    
    vm_details = []
    cluster_total_space = 0
    cluster_total_snapshots = 0
    processed_count = 0
    
    for vm in vms:
        vm_uuid = vm['vm_uuid']
        expected_count = vm['recovery_point_count']
        
        processed_count += 1
        log(f"[{processed_count}/{len(vms)}] Processing VM: {vm_uuid[:8]}... (Expected: {expected_count} recovery points)")
        
        # Get VM name
        vm_name = get_vm_name(vm_uuid)
        
        # Get detailed recovery points
        recovery_points = get_vm_recovery_points_details(vm_uuid)
        
        if not recovery_points:
            log(f"  ⚠️  No detailed recovery points found for VM {vm_name}", "WARNING")
            continue
        
        # Calculate total reclaimable space for this VM
        vm_total_space = sum(rp['totalExclusiveUsageBytes'] for rp in recovery_points)
        
        log(f"  ✓ VM: {vm_name}")
        log(f"    Recovery Points: {len(recovery_points)}")
        log(f"    Total Reclaimable Space: {format_bytes(vm_total_space)}")
        log("")
        
        # Add to cluster totals
        cluster_total_space += vm_total_space
        cluster_total_snapshots += len(recovery_points)
        
        # Store VM details
        vm_details.append({
            'vm_uuid': vm_uuid,
            'vm_name': vm_name,
            'recovery_point_count': len(recovery_points),
            'total_reclaimable_space_bytes': vm_total_space,
            'total_reclaimable_space_human': format_bytes(vm_total_space),
            'recovery_points': recovery_points
        })
    
    # Step 3: Generate cluster-level summary
    log("=" * 80)
    log("CLUSTER-LEVEL SUMMARY")
    log("=" * 80)
    log(f"Total VMs with Recovery Points: {len(vm_details)}")
    log(f"Total Recovery Points (Snapshots): {cluster_total_snapshots}")
    log(f"Total Reclaimable Space: {format_bytes(cluster_total_space)} ({cluster_total_space:,} bytes)")
    log("=" * 80)
    
    # Prepare summary data
    summary = {
        'cluster_summary': {
            'total_vms': len(vm_details),
            'total_recovery_points': cluster_total_snapshots,
            'total_reclaimable_space_bytes': cluster_total_space,
            'total_reclaimable_space_human': format_bytes(cluster_total_space),
            'prism_central': PRISM_IP,
            'analysis_timestamp': datetime.now().isoformat()
        },
        'vms': vm_details
    }
    
    # Export to JSON if enabled
    if EXPORT_TO_JSON:
        try:
            with open(JSON_OUTPUT_FILE, 'w') as f:
                json.dump(summary, f, indent=2)
            log(f"")
            log(f"Analysis exported to: {JSON_OUTPUT_FILE}", "SUCCESS")
        except Exception as e:
            log(f"Failed to export to JSON: {e}", "ERROR")
    
    return summary


def print_top_vms_by_space(summary, top_n=10):
    """Print top N VMs by reclaimable space."""
    if not summary or 'vms' not in summary:
        return
    
    vms = summary['vms']
    sorted_vms = sorted(vms, key=lambda x: x['total_reclaimable_space_bytes'], reverse=True)
    
    log("")
    log("=" * 80)
    log(f"TOP {min(top_n, len(sorted_vms))} VMs BY RECLAIMABLE SPACE")
    log("=" * 80)
    
    for i, vm in enumerate(sorted_vms[:top_n], 1):
        log(f"{i}. {vm['vm_name']}")
        log(f"   Recovery Points: {vm['recovery_point_count']}")
        log(f"   Reclaimable Space: {vm['total_reclaimable_space_human']}")
        log("")


def print_statistics(summary):
    """Print additional statistics."""
    if not summary or 'vms' not in summary:
        return
    
    vms = summary['vms']
    
    if not vms:
        return
    
    # Calculate statistics
    space_values = [vm['total_reclaimable_space_bytes'] for vm in vms]
    snapshot_counts = [vm['recovery_point_count'] for vm in vms]
    
    avg_space = sum(space_values) / len(space_values) if space_values else 0
    avg_snapshots = sum(snapshot_counts) / len(snapshot_counts) if snapshot_counts else 0
    
    max_space_vm = max(vms, key=lambda x: x['total_reclaimable_space_bytes'])
    max_snapshots_vm = max(vms, key=lambda x: x['recovery_point_count'])
    
    log("")
    log("=" * 80)
    log("STATISTICS")
    log("=" * 80)
    log(f"Average Reclaimable Space per VM: {format_bytes(int(avg_space))}")
    log(f"Average Recovery Points per VM: {avg_snapshots:.1f}")
    log("")
    log(f"VM with Most Reclaimable Space:")
    log(f"  {max_space_vm['vm_name']}: {max_space_vm['total_reclaimable_space_human']}")
    log("")
    log(f"VM with Most Recovery Points:")
    log(f"  {max_snapshots_vm['vm_name']}: {max_snapshots_vm['recovery_point_count']} recovery points")
    log("=" * 80)


def main():
    """Main execution function."""
    try:
        # Perform analysis
        summary = analyze_recovery_points()
        
        if summary:
            # Print additional insights
            print_top_vms_by_space(summary, top_n=10)
            print_statistics(summary)
        
    except KeyboardInterrupt:
        log("\n\nScript interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
