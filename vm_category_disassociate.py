import requests
import json
import random
import sys
import copy
import urllib3
import time
import uuid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

v4_url = "https://pc_ip:9440/api/vmm/v4.0/ahv/config/vms"
v3_url = "https://pc_ip:9440/api/nutanix/v3/vms"

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

c = 1
vm_group_list = {"entity_type":"mh_vm","query_name":"","grouping_attribute":" ","group_count":20,"group_offset":0,"group_attributes":[],"group_member_count":500,"group_member_offset":0,"group_member_sort_attribute":"cluster_name","group_member_sort_order":"DESCENDING","group_member_attributes":[{"attribute":"vm_name"},{"attribute":"num_vcpus"},{"attribute":"memory_size_bytes"},{"attribute":"ip_addresses"},{"attribute":"cluster_name"},{"attribute":"hypervisor_type"},{"attribute":"guest_os_name"},{"attribute":"ngt.installed_version"},{"attribute":"project_name"},{"attribute":"owner_username"},{"attribute":"project_reference"},{"attribute":"owner_reference"},{"attribute":"categories"},{"attribute":"cluster"},{"attribute":"state"},{"attribute":"message"},{"attribute":"reason"},{"attribute":"is_cvm"},{"attribute":"is_acropolis_vm"},{"attribute":"is_live_migratable"},{"attribute":"gpus_in_use"},{"attribute":"network_security_rule_id_list"},{"attribute":"zone_type"},{"attribute":"vm_annotation"},{"attribute":"vm_type"},{"attribute":"capacity.policy_anomaly_detail"},{"attribute":"capacity.policy_efficiency_detail"},{"attribute":"power_state"},{"attribute":"protection_type"},{"attribute":"memory_overcommit"},{"attribute":"ngt.guest_os"},{"attribute":"ngt.enabled_applications"},{"attribute":"ngt.cluster_version"},{"attribute":"node_name"},{"attribute":"node"},{"attribute":"is_agent_vm"},{"attribute":"volume_group"},{"attribute":"protection_policy_state"},{"attribute":"cbr_not_capable_reason"},{"attribute":"ngt.communication_active"},{"attribute":"ngt.communication_over_serial_port_active"},{"attribute":"vpc_name"}],"filter_criteria":"is_cvm==0"}
for i in range(10):
    vm_group_list['group_member_offset'] += 500
    url = "https://pc_ip:9440/api/nutanix/v3/groups"
    res = requests.request("POST", url, headers=headers, data=json.dumps(vm_group_list), verify=False)
    response = json.loads(res.content)
    for i in response['group_results'][0]['entity_results']:
        headers['ntnx-request-id'] = str(uuid.uuid4())
        print(f"INFO: Get vm [{i['data'][0]['values'][0]['values'][0]}], [{c}]")
        url = f"https://pc_ip:9440/api/vmm/v4.0/ahv/config/vms/{i['entity_id']}"
        res = requests.request("GET", url, headers=headers, verify=False)
        Etag = res.headers['Etag']
        headers['ntnx-request-id'] = str(uuid.uuid4())
        headers['if-match'] = Etag
        res = json.loads(res.content)
        print('categories' not in res['data'])
        if 'categories' not in res['data']:
            continue
        cate_count = 1
        print("before", res['data']['categories'])
        for cat_id in res['data']['categories'][::-1]:
            print(f"INFO: De-associating category [{cat_id['extId']}]for vm [{i['data'][0]['values'][0]['values'][0]}], [{cate_count}]")
            
            url = f"https://pc_ip:9440/api/vmm/v4.0/ahv/config/vms/{i['entity_id']}/$actions/disassociate-categories"
            pp = {
                "categories": [
                    {
                        "extId": cat_id['extId']
                    }
                ]
            }
            res = requests.request("POST", url, headers=headers, data=json.dumps(pp), verify=False)
            for _ in range(10):
                headers['ntnx-request-id'] = str(uuid.uuid4())
                url = f"https://pc_ip:9440/api/vmm/v4.0/ahv/config/vms/{i['entity_id']}"
                res = requests.request("GET", url, headers=headers, verify=False)
                Etag = res.headers['Etag']
                headers['ntnx-request-id'] = str(uuid.uuid4())
                headers['if-match'] = Etag
                res = json.loads(res.content)
                if 'categories' not in res['data']:
                    break
                print("after", res['data']['categories'])
                for cate_id in res['data']['categories']:
                    print( cat_id['extId'], cate_id['extId'], cat_id['extId'] == cate_id['extId'])
                    if cat_id['extId'] == cate_id['extId']:
                        print(f"INFO: waiting for associates updates for VM [{res['data']['name']}], [{c}] - [{cate_count}]") 
                        time.sleep(1)
                else:
                    break
            print(f"INFO: waiting for 1 sec for next de-associates for VM [{res['data']['name']}], [{c}] - [{cate_count}]") 
            cate_count =+ 1
        print(f"INFO: VM [{res['data']['name']}] all category de-associations is done., [{c}]")
        c+=1
        time.sleep(1)