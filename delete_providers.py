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

V3 = 'api/calm/v3.0/'

URL = BASE_URL + V3

#VERIFY_FAILED
#DRAFT
resp = client.post(URL + 'providers/list', data=json.dumps({"length":250,"offset":0,"filter":""}))
if resp.status_code != 200:
  print("error in list url")
resp = json.loads(resp.content)
for provider in resp['entities']:
  if provider['metadata']['name'] in ['Nutanix_PC', 'NDB']: continue
  print(f"Deleting resource_type [{provider['metadata']['name']}]")
  resp = client.delete(URL + 'providers/' + provider['metadata']['uuid'], data=json.dumps({}))
  print(resp.content)
