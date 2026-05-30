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

account_data = {}
ntnx_acc_uuid = ''
for account in accounts_list_response['entities']:
  if account['status']['name'] == 'NTNX_LOCAL_AZ':
      ntnx_acc_uuid = account['metadata']['uuid']
      break

base_url = f"https://{sys.argv[1]}:9440/api/calm/v3.0/providers/list"
providers_list_resp = requests.request("POST", base_url, headers=headers, data=json.dumps({}), verify=False)

if providers_list_resp.status_code != 200:
  print(providers_list_resp.content)
  print(providers_list_resp.status_code)
  sys.exit()

providers_list_response = json.loads(providers_list_resp.content)
ndb_provider_uuid = next((i['status']['uuid'] for i in providers_list_response['entities'] if i['status']['name'] == 'NDB'), None)

if ndb_provider_uuid == None:
    print("ERROR: pNDB procider didn't find.")
    sys.exit()

ndb_account_pay = {
    "api_version": "3.0",
    "metadata": {
        "kind": "account",
        "name": "testingDB",
        "uuid": str(uuid.uuid4())
    },
    "spec": {
        "resources": {
            "type": "NDB",
            "parent_reference": {
                "kind": "account",
                "uuid": ntnx_acc_uuid
            },
            "data": {
                "provider_reference": {
                    "kind": "provider",
                    "uuid": ndb_provider_uuid
                },
                "variable_list": [
                    {
                        "name": "ndb__ndb_endpoint",
                        "type": "LOCAL",
                        "value": "10.115.144.249",
                        "is_hidden": False,
                        "is_mandatory": True,
                        "label": "Server IP",
                        "uuid": str(uuid.uuid4())
                    },
                    {
                        "name": "ndb__ndb_username",
                        "type": "LOCAL",
                        "value": "admin",
                        "is_hidden": False,
                        "is_mandatory": True,
                        "label": "Username",
                        "uuid": str(uuid.uuid4())
                    },
                    {
                        "name": "ndb__ndb_password",
                        "type": "SECRET",
                        "value": "Nutanix.123",
                        "is_hidden": False,
                        "is_mandatory": True,
                        "label": "Password",
                        "attrs": {
                            "is_secret_modified": True
                        },
                        "uuid": str(uuid.uuid4())
                    },
                    {
                        "name": "ndb__insecure",
                        "type": "LOCAL",
                        "value": "true",
                        "is_hidden": True,
                        "is_mandatory": False,
                        "label": "",
                        "val_type": "BOOLEAN",
                        "uuid": str(uuid.uuid4())
                    }
                ]
            }
        },
        "name": "testingDB_" + str(random.randint(1,1000000))
    }
}

base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/accounts"
ndb_account_create_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(ndb_account_pay), verify=False)

if ndb_account_create_resp.status_code != 200:
  print(ndb_account_create_resp.content)
  print(ndb_account_create_resp.status_code)
  sys.exit()
ndb_account_create_response = json.loads(ndb_account_create_resp.content)

base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/accounts/{ndb_account_create_response['metadata']['uuid']}/verify"
ndb_account_verify_resp = requests.request("GET", base_url, headers=headers, verify=False)

if ndb_account_verify_resp.status_code != 200:
  print(ndb_account_verify_resp.content)
  print(ndb_account_verify_resp.status_code)
  sys.exit()
ndb_account_verify_response = json.loads(ndb_account_create_resp.content)



base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/accounts/list"
accounts_list_pay = {"filter":f"parent_reference=={ntnx_acc_uuid};provider_reference=={ndb_provider_uuid};(state!=DRAFT;state!=DELETED)","length":10,"offset":0}
accounts_list_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(accounts_list_pay), verify=False)

if accounts_list_resp.status_code != 200:
  print(accounts_list_resp.content)
  print(accounts_list_resp.status_code)
  sys.exit()

accounts_list_response = json.loads(accounts_list_resp.content)

ndb_acc_uuid = accounts_list_response['entities'][0]['metadata']['uuid']

base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/projects/list"
projects_list_pay = {"length": 249}
projects_list_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(projects_list_pay), verify=False)

if projects_list_resp.status_code != 200:
  print(projects_list_resp.content)
  print(projects_list_resp.status_code)
  sys.exit()

projects_list_response = json.loads(projects_list_resp.content)

update_only_first_project = False
for project in projects_list_response['entities']:
    print(f"INFO: Updating project [{project['spec']['name']}]")
    base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/projects_internal/{project['metadata']['uuid']}"
    project_get_resp = requests.request("GET", base_url, headers=headers, verify=False)

    if project_get_resp.status_code != 200:
        print(project_get_resp.content)
        print(project_get_resp.status_code)
        sys.exit()
    project_get_response = json.loads(project_get_resp.content)
    project_update_pay = {
        "metadata" : project_get_response['metadata'],
        "spec": project_get_response['spec'],
        "api_version": "3.1"
    }
    project_update_pay['spec']['project_detail']['resources']['account_reference_list'].append({"kind":"account","uuid":ndb_acc_uuid})
    if len(project_update_pay['spec']['access_control_policy_list']):
        project_update_pay['spec']['access_control_policy_list'][0]['operation'] = 'ADD'
    
    base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/projects_internal/{project['metadata']['uuid']}"
    project_update_resp = requests.request("PUT", base_url, headers=headers, data=json.dumps(project_update_pay), verify=False)

    if project_update_resp.status_code != 202:
        print(project_update_resp.content)
        print(project_update_resp.status_code)
        sys.exit()
    project_update_response = json.loads(project_update_resp.content)
    if update_only_first_project:
        break