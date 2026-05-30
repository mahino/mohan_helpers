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

from random import randint

def generate_random_ip():
    return '.'.join(
        str(randint(0, 255)) for _ in range(4)
    )

i=1
count= i+300
for i in range(i, count): 

  acc_name = 'ST_Test_NDB_' + str(i)

  subnet_uuid = 'edd9181e-38d0-41ca-82b9-50ee00841e69'

  cluster_uuid = '0005dc02-861b-4485-0000-00000002a955'

  acc_uuid = str(uuid.uuid4())
  
  random_ip = generate_random_ip()  

  

  true = True
  false = False


  pay = {"api_version":"3.0","metadata":{"kind":"account","name":acc_name,"uuid":acc_uuid},"spec":{"resources":{"type":"NDB","parent_reference":{"kind":"account","uuid":"ebe2fd5a-6c1a-4735-ba5f-290005f3394e"},"data":{"provider_reference":{"kind":"provider","uuid":"70b9d796-cff6-4351-bd21-34b770537a38"},"variable_list":[{"name":"ndb__ndb_endpoint","type":"LOCAL","value":random_ip,"is_hidden":false,"is_mandatory":true,"label":"Server IP","uuid":str(uuid.uuid4())},{"name":"ndb__ndb_username","type":"LOCAL","value":"admin","is_hidden":false,"is_mandatory":true,"label":"Username","uuid":str(uuid.uuid4())},{"name":"ndb__ndb_password","type":"SECRET","value":"Nutanix.123","is_hidden":false,"is_mandatory":true,"label":"Password","attrs":{"is_secret_modified":true},"uuid":str(uuid.uuid4())},{"name":"ndb__insecure","type":"LOCAL","value":"true","is_hidden":true,"is_mandatory":false,"label":"","val_type":"BOOLEAN","uuid":str(uuid.uuid4())}]}},"name":acc_name}}



  resp = client.post(URL + 'accounts', data=json.dumps(pay))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  else:
    print("Created NDB accounts {0} successfully".format(acc_name))
    resp = json.loads(resp.content)
  time.sleep(5)

