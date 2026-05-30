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
queued_count = 0
executed_count = 0
scheduled_count = 0
for i in range(1):
  resp = client.post(URL, data=json.dumps({"length": 50, "offset": i*50,"filter":""}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for count, sub in enumerate(resp['entities']):
    print(f"Fetching instances for scheduler [{sub['metadata']['name']}]. count [{count + (i*50)}]")
    instances_url = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/api/nutanix/v3/jobs/" + sub['metadata']['uuid'] + "/instances"
    s = client.post(instances_url, data=json.dumps({}))
    response = json.loads(s.content)
    for instance in response['entities']:
      if instance['resources']['state'] == 'SCHEDULED':
        scheduled_count += 1
      if instance['resources']['state'] == 'EXECUTED':
        executed_count += 1
print(f"Queued count: {queued_count}")
print(f"Scheduled count: {scheduled_count}")
print(f"Executed count: {executed_count}")
