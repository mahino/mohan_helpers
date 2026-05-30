"""Nucalm environment setup"""

import json
import os
import subprocess
import sys
import time
import uuid

import requests
import urllib3
from requests.auth import HTTPBasicAuth

sys.path.insert(1, '../locustfiles')
# from config_generator import (
#     generate_payload_for_create_quota,
#     generate_payload_for_quota_enable
# )
from helpers import id_generator
# from ndb import NDB
# from pc_helpers import get_advance_networking_controller_status, get_cmsp_enabled_state
# from test_features import TestFeatures
# from vpc import VPC

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# Configuration
# =============================================================================

# Get all IPs from command line arguments (supports up to 100 IPs)
PC_IPS = sys.argv[1:]
if not PC_IPS:
    print("ERROR: No IP addresses provided.")
    print("Usage: python nucalm_env_setup.py <ip1> <ip2> ... <ipN>")
    sys.exit(1)

print(f"Processing {len(PC_IPS)} IP(s): {PC_IPS}")

V3 = 'api/nutanix/v3/'

# Feature flags
ADD_IMAGES = False
ADD_DIRECTORY_SERVICE = True
ENABLE_POLICY = False
ENABLE_NDB = False
ENABLE_VPC = False
ADD_ACCOUNTS = False
ADD_VLANS = False

# =============================================================================
# Process each IP
# =============================================================================

