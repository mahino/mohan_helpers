""" Nucalm environment setup"""


import os
import sys
import json
import uuid
import time
import urllib3
from requests.auth import HTTPBasicAuth
import requests
from concurrent.futures import ThreadPoolExecutor

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
count = 1
for i in range(1):
  resp = client.post(URL + 'runbooks/list', data=json.dumps({"length":250,"offset":i*250,"filter": ''}))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  print(f"Deleting {len(resp['entities'])} runbooks")
  for acc in resp['entities']:
    print(f"Deleting runbook [{acc['metadata']['name']}]. count [{count}]")

    if acc['metadata']['name'] == 'NTNX_LOCAL_AZ':
      print(f"Skipping system runbook: {acc['metadata']['name']}")
      continue
    s = client.delete(URL + 'runbooks/' + acc['metadata']['uuid'], data=json.dumps({}))
    if s.status_code == 200:
      print(f"Runbook [{acc['metadata']['name']}] deleted successfully")
    else:
      print(s.content, "error in delete url")
    count += 1
