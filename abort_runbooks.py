""" Nucalm environment setup"""


import os
import sys
import json
import uuid
import time
import copy
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/calm/v3.0/runbooks/runlogs/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

task_pay = {
    "variable_list": [],
    "attrs": {
        "script_type": "sh",
        "login_credential_local_reference": {
            "kind": "app_credential",
            "uuid": "00a68e94-00bc-d979-81e2-e9a1201d9da9"
        },
        "script": "date\necho \"sample text: installing random feature\"\ndate"
    },
    "name": "Task 10",
    "status_map_list": [],
    "inherit_target": False,
    "target_any_local_reference": {
        "kind": "app_endpoint",
        "name": "vpc_ep_10_10_10_97",
        "uuid": "8a4b538c-d3a8-4ce8-a159-ddbcf5a11afa"
    },
    "child_tasks_local_reference_list": [],
    "type": "EXEC",
    "uuid": "d9248aa4-1311-1c74-234f-31568906f06c"
}
rb_pay = {
    "spec": {
        "resources": {
            "credential_definition_list": [{"name":"admin","type":"PASSWORD","cred_class":"static","username":"root","secret":{"attrs":{"is_secret_modified":True},"value":"nutanix/4u"},"uuid":"35969953-7fc7-583c-b4f5-49ebb9dde5d1"}],
            "endpoint_definition_list": [],
            "runbook": {
                "name": "7a569433_runbook",
                "variable_list": [],
                "task_definition_list": [
                    {
                        "name": "6beb4ef6_dag",
                        "type": "DAG",
                        "child_tasks_local_reference_list": [
                            {
                                "kind": "app_task",
                                "uuid": "11347f51-4f78-5b27-05a5-e4c685d3a5f8"
                            }
                        ],
                        "attrs": {
                            "edges": []
                        },
                        "uuid": "060a8735-7383-ccda-6a8c-b75fb506997d"
                    },
                    {
                        "name": "Task 1",
                        "attrs": {
                            "script_type": "sh",
                            "script": "date"
                        },
                        "variable_list": [],
                        "child_tasks_local_reference_list": [],
                        "type": "EXEC",
                        "status_map_list": [],
                        "uuid": "11347f51-4f78-5b27-05a5-e4c685d3a5f8"
                    }
                ],
                "main_task_local_reference": {
                    "kind": "app_task",
                    "uuid": "060a8735-7383-ccda-6a8c-b75fb506997d"
                },
                "uuid": "c0b97ee8-5a41-4d85-b512-99e9f3cb5805"
            },
            "default_target_reference": {
                "name": "stress_single_vm",
                "kind": "app_endpoint",
                "uuid": "4da0cce5-94fa-9619-3b85-67a412a97bcf"
            }
        },
        "name": "vpc1"
    },
    "api_version": "3.0",
    "metadata": {
        "kind": "runbook",
        "project_reference": {
            "name": "vpc",
            "kind": "project",
            "uuid": "3d00e185-ba99-4a63-a7b8-9d3f290a1762"
        },
        "uuid": "50f58c1f-8465-e5aa-b39f-b0dbab9859a8"
    }
}

for i in range(1):
    list_response = client.post(URL + 'list', data=json.dumps({"length":50,"offset":0,"filter":"state==RUNNING"}))
    for j in json.loads(list_response.content)['entities']:
        s = client.get(URL +  j['metadata']['uuid'])
        s = json.loads(s.content)
        print("aborting", j['metadata']['uuid'])
# https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/calm/v3.0/runbooks/runlogs/72a3cfeb-dc63-45c6-8329-aa2bb689f924/children/list
        s = client.post(URL +  j['metadata']['uuid'] + '/abort', data=json.dumps({}))
        


# https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/calm/v3.0/runbooks/runlogs/72a3cfeb-dc63-45c6-8329-aa2bb689f924/abort
# {
#     "spec": {},
#     "api_version": "3.0",
#     "metadata": {
#         "kind": "runlog",
#         "uuid": "72a3cfeb-dc63-45c6-8329-aa2bb689f924"
#     }
# }
# {
#     "api_version": "3.0",
#     "metadata": {
#         "total_matches": 1,
#         "kind": "runlog"
#     },
#     "entities": [
#         {
#             "status": {
#                 "type": "policy_runlog",
#                 "name": "approval",
#                 "description": "",
#                 "parent_reference": {
#                     "name": "",
#                     "uuid": "72a3cfeb-dc63-45c6-8329-aa2bb689f924",
#                     "kind": "app_workflow_action_runlog"
#                 }