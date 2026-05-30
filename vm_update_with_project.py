""" Nucalm environment setup"""


import os
import sys
import json
import copy
import uuid
import time
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = f"https://{sys.argv[1]}:9440/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

#params
project_uuid = "f975617d-67e6-4047-902b-6e327d9708c7"
user_name = "admin@systest.nutanix.com"
user_uuid = "d84897db-4f63-562b-8699-5fa3622bd672"
cluster_name =  "Interops_HOSTPE"
cluster_uuid = "000632e3-a432-f211-6bee-7cc255814617"


V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3
update_payload = {
    "action_on_failure": "CONTINUE",
    "execution_order": "NON_SEQUENTIAL",
    "api_request_list": [
        {
            "operation": "PUT",
            "path_and_params": "/api/nutanix/v3/vms/",
            "body": {
                "api_version": "3.1",
                "metadata": {
                    "kind": "vm",
                    "project_reference": {
                        "kind": "project",
                        "uuid": project_uuid
                    },
                    "uuid": "",
                    "spec_version": 1,
                    "categories": {},
                    "categories_mapping": {},
                    "creation_time": "2025-04-24T15:43:23Z",
                    "last_update_time": "2025-04-24T15:43:23Z",
                    "owner_reference": {
                        "kind": "user",
                        "name": user_name,
                        "uuid": user_uuid
                    },
                    "entity_version": "2"
                },
                "spec": {
                    "name": "",
                    "resources": {
                        "apc_config": {
                            "enabled": False
                        },
                        "num_sockets": 1,
                        "num_vcpus_per_socket": 1,
                        "num_threads_per_core": 1,
                        "memory_size_mib": 4096,
                        "memory_overcommit_enabled": False,
                        "gpu_console_enabled": False,
                        "is_vcpu_hard_pinned": False,
                        "power_state": "ON",
                        "power_state_mechanism": {
                            "mechanism": "HARD",
                            "guest_transition_config": {
                                "enable_script_exec": False,
                                "should_fail_on_script_failure": False
                            }
                        },
                        "hardware_clock_timezone": "UTC",
                        "is_agent_vm": False,
                        "disable_branding": False,
                        "enable_cpu_passthrough": False,
                        "machine_type": "PC",
                        "hardware_virtualization_enabled": False,
                        "vtpm_config": {
                            "vtpm_enabled": False
                        },
                        "disk_list": [
                            {
                                "uuid": "",
                                "device_properties": {
                                    "disk_address": {
                                        "adapter_type": "SCSI",
                                        "device_index": 0
                                    },
                                    "device_type": "DISK"
                                },
                                "disk_size_mib": 256,
                                "disk_size_bytes": 268435456,
                                "data_source_reference": {
                                    "kind": "image",
                                    "uuid": ""
                                },
                                "storage_config": {
                                    "storage_container_reference": {
                                        "kind": "storage_container",
                                        "uuid": "",
                                        "name": "SelfServiceContainer"
                                    }
                                }
                            }
                        ],
                        "nic_list": [
                            {
                                "uuid": "",
                                "nic_type": "NORMAL_NIC",
                                "vlan_mode": "ACCESS",
                                "trunked_vlan_list": [],
                                "num_queues": 1,
                                "mac_address": "50:6b:8d:a8:7a:d8",
                                "ip_endpoint_list": [],
                                "subnet_reference": {
                                    "kind": "subnet",
                                    "name": "vlan.141_Real_VMs",
                                    "uuid": ""
                                },
                                "is_connected": True
                            }
                        ],
                        "gpu_list": [],
                        "boot_config": {
                            "boot_device_order_list": [
                                "CDROM",
                                "DISK",
                                "NETWORK"
                            ],
                            "boot_type": "LEGACY"
                        },
                        "vga_console_enabled": True,
                        "vnuma_config": {
                            "num_vnuma_nodes": 0
                        },
                        "serial_port_list": [],
                        "cpu_hotplug_enabled": True,
                        "scsi_controller_enabled": True
                    },
                    "cluster_reference": {
                        "kind": "cluster",
                        "name": cluster_name,
                        "uuid": cluster_uuid
                    }
                }
            }
        }
    ],
    "api_version": "3.0"
}

