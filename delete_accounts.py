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
#resp = client.post(URL + 'accounts/list', data=json.dumps({"length":250,"offset":0,"filter":"state==DRAFT"}))
resp = client.post(URL + 'accounts/list', data=json.dumps({"length":250,"offset":0}))
if resp.status_code != 200:
  print("error in list url")
resp = json.loads(resp.content)
print(f"Deleting {len(resp['entities'])} accounts")

count = 1
for acc in resp['entities']:
    # if 'RPC' in acc['metadata']['name']:
      print(f"Deleting account [{acc['metadata']['name']}]. count [{count}]")
      delete_resp = client.delete(URL + 'accounts/' + acc['metadata']['uuid'], data=json.dumps({}))
      if delete_resp.status_code == 200:
        print(f"Account [{acc['metadata']['name']}] deleted successfully")
      else:
        print(delete_resp.content, "error in delete url")
      count += 1

