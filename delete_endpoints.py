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


client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = "https://10.36.199.79:9440/api/nutanix/v3/endpoints"
#VERIFY_FAILED
#DRAFT
#apps = "_state!=deleted"
count = 1
for i in range(1):
  resp = client.post(URL + "/list", data=json.dumps({"length":200,"offset":0,"filter":"name==.*.*;_state!=DELETED"}))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  print(f"Deleting {len(resp['entities'])} endpoints")
  for acc in resp['entities']:
    print(f"Deleting endpoint [{acc['metadata']['name']}]. count [{count}]")
    s = client.delete(URL + '/' + acc['metadata']['uuid'], data=json.dumps({}))
    if s.status_code != 200:
      print(s.content, "error in delete url")
      continue
    print(f"Endpoint [{acc['metadata']['name']}] deleted successfully")
    count += 1
