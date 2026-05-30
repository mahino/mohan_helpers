#!/usr/bin/env python3
"""
VM Memory Resize Test Script

This script performs a sequence of operations on a single VM:
1. Get list of VMs (first powered-off VM, or first VM if none powered-off)
2. Power off the VM (wait for task completion)
3. Update memory to 10GB (wait for task completion)
4. Power on the VM (wait for task completion)
5. Wait till CPU usage goes to <10%
6. Sleep 5s
7. Power off the VM (wait for task completion)
8. Update memory to 256MB (wait for task completion)
9. Power on the VM (wait for task completion)

Uses Prism v1/v2 APIs:
- v1 API: List VMs, check task status, get CPU stats
- v2 API: Power operations, update VM configuration
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

# API endpoints
BASE_URL = f"https://{PRISM_IP}:{PRISM_PORT}"
V1_VMS_URL = f"{BASE_URL}/PrismGateway/services/rest/v1/vms"
V2_VMS_URL = f"{BASE_URL}/PrismGateway/services/rest/v2.0/vms"
V2_SET_POWER_STATE_URL = f"{BASE_URL}/PrismGateway/services/rest/v2.0/vms"
V1_PROGRESS_MONITORS_URL = f"{BASE_URL}/PrismGateway/services/rest/v1/progress_monitors"

# Settings
CHECK_INTERVAL = 5  # seconds to wait between status checks
MAX_RETRIES = 60    # max number of status checks (5 minutes total for each operation)
CPU_CHECK_INTERVAL = 10  # seconds to wait between CPU checks
MAX_CPU_RETRIES = 60  # max number of CPU checks (10 minutes total)
CPU_THRESHOLD_PPM = 100000  # 10% CPU usage (in parts per million)

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


def get_all_vms():
    """
    Get all VMs from the cluster.
    Returns list of VMs, excluding control domains and CVMs.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    all_vms = []
    page = 1
    
    while True:
        params = {
            'count': 50,
            'page': page,
            'sortCriteria': '-hypervisor_cpu_usage_ppm',
            'searchAttributeList': 'vm_uuid',
            '_': str(int(time.time() * 1000)),
            'projection': 'stats,basicInfo,alerts',
            'filterCriteria': 'is_control_domain!=1;is_cvm==0'
        }
        
        try:
            log(f"Fetching VM list (page {page})...")
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
                break
            
            log(f"Found {len(entities)} VMs in page {page}")
            
            for entity in entities:
                vm_data = {
                    'uuid': entity.get('uuid'),
                    'vmId': entity.get('vmId'),
                    'name': entity.get('vmName'),
                    'power_state': entity.get('powerState')
                }
                all_vms.append(vm_data)
            
            # Check if we've fetched all VMs
            total_entities = metadata.get('totalEntities', 0)
            end_index = metadata.get('endIndex', 0)
            
            if end_index >= total_entities:
                log(f"Fetched all VMs (total: {len(all_vms)})")
                break
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            log(f"Error fetching VMs: {e}", "ERROR")
            if hasattr(e, 'response') and e.response:
                log(f"Response: {e.response.text}", "ERROR")
            break
    
    return all_vms


def get_vm_details(vm_uuid, vm_name, vm_index, total_vms):
    """
    Get detailed VM configuration using v2 API.
    Returns the full VM configuration needed for updates.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    params = {
        'include_vm_disk_config': 'true',
        'include_vm_nic_config': 'true',
        '__': str(int(time.time() * 1000))
    }
    
    try:
        response = requests.get(
            f"{V2_VMS_URL}/{vm_uuid}",
            headers=headers,
            params=params,
            verify=False,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Error getting VM details: {e}", "ERROR")
        if hasattr(e, 'response') and e.response:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Response: {e.response.text}", "ERROR")
        return None


def power_off_vm(vm_uuid, vm_name, vm_index, total_vms):
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
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Sending power off request")
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
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Power off task initiated: {task_uuid}")
            return task_uuid
        else:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] No task_uuid in response", "ERROR")
            return None
        
    except requests.exceptions.RequestException as e:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Error powering off: {e}", "ERROR")
        if hasattr(e, 'response') and e.response:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Response: {e.response.text}", "ERROR")
        return None


def power_on_vm(vm_uuid, vm_name, vm_index, total_vms):
    """
    Power on a VM using v2 API.
    Returns task_uuid if successful, None otherwise.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    payload = {"transition": "on"}
    
    try:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Sending power on request")
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
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Power on task initiated: {task_uuid}")
            return task_uuid
        else:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] No task_uuid in response", "ERROR")
            return None
        
    except requests.exceptions.RequestException as e:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Error powering on: {e}", "ERROR")
        if hasattr(e, 'response') and e.response:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Response: {e.response.text}", "ERROR")
        return None


