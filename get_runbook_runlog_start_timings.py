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
timings = {}
total = []
for i in range(1):
  resp = client.post(URL + 'runbooks/runlogs/list', data=json.dumps({"length":100,"offset":i*250,"filter":""}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for acc in resp['entities']:
    if acc['status']['state'] != 'SUCCESS':
      continue
    if int(acc['metadata']['creation_time'])//1000000 in timings:
      timings[int(acc['metadata']['creation_time'])//1000000] += 1
    else:
      timings[int(acc['metadata']['creation_time'])//1000000] = 1
    total.append(int(acc['metadata']['last_update_time'])//1000000 - int(acc['metadata']['creation_time'])//1000000)
print(timings)
print(sum(total)/(60*len(total)))
