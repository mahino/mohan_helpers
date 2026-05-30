""" Nucalm environment setup"""

import os
import sys
import json
import uuid
import time
import commands
import requests
import urllib3
from requests.auth import HTTPBasicAuth
sys.path.insert(1, '../locustfiles')
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
print("Waiting for 2 min")

# Add accounts
#if 'ADD_ACCOUNTS' in os.environ and json.loads(os.environ['ADD_ACCOUNTS']):

#commands.getstatusoutput("sshpass -p nutanix/4u ssh nutanix@10.36.0.32 'hostname -I'")
if True:
  print("POP")
  accounts = ['aws', 'azure', 'gcp', 'vmware']
  #accounts = []
  #if 'REMOTE_PC' in os.environ and json.loads(os.environ['REMOTE_PC']):
  if False:
    #rpc_ip_list = os.environ['REMOTE_PC_IP'].split()
    rpc_ip_list = ["10.36.0.28", "10.36.0.60", "10.36.0.27", "10.36.0.41", "10.36.0.32", "10.36.0.19", "10.36.0.4", "10.36.0.2", "10.36.0.11", "10.36.0.14", "10.36.0.55", "10.36.0.16", "10.36.0.24", "10.36.0.6", "10.36.0.22", "10.36.0.46"]
    for _ in range(len(rpc_ip_list)):
      accounts.append('nutanix')

  RPC_COUNT = 0
  for account in accounts:
    account_uuid = str(uuid.uuid4())
    spec_file = open('../config/' + account + '_create_account.json')
    data = json.load(spec_file)
    data['metadata']['uuid'] = account_uuid
    if account == 'nutanix':
      u="sshpass -p nutanix/4u ssh nutanix@{} 'hostname -I'".format(sys.argv[1])
      o=commands.getstatusoutput("sshpass -p nutanix/4u ssh nutanix@{} 'hostname -I'".format(sys.argv[1]))
      if rpc_ip_list[RPC_COUNT] in o[1]:
        RPC_COUNT += 1
        continue
      data['spec']['name'] = 'RPC_' + str(RPC_COUNT) + str(id_generator(8))
      pc_ip = data['spec']['resources']['data']['server'].replace('pc_ip', rpc_ip_list[RPC_COUNT])
      data['spec']['resources']['data']['server'] = pc_ip
      RPC_COUNT += 1
    print("creating account [{}]".format(account))
    response = client.post(URL + 'accounts', data=json.dumps(data))
    if response.status_code != 200:
      print(response.content)
      continue
    response = json.loads(response.content)
    print("Verifying account [{}]".format(response['spec']['name']))
    response = client.get(URL + 'accounts/' + account_uuid + '/verify', data=json.dumps(data))
    if response.status_code != 200:
      print(response.content)

  #if 'MULTI_VMWARE_ACCOUNTS' in os.environ and json.loads(os.environ['MULTI_VMWARE_ACCOUNTS']):
  e=0
  print("LOL")
  if True:
    payload = {"length":250,"offset":0,"filter":"state!=DELETED;type==vmware"}
    response = client.post(URL + 'accounts/list', data=json.dumps(payload))
    if response.status_code != 200:
      print(response.content)
    response = json.loads(response.content)
    vmware_uuid = next((acc['metadata']['uuid'] for acc in response['entities'] if acc['metadata']['name'] == 'vmware_account'), '')
    pay = {"filter":"account_uuid==" + vmware_uuid}
    resp = client.post(URL + 'vmware/v6/datacenter/list', data=json.dumps(pay))
    if resp.status_code != 200:
      print(resp.content)
    resp = json.loads(resp.content)
    spec_file = open('../config/vmware_create_account.json')
    data = json.load(spec_file)
    r = 0
    all_acc = []
    for DC in resp['entities']:
      dc = DC['status']['resources']['name']
      #all_acc.append(DC['status']['resources']['name'])
      #continue
      if dc == 'Auto_systest_calm_vcenter-DC':
        continue
      acc_uuid = str(uuid.uuid4())
      acc_name = 'vmware_account_' + dc.replace('.', '_').replace('-', '_')
      data['metadata']['uuid'] = acc_uuid
      data['spec']['name'] = acc_name[:65]
      data['spec']['resources']['data']['datacenter'] = dc
      for i in range(2):
        print("creating account [{}]".format(acc_name))
        response = client.post(URL + 'accounts', data=json.dumps(data))
        try:
          if len(json.loads(response.content)['message_list']):
            print('ERROR: getting error with name ' + acc_name)
            print(json.loads(response.content)['message_list'])
            data['spec']['name'] = acc_name[:55] + '_' + id_generator(8)
            client.delete(URL + 'accounts/' + acc_uuid, data=json.dumps({}))
            acc_uuid = str(uuid.uuid4())
            data['metadata']['uuid'] = acc_uuid
            continue

        except KeyError:
          break

      if response.status_code != 200:
        print(response.content)
        continue
        
      response = json.loads(response.content)
      print("Verifying account [{}]".format(response['spec']['name']))
      response = client.get(URL + 'accounts/' + acc_uuid + '/verify', data=json.dumps(data))
      if response.status_code != 200:
        print(response.content)
      r += 1
      if r > 100:
        break

  print(all_acc)
  #if 'ENABLE_QUOTA' in os.environ:
  print("QUOTA")
  if True:
    # enable default quota
    quota_pay = {"metadata":{"kind":"quota"},"spec":{"resources":{"entities":{},"state":"enabled"}}}
    resp = client.put(CALM_URL + 'quotas/update/state', data=json.dumps(quota_pay))
    if resp.status_code != 200:
      print('ERROR: failed to update default quota')
      print(resp.content)
    else:
      create_quota_pay = generate_payload_for_create_quota(self='')
      resp = client.post(CALM_URL + 'quotas', data=json.dumps(create_quota_pay))
      if resp.status_code != 200:
        print('ERROR: unable to create default quota')
        print(resp.content)    
    
    # enable quota at account level
    response = client.post(URL + 'accounts/list', data=json.dumps({"length":250,"offset":0,"filter":"state==VERIFIED;type==nutanix_pc|vmware"}))
    if response.status_code != 200:
      print(response.content)
    else:
      for acc in json.loads(response.content)['entities']:
        print(acc['status']['name'])
        acc_data = client.get(URL + 'accounts/'+acc['metadata']['uuid'])
        if acc_data.status_code != 200:
          print(acc_data.content)
          continue
        acc_data = json.loads(acc_data.content)
        if acc_data['spec']['resources']['type'] == 'vmware':
          account_data_resp = client.post(URL + 'vmware/v6/cluster/list', data=json.dumps({"filter":"account_uuid==" + acc['metadata']['uuid']}))
          account_data = json.loads(account_data_resp.content)
          if account_data_resp.status_code!= 200:
            print(account_data)
            continue
          else:
            try:
              cluster = account_data['entities'][0]['status']['resources']['name']
            except IndexError:
              print("Failed to get cluster details for account [{}]".format(acc['status']['name']))
              continue
        elif acc_data['spec']['resources']['type'] == 'nutanix_pc':
          cluster = acc_data['status']['resources']['data'] \
                    ['cluster_account_reference_list'][0] \
                    ['resources']['data']['cluster_uuid']
        else:
          continue

        quota_pay = generate_payload_for_quota_enable(account_uuid=acc['metadata']['uuid'])
        quota_pay['metadata'] = {'kind': 'quota'}
        print(json.dumps(quota_pay))
        resp = client.put(CALM_URL + 'quotas/update/state', data=json.dumps(quota_pay))
        if resp.status_code != 200:
          print('ERROR: failed to update quota at cluster level [{}]'.format(acc_data['status']['name']))
          print(resp.content)
        else:
          create_quota_pay = generate_payload_for_create_quota(self='', account_uuid=acc['metadata']['uuid'],
                                                               cluster=cluster)
          print(json.dumps(create_quota_pay))
          resp = client.post(CALM_URL + 'quotas', data=json.dumps(create_quota_pay))
          if resp.status_code != 200:
            print('ERROR: unable to create quota for account [{}]'.format(acc_data['status']['name']))
            print(resp.content)
