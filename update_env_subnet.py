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
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
  'Cookie': 'NTNX_IAM_SESSION=CgVhZG1pbhD08pm/BhoHTWVyY3VyeSAAKigxMDcyNzZiMGQ0ZTA3Y2QyOGIxZTE5M2I4ZWQ0NmZkNmE1YWUyNmQ2|ECLqpL/1A3VtcK1NPo8yHsrnzg1ZNTSUjX0H4qqvpL4=; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChlvNW12YXpydmx2a2R3bjM2ZXFqYXBya214EhlxdjJnMnk0NnR4bXlyMml5cHA0ZHVxcXlu; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhD08pm/BhoHTWVyY3VyeSAAKigxMDcyNzZiMGQ0ZTA3Y2QyOGIxZTE5M2I4ZWQ0NmZkNmE1YWUyNmQ2|ECLqpL/1A3VtcK1NPo8yHsrnzg1ZNTSUjX0H4qqvpL4='
}

# BASE_URL = f"https://{sys.argv[1]}:9440/"
# NCM_BASE_URL = f"https://{sys.argv[2]}:9440/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False
BASE_URL = f"https://{sys.argv[1]}:9440/"

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3 + 'environments'
subnet_uuid = '1b690e27-d868-49a9-819e-9aa505fb32aa'
# NCM_URL = NCM_BASE_URL + V3

##### delete setup pending projects only
payload = {"length":250,"offset":250,"filter":""}
count = 1
acc_already_pre_count = 0
for i in range(1):
  resp = client.post(URL + '/list', data=json.dumps(payload))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  for env in resp['entities']:
    evn_uuid = env['metadata']['uuid']
    print(evn_uuid)
    response = client.get(URL + '/' + evn_uuid)
    if response.status_code != 200:
      print(response.content, "error in get url")
    response = json.loads(response.content)
    del response['status']
    for r in response['spec']['resources']['infra_inclusion_list'][0]['subnet_references']:
      if r['uuid'] == subnet_uuid:
        print(f"INFO: subnet already present in environment [{response['spec']['name']}].")
        break
    else:
        print(f"INFO: adding subnet to environment [{response['spec']['name']}].")
        response['spec']['resources']['infra_inclusion_list'][0]['subnet_references'].append({'uuid': subnet_uuid})
        respi = client.put(URL + '/' + evn_uuid, data=json.dumps(response))
        print(respi.content)