def update_vm_memory(vm_uuid, vm_name, memory_mb, vm_index, total_vms):
    """
    Update VM memory using v2 API PUT request.
    Returns task_uuid if successful, None otherwise.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    # Get current VM configuration
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Fetching current VM configuration for memory update")
    vm_details = get_vm_details(vm_uuid, vm_name, vm_index, total_vms)
    if not vm_details:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Failed to get VM details for memory update", "ERROR")
        return None
    
    # Prepare update payload with minimal required fields
    payload = {
        "name": vm_details.get("name"),
        "memory_mb": memory_mb,
        "num_vcpus": vm_details.get("num_vcpus"),
        "num_cores_per_vcpu": vm_details.get("num_cores_per_vcpu"),
        "timezone": vm_details.get("timezone", "UTC")
    }
    
    # Include boot config if present
    if "boot" in vm_details:
        boot_config = vm_details["boot"]
        payload["boot"] = {
            "uefi_boot": boot_config.get("uefi_boot", False),
            "boot_device_type": boot_config.get("boot_device_type", "DISK").upper()
        }
        if "disk_address" in boot_config:
            payload["boot"]["disk_address"] = boot_config["disk_address"]
    
    # Include machine type if present
    if "machine_type" in vm_details:
        payload["machine_type"] = vm_details["machine_type"].upper()
    
    # Include VM features if present
    if "vm_features" in vm_details:
        payload["vm_features"] = vm_details["vm_features"]
    
    params = {
        'include_vm_disk_config': 'true',
        'include_vm_nic_config': 'true',
        'includeVMDiskSizes': 'true',
        'includeAddressAssignments': 'true'
    }
    
    try:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Updating memory to {memory_mb} MB ({memory_mb/1024:.1f} GB)")
        response = requests.put(
            f"{V2_VMS_URL}/{vm_uuid}",
            headers=headers,
            params=params,
            data=json.dumps(payload),
            verify=False,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        task_uuid = result.get('task_uuid')
        
        if task_uuid:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Memory update task initiated: {task_uuid}")
            return task_uuid
        else:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Memory update completed (no task_uuid returned)", "WARNING")
            return "completed"
        
    except requests.exceptions.RequestException as e:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Error updating VM memory: {e}", "ERROR")
        if hasattr(e, 'response') and e.response:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Response: {e.response.text}", "ERROR")
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


def wait_for_task_completion(task_uuid, vm_name, operation, vm_index, total_vms):
    """
    Wait for task to complete using progress_monitors API.
    Returns True if succeeded, False if failed or timeout.
    """
    if task_uuid == "completed":
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] {operation} completed immediately (no async task)")
        return True
    
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Waiting for {operation} to complete...")
    
    for attempt in range(1, MAX_RETRIES + 1):
        time.sleep(CHECK_INTERVAL)
        
        task_status = check_task_status(task_uuid)
        status = task_status.get('status', 'unknown')
        percentage = task_status.get('percentageCompleted', 0)
        
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Check {attempt}/{MAX_RETRIES}: Status = {status}, Progress = {percentage}%")
        
        if status == 'succeeded':
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] ✓ {operation} completed successfully", "SUCCESS")
            return True
        elif status in ['failed', 'error', 'aborted']:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] ✗ {operation} failed: {status}", "ERROR")
            return False
    
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] ✗ Timeout waiting for {operation}", "WARNING")
    return False


def get_vm_cpu_usage(vm_id, vm_name, vm_index, total_vms):
    """
    Get VM CPU usage using v1 stats API.
    Returns CPU usage in parts per million (ppm), or None if error.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': make_auth_header()
    }
    
    # Get last 5 minutes of stats
    end_time = int(time.time() * 1000000)  # microseconds
    start_time = end_time - (5 * 60 * 1000000)  # 5 minutes ago
    
    params = {
        'metrics': 'hypervisor_cpu_usage_ppm',
        'startTimeInUsecs': start_time,
        'endTimeInUsecs': end_time,
        'intervalInSecs': 60,
        '__': str(int(time.time() * 1000))
    }
    
    try:
        # Note: vmId format is "clusterId::uuid"
        response = requests.get(
            f"{V1_VMS_URL}/{vm_id}/stats",
            headers=headers,
            params=params,
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        stats_responses = data.get('statsSpecificResponses', [])
        
        if stats_responses:
            for stat in stats_responses:
                if stat.get('metric') == 'hypervisor_cpu_usage_ppm':
                    values = stat.get('values', [])
                    # Get the last non-zero value
                    for value in reversed(values):
                        if value > 0:
                            return value
                    # If all zeros, return 0
                    return 0
        
        return None
        
    except requests.exceptions.RequestException as e:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Error getting CPU stats: {e}", "ERROR")
        return None


def wait_for_low_cpu(vm_id, vm_name, vm_index, total_vms):
    """
    Wait until VM CPU usage drops below threshold.
    Returns True if CPU drops below threshold, False on timeout.
    """
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Waiting for CPU usage to drop below {CPU_THRESHOLD_PPM/10000}%...")
    
    for attempt in range(1, MAX_CPU_RETRIES + 1):
        time.sleep(CPU_CHECK_INTERVAL)
        
        cpu_usage_ppm = get_vm_cpu_usage(vm_id, vm_name, vm_index, total_vms)
        
        if cpu_usage_ppm is None:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Check {attempt}/{MAX_CPU_RETRIES}: Unable to get CPU stats", "WARNING")
            continue
        
        cpu_percentage = cpu_usage_ppm / 10000  # Convert ppm to percentage
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Check {attempt}/{MAX_CPU_RETRIES}: CPU usage = {cpu_percentage:.1f}%")
        
        if cpu_usage_ppm < CPU_THRESHOLD_PPM:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] ✓ CPU usage is below threshold ({cpu_percentage:.1f}% < {CPU_THRESHOLD_PPM/10000}%)", "SUCCESS")
            return True
    
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] ✗ Timeout waiting for CPU to drop below threshold", "WARNING")
    return False


