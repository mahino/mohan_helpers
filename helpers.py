"""
Copyright (c) 2017 Nutanix Inc. All rights reserved.
Author: ram.daga@nutanix.com
"""

# pylint: disable=invalid-name, unused-variable, relative-import
# pylint: disable=unused-argument

import json
import random
import string
import time
from os.path import dirname
from os import path
from constants import V0, V1, V3, SBTSKTRUE, OLDPRGTRUE, TIMEOUT, \
    PES_LIST_CSV, VMBULKCOUNT, VMDISKCLONE, VMDISKCREATE, VMNICINFO, \
    VMS_URL, CLUSTERINFO

CONFIG_FOLDER = path.join(dirname(__file__), "../", "config")


def get_json_config(file_name):
  """
  Load config by config file name.

  Args:
    file_name(str): The config file name to load

  Returns:
    dict: The content defined in the config file
  """
  file_path = path.join(CONFIG_FOLDER, file_name)

  with open(file_path, "r") as file_handle:
    config_data = json.load(file_handle)
  return config_data


def load_default(self, config, entity):
  """
    Make rest calls from default config in the config file

    Args:
      config(str): The config file name to load
      entity(str): Entity type

    Returns:
      None
  """
  for payload in config["default"]["payload"]:
    self.client.post(config["default"]["url"], data=json.dumps(payload),
                     name=self.__class__.__name__ + '/' + entity + '/default')


def group_by(self, config, entity):
  """
    Make rest calls from group_by config in the config file.

    Args:
      config(str): The config file name to load
      entity(str): Entity type

    Returns:
      None
  """
  for group in config["group_by"]:
    self.client.post(group["url"], data=json.dumps(group["payload"]),
                     name=self.__class__.__name__ + '/' + entity + '/group_by')


def load_filter(self, config, entity):
  """
    Make rest calls from filter config in the config file.

    Args:
      config(str): The config file name to load
      entity(str): Entity type

    Returns:
      None
  """
  c = self.client
  for _filter in config["filters"]:
    for payload in _filter["payload"]:
      resp = c.post(_filter["url"], data=json.dumps(payload),
                    name=self.__class__.__name__ + '/' + entity + '/filter')
      if resp.status_code != 200:
        print ("API for loading filter: %s for entity: %s failed") % \
              (_filter, entity)
        print ("URL: %s") % _filter["url"]
        print ("Payload: %s") % payload


def get_cluster_ids(self, api_version):
  """
    Make rest call to get id for each registered PE.

    Args:
      api_version(str): Rest API version to used to get registered PEs

    Returns:
      List of cluster uuids
  """
  c = self.client
  if api_version == "V1":
    response = c.get(V1 + "clusters",
                     name=self.__class__.__name__ + '/hp/clusters')
  else:
    payload = {"kind": "cluster", "offset": 0, "length": 300}
    response = c.post(V3 + "clusters/list", data=json.dumps(payload),
                      name=self.__class__.__name__ + '/hp/clusters/list')

  clusters_uuid = []

  if response.status_code == 200:
    response = json.loads(response.content)

    if api_version == "V1":
      cluster_count = response["metadata"]["totalEntities"]
    else:
      cluster_count = response["metadata"]["total_matches"]

    for i in range(cluster_count):
      if api_version == "V1":
        cluster_uuid = response["entities"][i]["id"]
      else:
        if 'name' not in response["entities"][i]["status"]:
          continue
        cluster_uuid = response["entities"][i]["metadata"]["uuid"]
      clusters_uuid.append(cluster_uuid)

  return clusters_uuid


def get_pe_uuids(self, pes_list):
  """
    Make rest call to get uuid for registered PE containing given prefix.

    Args:
      pes_list(list): List of PEs (names/ip) for which uuids are needed

    Returns:
      Dict of cluster name/ip, uuids
  """
  c = self.client
  response = c.get(V1 + "clusters", name=self.__class__.__name__ + '/clusters')
  cluster_info = {}
  if response.status_code == 200:
    response = json.loads(response.content)
    cluster_count = response["metadata"]["totalEntities"]
    for i in range(cluster_count):
      name = response["entities"][i]["name"]
      if name in pes_list:
        cluster_info[name] = response["entities"][i]["uuid"]
      else:
        ip = response["entities"][i]["clusterExternalIPAddress"]
        if ip in pes_list:
          cluster_info[ip] = response["entities"][i]["uuid"]
  return cluster_info


def get_cluster_uuids(self, api_version):
  """
    Make rest call to get uuid for each registered PE.

    Args:
      api_version(str): Rest API version to used to get registered PEs

    Returns:
      List of cluster uuids
  """
  cluster_ids = get_cluster_ids(self, api_version)
  for idx, cluster_id in enumerate(cluster_ids):
    cluster_ids[idx] = cluster_id.split('::')[0]
  return cluster_ids


