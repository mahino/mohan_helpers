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

BASE_URL = 'https://{}:9440/'.format(sys.argv[1])
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

groups_pay = {
    "entity_type": "nucalm_action",
    "group_member_attributes": [
        {
            "attribute": "run_count"
        },
        {
            "attribute": "name"
        },
        {
            "attribute": "project_name"
        },
        {
            "attribute": "state"
        },
        {
            "attribute": "running_runs"
        },
        {
            "attribute": "owner_username"
        },
        {
            "attribute": "last_run_time"
        },
        {
            "attribute": "_modified_timestamp_usecs_"
        }
    ],
    "filter_criteria": "state!=DELETED;type==workflow;is_mutable==true",
    "group_member_offset": 0,
    "group_member_count": 50,
    "group_member_sort_order": "DESCENDING",
    "group_member_sort_attribute": "_created_timestamp_usecs_"
}
run_count = 0
rb_uuids = []
for i in range(40):
  groups_pay['group_member_offset'] += 50
  resp = client.post(URL + 'groups', data=json.dumps(groups_pay))
  if resp.status_code != 200:
    print("error in list url")
  resp = json.loads(resp.content)
  for rb in resp['group_results'][0]['entity_results']:
    print(rb['data'][1]['values'][0]['values'][0])
    rb_uuids.append([rb['data'][1]['values'][0]['values'][0], rb['entity_id']])
    if len(rb['data'][0]['values']):
      run_count += int(rb['data'][0]['values'][0]['values'][0])
print(json.dumps(rb_uuids))
print(run_count)