""" Nucalm environment setup"""


import os
import sys
import json
import uuid
import time
import requests
import urllib3
import random
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://ncm.services.nconprem-10-114-55-128.ccpnx.com/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

policy_pay = {
    "api_version": "3.0",
    "metadata": {
        "kind": "app_protection_policy",
        "project_reference": {
            "kind": "project",
            "name": "Nucalm_10_16_55_j21m",
            "uuid": "9427fa64-da04-439a-905e-debbd73bb32c"
        },
        "uuid": "5078e337-d3ff-8860-cc18-5861a59fd846"
    },
    "spec": {
        "name": "fdcaedw",
        "description": "",
        "resources": {
            "is_default": False,
            "ordered_availability_site_list": [
                {
                    "environment_reference": {
                        "kind": "environment",
                        "uuid": "b24a40dd-0ed0-2158-1799-832dfc101e4e"
                    },
                    "infra_inclusion_list": {
                        "type": "nutanix_pc",
                        "account_reference": {
                            "kind": "account",
                            "uuid": "5268e859-8177-41cc-b5cd-ceac001a1ddd"
                        },
                        "cluster_references": [
                            {
                                "kind": "cluster",
                                "uuid": "00065031-3c14-1b72-7e15-7cc2558641c8"
                            }
                        ]
                    }
                },
                {
                    "environment_reference": {
                        "kind": "environment",
                        "uuid": "b24a40dd-0ed0-2158-1799-832dfc101e4e"
                    },
                    "infra_inclusion_list": {
                        "type": "nutanix_pc",
                        "account_reference": {
                            "kind": "account",
                            "uuid": "5268e859-8177-41cc-b5cd-ceac001a1ddd"
                        },
                        "cluster_references": [
                            {
                                "kind": "cluster",
                                "uuid": "00065035-b0c9-5144-07ad-7cc255864212"
                            }
                        ]
                    }
                },
                {
                    "environment_reference": {
                        "kind": "environment",
                        "uuid": "b24a40dd-0ed0-2158-1799-832dfc101e4e"
                    },
                    "infra_inclusion_list": {
                        "type": "nutanix_pc",
                        "account_reference": {
                            "kind": "account",
                            "uuid": "5268e859-8177-41cc-b5cd-ceac001a1ddd"
                        },
                        "cluster_references": [
                            {
                                "kind": "cluster",
                                "uuid": "00065035-daa1-70e4-7faf-ac1f6b61e0cf"
                            }
                        ]
                    }
                },
                {
                    "environment_reference": {
                        "kind": "environment",
                        "uuid": "b24a40dd-0ed0-2158-1799-832dfc101e4e"
                    },
                    "infra_inclusion_list": {
                        "type": "nutanix_pc",
                        "account_reference": {
                            "kind": "account",
                            "uuid": "5268e859-8177-41cc-b5cd-ceac001a1ddd"
                        },
                        "cluster_references": [
                            {
                                "kind": "cluster",
                                "uuid": "0006525e-4987-690e-6ada-7cc25530e93d"
                            }
                        ]
                    }
                }
            ],
            "app_protection_rule_list": [
                {
                    "name": "rule_cc0576853272d45180262d53c5a45eec",
                    "enabled": True,
                    "local_snapshot_retention_policy": {
                        "snapshot_expiry_policy": {
                            "multiple": 10
                        }
                    },
                    "first_availability_site_index": 0,
                    "second_availability_site_index": 0,
                    "recovery_point_objective_secs": -1,
                    "uuid": "cc057685-3272-d451-8026-2d53c5a45eec"
                },
                {
                    "name": "rule_16f5fb6bac0b106895324bd4cae9bed4",
                    "enabled": True,
                    "local_snapshot_retention_policy": {
                        "snapshot_expiry_policy": {
                            "multiple": 10
                        }
                    },
                    "first_availability_site_index": 1,
                    "second_availability_site_index": 1,
                    "recovery_point_objective_secs": -1,
                    "uuid": "16f5fb6b-ac0b-1068-9532-4bd4cae9bed4"
                },
                {
                    "name": "rule_bffe70aef64d69721c89f60a70957673",
                    "enabled": True,
                    "local_snapshot_retention_policy": {
                        "snapshot_expiry_policy": {
                            "multiple": 10
                        }
                    },
                    "first_availability_site_index": 2,
                    "second_availability_site_index": 2,
                    "recovery_point_objective_secs": -1,
                    "uuid": "bffe70ae-f64d-6972-1c89-f60a70957673"
                },
                {
                    "name": "rule_62b64e5fb998df97f34f18b6183799dd",
                    "enabled": True,
                    "local_snapshot_retention_policy": {
                        "snapshot_expiry_policy": {
                            "multiple": 10
                        }
                    },
                    "first_availability_site_index": 3,
                    "second_availability_site_index": 3,
                    "recovery_point_objective_secs": -1,
                    "uuid": "62b64e5f-b998-df97-f34f-18b6183799dd"
                }
            ]
        }
    }
}

