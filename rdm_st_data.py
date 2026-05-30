import copy
import requests
import json
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")


# all
url = "https://rdm.eng.nutanix.com/api/v1/filter/scheduled_deployments?expand=created_by&limit=25&raw_query=%7B%22%24and%22%3A%5B%7B%22%24or%22%3A%5B%7B%22created_by%22%3A%7B%22%24in%22%3A%5B%7B%22%24oid%22%3A%22652e4dbe82e14fdd0c50b6fb%22%7D%2C%7B%22%24oid%22%3A%225c5bf3476c9ece417c99c77e%22%7D%2C%7B%22%24oid%22%3A%225ad6ef5e460be1ad1a99940c%22%7D%5D%7D%7D%2C%7B%22client.owner%22%3A%7B%22%24in%22%3A%5B%22mohan.as1%22%2C%22nagaraj.bv%22%2C%22shashi.kiran%22%5D%7D%7D%5D%7D%2C%7B%22status%22%3A%7B%22%24in%22%3A%5B%22SUCCESS%22%2C%22PROCESSING%22%2C%22PENDING%22%2C%22PRE_PENDING%22%2C%22REQUESTING_RESOURCES%22%2C%22RESOURCES_ALLOCATED%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22PROVISIONING_RESOURCES%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22UPDATING_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%2C%22UPDATED_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%5D%7D%7D%5D%7D&sort=-created_at&start=0"
# mohan 
# url = "https://rdm.eng.nutanix.com/api/v1/filter/scheduled_deployments?expand=created_by&limit=25&raw_query=%7B%22%24and%22%3A%5B%7B%22%24or%22%3A%5B%7B%22created_by%22%3A%7B%22%24in%22%3A%5B%7B%22%24oid%22%3A%22652e4dbe82e14fdd0c50b6fb%22%7D%5D%7D%7D%2C%7B%22client.owner%22%3A%7B%22%24in%22%3A%5B%22mohan.as1%22%5D%7D%7D%5D%7D%2C%7B%22status%22%3A%7B%22%24in%22%3A%5B%22SUCCESS%22%2C%22PROCESSING%22%2C%22PENDING%22%2C%22PRE_PENDING%22%2C%22REQUESTING_RESOURCES%22%2C%22RESOURCES_ALLOCATED%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22PROVISIONING_RESOURCES%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22UPDATING_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%2C%22UPDATED_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%5D%7D%7D%5D%7D&sort=-created_at&start=0"

payload = {}
headers = {
  'Authorization': 'Basic bW9oYW4uYXMxOk1haGlub0A0MDE=',
  'Cookie': 'rdm__session_id=apkl62csgpe4y8vkq8z1j044zfqad3q3'
}

response = requests.request("GET", url, headers=headers, verify=False)

sample_data = {}
data = []

for deployment in json.loads(response.content)['data']:
  sData = copy.deepcopy(sample_data)
  s = deployment
  for i in s['deployments']:  
    url = "https://rdm.eng.nutanix.com/api/v1/deployments/" + i['$oid']
    lol = requests.request("GET", url, headers=headers, verify=False)
    lol = json.loads(lol.content)
    if 'message' in lol and lol['message'] == "ScheduledDeployment does not exist":
      continue
    elif 'svm_ip' in lol['data']['allocated_resource']:
      sData['pe_ip'] = lol['data']['allocated_resource']['svm_ip']
    elif 'host' in lol['data']['allocated_resource']:
      sData['pc_ip'] = lol['data']['allocated_resource']['host']
  sData['cluster_name'] = s['payload']['name']
  sData['user_name'] = s['client']['owner']
  sData['pool'] = s['allocated_pool']
  for i in s['payload']['resource_specs']:
    if "nos" in i['software']:
      sData['pe_version'] = i['software']['nos']['version']
  data.append(sData)

print(json.dumps(data))