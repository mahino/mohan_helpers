""" Nucalm environment setup"""


import os
import random
import sys
import json
import uuid
import time
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

action_payload = {
    "api_version": "3.0",
    "metadata": {
        "project_reference": {
            "kind": "project",
            "name": "",
            "uuid": ""
        },
        "categories_mapping": {
            "TemplateType": [
                "Vm"
            ]
        },
        "name": "",
        "creation_time": "1763719536096910",
        "spec_version": 3,
        "kind": "app",
        "last_update_time": "1763719778314057",
        "uuid": "",
        "categories": {
            "TemplateType": "Vm"
        },
        "owner_reference": {
            "kind": "user",
            "name": "admin",
            "uuid": "00000000-0000-0000-0000-000000000000"
        }
    },
    "spec": {
        "target_uuid": "",
        "target_kind": "Application",
        "args": []
    }
}

scheduler_payload = {
    "api_version": "3.0",
    "metadata": {
        "kind": "job",
        "project_reference": {
            "name": "Nucalm_05rl",
            "uuid": "85990dd7-a9f9-4ccd-94a4-7a5034df6cd4",
            "kind": "project"
        },
        "uuid": "7f02edf7-b75a-4394-6b2e-1088e42bc99d"
    },
    "resources": {
        "description": "",
        "type": "ONE-TIME",
        "schedule_info": {
            "time_zone": "Asia/Calcutta",
            "execution_time": "1763663400"
        },
        "name": "scheduler_test",
        "executable": {
            "entity": {
                "type": "app",
                "uuid": "8a4814e9-57b0-4a0a-a4ed-f0474618d371"
            },
            "action": {
                "type": "APP_ACTION_RUN",
                "spec": {
                    "uuid": "00726580-7124-4e4c-9236-b413073f0dd0",
                    "payload": ""
                }
            }
        }
    }
}

scheduler_url = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/nutanix/v3/jobs"

project_list_url = "https://dm.services.nconprem-10-53-60-173.ccpnx.com/api/nutanix/v3/projects/list"
project_list_payload = {"length":250,"offset":0,"filter":""}


stop_execute_gap = 600
start_execute_gap = 7200


# project_count = 0
# app_count = 0
# scheduler_count = 0
# for i in range(2):
#     project_list_payload['offset'] = i*250
#     project_list_response = client.post(project_list_url, data=json.dumps(project_list_payload))
#     project_list_response = json.loads(project_list_response.content)
#     for project in project_list_response['entities']:
#         project_uuid = project['metadata']['uuid']
#         project_name = project['metadata']['name']
#         apps_list_url ="https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/nutanix/v3/apps/list"
#         for j in range(10):
#             app_list_payload = {"length":250,"offset":j*250,"filter": f"_state!=deleted;project_reference=={project_uuid};name==.*[n|N][u|U][c|C][a|A][l|L][m|M]_.*"}
#             apps_list_response = client.post(apps_list_url, data=json.dumps(app_list_payload))
#             apps_list_response = json.loads(apps_list_response.content)
#             if len(apps_list_response['entities']) == 0:
#                 print(f"No apps found for project {project_name}, breaking out of loop")
#                 break
#             for app in apps_list_response['entities']:
#                 if app['status']['state'] == 'error':
#                     print(f"App {app['metadata']['name']} is in error state, skipping")
#                     continue
#                 app_uuid = app['metadata']['uuid']
#                 app_name = app['metadata']['name']
#                 get_app_url = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/nutanix/v3/apps/" + app_uuid
#                 get_app_response = client.get(get_app_url)
#                 get_app_response = json.loads(get_app_response.content)
#                 scheduler_name = ""
#                 try:
#                     for action in get_app_response['spec']['resources']['action_list']:
#                         if action['name'] == 'action_start':
#                             start_action_uuid = action['uuid']
#                         elif action['name'] == 'action_stop':
#                             stop_action_uuid = action['uuid']
#                 except Exception as e:
#                     print(f"Error getting app {app_name}: {e}")
#                     continue
#                 for action in ['stop', 'start']:

