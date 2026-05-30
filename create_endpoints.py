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

BASE_URL = f"https://{sys.argv[1]}:9440/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

ep_pay = {
    "api_version": "3.0",
    "metadata": {
        "kind": "endpoint",
        "project_reference": {
            "name": "vpc",
            "kind": "project",
            "uuid": "3d00e185-ba99-4a63-a7b8-9d3f290a1762"
        },
        "uuid": "69651c7d-e423-48e0-8e86-c4df2307076a"
    },
    "spec": {
        "resources": {
            "type": "Linux",
            "value_type": "IP",
            "attrs": {
                "credential_definition_list": [
                    {
                        "description": "",
                        "username": "root",
                        "type": "PASSWORD",
                        "name": "endpoint_cred_46b42821",
                        "cred_class": "static",
                        "secret": {
                            "attrs": {
                                "is_secret_modified": True
                            },
                            "value": "nutanix/4u"
                        },
                        "uuid": "43118085-64ee-37e4-721c-4157cdf35e93"
                    }
                ],
                "login_credential_reference": {
                    "name": "endpoint_cred_46b42821",
                    "kind": "app_credential",
                    "uuid": "43118085-64ee-37e4-721c-4157cdf35e93"
                },
                "values": [
                    "10.10.10.8"
                ],
                "port": 22
            },
            "tunnel_reference": {
                "kind": "tunnel",
                "uuid": "8c25fde0-f767-f773-d35a-7acead461445"
            }
        },
        "name": "10_10_10_8"
    }
}

count = 1
vms = ["10.10.10.102", "10.10.10.103", "10.10.10.107", "10.10.10.109", "10.10.10.110", "10.10.10.111", "10.10.10.113", "10.10.10.114", "10.10.10.116", "10.10.10.12", "10.10.10.120", "10.10.10.125", "10.10.10.130", "10.10.10.131", "10.10.10.132", "10.10.10.133", "10.10.10.134", "10.10.10.137", "10.10.10.138", "10.10.10.139", "10.10.10.14", "10.10.10.143", "10.10.10.144", "10.10.10.150", "10.10.10.151", "10.10.10.153", "10.10.10.156", "10.10.10.158", "10.10.10.159", "10.10.10.16", "10.10.10.161", "10.10.10.163", "10.10.10.165", "10.10.10.167", "10.10.10.169", "10.10.10.17", "10.10.10.175", "10.10.10.178", "10.10.10.18", "10.10.10.180", "10.10.10.184", "10.10.10.185", "10.10.10.187", "10.10.10.19", "10.10.10.191", "10.10.10.198", "10.10.10.20", "10.10.10.202", "10.10.10.204", "10.10.10.208", "10.10.10.21", "10.10.10.210", "10.10.10.214", "10.10.10.216", "10.10.10.221", "10.10.10.222", "10.10.10.223", "10.10.10.225", "10.10.10.226", "10.10.10.229", "10.10.10.231", "10.10.10.232", "10.10.10.234", "10.10.10.238", "10.10.10.239", "10.10.10.242", "10.10.10.243", "10.10.10.246", "10.10.10.247", "10.10.10.25", "10.10.10.30", "10.10.10.32", "10.10.10.35", "10.10.10.41", "10.10.10.42", "10.10.10.43", "10.10.10.47", "10.10.10.48", "10.10.10.49", "10.10.10.5", "10.10.10.51", "10.10.10.56", "10.10.10.60", "10.10.10.62", "10.10.10.65", "10.10.10.67", "10.10.10.68", "10.10.10.70", "10.10.10.72", "10.10.10.73", "10.10.10.74", "10.10.10.75", "10.10.10.76", "10.10.10.8", "10.10.10.82", "10.10.10.87", "10.10.10.88", "10.10.10.91", "10.10.10.93", "10.10.10.95"]
for vm_ip in vms:
    cred_uuid = str(uuid.uuid4())
    ep_pay['spec']['resources']['attrs']['credential_definition_list'][0]['uuid'] = cred_uuid
    ep_pay['spec']['resources']['attrs']['login_credential_reference']['uuid'] = cred_uuid
    ep_pay['metadata']['uuid'] = str(uuid.uuid4())
    ep_pay['spec']['resources']['attrs']['values'] = [vm_ip]
    ep_pay['spec']['name'] = "vpc_ep_" + vm_ip.replace('.', '_')
    resp = client.post(URL + 'endpoints', data=json.dumps(ep_pay))
    response = json.loads(resp.content)
    if resp.status_code != 200:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Endpoint [{response['spec']['name']}] created sucessfully, [{count}]")
    count += 1
    time.sleep(2)