import requests
import json

url = "https://10.46.117.165:9440/PrismGateway/services/rest/v1/vms?count=50&page=1&sortCriteria=-hypervisor_cpu_usage_ppm&searchAttributeList=vm_uuid&_=1779872146066&projection=stats%2CbasicInfo%2Calerts&filterCriteria=is_control_domain!%3D1%3Bis_cvm%3D%3D0"

payload = json.dumps({
  "params": {
    "metrics": "aggregate_hypervisor_memory_usage_ppm",
    "startTimeInUsecs": 1779850144623974,
    "endTimeInUsecs": 1779860944623974,
    "intervalInSecs": 30,
    "__": 1779860944623
  },
  "timeout": 20
})
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}

response = requests.request("GET", url, headers=headers, data=payload, verify=False)

print(response.text)