#                     schedule_time = int(time.time() + 60) + (stop_execute_gap if action == 'stop' else start_execute_gap)
#                     print(f"Creating scheduler for {app_name}-{action} of project {project_name} scheduled at {schedule_time}")
#                     print(f"Project count: {project_count}, App count: {app_count}, Scheduler count: {scheduler_count}")
#                     scheduler_name = app_name + "_" + action
#                     action_payload['metadata']['name'] = scheduler_name
#                     action_payload['metadata']['project_reference']['name'] = project_name
#                     action_payload['metadata']['project_reference']['uuid'] = project_uuid
#                     action_payload['metadata']['uuid'] = app_uuid
#                     action_payload['spec']['target_uuid'] = app_uuid
#                     action_payload['spec']['target_kind'] = 'Application'
#                     action_payload['spec']['args'] = []
#                     scheduler_payload['metadata']['uuid'] = str(uuid.uuid4())
#                     scheduler_payload['metadata']['project_reference']['name'] = project_name
#                     scheduler_payload['metadata']['project_reference']['uuid'] = project_uuid
#                     scheduler_payload['resources']['name'] = scheduler_name
#                     scheduler_payload['resources']['executable']['entity']['uuid'] = app_uuid
#                     scheduler_payload['resources']['executable']['action']['spec']['uuid'] = start_action_uuid if action == 'start' else stop_action_uuid
#                     scheduler_payload['resources']['executable']['action']['spec']['payload'] = json.dumps(action_payload)
#                     scheduler_payload['resources']['schedule_info']['execution_time'] = str(schedule_time)
#                     scheduler_response = client.post(scheduler_url, data=json.dumps(scheduler_payload))
#                     if scheduler_response.status_code != 200:
#                         print(f"Error creating scheduler for {app_name}-{action} of project {project_name}: {scheduler_response.content}")
#                         continue
#                     scheduler_response = json.loads(scheduler_response.content)
#                     print(f"Scheduler created for {app_name}-{action} of project {project_name} at {schedule_time}")
#                     scheduler_count += 1
#                 app_count += 1
#                 stop_execute_gap += 30
#                 start_execute_gap += 30
#         project_count += 1

payload = {
    "api_version": "3.0",
    "metadata": {
        "kind": "job",
        "project_reference": {
            "name": "Nucalm_05rl",
            "uuid": "85990dd7-a9f9-4ccd-94a4-7a5034df6cd4",
            "kind": "project"
        },
        "uuid": "6e2f9112-f349-a699-05cd-7a1f23beb194"
    },
    "resources": {
        "description": "",
        "type": "ONE-TIME",
        "schedule_info": {
            "time_zone": "Asia/Calcutta",
            "execution_time": "1764586980"
        },
        "name": "t4eszdgf",
        "executable": {
            "entity": {
                "type": "runbook",
                "uuid": "e42b4722-31c5-44af-ad76-2a1ec05d41d6"
            },
            "action": {
                "type": "RUNBOOK_RUN",
                "spec": {
                    "payload": "{\"spec\":{\"args\":[],\"default_target_reference\":{\"kind\":\"app_endpoint\",\"name\":\"100_ST_Endpoint_4_1a5\",\"uuid\":\"750846b3-3fea-4b7c-b4c9-6d06cd6877db\"},\"execution_name\":\"\"}}"
                }
            }
        }
    }
}
payload = {
    "api_version": "3.0",
    "metadata": {
        "kind": "job",
        "project_reference": {
            "name": "Nucalm_05rl",
            "uuid": "85990dd7-a9f9-4ccd-94a4-7a5034df6cd4",
            "kind": "project"
        },
        "uuid": "b0964027-236d-75ab-e527-52c3c967096c"
    },
    "resources": {
        "description": "",
        "type": "RECURRING",
        "schedule_info": {
            "start_time": "1764527400",
            "schedule": "* * * * *",
            "expiry_time": "1764613800",
            "time_zone": "Asia/Calcutta"
        },
        "name": "reasdf",
        "executable": {
            "entity": {
                "type": "runbook",
                "uuid": "e42b4722-31c5-44af-ad76-2a1ec05d41d6"
            },
            "action": {
                "type": "RUNBOOK_RUN",
                "spec": {
                    "payload": "{\"spec\":{\"args\":[],\"default_target_reference\":{\"kind\":\"app_endpoint\",\"name\":\"100_ST_Endpoint_4_1a5\",\"uuid\":\"750846b3-3fea-4b7c-b4c9-6d06cd6877db\"},\"execution_name\":\"\"}}"
                }
            }
        }
    }
}
execution_time = str(int(time.time()) + 300)
scheduler_name = "mohan_scheduler_test_" + str(random.randint(1, 1000))
for i in range(10):
    payload['metadata']['uuid'] = str(uuid.uuid4())
    # payload['resources']['schedule_info']['execution_time'] = str(int(payload['resources']['schedule_info']['execution_time']) + 600)
    # payload['resources']['schedule_info']['execution_time'] = execution_time
    payload['resources']['name'] = scheduler_name + "_" + str(i)
    # print(f"Creating scheduler for {payload['resources']['name']} at {payload['resources']['schedule_info']['execution_time']}")
    scheduler_response = client.post(scheduler_url, data=json.dumps(payload))
    if scheduler_response.status_code != 200:
        print(scheduler_response.content)
        print(f"Error creating scheduler for {payload['resources']['name']} at {payload['resources']['schedule_info']['execution_time']}")
        continue
    scheduler_response = json.loads(scheduler_response.content)
    print(f"Scheduler created for {payload['resources']['name']} at {payload['resources']['schedule_info']['start_time']}")
