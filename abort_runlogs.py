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


url = 'https://{0}:9440/api/calm/v3.0/runbooks/runlogs/'.format(sys.argv[1])
payload = {"length":45,"offset":0,"filter":"state==POLICY_EXEC"}

s = []
list_resp = client.post(url + 'list', data=json.dumps(payload))
for j in json.loads(list_resp.content)['entities']:
  s = client.get(url +  j['metadata']['uuid'])
  s = json.loads(s.content)
  del s['status']
  print('aborting', j['metadata']['uuid'])
  s = client.post(url +  j['metadata']['uuid'] + '/abort', data=json.dumps(s))
