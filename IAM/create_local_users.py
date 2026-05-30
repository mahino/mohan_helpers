


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

URL = f"https://iam.services.nconprem-10-53-55-30.ccpnx.com/api/iam/v4.1.b2/authn/users"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False


user_pay = {"firstName":"test","lastName":"user","username":"testuser","password":"Nutanix.123","status":"ACTIVE","userType":"LOCAL"}

count = 1
for i in range(100):
    user_pay['lastName'] = "user" + str(i)
    user_pay['username'] = "testuser" + str(i)
    resp = client.post(URL, data=json.dumps(user_pay))
    response = json.loads(resp.content)
    if resp.status_code != 201:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Local User [{response['data']['username']}] created sucessfully,")