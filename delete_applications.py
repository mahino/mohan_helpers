""" Nucalm environment setup"""

import sys
import json
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

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

delete_mock_vm_apps_only = False
delete_app = True
#VERIFY_FAILED
#DRAFT
timings = {}
end_timings = {}
total = []
error_list = {}
message_list = []
c = 1
l = 250 
skip_count = 1
del_failed = []
deleted_count = []
k= int(sys.argv[2]) if len(sys.argv) == 3 else 0
# custom_list = []
m = 0
for i in range(1):
  resp = client.post(URL + 'apps/list', data=json.dumps({"length":250,"offset":k*250, "filter":"_state==error"}))#stopped, error, running
  # groups_pay = {"length":"100","offset":100,"sort":"created_on","sort_order":"DESCENDING","fields":["app_name","uuid","categories","project_name","account_names","substrate_types","source_marketplace_name","state","environment","marketplace_version","vm_names","owner","app_url","created_on","updated_on","protection_status","failover_status"],"filter":"app_family==Other_Apps;source_marketplace_name!=NCM_APP;app_family==Other_Apps;(state==running)"}
  # resp = client.post('https://ncm.pc-10-117-59-93.nutanixqa.com:9440/api/calm/v3.0/groups', data=json.dumps(groups_pay))#stopped, error, running
  if resp.status_code != 200:
    print(resp.content, "error in list url")
  resp = json.loads(resp.content)
  # print(json.dumps(resp))
  for app in resp['entities']:
    m+=1
    print(f"INFO: app count [{m}/{len(resp['entities'])}]")
    if delete_mock_vm_apps_only:
      run_pay_1 = {"filter":f"application_reference=={app['metadata']['uuid']};(type==action_runlog,type==audit_runlog,type==ngt_runlog,type==clone_action_runlog,type==platform_sync_runlog,type==patch_runlog)"}
      temp_resp = client.post(BASE_URL + 'api/calm/v3.0/apps/' + app['metadata']['uuid'] + '/app_runlogs/list', data=json.dumps(run_pay_1)).content
      app_get_resp = json.loads(temp_resp)
      run_pay_2 = {"filter":f"root_reference=={app_get_resp['entities'][-1]['metadata']['uuid']}"}
      temp_resp = client.post(BASE_URL + 'api/calm/v3.0/apps/' + app['metadata']['uuid'] + '/app_runlogs/list', data=json.dumps(run_pay_2)).content
      app_get_resp = json.loads(temp_resp)
      # print(json.dumps(app_get_resp))
      subst_uuid = next((rl['metadata']['uuid'] for rl in app_get_resp['entities'] if 'element_type' in rl['status'] and rl['status']['element_type'] == 'SubstrateElement'), None)
      if subst_uuid:
        subst_get_resp = client.get(BASE_URL + f"api/calm/v3.0/apps/{app['metadata']['uuid']}/app_runlogs/{subst_uuid}/output").content
        subst_get_resp = json.loads(subst_get_resp)
        delete_app = False if len(subst_get_resp['status']['output_list'][0]['output']) else True
    if delete_app:
      print(app['metadata']['name'], len(deleted_count), m)
      deleted_count.append(app['metadata']['uuid'])
  # print(json.dumps(deleted_count))
    if delete_app == False:
      print(f"INFO: App [{app['metadata']['name']}] delete skipped, skip count [{skip_count}]")
      skip_count += 1
      continue
    print(app['metadata']['name'])
    try:
      actions_spec = client.delete(URL + 'apps/' + app['metadata']['uuid'], data=json.dumps({}))
      deleted_count.append(app['metadata']['uuid'])
    except Exception as e:
      del_failed.append(app['metadata']['uuid'])
      print(e)
    if actions_spec.status_code!= 200:
      print(actions_spec.content)
      continue
    for k in range(30):
      temp_resp = client.get(URL + 'apps/' + app['metadata']['uuid']).content
      try:
        app_get_resp = json.loads(temp_resp)
        # print(custom_list)
        if app_get_resp['status']['state'] == 'deleted':
          print("{0} = {1}, {2}".format(app_get_resp['metadata']['name'], app_get_resp['status']['state'], c))
          break
        print("{0} = {1}, {2}".format(app_get_resp['metadata']['name'], app_get_resp['status']['state'], c))
        time.sleep(10)
      except Exception as e:
        print(e)
        print(temp_resp.content)
        time.sleep(20)
    # custom_list.remove (j)
    
    c += 1

print(del_failed)
print(json.dumps(deleted_count))