def clusters_metrics(self, cluster_ids):
  """
    Make rest calls to get metrics for each registered PE.

    Args:
      cluster_ids(list): List of uuid of registered PEs

    Returns:
      None
  """
  c = self.client
  # Projection is for all PEs
  for cluster_id in cluster_ids:
    c.get(V1 + "clusters/" + cluster_id + "?projection=alerts_count%2Chealth",
          name=self.__class__.__name__ + '/' + cluster_id + '/projection')

  # Stats are collected for 10 PEs only
  for cluster_id in cluster_ids[0:10]:
    end_time = int(time.time()) * 1000000
    start_time = str(end_time - 7200000000)
    end_time = str(end_time)

    c.get(V1 + "clusters/" + cluster_id +
          "/stats?metrics=controller_avg_io_latency_usecs&startTimeInUsecs="
          + start_time + "&endTimeInUsecs=" + end_time + "&intervalInSecs=360",
          name=self.__class__.__name__ + '/hp/metrics/controller_avg_io')

    c.get(V1 + "clusters/" + cluster_id +
          "/stats?metrics=hypervisor_memory_usage_ppm&startTimeInUsecs=" +
          start_time + "&endTimeInUsecs=" + end_time + "&intervalInSecs=360",
          name=self.__class__.__name__ + '/hp/metrics/hypervisor_memory_usage')

    c.get(V1 + "clusters/" + cluster_id +
          "/stats?metrics=hypervisor_cpu_usage_ppm&startTimeInUsecs=" +
          start_time + "&endTimeInUsecs=" + end_time + "&intervalInSecs=360",
          name=self.__class__.__name__ + '/hp/metrics/hypervisor_cpu_usage_ppm')

    c.get(V1 + "clusters/" + cluster_id +
          "/stats?metrics=controller_num_iops&startTimeInUsecs=" +
          start_time + "&endTimeInUsecs=" + end_time + "&intervalInSecs=360",
          name=self.__class__.__name__ + '/hp/metrics/controller_num_iops')


def common_hp_bg_calls(self):
  """
    Make rest calls to mimic user login.

    Args:
      None

    Returns:
      None
  """
  c = self.client
  c.get(V1 + "cluster", name='common/hp/bg/cluster')
  c.get(V1 + "application/user_data?type=custom_dashboard",
        name='common/hp/bg/dashoard')
  c.get(V1 + "application/system_data?type=ui_config", name='common/hp/bg/ui')
  c.get(V1 + "health_checks?includeInternalChecks=true&"
             "exceptionDetails=true&globalConfig=true",
        name='common/hp/bg/health')
  end_time = str(int(time.time()) * 1000000)
  c.get(SBTSKTRUE + end_time + ")", name='common/hp/bg/progress_monitor')
  c.get(OLDPRGTRUE + end_time + ")", name='common/hp/bg/progress_monitor')


def create_dashboard(self):
  """
    Creates a user defined dashboard.

    Args:
      None

    Returns:
      None
  """
  self.client.get(V1 + "application/user_data?type=custom_dashboard")
  grid_id = "grid" + id_generator(12)
  dashboard_id = "id" + id_generator(12)
  title = "user" + id_generator(3)
  create_time = int(time.time()) * 1000000

  payload = {"gridId": grid_id, "vantagePoints": None,
             "customizable": False, "id": dashboard_id, "title": title,
             "createdTimeUsecs": create_time, "updatedTimeInUsecs": None,
             "type": "custom_dashboard", "key": dashboard_id,
             "value": "{\"gridId\":\"" + grid_id + "\","
                      "\"vantagePoints\":null,\"customizable\":false,"
                      "\"id\":\"" + dashboard_id + "\",\"title\":" + title + ","
                      "\"createdTimeUsecs\":" + str(create_time) + ","
                      "\"updatedTimeInUsecs\":null,"
                      "\"type\":\"custom_dashboard\","
                      "\"key\":" + dashboard_id + "}"}
  self.client.post(V1 + "application/user_data", data=json.dumps(payload))


def id_generator(length):
  """
    Generates a random id of given length.

    Args:
      length(int): Length of the random string

    Returns:
      Random generated string of given length
  """
  chars = string.ascii_lowercase + string.digits
  return ''.join(random.choice(chars) for _ in range(length))


def set_reset_focus(self, config, entity):
  """
    Set and reset focus.

    Args:
      config(json object): json object of the config file
      entity(str): entity type

    Returns:
      HTTP response on setting the focus (to be used later for extracting
      entity ids)
  """
  c = self.client

  resp = ''
  if "focus" in config:
    resp = c.post(config["focus"]["url"],
                  data=json.dumps(config["focus"]["payload"]),
                  name=self.__class__.__name__ + '/' + entity + '/set_focus')
    if resp.status_code != 200:
      print ("API for setting perf focus for entity: %s failed") % entity
      print ("URL: %s") % config["focus"]["url"]
      print ("Payload: %s") % config["focus"]["payload"]

  if "focus_reset" in config:
    resp2 = c.post(config["focus_reset"]["url"],
                   data=json.dumps(config["focus_reset"]["payload"]),
                   name=self.__class__.__name__ + '/' + entity + '/reset_focus')
    if resp2.status_code != 200:
      print ("API for re-setting perf focus for entity: %s failed") % entity
      print ("URL: %s") % config["focus_reset"]["url"]
      print ("Payload: %s") % config["focus_reset"]["payload"]

  if "batch" in config:
    resp2 = c.post(config["batch"]["url"],
                   data=json.dumps(config["batch"]["payload"]),
                   name=self.__class__.__name__ + '/' + entity + '/batch')
    if resp2.status_code != 200:
      print ("API for batch call for entity: %s failed") % entity
      print ("URL: %s") % config["batch"]["url"]
      print ("Payload: %s") % config["batch"]["payload"]

  return resp


