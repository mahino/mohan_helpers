import requests
import json
import random
import sys
import copy
import urllib3
import time
import uuid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

v4_url = "https://10.36.198.255:9440/api/vmm/v4.0/ahv/config/vms"
v3_url = "https://10.36.198.255:9440/api/nutanix/v3/vms"

vlan_name = 'vlan.114'
nic_uuid = "d8125ccf-30c3-4f6f-9b52-57632b31f4a4"
cluster_uuid = "00062bcd-f314-aa9c-0000-00000001c482"
image_uuid = "0b0c58bd-913e-4428-a4b9-61aa1355e84f"
# {"metadata":{"categories_mapping":{},"kind":"vm","use_categories_mapping":True},"spec":{"name":"temp3","resources":{"is_agent_vm":False,"num_sockets":1,"memory_size_mib":66,"num_vcpus_per_socket":1,"hardware_clock_timezone":"UTC","disk_list":[{"device_properties":{"device_type":"DISK","disk_address":{"adapter_type":"SCSI","device_index":0}},"disk_size_bytes":268435456,"data_source_reference":{"kind":"image","uuid":"0b0c58bd-913e-4428-a4b9-61aa1355e84f","name":"TinyCoreLinuxGUI.qcow2"}}],"gpu_list":[],"boot_config":{"boot_type":"LEGACY","boot_device_order_list":["CDROM","DISK","NETWORK"]},"nic_list":[]},"cluster_reference":{"uuid":"00062bcd-f314-aa9c-0000-00000001c482","kind":"cluster"}},"api_version":"3.1.0"}
v4_payload = {"$objectType":"vmm.v4.ahv.config.Vm","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"name":"tem1","description":"","cluster":{"$objectType":"vmm.v4.ahv.config.ClusterReference","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"extId":cluster_uuid},"numSockets":1,"numCoresPerSocket":1,"memorySizeBytes":68719477,"isAgentVm":False,"hardwareClockTimezone":"UTC","isMemoryOvercommitEnabled":False,"apcConfig":{"$objectType":"vmm.v4.ahv.config.ApcConfig","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isApcEnabled":False},"disks":[{"$objectType":"vmm.v4.ahv.config.Disk","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"diskAddress":{"$objectType":"vmm.v4.ahv.config.DiskAddress","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"busType":"SCSI","index":0},"backingInfo":{"$objectType":"vmm.v4.ahv.config.VmDisk","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"dataSource":{"$objectType":"vmm.v4.ahv.config.DataSource","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"reference":{"$objectType":"vmm.v4.ahv.config.ImageReference","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"imageExtId":image_uuid}},"storageConfig":{"$objectType":"vmm.v4.ahv.config.VmDiskStorageConfig","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isFlashModeEnabled":False}}}],"bootConfig":{"$objectType":"vmm.v4.ahv.config.LegacyBoot","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"bootOrder":["CDROM","DISK","NETWORK"]},"vtpmConfig":{"$objectType":"vmm.v4.ahv.config.VtpmConfig","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isVtpmEnabled":False},"nics":[{"$objectType":"vmm.v4.ahv.config.Nic","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"nicNetworkInfo":{"$objectType":"vmm.v4.ahv.config.VirtualEthernetNicNetworkInfo","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"subnet":{"$objectType":"vmm.v4.ahv.config.SubnetReference","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"extId":nic_uuid},"vlanMode":"ACCESS"},"nicBackingInfo":{"$objectType":"vmm.v4.ahv.config.VirtualEthernetNic","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isConnected":True}}]}
v3_payload = {"metadata":{"categories_mapping":{},"kind":"vm","use_categories_mapping":True},"spec":{"name":"main1","resources":{"is_agent_vm":False,"num_sockets":1,"memory_size_mib":66,"num_vcpus_per_socket":1,"hardware_clock_timezone":"UTC","disk_list":[{"device_properties":{"device_type":"DISK","disk_address":{"adapter_type":"SCSI","device_index":0}},"disk_size_bytes":268435456,"data_source_reference":{"kind":"image","uuid":image_uuid,"name":"TinyCoreLinuxGUI.qcow2"}}],"gpu_list":[],"boot_config":{"boot_type":"LEGACY","boot_device_order_list":["CDROM","DISK","NETWORK"]},"nic_list":[{"nic_type":"NORMAL_NIC","is_connected":True,"vlan_mode":"ACCESS","subnet_reference":{"uuid":nic_uuid,"name":vlan_name,"kind":"subnet"},"uuid":"37c6947d-9b71-4351-8434-44d0b7137641"}]},"cluster_reference":{"uuid":cluster_uuid,"kind":"cluster"}},"api_version":"3.1.0"}

headers = {
    'ntnx-request-id': str(uuid.uuid4()),
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
    'Cookie': 'NTNX_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U=; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChlxNHJoaGFjdGF4c3Z2bnZyaTZibHBhNWlhEhliaXpkYTd5ZHVmeGRib3o2bmZzZ3JrZTVk; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U='
}

vm_get_payload = {
    "action_on_failure": "CONTINUE",
    "execution_order": "NON_SEQUENTIAL",
    "api_request_list": [
        {
            "operation": "GET",
            "path_and_params": "/api/nutanix/v3/vms/"
        }
    ],
    "api_version": "3.0"
}


power_on_payload = {"action_on_failure":"CONTINUE","execution_order":"NON_SEQUENTIAL","api_request_list":[{"operation":"PUT","path_and_params":"/api/nutanix/v3/vms/","body":{"metadata":{"kind":"vm","project_reference":{"kind":"project","name":"_internal","uuid":"fc794204-542e-4db3-bcdb-ed6f00a3e10f"},"uuid":"08b9b460-a26a-4382-969e-af096eeb923c","spec_version":1,"categories":{},"categories_mapping":{},"creation_time":"2025-03-24T08:35:45Z","last_update_time":"2025-03-24T08:39:00Z","owner_reference":{"kind":"user","name":"admin","uuid":"00000000-0000-0000-0000-000000000000"},"entity_version":"1"},"api_version":"3.1","spec":{"name":"mainClone-1-100","resources":{"apc_config":{"enabled":False},"num_sockets":1,"num_vcpus_per_socket":1,"num_threads_per_core":1,"memory_size_mib":256,"memory_overcommit_enabled":False,"gpu_console_enabled":False,"is_vcpu_hard_pinned":False,"power_state":"ON","power_state_mechanism":{"mechanism":"HARD","guest_transition_config":{"enable_script_exec":False,"should_fail_on_script_failure":False}},"hardware_clock_timezone":"UTC","is_agent_vm":False,"disable_branding":False,"enable_cpu_passthrough":False,"machine_type":"PC","hardware_virtualization_enabled":False,"vtpm_config":{"vtpm_enabled":False},"disk_list":[{"uuid":"bb968bc3-ac92-4c89-a810-5735bc7dbd2e","device_properties":{"disk_address":{"adapter_type":"SCSI","device_index":0},"device_type":"DISK"},"disk_size_mib":256,"disk_size_bytes":268435456,"storage_config":{"storage_container_reference":{"kind":"storage_container","uuid":"d109dc95-1b70-41f4-9c3b-bfb651e1b9fc","name":"SelfServiceContainer"}}}],"nic_list":[{"uuid":str(uuid.uuid4()),"nic_type":"NORMAL_NIC","vlan_mode":"ACCESS","trunked_vlan_list":[],"num_queues":1,"mac_address":"50:6b:8d:f9:7b:1f","ip_endpoint_list":[],"subnet_reference":{"kind":"subnet","name":"vlan.114","uuid":"75840779-d9c6-4c18-b258-24ba32023108"},"is_connected":True}],"gpu_list":[],"boot_config":{"boot_device_order_list":["CDROM","DISK","NETWORK"],"boot_type":"LEGACY"},"vga_console_enabled":True,"vnuma_config":{"num_vnuma_nodes":0},"serial_port_list":[],"cpu_hotplug_enabled":True,"scsi_controller_enabled":True},"cluster_reference":{"kind":"cluster","name":"bug_verify","uuid":"000630fa-16bc-c32d-0000-00000001c47e"}}}}],"api_version":"3.0"}


vm_group_list = {
    "entity_type": "mh_vm",
    "query_name": "",
    "grouping_attribute": " ",
    "group_count": 1,
    "group_offset": 0,
    "group_attributes": [],
    "group_member_count": 500,
    "group_member_offset": 0,
    "group_member_sort_attribute": "vm_name",
    "group_member_sort_order": "ASCENDING",
    "group_member_attributes": [
        {
            "attribute": "vm_name"
        },
        {
            "attribute": "ip_addresses"
        },
        {
            "attribute": "power_state"
        }
        
    ],
    "filter_criteria": "is_cvm==0"
}

for i in range(1):
    vm_group_list['group_member_offset'] += 500*i
    url = "https://10.36.198.255:9440/api/nutanix/v3/groups"
    res = requests.request("POST", url, headers=headers, data=json.dumps(vm_group_list), verify=False)
    response = json.loads(res.content)
    for i in response['group_results'][0]['entity_results'][::-1]:
        if i['data'][2]['values'][0]['values'][0] == 'off':    
            headers['ntnx-request-id'] = str(uuid.uuid4())
            print(f"INFO: Get vm [{i['data'][0]['values'][0]['values'][0]}]")
            url = "https://10.36.198.255:9440/api/nutanix/v3/batch"
            vm_get_pay = copy.deepcopy(vm_get_payload)
            vm_get_pay['api_request_list'][0]['path_and_params'] += i['entity_id']
            res = requests.request("POST", url, headers=headers, data=json.dumps(vm_get_pay), verify=False)
            # Etag = res.headers['Etag']
            headers['ntnx-request-id'] = str(uuid.uuid4())
            # headers['if-match'] = Etag
            print(f"INFO: Powering on for vm [{i['data'][0]['values'][0]['values'][0]}]")
            url = "https://10.36.198.255:9440/api/nutanix/v3/batch"
            power_on_pay = copy.deepcopy(power_on_payload)
            power_on_pay['api_request_list'][0]['path_and_params'] += i['entity_id']
            power_on_pay['api_request_list'][0]['body']['metadata']['uuid'] = i['entity_id']
            power_on_pay['api_request_list'][0]['body']['spec']['name'] = i['data'][0]['values'][0]['values'][0]
            power_on_pay['api_request_list'][0]['body']['spec']['resources']['disk_list'][0]['uuid'] = str(uuid.uuid4())
            power_on_pay['api_request_list'][0]['body']['spec']['resources']['nic_list'][0]['uuid'] = str(uuid.uuid4())
            mac = [ random.randint(0, 255) for _ in range(6) ]
            mac[0] &= 0xFE  # Ensure the MAC address is universally unique
            mac_address = ':'.join(map(lambda x: f'{x:02x}', mac))

            power_on_pay['api_request_list'][0]['body']['spec']['resources']['nic_list'][0]['mac_address'] = mac_address
            res = requests.request("POST", url, headers=headers, data=json.dumps(power_on_pay), verify=False)
            for _ in range(10):
                headers['ntnx-request-id'] = str(uuid.uuid4())
                url = f"https://10.36.198.255:9440/api/vmm/v4.0/ahv/config/vms/{i['entity_id']}"
                res = requests.request("GET", url, headers=headers, verify=False)
                res = json.loads(res.content)
                print(json.dumps(res))
                if 'nics' in res['data'] and 'ipv4Info' in res['data']['nics'][0]['networkInfo']:
                    print(f"INFO: VM [{res['data']['name']}] got ip [{res['data']['nics'][0]['networkInfo']['ipv4Info']['learnedIpAddresses'][0]['value']}]")
                    break
                print(f"INFO: waiting for powering on for VM [{res['data']['name']}]")
                time.sleep(5)