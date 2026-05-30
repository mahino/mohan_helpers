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


url = 'https://10.36.0.{}:9440/api/nutanix/v3/jobs/'.format(sys.argv[1])
payload = {"length":250,"offset":0,"filter":""}

s = []
reasons = []
for i in range(4):
  payload['offset'] = 250*i
  list_resp = client.post(url + 'list', data=json.dumps(payload))
  try:
    for j in json.loads(list_resp.content)['entities']:
      e = client.post(url + j['metadata']['uuid'] + '/instances', json.dumps({"length":10,"offset":0,"filter":""}))
      try:
        s.append(json.loads(e.content)['entities'][0]['resources']['start_time'])
        if json.loads(e.content)['entities'][0]['resources']['state'] == 'FAILED':
          print(e.content)
          reasons.append(json.loads(e.content)['entities'][0]['resources']['reason'])
      except IndexError:
        print(j['metadata']['name'])
  except TypeError:
    print('error at '+ str(i))
    pass
  print(i) 

q = {}
for i in s:
  if i in q:
    q[i] += 1
  else:
    q[i] = 1

print(q)
print(len(s),max(s))
print(list(set(reasons)), len(reasons))
