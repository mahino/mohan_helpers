#!/usr/bin/env python3
"""
Script to delete VM Recovery Points using Nutanix Data Protection API.

Features:
- Lists all VMs with recovery points
- Allows selective or bulk deletion of recovery points
- Uses v4 data protection API: force-delete-all-recovery-points
- Monitors task completion
- Provides detailed progress and logging
"""

import requests
import json
import urllib3
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

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
V3_VMS_URL = f"{BASE_URL}/api/nutanix/v3/vms"
V4_PROTECTED_RESOURCES_URL = f"{BASE_URL}/api/dataprotection/v4.3/config/protected-resources"
V3_TASKS_URL = f"{BASE_URL}/api/nutanix/v3/tasks"

# Pagination settings
GROUPS_PAGE_SIZE = 60  # VMs per page for groups API

# Task polling settings
TASK_POLL_INTERVAL = 5  # seconds
TASK_TIMEOUT = 600  # seconds (10 minutes)

# ===================================================================


def log(message, level="INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emoji = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "DEBUG": "🔍",
        "PROGRESS": "⚡"
    }.get(level, "")
    print(f"[{timestamp}] {emoji} {message}")


def make_auth_header():
    """Generate basic auth header."""
    import base64
    credentials = f"{USERNAME}:{PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def get_vms_with_recovery_points() -> List[Dict]:
    """
    Fetch all VMs that have recovery points using v3 groups API.
    Returns list of VMs with: vm_name, vm_uuid, recovery_point_count
    """
    log("Fetching VMs with recovery points...", "INFO")
    
    all_vms = []
    offset = 0
    
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
            headers = make_auth_header()
            headers["Content-Type"] = "application/json"
            
            response = requests.post(
                V3_GROUPS_URL,
                headers=headers,
                data=json.dumps(payload),
                verify=False,
                timeout=60
            )
            
            if response.status_code != 200:
                log(f"Failed to fetch VMs (status {response.status_code}): {response.text}", "ERROR")
                break
            
            data = response.json()
            group_results = data.get("group_results", [])
            
            if not group_results:
                break
            
            for group in group_results:
                group_by_column_value = group.get("group_by_column_value")
                total_entity_count = group.get("total_entity_count", 0)
                
                if group_by_column_value and total_entity_count > 0:
                    vm_uuid = group_by_column_value
                    
                    # Get VM name by looking at entity results
                    vm_name = vm_uuid[:8] + "..."
                    entity_results = group.get("entity_results", [])
                    
                    if entity_results:
                        for entity in entity_results:
                            data_list = entity.get("data", [])
                            for data_item in data_list:
                                if data_item.get("name") == "vm_name":
                                    values = data_item.get("values", [])
                                    if values and values[0].get("values"):
                                        vm_name = values[0]["values"][0]
                                        break
                    
                    all_vms.append({
                        "vm_name": vm_name,
                        "vm_uuid": vm_uuid,
                        "recovery_point_count": total_entity_count
                    })
            
            log(f"📥 Fetched {len(group_results)} VMs (offset: {offset})", "PROGRESS")
            
            if len(group_results) < GROUPS_PAGE_SIZE:
                break
            
            offset += GROUPS_PAGE_SIZE
        
        except Exception as e:
            log(f"Exception while fetching VMs: {str(e)}", "ERROR")
            break
    
    log(f"✅ Found {len(all_vms)} VMs with recovery points", "SUCCESS")
    return all_vms


def get_vm_ext_id(vm_uuid: str) -> Optional[str]:
    """
    Get v4 extId for a VM using its v3 UUID.
    """
    try:
        headers = make_auth_header()
        url = f"{V3_VMS_URL}/{vm_uuid}"
        
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        
        if response.status_code != 200:
            log(f"Failed to fetch VM details for {vm_uuid}: {response.status_code}", "ERROR")
            return None
        
        data = response.json()
        
        # v4 extId is typically in metadata.uuid or can be derived
        # For v4 APIs, we can also use vm_uuid directly or get from status
        ext_id = data.get("metadata", {}).get("uuid")
        
        return ext_id
    
    except Exception as e:
        log(f"Exception fetching VM extId for {vm_uuid}: {str(e)}", "ERROR")
        return None


