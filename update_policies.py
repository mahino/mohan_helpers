import requests
import json

from requests.auth import HTTPBasicAuth

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False


URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/api/nutanix/v3/policies/"

payload = {
    "length": 75,
    "offset": 0,
    "filter": "type==APPROVAL"
}
count = 0
temp_count = 0
break_count = 100
offset = 0
for i in range(1):
    if count >=break_count:
        break
    payload['offset'] = offset

    resp = client.post(URL + "list", data=json.dumps(payload))
    pol_list = json.loads(resp.content)
    print(pol_list)
    for pol in pol_list['entities']:
        if count >=break_count:
            break
        count += 1
        print(f"Updating policy [{pol['metadata']['name']}]: {count}")
        pol_get = client.get(URL + pol['metadata']['uuid'])
        pol_get = json.loads(pol_get.content)
        pol_get['spec']['resources']['condition_list'][0]['criteria_list'][0]['rhs'] = "RB_ST"
        del pol_get['status']
        resp = client.put(URL + pol['metadata']['uuid'], data=json.dumps(pol_get))
        if resp.status_code != 200:
            print(f"Error updating policy [{pol['metadata']['name']}]")
            print(resp.content)
        else:
            print(f"Policy [{pol['metadata']['name']}] updated successfully: {count}")