
import requests
import json
import copy
import os


url = "https://rdm.eng.nutanix.com/api/v1/filter/scheduled_deployments?expand=created_by&limit=25&raw_query=%7B%22%24and%22%3A%5B%7B%22status%22%3A%7B%22%24in%22%3A%5B%22SUCCESS%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22UPDATING_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%2C%22UPDATED_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%5D%7D%7D%5D%7D&sort=-created_at&start="
url = "https://rdm.eng.nutanix.com/api/v1/filter/scheduled_deployments?expand=created_by&limit=25&raw_query=%7B%22%24and%22%3A%5B%7B%22%24or%22%3A%5B%7B%22created_by%22%3A%7B%22%24in%22%3A%5B%7B%22%24oid%22%3A%22652e4dbe82e14fdd0c50b6fb%22%7D%2C%7B%22%24oid%22%3A%225c5bf3476c9ece417c99c77e%22%7D%2C%7B%22%24oid%22%3A%225ad6ef5e460be1ad1a99940c%22%7D%5D%7D%7D%2C%7B%22client.owner%22%3A%7B%22%24in%22%3A%5B%22mohan.as1%22%2C%22nagaraj.bv%22%2C%22shashi.kiran%22%5D%7D%7D%5D%7D%2C%7B%22status%22%3A%7B%22%24in%22%3A%5B%22SUCCESS%22%2C%22PRODUCTION%22%2C%22PROCESSING%22%2C%22PENDING%22%2C%22PRE_PENDING%22%2C%22REQUESTING_RESOURCES%22%2C%22RESOURCES_ALLOCATED%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22PROVISIONING_RESOURCES%22%2C%22REQUESTING_SOFTWARE_RESOURCES%22%2C%22PROVISIONING_SOFTWARE_RESOURCES%22%2C%22SOFTWARE_RESOURCES_ALLOCATED%22%2C%22UPDATING_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%2C%22UPDATED_DEPLOYMENTS_WITH_ALLOCATED_RESOURCES%22%5D%7D%7D%5D%7D&sort=-created_at&start=0"
payload = {}
headers = {
  'Authorization': 'Basic bW9oYW4uYXMxOk1haGlub0A0MDE='
}



lol = []
pop = {}
pr = []
count = 0
for i in range(1):
  response = requests.request("GET", url + str(i*100), headers=headers, data=payload, verify=False)
  s = json.loads(response.content)
  for j in s['data']:
    for m in j['deployments']:
      pup = copy.deepcopy(pop)
      dep = requests.request("GET",f"https://rdm.eng.nutanix.com/api/v1/deployments/{m['$oid']}", headers=headers, data=payload, verify=False)
      dep = json.loads(dep.content)
      if 'software' in dep['data']['params'] and 'prism_central' in dep['data']['params']['software']:
        pup['pc_version'] = dep['data']['params']['software']['prism_central']['version']
        if dep['data']['status'] in ['PROCESSING', 'PENDING']:
          print(pup)
          continue
        if 'pc_static_ips' in dep['data']['allocated_resource']:
          pup['pc_ip'] = dep['data']['allocated_resource']['pc_static_ips']
        elif 'static_ips' in dep['data']['allocated_resource']:
          print(json.dumps(dep))
          pup['pc_ip'] = dep['data']['allocated_resource']['static_ips'][0]['ip']
        
        lol.append(pup)
      print(f"Working on deployement count [{count}]" )
      count +=1 

#     pup = copy.deepcopy(pop)
#     if 'nos' in i['payload']['resource_specs'][0]['software']:
#       if len(i['deployments']) < 2:
#         continue
#       pup['pe_version'] = i['payload']['resource_specs'][0]['software']['nos']['version']
#       pup['owner'] = i['created_by']['display_name']
#       pup['deployment_name'] = i['payload']['name']
#       pup['pe_name'] = i['payload']['resource_specs'][0]['name']
#       print(pup['pe_name'])
#       if len(i['deployments']) < 2:
#         continue
#       dep = requests.request("GET",f"https://rdm.eng.nutanix.com/api/v1/deployments/{i['deployments'][1]['$oid']}", headers=headers, data=payload, verify=False)
#       dep = json.loads(dep.content)
#       if 'prism_central' in dep['data']['params']['software']:
#         pup['pc_version'] = dep['data']['params']['software']['prism_central']['version']
#         if dep['data']['status'] in ['PROCESSING', 'PENDING']:
#           print(pup)
#           continue
#         pup['pc_ip'] = dep['data']['allocated_resource']['pc_static_ips']
#         lol.append(pup)
# print(json.dumps(lol))

# print(f"Total clusters : [{len(lol)}]")


d = []
for i in lol:
  if isinstance(i['pc_ip'], (list, str)):
    d.append(i['pc_ip'][0]) if isinstance(i['pc_ip'], list) else d.append(i['pc_ip'])
  
import subprocess
import json

def check_ping(ip_address):
    # Ping the IP address once
    process = subprocess.Popen(['ping', '-c', '1', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode == 0  # Return True if return code is 0 (success), False otherwise
p = []
for ip_to_check in d:
    if check_ping(ip_to_check):
      print(f"pc_ip working accessible [{ip_to_check}]")
      p.append(ip_to_check)


print(json.dumps(p))