projects_list = [["Nucalm_10_37_18_csx4", "e8839a7b-d1da-46d4-986f-7b384a482518"], ["Nucalm_10_36_50_vb29", "a4b98c7f-3af5-4971-be50-aff44492d1c2"], ["Nucalm_10_36_28_nv7b", "37e92fc8-9619-4313-bc0d-439e323c518b"], ["Nucalm_10_35_56_pfjh", "77ef9ab1-319a-48b1-86d1-c1a2f40bded2"], ["Nucalm_10_35_53_9zj8", "54f9bf76-4f3d-4cb4-a5a1-f9dfcb2a3577"], ["Nucalm_10_35_36_87vv", "5d259589-ee6f-43c5-873b-2e250895bb0b"], ["Nucalm_10_35_09_3tau", "469179a5-2ec4-44a0-aea8-91c8239a431a"], ["Nucalm_10_35_04_xjxy", "b90eab0c-1a3e-4f6c-a1a1-9c7300d6e58f"], ["Nucalm_10_34_05_ln0k", "dcdccd08-1141-4948-832c-d8d347fcd820"], ["Nucalm_10_34_03_izzi", "10a95458-cd15-46b8-b6cb-4eb8325371f9"], ["Nucalm_10_33_47_8s41", "89d3d3b5-cce2-4d8b-a264-a4e6309fac02"], ["Nucalm_10_33_27_o9ug", "8f605aa7-7902-4eb4-bf41-0b7cee357c2d"], ["Nucalm_10_33_19_tb0u", "2bfb3a77-3f06-4bd6-9edf-f40d3c592731"], ["Nucalm_10_32_33_pqpe", "6f5ab514-1656-4f1b-b6f0-9c50f1db3b5c"], ["Nucalm_10_32_23_5nga", "b5ff288b-2f7b-4068-9c06-e0605b4a05b7"], ["Nucalm_10_32_04_ii07", "f1463042-c6b9-42be-8819-5db2e17f73ad"], ["Nucalm_10_31_47_vvat", "854ae26c-afa3-4558-b3b2-57b7bb01175c"], ["Nucalm_10_31_46_mkhc", "843dabf3-451d-48a1-81ae-71a67ef570ea"], ["Nucalm_10_30_48_fmrf", "6516765f-12b5-47a0-ba29-2afebd660730"], ["Nucalm_10_30_47_xvdc", "fc59643e-b27e-45ae-9b83-20137e9cf6dc"], ["Nucalm_10_30_32_35g9", "047ac10a-1f19-459c-b10d-b5070ecb3abe"], ["Nucalm_10_30_10_yt74", "4ecc1b70-634a-4f2e-9fcf-c003a3d692e2"], ["Nucalm_10_30_08_d3ik", "119c5f4d-0fcc-4cdb-ab81-ca0da88f3ef8"], ["Nucalm_10_29_01_t8jl", "d7f34913-fbd4-43cd-af7f-73264c5360c7"], ["Nucalm_10_28_59_dknb", "de76d348-53a2-4551-bb54-54e6025e8b2e"], ["Nucalm_10_28_49_mqb0", "18cf00cd-ae27-4153-a468-86845c53140e"], ["Nucalm_10_28_39_kb6g", "bf1a521e-bc3b-41f6-92bb-2f6848c112f9"], ["Nucalm_10_28_32_5vmv", "fff00c6a-5dcb-4305-bae5-8388281f09ad"], ["Nucalm_10_27_26_ge48", "5c7b9f7a-5214-4fbc-ab86-dbcf152ff364"], ["Nucalm_10_27_20_dal1", "0072d59f-fe0a-40c5-896f-e6d105849d98"], ["Nucalm_10_27_07_tzpd", "03dd6df5-a830-4930-8300-08e4b12f0a43"], ["Nucalm_10_26_52_2f8k", "4aec72e2-a983-48d9-890a-039bfcf26c52"], ["Nucalm_10_26_42_7rmj", "7497a370-80ac-4fe7-9f2a-e33909d3e5e6"], ["Nucalm_10_25_55_pgy3", "efbac12c-6f39-4775-97a3-24a64a0e8285"], ["Nucalm_10_25_53_h4ly", "7b7b743d-ea51-400a-8328-1c19574fb19c"], ["Nucalm_10_25_40_skq0", "086c6f0c-bcca-445e-b2df-bf7f7e6b5753"], ["Nucalm_10_25_27_c641", "62e27622-e729-44fc-b7bd-948adc9df717"], ["Nucalm_10_25_16_twc4", "5ebdc915-7a97-4f4a-8f5a-34ea80332aef"], ["Nucalm_10_24_25_df1t", "acf9e7a6-86c6-466c-92f9-39e95842258b"], ["Nucalm_10_24_25_gxss", "b6224353-4391-4772-be99-f8d2b61d4914"], ["Nucalm_10_24_16_xywy", "117e6a7f-2e73-48f4-a772-72ff33a2cbd5"], ["Nucalm_10_23_57_34lw", "cd7e1913-cd2d-4b20-92dc-f2ca687837e9"], ["Nucalm_10_23_54_9ioo", "b15623f4-cc8d-4d15-855e-1f25c2bb4ab7"], ["Nucalm_10_22_29_hseb", "52441dd5-15d3-4a6d-ac90-1fa3b16a5e68"], ["Nucalm_10_22_29_7sza", "9eeacb50-a83e-4981-8212-67c12208c61f"], ["Nucalm_10_22_28_43wl", "68117cdd-fad9-4d84-8811-c5a8cc80e769"], ["Nucalm_10_22_28_tmrh", "61a32683-d6d6-468e-aa83-3fb4359b3cda"], ["Nucalm_10_22_27_b2xq", "986ec924-0d96-4de8-a384-349f12ed9360"], ["Nucalm_10_16_55_j21m", "9427fa64-da04-439a-905e-debbd73bb32c"], ["TestP1", "5e8af0a9-be7c-448e-aaaa-04384f5bd7bc"]]

