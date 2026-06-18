#!/usr/bin/env python3
"""
Script to power off VMs sequentially (one by one) with status checking.

Uses Prism v1/v2 APIs only:
- v1 API: List VMs and check task status
- v2 API: Power off VMs
"""

import requests
import json
import time
import urllib3
import sys
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================== CONFIGURATION ==========================
# Update these values for your environment
PRISM_IP = "10.46.117.165"
PRISM_PORT = "9440"
USERNAME = "admin"
PASSWORD = "Nutanix.123"

# API endpoints (v1/v2 only)
BASE_URL = f"https://{PRISM_IP}:{PRISM_PORT}"
V1_VMS_URL = f"{BASE_URL}/PrismGateway/services/rest/v1/vms"
V2_SET_POWER_STATE_URL = f"{BASE_URL}/PrismGateway/services/rest/v2.0/vms"
V1_PROGRESS_MONITORS_URL = f"{BASE_URL}/PrismGateway/services/rest/v1/progress_monitors"

# Power off settings
CHECK_INTERVAL = 5  # seconds to wait between status checks
MAX_RETRIES = 12    # max number of status checks (60 seconds total)
PAGE_SIZE = 50      # number of VMs to fetch per page

# Optional: Filter VMs by name pattern (set to None to process all VMs)
VM_NAME_FILTER = None  # Example: "ahv_ins_delete" to only process matching VMs
# VM_NAME_FILTER = "ahv_ins_delete"  # Uncomment to filter

# Optional: Limit number of VMs to process (set to None for no limit)
MAX_VMS_TO_PROCESS = None  # Example: 10 to process only first 10 VMs
# MAX_VMS_TO_PROCESS = 10  # Uncomment to limit

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


