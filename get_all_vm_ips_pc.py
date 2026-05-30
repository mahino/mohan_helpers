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

BASE_URL = "https://10.36.199.35:9440/api/nutanix/v3/accounts/3e720a50-b0da-421e-b54b-e9ac9a3f0a51/vms/list"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3
payload = {"length":10,"offset":0,"filter":""}
resp = client.post(URL, data=json.dumps(payload))
if resp.status_code != 200:
  print("error in list url")
resp = json.loads(resp.content)
account_uuids =[]
print(json.dumps(resp))
for acc in resp['entities']:
  account_uuids.append(acc['metadata']['uuid'])
print(json.dumps(account_uuids))
