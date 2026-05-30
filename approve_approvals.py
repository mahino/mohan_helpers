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

BASE_URL = f"https://ncm.services.nconprem-10-53-58-35.ccpnx.com/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

list_pay = {"length":75,"offset":0,"filter":"pending_on_me==true"}
approvals_list = client.post(URL + 'approvals/list', data=json.dumps(list_pay))
if approvals_list.status_code != 200:
    print("error in list url")
approvals_list = json.loads(approvals_list.content)
import re

status_to_be_changed = "APPROVED"
count = 0
for approval in approvals_list['entities']:
    approval_uuid = approval['metadata']['uuid']
    approval_set_uuid = approval['status']['resources']['approval_set_list'][0]['uuid']
    approaval_element_uuid = approval['status']['resources']['approval_set_list'][0]['approval_element_list'][0]['uuid']
    
    # Get the current spec_version from the approval metadata
    spec_version = approval['metadata'].get('spec_version', 0)
    
    api_url = URL + f"approvals/{approval_uuid}/approval_sets/{approval_set_uuid}/approval_elements/{approaval_element_uuid}"
    payload = {"comment": "", "state": status_to_be_changed, "spec_version": spec_version}
    
    resp = client.put(api_url, data=json.dumps(payload))
    
    if resp.status_code != 200:
        resp_json = json.loads(resp.content)
        error_msg = resp_json.get('message_list', [{}])[0].get('message', '')
        
        # Check for spec version mismatch and extract expected version
        if 'Spec Version mismatch' in error_msg:
            match = re.search(r"expected:'(\d+)'", error_msg)
            if match:
                expected_version = int(match.group(1))
                print(f"Spec version mismatch for [{approval['metadata']['name']}]. Retrying with version {expected_version}...")
                
                # Retry with correct spec_version
                payload['spec_version'] = expected_version
                resp = client.put(api_url, data=json.dumps(payload))
                
                if resp.status_code == 200:
                    print(f"{status_to_be_changed} [{approval['metadata']['name']}] on retry: {resp.status_code}")
                    count += 1
                    print(f"{status_to_be_changed} [{count}] approvals")
                    time.sleep(1)
                    continue
                else:
                    print(f"Retry failed for [{approval['metadata']['name']}]: {resp.content}, {resp.status_code}")
                    continue
        
        print(f"Error approving approval [{approval['metadata']['name']}]: {resp.content}, {resp.status_code}")
        continue
        
    print(f"{status_to_be_changed} [{approval['metadata']['name']}]: count {count}")
    count += 1
    time.sleep(1)
        