def get_entity_count(entity, response):
  """
    Get entity count from the given response

    Args:
      entity(str): entity type
      response(http response): http response

    Returns:
      entity count
  """
  response = json.loads(response.content)
  # Get details of 5 entities
  if entity == "categories":
    entity_count = response["total_group_count"]
  else:
    entity_count = response["total_entity_count"]
  return entity_count if entity_count < 5 else 5


def get_entity_ids_old(entity, response):
  """
    Get entity ids.

    Args:
      entity(str): entity type
      response(http response): http response

    Returns:
      list of entity ids
  """
  entity_count = get_entity_count(entity, response)
  response = json.loads(response.content)
  entity_ids = []

  for i in range(entity_count):
    if entity == "categories":
      entity_ids.append(response["group_results"][i]["group_summaries"]
                        ["sum:name"]["values"][0]["values"][0])

    elif entity == "clusters":
      # Response contains pc cluster uuid. skip that
      entity_id = ""
      cluster_data = response["group_results"][0]["entity_results"][i]["data"]
      for data in cluster_data:
        if data["name"] == "cluster_name" and data["values"] != []:
          entity_id = response["group_results"][0]["entity_results"][i]\
            ["entity_id"]
        else:
          continue
      if entity_id != "":
        entity_ids.append(entity_id)

    else:
      entity_ids.append(response["group_results"][0]["entity_results"][i]
                        ["entity_id"])

  return entity_ids


def load_default_get(self, config, entity):
  """
    Make rest calls from default config in the config file

    Args:
      config(str): The config file name to load
      entity(str): Entity type

    Returns:
      None
  """
  for url in config["default_get"]:
    self.client.get(url, name=self.__class__.__name__ + '/' + entity +
                    '/default_get')


def load_default_post(self, config, entity):
  """
    Make rest calls from default config in the config file

    Args:
      config(str): The config file name to load
      entity(str): Entity type

    Returns:
      None
  """
  for request in config["default_post"]:
    self.client.post(request["url"], data=json.dumps(request["payload"]),
                     name=self.__class__.__name__ + '/' + entity +
                     '/default_post')


def get_vm_id(self, vm_name):
  """
    Get the vm id for the given vm

    Args:
      vm_name(str): vm name

    Returns:
      vm id
  """
  payload = {"entity_type": "vm", "query_name": "eb:data",
             "filter_criteria": "vm_name==" + vm_name}
  for i in range(0, TIMEOUT, 5):
    resp = self.client.post(V1 + 'groups', data=json.dumps(payload),
                            name=self.__class__.__name__ + '/vm/id')
    if resp.status_code == 200:
      resp = json.loads(resp.content)
      entity_count = resp['filtered_entity_count']
      if entity_count == 1:
        vm_id = resp["group_results"][0]["entity_results"][0]["entity_id"]
        #print "VM: %s, VM ID: %s" % (vm_name, vm_id)
        return vm_id
    time.sleep(5)
  print ("Failed to fetch VM ID for VM: %s after %d seconds") % (vm_name, TIMEOUT)
  return ""


def vm_create(self, cluster_uuid, cluster_name):
  """
    Create a vm on the given cluster

    Args:
      cluster_uuid(str): cluster uuid
      cluster_name(str): cluster name

    Returns:
      vm name
  """
  vm_name = "locust_" + id_generator(12)
  VMDISK = [{"is_cdrom": False,
             "disk_address": {"device_bus": "scsi"},
             "vm_disk_clone":
               {"disk_address": {"vmdisk_uuid": VMDISKCLONE[cluster_name]},
                "minimum_size":1997159792.64}},
            {"is_cdrom": False,
             "disk_address": {"device_bus": "scsi"},
             "vm_disk_create":
               {"storage_container_uuid": VMDISKCREATE[cluster_name],
                "size":5368709120}}]

  VMNIC = [{"network_uuid": VMNICINFO[cluster_name]}]

  payload = [{"generic_dto":
                {"name": vm_name,
                 "memory_mb": 204.8,
                 "num_vcpus": 4,
                 "description": "",
                 "num_cores_per_vcpu": 1,
                 "vm_disks": VMDISK,
                 "hypervisor_type": "ACROPOLIS",
                 "affinity": None,
                 "vm_nics": VMNIC,
                 "vm_features": {"AGENT_VM": False}},
              "cluster_uuid": cluster_uuid}]

  print (payload)
  resp = self.client.post(V1 + 'vms/fanout', data=json.dumps(payload),
                          name=self.__class__.__name__ + '/vm/create')

  if resp.status_code == 200:
    print (resp.content)
    return vm_name
  else:
    print ("API to create VM: %s on cluster: %s failed") % \
          (vm_name, cluster_uuid)
    return ""


