""" Nucalm environment setup"""


import os
import re
import sys
import json
import uuid
import time
import requests
import urllib3
from requests.auth import HTTPBasicAuth
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/calm/v3.0/'

URL = BASE_URL + V3

update_url = f"https://10.53.60.176:9440/api/nutanix/v3/batch"
def convert_to_case_insensitive_pattern(pattern):
    """Convert a string pattern to case-insensitive regex pattern.
    Example: 'tiny' -> '[t|T][i|I][n|N][y|Y]'
    """
    return ''.join([f'[{char.lower()}|{char.upper()}]' for char in pattern])

groups_payload = {
  "length": 20,
  "offset": 0,
  "sort": "created_on",
  "sort_order": "DESCENDING",
  "fields": [
    "app_name",
    "uuid",
    "categories",
    "project_name",
    "account_names",
    "substrate_types",
    "source_marketplace_name",
    "state",
    "environment",
    "marketplace_version",
    "vm_names",
    "owner",
    "app_url",
    "created_on",
    "updated_on",
    "protection_status",
    "failover_status"
  ],
  "filter": "app_family==Other_Apps;(source_marketplace_name!=NCM_APP;source_marketplace_name!=MST_APP;source_marketplace_name!=NC_APP;source_marketplace_name!=NDB_APP;source_marketplace_name!=DL_APP);state!=deleted;app_family==Other_Apps"
}

vm_list_group_url = "https://10.53.60.176:9440/api/nutanix/v3/groups"
vm_list_group_pay = {
    "entity_type": "mh_vm",
    "query_name": "",
    "grouping_attribute": " ",
    "group_count": 500,
    "group_offset": 0,
    "group_attributes": [],
    "group_member_count": 20,
    "group_member_offset": 0,
    "group_member_sort_attribute": "vm_name",
    "group_member_sort_order": "ASCENDING",
    "group_member_attributes": [
        {
            "attribute": "vm_name"
        },
        {
            "attribute": "power_state"
        },
        {
            "attribute": "num_vcpus"
        },
        {
            "attribute": "memory_size_bytes"
        },
        {
            "attribute": "ip_addresses"
        },
        {
            "attribute": "cluster_name"
        },
        {
            "attribute": "hypervisor_type"
        },
        {
            "attribute": "guest_os_name"
        },
        {
            "attribute": "project_name"
        },
        {
            "attribute": "owner_username"
        },
        {
            "attribute": "project_reference"
        },
        {
            "attribute": "owner_reference"
        },
        {
            "attribute": "categories"
        },
        {
            "attribute": "cluster"
        },
        {
            "attribute": "state"
        },
        {
            "attribute": "message"
        },
        {
            "attribute": "reason"
        },
        {
            "attribute": "is_cvm"
        },
        {
            "attribute": "is_acropolis_vm"
        },
        {
            "attribute": "ngt.installed_version"
        },
        {
            "attribute": "is_live_migratable"
        },
        {
            "attribute": "gpus_in_use"
        },
        {
            "attribute": "network_security_rule_id_list"
        },
        {
            "attribute": "zone_type"
        },
        {
            "attribute": "vm_annotation"
        },
        {
            "attribute": "vm_type"
        },
        {
            "attribute": "capacity.policy_anomaly_detail"
        },
        {
            "attribute": "capacity.policy_efficiency_detail"
        },
        {
            "attribute": "protection_type"
        },
        {
            "attribute": "memory_overcommit"
        },
        {
            "attribute": "ngt.guest_os"
        },
        {
            "attribute": "ngt.enabled_applications"
        },
        {
            "attribute": "ngt.cluster_version"
        },
        {
            "attribute": "node_name"
        },
        {
            "attribute": "node"
        },
        {
            "attribute": "is_agent_vm"
        },
        {
            "attribute": "volume_group"
        },
        {
            "attribute": "protection_policy_state"
        },
        {
            "attribute": "cbr_not_capable_reason"
        },
        {
            "attribute": "ngt.communication_active"
        },
        {
            "attribute": "ngt.communication_over_serial_port_active"
        },
        {
            "attribute": "vpc_name"
        },
        {
            "attribute": "ngt.enabled"
        },
        {
            "attribute": "ngt.iso_mounted"
        },
        {
            "attribute": "memory_usage_ppm"
        },
        {
            "attribute": "storage_cluster_uuid"
        },
        {
            "attribute": "vga_console_enabled"
        },
        {
            "attribute": "hydration_status"
        },
        {
            "attribute": "hydration_remaining_bytes"
        }
    ],
    "filter_criteria": "vm_name==.*[t|T][i|I][n|N][y|Y].*"
}
batch_count = 0
output_file = "app_vm_mapping.json"
process_vm_count = 0
process_app_count = 0

