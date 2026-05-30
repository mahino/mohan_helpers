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
#client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.auth = HTTPBasicAuth('admin', 'HelloWorld@1234')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3
i=1
count= i+255
for i in range(i, count): 

  subnet_name = 'test_vln_' + str(i)

  #subnet_uuid = 'ed108a2d-0e1d-4603-b510-b5eaecce75d3'
  #subnet_uuid = '3f752906-1464-4913-be0a-d214ae97a4c7'
  subnet_uuid = 'c2e22551-cd4b-42fe-bf0e-753b6432fb05'

  #cluster_uuid = '0005f8a5-5ca5-718c-032a-4a186d44711e'
  #cluster_uuid = '0005f8a5-5ebf-17d0-0452-cb58cd44711e'
  cluster_uuid = '000620e4-a605-c602-4ce2-ac1f6b35f189'

  true = True
  false = False

  pay = {"metadata":{"kind":"subnet"},"spec":{"name":subnet_name,"resources":{"ip_config":{},"subnet_type":"VLAN","vlan_id":i,"is_external":false,"virtual_switch_uuid":subnet_uuid},"cluster_reference":{"kind":"cluster","uuid":cluster_uuid}},"api_version":"3.1.0"}

  resp = client.post(URL + 'subnets', data=json.dumps(pay))
  if resp.status_code != 202:
    print(resp.content, "error in list url")
  else:
    print("Created subnet {0} successfully".format(subnet_name))
    resp = json.loads(resp.content)
  time.sleep(2)

