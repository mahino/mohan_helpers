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
#BASE_URL = 'https://weeklyst.dev-calm.nutanix.com/'
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

j= 50
count = 2
for i in range(j, j+count): 

  ep_name = 'Ep' + str(i)

  ep_uuid = str(uuid.uuid4())

  cred_uuid = str(uuid.uuid4())

  print(ep_name)
  true = True

  pay =  {"api_version":"3.0","metadata":{"kind":"endpoint","project_reference":{"name":"nucalm","kind":"project","uuid":"bbf474b7-e23f-4b31-9f03-e69c04793adf"},"uuid":ep_uuid},"spec":{"resources":{"type":"Linux","value_type":"IP","attrs":{"credential_definition_list":[{"description":"","username":"root","type":"PASSWORD","name":"endpoint_cred_5fc631f8","cred_class":"static","secret":{"attrs":{"is_secret_modified":true},"value":"nutanix/4u"},"uuid":cred_uuid}],"login_credential_reference":{"name":"endpoint_cred_5fc631f8","kind":"app_credential","uuid":cred_uuid},"values":["10.46.8.91"],"port":22},"tunnel_reference":{"kind":"tunnel","uuid":"db633aa4-2401-e985-8054-beca805eba64"}},"name":ep_name}}

  resp = client.post(URL + 'endpoints', data=json.dumps(pay))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  else:
    print("Created endpoint successfully")
    resp = json.loads(resp.content)
  time.sleep(10)