def process_single_vm(vm, vm_index, total_vms):
    """
    Process a single VM through the full test sequence.
    Returns True if successful, False otherwise.
    """
    vm_uuid = vm['uuid']
    vm_id = vm['vmId']
    vm_name = vm['name']
    vm_power_state = vm['power_state']
    
    log("")
    log("=" * 80)
    log(f"PROCESSING VM {vm_index}/{total_vms}: {vm_name}")
    log("=" * 80)
    log(f"UUID: {vm_uuid}")
    log(f"VM ID: {vm_id}")
    log(f"Initial Power State: {vm_power_state}")
    log("=" * 80)
    log("")
    
    # Step 2: Power off if not already off
    if vm_power_state != 'off':
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 2: Powering off VM...")
        log("-" * 80)
        task_uuid = power_off_vm(vm_uuid, vm_name, vm_index, total_vms)
        if not task_uuid:
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Failed to power off VM", "ERROR")
            return False
        
        if not wait_for_task_completion(task_uuid, vm_name, "Power off", vm_index, total_vms):
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Power off operation failed", "ERROR")
            return False
        log("")
    else:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 2: VM is already powered off. Skipping.")
        log("")
    
    # Step 3: Update memory to 10GB
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 3: Updating memory to 10GB...")
    log("-" * 80)
    task_uuid = update_vm_memory(vm_uuid, vm_name, 10240, vm_index, total_vms)  # 10GB = 10240MB
    if not task_uuid:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Failed to update memory to 10GB", "ERROR")
        return False
    
    if task_uuid != "completed":
        if not wait_for_task_completion(task_uuid, vm_name, "Memory update to 10GB", vm_index, total_vms):
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Memory update to 10GB failed", "ERROR")
            return False
    log("")
    
    # Step 4: Power on VM
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 4: Powering on VM...")
    log("-" * 80)
    task_uuid = power_on_vm(vm_uuid, vm_name, vm_index, total_vms)
    if not task_uuid:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Failed to power on VM", "ERROR")
        return False
    
    if not wait_for_task_completion(task_uuid, vm_name, "Power on", vm_index, total_vms):
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Power on operation failed", "ERROR")
        return False
    log("")
    
    # Step 5: Wait for CPU to drop below 10%
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 5: Waiting for CPU usage to drop below 10%...")
    log("-" * 80)
    if not wait_for_low_cpu(vm_id, vm_name, vm_index, total_vms):
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] CPU did not drop below threshold in time. Continuing anyway...", "WARNING")
    log("")
    
    # Step 6: Sleep 5 seconds
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 6: Sleeping for 5 seconds...")
    log("-" * 80)
    time.sleep(5)
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Sleep completed")
    log("")
    
    # Step 7: Power off VM
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 7: Powering off VM...")
    log("-" * 80)
    task_uuid = power_off_vm(vm_uuid, vm_name, vm_index, total_vms)
    if not task_uuid:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Failed to power off VM", "ERROR")
        return False
    
    if not wait_for_task_completion(task_uuid, vm_name, "Power off", vm_index, total_vms):
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Power off operation failed", "ERROR")
        return False
    log("")
    
    # Step 8: Update memory to 256MB
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 8: Updating memory to 256MB...")
    log("-" * 80)
    task_uuid = update_vm_memory(vm_uuid, vm_name, 256, vm_index, total_vms)  # 256MB
    if not task_uuid:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Failed to update memory to 256MB", "ERROR")
        return False
    
    if task_uuid != "completed":
        if not wait_for_task_completion(task_uuid, vm_name, "Memory update to 256MB", vm_index, total_vms):
            log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Memory update to 256MB failed", "ERROR")
            return False
    log("")
    
    # Step 9: Power on VM
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] STEP 9: Powering on VM...")
    log("-" * 80)
    task_uuid = power_on_vm(vm_uuid, vm_name, vm_index, total_vms)
    if not task_uuid:
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Failed to power on VM", "ERROR")
        return False
    
    if not wait_for_task_completion(task_uuid, vm_name, "Power on", vm_index, total_vms):
        log(f"[VM {vm_index}/{total_vms}] [{vm_name}] Power on operation failed", "ERROR")
        return False
    log("")
    
    # VM completed successfully
    log("=" * 80)
    log(f"[VM {vm_index}/{total_vms}] [{vm_name}] ✓ VM COMPLETED SUCCESSFULLY", "SUCCESS")
    log("=" * 80)
    log(f"VM Name: {vm_name}")
    log(f"UUID: {vm_uuid}")
    log(f"Final State: Powered On with 256MB RAM")
    log("=" * 80)
    
    return True


