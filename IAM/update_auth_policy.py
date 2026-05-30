


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
client.headers = {'content-type': 'application/json', 'If-Match': 'YXBwbGljYXRpb24vanNvbg==:711ebb586a8e806fea87cb831576070e', "send-etag": "true"}
client.verify = False

users_list_response = client.get("https://iam.services.nconprem-10-53-55-30.ccpnx.com/api/iam/v4.1.b2/authn/users?$page=0&$limit=100&$filter=userType%20eq%20Iam.Authn.UserType%27LOCAL%27%20and%20status%20eq%20Iam.Authn.UserStatusType%27ACTIVE%27&$orderby=lastUpdatedTime%20desc")
users_list = []
for i in json.loads(users_list_response.content)['data']:
    users_list.append(i['extId'])


user_pay = {
    "entities": [
        {
            "$reserved": {
                "*": {
                    "*": {
                        "eq": "*"
                    }
                }
            }
        }
    ],
    "displayName": "Authorization Policy 1",
    "role": "7946acd5-d725-4af6-bf92-8887e08da29f",
    "identities": [
        {
            "$reserved": {
                "user": {
                    "uuid": {
                        "anyof": users_list
                    }
                }
            }
        }
    ],
    "extId": "7ac3a210-ef63-447d-412a-36ba4df6b04d",
    "description": ""
}

URL = "https://iam.services.nconprem-10-53-55-30.ccpnx.com/api/iam/v4.1.b2/authz/authorization-policies/7ac3a210-ef63-447d-412a-36ba4df6b04d"

count = 1
resp = client.put(URL, data=json.dumps(user_pay))
response = json.loads(resp.content)
if resp.status_code != 200:
    print(json.dumps(response))
    print(resp.status_code)
else:
    print(f"Authorization Policy updated sucessfully,")