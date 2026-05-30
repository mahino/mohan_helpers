## Create networks if number is lessthan user requirements
import requests
import sys
import json
import random
import time
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
  'Cookie': 'NTNX_IAM_SESSION=eyJhbGciOiJSUzI1NiIsImtpZCI6IjNkNWRkZTNmMzNjNDc1ZTdiM2E3YjE2ZTI1OWUwNTgwM2U3YzE1MTkifQ.eyJpc3MiOiJodHRwczovLzEwLjM2LjE5OS4yMTo5NDQwL2FwaS9pYW0vYXV0aG4iLCJzdWIiOiJhZG1pbiIsInN1Yl90eXBlIjoibG9jYWwiLCJhdWQiOiJkYzE2ZTgyMy0yZmIxLTViNTktODJlZi0yYmZhODQ0YjlkODgiLCJleHAiOjE3MDA4OTAwMjAsImlhdCI6MTcwMDg4OTEyMCwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJhZG1pbiIsInVzZXJfdXVpZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsImNvbm5lY3Rvcl91dWlkIjoiMzdmMzAxMzUtNDU1Yi01ZWJkLTk5NWYtYjQ3ZTgxN2E1OWYyIiwidGVuYW50Ijp7InV1aWQiOiI1OWQ1ZGU3OC1hOTY0LTU3NDYtOGM2ZS02NzdjNGM3YTc5ZGYiLCJuYW1lIjoiaWFtdjJpbmZyYSJ9LCJsZWdhY3lfcm9sZXMiOlsiUk9MRV9DTFVTVEVSX0FETUlOIiwiUk9MRV9DTFVTVEVSX1ZJRVdFUiIsIlJPTEVfVVNFUl9BRE1JTiJdLCJ1c2VyX3Byb2ZpbGUiOiJ7XCJ1c2VybmFtZVwiOlwiYWRtaW5cIixcImRvbWFpblwiOlwiXCIsXCJsZWdhY3lfYWRtaW5fYXV0aG9yaXRpZXNcIjpbXCJST0xFX0NMVVNURVJfQURNSU5cIixcIlJPTEVfQ0xVU1RFUl9WSUVXRVJcIixcIlJPTEVfVVNFUl9BRE1JTlwiXSxcImF1dGhlbnRpY2F0ZWRcIjp0cnVlLFwidXNlcnR5cGVcIjpcImxvY2FsXCIsXCJhdXRoX2luZm9cIjp7XCJ1c2VybmFtZVwiOlwiYWRtaW5cIixcInVzZXJfdXVpZFwiOlwiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwXCIsXCJ1c2VyX2dyb3VwX3V1aWRzXCI6W10sXCJ0ZW5hbnRfdXVpZFwiOlwiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwXCIsXCJ0b2tlbl9hdWRpZW5jZVwiOlwiXCIsXCJ0b2tlbl9pc3N1ZXJcIjpcIlwiLFwicmVtb3RlX2F1dGhvcml6YXRpb25cIjpcIlwiLFwicmVtb3RlX2F1dGhfanNvblwiOlwiXCJ9fSIsImxlZ2FjeV90ZW5hbnRfaWQiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDAifQ.b7HrrEGiAZcO8Wb6w0oR-fiGi1leUD8Us8EvFmfDSgN8XzVjLSBfLmo7KKH1IKfhv8j1LAhAaokDDA__89k28rQRdu1X0bTdDKQh6xPrW65kHwzJMNDaexk6BluG2mmmRfnDiAlGHyHknEiQMF44AlegwwQuxawKo8B6UW4j9XtzScU162c3IeAGYs_mgh3UK28KELnUKlMexbCFSLZZY-uDKc4pvld_FYRoW_er6RsHAweDZ6lCM9X5bVIvPxvbQuqj31oaFjxZVgI-PwIX1o1gDuwiHDRGoou18g2YjrnmQzBDtMK8rpW-bHElMg0G78VUzkM2D6HNhC_oSrWHHw; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChloZHZtdHN5cGZkanp5aW5yZWNzZnR2YnlmEhljc3huZ2E0Z2JqbWVlbGJ6cTJ1Z2RiajM3; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCki4arBhoHTWVyY3VyeSAAKigzZDVkZGUzZjMzYzQ3NWU3YjNhN2IxNmUyNTllMDU4MDNlN2MxNTE5|PgAHNLseq9x1sam01MPnwqmC93vB/bmZggMmKi+mXQo='
}
network_payload_copy = {
    "spec": {
      "name": "",
      "cluster_reference": {
        "kind": "cluster",
        "uuid": ""
      },
      "resources": {
        "subnet_type": "VLAN",
        "ip_config": {},
        "vlan_id": None
      }
    },
    "metadata": {
      "kind": "subnet"
    },
    "api_version": "3.1.0"
  }

cluster_list_payload = {
                          "length": 250,
                          "offset": 0,
                          "filter": "state==VERIFIED;type!=nutanix"
                        }

base_url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/clusters/list"
clusters_list_resp = requests.request("POST", base_url, headers=headers, data=json.dumps(cluster_list_payload), verify=False)

if clusters_list_resp != 200:
  clusters_list = json.loads(clusters_list_resp.content)['entities']

for cluster in clusters_list:
  if 'nodes' in cluster['status']['resources']:
    host_cluster_uuid = cluster['metadata']['uuid']

rand_val = str(random.randrange(10000, 100000000)) 
for count in range(int(sys.argv[2])):
  network_payload_copy['spec']['name'] = "calm_st_" + rand_val + '_' + str(count)
  network_payload_copy['spec']['resources']['vlan_id'] = count
  network_payload_copy['spec']['cluster_reference']['uuid'] = host_cluster_uuid
  url = f"https://{sys.argv[1]}:9440/api/nutanix/v3/subnets"
  create_subnet_resp = requests.request("POST", url, headers=headers, data=json.dumps(network_payload_copy), verify=False)
  if create_subnet_resp.status_code != 202:
    print(json.loads(create_subnet_resp.content))
    continue
  print(f"subnet [{network_payload_copy['spec']['name']}] created.")
  time.sleep(1)