import sys
import json
import requests
import urllib3
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BASE_URL = 'https://{}:9440/'.format(sys.argv[1])
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False
V3 = 'api/nutanix/v3/'
URL = BASE_URL + V3
urls = [ f"https://ncm.pc-10-117-59-93.nutanixqa.com:9440/api/nutanix/v3/runbooks/{i}/execute" for i in ["871d5284-2358-454b-a990-90dc96192b67", "96581822-8479-4553-8406-f16d569ba20c", "c9854e66-a93f-4113-8b60-791dd13bd76a", "84e85592-210d-4b64-8fe4-1ebe91a7c712", "be12dd6c-0fae-4680-84af-2843a5302524", "ba6af8ee-e786-4f42-a5f2-2160c9b50002", "7bafed31-5bec-4574-8694-7e0e0799bbd5", "c77d9ea3-796d-4aba-8e3f-ccf5b90c10a7", "24979133-8214-4aa8-b9c8-15125e5373e9", "55eb2468-bc29-4223-8177-a3ca391a82bd"]]
def fetch(url):
    response = client.post(url, data=json.dumps({"spec":{"args":[],"default_target_reference":{}}}))#"_state!=deleted"}))#state!=DELETED"}))#DELETED;(type!=nutanix;type!=custom_provider)"}))
    return response.text
with ThreadPoolExecutor() as executor:
    results = list(executor.map(fetch, urls))
for i, result in enumerate(results):
    print(f"Response from {urls[i]}: {result}")