def vm_clone(self, vm_name, vm_id, cluster_uuid):
  """
    Clone the given vm on the given cluster

    Args:
      vm_name(str): name of the clone vm
      vm_id(str): id of the source vm
      cluster_uuid(str): cluster uuid

    Returns:
      none
  """
  payload = [{"generic_dto": {"spec_list": [{"name": vm_name, "memory_mb":102.4,
                                             "num_vcpus": 1,
                                             "num_cores_per_vcpu": 1,
                                             "override_network_config":True,
                                             "clone_affinity":False}],
                              "uuid": vm_id}, "cluster_uuid": cluster_uuid}]
  self.client.post(V1 + 'vms/clone/fanout', data=json.dumps(payload),
                   name=self.__class__.__name__ + '/vm/clone')


def vm_update_desc(self, vm_name, vm_id, cluster_uuid):
  """
    Update description of the given vm

    Args:
      vm_name(str): vm name
      vm_id(str): vm id
      cluster_uuid(str): cluster uuid

    Returns:
      None
  """
  desc = "locust_desc_" + id_generator(12)
  payload = [{"generic_dto": {"name": vm_name, "memory_mb": 102.4,
                              "num_vcpus": 1, "description": desc,
                              "num_cores_per_vcpu": 1, "affinity": None,
                              "vm_features": {"AGENT_VM": False},
                              "uuid": vm_id}, "cluster_uuid": cluster_uuid}]
  self.client.post(V0 + 'vms/fanout', data=json.dumps(payload),
                   name=self.__class__.__name__ + '/vm/update')


def vm_check_state(self, vm_name, state):
  """
    Check if power state of the given vm matches given state until TIMEOUT

    Args:
      vm_name(str): vm name
      state(str): on, off, pause, resume

    Returns:
      true if the state matches, else false
  """
  c = self.client
  for i in range(0, TIMEOUT, 5):
    payload = {"entity_type": "vm", "query_name": "eb:data",
               "group_member_attributes": [{"attribute":"power_state"}],
               "filter_criteria": "vm_name==" + vm_name}
    resp = c.post(V1 + "groups", data=json.dumps(payload),
                  name=self.__class__.__name__ + '/vm/check_power_state')

    if resp.status_code == 200:
      resp = json.loads(resp.content)
      power_state = resp['group_results'][0]['entity_results'][0]['data'][0]\
        ['values'][0]['values'][0]
      if state == 'pause':
        state = 'suspended'
      if state == 'resume':
        state = 'on'
      if power_state == state:
        return True
      #else:
      #  print "VM power state Current: %s, Expected: %s" % (power_state, state)
    #else:
    #  print "Rest call to check power state for VM: %s failed with response " \
    #        "code: %d" % (vm_name, resp.status_code)

    # print "Waiting for 5 seconds before checking again"
    time.sleep(5)

  return False


def vm_change_state(self, vm_id, cluster_uuid, vm_name, state):
  """
    Change power state of the given vm

    Args:
      vm_id(str): vm id
      cluster_uuid(str): cluster uuid
      vm_name(str): vm name
      state(str): on, off, pause, resume

    Returns:
      bool true if the operation was successful, else false
  """
  c = self.client
  payload = [{"generic_dto": {"transition": state, "uuid": vm_id},
              "cluster_uuid": cluster_uuid}]
  c.post(V0 + 'vms/set_power_state/fanout', data=json.dumps(payload),
         name=self.__class__.__name__ + '/vm/state/' + state)
  return vm_check_state(self, vm_name, state)


def vm_bulk_change_state(self, vm_info, cluster_uuid, state):
  """
    Change power state of the given vm list

    Args:
      vm_info(dict): dictionary of vm names and vm ids
      cluster_uuid(str): cluster uuid
      state(str): on, off, pause, resume

    Returns:
      None
  """
  c = self.client
  payload = []
  for vm_name, vm_id in vm_info.items():
    payload.append({"generic_dto": {"transition": state, "uuid": vm_id},
                    "cluster_uuid": cluster_uuid})
  resp = c.post(V0 + 'vms/set_power_state/fanout', data=json.dumps(payload),
                name=self.__class__.__name__ + '/vm/bulk/state/' + state)

  if resp.status_code == 200:
    for vm_name, vm_id in vm_info.items():
      # print "Checking power state for %s (%s)" % (vm_name, vm_id)
      status = vm_check_state(self, vm_name, state)
      if not status:
        print (json.dumps(payload))
        print ("Failed to change the state of VM: ") + vm_name + (" to: ") + state
      # else:
      #   print ("Changed the state of VM: ") + vm_name + (" to: ") + state
  else:
    print ("Rest call for bulk state: %s failed (status code: %d)") \
          % (state, resp.status_code)