# https://pc-10-122-30-167.nutanixqa.com:9440/api/nutanix/v3/groups
groups_payload = {"entity_type":"mh_vm","query_name":"","grouping_attribute":" ","group_count":20,"group_offset":0,"group_attributes":[],"group_member_count":20,"group_member_offset":0,"group_member_sort_attribute":"project_name","group_member_sort_order":"ASCENDING","group_member_attributes":[{"attribute":"vm_name"},{"attribute":"num_vcpus"},{"attribute":"memory_size_bytes"},{"attribute":"ip_addresses"},{"attribute":"cluster_name"},{"attribute":"hypervisor_type"},{"attribute":"guest_os_name"},{"attribute":"ngt.installed_version"},{"attribute":"project_name"},{"attribute":"owner_username"},{"attribute":"project_reference"},{"attribute":"owner_reference"},{"attribute":"categories"},{"attribute":"cluster"},{"attribute":"state"},{"attribute":"message"},{"attribute":"reason"},{"attribute":"is_cvm"},{"attribute":"is_acropolis_vm"},{"attribute":"is_live_migratable"},{"attribute":"gpus_in_use"},{"attribute":"network_security_rule_id_list"},{"attribute":"zone_type"},{"attribute":"vm_annotation"},{"attribute":"vm_type"},{"attribute":"capacity.policy_anomaly_detail"},{"attribute":"capacity.policy_efficiency_detail"},{"attribute":"power_state"},{"attribute":"protection_type"},{"attribute":"memory_overcommit"},{"attribute":"ngt.guest_os"},{"attribute":"ngt.enabled_applications"},{"attribute":"ngt.cluster_version"},{"attribute":"node_name"},{"attribute":"node"},{"attribute":"is_agent_vm"},{"attribute":"volume_group"},{"attribute":"protection_policy_state"},{"attribute":"cbr_not_capable_reason"},{"attribute":"ngt.communication_active"},{"attribute":"ngt.communication_over_serial_port_active"},{"attribute":"vpc_name"}],"filter_criteria":"vm_name==.*[b|B][r|R][o|O][w|W][n|N][f|F][i|I][e|E][l|L][d|D]_[v|V][m|M].*;is_cvm==0"}

count = 1
for i in range(1,12):
  resp = client.post(URL + 'groups', data=json.dumps(groups_payload))
  if resp.status_code != 200:
    print(resp.content, "error in groups list url")
  resp = json.loads(resp.content)
  if len(resp['group_results'][0]['entity_results']) == 0: break
  for vm in resp['group_results'][0]['entity_results']: 
    print(vm['entity_id'], count)
    count += 1
    # url = "https://pc-10-122-30-167.nutanixqa.com:9440/api/vmm/v4.0/ahv/config/vms/ff3bf230-62bd-41de-a54b-a6d6b2c9bcca"
    get_resp = client.get(BASE_URL + f"api/vmm/v4.0/ahv/config/vms/{vm['entity_id']}")
    get_resp = json.loads(get_resp.content)
    update_payload_copy = copy.deepcopy(update_payload)
    update_payload_copy['api_request_list'][0]['path_and_params'] += vm['entity_id']
    update_payload_copy['api_request_list'][0]['body']['metadata']['uuid'] = vm['entity_id']
    update_payload_copy['api_request_list'][0]['body']['spec']['name'] = get_resp['data']['name']
    update_payload_copy['api_request_list'][0]['body']['spec']['resources']['disk_list'][0]['uuid'] = get_resp['data']['disks'][0]['backingInfo']['diskExtId']
    update_payload_copy['api_request_list'][0]['body']['spec']['resources']['disk_list'][0]['data_source_reference']['uuid'] = get_resp['data']['disks'][0]['backingInfo']['dataSource']['reference']['imageExtId']
    update_payload_copy['api_request_list'][0]['body']['spec']['resources']['disk_list'][0]['storage_config']['storage_container_reference']['uuid'] = get_resp['data']['disks'][0]['backingInfo']['storageContainer']['extId']
    update_payload_copy['api_request_list'][0]['body']['spec']['resources']['nic_list'][0]['uuid'] = get_resp['data']['nics'][0]['extId']
    update_payload_copy['api_request_list'][0]['body']['spec']['resources']['nic_list'][0]['subnet_reference']['uuid'] = get_resp['data']['nics'][0]['networkInfo']['subnet']['extId']
    print(f"INFO: Updating VM [{get_resp['data']['name']}]")
    put_resp = client.post(URL + 'batch', data=json.dumps(update_payload_copy))
    if put_resp.status_code != 200:
      print(put_resp.content, "error in batch url")
    print(f"INFO: Update VM [{get_resp['data']['name']}] success")
    time.sleep(1)
  groups_payload['group_member_offset'] += 20
    
# https://pc-10-122-30-167.nutanixqa.com:9440/api/nutanix/v3/batch