import requests
import sys
import json
import random
import time
import uuid
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
  'Cookie': 'NTNX_IAM_SESSION=eyJhbGciOiJSUzI1NiIsImtpZCI6IjNkNWRkZTNmMzNjNDc1ZTdiM2E3YjE2ZTI1OWUwNTgwM2U3YzE1MTkifQ.eyJpc3MiOiJodHRwczovLzEwLjM2LjE5OS4yMTo5NDQwL2FwaS9pYW0vYXV0aG4iLCJzdWIiOiJhZG1pbiIsInN1Yl90eXBlIjoibG9jYWwiLCJhdWQiOiJkYzE2ZTgyMy0yZmIxLTViNTktODJlZi0yYmZhODQ0YjlkODgiLCJleHAiOjE3MDA4OTAwMjAsImlhdCI6MTcwMDg4OTEyMCwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJhZG1pbiIsInVzZXJfdXVpZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsImNvbm5lY3Rvcl91dWlkIjoiMzdmMzAxMzUtNDU1Yi01ZWJkLTk5NWYtYjQ3ZTgxN2E1OWYyIiwidGVuYW50Ijp7InV1aWQiOiI1OWQ1ZGU3OC1hOTY0LTU3NDYtOGM2ZS02NzdjNGM3YTc5ZGYiLCJuYW1lIjoiaWFtdjJpbmZyYSJ9LCJsZWdhY3lfcm9sZXMiOlsiUk9MRV9DTFVTVEVSX0FETUlOIiwiUk9MRV9DTFVTVEVSX1ZJRVdFUiIsIlJPTEVfVVNFUl9BRE1JTiJdLCJ1c2VyX3Byb2ZpbGUiOiJ7XCJ1c2VybmFtZVwiOlwiYWRtaW5cIixcImRvbWFpblwiOlwiXCIsXCJsZWdhY3lfYWRtaW5fYXV0aG9yaXRpZXNcIjpbXCJST0xFX0NMVVNURVJfQURNSU5cIixcIlJPTEVfQ0xVU1RFUl9WSUVXRVJcIixcIlJPTEVfVVNFUl9BRE1JTlwiXSxcImF1dGhlbnRpY2F0ZWRcIjp0cnVlLFwidXNlcnR5cGVcIjpcImxvY2FsXCIsXCJhdXRoX2luZm9cIjp7XCJ1c2VybmFtZVwiOlwiYWRtaW5cIixcInVzZXJfdXVpZFwiOlwiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwXCIsXCJ1c2VyX2dyb3VwX3V1aWRzXCI6W10sXCJ0ZW5hbnRfdXVpZFwiOlwiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwXCIsXCJ0b2tlbl9hdWRpZW5jZVwiOlwiXCIsXCJ0b2tlbl9pc3N1ZXJcIjpcIlwiLFwicmVtb3RlX2F1dGhvcml6YXRpb25cIjpcIlwiLFwicmVtb3RlX2F1dGhfanNvblwiOlwiXCJ9fSIsImxlZ2FjeV90ZW5hbnRfaWQiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDAifQ.b7HrrEGiAZcO8Wb6w0oR-fiGi1leUD8Us8EvFmfDSgN8XzVjLSBfLmo7KKH1IKfhv8j1LAhAaokDDA__89k28rQRdu1X0bTdDKQh6xPrW65kHwzJMNDaexk6BluG2mmmRfnDiAlGHyHknEiQMF44AlegwwQuxawKo8B6UW4j9XtzScU162c3IeAGYs_mgh3UK28KELnUKlMexbCFSLZZY-uDKc4pvld_FYRoW_er6RsHAweDZ6lCM9X5bVIvPxvbQuqj31oaFjxZVgI-PwIX1o1gDuwiHDRGoou18g2YjrnmQzBDtMK8rpW-bHElMg0G78VUzkM2D6HNhC_oSrWHHw; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChloZHZtdHN5cGZkanp5aW5yZWNzZnR2YnlmEhljc3huZ2E0Z2JqbWVlbGJ6cTJ1Z2RiajM3; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCki4arBhoHTWVyY3VyeSAAKigzZDVkZGUzZjMzYzQ3NWU3YjNhN2IxNmUyNTllMDU4MDNlN2MxNTE5|PgAHNLseq9x1sam01MPnwqmC93vB/bmZggMmKi+mXQo='
}
accounts_list_pay = {"length":20,"offset":0,"filter":"state!=DELETED;(type!=nutanix;type!=custom_provider)"}


