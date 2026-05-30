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
URL = f"https://ncm.services.nconprem-10-114-55-128.ccpnx.com/"
NCM_V3 = 'api/nutanix/v3/'

NCM_URL = URL + NCM_V3
DM_URL = NCM_URL.replace('ncm', 'dm')

# NCM_URL = NCM_BASE_URL + V3

# account_update = False
# account_name = 'RPC1'
# account_uuid = '3811789b-02e1-2f4c-89fa-3e2c7d09fb18'

subnet_update = True
subnet_name = 'vlan.117'
subnet_uuid = '5c146a1e-7839-4cf5-84aa-9d9dee7543b5'

cluster_update = True
cluster_1_uuid = '0006525e-4987-690e-6ada-7cc25530e93d'
project_get_again = True

##### delete setup pending projects only
payload = {"entity_type":"project","group_member_attributes":[{"attribute":"name"},{"attribute":"description"},{"attribute":"uuid"},{"attribute":"state"},{"attribute":"vcpus_count"},{"attribute":"memory_bytes"},{"attribute":"storage_bytes"},{"attribute":"vcpus_count_limit"},{"attribute":"memory_bytes_limit"},{"attribute":"storage_bytes_limit"},{"attribute":"user_reference_list"},{"attribute":"user_group_reference_list"},{"attribute":"vms_count"},{"attribute":"network_id_list"},{"attribute":"environment_id_list"},{"attribute":"default_environment_id"},{"attribute":"account_id_list"},{"attribute":"message"},{"attribute":"error"}],"filter_criteria":"","group_member_offset":0,"group_member_count":500,"group_member_sort_order":"ASCENDING","group_member_sort_attribute":"name"}
count = 1
acc_already_pre_count = 0
for i in range(1):
  resp = client.post(DM_URL + 'groups', data=json.dumps(payload))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  respi = json.loads(resp.content)
  for count, pro in enumerate(respi['group_results'][0]['entity_results'][:1]):
    # update_account = True
    # payload = json.dumps({
    #   "length": 250,
    #   "offset": 0,
    #   "filter": "state==VERIFIED;type!=nutanix"
    # })
    # response = requests.request("POST", URL + 'accounts/list', headers=headers, data=payload, verify=False)

    # accounts_list = json.loads(response.content)
    # for account_data in accounts_list['entities']:
    #   for l in range(2):
        print("="*80, f"\nGet project [{pro['data'][0]['values'][0]['values'][0]}]: [{count}]/[{respi['filtered_entity_count']}]")
        if project_get_again:
          s = client.get(NCM_URL + 'projects_internal/' + pro['entity_id'], data=json.dumps({}))
          if s.status_code != 200:
            print("ERROR: faield to get project")
            print("="*80)
            continue
          s = json.loads(s.content)
          del s['status']
        if 'resource_domain' in s['spec']['project_detail']['resources']:
          del s['spec']['project_detail']['resources']['resource_domain']
        update_account = True
        proj_cluster_list = []
        for r in s['spec']['project_detail']['resources']['cluster_reference_list']:
          proj_cluster_list.append(r['uuid'])
        proj_acc_list = []
        for r in s['spec']['project_detail']['resources']['account_reference_list']:
          proj_acc_list.append(r['uuid'])
        acc = ["7109b5f4-0870-21f6-2e77-dfbbac846bb7", "365dd167-c242-2a53-849f-11b39d670321", "fddbc8f6-8020-8542-6239-ef2a35e38a17", "abd23d29-a960-ef13-3ea0-93e1ac39ef2d", "aaf5b06b-2785-a9d5-3502-174308a45043", "0747760e-a682-9d3a-ac06-53779fa175fe", "12a7f0a4-d05b-0db2-e289-9a70b8849d32", "52756948-d881-b054-c3b6-819877b75aa4", "31eebea9-01f5-a990-2bad-ba314d22407c", "a7a2a374-0e58-1c36-2d31-7ac5b855db9b", "771ecfc1-c95e-779d-5ab9-456fa15a6b2e", "c624f3a4-80c2-56c2-ac55-ad65ad27f0f0", "9993166b-4989-efa6-300d-80dd193266a3", "c767fadd-7d38-9c54-8a9e-8880c2601ecf", "35996b0c-f314-8054-18be-4b95387ec0ed", "c7644277-a903-8cc8-92cd-e78aa66fbcaf", "7273678e-4815-a66b-9d3d-90a9680462e0", "40f22e2d-178b-5e5e-ff62-b4a64bf16abb", "f5d20602-8e1d-7c1e-1cde-a2de50446dc9", "530fe7a3-4ef5-3238-683a-b70f63e23a78", "492fa1f9-f8cf-f322-7ecd-dcd89d08737c", "01bb51f4-6037-c581-94ad-e458ceeef2e7", "52fd61d2-7964-52e9-ad00-923d9a177d46", "4a4fbf99-5f74-8402-3318-49a9442f5f71", "b9704c61-a089-8e0f-886d-13ffb083df32"]
        cluster = ["00063ecc-b0d0-9aaf-0700-8c57df20f4fb", "00063ecc-b1e3-835f-0547-e7823f12c680", "00063ecc-b15b-edc0-09e1-b8b0e380d3c0", "00063ecc-b124-e115-0530-2da12ed6ef52", "00063e8e-dc39-5f8c-0ef8-15920b5dfcbc", "00063e8c-06de-a542-0a1c-51119efe9de3", "00063e8c-06de-a542-0a1c-51119efe9de3", "00063e8c-0879-a6af-06c5-258c9eb39dbb", "00063e8c-07f6-fe57-06d1-3a21a8121c69", "00063e8c-08a2-ee9a-0367-29d8c810c154", "00063e8c-06e5-7147-0f46-caabd7bfeaa4", "00063e8c-0809-3887-0b61-02edb4629859", "00063e8c-0969-ed22-068d-0fdd8949cf6d", "00063e8c-07f2-1dad-07cb-25bd600237e9", "00063ecc-b11f-db16-0aea-8ea279b90f43", "00063ecc-b065-dd7d-0300-bbb7b08dbe38", "00063ecc-af43-e0be-0935-ac48ab5be589", "00063ecc-af30-785b-07c7-cb32a4f6770a", "00063ecc-b164-0159-0282-74111e35b1d1", "00063ecc-b19a-1220-08ca-842f1a6d1a11", "00063ef1-2e1c-e92b-0f64-c5b5ef285092", "00063ef1-2e6f-1344-07f4-2472d57ed923", "00063ef1-3a57-a749-064b-1086c8fb24f5", "00063ef1-3acc-466e-0a59-3e878e0ed012", "00063ef1-3793-3dbe-0e32-2897dafc3e93"]
        if update_account:
          project_get_again = True
          # if l == 0:
          up_call = False
          for ac_uuid, cl_uuid in zip(acc, cluster):
            if ac_uuid not in proj_acc_list:
              up_call = True
              s['spec']['project_detail']['resources']['account_reference_list'].append({
                    "kind": "account",
                    "uuid": ac_uuid
                  })
            if cl_uuid not in proj_cluster_list:
              up_call = True
              s['spec']['project_detail']['resources']['cluster_reference_list'].append({
                    "kind": "cluster",
                    "uuid": cl_uuid
                  })
          # else:
          #   s['spec']['project_detail']['resources']['account_reference_list'] = []
          s['spec']['access_control_policy_list'] = []
          # s['metadata']['spec_version'] += 1
          # print(f"INFO: updating project [{pro['data'][0]['values'][0]['values'][0]}] with account [{account_data['metadata']['name']}]. count [{count}]")
          
          if up_call:
            resp = client.put(NCM_URL + 'projects_internal/' + s['metadata']['uuid'], data=json.dumps(s))
            print(resp.content)
            print(f"INFO: update project [{pro['data'][0]['values'][0]['values'][0]}] with account [{ac_uuid}] and cluster [{cl_uuid}] done, count [{count}]")
          else:
            print(f"INFO: account and cluster already present in project [{pro['data'][0]['values'][0]['values'][0]}].")
        # s['spec']['project_detail']['resources']['cluster_reference_list'].append({
        #         "kind": "cluster",
        #         "uuid": cluster_1_uuid
        #       })
        # s['spec']['project_detail']['resources']['external_network_list'].append({
        #         "name": subnet_name,
        #         "uuid": subnet_uuid
        #       },)

        # s['spec']['project_detail']['resources']['cluster_reference_list'].append({
        #         "kind": "cluster",
        #         "uuid": cluster_2_uuid
        #       })
        # if 'access_control_policy_list' not in s['spec']:
        # else:
        #   project_get_again = False
        #   acc_already_pre_count += 1
        #   print(f"INFO: account [{account_data['metadata']['name']} {account_uuid}] already present in project [{pro['data'][0]['values'][0]['values'][0]}]. count [{acc_already_pre_count}]")
    # if False:
    #   update_env = True
    #   if len(s['spec']['project_detail']['resources']['environment_reference_list']):
    #     env_resp = client.get(NCM_URL + 'environments/' + s['spec']['project_detail']['resources']['environment_reference_list'][0]['uuid'])
    #     if env_resp.status_code != 200:
    #       print("ERROR: faield to get environment")
    #       print("="*80)
    #       continue
    #     env_resp = json.loads(env_resp.content)
    #     for r in env_resp['spec']['resources']['infra_inclusion_list'][0]['subnet_references']:
    #       if r['uuid'] == subnet_uuid:
    #         update_env = False
    #         break
    #     del env_resp['status']
    #     if update_env:
    #       env_resp['spec']['resources']['infra_inclusion_list'][0]['subnet_references'].append({
    #               "uuid": subnet_uuid
    #             },)
    #       resp = client.put(NCM_URL + 'environments/' + s['spec']['project_detail']['resources']['environment_reference_list'][0]['uuid'], data=json.dumps(env_resp))
    #       print(resp.content)
    #       print(f"INFO: update project-environment [{env_resp['metadata']['name']}] done, ")
    #     else:
    #       print(f"INFO: subnet already present in environment [{pro['data'][0]['values'][0]['values'][0]}].")
    #   else:
    #     env_not_found.append([pro['data'][0]['values'][0]['values'][0], pro['entity_id']])
    # print(f"INFO: update project [{pro['data'][0]['values'][0]['values'][0]}] done, count [{count}]")
    # count += 1
      
    
    # print("="*80)

