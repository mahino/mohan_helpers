import requests
import json

url = "https://api.virtuoso.qa/api/testsuites/latest_status?snapshotId=656845&goalId=97156&envelope=false"

payload = {}
headers = {
  'Authorization': 'Bearer fa8073f2-5ce7-4a3a-8750-59c7a1686238'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(json.loads(response.content))
