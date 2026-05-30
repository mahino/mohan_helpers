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

BASE_URL = f"https://dm.services.nconprem-10-114-55-128.ccpnx.com/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

resp = client.post(URL + 'projects/list', data=json.dumps({"length":250,"offset":0}))
if resp.status_code != 200:
  print("error in list url")
resp = json.loads(resp.content)
account_uuids =[]
for acc in resp['entities']:
  account_uuids.append([acc['metadata']['name'],acc['metadata']['uuid']])
print(json.dumps(account_uuids))