def vm_bulk_delete(self, vm_info, c_uuid):
  """
    Delete the given vms on the given cluster

    Args:
      vm_info(dict): dictionary of vm names and vm ids
      c_uuid(str): cluster uuid

    Returns:
      None
  """
  payload = []
  for vm_name, vm_id in vm_info.items():
    payload.append({"generic_dto": {"uuid": vm_id}, "cluster_uuid": c_uuid})

  # print payload
  resp = self.client.post(V0 + 'vms/delete/fanout', data=json.dumps(payload),
                          name=self.__class__.__name__ + '/vm/bulk/delete')
  if resp.status_code != 200:
    print ("Rest call for bulk delete failed (status code: %d)") \
          % resp.status_code


def vm_delete(self, vm_id, cluster_uuid):
  """
    Delete the given vm on the given cluster

    Args:
      vm_id(str): id of the vm
      cluster_uuid(str): cluster uuid

    Returns:
      None
  """
  payload = [{"generic_dto": {"uuid": vm_id}, "cluster_uuid": cluster_uuid}]
  resp = self.client.post(V0 + 'vms/delete/fanout', data=json.dumps(payload),
                          name=self.__class__.__name__ + '/vm/delete')
  if resp.status_code != 200:
    print ("Rest call for VM delete failed (status code: %d)") \
          % resp.status_code


def vm_rw_ops(self, config):
  """
    Read-write operations on VMs

    Args:
      config(json): config file that has VM create bg calls

    Returns:
      None
  """
  pes_list = PES_LIST_CSV.split(",")
  cluster_info = get_pe_uuids(self, pes_list)
  if not cluster_info:
    print ("Failed to get uuids for clusters: %s") % PES_LIST_CSV
  else:
    for cluster_name, cluster_uuid in cluster_info.items():
      for url in config["create_vm_bg"]:
        url = url + cluster_uuid
        self.client.get(url, name=self.__class__.__name__ + 'vm/create/bg')

      vm_name = vm_create(self, cluster_uuid, cluster_name)
      if vm_name != "":
        print ("API to create VM: %s on cluster: %s passed") % \
              (vm_name, cluster_name)
        time.sleep(5)
        # clone_vm_name = vm_name + '-clone'
        vm_id = get_vm_id(self, vm_name)
        if vm_id != "":
          print ("VM: %s created on cluster: %s with VM id: %s") % \
                (vm_name, cluster_name, vm_id)
          vm_change_state(self, vm_id, cluster_uuid, vm_name, "on")
          print ("changed vm state to ON")
          time.sleep(5)
          vm_change_state(self, vm_id, cluster_uuid, vm_name, "pause")
          print ("changed vm state to PAUSE")
          time.sleep(5)
          vm_change_state(self, vm_id, cluster_uuid, vm_name, "resume")
          print ("changed vm state to RESUME")
          time.sleep(5)
          vm_change_state(self, vm_id, cluster_uuid, vm_name, "off")
          print ("changed vm state to OFF")
          time.sleep(5)
          # vm_clone(self, clone_vm_name, vm_id, cluster_uuid)
          # clone_vm_id = get_vm_id(self, clone_vm_name)
          # if clone_vm_id != '':
          #   vm_delete(self, clone_vm_id, cluster_uuid)
          vm_delete(self, vm_id, cluster_uuid)


def vm_bulk_rw_ops(self, config):
  """
    Read-write operations on VMs

    Args:
      config(json): config file that has VM create bg calls

    Returns:
      None
  """
  pes_list = PES_LIST_CSV.split(",")
  cluster_info = get_pe_uuids(self, pes_list)
  if not cluster_info:
    print ("Failed to get uuids for clusters: %s") % PES_LIST_CSV
  else:
    for cluster_name, cluster_uuid in cluster_info.items():
      vm_info = {}
      for vm in range(VMBULKCOUNT):
        # for url in config["create_vm_bg"]:
        #   url = url + cluster_uuid
        #   self.client.get(url,
        #                   name=self.__class__.__name__ + 'vm/bulk_create/bg')
        vm_name = vm_create(self, cluster_uuid, cluster_name)
        if vm_name != "":
          vm_id = get_vm_id(self, vm_name)
          if vm_id != "":
            vm_info[vm_name] = vm_id
      vm_bulk_change_state(self, vm_info, cluster_uuid, "on")
      vm_bulk_change_state(self, vm_info, cluster_uuid, "pause")
      vm_bulk_change_state(self, vm_info, cluster_uuid, "resume")
      vm_bulk_change_state(self, vm_info, cluster_uuid, "off")
      vm_bulk_delete(self, vm_info, cluster_uuid)