def delete_all_recovery_points(vm_name: str, vm_uuid: str, vm_ext_id: str) -> Optional[str]:
    """
    Delete all recovery points for a VM.
    Returns task extId if successful, None otherwise.
    """
    try:
        headers = make_auth_header()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        headers["NTNX-Request-Id"] = str(uuid.uuid4())
        
        # API endpoint for force delete all recovery points
        url = f"{V4_PROTECTED_RESOURCES_URL}/{vm_ext_id}/$actions/force-delete-all-recovery-points"
        
        # Empty payload as per HAR file
        payload = {}
        
        log(f"🗑️  Deleting recovery points for VM: {vm_name}", "PROGRESS")
        log(f"   VM UUID: {vm_uuid}", "DEBUG")
        log(f"   VM ExtId: {vm_ext_id}", "DEBUG")
        log(f"   API URL: {url}", "DEBUG")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            timeout=60
        )
        
        if response.status_code not in [200, 201, 202]:
            log(f"Failed to delete recovery points (status {response.status_code}): {response.text}", "ERROR")
            return None
        
        result = response.json()
        
        # v4 API returns task in 'data' field
        task_ext_id = result.get("data", {}).get("extId")
        
        if task_ext_id:
            log(f"✅ Delete initiated for {vm_name}, Task ID: {task_ext_id}", "SUCCESS")
        else:
            log(f"⚠️  Delete response received but no task ID found", "WARNING")
        
        return task_ext_id
    
    except Exception as e:
        log(f"Exception deleting recovery points for {vm_name}: {str(e)}", "ERROR")
        return None


def poll_task_status(task_ext_id: str, vm_name: str) -> bool:
    """
    Poll task status until completion or timeout.
    Returns True if task succeeded, False otherwise.
    """
    start_time = time.time()
    
    # Extract the actual task ID from extId (format: "ZXJnb24=:actual-uuid")
    if ":" in task_ext_id:
        task_id = task_ext_id.split(":")[-1]
    else:
        task_id = task_ext_id
    
    log(f"🔄 Polling task {task_id} for VM: {vm_name}", "PROGRESS")
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > TASK_TIMEOUT:
            log(f"⏱️  Task timeout after {int(elapsed)}s for {vm_name}", "WARNING")
            return False
        
        try:
            headers = make_auth_header()
            url = f"{V3_TASKS_URL}/{task_id}"
            
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            
            if response.status_code != 200:
                log(f"Failed to fetch task status (status {response.status_code})", "ERROR")
                time.sleep(TASK_POLL_INTERVAL)
                continue
            
            task_data = response.json()
            status = task_data.get("status", "UNKNOWN")
            progress = task_data.get("percentage_complete", 0)
            
            log(f"   Task status: {status}, Progress: {progress}%", "DEBUG")
            
            if status == "SUCCEEDED":
                log(f"✅ Task completed successfully for {vm_name}", "SUCCESS")
                return True
            elif status == "FAILED":
                error_detail = task_data.get("error_detail", "No error details")
                log(f"❌ Task failed for {vm_name}: {error_detail}", "ERROR")
                return False
            elif status in ["RUNNING", "QUEUED", "PENDING"]:
                time.sleep(TASK_POLL_INTERVAL)
                continue
            else:
                log(f"⚠️  Unknown task status: {status}", "WARNING")
                time.sleep(TASK_POLL_INTERVAL)
                continue
        
        except Exception as e:
            log(f"Exception polling task: {str(e)}", "ERROR")
            time.sleep(TASK_POLL_INTERVAL)