def append_to_json_file(app_name, vm_name, filename):
    """Append app_name and vm_name to JSON file"""
    try:
        # Read existing data
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        
        # Add or update the app entry
        if app_name not in data:
            data[app_name] = []
        if vm_name not in data[app_name]:
            data[app_name].append(vm_name)
        
        # Write back to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"SUCCESS: Added {app_name} -> {vm_name} to {filename}")
    except Exception as e:
        print(f"ERROR: Failed to write to file: {e}")

for i in range(100,500):
    groups_payload['offset'] += 20*i
    response = client.post(URL + 'groups', data=json.dumps(groups_payload))
    if response.status_code != 200:
        print(response.content, "error in list url")
        continue
    else:
        resp = json.loads(response.content)
        for app in resp['group_results'][0]['entity_results']:
            # Get app name and vm_names
            app_name = app.get('app_name', 'Unknown')
            vm_names = app.get('vm_names', [])
            
            process_app_count += 1
            print(f"\n{'='*80}")
            print(f"Processing App [{process_app_count}]: {app_name}")
            print(f"VMs: {vm_names}")
            print(f"{'='*80}\n")
            if len(vm_names) > 0 and len(vm_names[0]) > 0:
                for vm_name in vm_names:
                    vm_name_filter = convert_to_case_insensitive_pattern(vm_name)
                    vm_list_group_pay['filter_criteria'] = f"vm_name==.*{vm_name_filter}.*"
                    response = client.post(vm_list_group_url, data=json.dumps(vm_list_group_pay))
                    if response.status_code != 200:
                        print(response.content, "error in list url")
                        continue
                    else:
                        resp = json.loads(response.content)
                        retry_count = 0
                        break_flag = False
                        if len(resp['group_results']) == 0:
                            print(f"No VMs found for {vm_name}")
                            continue
                        for vm in resp['group_results'][0]['entity_results']:
                            print(vm['data'][0]['values'][0]['values'][0])
                            vm_name = vm['data'][0]['values'][0]['values'][0]
                            vm_uuid = vm['entity_id']
                            print(f"INFO: Processing VM [{vm_name}]:[{vm_uuid}]")
                            for r in vm['data']:
                                if r['name'] == 'cluster_name':
                                    cluster_name = r['values'][0]['values'][0]
                                elif r['name'] == 'project_name':
                                    project_name = r['values'][0]['values'][0]
                                elif r['name'] == 'project_reference':
                                    project_uuid = r['values'][0]['values'][0]
                                elif r['name'] == 'cluster':
                                    cluster_uuid = r['values'][0]['values'][0]
                            print(f"cluster_name: {cluster_name}, project_name: {project_name}, project_uuid: {project_uuid}, cluster_uuid: {cluster_uuid}")
                            process_vm_count += 1
                            print(f"Processing VM [{process_vm_count}]: {vm_name} (App: {app_name})")
                            update_pay = {
                                    "action_on_failure": "CONTINUE",
                                    "execution_order": "NON_SEQUENTIAL",
                                    "api_request_list": [
                                        {
                                            "operation": "PUT",
                                            "path_and_params": f"/api/nutanix/v3/mh_vms/{vm_uuid}",
                                            "body": {
                                                "spec": {
                                                    "resources": {},
                                                    "cluster_reference": {
                                                        "kind": "cluster",
                                                        "name": cluster_name,
                                                        "uuid": cluster_uuid
                                                    }
                                                },
                                                "api_version": "3.1",
                                                "metadata": {
                                                    "kind": "mh_vm",
                                                    "project_reference": {
                                                        "kind": "project",
                                                        "name": project_name,
                                                        "uuid": project_uuid
                                                    },
                                                    "uuid": vm_uuid,
                                                    "spec_version": 1,
                                                    "categories": {},
                                                    "categories_mapping": {},
                                                    "creation_time": vm['data'][0]['values'][0]['values'][0],
                                                    "last_update_time": vm['data'][0]['values'][0]['values'][0],
                                                    "owner_reference": {
                                                        "kind": "user",
                                                        "name": "admin",
                                                        "uuid": "00000000-0000-0000-0000-000000000000"
                                                    },
                                                    "use_categories_mapping": True
                                                }
                                            }
                                        }
                                    ],
                                    "api_version": "3.0"
                                }
                            while True and retry_count < 3:
                                
                                update_response = client.post(update_url, data=json.dumps(update_pay), verify=False)
                                print(f"DEBUG: Update response status code: {update_response.status_code}")
                                if update_response.status_code != 200:
                                    print(update_response.content, "error in batch url")
                                    break
                                update_response = json.loads(update_response.content)
                                print("update_response",update_response)
                                response_status = update_response['api_response_list'][0]['status']
                                print(f"DEBUG: API response status: {response_status}, type: {type(response_status)}")
                                print()
                                if response_status == '202' or response_status == 202:
                                    # VM update succeeded - append to JSON file
                                    print(f"DEBUG: VM update succeeded! Calling append_to_json_file with app_name={app_name}, vm_name={vm_name}")
                                    append_to_json_file(app_name, vm_name, output_file)
                                    break
                                elif 'api_response' in update_response['api_response_list'][0] and \
                                     'message_list' in update_response['api_response_list'][0]['api_response'] and \
                                     len(update_response['api_response_list'][0]['api_response']['message_list']) > 0 and \
                                     update_response['api_response_list'][0]['api_response']['message_list'][0]['reason'] == 'SPEC_VERSION_MISMATCH':
                                    error_message = update_response['api_response_list'][0]['api_response']['message_list'][0]['message']
                                    print(f"WARN: SPEC_VERSION_MISMATCH detected for [{vm_name}]: {error_message}")
                                    # Extract required spec_version from error message: "required X"
                                    match = re.search(r'required (\d+)', error_message)
                                    if match:
                                        required_spec_version = int(match.group(1))
                                        print(f"INFO: Updating spec_version to required value: {required_spec_version}")
                                        update_pay['api_request_list'][0]['body']['metadata']['spec_version'] = required_spec_version
                                        retry_count += 1
                                        continue
                                    else:
                                        print("ERROR: Could not extract required spec_version from error message")
                                        break_flag = True
                                        break
                                else:
                                    print(f"DEBUG: Unhandled response status or error")
                                    if 'api_response' in update_response['api_response_list'][0]:
                                        print(f"DEBUG: Full api_response: {update_response['api_response_list'][0]['api_response']}")
                                        if 'message_list' in update_response['api_response_list'][0]['api_response'] and \
                                           len(update_response['api_response_list'][0]['api_response']['message_list']) > 0:
                                            print(update_response['api_response_list'][0]['api_response']['message_list'][0]['reason'], "error in batch url")
                                    break_flag = True
                                    break
                            if break_flag:
                                print("break_flag", break_flag)
                                time.sleep(10)
                                break
                            time.sleep(1)
                        if break_flag:
                            print(f"Takin break 10 seconds before processing batch page, current batch count: [{batch_count}]")
                            time.sleep(10)
                            break
                        batch_count += 1

# Print final summary
print(f"\n{'='*80}")
print(f"PROCESSING COMPLETE!")
print(f"{'='*80}")
print(f"Total Apps Processed: {process_app_count}")
print(f"Total VMs Processed: {process_vm_count}")
print(f"App to VM mapping saved to: {output_file}")
print(f"{'='*80}\n")