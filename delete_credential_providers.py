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
#apps = "_state!=deleted"
count = 1
for i in range(1):
  resp = client.post(URL + 'accounts/list', data=json.dumps({"length":100,"offset":0,"filter":"type==custom_provider"}))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for acc in resp['entities']:
    print(acc['metadata']['name'], count)
    s = client.delete(URL + 'accounts/' + acc['metadata']['uuid'], data=json.dumps({}))
    count += 1