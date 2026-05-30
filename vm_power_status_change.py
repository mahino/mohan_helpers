"""Bulk power on/off non-CVM VMs via Prism Central groups API and v4 AHVm $actions.

Use ``--action on`` (default) or ``--action off``, or env ``VM_POWER_ACTION=on|off``.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PC_BASE = os.environ.get("PC_URL", "https://10.53.55.54:9440").rstrip("/")
POWER_PARALLEL = max(2, min(int(os.environ.get("VM_POWER_PARALLEL", "4")), 32))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Bulk power on or off non-CVM VMs via Prism Central groups + v4 AHVm API."
    )
    default_action = (os.environ.get("VM_POWER_ACTION") or "on").strip().lower()
    if default_action not in ("on", "off"):
        default_action = "on"
    p.add_argument(
        "--action",
        choices=("on", "off"),
        default=default_action,
        help="Power VMs on (only those currently off) or off (only those currently on). "
        "Default: env VM_POWER_ACTION or on.",
    )
    return p.parse_args()

log_filename = f"vm_power_status_change_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_file = open(log_filename, "a")
_log_lock = threading.Lock()


def log_print(message: object) -> None:
    """Print to console and write to log file (thread-safe)."""
    with _log_lock:
        print(message)
        log_file.write(str(message) + "\n")
        log_file.flush()


def _request_headers() -> dict:
    """Fresh headers per HTTP call (avoids races when using threads)."""
    h = dict(_base_headers)
    h["ntnx-request-id"] = str(uuid.uuid4())
    return h


def change_power_state(
    vm_id: str,
    vm_name: str,
    action: str,
    target_state: str,
    wait_for_ip_address: bool = True,
) -> bool:
    """
    Change VM power state (on/off) and wait for completion.

    Returns:
        bool: True if power reached target_state (and IP wait succeeded when requested), False otherwise.
    """
    action_url = f"{PC_BASE}/api/vmm/v4.2/ahv/config/vms/{vm_id}/$actions/{action}"
    log_print(f"INFO: Powering {action.split('-')[1]} for vm [{vm_name}]")
    res = requests.request("POST", action_url, headers=_request_headers(), verify=False)
    log_print(f"DEBUG [{vm_name}] POST {action}: {res.content!r}")
    for attempt in range(10):
        check_url = f"{PC_BASE}/api/vmm/v4.0/ahv/config/vms/{vm_id}"
        res = requests.request("GET", check_url, headers=_request_headers(), verify=False)
        body = json.loads(res.content)
        if body["data"]["powerState"] == target_state:
            log_print(f"INFO: VM [{body['data']['name']}] powered {action.split('-')[1]}")
            if wait_for_ip_address:
                return wait_for_ip_address_to_be_assigned(vm_id, vm_name)
            return True
        log_print(
            f"INFO: waiting for powering {action.split('-')[1]} for VM [{body['data']['name']}] "
            f"(Attempt {attempt + 1}/10)"
        )
        time.sleep(5)
    return False


def wait_for_ip_address_to_be_assigned(vm_id: str, vm_name: str) -> bool:
    """Wait for an IPv4 to appear on the first NIC (guest tools / DHCP). Returns True if seen."""
    for attempt in range(60):
        check_url = f"{PC_BASE}/api/vmm/v4.0/ahv/config/vms/{vm_id}"
        res = requests.request("GET", check_url, headers=_request_headers(), verify=False)
        body = json.loads(res.content)
        try:
            nics = body["data"].get("nics") or []
            if not nics:
                raise KeyError("no nics")
            net = nics[0].get("networkInfo") or {}
            ipv4 = net.get("ipv4Info") or {}
            learned = ipv4.get("learnedIpAddresses") or []
            if learned and learned[0].get("value"):
                ip_val = learned[0]["value"]
                log_print(f"INFO: VM [{body['data']['name']}] got ip [{ip_val}]")
                return True
        except (KeyError, IndexError, TypeError):
            pass
        log_print(
            f"INFO: waiting for ip address for VM [{body['data']['name']}]: sleep 5s "
            f"(attempt {attempt + 1}/60)"
        )
        time.sleep(5)
    log_print(f"WARN: Timed out waiting for IP on VM [{vm_name}]")
    return False


# --- constants (extracted from .pyc at first HTTP request; vm_get_payload / power_on_payload unused in script) ---

vm_get_payload = {
    "action_on_failure": "CONTINUE",
    "api_request_list": [{"operation": "GET", "path_and_params": "/api/nutanix/v3/vms/"}],
    "api_version": "3.0",
    "execution_order": "NON_SEQUENTIAL",
}

vm_group_list = {
    "entity_type": "mh_vm",
    "filter_criteria": "is_cvm==0",
    "group_attributes": [],
    "group_count": 1,
    "group_member_attributes": [
        {"attribute": "vm_name"},
        {"attribute": "ip_addresses"},
        {"attribute": "power_state"},
    ],
    "group_member_count": 500,
    "group_member_offset": 0,
    "group_member_sort_attribute": "vm_name",
    "group_member_sort_order": "ASCENDING",
    "group_offset": 0,
    "grouping_attribute": " ",
    "query_name": "",
}

power_on_payload = {
    "action_on_failure": "CONTINUE",
    "api_request_list": [
        {
            "body": {
                "api_version": "3.1",
                "metadata": {
                    "categories": {},
                    "categories_mapping": {},
                    "creation_time": "2025-03-24T08:35:45Z",
                    "entity_version": "1",
                    "kind": "vm",
                    "last_update_time": "2025-03-24T08:39:00Z",
                    "owner_reference": {
                        "kind": "user",
                        "name": "admin",
                        "uuid": "00000000-0000-0000-0000-000000000000",
                    },
                    "project_reference": {
                        "kind": "project",
                        "name": "_internal",
                        "uuid": "fc794204-542e-4db3-bcdb-ed6f00a3e10f",
                    },
                    "spec_version": 1,
                    "uuid": "08b9b460-a26a-4382-969e-af096eeb923c",
                },
                "spec": {
                    "cluster_reference": {
                        "kind": "cluster",
                        "name": "bug_verify",
                        "uuid": "000630fa-16bc-c32d-0000-00000001c47e",
                    },
                    "name": "mainClone-1-100",
                    "resources": {
                        "apc_config": {"enabled": False},
                        "boot_config": {
                            "boot_device_order_list": ["CDROM", "DISK", "NETWORK"],
                            "boot_type": "LEGACY",
                        },
                        "cpu_hotplug_enabled": True,
                        "disable_branding": False,
                        "disk_list": [
                            {
                                "device_properties": {
                                    "device_type": "DISK",
                                    "disk_address": {"adapter_type": "SCSI", "device_index": 0},
                                },
                                "disk_size_bytes": 268435456,
                                "disk_size_mib": 256,
                                "storage_config": {
                                    "storage_container_reference": {
                                        "kind": "storage_container",
                                        "name": "SelfServiceContainer",
                                        "uuid": "d109dc95-1b70-41f4-9c3b-bfb651e1b9fc",
                                    }
                                },
                                "uuid": "bb968bc3-ac92-4c89-a810-5735bc7dbd2e",
                            }
                        ],
                        "enable_cpu_passthrough": False,
                        "gpu_console_enabled": False,
                        "gpu_list": [],
                        "hardware_clock_timezone": "UTC",
                        "hardware_virtualization_enabled": False,
                        "is_agent_vm": False,
                        "is_vcpu_hard_pinned": False,
                        "machine_type": "PC",
                        "memory_overcommit_enabled": False,
                        "memory_size_mib": 256,
                        "nic_list": [
                            {
                                "ip_endpoint_list": [],
                                "is_connected": True,
                                "mac_address": "50:6b:8d:f9:7b:1f",
                                "nic_type": "NORMAL_NIC",
                                "num_queues": 1,
                                "subnet_reference": {
                                    "kind": "subnet",
                                    "name": "vlan.114",
                                    "uuid": "75840779-d9c6-4c18-b258-24ba32023108",
                                },
                                "trunked_vlan_list": [],
                                "uuid": "75888a8f-e94a-4857-a35b-66b7a2a15148",
                                "vlan_mode": "ACCESS",
                            }
                        ],
                        "num_sockets": 1,
                        "num_threads_per_core": 1,
                        "num_vcpus_per_socket": 1,
                        "power_state": "ON",
                        "power_state_mechanism": {
                            "guest_transition_config": {
                                "enable_script_exec": False,
                                "should_fail_on_script_failure": False,
                            },
                            "mechanism": "HARD",
                        },
                        "scsi_controller_enabled": True,
                        "serial_port_list": [],
                        "vga_console_enabled": True,
                        "vnuma_config": {"num_vnuma_nodes": 0},
                        "vtpm_config": {"vtpm_enabled": False},
                    },
                },
            },
            "operation": "PUT",
            "path_and_params": "/api/nutanix/v3/vms/",
        }
    ],
    "api_version": "3.0",
    "execution_order": "NON_SEQUENTIAL",
}

_base_headers = {
    "Content-Type": "application/json",
    "Authorization": "Basic YWRtaW46TnV0YW5peC4xMjM=",
    "Cookie": (
        "NTNX_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U=; "
        "NTNX_MERCURY_IAM_REFRESH_TOKEN=ChlxNHJoaGFjdGF4c3Z2bnZyaTZibHBhNWlhEhliaXpkYTd5ZHVmeGRib3o2bmZzZ3JrZTVk; "
        "NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U="
    ),
}
headers = _base_headers


def _power_change_worker(vm_id: str, vm_name: str, *, want_on: bool) -> tuple[str, str, bool]:
    """Worker: power on (wait for IP) or power off (no IP wait). Returns (vm_id, vm_name, ok)."""
    if want_on:
        ok = change_power_state(vm_id, vm_name, "power-on", "ON", wait_for_ip_address=True)
    else:
        ok = change_power_state(vm_id, vm_name, "power-off", "OFF", wait_for_ip_address=False)
    return vm_id, vm_name, bool(ok)


def _run(args: argparse.Namespace) -> None:
    want_on = args.action == "on"
    log_print("=" * 80)
    log_print("VM Power Status Change Script Started")
    log_print("Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log_print(f"Log file: {log_filename}")
    log_print(f"Action: POWER {'ON' if want_on else 'OFF'} (--action / VM_POWER_ACTION)")
    if want_on:
        log_print(
            f"Parallel power-on + IP wait: up to {POWER_PARALLEL} VMs at a time (VM_POWER_PARALLEL)"
        )
    else:
        log_print(f"Parallel power-off: up to {POWER_PARALLEL} VMs at a time (VM_POWER_PARALLEL)")
    log_print(f"PC base URL: {PC_BASE}")
    log_print("=" * 80 + "\n")

    vm_count = 0
    queued = 0
    ok_count = 0
    fail_count = 0

    try:
        for i in range(8):
            vm_group_list["group_member_offset"] = 500 * i
            log_print("\n" + "=" * 80)
            log_print(f"Processing batch [{i + 1}/8] - Offset: {vm_group_list['group_member_offset']}")
            log_print("=" * 80)

            url = f"{PC_BASE}/api/nutanix/v3/groups"
            res = requests.request(
                "POST",
                url,
                headers=_request_headers(),
                data=json.dumps(vm_group_list),
                verify=False,
            )
            response = json.loads(res.content)
            to_change: list[tuple[str, str]] = []

            for vm in response["group_results"][0]["entity_results"]:
                vm_count += 1
                vm_name = vm["data"][0]["values"][0]["values"][0]
                vm_id = vm["entity_id"]
                current_power_state = vm["data"][2]["values"][0]["values"][0]
                ps = (current_power_state or "").strip().lower()
                log_print(f"\n--- VM [{vm_count}] ---")
                log_print(f"INFO: Get vm [{vm_name}]")
                log_print(f"UUID: {vm_id}")
                log_print(f"Power State: {current_power_state}")
                if want_on:
                    if ps != "off":
                        continue
                else:
                    if ps != "on":
                        continue
                queued += 1
                to_change.append((vm_id, vm_name))

            if not to_change:
                continue

            verb = "on" if want_on else "off"
            log_print(
                f"\nBatch {i + 1}: powering {verb} {len(to_change)} VM(s) "
                f"with up to {POWER_PARALLEL} concurrent workers…"
            )
            with ThreadPoolExecutor(max_workers=min(POWER_PARALLEL, len(to_change))) as pool:
                futures = {
                    pool.submit(_power_change_worker, vid, vname, want_on=want_on): (vid, vname)
                    for vid, vname in to_change
                }
                for fut in as_completed(futures):
                    vid, vname, ok = fut.result()
                    if ok:
                        ok_count += 1
                        log_print(f"RESULT OK: {vname} ({vid[:8]}…)")
                    else:
                        fail_count += 1
                        log_print(f"RESULT FAIL: {vname} ({vid[:8]}…)")
    except KeyboardInterrupt:
        log_print("\n\nScript interrupted by user")
    except Exception as e:
        log_print(f"\n\nERROR: {e}")
    finally:
        log_print("\n" + "=" * 80)
        log_print("SUMMARY")
        log_print("=" * 80)
        log_print(f"Total VMs Processed: {vm_count}")
        if want_on:
            log_print(f"VMs queued for power ON: {queued}")
            log_print(f"Power-on + IP wait succeeded: {ok_count}")
            log_print(f"Power-on + IP wait failed: {fail_count}")
        else:
            log_print(f"VMs queued for power OFF: {queued}")
            log_print(f"Power-off succeeded: {ok_count}")
            log_print(f"Power-off failed: {fail_count}")
        log_print("=" * 80)
        log_print(f"Log saved to: {log_filename}")
        log_print("Completed at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        log_print("=" * 80)
        log_file.close()


if __name__ == "__main__":
    _run(_parse_args())