base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/accounts/list"
accounts_list_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(accounts_list_pay), verify=False)

if accounts_list_resp.status_code != 200:
  print(accounts_list_resp.content)
  print(accounts_list_resp.status_code)
  sys.exit()

accounts_list_response = json.loads(accounts_list_resp.content)

ntnx_acc_uuid = ''
cluster_uuid = ''
for account in accounts_list_response['entities']:
  if account['status']['name'] == 'NTNX_LOCAL_AZ':
      ntnx_acc_uuid = account['metadata']['uuid']
      cluster_uuid = account['status']['resources']['data']['cluster_account_reference_list'][0]['resources']['data']['cluster_uuid']
      break

vpc_list_pay = {
    "length": 1000,
    "offset": 0,
    "filter": f"account_uuid=={ntnx_acc_uuid}"
}

for ov, vp in [  ["ST_OVERLAY_16", "ST_VPC_16"], ["ST_OVERLAY_17", "ST_VPC_17"], ["ST_OVERLAY_18", "ST_VPC_18"], ["ST_OVERLAY_19", "ST_VPC_19"], ["ST_OVERLAY_20", "ST_VPC_20"]]:
  base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/nutanix/v1/vpcs/list"
  vpc_list_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(vpc_list_pay), verify=False)

  print(vpc_list_resp)

  if vpc_list_resp.status_code != 200:
    print(vpc_list_resp.content)
    print(vpc_list_resp.status_code)
    sys.exit()

  vpc_list_response = json.loads(vpc_list_resp.content)
  vpc_uuid = next((i['metadata']['uuid'] for i in vpc_list_response['entities'] if i['status']['name'] == vp), None)

  subnet_groups_pay = {
      "entity_type": "virtual_network",
      "group_member_attributes": [
          {
              "attribute": "name"
          }
      ],
      "filter_criteria": f"account_uuid=={ntnx_acc_uuid}",
      "group_member_offset": 0,
      "group_member_count": 100
  }
  base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/nutanix/v1/groups/list"
  subnet_groups_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(subnet_groups_pay), verify=False)

  if subnet_groups_resp.status_code != 200:
    print(subnet_groups_resp.content)
    print(subnet_groups_resp.status_code)
    sys.exit()

  subnet_groups_response = json.loads(subnet_groups_resp.content)
  overlay_uuid = ''
  for i in subnet_groups_response['group_results'][0]['entity_results']:
      if i['data'][0]['values'][0]['values'][0] == ov:
          overlay_uuid = i['entity_id']

  rand_str = str(random.randint(10030, 99999))
  create_VPC_tunnel_pay = {
    "api_version": "3.1.0",
    "metadata": {
      "kind": "network_group_tunnel",
      "uuid": str(uuid.uuid4())
    },
    "spec": {
      "resources": {
        "platform_vpc_uuid_list": [
          vpc_uuid
        ],
        "tunnel_reference": {
          "kind": "tunnel",
          "uuid": str(uuid.uuid4()),
          "name": "NTNX_LOCAL_AZ_" + vp + "_Tunnel"
        },
        "account_reference": {
          "kind": "account",
          "name": "NTNX_LOCAL_AZ",
          "uuid": ntnx_acc_uuid
        },
        "tunnel_vm_spec": {
          "vm_name": vp + "_TunnelVM",
          "subnet_uuid": overlay_uuid,
          "cluster_uuid": cluster_uuid
        }
      },
      "name": vp + "_NTNX_LOCAL_AZ_ng_" + rand_str
    }
  }

  base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/network_groups/tunnels"
  print(create_VPC_tunnel_pay)
  create_VPC_tunnel_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(create_VPC_tunnel_pay), verify=False)

  if create_VPC_tunnel_resp.status_code != 200:
    print(create_VPC_tunnel_resp.content)
    print(create_VPC_tunnel_resp.status_code)
    sys.exit()

  create_VPC_tunnel_response = json.loads(create_VPC_tunnel_resp.content)
  print(json.dumps(create_VPC_tunnel_response))
  time.sleep(30)