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
for i in range(50):
  payload["filter"] = "state==ACTIVE"
  #payload['offset'] = 250*i
  list_resp = client.post(url + 'list', data=json.dumps(payload))
  try:
    for j in json.loads(list_resp.content)['entities']:
      e = json.loads(client.get(url + j['metadata']['uuid']).content)
      print(e['resources']['state'])
      #if 'schedule' in e['resources']['schedule_info']:
      if e['resources']['state'] == 'ACTIVE':
        e['resources']['schedule_info'] = {
            "execution_time": "1638930600",
            "time_zone": "Asia/Kolkata"
        }
        e['resources']['type'] = 'ONE-TIME'
        print(e['metadata']['name'], i)
        s = client.delete(url + j['metadata']['uuid'])
        #break
  except TypeError as msg:
    print('error at '+ str(i), msg)
    pass
  print(i)    

q = {}
for i in s:
  if i in q:
    q[i] += 1
  else:
    q[i] = 1

print(q)
print(max(s))
    