def vm_entity_details(self, response):
  """
    API calls when entity detail page is loaded

    Args:
      response(json): http response from general focus that has entity details

    Returns:
      None
  """
  c = self.client
  entity_count = get_entity_count("vms", response)
  entity_ids = get_entity_ids(entity_count, response)
  for entity_id in entity_ids:
    c.get("console/app-extension/extras/entity_config/details.json")
    query_eb_stats(self, entity_id, "vms")
    query_base_group_model_name(self, entity_id, "vms")
    query_base_group_model_msg(self, entity_id, "vm")


def cluster_entity_details(self, response):
  """
    API calls when entity detail page is loaded

    Args:
      response(json): http response from general focus that has entity details

    Returns:
      None
  """
  c = self.client
  entity_count = get_entity_count("clusters", response)
  entity_ids = get_entity_ids(entity_count, response)
  for entity_id in entity_ids:
    query_eb_stats(self, entity_id, "clusters")
    query_base_group_model_name(self, entity_id, "clusters")
    query_base_group_model_msg(self, entity_id, "cluster")


def project_entity_details(self, response):
  """
    API calls when entity detail page is loaded

    Args:
      response(json): http response from general focus that has entity details

    Returns:
      None
  """
  c = self.client
  entity_count = get_entity_count("projects", response)
  entity_ids = get_entity_ids(entity_count, response)
  for entity_id in entity_ids:
    query_base_group_model_name(self, entity_id, "projects")
    query_base_group_model_project_reference(self, entity_id, "projects")
    query_base_group_model_catid(self, entity_id, "projects")
    query_base_group_model_msg(self, entity_id, "project")
    query_base_group_model_network(self, entity_id, "projects")
    # Usage tab
    query_eb_stats(self, entity_id, "projects")



def role_entity_details(self, response):
  """
    API calls when entity detail page is loaded

    Args:
      response(json): http response from general focus that has entity details

    Returns:
      None
  """
  c = self.client
  entity_count = get_entity_count("roles", response)
  entity_ids = get_entity_ids(entity_count, response)
  for entity_id in entity_ids:
    c.get(V3 + 'roles/' + entity_id,
          name=self.__class__.__name__ +  '/roles/details/' + entity_id)
    query_base_group_model_name(self, entity_id, "roles")
    query_base_group_model_msg(self, entity_id, "role")


def user_entity_details(self, response):
  """
    API calls when entity detail page is loaded

    Args:
      response(json): http response from general focus that has entity details

    Returns:
      None
  """
  c = self.client
  entity_count = get_entity_count("users", response)
  entity_ids = get_entity_ids(entity_count, response)
  for entity_id in entity_ids:
    query_base_group_model_abac(self, entity_id, "users")
    query_base_group_model_user_uuid(self, entity_id, "users")
    query_base_group_model_msg(self, entity_id, "abac_user_capability")


def get_entity_ids(entity_count, response):
  """
    Extract entity ids from thre response

    Args:
      entity_count(int): number of entity ids to be retrieved
      response(json): http from general focus that has entity details

    Returns:
      entity_ids(list): list of entity ids
  """
  entity_ids = []
  for i in range(entity_count):
    if response.__class__.__name__ == 'Response':
      response = json.loads(response.content)

    entity_id = response["group_results"][0]["entity_results"][i]["entity_id"]
    if entity_id == "1":
      continue
    entity_ids.append(entity_id)
  return entity_ids


