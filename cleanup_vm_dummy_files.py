#!/usr/bin/env python3
"""
Script to fetch VMs from Prism Element and delete /root/dummy* files via SSH.

Usage:
    python3 cleanup_vm_dummy_files.py <pe_ip> <pe_user> <pe_pass>
    
Example:
    python3 cleanup_vm_dummy_files.py 10.46.117.165 admin 'YourPassword'
"""

import sys
import json
import subprocess
import urllib3
from typing import List, Dict, Tuple

import requests

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# VM SSH credentials
VM_SSH_USER = "root"
VM_SSH_PASSWORD = "nutanix/4u"
PE_IP = "10.46.117.165"
PE_USER = 'admin'
PE_PASSWORD = 'Nutanix.123'

def fetch_vms_from_pe(pe_ip: str, pe_user: str, pe_password: str) -> List[Dict]:
    """
    Fetch all VMs from Prism Element using v1 API.
    Returns list of VM dictionaries with name, IP, power state, etc.
    """
    print(f"\n=== Fetching VMs from Prism Element: {pe_ip} ===")
    
    vms = []
    page = 1
    page_size = 500
    
    while True:
        url = (
            f"https://{pe_ip}:9440/PrismGateway/services/rest/v1/vms"
            f"?count={page_size}&page={page}"
            f"&projection=basicInfo"
            f"&filterCriteria=is_control_domain!=1"
        )
        
        try:
            response = requests.get(
                url,
                auth=(pe_user, pe_password),
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            entities = data.get("entities", [])
            
            if not entities:
                break
            
            vms.extend(entities)
            
            metadata = data.get("metadata", {})
            total_entities = metadata.get("totalEntities", 0)
            end_index = metadata.get("endIndex", 0)
            
            print(f"  Fetched page {page}: {len(entities)} VMs (total so far: {len(vms)}/{total_entities})")
            
            # Check if we've fetched all VMs
            if end_index >= total_entities:
                break
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching VMs from {pe_ip}: {e}")
            sys.exit(1)
    
    print(f"✅ Total VMs fetched: {len(vms)}")
    return vms


def filter_vms_for_cleanup(vms: List[Dict]) -> List[Tuple[str, str]]:
    """
    Filter VMs that are powered on and have IP addresses.
    Returns list of tuples: (vm_name, vm_ip)
    """
    cleanup_vms = []
    
    for vm in vms:
        vm_name = vm.get("vmName", "")
        power_state = vm.get("powerState", "")
        ip_addresses = vm.get("ipAddresses", [])
        
        if power_state == "on" and ip_addresses:
            vm_ip = ip_addresses[0]  # Use first IP
            cleanup_vms.append((vm_name, vm_ip))
    
    print(f"\n=== VMs eligible for cleanup: {len(cleanup_vms)} ===")
    print(f"  (Filtered: powered ON + has IP address)")
    
    return cleanup_vms


def delete_dummy_files_on_vm(vm_name: str, vm_ip: str) -> bool:
    """
    SSH to a VM and delete all /root/dummy* files.
    Returns True if successful, False otherwise.
    """
    # Check if sshpass is available
    try:
        subprocess.run(
            ["which", "sshpass"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print("❌ ERROR: sshpass is not installed. Please install it:")
        print("   Ubuntu/Debian: sudo apt-get install sshpass")
        print("   CentOS/RHEL:   sudo yum install sshpass")
        sys.exit(1)
    
    # Command to delete dummy files
    delete_cmd = "rm -fv /root/dummy* 2>&1"
    
    # SSH command
    ssh_command = [
        "sshpass",
        "-p", VM_SSH_PASSWORD,
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=10",
        f"{VM_SSH_USER}@{vm_ip}",
        delete_cmd
    ]
    
    try:
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                # Files were deleted
                deleted_files = [line for line in output.split('\n') if line.startswith('removed')]
                if deleted_files:
                    print(f"  ✅ {vm_name} ({vm_ip}): Deleted {len(deleted_files)} file(s)")
                    for line in deleted_files[:3]:  # Show first 3 files
                        print(f"     - {line}")
                    if len(deleted_files) > 3:
                        print(f"     ... and {len(deleted_files) - 3} more")
                else:
                    print(f"  ✅ {vm_name} ({vm_ip}): No dummy files found")
            else:
                print(f"  ✅ {vm_name} ({vm_ip}): No dummy files found")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"  ❌ {vm_name} ({vm_ip}): SSH failed - {error_msg}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ {vm_name} ({vm_ip}): SSH timeout")
        return False
    except Exception as e:
        print(f"  ❌ {vm_name} ({vm_ip}): Error - {str(e)}")
        return False


def main():

    
    pe_ip = PE_IP
    pe_user = PE_USER
    pe_password = PE_PASSWORD
    
    print("=" * 80)
    print("VM Dummy Files Cleanup Script")
    print("=" * 80)
    print(f"Prism Element: {pe_ip}")
    print(f"PE User:       {pe_user}")
    print(f"VM SSH User:   {VM_SSH_USER}")
    print(f"Target Files:  /root/dummy*")
    print("=" * 80)
    
    # Step 1: Fetch VMs from PE
    vms = fetch_vms_from_pe(pe_ip, pe_user, pe_password)
    
    if not vms:
        print("\n❌ No VMs found on this cluster")
        sys.exit(1)
    
    # Step 2: Filter VMs for cleanup (powered on + has IP)
    cleanup_vms = filter_vms_for_cleanup(vms)
    
    if not cleanup_vms:
        print("\n❌ No VMs eligible for cleanup (need: powered ON + IP address)")
        sys.exit(1)
    
    # Step 3: Ask for confirmation
    print(f"\n⚠️  About to SSH to {len(cleanup_vms)} VMs and delete /root/dummy* files")
    response = input("Continue? [y/N]: ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("❌ Aborted by user")
        sys.exit(0)
    
    # Step 4: Clean up each VM
    print(f"\n=== Cleaning up {len(cleanup_vms)} VMs ===")
    
    success_count = 0
    failed_count = 0
    
    for vm_name, vm_ip in cleanup_vms:
        if delete_dummy_files_on_vm(vm_name, vm_ip):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Total VMs:     {len(cleanup_vms)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed:     {failed_count}")
    print("=" * 80)
    
    if failed_count > 0:
        print("\n⚠️  Some VMs failed - possible reasons:")
        print("  - VM is not reachable via SSH")
        print("  - SSH credentials are incorrect")
        print("  - VM firewall blocking SSH")
        print("  - VM doesn't have SSH server installed")
    
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
