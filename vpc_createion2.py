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

#VERIFY_FAILED
#DRAFT
timings = {}
total = []
#https://10.36.0.44:9440/api/nutanix/v3/vpcs
starting = 0
resp = client.post(URL + 'groups', data=json.dumps({"entity_type":"atlas_virtual_network","query_name":"prism:BaseGroupModel"}))
resp = json.loads(resp.content)
total_vpcs = resp['total_entity_count']
for i in range(total_vpcs, total_vpcs+5):
  pay = {"api_version":"3.1.0","metadata":{"kind":"vpc"},"spec":{"name":"vpcst_","resources":{"external_subnet_list":[{"external_subnet_reference":{"kind":"subnet","uuid":"56f8af62-790a-4dfe-b4eb-736043d9d0ef"}}]}}}
  pay['spec']['name'] += str(i)
  resp = client.post(URL + 'vpcs', data=json.dumps(pay))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 202:
    print(resp.content, "error in list url")
  else:
    print(f"Created VPC [{pay['spec']['name']}] successfully.")
  resp = json.loads(resp.content)
  vpc_uuid = resp['metadata']['uuid']

  tmp_total_vpcs = total_vpcs
  while total_vpcs > total_vpcs:
    resp = client.post(URL + 'groups', data=json.dumps({"entity_type":"atlas_virtual_network","query_name":"prism:BaseGroupModel"}))
    resp = json.loads(resp.content)
    tmp_total_vpcs = resp['total_entity_count']
    time.sleep(30) 
  total_vpcs = tmp_total_vpcs
  #subnet 
  pay = {"metadata":{"kind":"subnet"},"spec":{"name":"vsoverlay","resources":{"ip_config":{"subnet_ip":"10.10.10.0","prefix_length":23,"default_gateway_ip":"10.10.10.1","pool_list":[{"range":"10.10.10.2 10.10.11.250"}]},"subnet_type":"OVERLAY","vpc_reference":{"kind":"vpc","uuid":"e8b0aa3f-60b1-49a1-9f9d-7c7a44a41a10"}}},"api_version":"3.1.0"}
  pay['spec']['resources']['vpc_reference']['uuid'] = vpc_uuid
  pay['spec']['name'] += '_' + resp['spec']['name']
  resp = client.post(URL + 'subnets', data=json.dumps(pay))
  if resp.status_code != 202:
    print(resp.content, "error in list url")
  else:
    print(f"Created subnet {pay['spec']['name']} successfully.")
  

  resp = client.post(URL + 'subnets/list', data=json.dumps({}))
  resp = json.loads(resp.content)
  total_subnets = resp['metadata']['total_matches']

  tmp_total_subnets = total_subnets
  while total_vpcs > total_vpcs:
    resp = client.post(URL + 'subnets/list', data=json.dumps({}))
    resp = json.loads(resp.content)
    tmp_total_vpcs = resp['metadata']['total_matches']
    time.sleep(20)
  total_subnets = tmp_total_vpcs

  #route_table
  resp = client.get(URL + 'vpcs/' + vpc_uuid + '/route_tables')
  if resp.status_code != 200:
    print("Failed to fetch route_tables")
    continue
  resp = json.loads(resp.content)
  pay = {"api_version":"3.1.0","metadata":{"last_update_time":"2022-04-12T11:30:51Z","kind":"vpc_route_table","uuid":"560c5afd-2297-b675-7c7d-ffcd309d4100","spec_version":0,"creation_time":"2022-04-12T11:30:51Z","spec_hash":"00000000000000000000000000000000000000000000000000","categories_mapping":{},"categories":{}},"spec":{"resources":{"static_routes_list":[],"default_route_nexthop":{"external_subnet_reference":{"name":"vlan100","kind":"subnet","uuid":"56f8af62-790a-4dfe-b4eb-736043d9d0ef"}}}}}
  pay['metadata']['uuid'] = resp['metadata']['uuid']
  resp = client.put(URL + 'vpcs/' + vpc_uuid + '/route_tables', data=json.dumps(pay))
  if resp.status_code != 202:
    print("Failed to add 0000 in route_tables")
    print(resp.status_code)
    continue
  resp = json.loads(resp.content)
  time.sleep(20)
  print("All actions are done")
