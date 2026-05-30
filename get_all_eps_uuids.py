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

resp = client.post(URL + 'endpoints/list', data=json.dumps({"length":250,"offset":0,"filter":"name==.*[v|V][p|P][c|C].*;_state!=DELETED"}))
if resp.status_code != 200:
  print("error in list url")
resp = json.loads(resp.content)
ep_uuids =[]
print(json.dumps(resp))
for ep in resp['entities']:
  ep_uuids.append([ep['metadata']['name'], ep['metadata']['uuid']])
print(json.dumps(ep_uuids))
