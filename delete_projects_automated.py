""" Delete Projects """

import json
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

URL = "https://10.36.199.79:9440/api/multidomain/v4.3.b1/config/projects"

# Get projects (excluding system and default)
filter_param = "(isSystemDefined ne true and isDefault ne true)"
resp = client.get(f"{URL}?$filter={filter_param}&$limit=100")

if resp.status_code != 200:
    print(resp.content, "error in list url")
    exit()

resp_data = json.loads(resp.content)
projects = resp_data.get('data', [])

print(f"Deleting {len(projects)} projects")

count = 1
for project in projects:
    name = project.get('name', 'Unknown')
    ext_id = project.get('extId')
    
    # Only delete Nucalm projects for safety
    if not name.startswith('Nucalm_'):
        print(f"Skipping non-Nucalm project: {name}")
        continue
    
    print(f"Deleting project [{name}]. count [{count}]")
    
    s = client.delete(f"{URL}/{ext_id}")
    if s.status_code not in [200, 202, 204]:
        print(s.content, "error in delete url")
        continue
    
    print(f"Project [{name}] deleted successfully")
    count += 1