def main():
    """Main execution function."""
    log("=" * 80)
    log("VM MEMORY RESIZE TEST SCRIPT - ALL VMS")
    log("=" * 80)
    log(f"Prism Central: {PRISM_IP}")
    log(f"Check Interval: {CHECK_INTERVAL}s")
    log(f"Max Retries: {MAX_RETRIES}")
    log(f"CPU Check Interval: {CPU_CHECK_INTERVAL}s")
    log(f"CPU Threshold: {CPU_THRESHOLD_PPM/10000}%")
    log("=" * 80)
    log("")
    
    # Step 1: Get all VMs
    log("STEP 1: Getting all VMs from cluster...")
    log("-" * 80)
    vms = get_all_vms()
    if not vms:
        log("No VMs found in the cluster!", "ERROR")
        return 1
    
    total_vms = len(vms)
    log(f"Found {total_vms} VMs to process")
    log("")
    
    # Print VM list
    log("VM LIST:")
    log("-" * 80)
    for idx, vm in enumerate(vms, 1):
        log(f"{idx}. {vm['name']} (UUID: {vm['uuid']}, Power State: {vm['power_state']})")
    log("")
    
    # Statistics
    successful_vms = []
    failed_vms = []
    
    # Process each VM
    start_time = time.time()
    
    for index, vm in enumerate(vms, 1):
        try:
            success = process_single_vm(vm, index, total_vms)
            if success:
                successful_vms.append(vm['name'])
            else:
                failed_vms.append(vm['name'])
        except Exception as e:
            log(f"[VM {index}/{total_vms}] [{vm['name']}] Unexpected error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            failed_vms.append(vm['name'])
        
        # Small delay between VMs to avoid overwhelming the API
        if index < total_vms:
            log("")
            log(f"Waiting 10 seconds before processing next VM...")
            time.sleep(10)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Final summary
    log("")
    log("=" * 80)
    log("ALL VMS PROCESSING COMPLETED")
    log("=" * 80)
    log(f"Total VMs: {total_vms}")
    log(f"Successful: {len(successful_vms)}")
    log(f"Failed: {len(failed_vms)}")
    log(f"Success Rate: {(len(successful_vms)/total_vms*100):.1f}%" if total_vms > 0 else "N/A")
    log(f"Total Duration: {total_duration/60:.1f} minutes ({total_duration:.0f} seconds)")
    log(f"Average Time per VM: {total_duration/total_vms:.1f} seconds" if total_vms > 0 else "N/A")
    log("=" * 80)
    
    if successful_vms:
        log("")
        log("SUCCESSFUL VMs:")
        for vm_name in successful_vms:
            log(f"  ✓ {vm_name}")
    
    if failed_vms:
        log("")
        log("FAILED VMs:")
        for vm_name in failed_vms:
            log(f"  ✗ {vm_name}")
    
    log("=" * 80)
    
    return 0 if len(failed_vms) == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\nScript interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
