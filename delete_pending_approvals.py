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

V3 = 'api/calm/v3.0/'

URL = BASE_URL + V3

#VERIFY_FAILED
#DRAFT

count = 1
for i in range(1):
  resp = client.post(URL + 'approvals/list', data=json.dumps({"length":250,"offset":0*250,"sort_attribute":"creation_time","sort_order":"ASCENDING","filter":"pending_on_me==true"}))
  if resp.status_code != 200:
    print("error in list url")
  resp = json.loads(resp.content)
  for ap in resp['entities']:
    appreglist_ent1 = ap['status']['resources']['approval_set_list']
    uuid_1 = ap['metadata']['uuid']
    uuid_2 = appreglist_ent1[0]['uuid']
    uuid_3 = appreglist_ent1[0]['approval_element_list'][0]['uuid']
    print(f"Rejecting resource_type [{ap['metadata']['name']}]" + f":     {count}")
    resp = client.put(URL + f"approvals/{uuid_1}/approval_sets/{uuid_2}/approval_elements/{uuid_3}", data=json.dumps({"comment":"","state":"REJECTED","spec_version":0}))
    print(resp)
    count += 1
