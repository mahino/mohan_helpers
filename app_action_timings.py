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

BASE_URL = "https://ncm.cluster-name.nutanix.com:9440/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

payload = {
    "length": 500,
    "offset": -500,
    "sort": "updated_on",
    "sort_order": "DESCENDING",
    "fields": [
        "app_name",
        "uuid",
        "categories",
        "project_name",
        "account_names",
        "substrate_types",
        "source_marketplace_name",
        "state",
        "environment",
        "marketplace_version",
        "vm_names",
        "owner",
        "app_url",
        "created_on",
        "updated_on",
        "protection_status",
        "failover_status"
    ],
    "filter": "state!=deleted"
}

payload = {
    "length": 126,
    "offset": 0,
    "filter": "_state!=deleted",
    "sort_attribute": "created_on",
    "sort_order": "ASCENDING"
}
timings = {}
total = []
# for app_uuid in app_uuids:
for i in range(1):
  # payload['offset'] += 500
  resp = client.post(URL + "/apps/list", data=json.dumps(payload))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for index, app in enumerate(resp['entities']):
    if 'Infrastructure' == app['status']['name']:continue
    print(app['status']['name'], index+1 +payload['offset'])
    app_uuid = app['status']['uuid'] 
    runlog_pay = {'filter':'application_reference=={};(type==action_runlog,type==audit_runlog,type==ngt_runlog,type==clone_action_runlog,type==platform_sync_runlog,type==patch_runlog)'.format(app_uuid)}
    app_runlog_resp = client.post(URL + 'apps/{}/app_runlogs/list'.format(app_uuid), data=json.dumps(runlog_pay))
    if app_runlog_resp.status_code!=200:
      print("ERROR:", app_runlog_resp.content)
      # break
    for action in json.loads(app_runlog_resp.content)['entities']:
      try:
        print(action['status']['action_reference']['name'], int(action['metadata']['last_update_time'])//1000000 - int(action['metadata']['creation_time'])//1000000)
        if action['status']['state'] != 'SUCCESS':
          continue
        if action['status']['action_reference']['name'] in timings:
          timings[action['status']['action_reference']['name']].append(int(action['metadata']['last_update_time'])//1000000 - int(action['metadata']['creation_time'])//1000000)
        else:
          timings[action['status']['action_reference']['name']] = [int(action['metadata']['last_update_time'])//1000000 - int(action['metadata']['creation_time'])//1000000]
      except KeyError:
        pass
  
print(timings)