def delete_recovery_points_bulk(vms: List[Dict], confirm: bool = True) -> Dict:
    """
    Delete recovery points for multiple VMs.
    Returns summary statistics.
    """
    total_vms = len(vms)
    successful = 0
    failed = 0
    skipped = 0
    
    log(f"", "INFO")
    log(f"{'='*80}", "INFO")
    log(f"BULK DELETION STARTED", "INFO")
    log(f"{'='*80}", "INFO")
    log(f"Total VMs to process: {total_vms}", "INFO")
    log(f"", "INFO")
    
    if confirm:
        log(f"⚠️  WARNING: This will delete ALL recovery points for {total_vms} VMs!", "WARNING")
        log(f"", "INFO")
        response = input("Do you want to continue? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            log(f"Deletion cancelled by user", "INFO")
            return {"total": total_vms, "successful": 0, "failed": 0, "skipped": total_vms}
    
    start_time = time.time()
    
    for idx, vm in enumerate(vms, 1):
        vm_name = vm["vm_name"]
        vm_uuid = vm["vm_uuid"]
        recovery_count = vm["recovery_point_count"]
        
        log(f"", "INFO")
        log(f"[{idx}/{total_vms}] Processing: {vm_name}", "PROGRESS")
        log(f"   UUID: {vm_uuid}", "DEBUG")
        log(f"   Recovery Points: {recovery_count}", "DEBUG")
        
        # Get v4 extId
        vm_ext_id = get_vm_ext_id(vm_uuid)
        
        if not vm_ext_id:
            log(f"⚠️  Skipping {vm_name}: Could not get VM extId", "WARNING")
            skipped += 1
            continue
        
        # Delete recovery points
        task_id = delete_all_recovery_points(vm_name, vm_uuid, vm_ext_id)
        
        if not task_id:
            log(f"❌ Failed to initiate deletion for {vm_name}", "ERROR")
            failed += 1
            continue
        
        # Poll task status
        task_success = poll_task_status(task_id, vm_name)
        
        if task_success:
            successful += 1
        else:
            failed += 1
    
    duration = time.time() - start_time
    
    log(f"", "INFO")
    log(f"{'='*80}", "INFO")
    log(f"DELETION COMPLETE", "SUCCESS")
    log(f"{'='*80}", "INFO")
    log(f"Total VMs Processed: {total_vms}", "INFO")
    log(f"Successful: {successful}", "SUCCESS")
    log(f"Failed: {failed}", "ERROR" if failed > 0 else "INFO")
    log(f"Skipped: {skipped}", "WARNING" if skipped > 0 else "INFO")
    log(f"Duration: {duration:.2f} seconds", "INFO")
    log(f"{'='*80}", "INFO")
    
    return {
        "total": total_vms,
        "successful": successful,
        "failed": failed,
        "skipped": skipped,
        "duration": duration
    }


def interactive_mode():
    """
    Interactive mode to select VMs for deletion.
    """
    log("Starting interactive deletion mode...", "INFO")
    
    # Fetch VMs
    vms = get_vms_with_recovery_points()
    
    if not vms:
        log("No VMs with recovery points found", "INFO")
        return
    
    log(f"", "INFO")
    log(f"Found {len(vms)} VMs with recovery points:", "INFO")
    log(f"", "INFO")
    
    # Display VMs
    for idx, vm in enumerate(vms, 1):
        print(f"{idx:3d}. {vm['vm_name']:<50} | Recovery Points: {vm['recovery_point_count']:>4}")
    
    print(f"\n{'='*80}")
    print("Selection Options:")
    print("  - Enter VM numbers separated by commas (e.g., 1,3,5)")
    print("  - Enter a range (e.g., 1-10)")
    print("  - Enter 'all' to select all VMs")
    print("  - Enter 'quit' to exit")
    print(f"{'='*80}\n")
    
    selection = input("Your selection: ").strip().lower()
    
    if selection == "quit":
        log("Exiting...", "INFO")
        return
    
    selected_vms = []
    
    if selection == "all":
        selected_vms = vms
    elif "-" in selection:
        try:
            start, end = map(int, selection.split("-"))
            selected_vms = vms[start-1:end]
        except:
            log("Invalid range format", "ERROR")
            return
    else:
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            selected_vms = [vms[i-1] for i in indices if 0 < i <= len(vms)]
        except:
            log("Invalid selection format", "ERROR")
            return
    
    if not selected_vms:
        log("No VMs selected", "INFO")
        return
    
    # Confirm and delete
    delete_recovery_points_bulk(selected_vms, confirm=True)


def main():
    """Main entry point."""
    import argparse
    
    # Declare globals at the start
    global PRISM_IP, USERNAME, PASSWORD, BASE_URL, V3_GROUPS_URL, V3_VMS_URL, V4_PROTECTED_RESOURCES_URL, V3_TASKS_URL
    
    parser = argparse.ArgumentParser(
        description="Delete VM Recovery Points",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (select VMs)
  python delete_recovery_points.py

  # Delete all recovery points for all VMs (with confirmation)
  python delete_recovery_points.py --all

  # Delete for specific VM by name
  python delete_recovery_points.py --vm-name "my-vm-01"

  # Delete for specific VM by UUID
  python delete_recovery_points.py --vm-uuid "12345678-1234-1234-1234-123456789abc"

  # Non-interactive mode (skip confirmation) - USE WITH CAUTION!
  python delete_recovery_points.py --all --yes
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Delete recovery points for all VMs")
    parser.add_argument("--vm-name", type=str, help="Delete recovery points for specific VM by name")
    parser.add_argument("--vm-uuid", type=str, help="Delete recovery points for specific VM by UUID")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts (USE WITH CAUTION!)")
    parser.add_argument("--pc-ip", type=str, help=f"Prism Central IP (default: {PRISM_IP})")
    parser.add_argument("--username", type=str, help=f"Username (default: {USERNAME})")
    parser.add_argument("--password", type=str, help="Password")
    
    args = parser.parse_args()
    
    if args.pc_ip:
        PRISM_IP = args.pc_ip
        BASE_URL = f"https://{PRISM_IP}:{PRISM_PORT}"
        V3_GROUPS_URL = f"{BASE_URL}/api/nutanix/v3/groups"
        V3_VMS_URL = f"{BASE_URL}/api/nutanix/v3/vms"
        V4_PROTECTED_RESOURCES_URL = f"{BASE_URL}/api/dataprotection/v4.3/config/protected-resources"
        V3_TASKS_URL = f"{BASE_URL}/api/nutanix/v3/tasks"
    
    if args.username:
        USERNAME = args.username
    
    if args.password:
        PASSWORD = args.password
    
    log(f"Prism Central: {PRISM_IP}", "INFO")
    log(f"Username: {USERNAME}", "INFO")
    log(f"", "INFO")
    
    # Fetch VMs
    vms = get_vms_with_recovery_points()
    
    if not vms:
        log("No VMs with recovery points found. Exiting.", "INFO")
        sys.exit(0)
    
    # Filter based on arguments
    selected_vms = []
    
    if args.all:
        selected_vms = vms
    elif args.vm_name:
        selected_vms = [vm for vm in vms if vm["vm_name"] == args.vm_name]
        if not selected_vms:
            log(f"VM with name '{args.vm_name}' not found", "ERROR")
            sys.exit(1)
    elif args.vm_uuid:
        selected_vms = [vm for vm in vms if vm["vm_uuid"] == args.vm_uuid]
        if not selected_vms:
            log(f"VM with UUID '{args.vm_uuid}' not found", "ERROR")
            sys.exit(1)
    else:
        # Interactive mode
        interactive_mode()
        sys.exit(0)
    
    # Execute deletion
    result = delete_recovery_points_bulk(selected_vms, confirm=not args.yes)
    
    # Exit with appropriate code
    if result["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
