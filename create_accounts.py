""" Nucalm environment setup"""


import os
import sys
import json
import uuid
import time
import requests
import urllib3
import random
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = f"https://{sys.argv[1]}:9440/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

account_pay = {
    "api_version": "3.0",
    "metadata": {
        "kind": "account",
        "uuid": "826c2598-faca-c6d9-5375-9ebcd1cebbe9"
    },
    "spec": {
        "name": "RPC7vrefd",
        "resources": {
            "type": "nutanix_pc",
            "data": {
                "server": "10.122.30.125",
                "username": "admin",
                "password": {
                    "value": "Nutanix.123",
                    "attrs": {
                        "is_secret_modified": True
                    }
                }
            },
            "sync_interval_secs": 1200
        }
    }
}


user_acc_count = int(sys.argv[2]) if len(sys.argv) == 3 else 1

count = 1
for i in range(81,100):
    acc_uuid = str(uuid.uuid4())
    account_pay['metadata']['uuid'] = acc_uuid
    account_pay['spec']['name'] = 'RPC' + str(i+1)
    resp = client.post(URL + 'accounts', data=json.dumps(account_pay))
    response = json.loads(resp.content)
    if resp.status_code != 200:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Account [{response['spec']['name']}] created sucessfully, [{count}]")
    time.sleep(2)
    verify_resp = client.get(URL + f"accounts/{acc_uuid}/verify", data=json.dumps(account_pay))
    verify_response = json.loads(verify_resp.content)
    if verify_resp.status_code != 200:
        print(json.dumps(verify_response))
        print(verify_resp.status_code)
        continue
    print(f"Account [{response['spec']['name']}] verified sucessfully, [{count}]")
    time.sleep(2)
    count+=1
    
    
# sync api : https://ncm.pc-10-117-59-93.nutanixqa.com:9440/api/nutanix/v3/accounts/1d4c810e-c817-b252-d139-049d627d6bf7/sync