def get_vms_using_v1_api():
    """
    Get list of all powered-on VMs using v1 API.
    Uses GET request with all query parameters from Untitled-3.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    all_vms = []
    page = 1
    
    while True:
        log(f"Fetching VMs (page: {page})...")
        
        # Build query parameters - ALL from Untitled-3
        params = {
            'count': PAGE_SIZE,
            'page': page,
            'sortCriteria': '-hypervisor_cpu_usage_ppm',
            'searchAttributeList': 'vm_uuid',
            '_': str(int(time.time() * 1000)),  # Cache buster timestamp
            'projection': 'stats,basicInfo,alerts',
            'filterCriteria': 'is_control_domain!=1;is_cvm==0'
        }
        
        try:
            response = requests.get(
                V1_VMS_URL,
                headers=headers,
                params=params,
                verify=False,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            metadata = data.get('metadata', {})
            entities = data.get('entities', [])
            
            if not entities:
                log("No more VMs found")
                break
            
            log(f"Found {len(entities)} VMs in this batch (page {page})")
            
            for entity in entities:
                vm_uuid = entity.get('uuid')
                vm_name = entity.get('vmName')
                power_state = entity.get('powerState')
                
                # Filter for powered-on VMs only
                if power_state != 'on':
                    continue
                
                # Apply name filter if configured
                if VM_NAME_FILTER and VM_NAME_FILTER not in vm_name:
                    continue
                
                all_vms.append({
                    'uuid': vm_uuid,
                    'name': vm_name,
                    'power_state': power_state
                })
            
            # Check if we've fetched all VMs
            total_entities = metadata.get('totalEntities', 0)
            end_index = metadata.get('endIndex', 0)
            
            if end_index >= total_entities:
                log(f"Reached end of VM list (total: {total_entities})")
                break
            
            # Stop if we've reached the max VMs limit
            if MAX_VMS_TO_PROCESS and len(all_vms) >= MAX_VMS_TO_PROCESS:
                all_vms = all_vms[:MAX_VMS_TO_PROCESS]
                break
            
            page += 1
        except requests.exceptions.RequestException as e:
            log(f"Error fetching VMs: {e}", "ERROR")
            if hasattr(e, 'response') and e.response:
                log(f"Response: {e.response.text}", "ERROR")
            break
    
    return all_vms


def power_off_vm(vm_uuid, vm_name, index, total_vms):
    """
    Power off a VM using v2 API.
    Returns task_uuid if successful, None otherwise.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    payload = {"transition": "off"}
    
    try:
        log(f"Processing VM {index}/{total_vms}: Sending power off request for: {vm_name}")
        response = requests.post(
            f"{V2_SET_POWER_STATE_URL}/{vm_uuid}/set_power_state",
            headers=headers,
            data=json.dumps(payload),
            verify=False,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        task_uuid = result.get('task_uuid')
        
        if task_uuid:
            log(f"Processing VM {index}/{total_vms}: Power off task initiated: {task_uuid}")
            return task_uuid
        else:
            log(f"No task_uuid in response", "ERROR")
            return None
        
    except requests.exceptions.RequestException as e:
        log(f"Error powering off VM {vm_name}: {e}", "ERROR")
        if hasattr(e, 'response') and e.response:
            log(f"Response: {e.response.text}", "ERROR")
        return None


def check_task_status(task_uuid):
    """
    Check task status using v1 progress_monitors API.
    Returns dict with 'status' and 'percentageCompleted'.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    params = {
        'filterCriteria': f'uuid=={task_uuid}'
    }
    
    try:
        response = requests.get(
            V1_PROGRESS_MONITORS_URL,
            headers=headers,
            params=params,
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        entities = data.get('entities', [])
        
        if entities:
            task = entities[0]
            return {
                'status': task.get('status', 'unknown'),
                'percentageCompleted': task.get('percentageCompleted', 0),
                'taskDisplayName': task.get('taskDisplayName', '')
            }
        else:
            return {'status': 'not_found', 'percentageCompleted': 0}
            
    except requests.exceptions.RequestException as e:
        log(f"Error checking task status: {e}", "ERROR")
        return {'status': 'error', 'percentageCompleted': 0}


def wait_for_task_completion(task_uuid, vm_name, index, total_vms):
    """
    Wait for task to complete using progress_monitors API.
    Returns True if succeeded, False if failed or timeout.
    """
    log(f"Processing VM {index}/{total_vms}: Waiting for {vm_name} power off task to complete...")
    
    for attempt in range(1, MAX_RETRIES + 1):
        time.sleep(CHECK_INTERVAL)
        
        task_status = check_task_status(task_uuid)
        status = task_status.get('status', 'unknown')
        percentage = task_status.get('percentageCompleted', 0)
        
        log(f"Processing VM {index}/{total_vms}: Check {attempt}/{MAX_RETRIES}: Status = {status}, Progress = {percentage}%")
        
        if status == 'succeeded':
            log(f"✓ {vm_name} is now powered off", "SUCCESS")
            return True
        elif status in ['failed', 'error', 'aborted']:
            log(f"✗ Task failed for {vm_name}: {status}", "ERROR")
            return False
    
    log(f"✗ Timeout waiting for {vm_name} to power off", "WARNING")
    return False


def main():
    """Main execution function."""
    log("=" * 80)
    log("VM SEQUENTIAL POWER OFF SCRIPT")
    log("=" * 80)
    log(f"Prism Central: {PRISM_IP}")
    log(f"Page Size: {PAGE_SIZE}")
    log(f"Check Interval: {CHECK_INTERVAL}s")
    log(f"Max Retries: {MAX_RETRIES}")
    if VM_NAME_FILTER:
        log(f"VM Name Filter: {VM_NAME_FILTER}")
    if MAX_VMS_TO_PROCESS:
        log(f"Max VMs to Process: {MAX_VMS_TO_PROCESS}")
    log("=" * 80)
    log("")
    
    # Get list of VMs
    log("Step 1: Fetching list of powered-on VMs...")
    vms = get_vms_using_v1_api()
    
    if not vms:
        log("No powered-on VMs found!", "WARNING")
        return
    
    log(f"Found {len(vms)} powered-on VMs to process")
    log("")
    
    # Statistics
    total_vms = len(vms)
    successful = 0
    failed = 0
    
    # Process each VM
    log("Step 2: Powering off VMs sequentially...")
    log("")
    
    for index, vm in enumerate(vms, 1):
        log("-" * 80)
        log(f"Processing VM {index}/{total_vms}")
        log(f"Name: {vm['name']}")
        log(f"UUID: {vm['uuid']}")
        log("-" * 80)
        
        # Power off the VM
        task_uuid = power_off_vm(vm['uuid'], vm['name'], index, total_vms)
        if task_uuid:
            # Wait for task to complete
            if wait_for_task_completion(task_uuid, vm['name'], index, total_vms):
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
        
        log("")
        
        # Small delay between VMs to avoid overwhelming the API
        if index < total_vms:
            time.sleep(2)
    
    # Final summary
    log("=" * 80)
    log("POWER OFF OPERATION COMPLETED")
    log("=" * 80)
    log(f"Total VMs Processed: {total_vms}")
    log(f"Successfully Powered Off: {successful}")
    log(f"Failed: {failed}")
    log(f"Success Rate: {(successful/total_vms*100):.1f}%" if total_vms > 0 else "N/A")
    log("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nScript interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
