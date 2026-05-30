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

#VERIFY_FAILED
#DRAFT
#apps = "_state!=deleted"
for i in range(15):
  resp = client.post(URL + 'subnets/list', data=json.dumps({"length":30,"offset":i*30,"filter": ''}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for count, sub in enumerate(resp['entities']):
    if sub['status']['name'] in ['vlan.114', 'vlan.148', 'vlan.154', 'vlan.500', 'vlan.102']:continue
    print(f"Deleting subnet [{sub['status']['name']}]. count [{count * (i+1)}]")
    s = client.post(URL + 'batch', data=json.dumps({"action_on_failure":"CONTINUE","execution_order":"NON_SEQUENTIAL","api_request_list":[{"operation":"DELETE","path_and_params":f"/api/nutanix/v3/subnets/{sub['metadata']['uuid']}"}],"api_version":"3.0"}))