def query_eb_stats(self, entity_id, entity_type):
  """
    EB stats query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  end_time = int(time.time()) * 1000000
  start_time = end_time - 3600000

  if entity_type == "vms":
    payload = {"entity_type": "vm", "entity_ids": [entity_id],
               "group_member_attributes":
                 [{"attribute": "hypervisor_cpu_usage_ppm"}],
               "interval_start_ms": start_time,
               "interval_end_ms": end_time,
               "downsampling_interval": 30,
               "query_name": "prism:EBStatsModel"}
  elif entity_type == "clusters":
    payload = {"entity_type": "cluster", "entity_ids": [entity_id],
               "group_member_attributes":
                 [{"attribute": "hypervisor_cpu_usage_ppm"},
                  {"attribute": "hypervisor_memory_usage_ppm"},
                  {"attribute": "controller_num_iops"},
                  {"attribute": "controller_io_bandwidth_kBps"},
                  {"attribute": "controller_avg_io_latency_usecs"}],
               "interval_start_ms": start_time,
               "interval_end_ms": end_time,
               "downsampling_interval": 30,
               "query_name": "prism:EBStatsModel"}
  elif entity_type == "projects":
    payload = {"entity_type": "project", "entity_ids": [entity_id],
               "group_member_attributes":
                 [{"attribute": "vcpus_count"},
                  {"attribute": "memory_bytes"},
                  {"attribute": "storage_bytes"}],
               "interval_start_ms": start_time,
               "interval_end_ms": end_time,
               "downsampling_interval":3600,
               "query_name":"prism:EBStatsModel"}

  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ +  '/' + entity_type +
         '/details/prism:EBStatsModel')


def query_base_group_model_name(self, entity_id, entity_type):
  """
    Base group model query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  payload = {}
  if entity_type == "vms":
    payload = {"entity_type": "vm", "entity_ids": [entity_id],
               "group_member_attributes":
                 [{"attribute": "vm_name"},
                  {"attribute": "description"},
                  {"attribute": "power_state"},
                  {"attribute": "capacity.vm_efficiency_status"},
                  {"attribute": "capacity.vm_efficiency_detail"},
                  {"attribute": "project_name"},
                  {"attribute": "owner_username"},
                  {"attribute": "ip_addresses"},
                  {"attribute": "memory_size_bytes"},
                  {"attribute": "num_vcpus"},
                  {"attribute": "capacity_bytes"},
                  {"attribute": "num_network_adapters"},
                  {"attribute": "gpu_type"},
                  {"attribute": "configured_gpu_list"},
                  {"attribute": "guest_driver_version"},
                  {"attribute": "state"},
                  {"attribute": "is_cvm"},
                  {"attribute": "hypervisor_type"},
                  {"attribute": "is_acropolis_vm"},
                  {"attribute": "cluster"}],
               "query_name": "prism:BaseGroupModel"}
  elif entity_type == "clusters":
    payload = {"entity_type": "cluster", "entity_ids": [entity_id],
               "group_member_attributes":
                 [{"attribute": "cluster_name"},
                  {"attribute": "check.overall_score"},
                  {"attribute": "capacity.runway"},
                  {"attribute": "version"},
                  {"attribute": "hypervisor_types"},
                  {"attribute": "num_vms"},
                  {"attribute": "num_nodes"},
                  {"attribute": "external_ip_address"}],
               "query_name": "prism:BaseGroupModel"}
  elif entity_type == "projects":
    payload = {"entity_type": "project", "entity_ids": [entity_id],
               "group_member_attributes":
                 [{"attribute": "name"},
                  {"attribute": "vms_count"},
                  {"attribute": "user_reference_list"},
                  {"attribute": "user_group_reference_list"},
                  {"attribute": "network_id_list"},
                  {"attribute": "vcpus_count"},
                  {"attribute": "memory_bytes"},
                  {"attribute": "storage_bytes"},
                  {"attribute": "description"},
                  {"attribute": "vcpus_count_limit"},
                  {"attribute": "memory_bytes_limit"},
                  {"attribute": "storage_bytes_limit"},
                  {"attribute": "is_default"}],
               "query_name": "prism:BaseGroupModel"}
  elif entity_type == "roles":
    payload = {"entity_type": "role", "entity_ids": [entity_id],
               "group_member_attributes":
                 [{"attribute": "name"},
                  {"attribute": "assigned_users_count"},
                  {"attribute": "assigned_user_groups_count"}],
               "query_name":"prism:BaseGroupModel"}

  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ + '/' + entity_type +
         '/details/prism:BaseGroupModel_name')


def query_base_group_model_msg(self, entity_id, entity_type):
  """
    Base group model query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  payload = {"entity_type": entity_type, "entity_ids": [entity_id],
             "group_member_attributes":
               [{"attribute": "message"}, {"attribute": "state"},
                {"attribute": "reason"}],
             "query_name": "prism:BaseGroupModel"}
  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ +  '/' + entity_type +
         '/details/prism:BaseGroupModel_msg')


def query_base_group_model_project_reference(self, entity_id, entity_type):
  """
    Base group model query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  payload = {"entity_type": "abac_entity_capability",
             "group_member_attributes":
               [{"attribute": "kind"},
                {"attribute": "kind_id"},
                {"attribute": "owner_username"},
                {"attribute": "project_name"},
                {"attribute": "project_reference"}],
             "query_name": "prism:BaseGroupModel",
             "filter_criteria": "project_reference==" + entity_id + ";kind==vm"}
  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ +  '/' + entity_type +
         '/details/prism:BaseGroupModel_project_reference')


def query_base_group_model_catid(self, entity_id, entity_type):
  """
    Base group model query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  payload = {"entity_type": "project", "entity_ids": [entity_id],
             "group_member_attributes": [{"attribute": "category_id"}],
             "query_name":"prism:BaseGroupModel"}
  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ +  '/' + entity_type +
         '/details/prism:BaseGroupModel_catid')


def query_base_group_model_network(self, entity_id, entity_type):
  """
    Base group model query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  payload = {"entity_type": "virtual_network", "entity_ids": [entity_id],
             "group_member_attributes": [{"attribute": "name"}],
             "query_name":"prism:BaseGroupModel"}
  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ +  '/' + entity_type +
         '/details/prism:BaseGroupModel_network')


