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

URL = "https://dm.services.nconprem-10-122-28-170.ccpnx.com/api/nutanix/v3/"

##### delete setup pending projects only
payload = {"kind":"project","length":20,"offset":0,"filter":"name==.*[s|S][t|T]_[p|P][r|R][o|O][j|J][e|E][c|C][t|T].*","sort_attribute":"name","sort_order":"ASCENDING"}
count = 1
delete_only_pending_proj = False
for i in range(20):
  payload['offset'] = i * 30
  resp = client.post(URL + 'projects/list', data=json.dumps(payload))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for pro in resp['entities']:
    if delete_only_pending_proj:
      if len(pro['data'][-6]['values']):
        continue
    print(f"Deleting project [{pro['metadata']['name']}], {count}")
    s = client.delete(URL + 'projects/' + pro['metadata']['uuid'], data=json.dumps({}))
    if s.status_code != 200:
      print(s.content, "error in delete url")
      continue
    print(s.content)
    count += 1

# v4 version
