import os
import sys
import json
import uuid
import time
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://{}:9440/'.format(sys.argv[1])
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

URL = "https://{}:9440/api/calm/v3.0/quotas".format(sys.argv[1])
for i in range(int(sys.argv[2])):
  project_uuid = str(uuid.uuid4())
  quota_uuid = str(uuid.uuid4())
  payload = json.dumps({n
    "metadata": {
      "kind": "quota",
      "project_reference": {
        "kind": "project",
        "name": "nucalm_1",
        "uuid": project_uuid
      },
      "uuid": quota_uuid
    },
    "spec": {
      "resources": {
        "data": {
          "disk": 107374182400000000,
          "vcpu": 100000,
          "memory": 107374182400000000
        },
        "entities": {
          "project": project_uuid
        },
        "metadata": {},
        "uuid": quota_uuid
      }
    }
  })
  response = client.post(URL, data=payload)
  print(response.text)

