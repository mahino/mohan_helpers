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

BASE_URL = "https://ncm.services.nconprem-10-114-55-128.ccpnx.com/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL

list_groups_payload = {
    "group_offset": 0,
    "group_length": 2,
    "group_by": "app_family",
    "length": 1,
    "sort": "created_on",
    "sort_order": "DESCENDING",
    "fields": [
        "app_name",
        "uuid",
    ],
    "filter": "state!=deleted;app_family==Other_Apps"
}

timings = {}
actions_uuids = {
  "snapshot_config": {"uuid": "", "action_uuid": ""},
  "restore_config": {"uuid": "", "action_uuid": ""},
  "start": {"uuid": "", "action_uuid": ""},
  "stop": {"uuid": "", "action_uuid": ""},
  "restart": {"uuid": "", "action_uuid": ""},
  "create": {"uuid": "", "action_uuid": ""},
}
trigger_actions = [
  "snapshot_config",
#   "restore_config",
  # "start",
  # "stop",
  # "restart",
  # "create",
]
total = []
for i in range(1):
  resp = client.post(URL + "api/calm/v3.0/groups", data=json.dumps(list_groups_payload))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for index, group in enumerate(resp['group_results']):
    app_uuid = group['entity_results'][0]['uuid']
    app_name = group['entity_results'][0]['app_name']
    app_get = client.get(URL + V3 + 'apps/{}'.format(app_uuid))
    if app_get.status_code != 200:
      print(app_get.content, "error in get url")
    app_get = json.loads(app_get.content)
    project_uuid = app_get['metadata']['project_reference']['uuid']
    project_name = app_get['metadata']['project_reference']['name']
    for i in app_get['spec']['resources']['action_list']:
      if 'snapshot_config' in i['name'].lower():
        actions_uuids['snapshot_config'] = {'uuid': i['uuid'], 'action_uuid': i['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'][0]['uuid']}
      elif 'restore_config' in i['name'].lower():
        actions_uuids['restore_config'] = {'uuid': i['uuid'], 'action_uuid': i['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'][0]['uuid']}
      elif 'start' in i['name'].lower():
        actions_uuids['start'] = {'uuid': i['uuid'], 'action_uuid': i['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'][0]['uuid']}
      elif 'stop' in i['name'].lower():
        actions_uuids['stop'] = {'uuid': i['uuid'], 'action_uuid': i['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'][0]['uuid']}
      elif 'restart' in i['name'].lower():
        actions_uuids['restart'] = {'uuid': i['uuid'], 'action_uuid': i['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'][0]['uuid']}
      elif 'create' in i['name'].lower():
        actions_uuids['create'] = {'uuid': i['uuid'], 'action_uuid': i['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'][0]['uuid']}
    for action in trigger_actions:
      if actions_uuids[action] == "":
        print(f"Action {action} not found for app {app_name}")
        continue

    action_run_payload = {
        "api_version": "3.0",
        "metadata": {
            "project_reference": {
                "kind": "project",
                "name": project_name,
                "uuid": project_uuid
            },
            "name": app_name,
            "spec_version": 9,
            "kind": "app",
            "uuid": str(uuid.uuid4())
        },
        "spec": {
            "target_uuid": app_uuid,
            "target_kind": "Application",
            "args": [
                {
                    "name": "snapshot_name",
                    "value": "snapshot-@@{calm_array_index}@@-@@{calm_time}@@",
                    "task_uuid": actions_uuids[action]['action_uuid']
                }
            ]
        }
    }
    action_run_resp = client.post(URL + V3 + 'apps/{}/actions/{}/run'.format(app_uuid, actions_uuids[action]['uuid']), data=json.dumps(action_run_payload))
    if action_run_resp.status_code != 200:
      print(action_run_resp.content, "error in run url")
    action_run_resp = json.loads(action_run_resp.content)
    runlog_uuid = action_run_resp['status']['runlog_uuid']
    print(f"Waiting 5 seconds for runlog {runlog_uuid} to be created")
    time.sleep(5)
    runlog_pay = {'filter':'root_reference=={}'.format(runlog_uuid)}
    app_runlog_resp = client.post(URL + V3 + 'apps/{}/app_runlogs/list'.format(app_uuid), data=json.dumps(runlog_pay))
    if app_runlog_resp.status_code!=200:
        print("ERROR:", app_runlog_resp.content)
    app_runlog_resp = json.loads(app_runlog_resp.content)
    total_tasks = len(app_runlog_resp['entities'])
    success_tasks = 0
    wait_count = 0
    while success_tasks < total_tasks and wait_count < 10:
        print(f"Waiting 5 seconds for runlog {runlog_uuid} to be updated")
        time.sleep(5)
        app_runlog_resp = client.post(URL + V3 + 'apps/{}/app_runlogs/list'.format(app_uuid), data=json.dumps(runlog_pay))
        if app_runlog_resp.status_code!=200:
            print("ERROR:", app_runlog_resp.content)
        app_runlog_resp = json.loads(app_runlog_resp.content)
        total_tasks = len(app_runlog_resp['entities'])
        success_tasks = 0
        for runlog in app_runlog_resp['entities']:
            if runlog['status']['state'] == 'SUCCESS':
                success_tasks += 1
        wait_count += 1
        print(f"Total tasks: {total_tasks} Success tasks: {success_tasks}")
    if success_tasks == total_tasks:
        print(f"Action {action} successful for app {app_name}")
    else:
        print(f"Action {action} failed for app {app_name}\n total tasks: {total_tasks} success tasks: {success_tasks}")