for count, pro in enumerate(projects_list):
    print(f"Processing project: [{pro[0]}] count: [{count}]")
    policy_pay['metadata']['project_reference']['name'] = pro[0]
    policy_pay['metadata']['project_reference']['uuid'] = pro[1]
    resp = client.get('https://dm.services.nconprem-10-114-55-128.ccpnx.com/api/nutanix/v3/projects_internal/' + pro[1])
    if resp.status_code != 200:
        print(resp.status_code)
        continue
    response = json.loads(resp.content)
    for i in response['spec']['project_detail']['resources']['environment_reference_list']:
        print(f"************************************************")
        print(f"Creating Request for GET https://ncm.services.nconprem-10-114-55-128.ccpnx.com/api/nutanix/v3/environments/{i['uuid']}")
        print(f"  Project: {pro[0]} ({pro[1]})")
        print(f"************************************************")
        env_resp = client.get('https://ncm.services.nconprem-10-114-55-128.ccpnx.com/api/nutanix/v3/environments/' + i['uuid'])
        if env_resp.status_code != 200:
            print(f"ERROR: Environment GET failed!")
            print(f"  - Project Name: {pro[0]}")
            print(f"  - Project UUID: {pro[1]}")
            print(f"  - Environment UUID: {i['uuid']}")
            print(f"  - HTTP Status Code: {env_resp.status_code}")
            
            # Store failed environments to a file
            failed_env = {
                "project_name": pro[0],
                "project_uuid": pro[1],
                "environment_uuid": i['uuid'],
                "status_code": env_resp.status_code,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Append to failed environments log file
            with open('failed_environments.json', 'a') as f:
                f.write(json.dumps(failed_env) + '\n')
            
            continue
        env_response = json.loads(env_resp.content)
        print(f"Project [{pro[0]}]: environment: [{env_response['spec']['name']}]")
        policy_name = 'policy_' + env_response['spec']['name'] + '_' + str(uuid.uuid4())[:8]
        policy_uuid = str(uuid.uuid4())
        policy_pay['spec']['name'] = policy_name
        policy_pay['metadata']['uuid'] = policy_uuid
        for lo, j in enumerate(policy_pay['spec']['resources']['ordered_availability_site_list']):
            j['environment_reference']['uuid'] = i['uuid']
            temp_uuid = str(uuid.uuid4())
            policy_pay['spec']['resources']['app_protection_rule_list'][lo]['uuid'] = temp_uuid
            policy_pay['spec']['resources']['app_protection_rule_list'][lo]['name'] = 'rule_' + temp_uuid.replace('-', '')
        resp = client.post(URL + 'api/calm/v3.0/app_protection_policies', data=json.dumps(policy_pay))
        if resp.status_code != 200:
            print(json.dumps(json.loads(resp.content)))
            print(resp.status_code)
            continue
        print(f"Project [{pro[0]}]: policy [{policy_name}] created sucessfully")
            
