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

resp = client.post(URL + 'accounts/list', data=json.dumps({"length":250,"offset":0,"filter":"state!=DELETED;(type!=nutanix;type!=custom_provider)"}))
if resp.status_code != 200:
  print("error in list url")
resp = json.loads(resp.content)
account_uuids =[]
cluster_uuids =[]
for acc in resp['entities']:
  if 'RPC' in acc['metadata']['name']:
    account_uuids.append(acc['metadata']['uuid'])
    cluster_uuids.append(acc['status']['resources']['data']['cluster_account_reference_list'][0]['resources']['data']['cluster_uuid'])
print(json.dumps(account_uuids))
print(json.dumps(cluster_uuids))