def query_base_group_model_abac(self, entity_id, entity_type):
  """
    Base group model query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  payload = {"entity_type": "abac_user_capability", "entity_ids": [entity_id],
             "group_member_attributes":
               [{"attribute": "display_name"},
                {"attribute": "category_id_list"},
                {"attribute": "user_uuid"},
                {"attribute": "username"},
                {"attribute": "projects_count"},
                {"attribute": "vms_count"},
                {"attribute": "vcpus_count"},
                {"attribute": "memory_bytes"},
                {"attribute": "storage_bytes"}],
             "query_name": "prism:BaseGroupModel"}
  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ +  '/' + entity_type +
         '/details/prism:BaseGroupModel_abac')


def query_base_group_model_user_uuid(self, entity_id, entity_type):
  """
    Base group model query

    Args:
      entity_id(str): entity id
      entity_type(str): entity type

    Returns:
      None
  """
  c = self.client
  payload = {"entity_type": "abac_user_capability", "entity_ids": [entity_id],
             "group_member_attributes": [{"attribute":"user_uuid"}],
             "query_name":"prism:BaseGroupModel"}
  c.post(V3 + 'groups', data=json.dumps(payload),
         name=self.__class__.__name__ +  '/' + entity_type +
         '/details/prism:BaseGroupModel_user_uuid')

def get_spec(vm_name, cluster_name):
  """
  Get spec with vm name provided

  Args:
    vm_name(str): vm name
    cluster_name(str): cluster name

  Returns:
    payload
  """
  payload = {
    "spec": {
      "name": vm_name,
      "cluster_reference": {
        "kind": "cluster",
        "uuid": CLUSTERINFO[cluster_name]
      },
      "resources": {
        "power_state": "OFF",
        "num_vcpus_per_socket": 1,
        "num_sockets": 1,
        "memory_size_mib": 1,
        "power_state_mechanism": {
          "mechanism": "HARD"
        },
        "disk_list": [{
          "device_properties": {
            "device_type": "CDROM",
            "disk_address": {
              "adapter_type": "IDE",
              "device_index": 0
            }
          }
        }],
        "nic_list": [{
          "subnet_reference": {
            "uuid": VMNICINFO[cluster_name],
            "kind": "subnet"
          }
        }]
      }
    },
    "metadata": {
      "kind": "vm"
    },
    "api_version": "3.1.0"
  }
  return payload

def create_vm(self, cluster_name, vm_name):
  """
  Create vm based on spec from get_spec

  Args:
    cluster_name(str): cluster name
    vm_name(str): vm name

  Returns:
    vm_uuid
  """
  payload = get_spec(vm_name, cluster_name)
  resp = self.client.request('POST', "{}".format(VMS_URL), json=payload,
                             name="CREATE VMs")
  if not resp.ok:
    return ""
  else:
    resp = json.loads(resp.content)
    return resp["metadata"]["uuid"]

def group_vm(self):
  """
  group api call on vm

  Returns:
    None
  """
  url = "api/nutanix/v3/groups"
  data = {
    "entity_type": "vm",
    "group_member_sort_attribute": "vm_name",
    "group_member_sort_order": "ASCENDING",
    "group_member_attributes": [{
      "attribute": "vm_name"
    }],
    "filter_criteria": "is_cvm==0;"
                       "vm_name==.*[a|A][p|P][i|I][t|T][e|E][s|S][t|T].*"
  }

  groups_resp = self.client.request('POST', url, json=data, name="Groups_VM")
  if not groups_resp.ok:
    return

def get_vm(self, vm_uuid):
  """
  Get api call on vm with vm uuid

  Args:
    vm_uuid(str): vm uuid

  Returns:
    resp for getting vm call
  """
  get_resp = self.client.request('GET', "{}/{}".format(VMS_URL, vm_uuid),
                                 name="GET_VM")
  return get_resp

def get_vm_recursive(self, vm_uuid):
  """
  Get api call recusively on vm with vm uuid

  Args:
    vm_uuid(str): vm uuid

  Returns:
    resp for getting vm call
  """
  start = time.time()
  get_resp = get_vm(self, vm_uuid)
  get_resp = json.loads(get_resp.content)
  get_state = get_resp["status"]["state"]
  while get_state.upper() != "COMPLETE":
    get_resp = get_vm(self, vm_uuid)
    get_resp = json.loads(get_resp.content)
    get_state = get_resp["status"]["state"]
    end = time.time()
    if end - start > TIMEOUT:
      break
  return get_resp

def update_vm(self, get_resp, vm_uuid):
  """
  Update vm with new name

  Args:
    get_resp(json): response from getting vm call
    vm_uuid(str): vm uuid

  Returns:
    resp for updating vm call
  """
  spec = get_resp['spec']
  metadata = get_resp['metadata']
  metadata.pop('last_update_time')
  metadata.pop('creation_time')

  # Update name
  spec["name"] = "apitest-update" + ""\
      .join(random.sample(string.lowercase + string.digits, 5))
  payload = {
    "spec": spec,
    "api_version": "3.1",
    "metadata": metadata
  }
  put_resp = self.client.request('PUT', "{}/{}".format(VMS_URL, vm_uuid),
                                 json=payload, name="PUT_VMS")
  return put_resp

def _print(user_spawned, text):
  """
  Just customized print
  Args:
    user_spawned(str): name of the user
    text(str): text to be appended to user

  Returns:
    None
  """
  if user_spawned is None:
    user_spawned = ''
  message = "[{0}]: [{1}]".format(user_spawned, text)
  print (message)
