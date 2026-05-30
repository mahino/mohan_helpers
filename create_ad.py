""" Nucalm environment setup"""

import os
import sys
import json
import uuid
import time
import requests
import subprocess
import urllib3
from requests.auth import HTTPBasicAuth
sys.path.insert(1, '../locustfiles')
from test_features import TestFeatures
from config_generator import generate_payload_for_create_quota, \
  generate_payload_for_quota_enable
from helpers import id_generator

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://{}:9440/'.format(sys.argv[1])
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3
CALM_URL = BASE_URL + 'api/calm/v3.0/'


# Directory Service
print("Adding Directiry service")
directory_service_pay={"name":"ST_AUTO_PC_AD","domain":"systest.nutanix.com","directoryUrl":"ldap://10.46.1.152:389","groupSearchType":"RECURSIVE","directoryType":"ACTIVE_DIRECTORY","connectionType":"LDAP","serviceAccountUsername":"Administrator@systest.nutanix.com","serviceAccountPassword":"Nutanix/4u"}
s = client.post(BASE_URL + 'PrismGateway/services/rest/v1/authconfig/directories', data=json.dumps(directory_service_pay))
print(s.content)

time.sleep(5)

# Role Mapping
print("Role mapping")
role_mapping_pay={"directoryName":"ST_AUTO_PC_AD","role":"ROLE_CLUSTER_ADMIN","entityType":"USER","entityValues":["st-sspadmin"]}
s = client.post(BASE_URL + 'PrismGateway/services/rest/v1/authconfig/directories/ST_AUTO_PC_AD/role_mappings?&entityType=USER&role=ROLE_CLUSTER_ADMIN', data=json.dumps(role_mapping_pay))
print(s.content)

time.sleep(5)

# User Role
print("User role")
user_role_pay={"profile":{"username":"st-sspadmin","firstName":"st-ssp","lastName":"admin","emailId":"st-sspadmin@systest.nutanix.com","password":"nutanix/4u","locale":"en-US"},"mode":"Create","enabled":False,"roles":[]}
client.get(BASE_URL + 'PrismGateway/services/rest/v1/users', data=json.dumps(user_role_pay))

add_user_role_pay=["ROLE_USER_ADMIN","ROLE_MULTICLUSTER_ADMIN"]
s = client.put(BASE_URL + 'PrismGateway/services/rest/v1/users/st-sspadmin/roles', data=json.dumps(add_user_role_pay))
print(s.content)
