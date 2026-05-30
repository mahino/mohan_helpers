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

BASE_URL = 'https://10.36.199.{}:9440/'.format(sys.argv[1])
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

payload= {
  "entity_type": "nucalm_action",
  "group_member_attributes": [
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
      "attribute": "run_count"
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
  "group_member_offset": 500,
  "group_member_count": 500,
  "group_member_sort_order": "DESCENDING",
  "group_member_sort_attribute": "_created_timestamp_usecs_"
}
from collections import defaultdict

# Define a defaultdict with a default value of int (defaulting to 0)
d = defaultdict(int)

d = {"DAG": 5000, "EXEC": 84314, "SET_VARIABLE": 37053, "DECISION": 33018, "META": 74844, "WHILE_LOOP": 8808, "DELAY": 16878}
rb_count = 5000
for i in range(10,13):
  payload['group_member_offset'] = 500 * i
  resp = client.post(URL + 'groups', data=json.dumps(payload))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for acc in resp['group_results'][0]['entity_results']:
    name = acc['data'][0]['values'][0]['values'][0]
    print(name, rb_count)
    s = client.get(URL + 'runbooks/' + acc['entity_id'], data=json.dumps({}))
    for task in json.loads(s.content)['status']['resources']['runbook']['task_definition_list']:
      d[task['type']] += 1
    rb_count += 1

print(json.dumps(dict(d)))
