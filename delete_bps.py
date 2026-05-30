"""

Pass the project uuid for which you want to delete the associated BPs

"""

import os
import sys
import json
import uuid
import time
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://ncm.services.nconprem-10-114-55-128.ccpnx.com/'
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False
false = False
V3 = 'api/nutanix/v3/'
URL = BASE_URL + V3

project_uuid = ''

s = 0
offset = 0
# resp = client.post(URL + 'blueprints/list', data=json.dumps({"length":250,"offset":s*offset,"filter": 'state==DRAFT'}))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
groups_pay  = {
    "entity_type": "nucalm_app_blueprint",
    "group_member_attributes": [
        {
            "attribute": "name"
        },
        {
            "attribute": "description"
        },
        {
            "attribute": "categories"
        },
        {
            "attribute": "app_count"
        },
        {
            "attribute": "project_name"
        },
        {
            "attribute": "state"
        },
        {
            "attribute": "_created_timestamp_usecs_"
        },
        {
            "attribute": "_modified_timestamp_usecs_"
        }
    ],
    "filter_criteria": "state!=DELETED;cloned!=true",
    "group_member_offset": -50,
    "group_member_count": 50,
    "group_member_sort_order": "DESCENDING",
    "group_member_sort_attribute": "_created_timestamp_usecs_"
}

c = 1
for m in range(20):
    groups_pay['group_member_offset'] += 20
    resp = client.post(URL + 'groups', data=json.dumps(groups_pay))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
    if resp.status_code != 200:
        print(resp.content, "error in list url")
    s = json.loads(resp.content)
    for i in s['group_results'][0]['entity_results']:
        # if 'nucalm_locust_AHV' in i['data'][0]['values'][0]['values'][0]:
        re = next((j for j in range(len(i['data'])) if i['data'][j]['name'] == 'app_count'), False)
        if re and  i['data'][re]['values'][0]['values'][0] == '0':
            print("deleting " + i['data'][0]['values'][0]['values'][0], c, i['data'][1]['values'][0]['values'][0])
            # time.sleep(10)
            print(json.dumps(i))
            # time.sleep(5)
            c+=1
            rsp = client.delete(URL + 'blueprints/' + i['entity_id'])
            time.sleep(2)
        