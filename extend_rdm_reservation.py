import json
import requests

import sys
import json
import uuid
import time
import base64
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = requests.Session()
user_name = sys.argv[1]
password = sys.argv[2]
client.auth = HTTPBasicAuth(user_name, password)
client.headers = {'content-type': 'application/json'}
client.verify = False


url = f"https://rdm.eng.nutanix.com/api/v1/filter/scheduled_deployments?expand=created_by&limit=25&raw_query=%7B%22%24and%22%3A%5B%7B%22%24or%22%3A%5B%7B%22created_by%22%3A%7B%22%24in%22%3A%5B%7B%22%24oid%22%3A%22652e4dbe82e14fdd0c50b6fb%22%7D%5D%7D%7D%2C%7B%22client.owner%22%3A%7B%22%24in%22%3A%5B%22{user_name}%22%5D%7D%7D%5D%7D%2C%7B%22status%22%3A%7B%22%24in%22%3A%5B%22SUCCESS%22%2C%22PROCESSING%22%2C%22PENDING%22%2C%22PRE_PENDING%22%2C%22REQUESTING_RESOURCES%22%2C%22RESOURCES_ALLOCATED%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22PROVISIONING_RESOURCES%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22UPDATING_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%2C%22UPDATED_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%5D%7D%7D%5D%7D&sort=-created_at&start=0"
payload={}
headers = {}



for _ in range(10):
  response = client.get(url, headers=headers, data=payload)
  for i in json.loads(response.text)['data']:
    print(i)
    url = 'https://rdm.eng.nutanix.com/api/v1/scheduled_deployments/' + i['_id']['$oid']
    payload = json.dumps({
      "duration": 120
    })
    base_64_auth = base64.b64encode(f"{user_name}:{password}".encode('utf-8'))
    headers = {
      'Content-Type': 'application/json',
      'Authorization': f"Basic {base_64_auth}",
      "x-requested-with": 'XMLHttpRequest'
    }
    response = client.put(url, headers=headers, data=payload, verify=False)
    print(response.content)
    print(response.status_code)
    print(i['name'])
