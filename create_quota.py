#!/usr/bin/env python

import sys
import requests
import time
import uuid
import json
import random
import paramiko
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3 needed for the requests library
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

true=True
false=False
i = 1

if len(sys.argv) < 3:
  print("usage: python create_quota <policy_ip> <no_of_quotas>")
  sys.exit()


resp = client.get('https://{}:9440/api/nutanix/v3/features/policy'.format(sys.argv[1]), auth=('admin', 'Nutanix.123'), verify=False)

policy_vm_ip = json.loads(resp.content)['status']['feature_status']['config']['data']['ip_list'][0]
print(policy_vm_ip)
for i in range(1, int(sys.argv[2])+1):
  client = requests.Session()
  client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
  client.headers = {'content-type': 'application/json'}
  client.verify = False
  quota_uuid = str(uuid.uuid4())
  project_uuid = str(uuid.uuid4())
  pay = {
    "metadata": {
      "kind": "quota",
      "project_reference": {
        "kind": "project",
        "name": "testing_" + str(random.randrange(1, 1000000000001)),
        "uuid": project_uuid
      },
      "uuid": quota_uuid
    },
    "spec": {
      "resources": {
        "data": {
          "disk": 107374182400000,
          "vcpu": 1000,
          "memory": 107374182400000
        },
        "entities": {
          "project": project_uuid
        },
        "metadata": {},
        "uuid": quota_uuid
      }
    }
  }
  resp = client.post('https://{}:9440/api/calm/v3.0/quotas'.format(sys.argv[1]), data=json.dumps(pay))
  pay = {
      "spec": {
          "resources": {
              "entities": {
                  "project": project_uuid
              },
              "state": "enabled"
          }
      }
  }
  resp = client.put('https://{}:9440/api/calm/v3.0/quotas/update/state'.format(sys.argv[1]), data=json.dumps(pay))
  print(f"Quota Created count [{i}]")

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(policy_vm_ip, 22, 'nutanix', 'nutanix/4u')
for i in range(1, int(sys.argv[3])+1):
  meter_uuid = str(uuid.uuid4())
  project_uuid = str(uuid.uuid4())
  task = [{
    "uuid": meter_uuid,
    "entity_type": "VM",
    "resource_type": "disk",
    "value": 1171549184,
    "state": "reserved",
    "tags": {
        "account": "ec1cadbb-e5fb-42fd-8bb7-8e49f3095273",
        "app": "4090a72d-654a-4b59-a114-2243171e97f6",
        "cluster": "0005aecc-16a4-bd62-0000-0000000085f5",
        "project": project_uuid,
        "runlog": "2ddf7773-860d-4a0e-8864-b5f898c5ee8e",
        "substrate_cfg": "d2f3b854-fbce-4559-98fd-86e17c46df1f"
      }
  },{
    "uuid": meter_uuid,
    "entity_type": "VM",
    "resource_type": "vcpu",
    "value": 1,
    "state": "reserved",
    "tags": {
        "account": "ec1cadbb-e5fb-42fd-8bb7-8e49f3095273",
        "app": "4090a72d-654a-4b59-a114-2243171e97f6",
        "cluster": "0005aecc-16a4-bd62-0000-0000000085f5",
        "project": project_uuid,
        "runlog": "2ddf7773-860d-4a0e-8864-b5f898c5ee8e",
        "substrate_cfg": "d2f3b854-fbce-4559-98fd-86e17c46df1f"
      }
  },{
    "uuid": meter_uuid,
    "entity_type": "VM",
    "resource_type": "memory",
    "value": 256058496,
    "state": "reserved",
    "tags": {
        "account": "ec1cadbb-e5fb-42fd-8bb7-8e49f3095273",
        "app": "4090a72d-654a-4b59-a114-2243171e97f6",
        "cluster": "0005aecc-16a4-bd62-0000-0000000085f5",
        "project": project_uuid,
        "runlog": "2ddf7773-860d-4a0e-8864-b5f898c5ee8e",
        "substrate_cfg": "d2f3b854-fbce-4559-98fd-86e17c46df1f"
      }
  }]

  url = f'http://{policy_vm_ip}:4211/reservations'
  print(url, json.dumps(task))
  cmd = f"curl -s -X POST -u 'admin:$Nutanix.123' -H 'Content-Type: application/json' -d '{json.dumps(task)}' --insecure '{url}'"
  stdin, stdout, stderr = ssh_client.exec_command(cmd)
  print(f"MeterData Created count [{i}]")
  output = stdout.read().decode()
  error = stderr.read().decode()

  if output:
      print(output)
  if error:
      print("Command error:")
      print(error)