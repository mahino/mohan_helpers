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
for i in range(total_vpcs, total_vpcs+250):
  #external_subnet_uuid = '997a6916-45a1-4c5e-94d7-eca730fa1e51'
  external_subnet_uuid = '77c1912c-67cb-4a80-84cc-da53e37f6e44'
  pay = {"api_version":"3.1.0","metadata":{"kind":"vpc"},"spec":{"name":"vpcst_","resources":{"external_subnet_list":[{"external_subnet_reference":{"kind":"subnet","uuid":external_subnet_uuid}}]}}}
  pay['spec']['name'] += str(i)
  resp = client.post(URL + 'vpcs', data=json.dumps(pay))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 202:
    print(resp.content, "error in list url")
  else:
    print(f"Created VPC [{pay['spec']['name']}] successfully.")
  resp = json.loads(resp.content)
  vpc_uuid = resp['metadata']['uuid']
  print(f"VPC uuid [{vpc_uuid}]")

  tmp_total_vpcs = total_vpcs
  while total_vpcs > total_vpcs:
    resp = client.post(URL + 'groups', data=json.dumps({"entity_type":"atlas_virtual_network","query_name":"prism:BaseGroupModel"}))
    resp = json.loads(resp.content)
    tmp_total_vpcs = resp['total_entity_count']
    time.sleep(10)
  time.sleep(10) 
  total_vpcs = tmp_total_vpcs
  #subnet 
  pay = {"metadata":{"kind":"subnet"},"spec":{"name":"vpcoverlay","resources":{"ip_config":{"subnet_ip":"10.10.10.0","prefix_length":23,"default_gateway_ip":"10.10.10.1","pool_list":[{"range":"10.10.10.2 10.10.11.250"}]},"subnet_type":"OVERLAY","vpc_reference":{"kind":"vpc","uuid":""}}},"api_version":"3.1.0"}
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
  #print(f"subnet uuid {resp['metadata']['uuid']}")
  resp = json.loads(resp.content)
  pay = {"api_version":"3.1.0","metadata":{"last_update_time":"2022-04-12T11:30:51Z","kind":"vpc_route_table","uuid":"","spec_version":0,"creation_time":"2022-04-12T11:30:51Z","spec_hash":"00000000000000000000000000000000000000000000000000","categories_mapping":{},"categories":{}},"spec":{"resources":{"static_routes_list":[],"default_route_nexthop":{"external_subnet_reference":{"name":"vlan100","kind":"subnet","uuid":external_subnet_uuid}}}}}
  pay['metadata']['uuid'] = resp['metadata']['uuid']
  resp = client.put(URL + 'vpcs/' + vpc_uuid + '/route_tables', data=json.dumps(pay))
  if resp.status_code != 202:
    print("Failed to add 0000 in route_tables")
    print(resp.status_code)
    continue
  resp = json.loads(resp.content)
  time.sleep(10)
  print("All actions are done")

CREATE_VM_TUNNEL = False
if CREATE_VM_TUNNEL:
  
  resp = client.post(URL + 'subnets/list', data=json.dumps({"length":10,"offset":0}))
  resp = json.loads(resp.content)
  for i in resp['entities']:
    pay = {
      "api_version": "3.1.0",
      "metadata": {
        "kind": "network_group_tunnel",
        "uuid": str(uuid.uuid4())
      },
      "spec": {
        "resources": {
          "platform_vpc_uuid_list": [],
          "tunnel_reference": {
            "kind": "tunnel",
            "uuid": str(uuid.uuid4()),
            "name": "NTNX_LOCAL_AZ_" + i['spec']['name'] + "_Tunnel"
          },
          "account_reference": {
            "kind": "account",
            "name": "NTNX_LOCAL_AZ",
            "uuid": "9be58801-7688-4696-9c14-accd045417ed"
          },
          "tunnel_vm_spec": {
            "vm_name": i['spec']['name'] + "_TunnelVM",
            "subnet_uuid":  i['metadata']['uuid'],
            "cluster_uuid": "0005dc4a-d7f6-bd58-0000-00000001c47c"
          }
        },
        "name": i['spec']['name'] + "_NTNX_LOCAL_AZ_ng_d324e"
      }
    }
    sub_resp = client.get(URL + 'subnets/' + i['metadata']['uuid'])
    print(sub_resp.content)
    sub_resp = json.loads(sub_resp.content)
    pay['spec']['resources']['platform_vpc_uuid_list'].append(sub_resp['status']['resources']['vpc_reference']['uuid'])
    print(pay['spec']['resources']['platform_vpc_uuid_list'])
    
    resp = client.post(URL + 'network_groups/tunnels', data=json.dumps(pay))

    time.sleep(40)
