""" Nucalm environment setup"""


import os
import sys
import json
import uuid
import time
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://dm.services.nconprem-10-114-55-128.ccpnx.com/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3
ENV_URL = URL.replace('dm', 'ncm')

projects_list = [["Nucalm_10_37_18_csx4", "e8839a7b-d1da-46d4-986f-7b384a482518"],["Nucalm_10_36_50_vb29", "a4b98c7f-3af5-4971-be50-aff44492d1c2"], ["Nucalm_10_36_28_nv7b", "37e92fc8-9619-4313-bc0d-439e323c518b"], ["Nucalm_10_35_56_pfjh", "77ef9ab1-319a-48b1-86d1-c1a2f40bded2"], ["Nucalm_10_35_53_9zj8", "54f9bf76-4f3d-4cb4-a5a1-f9dfcb2a3577"], ["Nucalm_10_35_36_87vv", "5d259589-ee6f-43c5-873b-2e250895bb0b"], ["Nucalm_10_35_09_3tau", "469179a5-2ec4-44a0-aea8-91c8239a431a"], ["Nucalm_10_35_04_xjxy", "b90eab0c-1a3e-4f6c-a1a1-9c7300d6e58f"], ["Nucalm_10_34_05_ln0k", "dcdccd08-1141-4948-832c-d8d347fcd820"], ["Nucalm_10_34_03_izzi", "10a95458-cd15-46b8-b6cb-4eb8325371f9"], ["Nucalm_10_33_47_8s41", "89d3d3b5-cce2-4d8b-a264-a4e6309fac02"], ["Nucalm_10_33_27_o9ug", "8f605aa7-7902-4eb4-bf41-0b7cee357c2d"], ["Nucalm_10_33_19_tb0u", "2bfb3a77-3f06-4bd6-9edf-f40d3c592731"], ["Nucalm_10_32_33_pqpe", "6f5ab514-1656-4f1b-b6f0-9c50f1db3b5c"], ["Nucalm_10_32_23_5nga", "b5ff288b-2f7b-4068-9c06-e0605b4a05b7"], ["Nucalm_10_32_04_ii07", "f1463042-c6b9-42be-8819-5db2e17f73ad"], ["Nucalm_10_31_47_vvat", "854ae26c-afa3-4558-b3b2-57b7bb01175c"], ["Nucalm_10_31_46_mkhc", "843dabf3-451d-48a1-81ae-71a67ef570ea"], ["Nucalm_10_30_48_fmrf", "6516765f-12b5-47a0-ba29-2afebd660730"], ["Nucalm_10_30_47_xvdc", "fc59643e-b27e-45ae-9b83-20137e9cf6dc"], ["Nucalm_10_30_32_35g9", "047ac10a-1f19-459c-b10d-b5070ecb3abe"], ["Nucalm_10_30_10_yt74", "4ecc1b70-634a-4f2e-9fcf-c003a3d692e2"], ["Nucalm_10_30_08_d3ik", "119c5f4d-0fcc-4cdb-ab81-ca0da88f3ef8"], ["Nucalm_10_29_01_t8jl", "d7f34913-fbd4-43cd-af7f-73264c5360c7"], ["Nucalm_10_28_59_dknb", "de76d348-53a2-4551-bb54-54e6025e8b2e"], ["Nucalm_10_28_49_mqb0", "18cf00cd-ae27-4153-a468-86845c53140e"], ["Nucalm_10_28_39_kb6g", "bf1a521e-bc3b-41f6-92bb-2f6848c112f9"], ["Nucalm_10_28_32_5vmv", "fff00c6a-5dcb-4305-bae5-8388281f09ad"], ["Nucalm_10_27_26_ge48", "5c7b9f7a-5214-4fbc-ab86-dbcf152ff364"], ["Nucalm_10_27_20_dal1", "0072d59f-fe0a-40c5-896f-e6d105849d98"], ["Nucalm_10_27_07_tzpd", "03dd6df5-a830-4930-8300-08e4b12f0a43"], ["Nucalm_10_26_52_2f8k", "4aec72e2-a983-48d9-890a-039bfcf26c52"], ["Nucalm_10_26_42_7rmj", "7497a370-80ac-4fe7-9f2a-e33909d3e5e6"], ["Nucalm_10_25_55_pgy3", "efbac12c-6f39-4775-97a3-24a64a0e8285"], ["Nucalm_10_25_53_h4ly", "7b7b743d-ea51-400a-8328-1c19574fb19c"], ["Nucalm_10_25_40_skq0", "086c6f0c-bcca-445e-b2df-bf7f7e6b5753"], ["Nucalm_10_25_27_c641", "62e27622-e729-44fc-b7bd-948adc9df717"], ["Nucalm_10_25_16_twc4", "5ebdc915-7a97-4f4a-8f5a-34ea80332aef"], ["Nucalm_10_24_25_df1t", "acf9e7a6-86c6-466c-92f9-39e95842258b"], ["Nucalm_10_24_25_gxss", "b6224353-4391-4772-be99-f8d2b61d4914"], ["Nucalm_10_24_16_xywy", "117e6a7f-2e73-48f4-a772-72ff33a2cbd5"], ["Nucalm_10_23_57_34lw", "cd7e1913-cd2d-4b20-92dc-f2ca687837e9"], ["Nucalm_10_23_54_9ioo", "b15623f4-cc8d-4d15-855e-1f25c2bb4ab7"], ["Nucalm_10_22_29_hseb", "52441dd5-15d3-4a6d-ac90-1fa3b16a5e68"], ["Nucalm_10_22_29_7sza", "9eeacb50-a83e-4981-8212-67c12208c61f"], ["Nucalm_10_22_28_43wl", "68117cdd-fad9-4d84-8811-c5a8cc80e769"], ["Nucalm_10_22_28_tmrh", "61a32683-d6d6-468e-aa83-3fb4359b3cda"], ["Nucalm_10_22_27_b2xq", "986ec924-0d96-4de8-a384-349f12ed9360"], ["Nucalm_10_16_55_j21m", "9427fa64-da04-439a-905e-debbd73bb32c"], ["TestP1", "5e8af0a9-be7c-448e-aaaa-04384f5bd7bc"]]

