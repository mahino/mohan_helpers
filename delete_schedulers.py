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

BASE_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/nutanix/v3/jobs/list"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

URL = BASE_URL 

#VERIFY_FAILED
#DRAFT
#apps = "_state!=deleted"
for i in range(20):
  resp = client.post(URL, data=json.dumps({"length": 20, "offset": 0,"filter":"state==ACTIVE"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for count, sub in enumerate(resp['entities']):
    print(f"Deleting scheduler [{sub['metadata']['name']}]. count [{count * (i+1)}]")
    delete_url = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/nutanix/v3/jobs/" + sub['metadata']['uuid']
    s = client.delete(delete_url, data=json.dumps({}))
    print(s.content)