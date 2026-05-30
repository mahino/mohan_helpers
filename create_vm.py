import requests
import json
import random
import sys
import copy
import urllib3
import time
import uuid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

v4_url = "https://10.36.199.49:9440/api/vmm/v4.0/ahv/config/vms"
v3_url = "https://10.36.199.49:9440/api/nutanix/v3/vms"

vlan_name = 'vlan.114'
nic_uuid = "d8125ccf-30c3-4f6f-9b52-57632b31f4a4"
cluster_uuid = "00062bcd-f314-aa9c-0000-00000001c482"
image_uuid = "0b0c58bd-913e-4428-a4b9-61aa1355e84f"
# {"metadata":{"categories_mapping":{},"kind":"vm","use_categories_mapping":true},"spec":{"name":"temp3","resources":{"is_agent_vm":false,"num_sockets":1,"memory_size_mib":66,"num_vcpus_per_socket":1,"hardware_clock_timezone":"UTC","disk_list":[{"device_properties":{"device_type":"DISK","disk_address":{"adapter_type":"SCSI","device_index":0}},"disk_size_bytes":268435456,"data_source_reference":{"kind":"image","uuid":"0b0c58bd-913e-4428-a4b9-61aa1355e84f","name":"TinyCoreLinuxGUI.qcow2"}}],"gpu_list":[],"boot_config":{"boot_type":"LEGACY","boot_device_order_list":["CDROM","DISK","NETWORK"]},"nic_list":[]},"cluster_reference":{"uuid":"00062bcd-f314-aa9c-0000-00000001c482","kind":"cluster"}},"api_version":"3.1.0"}
v4_payload = {"$objectType":"vmm.v4.ahv.config.Vm","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"name":"tem1","description":"","cluster":{"$objectType":"vmm.v4.ahv.config.ClusterReference","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"extId":cluster_uuid},"numSockets":1,"numCoresPerSocket":1,"memorySizeBytes":68719477,"isAgentVm":False,"hardwareClockTimezone":"UTC","isMemoryOvercommitEnabled":False,"apcConfig":{"$objectType":"vmm.v4.ahv.config.ApcConfig","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isApcEnabled":False},"disks":[{"$objectType":"vmm.v4.ahv.config.Disk","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"diskAddress":{"$objectType":"vmm.v4.ahv.config.DiskAddress","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"busType":"SCSI","index":0},"backingInfo":{"$objectType":"vmm.v4.ahv.config.VmDisk","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"dataSource":{"$objectType":"vmm.v4.ahv.config.DataSource","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"reference":{"$objectType":"vmm.v4.ahv.config.ImageReference","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"imageExtId":image_uuid}},"storageConfig":{"$objectType":"vmm.v4.ahv.config.VmDiskStorageConfig","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isFlashModeEnabled":False}}}],"bootConfig":{"$objectType":"vmm.v4.ahv.config.LegacyBoot","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"bootOrder":["CDROM","DISK","NETWORK"]},"vtpmConfig":{"$objectType":"vmm.v4.ahv.config.VtpmConfig","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isVtpmEnabled":False},"nics":[{"$objectType":"vmm.v4.ahv.config.Nic","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"nicNetworkInfo":{"$objectType":"vmm.v4.ahv.config.VirtualEthernetNicNetworkInfo","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"subnet":{"$objectType":"vmm.v4.ahv.config.SubnetReference","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"extId":nic_uuid},"vlanMode":"ACCESS"},"nicBackingInfo":{"$objectType":"vmm.v4.ahv.config.VirtualEthernetNic","$reserved":{"$fv":"v4.r0"},"$unknownFields":{},"isConnected":True}}]}
v3_payload = {"metadata":{"categories_mapping":{},"kind":"vm","use_categories_mapping":True},"spec":{"name":"main1","resources":{"is_agent_vm":False,"num_sockets":1,"memory_size_mib":66,"num_vcpus_per_socket":1,"hardware_clock_timezone":"UTC","disk_list":[{"device_properties":{"device_type":"DISK","disk_address":{"adapter_type":"SCSI","device_index":0}},"disk_size_bytes":268435456,"data_source_reference":{"kind":"image","uuid":image_uuid,"name":"TinyCoreLinuxGUI.qcow2"}}],"gpu_list":[],"boot_config":{"boot_type":"LEGACY","boot_device_order_list":["CDROM","DISK","NETWORK"]},"nic_list":[{"nic_type":"NORMAL_NIC","is_connected":True,"vlan_mode":"ACCESS","subnet_reference":{"uuid":nic_uuid,"name":vlan_name,"kind":"subnet"},"uuid":"37c6947d-9b71-4351-8434-44d0b7137641"}]},"cluster_reference":{"uuid":cluster_uuid,"kind":"cluster"}},"api_version":"3.1.0"}

headers = {
    'ntnx-request-id': str(uuid.uuid4()),
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
    'Cookie': 'NTNX_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U=; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChlxNHJoaGFjdGF4c3Z2bnZyaTZibHBhNWlhEhliaXpkYTd5ZHVmeGRib3o2bmZzZ3JrZTVk; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U='
}

# v4
# for i in range(0,750):
#   v4_payload['name'] = f"newly_{i}"
#   print(f"INFO: Creating VM [{v4_payload['name']}]")
#   headers['ntnx-request-id'] = str(uuid.uuid4())
#   response = requests.request("POST", v4_url, headers=headers, data=json.dumps(v4_payload), verify=False)
#   response = json.loads(response.content)
#   print(response)
#   time.sleep(2)
  
# # v3
# for i in range(0,500):
#   v3_payload['spec']['name'] = f"newly_{i}"
#   v3_payload['spec']['resources']['nic_list'][0]['uuid'] = str(uuid.uuid4())
#   print(f"INFO: Creating VM [{v3_payload['spec']['name']}]")
#   headers['ntnx-request-id'] = str(uuid.uuid4())
#   response = requests.request("POST", v3_url, headers=headers, data=json.dumps(v3_payload), verify=False)
#   response = json.loads(response.content)
#   print(response)
#   time.sleep(2)


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
for i in range(10):
    vm_group_list['group_member_offset'] += 500*i
    url = "https://10.36.199.49:9440/api/nutanix/v3/groups"
    res = requests.request("POST", url, headers=headers, data=json.dumps(vm_group_list), verify=False)
    response = json.loads(res.content)
    for i in response['group_results'][0]['entity_results']:
        if i['data'][2]['values'][0]['values'][0] == 'off':    
            headers['ntnx-request-id'] = str(uuid.uuid4())
            print(f"INFO: Get vm [{i['data'][0]['values'][0]['values'][0]}]")
            url = f"https://10.36.199.49:9440/api/vmm/v4.0/ahv/config/vms/{i['entity_id']}"
            res = requests.request("GET", url, headers=headers, verify=False)
            Etag = res.headers['Etag']
            headers['ntnx-request-id'] = str(uuid.uuid4())
            headers['if-match'] = Etag
            print(f"INFO: Powering on for vm [{i['data'][0]['values'][0]['values'][0]}]")
            url = f"https://10.36.199.49:9440/api/vmm/v4.0/ahv/config/vms/{i['entity_id']}/$actions/power-on"
            res = requests.request("POST", url, headers=headers, verify=False)
            for _ in range(10):
                headers['ntnx-request-id'] = str(uuid.uuid4())
                url = f"https://10.36.199.49:9440/api/vmm/v4.0/ahv/config/vms/{i['entity_id']}"
                res = requests.request("GET", url, headers=headers, verify=False)
                res = json.loads(res.content)
                if 'ipv4Info' in res['data']['nics'][0]['nicNetworkInfo']:
                    print(f"INFO: VM [{res['data']['name']}] got ip [{res['data']['nics'][0]['nicNetworkInfo']['ipv4Info']['learnedIpAddresses'][0]['value']}]")
                    break
                print(f"INFO: waiting for powering on for VM [{res['data']['name']}]")
                time.sleep(5)