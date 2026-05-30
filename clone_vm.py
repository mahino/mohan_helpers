import requests
import json
import random
import sys
import copy
import urllib3
import time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# url = "https://10.36.198.255:9440/api/nutanix/v3/vms/453e8a1b-69e7-490f-9668-fc732ce952fa/clone"
url = "https://10.36.198.255:9440/api/nutanix/v3/vms/e5ed65fe-4229-49eb-9500-b3f07f7a6b43/clone"

payload = {
    "override_spec": {
        "name": "vCheater-",
        "memory_size_mib": 256,
        "num_sockets": 1,
        "num_vcpus_per_socket": 1,
        "boot_config": {
            "boot_type": "LEGACY",
            "boot_device": {
                "disk_address": {
                    "device_index": 0,
                    "adapter_type": "SCSI"
                }
            }
        }
    }
}

headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
  'Cookie': 'NTNX_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U=; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChlxNHJoaGFjdGF4c3Z2bnZyaTZibHBhNWlhEhliaXpkYTd5ZHVmeGRib3o2bmZzZ3JrZTVk; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCI1vyuBhoHTWVyY3VyeSAAKihhOTU2NTNmNWJjNDYyZDIwZGYxYzI0MTE3NDQxNTgxZDM4Y2UyMzY2|ycnGsf6wfyw8VV4+q3JTqWNLYJgCBf1yP3KwdgV9n7U='
}

for i in range(1,250):
  pp = copy.deepcopy(payload)
  pp['override_spec']['name'] += str(i)
  response = requests.request("POST", url, headers=headers, data=json.dumps(pp), verify=False)
  response = json.loads(response.content)
  print(pp['override_spec']['name'])
  time.sleep(1)