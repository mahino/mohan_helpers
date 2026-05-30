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

URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/api/nutanix/v3/policies"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

policy_pay = {
    "metadata": {
        "kind": "policy",
        "project_reference": {
            "kind": "project",
            "name": "Nucalm_manual",
            "uuid": "e4bb45fd-e89c-4282-aae5-17e6241022a0"
        },
        "uuid": "e2c31f51-1321-4141-957c-755fc991642f"
    },
    "spec": {
        "name": "gtewasfd",
        "description": "",
        "resources": {
            "action_list": [
                {
                    "action_type_reference": {
                        "kind": "policy_action_type",
                        "uuid": "6578208e-ab51-44ad-ad04-e4fdb0f536db"
                    },
                    "attrs": {
                        "approver_set_list": [
                            {
                                "type": "ANY",
                                "external_user_list": [],
                                "user_reference_list": [
                                    {
                                        "name": "admin",
                                        "kind": "user",
                                        "email": "",
                                        "uuid": "00000000-0000-0000-0000-000000000000"
                                    }
                                ],
                                "user_group_reference_list": [],
                                "name": "Set 1"
                            }
                        ]
                    }
                }
            ],
            "category_list": {
                "Project": "Nucalm_manual"
            },
            "condition_list": [
                {
                    "attribute_name": "Runbook Name",
                    "criteria_list": [
                        {
                            "lhs": "action_payload.spec.name",
                            "operator": "contains",
                            "rhs": "TEMP",
                            "is_primary": True
                        }
                    ]
                }
            ],
            "enabled": False,
            "event_reference": {
                "kind": "policy_event",
                "uuid": "5612ce6e-9726-49f3-8217-44e22f53b705"
            }
        }
    }
}


user_acc_count = int(sys.argv[2]) if len(sys.argv) == 3 else 1

count = 1
for i in range(100):
    policy_pay['metadata']['uuid'] = str(uuid.uuid4())
    policy_pay['spec']['name'] = 'policy_' + str(i+1)
    # policy_pay['spec']['resources']['event_reference']['uuid'] = str(uuid.uuid4())
    # policy_pay['spec']['resources']['action_list'][0]['action_type_reference']['uuid'] = str(uuid.uuid4())

    resp = client.post(URL, data=json.dumps(policy_pay))
    response = json.loads(resp.content)
    if resp.status_code != 200:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Policy [{response['spec']['name']}] created sucessfully, [{count}]")
    policy_uuid = response['metadata']['uuid']
    del response['status']
    response['spec']['resources']['enabled'] = True
    print(f"Updating policy [{response['spec']['name']}]")
    resp = client.put(URL + '/' + policy_uuid, data=json.dumps(response))
    if resp.status_code != 200:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Policy [{response['spec']['name']}] updated sucessfully, [{count}]")
    count+=1
    