for ip_index, pc_ip in enumerate(PC_IPS, start=1):
    print("\n" + "=" * 60)
    print(f"[{ip_index}/{len(PC_IPS)}] Processing: {pc_ip}")
    print("=" * 60)

    # Setup client for this IP
    BASE_URL = f'https://{pc_ip}:9440/'
    client = requests.Session()
    client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
    client.headers = {'content-type': 'application/json'}
    client.verify = False

    URL = BASE_URL + V3
    CALM_URL = BASE_URL + 'api/calm/v3.0/'

    # print("Waiting for 10 sec")
    # time.sleep(10)

    # =========================================================================
    # NuCalm Status Check
    # =========================================================================

    # nucalm_status = {
    #     "nucalm_lite_status": "DISABLED",
    #     "nucalm_status": "DISABLED"
    # }

    # lite_resp = client.get(URL + 'services/nucalm_lite/status')
    # if lite_resp.status_code == 200:
    #     lite_response = json.loads(lite_resp.content)
    #     nucalm_status['nucalm_lite_status'] = lite_response['service_enablement_status']
    #     if nucalm_status['nucalm_lite_status'] == 'ENABLED':
    #         ss_resp = client.get(URL + 'services/nucalm/status')
    #         if ss_resp.status_code == 200:
    #             ss_response = json.loads(ss_resp.content)
    #             nucalm_status['nucalm_status'] = ss_response['service_enablement_status']
    #         else:
    #             print(f"ERROR: nucalm status API failed: [{ss_resp.content}]")
    # else:
    #     print(f"ERROR: nucalm_lite status API failed: [{lite_resp.content}]")

    # # Enable Nucalm
    # is_marketplace_enabled = (
    #     True if nucalm_status['nucalm_lite_status'] == 'ENABLED'
    #     else json.loads(os.environ['ENABLE_MARKETPLACE']) if 'ENABLE_MARKETPLACE' in os.environ
    #     else True
    # )

    # is_self_service_enabled = (
    #     True if nucalm_status['nucalm_status'] == 'ENABLED'
    #     else json.loads(os.environ['ENABLE_SELF_SERVICE']) if 'ENABLE_SELF_SERVICE' in os.environ
    #     else True
    # )

    # if is_self_service_enabled:
    #     print("Enable calm_appication, it works when isci ip added in PE")
    #     calm_enable_pay = {"enable_nutanix_apps": True, "state": "ENABLE"}
    #     os.system(
    #         "curl -s -u admin:Nutanix.123 -d '{0}' -H \"Content-Type: application/json\" "
    #         "-k POST {1}services/nucalm --cacert trash_files/certificate.crt > /dev/null".format(
    #             json.dumps(calm_enable_pay), URL
    #         )
    #     )

    # =========================================================================
    # Add Images
    # =========================================================================

    if ADD_IMAGES:
        CENTOS_IMAGE = False
        WINDOWS_IMAGE = False
        NDB_IMAGE = False
        TINY_LINUX_IMAGE = False

        for image in ['Centos7HadoopMaster', 'WindowsServer2016', 'PACKAGE_TEST_1', 'TinyCoreLinuxGUI']:
            payload = {"entity_type": "image", "group_member_attributes": [{"attribute": "name"}]}
            resp = client.post(URL + 'groups', data=json.dumps(payload))
            images_data = json.loads(resp.content)
            try:
                images_list = images_data['group_results'][0]['entity_results']
                for img in images_list:
                    if img['data'][0]['values'][0]['values'][0] == image:
                        if image == 'Centos7HadoopMaster':
                            CENTOS_IMAGE = True
                        if image == 'WindowsServer2016':
                            WINDOWS_IMAGE = True
                        if image == 'PACKAGE_TEST_1':
                            NDB_IMAGE = True
                        if image == 'TinyCoreLinuxGUI':
                            TINY_LINUX_IMAGE = True
            except IndexError:
                pass

        # Linux Image
        if not CENTOS_IMAGE:
            print("Adding Linux image")
            linux_image_pay = {
                "action_on_failure": "CONTINUE",
                "execution_order": "NON_SEQUENTIAL",
                "api_request_list": [{
                    "operation": "POST",
                    "path_and_params": "/api/nutanix/v3/images",
                    "body": {
                        "spec": {
                            "name": "Centos7HadoopMaster",
                            "resources": {
                                "image_type": "DISK_IMAGE",
                                "source_uri": "http://endor.dyn.nutanix.com/GoldImages/NuCalm/AHV-UVM-Images/Centos7HadoopMaster.qcow2"
                            }
                        },
                        "metadata": {"kind": "image"},
                        "api_version": "3.1.0"
                    }
                }],
                "api_version": "3.0"
            }
            client.post(URL + 'batch', data=json.dumps(linux_image_pay))
        else:
            print("Centos7HadoopMaster image already exist.")

        # Windows Image
        if not WINDOWS_IMAGE:
            print("Adding Windows image")
            windows_image_pay = {
                "action_on_failure": "CONTINUE",
                "execution_order": "NON_SEQUENTIAL",
                "api_request_list": [{
                    "operation": "POST",
                    "path_and_params": "/api/nutanix/v3/images",
                    "body": {
                        "spec": {
                            "name": "WindowsServer2016",
                            "resources": {
                                "image_type": "DISK_IMAGE",
                                "source_uri": "http://endor.dyn.nutanix.com/GoldImages/NuCalm/AHV-UVM-Images/WindowsServer2016-Base.qcow2"
                            }
                        },
                        "metadata": {"kind": "image"},
                        "api_version": "3.1.0"
                    }
                }],
                "api_version": "3.0"
            }
            client.post(URL + 'batch', data=json.dumps(windows_image_pay))
        else:
            print("WindowsServer2016 image already exist.")

        # NDB Image
        if not NDB_IMAGE:
            print("Adding NDB image")
            ndb_image_pay = {
                "action_on_failure": "CONTINUE",
                "execution_order": "NON_SEQUENTIAL",
                "api_request_list": [{
                    "operation": "POST",
                    "path_and_params": "/api/nutanix/v3/images",
                    "body": {
                        "spec": {
                            "name": "PACKAGE_TEST_1",
                            "resources": {
                                "image_type": "DISK_IMAGE",
                                "source_uri": "http://phx-builds.corp.nutanix.com/cdv-builds/2.5/c3bce35f6a9b14bff0bd47f6cb077dc35e7bcc17/release/NDB-Server-build-2.5-c3bce35f6a9b14bff0bd47f6cb077dc35e7bcc17.qcow2"
                            }
                        },
                        "metadata": {"kind": "image"},
                        "api_version": "3.1.0"
                    }
                }],
                "api_version": "3.0"
            }
            client.post(URL + 'batch', data=json.dumps(ndb_image_pay))
        else:
            print("NDB image already exist.")

        # Tiny Linux Image
        if not TINY_LINUX_IMAGE:
            print("Adding TINY_LINUX_IMAGE image")
            tiny_linux_image_pay = {
                "action_on_failure": "CONTINUE",
                "execution_order": "NON_SEQUENTIAL",
                "api_request_list": [{
                    "operation": "POST",
                    "path_and_params": "/api/nutanix/v3/images",
                    "body": {
                        "spec": {
                            "name": "TinyCoreLinuxGUI",
                            "resources": {
                                "image_type": "DISK_IMAGE",
                                "source_uri": "http://endor.dyn.nutanix.com/GoldImages/LRIO/TinyCoreLinuxGUI.qcow2"
                            }
                        },
                        "metadata": {"kind": "image"},
                        "api_version": "3.1.0"
                    }
                }],
                "api_version": "3.0"
            }
            client.post(URL + 'batch', data=json.dumps(tiny_linux_image_pay))
        else:
            print("TINY_LINUX_IMAGE image already exist.")

        time.sleep(5)

    # =========================================================================
    # Add Directory Service
    # =========================================================================

    if ADD_DIRECTORY_SERVICE:
        # Directory Service
        print("Adding Directory service")
        directory_service_pay = {
            "name": "ST_AUTO_PC_AD",
            "domain": "systest.nutanix.com",
            "directoryUrl": "ldap://10.46.1.152:389",
            "groupSearchType": "RECURSIVE",
            "directoryType": "ACTIVE_DIRECTORY",
            "connectionType": "LDAP",
            "serviceAccountUsername": "Administrator@systest.nutanix.com",
            "serviceAccountPassword": "Nutanix/4u"
        }
        client.post(
            BASE_URL + 'PrismGateway/services/rest/v1/authconfig/directories',
            data=json.dumps(directory_service_pay)
        )

        time.sleep(5)

        # Role Mapping
        print("Role mapping")
        role_mapping_pay = {
            "directoryName": "ST_AUTO_PC_AD",
            "role": "ROLE_CLUSTER_ADMIN",
            "entityType": "USER",
            "entityValues": ["st-sspadmin"]
        }
        client.post(
            BASE_URL + 'PrismGateway/services/rest/v1/authconfig/directories/ST_AUTO_PC_AD/role_mappings?&entityType=USER&role=ROLE_CLUSTER_ADMIN',
            data=json.dumps(role_mapping_pay)
        )

        time.sleep(5)

        # User Role
        print("User role")
        user_role_pay = {
            "profile": {
                "username": "st-sspadmin",
                "firstName": "st-ssp",
                "lastName": "admin",
                "emailId": "st-sspadmin@systest.nutanix.com",
                "password": "nutanix/4u",
                "locale": "en-US"
            },
            "mode": "Create",
            "enabled": False,
            "roles": []
        }
        client.get(
            BASE_URL + 'PrismGateway/services/rest/v1/users',
            data=json.dumps(user_role_pay)
        )

        add_user_role_pay = ["ROLE_USER_ADMIN", "ROLE_MULTICLUSTER_ADMIN"]
        client.put(
            BASE_URL + 'PrismGateway/services/rest/v1/users/st-sspadmin/roles',
            data=json.dumps(add_user_role_pay)
        )

    if ADD_IMAGES:
        print("Waiting 5min for above tasks to complete")
        time.sleep(300)

    # =========================================================================
    # Status Check
    # =========================================================================

    # if is_self_service_enabled:
    #     print('Status check for above steps')
    #     count = 0
    #     pc_ips_check = subprocess.check_output(
    #         'sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@{} '
    #         '"/usr/local/nutanix/cluster/bin/svmips"'.format(pc_ip),
    #         shell=True
    #     ).split()

    #     while count < 120:
    #         for ip in pc_ips_check:
    #             print(ip)
    #             output = subprocess.check_output(
    #                 'sshpass -p "nutanix/4u" ssh -o StrictHostKeyChecking=no nutanix@{} '
    #                 '"docker ps | egrep \'nucalm|epsilon|IMAGE\' "'.format(ip.decode("utf-8")),
    #                 shell=True
    #             ).decode("utf-8")
    #             if output.count("(healthy)") == 2:
    #                 print('calm enabled on :', ip)
    #                 pc_ips_check.remove(ip)
    #         if len(pc_ips_check) == 0:
    #             break
    #         count += 1
    #         time.sleep(30)

    # =========================================================================
    # Policy Enablement
    # =========================================================================

    if ENABLE_POLICY:
        enable_policy = True
        if 'ENABLE_POLICY' in os.environ:
            enable_policy = json.loads(os.environ['ENABLE_POLICY'])
        if is_self_service_enabled and enable_policy:
            policy = TestFeatures(client, BASE_URL)
            policy_resp = policy.feature_policy_get()
            if policy_resp['spec']['feature_status']['is_enabled'] == False:
                print("Enabling policy")
                if not policy_resp:
                    print("ERROR: error in policy apis")
                policy.feature_policy_update(policy_resp, enable_policy=enable_policy)

    # =========================================================================
    # Add Accounts
    # =========================================================================

    if ADD_ACCOUNTS and 'ADD_ACCOUNTS' in os.environ and json.loads(os.environ['ADD_ACCOUNTS']):
        accounts = ['aws', 'azure', 'gcp', 'vmware']
        if 'REMOTE_PC' in os.environ and json.loads(os.environ['REMOTE_PC']):
            rpc_ip_list = os.environ['REMOTE_PC_IP'].split()
            for _ in range(len(rpc_ip_list)):
                accounts.append('nutanix')

        RPC_COUNT = 0
        for account in accounts:
            account_uuid = str(uuid.uuid4())
            spec_file = open('../config/' + account + '_create_account.json')
            data = json.load(spec_file)
            data['metadata']['uuid'] = account_uuid
            if account == 'nutanix':
                data['spec']['name'] = 'RPC_' + str(RPC_COUNT) + str(id_generator(8))
                pc_ip_acc = data['spec']['resources']['data']['server'].replace('pc_ip', rpc_ip_list[RPC_COUNT])
                data['spec']['resources']['data']['server'] = pc_ip_acc
                RPC_COUNT += 1
            print("creating account [{}]".format(account))
            response = client.post(URL + 'accounts', data=json.dumps(data))
            if response.status_code != 200:
                print(response.content)
                continue
            response = json.loads(response.content)
            print("Verifying account [{}]".format(response['spec']['name']))
            response = client.get(URL + 'accounts/' + account_uuid + '/verify', data=json.dumps(data))
            if response.status_code != 200:
                print(response.content)

        # Multi VMware Accounts
        if 'MULTI_VMWARE_ACCOUNTS' in os.environ and json.loads(os.environ['MULTI_VMWARE_ACCOUNTS']):
            payload = {"length": 250, "offset": 0, "filter": "state!=DELETED;type==vmware"}
            response = client.post(URL + 'accounts/list', data=json.dumps(payload))
            if response.status_code != 200:
                print(response.content)
            response = json.loads(response.content)
            vmware_uuid = next(
                (acc['metadata']['uuid'] for acc in response['entities'] if acc['metadata']['name'] == 'vmware_account'),
                ''
            )
            pay = {"filter": "account_uuid==" + vmware_uuid}
            resp = client.post(URL + 'vmware/v6/datacenter/list', data=json.dumps(pay))
            if resp.status_code != 200:
                print(resp.content)
            resp = json.loads(resp.content)
            spec_file = open('../config/vmware_create_account.json')
            data = json.load(spec_file)

            for DC in resp['entities']:
                dc = DC['status']['resources']['name']
                if dc == 'Auto_systest_calm_vcenter-DC':
                    continue
                acc_uuid = str(uuid.uuid4())
                acc_name = 'vmware_account_' + dc.replace('.', '_').replace('-', '_')
                data['metadata']['uuid'] = acc_uuid
                data['spec']['name'] = acc_name[:65]
                data['spec']['resources']['data']['datacenter'] = dc

                for i in range(2):
                    print("creating account [{}]".format(acc_name))
                    response = client.post(URL + 'accounts', data=json.dumps(data))
                    try:
                        if len(json.loads(response.content)['message_list']):
                            print('ERROR: getting error with name ' + acc_name)
                            print(json.loads(response.content)['message_list'])
                            data['spec']['name'] = acc_name[:55] + '_' + id_generator(8)
                            client.delete(URL + 'accounts/' + acc_uuid, data=json.dumps({}))
                            acc_uuid = str(uuid.uuid4())
                            data['metadata']['uuid'] = acc_uuid
                            continue
                    except KeyError:
                        break

                if response.status_code != 200:
                    print(response.content)
                    continue

                response = json.loads(response.content)
                print("Verifying account [{}]".format(response['spec']['name']))
                response = client.get(URL + 'accounts/' + acc_uuid + '/verify', data=json.dumps(data))
                if response.status_code != 200:
                    print(response.content)

        # Enable Quota
        if 'ENABLE_QUOTA' in os.environ:
            # Enable default quota
            quota_pay = {
                "metadata": {"kind": "quota"},
                "spec": {"resources": {"entities": {}, "state": "enabled"}}
            }
            resp = client.put(CALM_URL + 'quotas/update/state', data=json.dumps(quota_pay))
            if resp.status_code != 200:
                print('ERROR: failed to update default quota')
                print(resp.content)
            else:
                create_quota_pay = generate_payload_for_create_quota(self='')
                resp = client.post(CALM_URL + 'quotas', data=json.dumps(create_quota_pay))
                if resp.status_code != 200:
                    print('ERROR: unable to create default quota')
                    print(resp.content)

            # Enable quota at account level
            response = client.post(
                URL + 'accounts/list',
                data=json.dumps({"length": 250, "offset": 0, "filter": "state==VERIFIED;type==nutanix_pc|vmware"})
            )
            if response.status_code != 200:
                print(response.content)
            else:
                for acc in json.loads(response.content)['entities']:
                    print(acc['status']['name'])
                    acc_data = client.get(URL + 'accounts/' + acc['metadata']['uuid'])
                    if acc_data.status_code != 200:
                        print(acc_data.content)
                        continue
                    acc_data = json.loads(acc_data.content)

                    if acc_data['spec']['resources']['type'] == 'vmware':
                        account_data_resp = client.post(
                            URL + 'vmware/v6/cluster/list',
                            data=json.dumps({"filter": "account_uuid==" + acc['metadata']['uuid']})
                        )
                        account_data = json.loads(account_data_resp.content)
                        if account_data_resp.status_code != 200:
                            print(account_data)
                            continue
                        else:
                            try:
                                cluster = account_data['entities'][0]['status']['resources']['name']
                            except IndexError:
                                print("Failed to get cluster details for account [{}]".format(acc['status']['name']))
                                continue
                    elif acc_data['spec']['resources']['type'] == 'nutanix_pc':
                        cluster = (
                            acc_data['status']['resources']['data']
                            ['cluster_account_reference_list'][0]
                            ['resources']['data']['cluster_uuid']
                        )
                    else:
                        continue

                    quota_pay = generate_payload_for_quota_enable(account_uuid=acc['metadata']['uuid'])
                    quota_pay['metadata'] = {'kind': 'quota'}
                    print(json.dumps(quota_pay))
                    resp = client.put(CALM_URL + 'quotas/update/state', data=json.dumps(quota_pay))
                    if resp.status_code != 200:
                        print('ERROR: failed to update quota at cluster level [{}]'.format(acc_data['status']['name']))
                        print(resp.content)
                    else:
                        create_quota_pay = generate_payload_for_create_quota(
                            self='',
                            account_uuid=acc['metadata']['uuid'],
                            cluster=cluster
                        )
                        print(json.dumps(create_quota_pay))
                        resp = client.post(CALM_URL + 'quotas', data=json.dumps(create_quota_pay))
                        if resp.status_code != 200:
                            print('ERROR: unable to create quota for project [{}]'.format(project_name))
                            print(resp.content)

    # =========================================================================
    # Add Images (Wait for completion)
    # =========================================================================

    if ADD_IMAGES:
        count = 0
        images = []
        while count < 120:
            for image in ['Centos7HadoopMaster', 'WindowsServer2016', 'PACKAGE_TEST_1', 'TinyCoreLinuxGUI']:
                payload = {"entity_type": "image", "group_member_attributes": [{"attribute": "name"}]}
                resp = client.post(URL + 'groups', data=json.dumps(payload))
                images_data = json.loads(resp.content)
                try:
                    images_list = images_data['group_results'][0]['entity_results']
                    for img in images_list:
                        if img['data'][0]['values'][0]['values'][0] == image:
                            if image not in images:
                                print(image, 'added')
                                images.append(image)
                            if len(images) == 2:
                                count = 120
                                break
                    else:
                        print(image, 'waiting for update')
                        count += 1
                        time.sleep(30)
                except IndexError:
                    print(image, 'waiting for update')
                    count += 1
                    time.sleep(30)
            else:
                print("All images were added")

    # =========================================================================
    # Add VLANs
    # =========================================================================

    if ADD_VLANS:
        default_vlans = ["vlan.148", "vlan.114"]
        add_vlans = os.environ['ADD_VLANS'].split(',') if 'ADD_VLANS' in os.environ else []
        add_vlans.extend(default_vlans)

        vlan_presence = {}
        for vlan in add_vlans:
            vlan_presence[vlan] = False

        subnet_group_list_payload = {
            "entity_type": "subnet",
            "group_member_attributes": [
                {"attribute": "name"},
                {"attribute": "migration_state"}
            ],
            "group_member_count": 500,
            "group_member_offset": 0
        }

        subnet_create_payload = {
            "spec": {
                "name": "vlan.0",
                "cluster_reference": {
                    "kind": "cluster",
                    "uuid": ""
                },
                "resources": {
                    "subnet_type": "VLAN",
                    "ip_config": {},
                    "vlan_id": 0
                }
            },
            "metadata": {
                "kind": "subnet"
            },
            "api_version": "3.1.0"
        }

        response = client.post(URL + 'groups', data=json.dumps(subnet_group_list_payload))
        if response.status_code == 200:
            for i in json.loads(response.content)['group_results'][0]['entity_results']:
                for j in i['data']:
                    if (j['name'] == 'name') and (j['values'][0]['values'][0] in vlan_presence):
                        vlan_presence[j['values'][0]['values'][0]] = True

        print(vlan_presence)
        for vlan in vlan_presence:
            if not vlan_presence[vlan]:
                print(f"INFO: creating vlan [{vlan}].")
                subnet_create_payload['spec']['name'] = vlan
                subnet_create_payload['spec']['resources']['vlan_id'] = int(vlan.split('.')[1])
                clusters_list_resp = client.post(
                    URL + "clusters/list",
                    data=json.dumps({
                        "length": 250,
                        "offset": 0,
                        "filter": "state==VERIFIED;type!=nutanix"
                    })
                )
                for cluster in json.loads(clusters_list_resp.content)['entities']:
                    if 'nodes' in cluster['status']['resources']:
                        subnet_create_payload['spec']['cluster_reference']['uuid'] = cluster['metadata']['uuid']

                create_sub_resp = client.post(URL + 'subnets', data=json.dumps(subnet_create_payload))
                print(create_sub_resp.content)
            else:
                print(f"INFO: vlan [{vlan}] already exits.")

    # =========================================================================
    # Enable NDB
    # =========================================================================

    if ENABLE_NDB:
        enable_ndb = False
        if 'ENABLE_NDB' in os.environ:
            enable_ndb = json.loads(os.environ['ENABLE_NDB'])

        if enable_ndb:
            ndb_temp = NDB(client)
            bp_data = ndb_temp.create_ndb_bp()

        enable_vpc = False
        if 'ENABLE_VPC' in os.environ:
            enable_vpc = json.loads(os.environ['ENABLE_VPC'])

        if enable_vpc:
            # vpc_temp = VPC(client)
            # bp_data = vpc_temp.create_ndb_bp()
            cmsp_state = get_cmsp_enabled_state(client, api_version='v1')
            anc_state = get_advance_networking_controller_status(client, api_version='v4.0.b2')
            if anc_state != 'UP':
                # https://10.36.199.30:9440/api/networking/v4.0.b2/config/controllers
                # {"defaultVlanStack":"LEGACY","$reserved":{"$fv":"v4.r0.b2"},"$objectType":"networking.v4.config.NetworkController","$unknownFields":{}}
                print("TEMP")
            vpc_temp = VPC(client)
            for i in range(2, 21):
                vpc_create_resp = vpc_temp.create_vpc(i)
                if vpc_create_resp is None:
                    break
                # overlay_network_create_resp =

    print(f"\n✅ Completed processing: {pc_ip}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 60)
print(f"🎉 All {len(PC_IPS)} IP(s) processed successfully!")
print("=" * 60)
