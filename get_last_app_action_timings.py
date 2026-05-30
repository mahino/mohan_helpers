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
end_timings = {}
total = []
error_list = {}
message_list = []
count = 251
c=0
for i in range(2):
  l = 250
  #if i == 1:
  #  l=150
  resp = client.post(URL + 'apps/list', data=json.dumps({"length":l,"offset":i*250, "filter":"_state!=deleted"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for acc in resp['entities']:
    print(acc['metadata']['name'])
    actions_spec = client.post(URL + 'apps/' + acc['metadata']['uuid'] + '/app_runlogs/list', data=json.dumps({"filter":"application_reference=={};(type==action_runlog,type==audit_runlog,type==ngt_runlog,type==clone_action_runlog,type==platform_sync_runlog,type==patch_runlog)".format(acc['metadata']['uuid'])}))
    if actions_spec.status_code!= 200:
      print(actions_spec.content)
    for i in json.loads(actions_spec.content)['entities']:
      try:
        if i['status']['action_reference']['name'] == 'action_stop':
          actions_spec = i
          break
      except KeyError:
        continue
    else:
      print("INFO: No restart action")
      continue
    if int(actions_spec['metadata']['creation_time'])//1000000 in timings:
      timings[int(actions_spec['metadata']['creation_time'])//1000000] += 1
    else:
      timings[int(actions_spec['metadata']['creation_time'])//1000000] = 1
    if int(actions_spec['metadata']['last_update_time'])//1000000 in end_timings:
      end_timings[int(actions_spec['metadata']['last_update_time'])//1000000] += 1
    else:
      end_timings[int(actions_spec['metadata']['last_update_time'])//1000000] = 1
    if actions_spec['status']['state'] in error_list:
      error_list[actions_spec['status']['state']] += 1
    else:
      error_list[actions_spec['status']['state']] = 1
    if 'reason_list' in actions_spec['status']:
      message_list.extend(actions_spec['status']['reason_list'])
    total.append(int(actions_spec['metadata']['last_update_time'])//1000000 - int(actions_spec['metadata']['creation_time'])//1000000)
    c += 1
    if c == count:
      break
print(timings)
print(end_timings)
print(sum(total)/(len(total)))
print("*"*100)
print(error_list)
print("*"*100)
print(message_list)