env_payload = {
    "api_version": "3.0",
    "metadata": {
        "kind": "environment",
        "project_reference": {
            "kind": "project",
            "name": "Nucalm_10_22_28_tmrh",
            "uuid": "61a32683-d6d6-468e-aa83-3fb4359b3cda"
        },
        "uuid": "975506d3-11c8-ac4c-fe07-2154417f4231"
    },
    "spec": {
        "name": "temp",
        "description": "",
        "resources": {
            "substrate_definition_list": [
                {
                    "variable_list": [],
                    "type": "AHV_VM",
                    "os_type": "Windows",
                    "action_list": [],
                    "create_spec": {
                        "name": "vm-@@{calm_array_index}@@-@@{calm_time}@@",
                        "resources": {
                            "disk_list": [
                                {
                                    "data_source_reference": {
                                        "kind": "image",
                                        "name": "WindowsServer2016",
                                        "uuid": "4de0400d-4cf2-4786-ab58-286ef12d0c79"
                                    },
                                    "device_properties": {
                                        "device_type": "DISK",
                                        "disk_address": {
                                            "device_index": 0,
                                            "adapter_type": "SCSI"
                                        }
                                    },
                                    "disk_size_mib": 102400
                                }
                            ],
                            "memory_size_mib": 1024,
                            "num_sockets": 1,
                            "num_vcpus_per_socket": 1,
                            "account_uuid": "e54e7b86-2b74-4050-8808-9173cbb8020f",
                            "boot_config": {
                                "boot_device": {
                                    "disk_address": {
                                        "device_index": 0,
                                        "adapter_type": "SCSI"
                                    }
                                },
                                "boot_type": "LEGACY"
                            },
                            "gpu_list": [],
                            "nic_list": [
                                {
                                    "subnet_reference": {
                                        "uuid": "caf59b43-36f8-43d3-999e-c117631a5666"
                                    }
                                }
                            ],
                            "power_state": "ON"
                        },
                        "categories": {},
                        "cluster_reference": {
                            "name": "SSCG_NCM_2_1_Small_PE2",
                            "uuid": "00065035-daa1-70e4-7faf-ac1f6b61e0cf"
                        }
                    },
                    "readiness_probe": {
                        "disable_readiness_probe": True,
                        "connection_type": "POWERSHELL",
                        "connection_port": 5985,
                        "connection_protocol": "http",
                        "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                        "login_credential_local_reference": {
                            "kind": "app_credential",
                            "uuid": "18e68dd8-ccdc-67df-7aff-806580082c6c"
                        }
                    },
                    "name": "Untitled",
                    "uuid": "fe0edd4f-06f3-f274-8b99-cb8ca30419b1"
                },
                {
                    "variable_list": [],
                    "type": "AHV_VM",
                    "os_type": "Linux",
                    "action_list": [],
                    "create_spec": {
                        "name": "vm-@@{calm_array_index}@@-@@{calm_time}@@",
                        "resources": {
                            "disk_list": [
                                {
                                    "data_source_reference": {
                                        "kind": "image",
                                        "name": "Centos7HadoopMaster",
                                        "uuid": "4e87ff95-1e83-4ab1-9cc7-bf0a3afd664b"
                                    },
                                    "device_properties": {
                                        "device_type": "DISK",
                                        "disk_address": {
                                            "device_index": 0,
                                            "adapter_type": "SCSI"
                                        }
                                    },
                                    "disk_size_mib": 20480
                                }
                            ],
                            "memory_size_mib": 256,
                            "num_sockets": 1,
                            "num_vcpus_per_socket": 1,
                            "account_uuid": "e54e7b86-2b74-4050-8808-9173cbb8020f",
                            "boot_config": {
                                "boot_device": {
                                    "disk_address": {
                                        "device_index": 0,
                                        "adapter_type": "SCSI"
                                    }
                                },
                                "boot_type": "LEGACY"
                            },
                            "gpu_list": [],
                            "nic_list": [
                                {
                                    "subnet_reference": {
                                        "uuid": "caf59b43-36f8-43d3-999e-c117631a5666"
                                    }
                                }
                            ],
                            "power_state": "ON"
                        },
                        "categories": {},
                        "cluster_reference": {
                            "name": "SSCG_NCM_2_1_Small_PE2",
                            "uuid": "00065035-daa1-70e4-7faf-ac1f6b61e0cf"
                        }
                    },
                    "readiness_probe": {
                        "disable_readiness_probe": True,
                        "connection_type": "SSH",
                        "connection_port": 22,
                        "connection_protocol": "",
                        "address": "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
                        "login_credential_local_reference": {
                            "kind": "app_credential",
                            "uuid": "4c7d6f26-7ec2-d7bf-19ae-74ebf7832d2a"
                        }
                    },
                    "name": "Untitled",
                    "uuid": "98a0740e-3c31-0711-d154-a104d6cb891a"
                }
            ],
            "credential_definition_list": [
                {
                    "name": "administrator",
                    "type": "PASSWORD",
                    "cred_class": "static",
                    "username": "administrator",
                    "secret": {
                        "attrs": {
                            "is_secret_modified": True
                        },
                        "value": "Nutanix/4u"
                    },
                    "uuid": "18e68dd8-ccdc-67df-7aff-806580082c6c"
                },
                {
                    "name": "admin",
                    "type": "PASSWORD",
                    "cred_class": "static",
                    "username": "root",
                    "secret": {
                        "attrs": {
                            "is_secret_modified": True
                        },
                        "value": "nutanix/4u"
                    },
                    "uuid": "4c7d6f26-7ec2-d7bf-19ae-74ebf7832d2a"
                }
            ],
            "infra_inclusion_list": [
                {
                    "account_reference": {
                        "uuid": "5268e859-8177-41cc-b5cd-ceac001a1ddd",
                        "kind": "account"
                    },
                    "type": "nutanix_pc",
                    "subnet_references": [
                        {
                            "uuid": "4d3fb742-333b-4167-9a36-0e600dea43be"
                        },
                        {
                            "uuid": "ef70b4c6-e822-4212-bed1-2e0d91931d28"
                        },
                        {
                            "uuid": "80b29b1e-e419-4686-9b64-f0eee3dc6eeb"
                        },
                        {
                            "uuid": "0468324a-101c-4e10-ab92-0f406b276709"
                        },
                        {
                            "uuid": "f0f85659-c071-4fd6-bb05-df1a45448a15"
                        },
                        {
                            "uuid": "6502f67f-bd02-49e3-a55a-a37846198e2b"
                        },
                        {
                            "uuid": "d9910cec-6c62-421c-95c4-2437b647d647"
                        },
                        {
                            "uuid": "10bc5e02-5088-4795-aea0-18f0566a841b"
                        },
                        {
                            "uuid": "caf59b43-36f8-43d3-999e-c117631a5666"
                        }
                    ],
                    "cluster_references": [
                        {
                            "uuid": "00065031-3c14-1b72-7e15-7cc2558641c8"
                        },
                        {
                            "uuid": "00065035-b0c9-5144-07ad-7cc255864212"
                        },
                        {
                            "uuid": "00065035-daa1-70e4-7faf-ac1f6b61e0cf"
                        }
                    ],
                    "vpc_references": [],
                    "default_subnet_reference": {
                        "uuid": "4d3fb742-333b-4167-9a36-0e600dea43be"
                    }
                }
            ]
        }
    }
}


for pro in projects_list:

    print(f"Emptying save project: [{pro[0]}]")
    print("="*80, f"\nGet project:2 [{pro[0]}]")
    s = client.get(URL + 'projects_internal/' + pro[1])
    if s.status_code != 200:
      print("ERROR: faield to get project")
      print("="*80)
      continue
    response = json.loads(s.content)
    payload = {
      'metadata': response['metadata'],
      'api_version': "3.1",
      'spec': response['spec']
    }

    del payload['metadata']['last_update_time']
    del payload['spec']['project_detail']['resources']['resource_domain']

    print(f"Updating project: [{pro[0]}]")
    resp = client.put(URL + 'projects_internal/' + pro[1], data=json.dumps(payload))
    print(resp.content)
    
    
    
    