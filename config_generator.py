"""
Copyright (c) 2018 Nutanix Inc. All rights reserved.
Author: dhruvil.patel@nutanix.com
"""
# pylint: disable=too-many-locals
# pylint: disable=too-many-return-statements
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=too-many-lines
# pylint: disable=relative-import
# pylint: disable=too-many-nested-blocks
# pylint: disable=invalid-name

import os
import sys
import json
import uuid
import copy
import time
import random
from helpers import id_generator, _print

V3 = 'api/nutanix/v3/'
CALM_V3 = 'api/calm/v3.0/'
PRISM_V2_A1 = 'api/prism/v2.a1/'
CONFIG_FOLDER = os.path.join(os.path.dirname(__file__), "../", "config")
DEFAULT_AHV_BLUEPRINT_INSTANCE_NAME = "ahv_bp_vm"
DEFAULT_AHV_BLUEPRINT_LINUX_IMAGE_NAME = "Centos7HadoopMaster"
DEFAULT_AHV_BLUEPRINT_WINDOWS_IMAGE_NAME = "WindowsServer2016"
DEFAULT_AHV_BLUEPRINT_DISK_TYPE = "DISK"
DEFAULT_AHV_BLUEPRINT_DEVICE_BUS = "SCSI"
DEFAULT_AHV_BLUEPRINT_NIC = "vlan.501"
DEFAULT_LOCAL_NUTANIX_ACCOUNT_NAME = "NTNX_LOCAL_AZ"

DEFAULT_AWS_BLUEPRINT_INSTANCE_NAME = "aws_ins_delete"
DEFAULT_SHUTDOWN_BEHAVIOUR = "TERMINATE"
DEFAULT_AWS_BLUEPRINT_INSTANCE_TYPE = "t2.nano"
DEFAULT_AWS_BLUEPRINT_REGION = "us-east-1"
DEFAULT_AWS_AVAILABLE_ZONE = "us-east-1a"
DEFAULT_AWS_BLUEPRINT_LINUX_IMAGE_NAME = "DND_CENTOS_QA"
DEFAULT_AWS_BLUEPRINT_WINDOWS_IMAGE_NAME = "WindowsServer2016"
DEFAULT_AWS_BLUEPRINT_IAM_ROLE = ""
DEFAULT_AWS_BLUEPRINT_KEY_PAIR = "calm-blueprints"
DEFAULT_AWS_VPC_CIDR_BLOCK = "10.0.0.0/16"
DEFAULT_AWS_VPC_ID = "vpc-ffd54d98"
DEFAULT_AWS_SECURITY_GROUP_NAME = "DEMO"
DEFAULT_AWS_LINUX_ROOT_DISK_SIZE = 10
DEFAULT_AWS_WINDOWS_ROOT_DISK_SIZE = 30
DEFAULT_AWS_DISK_VOLUME_TYPE = "General_Purpose_SSD"
# for volume types here spaces are replaced by '_'
AWS_DISK_VOLUME_TYPES_MAP = {
  "General_Purpose_SSD": "GP2",
  "Provisioned_IOPS_SSD": "IO1",
  "Cold_HDD": "SC1",
  "Throughput_Optimized_HDD": "ST1",
  "EBS_Magnetic_HDD": "STANDARD"
}

NUCALM_VMWARE_ACCOUNT_NAME = "vmware_account"
DEFAULT_VMWARE_BLUEPRINT_INSTANCE_NAME = "vmw_ins_delete"
DEFAULT_VMWARE_BLUEPRINT_HOST_NAME = "10.46.211.8"
DEFAULT_VMWARE_BLUEPRINT_TEMPLATE_NAME = "centos_without_nic"
DEFAULT_VMWARE_BLUEPRINT_DATASTORE_NAME = "default-container-115847"

#DEFAULT_VMWARE_BLUEPRINT_DATASTORE_NAME = "default-container-46308"

#Temp changes for CalmVM task
#DEFAULT_VMWARE_BLUEPRINT_HOST_NAME = "10.46.211.43"
#DEFAULT_VMWARE_BLUEPRINT_TEMPLATE_NAME = "DND_Centos_without_nic"
#DEFAULT_VMWARE_BLUEPRINT_DATASTORE_NAME = "default-container-103294"

DEFAULT_VMWARE_BLUEPRINT_GUEST_HOST_NAME = "host-" + id_generator(8)
DEFAULT_VMWARE_BLUEPRINT_GUEST_DOMAIN = "nutanix.com"
DEFAULT_VMWARE_BLUEPRINT_DNS_PRIMARY = "10.4.8.15"
DEFAULT_VMWARE_BLUEPRINT_DNS_SECONDARY = "10.1.1.100"
DEFAULT_VMWARE_BLUEPRINT_DNS_SEARCH_PATH = "eng.nutanix.com qa.nutanix.com"

DEFAULT_GCP_BLUEPRINT_INSTANCE_NAME = "gcp-ins-delete"
DEFAULT_GCP_ACCOUNT_NAME = "gcp_account"
DEFAULT_GCP_BLUEPRINT_ZONE_NAME = "us-east1-b"
DEFAULT_GCP_BLUEPRINT_MACHINE_TYPE = "f1-micro"
DEFAULT_GCP_SSH_KEYS = ["ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCRaWr8SHO30knQvWAgoX526w7N85Un/4mxP9FDHvjknbTU0r1RuOCls9JM88tFJSz1i9U6EJLEzRsjaKm0eBaQ8/ZMhJdGXzOCmDDrhgbc+sNk2+tUpW+51zZ/oSyMVjREOC4GMNkSK98NEAqCLvvsGB1LJcnAfkcB2EqAlnPbPNWnX9f4LpmjYFQnwWOstrgEztTx6Si8HEHC17x1Qcc0w0KfHFwHuBWw6747XKuEyoCiYx3GzmvKInsqAZf+LWWR2d1miAx4MJay2BQDoOKYb3jogx7t7KP7KjESlDZu0l/EQrCoErcxoFWCf5RkPhXtIoDJMmp/BtYvNVC6Cb01 harsha.deshpande@C02TN07WHF1Q"]

DEFAULT_AZURE_BLUEPRINT_INSTANCE_NAME = "a"
DEFAULT_AZURE_ACCOUNT_NAME = "azure_account"
DEFAULT_AZURE_RESOURCE_GROUP_NAME = "calmrg"
DEFAULT_AZURE_LOCATION_NAME = "eastus2"
DEFAULT_AZURE_AVAILABILITY_SET_NAME = "STAvailabilitySet"
DEFAULT_AZURE_VM_SIZE_NAME = "Basic_A0"
DEFAULT_AZURE_IMAGE_PUBLISHER_NAME = "Canonical"
DEFAULT_AZURE_IMAGE_OFFER_NAME = "UbuntuServer"
DEFAULT_AZURE_IMAGE_SKU = "19.04"
DEFAULT_AZURE_IMAGE_VERSION = "19.04.201908140"
DEFAULT_AZURE_DISK_NAME = "os"
DEFAULT_AZURE_STORAGE_TYPE = "Standard"
DEFAULT_AZURE_DISK_CACHING_TYPE = "ReadWrite"
DEFAULT_AZURE_DISK_CREATE_OPTION = "FromImage"
DEFAULT_AZURE_DISK_SIZE = 30
DEFAULT_AZURE_NIC_NAME = "nic"
DEFAULT_AZURE_SECURITY_GROUP = "sg-allow-all-eastus2"
DEFAULT_AZURE_VIRTUAL_NETWORK = "calm-virtual-network-eastus2"
DEFAULT_AZURE_SUBNET_NAME = "default"
DEFAULT_AZURE_PUBLIC_IP_NAME = "public-ip"
DEFAULT_AZURE_PUBLIC_IP_ALLOCATION_METHOD = "Dynamic"
DEFAULT_AZURE_PUBLIC_IP_DNS_LABEL = "dns"
DEFAULT_AZURE_PRIVATE_IP_ALLOCATION_METHOD = "Dynamic"
DEFAULT_AZURE_WIN_IMAGE_PUBLISHER_NAME = "MicrosoftWindowsServer"
DEFAULT_AZURE_WIN_IMAGE_OFFER_NAME = "WindowsServer"
DEFAULT_AZURE_WIN_IMAGE_SKU = "2019-Datacenter-smalldisk"
DEFAULT_AZURE_WIN_IMAGE_VERSION = "2019.0.20190214"

NUCALM_KUBERNETES_ACCOUNT_NAME = "kubernetes_account"
NUCALM_KUBERNETES_RESTARTPOLICY = "Always"
NUCALM_KUBERNETES_NAMESPACE = "default"
NUCALM_KUBERNETES_IMAGE = "nginx"
NUCALM_KUBERNETES_PACKAGE_TYPE = "K8S_IMAGE"
NUCALM_KUBERNETES_LABELS = {
  "test": "test"
}
NUCALM_KUBERNETES_SELECTORS = {
  "test": "test"
}

NUCALM_AWS_ACCOUNT_NAME = "aws_account"
DEFAULT_EM_IP_ADDRESS = "10.46.1.78"
DEFAULT_EM_WIN_IP_ADDRESS = "10.46.8.92"
DEFAULT_CREDENTIAL_NAME = "root"
DEFAULT_CREDENTIAL_USERNAME = "root"
DEFAULT_CREDENTIAL_TYPE = "PASSWORD"
DEFAULT_CREDENTIAL_PASSWORD = "nutanix/4u"
DEFAULT_APP_PROFILE_NAME = "Default"
DEFAULT_NUM_OF_REPLICAS = "1"
DEFAULT_MIN_REPLICAS = "1"
DEFAULT_MAX_REPLICAS = "100"

DEFAULT_WINDOWS_PORT = 5985
DEFAULT_LINUX_PORT = 22
DEFAULT_LINUX_PACKAGE_TYPE = "DEB"
DEFAULT_WINDOWS_PACKAGE_TYPE = "DEB"

DEFAULT_CALM_ST_ADMIN_USER = "st-sspadmin@systest.nutanix.com"
DEFAULT_CALM_DIRECTORY = "ST_AUTO_PC_AD"

DEFAULT_APP_PROFILE = [
  {
    "name": "Default"
  }
]

CREDENTIALS_FILE = 'credentials.json'

DEAFULT_HTTP_ATTRIBUTES = {
  "connection_timeout": 120,
  "retry_count": 1,
  "retry_interval": 10,
  "tls_verify": True,
  "url": "https://www.geeksforgeeks.org/"
}

DEFAULT_ROLE_ENTITY_MAP = {
  'Project Admin': ['image', 'marketplace_item', 'directory_service', 'role',
                    'project', 'user', 'user_group', 'environment', 'app_icon',
                    'category', 'app_task', 'app_variable',
                    'identity_provider'],
  'Developer': ['image', 'marketplace_item', 'app_icon', 'category', 'app_task',
                'app_variable'],
  'Consumer': ['image', 'marketplace_item', 'app_icon', 'category', 'app_task',
               'app_variable'],
  'Operator': []
}

DEFAULT_MEMORY_SIZE = 256
DEFAULT_VCPUS_PER_SOCKET = 5
DEFAULT_SOCKETS = 2

DEFAULT_QUOTA_DISK = 107374182400000
DEFAULT_QUOTA_VCPU = 1000
DEFAULT_QUOTA_MEMORY = 1073741824000

def response_check(response, status_code=200):
  """
  This method checks the response if it is correct
  Args:
    response(dict): response of API call
    status_code(int): status code to check
  Returns:
    whole content of response else None
  """
  if response.status_code == status_code:
    response = json.loads(response.content)
    return response
  print("Response failed with status code [{0}]".format(response.status_code))
  print(response.content)
  return None

def get_list(**kwargs):
  """
  This method returns the list of entities required
  Args:
    kwargs:
      self: self object
      url(str): url for the API call
      payload(dict): payload for API call
      recall(bool): recall the api if it fails
      calm_v3(bool): calm api or not
      user_spawned(str): name of the user spawned

  Returns:
    list of entities required
  """
  self = kwargs.get('self')
  url = kwargs.get('url')
  payload = kwargs.get('payload', {})
  calm_v3 = kwargs.get('calm_v3', False)
  return_total_resp = kwargs.get('return_total_resp', False)
  user_spawned = kwargs.get('user_spawned', '')

  url = CALM_V3 + url if calm_v3 else V3 + url
  for count in range(10):
    response = self.client.post(url, data=json.dumps(payload))
    response = response_check(response)
    if response is None:
      _print(user_spawned, "Error in response of url - [{0}] "
             "recalling again after 3sec sleep : loop count [{1}]"
             .format(url, count))
      time.sleep(3)
      continue
    if return_total_resp:
      return response
    return response['entities']
  _print(user_spawned, "Error in response of url - [{0}]".format(url))
  return None

def get_calm_list(self, **kwargs):
  """
  This method returns the list of entities required
  Args:
    kwargs:
      self: self object
      url(str): url for the API call
      payload(dict): payload for API call

  Returns:
    list of entities required
  """
  url = kwargs.get('url')
  payload = kwargs.get('payload')

  response = self.client.post(CALM_V3 + url, data=json.dumps(payload))
  response = response_check(response)
  if response is None:
    print("Error in response of url - [{}]".format(url))
    return None
  return response['search_result_list']

def get_grouped_list(**kwargs):
  """
  This method returns the list of entity uuids and attributes which are passed
  Args:
    kwargs:
      self: self object
      query_name: query name
      entity_type: type of entity
      user_spawned(str): name of the user spawned
      attributes(list, optional): list of attributes
      filter_criteria(str): filters criteria for entity

  Returns:
    list of entity info object
  """
  self = kwargs.get('self')
  length = kwargs.get('length', 20)
  entity_type = kwargs.get('entity_type')
  attributes = kwargs.get('attributes', [])
  query_name = kwargs.get('query_name', None)
  user_spawned = kwargs.get('user_spawned', '')
  filter_criteria = kwargs.get('filter_criteria', '')
  group_attributes = kwargs.get('group_attributes', [])
  grouping_attribute = kwargs.get('grouping_attribute', None)
  group_member_sort_attribute = kwargs.get('group_member_sort_attribute', None)
  group_result = kwargs.get('group_result', False)

  payload = {
    "entity_type": "",
    "group_member_attributes": [],
    "filter_criteria": "",
    "group_member_offset": 0,
    "group_member_count": length,
    "group_attributes": group_attributes
  }

  if query_name:
    payload['query_name'] = query_name
  if filter_criteria:
    payload['filter_criteria'] = filter_criteria
  if grouping_attribute:
    payload['grouping_attribute'] = grouping_attribute
  if group_member_sort_attribute:
    payload['group_member_sort_attribute'] = group_member_sort_attribute

  payload['entity_type'] = entity_type
  for attribute in attributes:
    payload['group_member_attributes'].append({'attribute': attribute})

  response = self.client.post(V3 + 'groups', data=json.dumps(payload))

  response = response_check(response)
  if response is None:
    _print(user_spawned, "Error in response of group call")
    return None

  if len(response['group_results'][0]['entity_results']) == 0:
    _print(user_spawned, "Error: Group entity results list is empty")
    return None

  if group_result:
    return response['group_results']

  return response['group_results'][0]['entity_results']

def get_entity(**kwargs):
  """
  This method returns the list of entities required
  Args:
    kwargs:
      self: self object
      url(str): url for the API call
      payload(dict): payload for API call
      user_spawned(str): name of the user spawned

  Returns:
    entities required
  """
  self = kwargs.get('self')
  url = kwargs.get('url')
  user_spawned = kwargs.get('user_spawned', '')
  api_name = kwargs.get('api_name', url)

  response = self.client.get(V3 + url, name=self.__class__.__name__ + api_name)
  response = response_check(response)
  if response is None:
    _print(user_spawned, "Error in response of url - [{0}]".format(url))
    return None
  return response

def get_role_uuid_pair(self):
  """
  This method returns dist of roles and its uuids
  Args:
  Returns:
    dict of roles and uuids
  """
  roles_list = get_list(self=self, url='roles/list', user_spawned='',
                        payload={
                          "length": 1000,
                          "offset": 0,
                          "kind":"role"
                        })

  roles_pair = {}
  for role in roles_list:
    roles_pair[role['spec']['name']] = role['metadata']['uuid']
  return roles_pair

def call_projects_list_consumption_api(self, user_spawned):
  """
  This method calls the projects list consumption api
  Args:
    user_spawned(str): name of the user spawned

  Returns:
    True if called successfully else False.
  """
  project_list = get_list(self=self, url="projects/list", payload={},
                          user_spawned=user_spawned)
  if project_list is None:
    return False

  payload_for_project_consumption = {
    "time_unit": "month",
    "filters": {
      "entity_ids": []
    }
  }
  project_uuid_list = []
  for _proj in project_list:
    project_uuid_list.append(_proj['metadata']['uuid'])
  payload_for_project_consumption['filters']['entity_ids'] = \
    project_uuid_list
  _print(user_spawned, "Calling projects_list_consumption_api")
  project_consumption_api = self.client.post(
    V3 + "projects/consumption_list",
    data=json.dumps(payload_for_project_consumption),
    name=self.__class__.__name__ + '/projects_list_consumption_api')
  if project_consumption_api.status_code != 200:
    _print(user_spawned, "WARN: projects_list_consumption_api call failed "
                         "with status code: [{0}]".
           format(str(project_consumption_api.status_code)))
    return False
  return True

def generate_payload_for_creating_blueprint(self, **kwargs):
  """
  generates payload for the blueprint create from spec file,
  spec file name should be provided and should be in
  systest/config/nucalm folder
  Args:
    kwargs:
      blueprint_type(str, optional): Type of the blueprint to be created
      blueprint_name(str): name of blueprint
      api_version(str): api version used
      project_name(str): name of project
      vm_type(str): type of vm (single or multi)
      spec_file(str): name of json file containing all the parameters for
        creating blueprint
      user_spawned(str): name of the user spawned
      show_consumption_api(boolean, optional): indicates whether to show
        consumption API
        NOTE: default values is False.
      num_of_services_per_bp(int): no.of services per bp
      clone_from_environments(bool): clone from environment
      account_names(dict): specific account names if required
      no_of_app_profiles(int): no.of app_profiles in bp
      num_of_replicas(str): number of replicas per service in BP
      num_configs_per_service(int): no.of configs per service

  Returns:
    payload(dict): payload for creating blueprint
  """
  blueprint_name = kwargs.get('blueprint_name')
  project_name = kwargs.get('project_name')
  spec_file = kwargs.get('spec_file')
  os_types = kwargs.get('os_types')
  workflows = kwargs.get('workflows')
  vm_type = kwargs.get('vm_type', 'multi')
  vlan_names_list = kwargs.get('vlan_names_list', [])
  blueprint_type = kwargs.get('blueprint_type', 'USER')
  user_spawned = kwargs.get('user_spawned', '')
  num_of_services_per_bp = kwargs.get('num_of_services_per_bp')
  show_consumption_api = kwargs.get('show_consumption_api', False)
  clone_from_environments = kwargs.get('clone_from_environments', False)
  account_names = kwargs.get('account_names', {})
  no_of_app_profiles = kwargs.get('no_of_app_profiles')
  num_of_replicas = kwargs.get('num_of_replicas', '1')
  scaling_count = kwargs.get('scaling_count', '2')
  linux_guest_customization_delay = \
    kwargs.get('linux_guest_customization_delay', '60')
  windows_guest_customization_delay = \
    kwargs.get('windows_guest_customization_delay', '60')
  no_of_categories = kwargs.get('no_of_categories', 1)
  spec_edit = kwargs.get('spec_edit', False)
  num_configs_per_service = kwargs.get('num_configs_per_service', 1)

  payload = {
    "api_version": kwargs.get('api_version'),
    "metadata": {
      "kind": "blueprint",
      "project_reference": {
        "kind": "project",
        "uuid": ""
      },
      "uuid": str(uuid.uuid4())
    },
    "spec": {
      "resources": {
        "type": blueprint_type,
        "client_attrs": {},
        "app_profile_list": [],
        "substrate_definition_list": [],
        "credential_definition_list": [],
        "published_service_definition_list": [],
        "service_definition_list": [],
        "package_definition_list": []
      },
      "name": blueprint_name
    }
  }
  # Step 1: add project uuid
  project_list = get_grouped_list(self=self, entity_type='project', length=1001,
                                  attributes=['name', 'environment_id_list'],
                                  user_spawned=user_spawned)
  if project_list is None:
    return None
  if show_consumption_api:
    called = call_projects_list_consumption_api(self, user_spawned)
    if not called:
      _print(user_spawned, "ERROR: Unable to call projects_list "
                           "consumption API")

  project = None
  for project_obj in project_list:
    for attribute in project_obj['data']:
      if attribute['name'] == 'name':
        if attribute['values'][0]['values'][0] == project_name:
          project = project_obj
          break
    if project is not None:
      break

  if project is None:
    _print(user_spawned, "Project [{0}] not found".format(project_name))
    return None
  payload['metadata']['project_reference']['uuid'] = \
    project['entity_id']

  # Step 2: complete adding spec
  spec_file = generate_spec_file(num_of_services_per_bp=num_of_services_per_bp,
                                 workflows=workflows, os_types=os_types,
                                 no_of_app_profiles=no_of_app_profiles,
                                 account_names=account_names,
                                 num_of_replicas=num_of_replicas,
                                 scaling_count=scaling_count)

  # Step 2a: adding credentials
  credentials_to_be_added = spec_file.get('credential_list', [])
  credential_list = add_credentials(credentials_to_be_added, user_spawned)
  if credential_list is None:
    return None
  payload['spec']['resources']['credential_definition_list'] = credential_list

  # Step 2b: adding default credential
  default_credential_name = \
    spec_file.get('default_credential_name', DEFAULT_CREDENTIAL_NAME)
  default_credential_uuid = \
    next((credential.get('uuid') for credential in credential_list
          if credential.get('name') == default_credential_name), None)
  if default_credential_uuid is None:
    _print(user_spawned, "Default credential with name [{0}] not found". \
      format(default_credential_name))
    return None
  if len(credential_list) != 0:
    default_credential_local_reference = {
      "kind": "app_credential",
      "name": "default_credential",
      "uuid": ""
    }
    payload['spec']['resources']['default_credential_local_reference'] = \
      default_credential_local_reference
    payload['spec']['resources']['default_credential_local_reference'][
      'uuid'] = default_credential_uuid

  published_services_to_be_added = spec_file.get('published_services', [])
  if len(published_services_to_be_added) > 0:
    published_services_list = add_published_services(
      published_services_to_be_added=published_services_to_be_added,
      user_spawned=user_spawned)
    if published_services_list is None:
      return None
    payload['spec']['resources']['published_service_definition_list'] = \
      published_services_list
  else:
    published_services_list = []

  # Step 2d: adding services
  services_to_be_added = spec_file.get('service', [])
  service_list = add_services(services_to_be_added=services_to_be_added,
                              credential_list=credential_list,
                              user_spawned=user_spawned)
  if service_list is None:
    return None
  payload['spec']['resources']['service_definition_list'] = service_list

  # Step 2e: adding substrates
  vlan_list = []
  if len(vlan_names_list) != 0:
    for vlan_name in vlan_names_list:
      vlan_list.append({'name': vlan_name})

  substrates_to_be_added = spec_file.get('substrate', [])
  project_uuid = payload['metadata']['project_reference']['uuid']
  if clone_from_environments:
    for attribute in project['data']:
      if attribute['name'] == 'environment_id_list':
        environment_list = attribute['values'][0]['values']
    environment_uuid = random.choice(environment_list)
    substrate_list = get_substrates_from_environment(self, environment_uuid= \
      environment_uuid, workflows=workflows, credential_list=credential_list, \
      os_types=os_types, num_of_services_per_bp=num_of_services_per_bp)
    if len(substrates_to_be_added) > 0:
      for deployment in spec_file['deployment_list']:
        for count, substrate in enumerate(substrate_list):
          deployment['deployments'][count]['substrate_name'] = substrate['name']
      for app_pro in spec_file['app_profile']:
        for count, substrate in enumerate(substrate_list):
          for action in app_pro['action']:
            action['task'][0]['substrate_name'] = substrate['name']

  else:
    substrate_list = \
      add_substrates(self=self, substrates_to_be_added=substrates_to_be_added,
                     service_list=service_list, credential_list=credential_list,
                     blueprint_name=blueprint_name, user_spawned=user_spawned,
                     vm_type=vm_type, vlan_list=vlan_list,
                     project_uuid=project_uuid,
                     linux_guest_customization_delay= \
                     linux_guest_customization_delay,
                     windows_guest_customization_delay=\
                     windows_guest_customization_delay,
                     no_of_categories=no_of_categories,
                     spec_edit=spec_edit)
  if substrate_list is None:
    return None
  payload['spec']['resources']['substrate_definition_list'] = substrate_list

  # Step 2f: adding packages
  packages_to_be_added = spec_file.get('package', [])
  package_list = add_packages(packages_to_be_added=packages_to_be_added,
                              service_list=service_list,
                              credential_list=credential_list,
                              user_spawned=user_spawned)
  if package_list is None:
    return None
  payload['spec']['resources']['package_definition_list'] = package_list

  # Step 2g: adding app_profiles
  deployments_list_to_be_added = spec_file.get('deployment_list', [])
  app_profiles_to_be_added = spec_file.get('app_profile', [])
  app_profile_list = \
    add_app_profiles(app_profiles_to_be_added=app_profiles_to_be_added,
                     credential_list=credential_list, vm_type=vm_type,
                     deployment_list=deployments_list_to_be_added,
                     substrate_list=substrate_list, package_list=package_list,
                     published_services_list=published_services_list,
                     num_of_replicas=num_of_replicas, user_spawned=user_spawned,
                     spec_edit=spec_edit,
                     num_configs_per_service=num_configs_per_service)
  if app_profile_list is None:
    return None
  if clone_from_environments:
    for app_profile in app_profile_list:
      app_profile['environment_reference_list'].append(environment_uuid)

  payload['spec']['resources']['app_profile_list'] = app_profile_list

  # Step 2h: adding client_attrs
  client_attrs = add_client_attrs(service_list=service_list)
  payload['spec']['resources']['client_attrs'] = client_attrs
  return payload

def generate_payload_for_single_vm_blueprint(self, **kwargs):
  """
  generates payload for the blueprint create from spec file,
  spec file name should be provided and should be in
  systest/config/nucalm folder
  Args:
    kwargs:
      blueprint_type(str, optional): Type of the blueprint to be created
      blueprint_name(str): name of blueprint
      api_version(str): api version used
      project_name(str): name of project
      vm_type(str): type of vm (single or multi)
      cloud(str): type of cloud for single vm
      vlan_names_list(list, optional): list of vlan names
      spec_file(str): name of json file containing all the parameters for
        creating blueprint
      user_spawned(str): name of the user spawned
      show_consumption_api(boolean, optional): indicates whether to show
        consumption API
        NOTE: default values is False.

  Returns:
    payload(dict): payload for creating blueprint
  """
  blueprint_name = kwargs.get('blueprint_name')
  project_name = kwargs.get('project_name')
  spec_file = kwargs.get('spec_file')
  vm_type = kwargs.get('vm_type', 'multi')
  cloud = kwargs.get('cloud')
  vlan_names_list = kwargs.get('vlan_names_list', [])
  blueprint_type = kwargs.get('blueprint_type', 'USER')
  user_spawned = kwargs.get('user_spawned', '')
  show_consumption_api = kwargs.get('show_consumption_api', False)
  spec_edit = kwargs.get('spec_edit', False)
  num_configs_per_service = kwargs.get('num_configs_per_service', 1)

  payload = {
    "api_version": kwargs.get('api_version'),
    "metadata": {
      "kind": "blueprint",
      "project_reference": {
        "kind": "project",
        "uuid": ""
      },
      "categories":{
        "TemplateType": "Vm"
      },
      "uuid": ""
    },
    "spec": {
      "resources": {
        "type": blueprint_type,
        "client_attrs": {},
        "app_profile_list": [],
        "substrate_definition_list": [],
        "package_definition_list": []
      },
      "name": blueprint_name
    }
  }
  # Step 1: add project uuid
  project_list = get_grouped_list(self=self, entity_type='project', length=1001,
                                  attributes=['name', 'environment_id_list'],
                                  user_spawned=user_spawned)
  if project_list is None:
    return None
  if show_consumption_api:
    called = call_projects_list_consumption_api(self, user_spawned)
    if not called:
      _print(user_spawned, "ERROR: Unable to call projects_list "
                           "consumption API")

  project = None
  for project_obj in project_list:
    for attribute in project_obj['data']:
      if attribute['name'] == 'name':
        if attribute['values'][0]['values'][0] == project_name:
          project = project_obj
          break
    if project is not None:
      break

  if project is None:
    _print(user_spawned, "Project [{0}] not found".format(project_name))
    return None
  payload['metadata']['project_reference']['uuid'] = \
    project['entity_id']

  payload['metadata']['uuid'] = str(uuid.uuid4())

  # Step 2: complete adding spec
  spec_file_path = os.path.join(CONFIG_FOLDER, spec_file)
  try:
    json_file = open(spec_file_path)
  except IOError as file_not_found_error:
    _print(user_spawned, str(file_not_found_error))
    return None
  spec_file = json.load(json_file)

  # Step 2a: adding credentials
  credentials = spec_file.get('credential_list', [])
  credentials_to_be_added = credentials.get(cloud, [])
  credential_list = add_credentials(credentials_to_be_added, user_spawned)
  if credential_list is None:
    return None
  payload['spec']['resources']['credential_definition_list'] = credential_list
  default_credential_local_reference = {
    "kind": "app_credential",
    "name": "default_credential",
    "uuid": ""
  }
  payload['spec']['resources']['default_credential_local_reference'] = \
    default_credential_local_reference
  default_credential_name = credential_list[0]['name']
  default_credential_uuid = \
    next((credential.get('uuid') for credential in credential_list
          if credential.get('name') == default_credential_name), None)
  if default_credential_uuid is None:
    _print(user_spawned, "Default credential with name [{0}] not found". \
      format(default_credential_name))
    return None
  payload['spec']['resources']['default_credential_local_reference'][
    'uuid'] = default_credential_uuid

  # Step 2b: adding services
  services_to_be_added = spec_file.get('service', [])
  service_list = add_services(services_to_be_added=services_to_be_added,
                              credential_list=credential_list,
                              user_spawned=user_spawned)
  if service_list is None:
    return None

  payload['spec']['resources']['service_definition_list'] = service_list

  # Step 2c: adding substrates
  vlan_list = []
  if len(vlan_names_list) != 0:
    for vlan_name in vlan_names_list:
      vlan_list.append({'name': vlan_name})

  substrates_to_be_added = spec_file.get('substrate', [])
  substrates_to_be_added['type'] = cloud
  project_uuid = payload['metadata']['project_reference']['uuid']
  substrate_list = \
    add_substrates(self=self, substrates_to_be_added=substrates_to_be_added,
                   service_list=service_list, credential_list=credential_list,
                   user_spawned=user_spawned, vm_type=vm_type,
                   vlan_list=vlan_list, project_uuid=project_uuid,
                   spec_edit=spec_edit, no_of_categories=no_of_categories)
  if substrate_list is None:
    return None
  substrate_list[0]['readiness_probe']['login_credential_local_reference']\
    ['kind'] = default_credential_local_reference['kind']
  substrate_list[0]['readiness_probe']['login_credential_local_reference']\
    ['uuid'] = default_credential_local_reference['uuid']
  payload['spec']['resources']['substrate_definition_list'] = substrate_list

  # Step 2d: adding packages
  packages_to_be_added = spec_file.get('package', [])
  package_list = add_packages(packages_to_be_added=packages_to_be_added,
                              service_list=service_list, cloud=cloud,
                              credential_list=credential_list,
                              user_spawned=user_spawned)

  if package_list is None:
    return None
  payload['spec']['resources']['package_definition_list'] = package_list

  # Step 2e: adding app_profiles
  deployments_list_to_be_added = spec_file.get('deployment_list', [])
  app_profiles_to_be_added = spec_file.get('app_profile', [])
  app_profile_list = \
    add_app_profiles(app_profiles_to_be_added=app_profiles_to_be_added,
                     credential_list=credential_list, vm_type=vm_type,
                     deployment_list=deployments_list_to_be_added,
                     substrate_list=substrate_list, package_list=package_list,
                     user_spawned=user_spawned, spec_edit=spec_edit,
                     num_configs_per_service=num_configs_per_service)
  if app_profile_list is None:
    return None
  payload['spec']['resources']['app_profile_list'] = app_profile_list

  # Step 2f: adding client_attrs
  payload['spec']['resources']['client_attrs'] = {}
  return payload

def add_client_attrs(**kwargs):
  """
  This method is used to add the client attrs
  Args:
    kwargs:
      service_list(list): list of all the services

  Returns:
    client_attrs(dict): dict of client attributes
  """
  service_list = kwargs.get('service_list')

  x_value = 200
  y_value = 200
  client_attrs = {}
  for _service in service_list:
    service_uuid = _service.get('uuid')
    client_attrs[service_uuid] = {
      'x': x_value,
      'y': y_value
    }
    x_value += 20
    y_value += 20
  return client_attrs


def add_credentials(credentials_to_be_added, user_spawned=''):
  """
  This method adds the credentials
  Args:
    credentials_to_be_added(list): list of the credentials to be added
    user_spawned(str): name of the locust user spawned.

  Returns:
    list of all the credentials.
            or
    None if duplicate credentials
  """

  credential = {
    "name": "",
    "type": "",
    "username": "",
    "secret": {
      "attrs": {
        "is_secret_modified": True
      },
      "value": ""
    },
    "uuid": ""
  }

  credential_list = []
  credential_names_list = []
  if len(credentials_to_be_added) == 0:
    credentials_to_be_added = [
      {
        "name": DEFAULT_CREDENTIAL_NAME,
        "username": DEFAULT_CREDENTIAL_USERNAME,
        "type": DEFAULT_CREDENTIAL_TYPE,
        "value": DEFAULT_CREDENTIAL_PASSWORD
      }
    ]

  for _credential in credentials_to_be_added:
    credential_name = _credential.get('name')
    if validate_if_duplicate_entity(
        entity_name=credential_name, entity_names_list=credential_names_list,
        entity_type='Credential', user_spawned=user_spawned):
      _print(user_spawned, "WARN: creadentials with name [{}] already exists"\
             .format(credential_name))
      continue
    credential_names_list.append(credential_name)
    credential_copy = copy.deepcopy(credential)
    credential_copy['name'] = credential_name
    credential_copy['type'] = _credential.get('type')
    credential_copy['username'] = _credential.get('username')
    is_secret_modified = _credential.get('is_secret_modified', None)
    if is_secret_modified is not None:
      credential_copy['secret']['attrs']['is_secret_modified'] = \
        is_secret_modified
    credential_copy['secret']['value'] = _credential.get('value')
    credential_copy['uuid'] = str(uuid.uuid4())
    credential_list.append(credential_copy)

  return credential_list

def add_app_profiles(**kwargs):
  """
  This method is used to add the app_profiles
  Args:
    kwargs:
      app_profiles_to_be_added(list): list of app_profiles to be added
      credential_list(list): list of all the credentials
      user_spawned(str): name of the locust user spawned
      deployment_list(list): list of deploy ments to be added (from spec file)
      published_service_definition_list(list): list pf published services
        to be added
      substrate_list(list): list of all the substrates
      package_list(list): list of all the packages
      vm_type(str): type of vm (single or multi)
      num_of_replicas(str): number of replicas per service in BP
      spec_edit(bool): spec_edit
      num_configs_per_service(int): no.of configs per service

  Returns:
    app_profile_list: list of all the app_profiles
                  or
    None if a)duplicate app_profiles b)duplicate variables c)duplicate actions
  """
  app_profiles_to_be_added = kwargs.get('app_profiles_to_be_added')
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')
  deployments_list_to_be_added = kwargs.get('deployment_list', [])
  published_services_list = kwargs.get( \
    'published_services_list', [])
  substrate_list = kwargs.get('substrate_list')
  vm_type = kwargs.get('vm_type', 'multi')
  package_list = kwargs.get('package_list')
  num_of_replicas = kwargs.get('num_of_replicas', '1')
  spec_edit = kwargs.get('spec_edit', False)
  num_configs_per_service = kwargs.get('num_configs_per_service', 1)

  app_profile = {
    "name": "",
    "action_list": [],
    "variable_list": [],
    "deployment_create_list": [],
    "environment_reference_list": [],
    "uuid": ""
  }

  patch = {
    "name": "",
    "variable_list": [],
    "attrs_list": [
      {
        "target_any_local_reference": {
          "kind": 'app_blueprint_deployment'
        },
        "data": {
          "num_vcpus_per_socket_ruleset": {
            "operation": "",
            "editable": None,
            "value": None,
            "min_value": None
          },
          "num_sockets_ruleset": {
            "operation": "",
            "editable": None,
            "value": None,
            "min_value": None,
            "max_value": None
          },
          "memory_size_mib_ruleset": {
            "operation": "",
            "editable": None,
            "value": None,
            "max_value": None
          },
          "pre_defined_disk_list": [],
          "pre_defined_nic_list": [],
          "pre_defined_categories": [],
          "type": "nutanix",
          "nic_delete_allowed": True
        },
        "uuid": ""
      }
    ],
    "type": "PATCH",
    "uuid": ""
  }
  if len(app_profiles_to_be_added) == 0:
    app_profiles_to_be_added = [
      {
        "name": DEFAULT_APP_PROFILE_NAME
      }
    ]

  app_profile_list = []
  app_profiles_names = []
  for _app_profile in app_profiles_to_be_added:
    app_profile_name = _app_profile.get('name')
    if validate_if_duplicate_entity(
        entity_name=app_profile_name, entity_names_list=app_profiles_names,
        entity_type='App Profile', user_spawned=user_spawned):
      return None
    app_profiles_names.append(app_profile_name)
    app_profile_copy = copy.deepcopy(app_profile)
    app_profile_copy['name'] = app_profile_name
    app_profile_copy['uuid'] = str(uuid.uuid4())

    # adding deployments
    deployment_list = None
    for _deployment in deployments_list_to_be_added:
      deployment_app_profile_name = _deployment.get('app_profile_name')
      if deployment_app_profile_name == app_profile_name:
        deployments_to_be_added = _deployment.get('deployments', [])
        deployment_list = \
          add_deployments(deployments_to_be_added=deployments_to_be_added,
                          substrate_list=substrate_list, vm_type=vm_type,
                          published_services_list=published_services_list,
                          package_list=package_list,
                          num_of_replicas=num_of_replicas,
                          user_spawned=user_spawned)
        if deployment_list is None:
          return None
        app_profile_copy['deployment_create_list'] = deployment_list
        break

    # adding actions
    actions_to_be_added = _app_profile.get('action', [])
    if len(actions_to_be_added) != 0:
      action_list = add_actions(actions_to_be_added=actions_to_be_added,
                                credential_list=credential_list,
                                user_spawned=user_spawned,
                                deployment_list=deployment_list,
                                substrate_list=substrate_list)
      if action_list is None:
        return None
      app_profile_copy['action_list'] = action_list

    patch_list = []
    if spec_edit:
      app_profile_copy['patch_list'] = []
      for deployment in deployment_list:
        substrate_for_patch = next((substrate for substrate in substrate_list
                                    if substrate['type'] == 'AHV_VM'), None)
        if substrate_for_patch:
          count = 0
          while count < num_configs_per_service:
            patch_copy = copy.deepcopy(patch)
            patch_copy['name'] = 'Config_' + str(id_generator(8))
            patch_copy['uuid'] = str(uuid.uuid4())
            patch_copy['attrs_list'][0]['target_any_local_reference']\
              ['name'] = deployment['name']
            patch_copy['attrs_list'][0]['target_any_local_reference']\
              ['uuid'] = deployment['uuid']
            patch_copy['attrs_list'][0]['data']\
              ['num_vcpus_per_socket_ruleset']['operation'] = 'decrease'
            patch_copy['attrs_list'][0]['data']\
              ['num_vcpus_per_socket_ruleset']['editable'] = True
            patch_copy['attrs_list'][0]['data']\
              ['num_vcpus_per_socket_ruleset']['value'] = 1
            patch_copy['attrs_list'][0]['data']\
              ['num_vcpus_per_socket_ruleset']['min_value'] = 1
            patch_copy['attrs_list'][0]['data']['num_sockets_ruleset']\
              ['operation'] = 'equal'
            patch_copy['attrs_list'][0]['data']['num_sockets_ruleset']\
              ['editable'] = True
            patch_copy['attrs_list'][0]['data']['num_sockets_ruleset']\
              ['value'] = 2
            patch_copy['attrs_list'][0]['data']['num_sockets_ruleset']\
              ['min_value'] = 1
            patch_copy['attrs_list'][0]['data']['num_sockets_ruleset']\
              ['max_value'] = 10
            patch_copy['attrs_list'][0]['data']['memory_size_mib_ruleset']\
              ['operation'] = 'increase'
            patch_copy['attrs_list'][0]['data']['memory_size_mib_ruleset']\
              ['editable'] = True
            patch_copy['attrs_list'][0]['data']['memory_size_mib_ruleset']\
              ['value'] = 256
            patch_copy['attrs_list'][0]['data']['memory_size_mib_ruleset']\
              ['max_value'] = 5120
            _disk_list = copy.deepcopy(substrate_for_patch['create_spec']\
                                       ['resources']['disk_list'])
            for _disk in _disk_list:
              _disk['operation'] = 'modify'
              _disk['data_source_reference'] = {}
            patch_copy['attrs_list'][0]['data']['pre_defined_disk_list'] = \
              _disk_list
            _nic_list = copy.deepcopy(substrate_for_patch['create_spec']\
                                      ['resources']['nic_list'])
            for _nic in _nic_list:
              _nic['operation'] = 'modify'
              _nic['network_function_nic_type'] = 'INGRESS'
              _nic['nic_type'] = 'NORMAL_NIC'
              _nic['network_function_chain_reference'] = None
              _nic['mac_address'] = ''
              _nic['identifier'] = '0'
            patch_copy['attrs_list'][0]['data']['pre_defined_nic_list'] = \
              _nic_list
            categories_list = []
            categories = substrate_for_patch['create_spec']['categories']
            for category in categories:
              categories_list.append({"operation": "modify", "value": \
                                      category + ':' + categories[category]})
            patch_copy['attrs_list'][0]['data']['pre_defined_categories'] = \
              categories_list
            patch_copy['attrs_list'][0]['data']['type'] = 'nutanix'
            patch_copy['attrs_list'][0]['data']['nic_delete_allowed'] = True
            patch_list.append(patch_copy)
            count += 1
    app_profile_copy['patch_list'] = patch_list
    app_profile_list.append(app_profile_copy)
  return app_profile_list

def add_actions(**kwargs):
  """
  This method adds the actions
  Args:
    kwargs:
      actions_to_be_added(list): list of all the actions to be added
      kind(str): name of kind
      main_task_kind(str): name of kind for main task
      task_uuid(str): uuid of main task
      kind_uuid(str): uuid of kind
      credential_list(list): list of all the credentials
      user_spawned(str): name of the locust user spawned

  Returns:
    action_list(list): list of all the actions
                or
    None if a)duplicate variables, b)duplicate tasks, c)duplicate actions
  """
  actions_to_be_added = kwargs.get('actions_to_be_added')
  main_task_kind = kwargs.get('main_task_kind', None)
  kind = kwargs.get('kind', None)
  task_uuid = kwargs.get('task_uuid', None)
  kind_uuid = kwargs.get('kind_uuid', None)
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')
  deployment_list = kwargs.get('deployment_list', None)
  substrate_list = kwargs.get('substrate_list', None)

  action = {
    "name": "",
    "runbook": {},
    "type": "",
    "uuid": ""
  }

  action_list = []
  action_names_list = []

  for _action in actions_to_be_added:
    action_name = _action.get('name')
    if validate_if_duplicate_entity(
        entity_name=action_name, entity_names_list=action_names_list,
        entity_type='Action', user_spawned=user_spawned):
      return None
    action_copy = copy.deepcopy(action)
    action_copy['name'] = action_name
    action_copy['uuid'] = str(uuid.uuid4())
    action_copy['type'] = _action.get('type', 'user')

    #fixme: If critical is added please uncomment it.
    #critical = _action.get('critical', None)
    #if critical is not None:
    #  action_copy['critical'] = critical

    # add tasks and variables(in runbook)
    tasks_to_be_added = _action.get('task', [])
    variables_to_be_added = _action.get('variable', [])
    runbook = \
      add_runbook(tasks_to_be_added=tasks_to_be_added, task_uuid=task_uuid,
                  variables_to_be_added=variables_to_be_added, kind=kind,
                  kind_uuid=kind_uuid, credential_list=credential_list,
                  user_spawned=user_spawned, main_task_kind=main_task_kind,
                  deployment_list=deployment_list,
                  substrate_list=substrate_list)
    if runbook is None:
      return None
    action_copy['runbook'] = runbook
    action_list.append(action_copy)

  return action_list

def add_runbook(**kwargs):
  """
  This method adds the runbook
  Args:
    kwargs:
      tasks_to_be_added(list): list of all the tasks to be added
      variables_to_be_added(list): list of variables to be added
      kind(str): name of kind on which it is applied
      main_task_kind(str): name of kind on which it is applied for main task
      kind_uuid(str): uuid of kind
      task_uuid(str): uuid of package definition
      credential_list(list): list of all the credentials
      user_spawned(str): name of the locust user spawned

  Returns:
    runbook_copy(dict): of all the info
                  or
    None if a)duplicate variables, b)duplicate tasks
  """
  tasks_to_be_added = kwargs.get('tasks_to_be_added')
  variables_to_be_added = kwargs.get('variables_to_be_added')
  kind = kwargs.get('kind')
  main_task_kind = kwargs.get('main_task_kind')
  task_uuid = kwargs.get('task_uuid')
  kind_uuid = kwargs.get('kind_uuid')
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')
  deployment_list = kwargs.get('deployment_list', None)
  substrate_list = kwargs.get('substrate_list', None)

  runbook = {
    "name": "",
    "variable_list": [],
    "main_task_local_reference": {},
    "task_definition_list": [],
    "uuid": ""
  }

  runbook_copy = copy.deepcopy(runbook)
  runbook_copy['name'] = id_generator(8) + '_runbook'
  runbook_copy['uuid'] = str(uuid.uuid4())

  # adding variables
  variable_list = add_variables(variables_to_be_added=variables_to_be_added,
                                user_spawned=user_spawned)
  if variable_list is None:
    return None
  runbook['variable_list'] = variable_list

  # adding tasks
  task_list, main_task_uuid = \
    add_tasks(credential_list=credential_list, user_spawned=user_spawned,
              tasks_to_be_added=tasks_to_be_added, kind=kind,
              task_uuid=task_uuid, kind_uuid=kind_uuid,
              main_task_kind=main_task_kind, deployment_list=deployment_list,
              substrate_list=substrate_list)
  if task_list is None:
    return None
  runbook_copy['task_definition_list'] = task_list
  runbook_copy['main_task_local_reference']['kind'] = "app_task"
  runbook_copy['main_task_local_reference']['uuid'] = main_task_uuid

  return runbook_copy


def add_variables(**kwargs):
  """
  This method adds the variables
  Args:
    kwargs:
      variables_to_be_added(list): list of variables to be added
      user_spawned(str): name of the locust user spawned

  Returns:
    variable_list(list): list of all the variables
              or
    None if duplicate variables.
  """
  variables_to_be_added = kwargs.get('variables_to_be_added')
  user_spawned = kwargs.get('user_spawned', '')

  variable = {
    "attrs": {},
    "name": "",
    "editables": {},
    "value": "",
    "label": "",
    "val_type": "",
    "type": "",
    "description": "",
    "uuid": ""
  }
  variable_list = []
  variable_names_list = []

  for _variable in variables_to_be_added:
    variable_copy = copy.deepcopy(variable)
    variable_name = _variable.get('name')
    if validate_if_duplicate_entity(
        entity_name=variable_name, entity_names_list=variable_names_list,
        entity_type='Variable', user_spawned=user_spawned):
      return None
    variable_names_list.append(variable_name)
    variable_copy['name'] = variable_name
    variable_copy['uuid'] = str(uuid.uuid4())
    variable_copy['value'] = _variable.get('value')
    variable_copy['val_type'] = _variable.get('val_type', 'STRING')
    if _variable.get('is_secret', False):
      variable_copy['type'] = 'SECRET'
      variable_copy['attrs']['is_secret_modified'] = True
    else:
      variable_copy['type'] = 'LOCAL'
    if _variable.get('is_runtime', False):
      variable_copy['editables']['value'] = True
    variable_list.append(variable_copy)

  return variable_list


def add_ports(**kwargs):
  """
  This method adds the ports
  Args:
    kwargs:
      ports_to_be_added(list): list of port attributes to be added
      user_spawned(str): name of the locust user spawned

  Returns:
    port_list(list): list of all the ports added
                    or
    None if duplicate ports
  """
  ports_to_be_added = kwargs.get('ports_to_be_added')
  user_spawned = kwargs.get('user_spawned', '')

  port = {
    "endpoint_name": "",
    "protocol": "",
    "target_port": ""
  }

  port_list = []
  port_names_list = []
  for _port in ports_to_be_added:
    port_name = _port.get('name')
    if validate_if_duplicate_entity(
        entity_name=port_name, entity_names_list=port_names_list,
        entity_type='Port', user_spawned=user_spawned):
      return None
    port_names_list.append(port_name)
    port_copy = copy.deepcopy(port)
    port_copy['endpoint_name'] = port_name
    port_copy['protocol'] = _port.get('protocol')
    port_copy['target_port'] = _port.get('target_port')
    port_list.append(port_copy)
  return port_list


def add_tasks(**kwargs):
  """
  This method adds the tasks
  Args:
    kwargs:
      tasks_to_be_added(list): list of all the tasks to be added
      kind(str): name of kind on which the task will be applied
      main_task_kind(str): name of kind on which the
        task will be applied for main task
      kind_uuid(str): uuid of kind
      task_uuid(str): uuid of package definition
      credential_list(list): list of all the credentials
      user_spawned(str): name of the locust user spawned.

  Returns:
    None if a)duplicate task names, b)kind is None
              or
    tasks_list(list): list of all the task,
    main_task_uuid(str): uuid of main task
  """
  #fixme: add all_dependent as blueprint_config_generator
  #fixme: also add code for the edges between tasks.

  tasks_to_be_added = kwargs.get('tasks_to_be_added')
  kind = kwargs.get('kind')
  main_task_kind = kwargs.get('main_task_kind')
  kind_uuid = kwargs.get('kind_uuid')
  task_uuid = kwargs.get('task_uuid')
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')
  deployment_list = kwargs.get('deployment_list', None)
  substrate_list = kwargs.get('substrate_list', None)

  task_list = []
  main_task = add_main_task(task_uuid=task_uuid, main_task_kind=main_task_kind)
  task_list.append(main_task)

  task = {
    "name": "",
    "variable_list": [],
    "child_tasks_local_reference_list": [],
    "target_any_local_reference": {},
    "type": "",
    "attrs": {},
    "uuid": ""
  }
  child_reference = {'kind': 'app_task',
                     'uuid': ''}
  task_names_list = []
  task_number = 1
  for _task in tasks_to_be_added:
    task_name = _task.get('name')
    if validate_if_duplicate_entity(
        entity_name=task_name, entity_names_list=task_names_list,
        entity_type='Task', user_spawned=user_spawned):
      return None, main_task['uuid']
    task_copy = copy.deepcopy(task)
    task_copy['name'] = task_name
    task_copy['uuid'] = str(uuid.uuid4())

    # fixme: add code here for adding variables

    if task_number > 1:
      task_link = {
        "from_task_reference": {
          "kind": "app_task",
          "uuid": main_task['child_tasks_local_reference_list'] \
            [len(main_task['child_tasks_local_reference_list'])-1]['uuid']
        },
        "to_task_reference": {
          "kind": "app_task",
          "uuid": task_copy['uuid']
        },
        "uuid": str(uuid.uuid4())
      }
      main_task['attrs']['edges'].append(task_link)
    main_task['child_tasks_local_reference_list'].append({
      "kind": "app_task",
      "uuid": task_copy['uuid']
    })

    main_task['attrs']['edges'] = []
    task_copy['type'] = _task.get('type')
    if task_copy['type'] == 'HTTP':
      task_copy['attrs']['method'] = _task.get('method')
      task_copy['attrs']['relative_url'] = _task.get('relative_url')
      task_copy['attrs']['content_type'] = _task.get('content_type')
      task_copy['attrs']['expected_response_params'] = \
       _task.get('expected_response_params')
      task_list.append(task_copy)
      task_number += 1
      continue

    if task_copy['type'] == "SCALING":
      task_copy['attrs']['scaling_type'] = _task.get('scaling_type')
      task_copy['attrs']['scaling_count'] = _task.get('scaling_count', "1")

      kind = 'app_blueprint_deployment'
      substrate_name = _task.get('substrate_name')
      substrate_uuid = None
      for _substrate in substrate_list:
        if substrate_name == _substrate['name']:
          substrate_uuid = _substrate.get('uuid')
          break
      if substrate_uuid is None:
        _print(user_spawned, "Substrate with name [{0}] not found".
               format(substrate_name))
        return None
      for _deployment in deployment_list:
        if _deployment['substrate_local_reference']['uuid'] == substrate_uuid:
          kind_uuid = _deployment.get('uuid')
          break
      if kind_uuid is None:
        _print(user_spawned, "Deployment with Substrate [{0}] not found".
               format(substrate_name))
        return None

    elif task_copy['type'] in ['EXEC', 'SET_VARIABLE', 'DECISION']:
      task_copy['attrs']['script_type'] = _task.get('script_type')
      task_copy['attrs']['script'] = _task.get('script')
      if task_copy['attrs']['script_type'] == "sh":
        credential_name = _task.get('credential_name')
        credential_uuid = \
          next((credential.get('uuid') for credential in credential_list
                if credential.get('name') == credential_name), None)
        if credential_uuid is None:
          _print(user_spawned, "Credential [{0}] not "
                               "found".format(credential_name))
          return None
        task_copy['attrs']['login_credential_local_reference'] = {
          "kind": "app_credential",
          "uuid": credential_uuid
        }
      if task_copy['type'] == 'SET_VARIABLE':
        task_copy['attrs']['eval_variables'] = _task.get('eval_variables')
      elif task_copy['type'] == 'DECISION':
        if _task.get('nested_dec'):
          child_tasks = _task.get('nested_dec')
          child_tasks_prefix_name = task_copy['name'] + id_generator(4)
          for dec_task in child_tasks:
            dec_task['name'] = child_tasks_prefix_name
          nested_task = []
          child_task_list, main_task_uuid = add_tasks(kind=kind, \
            tasks_to_be_added=child_tasks, task_uuid=task_uuid, \
            kind_uuid=kind_uuid, credential_list=credential_list, \
            user_spawned=user_spawned, main_task_kind=main_task_kind)

          child_task_list.pop(0)
          task_list.extend(child_task_list)

          for count, dec_task in enumerate(child_task_list):
            if child_tasks_prefix_name == dec_task['name']:
              dec_task['name'] = dec_task['name'] + str(count)
              nested_task.append(dec_task)
          child_task_list = nested_task

        elif _task.get('decision_tasks'):
          child_tasks = _task.get('decision_tasks')
          child_task_list, main_task_uuid = add_tasks(kind=kind, \
            tasks_to_be_added=child_tasks, task_uuid=task_uuid, \
            kind_uuid=kind_uuid, credential_list=credential_list, \
            user_spawned=user_spawned, main_task_kind=main_task_kind)
          child_task_list.pop(0)
          task_list.extend(child_task_list)

        failure_task = copy.deepcopy(task)
        failure_task['name'] = id_generator(8) + '_FAILURE_META'
        failure_task['uuid'] = str(uuid.uuid4())
        failure_task['type'] = 'META'

        success_task = copy.deepcopy(task)
        success_task['name'] = id_generator(8) + '_SUCCESS_META'
        success_task['uuid'] = str(uuid.uuid4())
        success_task['type'] = 'META'

        for child_task in child_task_list:
          meta_child_reference = copy.deepcopy(child_reference)
          meta_child_reference['uuid'] = child_task['uuid']
          if child_task_list.index(child_task)%2:
            success_task['child_tasks_local_reference_list'] \
              .append(meta_child_reference)
          else:
            failure_task['child_tasks_local_reference_list'] \
              .append(meta_child_reference)

        task_copy['attrs']['failure_child_reference'] = {
          'kind': 'app_task',
          'uuid': failure_task['uuid']
        }
        task_copy['attrs']['success_child_reference'] = {
          'kind': 'app_task',
          'uuid': success_task['uuid']
        }

        task_list.extend([failure_task, success_task])
        del main_task_uuid

    elif task_copy['type'] == 'WHILE_LOOP':
      if _task.get('nested_while'):
        child_tasks = _task.get('nested_while')
        child_task_list, main_task_uuid = add_tasks(kind=kind, \
          tasks_to_be_added=child_tasks, task_uuid=task_uuid, \
          kind_uuid=kind_uuid, credential_list=credential_list, \
          user_spawned=user_spawned, main_task_kind=main_task_kind)
        child_task_list.pop(0)
        task_list.extend(child_task_list)
        child_task_list = [child_task_list.pop()]


      elif _task.get('while_task'):
        child_tasks = _task.get('while_task')
        child_task_list, main_task_uuid = add_tasks(kind=kind, \
          tasks_to_be_added=child_tasks, task_uuid=task_uuid, \
          kind_uuid=kind_uuid, credential_list=credential_list, \
          user_spawned=user_spawned, main_task_kind=main_task_kind)
        child_task_list.pop(0)
        task_list.extend(child_task_list)

      for child_task in child_task_list:
        meta_task = copy.deepcopy(task)
        meta_child_reference = copy.deepcopy(child_reference)
        meta_child_reference['uuid'] = child_task['uuid']
        meta_task['child_tasks_local_reference_list'] \
          .append(meta_child_reference)
        meta_task['name'] = id_generator(8) + '_' + \
          str(child_task_list.index(child_task)) + '_META'
        meta_task['type'] = 'META'
        meta_task['uuid'] = str(uuid.uuid4())
        task_list.append(meta_task)

        task_child_reference = copy.deepcopy(child_reference)
        task_child_reference['uuid'] = meta_task['uuid']
        task_copy['child_tasks_local_reference_list'] \
          .append(task_child_reference)

      task_copy['attrs']['exit_condition_type'] = \
       _task.get('exit_condition_type')
      task_copy['attrs']['iterations'] = _task.get('iterations')
      task_copy['attrs']['loop_variable'] = _task.get('loop_variable')
      del main_task_uuid

    if kind is None:
      _print(user_spawned, "kind is required")
      return None
    task_copy['target_any_local_reference']['kind'] = kind
    task_copy['target_any_local_reference']['uuid'] = kind_uuid
    task_list.append(task_copy)

    task_number += 1
  return task_list, main_task['uuid']

def add_main_task(**kwargs):
  """
  This method adds the main task
  Args:
    kwargs:
      main_task_kind(str): kind on which it applies
      task_uuid(str): uuid of kind.

  Returns:
    dict of main_task info.
  """
  main_task_kind = kwargs.get('main_task_kind', None)
  task_uuid = kwargs.get('task_uuid', None)

  task = {
    "name": "",
    "variable_list": [],
    "child_tasks_local_reference_list": [],
    "type": "",
    "attrs": {
      "edges": []
    },
    "uuid": ""
  }

  task_copy = copy.deepcopy(task)
  task_copy['name'] = id_generator(8) + '_dag'
  task_copy['type'] = 'DAG'
  task_copy['uuid'] = str(uuid.uuid4())
  if main_task_kind is not None:
    task_copy['target_any_local_reference'] = {
      'kind': main_task_kind,
      'uuid': task_uuid
    }

  return task_copy


def add_services(**kwargs):
  """
  This method adds the services to the blueprint
  Args:
    kwargs:
      services_to_be_added(list): list of services to be added.
      credential_list(list): list of all the credentials
      user_spawned(str): name of the locust user spawned

  Returns:
    service_list(list): list of all the services
                      or
    None if duplicate services
  """
  services_to_be_added = kwargs.get('services_to_be_added')
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')

  service = {
    "name": "",
    "depends_on_list": [],
    "variable_list": [],
    "port_list": [],
    "action_list": [],
    "uuid": ""
  }

  service_list = []
  service_names_list = []

  for _service in services_to_be_added:
    service_copy = copy.deepcopy(service)
    service_name = _service.get('name')
    if validate_if_duplicate_entity(
        entity_name=service_name, entity_names_list=service_names_list,
        entity_type='Service', user_spawned=user_spawned):
      return None
    service_names_list.append(service_name)
    service_copy['name'] = service_name
    service_copy['uuid'] = str(uuid.uuid4())
    if _service.get('singleton', None) is not None:
      service_copy['singleton'] = _service.get('singleton')

    # fixme: add method for adding depends_on.

    # adding variables
    variables_to_be_added = _service.get('variable', [])
    variable_list = add_variables(
      variables_to_be_added=variables_to_be_added, user_spawned=user_spawned)
    if variable_list is None:
      return None
    service_copy['variable_list'] = variable_list

    # adding ports
    ports_to_be_added = _service.get('port', [])
    port_list = add_ports(
      ports_to_be_added=ports_to_be_added, user_spawned=user_spawned)
    if port_list is None:
      return None
    service_copy['port_list'] = port_list

    # adding regular_actions and actions added by user.
    actions_to_be_added = _service.get('action', [])
    regular_action_list = \
      add_regular_actions(kind="app_service", kind_uuid=service_copy['uuid'],
                          task_uuid=service_copy['uuid'],
                          credential_list=credential_list,
                          user_spawned=user_spawned)
    if regular_action_list is None:
      return None
    service_copy['action_list'] = regular_action_list
    action_list = add_actions(actions_to_be_added=actions_to_be_added,
                              credential_list=credential_list,
                              user_spawned=user_spawned)
    if action_list is None:
      return None
    for _action in action_list:
      main_task_uuid = _action['runbook']['main_task_local_reference']['uuid']
      task_list = _action['runbook']['task_definition_list']
      for task in task_list:
        if task.get('uuid') == main_task_uuid:
          task['target_any_local_reference'] = {}
          break
      service_copy['action_list'].append(_action)
    if _service.get('type') == 'K8S_POD':
      service_copy['container_spec'] = {
        "ports": [
          {
            "protocol": "TCP",
            "containerPort": 8080
          }
        ],
        "name": service_name
      }
    service_list.append(service_copy)

  return service_list


def add_regular_actions(**kwargs):
  """
  This method adds the regular actions for the service
  Args:
    kwargs:
      kind(str): name of kind
      kind_uuid(str): uuid of kind
      task_uuid(str): uuid of task
      credential_list(list): list of all the credentials
      user_spawned(str): name of the locust user spawned

  Returns:
    action_list(list): list of all the regular actions
  """
  action_names = ['action_create', 'action_delete', 'action_start',
                  'action_stop', 'action_restart']
  kind = kwargs.get('kind')
  kind_uuid = kwargs.get('kind_uuid')
  task_uuid = kwargs.get('task_uuid')
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')

  actions_to_be_added = []
  for action_name in action_names:
    action = {
      "name": action_name,
      "description": "",
      "type": "system"
    }
    actions_to_be_added.append(action)

  action_list = add_actions(actions_to_be_added=actions_to_be_added,
                            kind=kind, kind_uuid=kind_uuid,
                            credential_list=credential_list,
                            user_spawned=user_spawned,
                            task_uuid=task_uuid)
  if action_list is None:
    return None
  return action_list


def validate_if_duplicate_entity(**kwargs):
  """
  This method checks if the entity has duplicates or not
  Args:
    kwargs:
      entity_name(str): name of entity
      entity_names_list(list): list of all the entity names until now.
      entity_type(str): type of entity
      user_spawned(str): name of the locust user spawned

  Returns:
    True: if duplicate entity exists
    False : if no duplicate entity exists
  """
  entity_name = kwargs.get('entity_name')
  entity_names_list = kwargs.get('entity_names_list')
  entity_type = kwargs.get('entity_type')
  user_spawned = kwargs.get('user_spawned', '')

  if entity_name in entity_names_list:
    _print(user_spawned, "{0} with name [{1}] already exists".format(
      entity_type, entity_name))
    return True
  return False


def add_substrates(**kwargs):
  """
  This method adds the substrates
  Args:
    kwargs:
      self(object): self object
      substrates_to_be_added(list): list of all the substrates to be added
      service_list(list): list of all the services
      credential_list(list): list of all the credentials
      vlan_list(list, optional): names list of network adapters
      vm_type(str): type of the vm (single or multi)
      project_uuid(str): project uuid
      user_spawned(str): name of the locust user spawned

  Returns:
    substrate_list(list): list of all the substrates
  """
  self = kwargs.get('self')
  substrates_to_be_added = kwargs.get('substrates_to_be_added')
  service_list = kwargs.get('service_list')
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')
  vm_type = kwargs.get('vm_type', 'multi')
  vlan_list = kwargs.get('vlan_list', [])
  project_uuid = kwargs.get('project_uuid', '')
  linux_guest_customization_delay = \
    kwargs.get('linux_guest_customization_delay', '60')
  windows_guest_customization_delay = \
    kwargs.get('windows_guest_customization_delay', '60')
  no_of_categories = kwargs.get('no_of_categories', 1)
  spec_edit = kwargs.get('spec_edit', False)

  if vm_type != 'single':
    services_with_no_substrates = []
    substrate_service_names = []
    for _substrate in substrates_to_be_added:
      service_names_list = _substrate.get('service_name').split(',')
      substrate_service_names.extend(service_names_list)

    if service_list is not None:
      for _service in service_list:
        if _service.get('name') not in substrate_service_names:
          services_with_no_substrates.append(_service.get('name'))

      if len(services_with_no_substrates) != 0:
        _print(user_spawned, "Add substrates for these services also\n {0}". \
          format("\n".join(services_with_no_substrates)))
        return None

  substrate = {
    "variable_list": [],
    "type": "",
    "os_type": "",
    "action_list": [],
    "create_spec": {},
    "name": "",
    "readiness_probe": {
      "address": "",
      "disable_readiness_probe": True,
      "connection_protocol": "",
      "connection_type": "",
      "connection_port": "",
      "delay_secs": "",
      "login_credential_local_reference": {
        "kind": "",
        "uuid": ""
      },
      "retries": ""
    },
    "uuid": ""
  }
  if vm_type == 'multi':
    substrate['readiness_probe']['login_credential_local_reference'] = {
      "kind": "app_credential",
      "uuid": ""
    }
  substrate_list = []
  substrate_names_list = []
  aws_instance_names_added = []
  vmware_instance_names_added = []
  gcp_instance_names_added = []
  azure_instance_names_added = []
  if vm_type == 'single':
    substrates_to_be_added = [substrates_to_be_added]
  for _substrate in substrates_to_be_added:
    substrate_name = _substrate.get('name')
    if validate_if_duplicate_entity(
        entity_name=substrate_name, entity_names_list=substrate_names_list,
        entity_type='Substrate', user_spawned=user_spawned):
      return None
    substrate_names_list.append(substrate_name)
    substrate_copy = copy.deepcopy(substrate)
    substrate_copy['name'] = substrate_name
    substrate_copy['uuid'] = str(uuid.uuid4())
    substrate_copy['type'] = _substrate.get('type')
    substrate_copy['os_type'] = _substrate.get('os_type')
    if substrate_copy['os_type'] == 'Linux':
      substrate_copy['readiness_probe']['connection_type'] = "SSH"
      substrate_copy['readiness_probe']['connection_port'] = 22
      substrate_copy['readiness_probe']['retries'] = \
        _substrate.get('retries', '5')
      substrate_copy['readiness_probe']['delay_secs'] = \
        _substrate.get('timeout', linux_guest_customization_delay)
    elif substrate_copy['os_type'] == 'Windows':
      substrate_copy['readiness_probe']['connection_type'] = "POWERSHELL"
      substrate_copy['readiness_probe']['connection_port'] = 5985
      substrate_copy['readiness_probe']['delay_secs'] = \
        _substrate.get('timeout', windows_guest_customization_delay)
      substrate_copy['readiness_probe']['retries'] = \
        _substrate.get('retries', '5')
    else:
      _print(user_spawned,
             "Current os_type [{0}] is either not supported or not "
             "Automated".format(substrate_copy['os_type']))
      return None

    disable_readiness_probe = _substrate.get('disable_readiness_probe', False)
    if vm_type == 'single':
      disable_readiness_probe = _substrate.get('disable_readiness_probe', True)
      action_names = ['pre_action_create', 'post_action_delete']
      actions_to_be_added = []
      for action_name in action_names:
        action = {
          "name": action_name,
          "description": "",
          "type": "fragment"
        }
        actions_to_be_added.append(action)
      substrate_copy['action_list'] = add_actions(
        actions_to_be_added=actions_to_be_added, kind='app_substrate',
        task_uuid=substrate_copy['uuid'], credential_list=credential_list,
        user_spawned=user_spawned)

    if disable_readiness_probe:
      substrate_copy['readiness_probe']['disable_readiness_probe'] = True
    if vm_type == 'multi' and _substrate.get('type') != 'K8S_POD':
      credential_name = _substrate.get('credential_name')
      if credential_name is None:
        _print(user_spawned, "SKIP: credential name for substrate [{0}] not"
                             " specified".format(substrate_name))
        return None
      credential_uuid = \
        next((credential.get('uuid') for credential in credential_list
              if credential.get('name') == credential_name), None)
      if credential_uuid is None:
        _print(user_spawned,
               "Credential [{0}] not found".format(credential_name))
        return None
      substrate_copy['readiness_probe']['login_credential_local_reference'][
        'uuid'] = credential_uuid

    if substrate_copy['type'] == 'EM':
      substrate_copy['type'] = 'EXISTING_VM'
      substrate_copy['create_spec']['type'] = "PROVISION_EXISTING_MACHINE"
      if substrate_copy['os_type'] == 'Windows':
        ip_address = _substrate.get('em_win_ip_address',
                                    DEFAULT_EM_WIN_IP_ADDRESS)
      elif substrate_copy['os_type'] == 'Linux':
        ip_address = _substrate.get('em_ip_address', DEFAULT_EM_IP_ADDRESS)
      substrate_copy['create_spec']['address'] = ip_address
      substrate_copy['readiness_probe']['address'] = "@@{ip_address}@@"
    elif substrate_copy['type'] == 'AHV':
      substrate_copy['type'] = 'AHV_VM'
      ahv_instance_name = _substrate.get('ahv_instance_name', None)
      if ahv_instance_name is None:
        ahv_instance_name = DEFAULT_AHV_BLUEPRINT_INSTANCE_NAME
      ahv_instance_name += '-@@{calm_array_index}@@-@@{calm_time}@@'
      substrate_copy['create_spec']['name'] = ahv_instance_name

      resources = {
        "boot_config": {},
        "disk_list": [],
        "num_sockets": "",
        "num_vcpus_per_socket": "",
        "memory_size_mib": "",
        "nic_list": []
      }

      data = {
        'filter': 'state!=DELETED'
      }

      account_name = _substrate.get('account_name', \
        DEFAULT_LOCAL_NUTANIX_ACCOUNT_NAME)

      project_data = get_entity(self=self, \
        url='projects_internal/'+project_uuid, api_name='/projects_internal')

      if project_data is None:
        return None

      account_ref_list = project_data['spec']['project_detail']['resources'] \
                         ['account_reference_list']
      subnet_reference_list = project_data['spec']['project_detail'] \
                              ['resources']['subnet_reference_list']
      external_network_list = project_data['spec']['project_detail'] \
                              ['resources']['external_network_list']

      is_host_pc = False
      remote_pc_ip = ''
      for acc in account_ref_list:
        account_data = get_entity(self=self, \
          url='accounts/'+acc['uuid'], api_name='/accounts')
        if account_data['spec']['resources']['type'] == 'nutanix_pc' and \
            account_data['spec']['name'] == account_name:
          if 'host_pc' in account_data['spec']['resources']['data']:
            is_host_pc = account_data['spec']['resources']['data']['host_pc']
          remote_pc_ip = account_data['spec']['resources']['data']['server']
          account_uuid = account_data['status']['resources']['data'] \
                         ['cluster_account_reference_list'][0]['uuid']
          break

      resources_copy = copy.deepcopy(resources)

      resources_copy['num_sockets'] = _substrate.get('num_of_vcpus', 1)
      resources_copy['num_vcpus_per_socket'] = \
        _substrate.get('cores_per_vcpu', 1)
      resources_copy['memory_size_mib'] = _substrate.get('memory', 256)
      if spec_edit:
        resources_copy['num_sockets'] = \
          os.environ.get('NUM_SOCKETS', DEFAULT_SOCKETS)
        resources_copy['num_vcpus_per_socket'] = \
          os.environ.get('NUM_VCPUS_PER_SOCKET', DEFAULT_VCPUS_PER_SOCKET)
        resources_copy['memory_size_mib'] = \
          os.environ.get('MEMORY_SIZE', DEFAULT_MEMORY_SIZE)

      # add images
      images_to_be_added = _substrate.get('image_list', [])
      disk_list = \
        add_images(self=self, images_to_be_added=images_to_be_added,
                   is_host_pc=is_host_pc, remote_pc_ip=remote_pc_ip,
                   user_spawned=user_spawned)
      if disk_list is None:
        return None
      resources_copy['disk_list'] = disk_list

      # add bootable image
      if substrate_copy['os_type'] == 'Linux':
        bootable_image = \
          _substrate.get('bootable_disk',
                         DEFAULT_AHV_BLUEPRINT_LINUX_IMAGE_NAME)
      else:
        bootable_image = \
          _substrate.get('bootable_disk',
                         DEFAULT_AHV_BLUEPRINT_WINDOWS_IMAGE_NAME)

      disk = next((disk for disk in disk_list if disk['data_source_reference'][
        'name'] == bootable_image), None)
      if disk is None:
        _print(user_spawned,
               "Bootable Image [{0}] not found".format(bootable_image))
        return None
      resources_copy['boot_config'] = {
        'boot_device': {
          'disk_address': disk['device_properties']['disk_address']
        }
      }

      # add network adapters
      if len(vlan_list) != 0:
        nic_to_be_added = vlan_list
      else:
        nic_to_be_added = _substrate.get('nic', [])
      nic_list = add_network_adapters(
        self=self, nic_to_be_added=nic_to_be_added, user_spawned=user_spawned,
        vm_type=vm_type, is_host_pc=is_host_pc, remote_pc_ip=remote_pc_ip,
        subnet_reference_list=subnet_reference_list,
        external_network_list=external_network_list)
      if nic_list is None:
        return None
      resources_copy['nic_list'] = nic_list

      # adding resources
      substrate_copy['readiness_probe']['address'] = \
        "@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@"

      # adding account uuid
      resources_copy['account_uuid'] = account_uuid

      substrate_copy['create_spec']['resources'] = resources_copy
      # adding categories
      categories = create_categories(self, no_of_categories)
      substrate_copy['create_spec']['categories'] = categories

    elif substrate_copy['type'] == "AWS":
      substrate_copy['type'] = 'AWS_VM'
      if _substrate.get('address', None) is None:
        substrate_copy['readiness_probe']['address'] = \
          "@@{public_ip_address}@@"
      elif _substrate.get('address') == 'public_ip':
        substrate_copy['readiness_probe']['address'] = \
          "@@{public_ip_address}@@"
      else:
        substrate_copy['readiness_probe']['address'] = \
          "@@{private_ip_address}@@"

      substrate_copy['create_spec']['type'] = "PROVISION_AWS_VM"
      aws_instance_name = _substrate.get('aws_instance_name', None)
      if aws_instance_name is None:
        aws_instance_name = DEFAULT_AWS_BLUEPRINT_INSTANCE_NAME
      aws_instance_name += '-@@{calm_array_index}@@-@@{calm_time}@@'
      if aws_instance_name in aws_instance_names_added:
        _print(user_spawned, "AWS Instance with name [{0}] already added,"
                             " cannot add duplicate instance names".
               format(aws_instance_name))
        return None
      aws_instance_names_added.append(aws_instance_name)
      substrate_copy['create_spec']['name'] = aws_instance_name

      resources = {
        "instance_type": "",
        "block_device_map": {
          "root_disk": {
            "size_gb": 8,
            "volume_type": "GP2",
            "delete_on_termination": True,
            "device_name": "/dev/sda1"
          }
        },
        "key_name": "",
        "account_uuid": "",
        "availability_zone": "",
        "vpc_id": "",
        "associate_public_ip_address": "",
        "region": "",
        "security_group_list": [],
        "subnet_id": "",
        "image_id": ""
      }

      account_name = _substrate.get('account_name', NUCALM_AWS_ACCOUNT_NAME)
      data = {
        'filter': 'state!=DELETED;type==aws'
      }
      account_list = get_list(self=self, url='accounts/list', payload=data,
                              user_spawned=user_spawned)
      if account_list is None:
        return None
      account = next((account for account in account_list
                      if account['status']['name'] == account_name), None)
      if account is None:
        _print(user_spawned,
               "Account with name [{0}] not found".format(account_name))
        return None

      resources_copy = copy.deepcopy(resources)
      resources_copy['account_uuid'] = account['metadata']['uuid']
      resources_copy['associate_public_ip_address'] = _substrate.get(
        'associate_public_ip_address', True)
      resources_copy['instance_type'] = _substrate.get(
        'instance_type', DEFAULT_AWS_BLUEPRINT_INSTANCE_TYPE)
      #resources_copy['instance_initiated_shutdown_behavior'] = \
      #  _substrate.get('shutdown_behaviour', DEFAULT_SHUTDOWN_BEHAVIOUR)
      region = _substrate.get('region', DEFAULT_AWS_BLUEPRINT_REGION)
      resources_copy['region'] = region

      filters = \
        "".join(['account_uuid==', account['metadata']['uuid'], ';',
                 'region==', region])

      # a) select avaialable zone
      available_zone = \
        _substrate.get('available_zone', DEFAULT_AWS_AVAILABLE_ZONE)
      resources_copy['availability_zone'] = available_zone

      # b) select image
      data = {
        'filter': filters
      }
      images_list = get_list(self=self, url='aws/images/list', payload=data,
                             user_spawned=user_spawned, recall=True)
      if images_list is None:
        _print(user_spawned, "Unable to get the list of the aws images")
        return None
      image_name = _substrate.get('aws_image_name', None)
      if image_name is None:
        if substrate_copy['os_type'] == 'Linux':
          image_name = DEFAULT_AWS_BLUEPRINT_LINUX_IMAGE_NAME
        elif substrate_copy['os_type'] == 'Windows':
          image_name = DEFAULT_AWS_BLUEPRINT_WINDOWS_IMAGE_NAME
        else:
          _print(user_spawned, "SKIP: Image for aws is required to be added.")
          return None
      if length_check(images_list, 'image', user_spawned) is None:
        return None
      image_id = \
        next((image['status']['resources']['id'] for image in images_list
              if image['status']['name'] == image_name), None)
      if image_id is None:
        _print(user_spawned, "Image [{0}] not found".format(image_name))
        return None
      resources_copy['image_id'] = image_id

      # c) select IAM role
      role_name = \
        _substrate.get('instance_profile_name', DEFAULT_AWS_BLUEPRINT_IAM_ROLE)
      roles_list = get_list(self=self, url='aws/roles/list', payload=data,
                            user_spawned=user_spawned, recall=True)
      if roles_list is None:
        return None
      if length_check(roles_list, 'role', user_spawned) is None:
        return None
      if role_name != '':
        role_name = next((role['status']['name'] for role in roles_list
                          if role['status']['name'] == role_name), None)
        if role_name is None:
          _print(user_spawned, "Role [{0}] not found".format(role_name))
          return None
        resources_copy['instance_profile_name'] = role_name

      # d) select keypair
      keypair_name = \
        _substrate.get('keypair_name', DEFAULT_AWS_BLUEPRINT_KEY_PAIR)
      keypair_list = \
        get_list(self=self, url='aws/key_pairs/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      if keypair_list is None:
        return None
      if length_check(keypair_list, 'key_pair', user_spawned) is None:
        return None
      keypair_name = \
        next((keypair['status']['name'] for keypair in keypair_list
              if keypair['status']['name'] == keypair_name), None)
      if keypair_name is None:
        _print(user_spawned, "Keypair [{0}] not found".format(keypair_name))
        return None
      resources_copy['key_name'] = keypair_name

      # e) select vpc
      vpc_list = get_list(self=self, url='aws/vpcs/list', payload=data,
                          user_spawned=user_spawned, recall=True)
      if vpc_list is None:
        _print(user_spawned, "Unable to get the list of vpc for aws")
        return None
      if length_check(vpc_list, 'vpc', user_spawned) is None:
        return None
      vpc_cidr_block = \
        _substrate.get('vpc_cidr_block', DEFAULT_AWS_VPC_CIDR_BLOCK)
      vpc_id = _substrate.get('vpc_id', DEFAULT_AWS_VPC_ID)
      vpc = \
        next((vpc for vpc in vpc_list
              if vpc['status']['resources']['cidr_block'] == vpc_cidr_block
              and vpc['status']['resources']['id'] == vpc_id), None)
      if vpc is None:
        _print(user_spawned, "No vpc is available")
        return None
      resources_copy['vpc_id'] = vpc_id

      # f) add security groups
      filters += "".join([';', 'vpc_id==', vpc_id])
      security_groups_to_be_added = _substrate.get('security_groups_list', [])
      security_group_list = add_security_groups(
        self=self, security_groups_to_be_added=security_groups_to_be_added,
        filters=filters, user_spawned=user_spawned)
      if security_group_list is None:
        _print(user_spawned, "cannot add security groups")
        return None
      resources_copy['security_group_list'] = security_group_list

      # g) select subnet
      filters += "".join([';', 'availability_zone==', available_zone])
      data = {
        'filter': filters
      }
      subnet_list = get_list(self=self, url='aws/subnets/list', payload=data,
                             user_spawned=user_spawned, recall=True)
      if subnet_list is None:
        return None
      if length_check(subnet_list, 'subnet', user_spawned) is None:
        return None
      subnet_id = next(
        (subnet['status']['resources']['id'] for subnet in subnet_list
         if subnet['status']['resources']['state'] == 'AVAILABLE'), None)
      if subnet_id is None:
        _print(user_spawned,
               "No subnet is available in [{0}]".format(available_zone))
        return None
      resources_copy['subnet_id'] = subnet_id
      # fixme: add methods for parameterizing adding storage.

      # h) Adding storage
      # h.i) Adding root disk
      root_disk_size = _substrate.get('root_disk_size', None)
      if root_disk_size is None:
        if substrate_copy['os_type'] == 'Linux':
          root_disk_size = DEFAULT_AWS_LINUX_ROOT_DISK_SIZE
        elif substrate_copy['os_type'] == 'Windows':
          root_disk_size = DEFAULT_AWS_WINDOWS_ROOT_DISK_SIZE
        else:
          _print(user_spawned, "For Mentioned os_type [{0}], disk size is"
                               " not given, so taking default size as 8gb".
                 format(substrate_copy['os_type']))
          root_disk_size = DEFAULT_AWS_LINUX_ROOT_DISK_SIZE
      root_disk_volume_type = \
        _substrate.get('root_disk_volume_type', DEFAULT_AWS_DISK_VOLUME_TYPE)
      disk_volume_type = \
        AWS_DISK_VOLUME_TYPES_MAP.get(root_disk_volume_type, None)
      if disk_volume_type is None:
        _print(
          user_spawned, "No corresponding name found in aws_volume_type_map"
                        " for [{0}]".format(root_disk_volume_type))
        return None

      volume_types_list = get_list(
        self=self, url='aws/volume_types/list', payload={},
        user_spawned=user_spawned, recall=True)
      if volume_types_list is None:
        return None
      volume_type_found = False
      spare_volume_type = None
      for vol_type in volume_types_list:
        if vol_type['status']['name'] == disk_volume_type.lower():
          volume_type_found = True
          break
        if spare_volume_type is None:
          spare_volume_type = vol_type
      if not volume_type_found:
        _print(user_spawned, "Volume Type [{0}] not found".format(
          root_disk_volume_type))
        if spare_volume_type is None:
          _print(user_spawned, "No Spare or extra volume types found. "
                               "Either volume types list is empty")
          return None
        spare_volume_type_name = spare_volume_type['status']['name']
        spare_volume_type_name = spare_volume_type_name.upper()
        _print(user_spawned, "Adding [{0}] as volume type".
               format(spare_volume_type_name))
        disk_volume_type = spare_volume_type_name

      delete_on_termination = \
        _substrate.get('root_disk_delete_on_termination', True)
      resources_copy['block_device_map']['root_disk']['size_gb'] = \
        root_disk_size
      resources_copy['block_device_map']['root_disk']['volume_type'] = \
        disk_volume_type
      resources_copy['block_device_map']['root_disk'][
        'delete_on_termination'] = delete_on_termination

      # h.ii) Adding ESB disks
      esb_disk_list = _substrate.get('ebs_disk_list', [])
      new_esb_disk_list = [] + esb_disk_list
      if len(esb_disk_list) >= 12:
        _print(user_spawned, "Cannot add [{0}] disks, only adding first 11 "
                             "disks among the given list".
               format(str(len(esb_disk_list))))
        new_esb_disk_list = esb_disk_list[0:11]
      data_disk_list = []
      char_count = 98
      for esb_disk in new_esb_disk_list:
        disk_size = esb_disk.get('disk_size', None)
        if disk_size is None:
          _print(user_spawned, "Disk does not have any size mentioned. "
                               "So giving 1gb as disk size")
          disk_size = 1

        volume_type = esb_disk.get('disk_volume_type')
        disk_vol_type = AWS_DISK_VOLUME_TYPES_MAP.get(volume_type, None)
        if disk_vol_type is None:
          _print(user_spawned, "Volume type [{0}] does not have any name"
                               " corresponding in aws_vol_type_map".
                 format(volume_type))
          return None

        volume_types_list = get_list(
          self=self, url='aws/volume_types/list', payload={},
          user_spawned=user_spawned, recall=True)
        if volume_types_list is None:
          return None
        volume_type_found = False
        spare_volume_type = None
        for vol_type in volume_types_list:
          if vol_type['status']['name'] == disk_volume_type.lower():
            volume_type_found = True
            break
          if spare_volume_type is None:
            spare_volume_type = vol_type
        if not volume_type_found:
          _print(user_spawned, "Volume Type [{0}] not found".
                 format(root_disk_volume_type))
          if spare_volume_type is None:
            _print(
              user_spawned, "No Spare or extra volume types found. Either "
                            "volume types list is empty")
            return None
          spare_volume_type_name = spare_volume_type['status']['name']
          spare_volume_type_name = spare_volume_type_name.upper()
          _print(user_spawned, "Adding [{0}] as volume type".
                 format(spare_volume_type_name))
          disk_vol_type = spare_volume_type_name

        data_disk = {
          'device_name': '/dev/sd{0}'.format(chr(char_count)),
          'size_gb': disk_size,
          'volume_type': disk_vol_type,
          'delete_on_termination': esb_disk.get('delete_on_termination', True)
        }
        char_count += 1
        data_disk_list.append(data_disk)
      if len(data_disk_list) != 0:
        resources_copy['block_device_map']['data_disk_list'] = data_disk_list

      substrate_copy['create_spec']['resources'] = resources_copy
    elif substrate_copy['type'] == 'VMWARE':
      substrate_copy['type'] = 'VMWARE_VM'

      substrate_copy['create_spec']['type'] = 'PROVISION_VMWARE_VM'

      # adding instance name
      vmware_instance_name = _substrate.get('vmware_instance_name', None)
      if vmware_instance_name is None:
        vmware_instance_name = DEFAULT_VMWARE_BLUEPRINT_INSTANCE_NAME
      vmware_instance_name += '_' + id_generator(8)
      vmware_instance_name += '-@@{calm_array_index}@@-@@{calm_time}@@'
      if vmware_instance_name in vmware_instance_names_added:
        _print(user_spawned, "Vmware Instance with name [{0}] already added,"
                             " cannot add duplicate instance names".
               format(vmware_instance_name))
        return None
      vmware_instance_names_added.append(vmware_instance_name)
      substrate_copy['create_spec']['name'] = vmware_instance_name
      #substrate_copy['readiness_probe']['address'] = \
      #  '@@{platform.ipAddressList[0]}@@'
      substrate_copy['readiness_probe']['address'] = ''

      vmware_account_name = _substrate.get(
        'account_name', NUCALM_VMWARE_ACCOUNT_NAME)
      data = {
        'filter': 'state!=DELETED;type==vmware'
      }
      account_list = get_list(self=self, url='accounts/list', payload=data,
                              user_spawned=user_spawned, recall=True)
      vmware_account = next((
        account for account in account_list
        if account['status']['name'] == vmware_account_name), None)
      if vmware_account is None:
        _print(user_spawned, "Account with name [{0}] not found".
               format(vmware_account_name))
        return None

      # 1) adding the host hardware uuid
      host_name = _substrate.get(
        'host_name', DEFAULT_VMWARE_BLUEPRINT_HOST_NAME)
      filters = "account_uuid=={0};".format(vmware_account['metadata']['uuid'])
      data = {
        'filter': filters
      }
      host_list = get_list(self=self, url='vmware/v6/host/list', payload=data,
                           user_spawned=user_spawned, recall=True)
      if len(host_list) == 0:
        _print(user_spawned, "No hosts found")
        return None
      host_hardware_uuid = None
      for _host in host_list:
        if _host['status']['resources']['name'] == host_name:
          host_hardware_uuid = \
            _host['status']['resources']['summary']['hardware']['uuid']
          break
      if host_hardware_uuid is None:
        _print(user_spawned, "Host with name [{0}] not found".
               format(host_name))
        return None
      substrate_copy['create_spec']['host'] = host_hardware_uuid

      # 2) adding the template instance uuid
      template_name = _substrate.get(
        'template_name', DEFAULT_VMWARE_BLUEPRINT_TEMPLATE_NAME)
      template_list = \
        get_list(self=self, url='vmware/v6/template/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      if len(template_list) == 0:
        _print(user_spawned, "No Templates found")
        return None
      template_instance_uuid = None
      for _template in template_list:
        if _template['status']['resources']['name'] == template_name:
          template_instance_uuid = \
            _template['status']['resources']['config']['instanceUuid']
          break
      if template_instance_uuid is None:
        _print(user_spawned, "Template with name [{0}] not found".
               format(template_name))
        return None
      substrate_copy['create_spec']['template'] = template_instance_uuid

      # 3) adding the datastore url
      datastore_name = _substrate.get(
        'datastore_name', DEFAULT_VMWARE_BLUEPRINT_DATASTORE_NAME)
      filters = ''.join([filters, 'host_id=={0}'.format(host_hardware_uuid)])
      data = {
        'filter': filters
      }
      datastore_list = \
        get_list(self=self, url='vmware/v6/datastore/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      if len(datastore_list) == 0:
        _print(user_spawned, "No DataStores found")
        return None
      datastore_url = None
      for _datastore in datastore_list:
        if _datastore['status']['resources']['name'] == datastore_name:
          datastore_url = _datastore['status']['resources']['summary']['url']
          break
      if datastore_url is None:
        _print(user_spawned, "DataStore with name [{0}] not found".
               format(datastore_name))
        return None
      substrate_copy['create_spec']['datastore'] = datastore_url

      # 4) adding resources
      resources = {
        "account_uuid": "",
        "guest_customization": {},
        "num_vcpus_per_socket": "",
        "num_sockets": "",
        "memory_size_mib": "",
        "disk_list": [],
        "nic_list": []
      }

      # 4.a) adding accopunt_uuid, num of sockets, num of vcpus per socket
      #      and memory
      resources_copy = copy.deepcopy(resources)
      resources_copy['account_uuid'] = vmware_account['metadata']['uuid']
      resources_copy['num_sockets'] = _substrate.get('num_of_vcpus', str(1))
      resources_copy['num_vcpus_per_socket'] = \
        _substrate.get('cores_per_vcpu', 1)
      resources_copy['memory_size_mib'] = _substrate.get('memory', 256)
      resources_copy['template_nic_list'] = []

      #fixme: please uncomment when nic_list is neccessary for vcenter
      resources_copy['nic_list'] = [
        {
          #"key": 4000,
          "net_name": "key-vim.host.PortGroup-vlan.501",
          "nic_type": "e1000",
          #"is_deleted": False
        }
      ]


      # 4.b) adding vdisk's
      vdisks = _substrate.get('vdisk', None)
      disk_list = []
      if vdisks is None:
        disk_list.append({
          "disk_type": "disk",
          "adapter_type": "SCSI",
          "disk_size_mb": 8192
        })
      else:
        disk = {
          "disk_type": "",
          "adapter_type": "",
          "disk_size_mb": ""
        }
        for _disk in vdisks:
          disk_copy = copy.deepcopy(disk)
          disk_copy['disk_type'] = _disk.get('device_type')
          disk_copy['adapter_type'] = _disk.get('adapter_type')
          size = _disk.get('size')
          if isinstance(size, int):
            disk_copy['disk_size_mb'] = _disk.get('size') * 1024
          elif isinstance(size, str):
            _print(user_spawned, "WARN: size of disk is in string type "
                                 "changing to int")
            disk_copy['disk_size_mb'] = int(_disk.get('size')) * 1024
          else:
            _print(user_spawned, "Size of disk is neither in int or string")
            return None
          disk_list.append(disk_copy)
      resources_copy['disk_list'] = disk_list

      # 4.c) adding the nic's
      num_of_nics = 1
      nics = _substrate.get('vmware_nic', None)
      if nics is not None:
        nic_list = []
        nic = {
          "nic_type": "",
          "net_name": ""
        }

        for _nic in nics:
          num_of_nics += 1
          nic_copy = copy.deepcopy(nic)
          nic_copy['nic_type'] = _nic.get('nic_type')
          nic_copy['net_name'] = _nic.get('net_name')
          nic_list.append(nic_copy)
        resources_copy['nic_list'] = nic_list

      # 4.d) adding guest customization
      if substrate_copy['os_type'] == 'Linux':
        resources_copy['guest_customization']['customization_type'] = \
          'GUEST_OS_LINUX'
        #fixme: please uncomment when linux data is necessary for vcenter
        #resources_copy['guest_customization']['linux_data'] = {
        #  "hostname": _substrate.get('guest_host_name',
        #                             DEFAULT_VMWARE_BLUEPRINT_GUEST_HOST_NAME),
        #  "domain": _substrate.get('domain',
        #                           DEFAULT_VMWARE_BLUEPRINT_GUEST_DOMAIN),
        #  "timezone": "",
        #  "network_settings": []
        #}

        ## get timezones list
        #filters = "guest_os=={0};".format(
        #  resources_copy['guest_customization']['customization_type'])
        #data = {
        #  'filter': filters
        #}
        #timezone_list = \
        #  get_list(self=self, url='vmware/v6/timezone/list', payload=data,
        #           user_spawned=user_spawned, recall=True)
        #if len(timezone_list) == 0:
        #  _print(user_spawned, "NO Timezones found")
        #  return None
        #timezone_name = _substrate.get('timezone', None)
        #if timezone_name is None:
        #  resources_copy['guest_customization']['linux_data']['timezone'] = \
        #    timezone_list[0]['status']['resources']['name']
        #else:
        #  timezone_found = False
        #  for _timezone in timezone_list:
        #    if _timezone['status']['resources']['name'] == timezone_name:
        #      timezone_found = True
        #      break
        #  if not timezone_found:
        #    _print(user_spawned, "TimeZone [{0}] not found".
        #           format(timezone_name))
        #    return None
        #  resources_copy['guest_customization']['linux_data']['timezone'] = \
        #    timezone_name

        ## adding network settings
        #for i in range(0, num_of_nics):
        #  i += 1
        #  resources_copy['guest_customization']['linux_data'][
        #    'network_settings'].append({"is_dhcp": True})
        #  # fixme: add the appropriate attributes when 'is_dhcp' is False
        #  # fixme: remember that number of nic's == number of network settings

        ## adding DNS setting
        #if _substrate.get('dns_primary', None) is not None:
        #  resources_copy['guest_customization']['linux_data']['dns_primary'] \
        #    = _substrate.get('dns_primary')
        #else:
        #  resources_copy['guest_customization']['linux_data'][
        #    'dns_primary'] = DEFAULT_VMWARE_BLUEPRINT_DNS_PRIMARY

        #if _substrate.get('dns_secondary', None) is not None:
        #  resources_copy['guest_customization']['linux_data'][
        #    'dns_secondary'] = _substrate.get('dns_secondary')
        #else:
        #  resources_copy['guest_customization']['linux_data'][
        #    'dns_secondary'] = DEFAULT_VMWARE_BLUEPRINT_DNS_SECONDARY

        #if _substrate.get('dns_tertiary', None) is not None:
        #  resources_copy['guest_customization']['linux_data'][
        #    'dns_tertiary'] = _substrate.get('dns_tertiary')

        #if _substrate.get('dns_search_path', None) is not None:
        #  resources_copy['guest_customization']['linux_data'][
        #    'dns_search_path'] = _substrate.get('dns_search_path')
        #else:
        #  resources_copy['guest_customization']['linux_data'][
        #    'dns_search_path'] = DEFAULT_VMWARE_BLUEPRINT_DNS_SEARCH_PATH

      else:
        resources_copy['guest_customization']['customization_type'] = \
          'GUEST_OS_WINDOWS'
        # fixme: Please automate for adding windows_data
        resources_copy['template_controller_list'] = [
          {
            "bus_sharing": "noSharing",
            "controller_type": "VirtualLsiLogicSASController",
            "is_deleted": False,
            "key": 1000
          }
        ]
        resources_copy['template_disk_list'] = [
          {
            "adapter_type": "SCSI",
            "controller_key": 1000,
            "device_slot": 0,
            "disk_mode": "persistent",
            "disk_size_mb": 40960,
            "disk_type": "disk",
            "is_deleted": False,
            "key": 2000,
            "location": "ds:///vmfs/volumes/db95445c-3506d74a/"
          },
          {
            "adapter_type": "IDE",
            "controller_key": 200,
            "device_slot": 0,
            "disk_size_mb": None,
            "disk_type": "cdrom",
            "is_deleted": False,
            "key": 3000
          }
        ]

      substrate_copy['create_spec']['resources'] = resources_copy

      # 5) adding editables
      # fixme: add attributes for the editables
      substrate_copy['editables'] = {
        "create_spec": {
          "resources": {
            "disk_list": {},
            "nic_list": {},
            "guest_customization": {
              "linux_data": {
                "network_settings": {}
              }
            }
          }
        }
      }
    elif substrate_copy['type'] == 'GCP':
      substrate_copy['type'] = 'GCP_VM'
      substrate_copy['create_spec']['type'] = 'PROVISION_GCP_VM'
      address_type = _substrate.get('address', None)
      if address_type is None or 'public' in address_type:
        substrate_copy['readiness_probe']['address'] = \
          '@@{public_ip_address}@@'
      else:
        substrate_copy['readiness_probe']['address'] = \
          '@@{private_ip_address}@@'

      # adding resources
      resources = {
        "machineType": "",
        "networkInterfaces": [],
        "name": "",
        "zone": "",
        "account_uuid": "",
        "canIpForward": False,
        "scheduling": {
          "onHostMaintenance": "TERMINATE",
          "preemptible": False,
          "automaticRestart": True
        },
        "disks": [],
        "serviceAccounts": [],
        "sshKeys": [],
        "metadata": {
          "items": []
        }
      }
      resources_copy = copy.deepcopy(resources)

      gcp_account_name = _substrate.get(
        'account_name', DEFAULT_GCP_ACCOUNT_NAME)
      data = {
        'filter': 'state!=DELETED;type==gcp'
      }
      account_list = get_list(self=self, url='accounts/list', payload=data,
                              user_spawned=user_spawned, recall=True)
      gcp_account = \
        next((account for account in account_list
              if account['status']['name'] == gcp_account_name), None)
      if gcp_account is None:
        _print(user_spawned, "Gcp account [{0}] not found".
               format(gcp_account_name))
        return None

      resources_copy['account_uuid'] = gcp_account['metadata']['uuid']

      # a) adding the instance name
      gcp_instance_name = _substrate.get('gcp_instance_name', None)
      if gcp_instance_name is None:
        gcp_instance_name = DEFAULT_GCP_BLUEPRINT_INSTANCE_NAME
      gcp_instance_name += '-' + id_generator(8)
      gcp_instance_name = gcp_instance_name.lower()
      gcp_instance_name += '-@@{calm_array_index}@@-@@{calm_time}@@'
      if gcp_instance_name in gcp_instance_names_added:
        _print(user_spawned, "Gcp Instance with name [{0}] already exists,"
                             " cannot add duplicate instance names".
               format(gcp_instance_name))
        return None
      gcp_instance_names_added.append(gcp_instance_name)
      resources_copy['name'] = gcp_instance_name

      # b) adding the zone
      filters = 'account_uuid=={0};region==undefined'.\
        format(gcp_account['metadata']['uuid'])
      zone_name = _substrate.get('zone_name', DEFAULT_GCP_BLUEPRINT_ZONE_NAME)
      data = {
        'filter': filters
      }
      zones_list = get_list(self=self, url='gcp/v1/zones/list', payload=data,
                            user_spawned=user_spawned, recall=True)

      # Filter zones based on regions added in gcp account or setting
      values = filters.split(';')
      data = {
        'filter': values[0]
      }
      regions_list = \
        get_list(self=self, url='gcp/v1/regions/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      if len(regions_list) == 0:
        _print(user_spawned, "GCP Regions list is empty")
      gcp_regions_names = \
        [region['name'] for region in
         gcp_account['status']['resources']['data']['regions']]
      gcp_regions_links = []
      for region in regions_list:
        reg_name = region['status']['name']
        if reg_name in gcp_regions_names:
          gcp_regions_links.append(region['status']['resources']['selfLink'])
      old_zones = [] + zones_list
      zones_list = []
      for zone in old_zones:
        if zone['status']['resources']['region'] in gcp_regions_links:
          zones_list.append(zone)

      zone_found = False
      is_zone_up = False
      spare_zone = None
      for _zone in zones_list:
        if _zone['status']['name'] == zone_name:
          zone_found = True
          if _zone['status']['resources']['status'] != 'UP':
            _print(user_spawned, "Zone [{0}] is not in up state".
                   format(zone_name))
          else:
            is_zone_up = True
            break
        else:
          if _zone['status']['resources']['status'] == 'UP' and \
              spare_zone is None:
            spare_zone = _zone
      if zone_found and is_zone_up:
        resources_copy['zone'] = zone_name
      elif zone_found and not is_zone_up:
        _print(user_spawned, "Zone [{0}] is found but is not up, So using"
                             " another zone [{1}] which is "
                             "Up".format(zone_name,
                                         spare_zone['status']['name']))
        resources_copy['zone'] = spare_zone['status']['name']
      elif not zone_found and spare_zone is not None:
        _print(user_spawned, "Zone [{0}] not found, Using another zone "
                             "[{1}]".format(zone_name,
                                            spare_zone['status']['name']))
        resources_copy['zone'] = spare_zone['status']['name']
      elif not zone_found and spare_zone is None:
        _print(user_spawned, "No Zone is available")
        return None

      # c) adding machine type
      val = filters.split(';')
      filters = val[0] + ';zone=={0}'.format(zone_name)
      machine_type = _substrate.get(
        'machine_type', DEFAULT_GCP_BLUEPRINT_MACHINE_TYPE)
      data = {
        'filter': filters
      }
      machine_types_list = \
        get_list(self=self, url='gcp/v1/machine_types/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      machine_type_found = False
      for _machine_type in machine_types_list:
        if _machine_type['status']['name'] == machine_type:
          machine_type_found = True
          machine_type_url = _machine_type['status']['resources']['selfLink']
          break
      if not machine_type_found:
        _print(user_spawned, "Machine type [{0}] not found".
               format(machine_type))
        return None
      resources_copy['machineType'] = machine_type_url

      # d) adding disks
      disk = {
        "disk_type": "PERSISTENT",
        "boot": "",
        "autoDelete": "",
        "initializeParams": {
          "diskType": ""
        }
      }
      boot_already_added = False
      disks_to_be_added = _substrate.get('gcp_disks', [])
      disk_list = []
      if len(disks_to_be_added) == 0:
        _print(
          user_spawned, "WARN: There shoule be atleast one disk to be added")
        disk_info = {
          "boot": True,
          "autoDelete": True,
          "diskType": "pd-ssd",
          "sourceImage": "centos-7"
        }
        disks_to_be_added.append(disk_info)
      filters = filters + ';unused==true;private_only==true'
      data = {
        'filter': filters
      }
      disk_types_list = \
        get_list(self=self, url='gcp/v1/disk_types/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      for _disk in disks_to_be_added:
        disk_copy = copy.deepcopy(disk)
        disk_copy['boot'] = _disk['boot']
        if disk_copy['boot']:
          if boot_already_added:
            _print(user_spawned, "Boot Disk is already added,"
                                 " There can be only one boot disk")
            return None
          boot_already_added = True
        if _disk.get('autoDelete', None) is None:
          disk_copy['autoDelete'] = True
        else:
          disk_copy['autoDelete'] = _disk['autoDelete']

        if _disk.get('diskType', None) is None:
          disk_type_name = 'pd-ssd'
        else:
          disk_type_name = _disk['diskType']
        disk_type_url = None
        for _disk_type in disk_types_list:
          if _disk_type['status']['name'] == disk_type_name:
            disk_type_url = _disk_type['status']['resources']['selfLink']
            break
        if disk_type_url is None:
          _print(user_spawned, "DiskType with name [{0}] not "
                               "found".format(disk_type_name))
          return None
        disk_copy['initializeParams']['diskType'] = disk_type_url
        if disk_type_name == 'local-ssd':
          disk_copy['disk_type'] = 'SCRATCH'
          if _disk.get('interface', None) is None:
            disk_copy['interface'] = 'SCSI'
          else:
            disk_copy['interface'] = _disk['interface']
        else:
          if _disk.get('sourceImage', None) is None:
            image_name = 'centos-7'
          else:
            image_name = _disk.get('sourceImage')
          images_list = \
            get_list(self=self, url='gcp/v1/images/list', payload=data,
                     user_spawned=user_spawned, recall=True)
          image_url = None
          for _image in images_list:
            if _image['status']['name'] == image_name:
              image_url = _image['status']['resources']['selfLink']
              break
          if image_url is None:
            _print(user_spawned, "Image with name [{0}] not found".
                   format(image_name))
            return None
          disk_copy['initializeParams']['sourceImage'] = image_url
        disk_list.append(disk_copy)
      resources_copy['disks'] = disk_list

      # e) adding Blank disks
      blank_disk = {
        "autoDelete": "",
        "name": "",
        "disk_type": "",
        "sizeGb": ""
      }
      if _substrate.get('gcp_blank_disks', None) is not None:
        disks_added = []
        blank_disk_list = []
        for _disk in _substrate['gcp_blank_disks']:
          blank_disk_copy = copy.deepcopy(blank_disk)
          if _disk.get('disk_name', None) is None:
            blank_disk_copy['name'] = \
              'blank-disk-' + id_generator(8) + \
              '-@@{calm_array_index}@@-@@{calm_time}@@"'
            disks_added.append(blank_disk_copy['name'])
          else:
            disk_name = \
              _disk['disk_name'] + '-@@{calm_array_index}@@-@@{calm_time}@@"'
            if disk_name in disks_added:
              _print(
                user_spawned, "Disk [{0}] already added".format(disk_name))
              return None
            blank_disk_copy['name'] = disk_name

          if _disk.get('autoDelete', None) is None:
            blank_disk_copy['autoDelete'] = True
          else:
            blank_disk_copy['autoDelete'] = _disk['autoDelete']

          if _disk.get('size', None) is None:
            blank_disk_copy['sizeGb'] = 1
          else:
            blank_disk_copy['sizeGb'] = _disk['size']

          if _disk.get('disk_type', None) is None:
            disk_type_name = 'pd-ssd'
          else:
            disk_type_name = _disk['disk_type']
          disk_type_url = None
          for _disk_type in disk_types_list:
            if _disk_type.name == disk_type_name:
              disk_type_url = _disk_type.resources['selfLink']
              break
          if disk_type_url is None:
            _print(
              user_spawned, "Disk Type [{0}] not found".format(disk_type_name))
            return None
          blank_disk_copy['disk_type'] = disk_type_url
          blank_disk_list.append(blank_disk_copy)
        resources_copy['blankDisks'] = blank_disk_list

      # f) adding Networks
      network = {
        "accessConfigs": [],
        "network": "",
        "subnetwork": ""
      }
      network_to_be_added = _substrate.get('network', [])
      if len(network_to_be_added) == 0:
        _print(user_spawned, "WARN: Atleast one network is required")
        network_info = {
          "network": "default",
          "subnetwork": "default",
          "access_configuration_type": "ONE_TO_ONE_NAT",
          "access_configuration_name": "Network-{0}".format(
            str(id_generator(8)))
        }
        network_to_be_added.append(network_info)

      val = filters.split(';')
      filters = val[0] + ';' + val[1]
      data = {
        'filter': filters
      }
      networks_list = \
        get_list(self=self, url='gcp/v1/networks/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      subnetworks_list = \
        get_list(self=self, url='gcp/v1/subnetworks/list', payload=data,
                 user_spawned=user_spawned, recall=True)
      network_list = []
      networks_added = []
      for _network in network_to_be_added:
        # fixme: The fields are assumed to be given, add a way to give
        #        field values dynamically
        network_copy = copy.deepcopy(network)
        if _network.get('network', None) is None:
          _print(user_spawned, "Network is required")
          return None
        network_name = _network['network']
        network_url = None
        for _net in networks_list:
          if _net['status']['name'] == network_name:
            network_url = _net['status']['resources']['selfLink']
            break
        if network_url is None:
          _print(
            user_spawned, "Network [{0}] not found".format(network_name))
          return None
        network_copy['network'] = network_url

        if _network.get('subnetwork', None) is None:
          _print(user_spawned, "Subnetwork is required")
          return None
        subnet_name = _network['subnetwork']
        subnet_url = None
        for _subnet in subnetworks_list:
          if _subnet['status']['name'] == subnet_name:
            subnet_url = _subnet['status']['resources']['selfLink']
            break
        if subnet_url is None:
          _print(user_spawned, "Subnet with name [{0}] not "
                               "found".format(subnet_name))
          return None
        network_copy['subnetwork'] = subnet_url

        network_config = {}
        if _network.get('access_configuration_type', None) is None:
          network_config['config_type'] = 'ONE_TO_ONE_NAT'
        else:
          network_config['config_type'] = _network['access_configuration_type']

        if _network.get('access_configuration_name', None) is None:
          network_config['name'] = 'Network-' + id_generator(8)
          networks_added.append(network_config['name'])
        else:
          name = _network['access_configuration_name']
          if name in networks_added:
            _print(user_spawned, "Access Configuration Name [{0}] already "
                                 "exists".format(name))
            return None
          network_config['name'] = name
        network_copy['accessConfigs'].append(network_config)
        network_list.append(network_copy)
      resources_copy['networkInterfaces'] = network_list

      # g) adding ssh keys
      ssh_keys = _substrate.get('ssh_keys', [])
      if len(ssh_keys) == 0:
        _print(user_spawned, "Atleast one ssh key should be added")
        return None
      for _ssh_key in ssh_keys:
        resources_copy['sshKeys'].append(_ssh_key)

      # h) adding service accounts scope
      # fixme: Write methods for adding service accounts dynamically

      default_access_scope = [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/logging.write",
        "https://www.googleapis.com/auth/monitoring.write",
        "https://www.googleapis.com/auth/servicecontrol",
        "https://www.googleapis.com/auth/service.management.readonly",
        "https://www.googleapis.com/auth/trace.append"
      ]
      full_access_scope = [
        "https://www.googleapis.com/auth/cloud-platform"
      ]
      resources_copy['serviceAccounts'] = [
        {
          "email": "108048128720-compute@developer.gserviceaccount.com",
          "scopes": []
        }
      ]
      scope = _substrate.get('service_account_scope', 'default_access')
      if scope == 'default_access':
        resources_copy['serviceAccounts'][0]['scopes'] = default_access_scope
      elif scope == 'full_access':
        resources_copy['serviceAccounts'][0]['scopes'] = full_access_scope

      # i) adding metdata items
      block_project_ssh_keys = _substrate.get('block_project_ssh_keys', None)
      if block_project_ssh_keys is not None:
        resources_copy['metadata']['items'].append(
          {
            "key": "block_project_ssh_keys",
            "value": True
          }
        )

      # fixme: add ways for adding canIpForward and scheduling
      substrate_copy['create_spec']['resources'] = resources_copy
    elif substrate_copy['type'] == 'AZURE':
      substrate_copy['type'] = 'AZURE_VM'
      substrate_copy['create_spec']['type'] = 'PROVISION_AZURE_VM'
      address_type = _substrate.get('azure_connection_address', None)
      if address_type is None or 'public' in address_type:
        substrate_copy['readiness_probe']['address'] = \
          '@@{platform.publicIPAddressList[0]}@@'
      else:
        substrate_copy['readiness_probe']['address'] = \
          '@@{platform.privateIPAddressList[0]}@@'

      substrate_copy['editables'] = {
        "create_spec": {
          "resources": {
            "nw_profile": {},
            "storage_profile": {}
          }
        }
      }

      resources = {
        "storage_profile": {
          "is_managed": True,
          "data_disk_list": [],
          "os_disk_details": {
            "name": "",
            "create_option": "",
            "caching_type": "",
            "size_in_gb": 30,
            "storage_type": ""
          },
          "image_details": {
            "publisher": "",
            "offer": "",
            "sku": "",
            "version": ""
          }
        },
        "account_uuid": "",
        "os_profile": {
          "windows_config": {}
        },
        "resource_group": "",
        "nw_profile": {},
        "vm_name": "",
        "location": "",
        "hw_profile": {},
        "availability_set_id": ""
      }
      resources_copy = copy.deepcopy(resources)

      # a) adding account uuid
      azure_account_name = _substrate.get(
        'account_name', DEFAULT_AZURE_ACCOUNT_NAME)
      data = {
        'filter': 'state!=DELETED;type==azure'
      }
      account_list = get_list(self=self, url='accounts/list', payload=data,
                              user_spawned=user_spawned, recall=True)
      azure_account = next((
        account for account in account_list
        if account['metadata']['name'] == azure_account_name), None)
      if azure_account is None:
        _print(user_spawned, "Azure account with name [{0}] not "
                             "found".format(azure_account_name))
        return None
      resources_copy['account_uuid'] = azure_account['metadata']['uuid']

      # b) adding instance name
      azure_instance_name = _substrate.get('azure_instance_name', None)
      if azure_instance_name is None:
        azure_instance_name = DEFAULT_AZURE_BLUEPRINT_INSTANCE_NAME
      azure_instance_name += '@@{calm_random()}@@'
      ## please enable this condition if we are using same name for all vms
      #if azure_instance_name in azure_instance_names_added:
      #  _print(user_spawned, "Azure Instance with name [{0}] already added,"
      #                       " cannot add duplicate instance names".
      #         format(azure_instance_name))
      #  return None
      azure_instance_names_added.append(azure_instance_name)
      resources_copy['vm_name'] = azure_instance_name

      # c) adding resource group
      filters = 'account_uuid=={0}'.format(azure_account['metadata']['uuid'])
      resource_group_name = _substrate.get(
        'resource_group_name', DEFAULT_AZURE_RESOURCE_GROUP_NAME)
      data = {
        'filter': filters
      }
      resource_groups_list = get_list(
        self=self, url='azure_rm/v1/resource_groups/list', payload=data,
        user_spawned=user_spawned, recall=True)
      resource_group_found = next((
        _resource_group for _resource_group in resource_groups_list
        if _resource_group['status']['name'] == resource_group_name), None)
      if resource_group_found is None:
        _print(user_spawned, "Resource Group with name [{0}] not found".
               format(resource_group_name))
        return None
      resources_copy['resource_group'] = resource_group_name

      # d) adding location
      location_name = \
        _substrate.get('location_name', DEFAULT_AZURE_LOCATION_NAME)
      locations_list = get_list(
        self=self, url='azure_rm/v1/locations/list', payload=data,
        user_spawned=user_spawned, recall=True)
      location_found = next((
        _location for _location in locations_list
        if _location['status']['name'] == location_name), None)
      if location_found is None:
        _print(user_spawned, "Location with name [{0}] not "
                             "found".format(location_name))
        return None
      resources_copy['location'] = location_name

      # e) adding availability sets
      filters += ';resource_group=={0}'.format(resource_group_name)
      availability_set_name = _substrate.get(
        'availability_set_name', DEFAULT_AZURE_AVAILABILITY_SET_NAME)
      data = {
        'filter': filters
      }
      availability_sets_list = get_list(
        self=self, url='azure_rm/v1/availability_sets/list', payload=data,
        user_spawned=user_spawned, recall=True)
      availability_set_found = next((
        _availability_set for _availability_set in availability_sets_list
        if _availability_set['status']['name'] == availability_set_name), None)
      if availability_set_found is None:
        _print(user_spawned, "Availability set with name [{0}] not "
                             "found".format(availability_set_name))
        #fixme: Availability set is not used in this locaiton
        #please review this comments any further modificatios.
        #return None
      #resources_copy['availability_set_id'] = \
        #availability_set_found['status']['resources']['id']

      # f) adding hardware profile
      filters_values = filters.split(';')
      filters = filters_values[0] + ';location=={0}'.format(location_name)
      vm_size_name = _substrate.get('vm_size_name', DEFAULT_AZURE_VM_SIZE_NAME)
      data = {
        'filter': filters
      }
      vm_sizes_list = get_list(
        self=self, url='azure_rm/v1/vm_sizes/list', payload=data,
        user_spawned=user_spawned, recall=True)
      vm_size_found = next((
        _vm_size for _vm_size in vm_sizes_list
        if _vm_size['status']['name'] == vm_size_name), None)
      if vm_size_found is None:
        _print(user_spawned, "Vm size type with name [{0}] not "
                             "found".format(vm_size_name))
        return None
      resources_copy['hw_profile']['vm_size'] = vm_size_name

      # g) adding image publishers
      image_publisher_name = _substrate.get(
        'image_publisher_name', DEFAULT_AZURE_IMAGE_PUBLISHER_NAME)
      image_publishers_list = get_list(
        self=self, url='azure_rm/v1/image_publishers/list', payload=data,
        user_spawned=user_spawned, recall=True)
      image_publisher_found = next((
        _image_publisher for _image_publisher in image_publishers_list
        if _image_publisher['status']['name'] == image_publisher_name), None)
      if image_publisher_found is None:
        _print(user_spawned, "Image Publisher with name [{0}] not "
                             "found".format(image_publisher_name))
        return None
      resources_copy['storage_profile']['image_details']['publisher'] = \
        image_publisher_name

      # fixme: add way for adding custom images.
      # h) adding image offers
      filters += ';publisher=={0}'.format(image_publisher_name)
      image_offer_name = _substrate.get(
        'image_offer_name', DEFAULT_AZURE_IMAGE_OFFER_NAME)
      data = {
        'filter': filters
      }
      image_offers_list = get_list(
        self=self, url='azure_rm/v1/image_offers/list', payload=data,
        user_spawned=user_spawned, recall=True)
      image_offer_found = next((
        _image_offer for _image_offer in image_offers_list
        if _image_offer['status']['name'] == image_offer_name), None)
      if image_offer_found is None:
        _print(user_spawned, "Image offer with name [{0}] not "
                             "found".format(image_offer_name))
        return None
      resources_copy['storage_profile']['image_details']['offer'] = \
        image_offer_name

      # i) adding image sku
      filters += ';offer=={0}'.format(image_offer_name)
      image_sku_name = \
        _substrate.get('image_sku_name', DEFAULT_AZURE_IMAGE_SKU)
      data = {
        'filter': filters
      }
      image_skus_list = get_list(
        self=self, url='azure_rm/v1/image_skus/list', payload=data,
        user_spawned=user_spawned, recall=True)
      image_sku_found = next((
        _image_sku for _image_sku in image_skus_list
        if _image_sku['status']['name'] == image_sku_name), None)
      if image_sku_found is None:
        _print(user_spawned, "Image sku with name [{0}] not "
                             "found".format(image_sku_name))
        return None
      resources_copy['storage_profile']['image_details']['sku'] = \
        image_sku_name

      # j) adding image version
      filters += ';sku=={0}'.format(image_sku_name)
      image_version = \
        _substrate.get('image_version', DEFAULT_AZURE_IMAGE_VERSION)
      data = {
        'filter': filters
      }
      image_versions_list = get_list(
        self=self, url='azure_rm/v1/image_versions/list', payload=data,
        user_spawned=user_spawned, recall=True)
      image_version_found = next((
        _image_version for _image_version in image_versions_list
        if _image_version['status']['name'] == image_version), None)
      if image_version_found is None:
        _print(user_spawned, "Image version [{0}] not "
                             "found".format(image_version))
        return None
      resources_copy['storage_profile']['image_details']['version'] = \
        image_version

      # fixme: add method for 'managed disks' option

      # k) adding disk name
      disk_name = _substrate.get('azure_disk_name', DEFAULT_AZURE_DISK_NAME)
      disk_name += '-@@{calm_random_hash}@@-@@{calm_array_index}@@-disk'
      resources_copy['storage_profile']['os_disk_details']['name'] = disk_name

      # l) adding disk storage type
      storage_type = \
        _substrate.get('azure_storage_type', DEFAULT_AZURE_STORAGE_TYPE)
      storage_type += '_LRS'
      resources_copy['storage_profile']['os_disk_details']['storage_type'] = \
        storage_type

      # m) adding disk caching type
      disk_caching_type = _substrate.get(
        'azure_disk_caching_type', DEFAULT_AZURE_DISK_CACHING_TYPE)
      resources_copy['storage_profile']['os_disk_details']['caching_type'] = \
        disk_caching_type

      # n) adding disk create options
      disk_create_option = _substrate.get(
        'azure_disk_create_option', DEFAULT_AZURE_DISK_CREATE_OPTION)
      resources_copy['storage_profile']['os_disk_details']['create_option'] = \
        disk_create_option

      # o) adding disk size
      disk_size = _substrate.get('azure_disk_size', DEFAULT_AZURE_DISK_SIZE)
      resources_copy['storage_profile']['os_disk_details']['size_in_gb'] = \
        disk_size

      # p) adding network profiles.
      nic_to_be_added = _substrate.get('nic_list', [])
      if len(nic_to_be_added) == 0:
        _print(user_spawned, "Atleast one nic should be added, so adding "
                             "the default one")
        nic_to_be_added = [
          {
            "nic_name": DEFAULT_AZURE_NIC_NAME,
            "security_group": DEFAULT_AZURE_SECURITY_GROUP,
            "virtual_network": DEFAULT_AZURE_VIRTUAL_NETWORK,
            "subnet": DEFAULT_AZURE_SUBNET_NAME,
            "public_ip_name": DEFAULT_AZURE_PUBLIC_IP_NAME,
            "public_ip_allocation_method":
              DEFAULT_AZURE_PUBLIC_IP_ALLOCATION_METHOD,
            "public_ip_dns_label": DEFAULT_AZURE_PUBLIC_IP_DNS_LABEL,
            "private_ip_allocation_method":
              DEFAULT_AZURE_PRIVATE_IP_ALLOCATION_METHOD
          }
        ]

      nic_dict = {
        "vnet_name": "",
        "nsg_name": "",
        "private_ip_info": {
          "ip_allocation_method": ""
        },
        "nic_name": "",
        "subnet_name": "",
        "public_ip_info": {
          "ip_name": "",
          "dns_label": "",
          "ip_allocation_method": ""
        }
      }

      nic_list = []
      nic_count = 0
      for nic in nic_to_be_added:
        nic_info = copy.deepcopy(nic_dict)

        # 1. adding nic name
        nic_name = nic.get('nic_name', DEFAULT_AZURE_NIC_NAME)
        nic_count += 1
        nic_name += '-@@{calm_random_hash}@@-@@{calm_array_index}@@-'
        nic_name += '{0}'.format(str(nic_count))
        nic_info['nic_name'] = nic_name

        # 2. adding security group
        security_group = \
          nic.get('security_group', DEFAULT_AZURE_SECURITY_GROUP)
        filters_values = filters.split(';')
        filters = filters_values[0] + \
                  ';resource_group=={0}'.format(resource_group_name)
        data = {
          'filter': filters
        }
        security_groups_list = get_list(
          self=self, url='azure_rm/v1/security_groups/list', payload=data,
          user_spawned=user_spawned, recall=True)
        security_group_found = next((
          _security_group for _security_group in security_groups_list
          if _security_group['status']['name'] == security_group), None)
        if security_group_found is None:
          _print(user_spawned, "Security group with name [{0}] not "
                               "found".format(security_group))
          return None
        nic_info['nsg_name'] = security_group

        # 3. adding virtual network
        virtual_network_name = \
          nic.get('virtual_network', DEFAULT_AZURE_VIRTUAL_NETWORK)
        virtual_networks_list = get_list(
          self=self, url='azure_rm/v1/virtual_networks/list', payload=data,
          user_spawned=user_spawned, recall=True)
        virtual_network_found = next((
          _virtual_network for _virtual_network in virtual_networks_list
          if _virtual_network['status']['name'] == virtual_network_name), None)
        if virtual_network_found is None:
          _print(user_spawned, "Virtual Network with name [{0}] not "
                               "found".format(virtual_network_name))
          return None
        nic_info['vnet_name'] = virtual_network_name

        # 4. adding subnet
        filters += ';virtual_network=={0}'.format(virtual_network_name)
        subnet_name = nic.get('subnet', DEFAULT_AZURE_SUBNET_NAME)
        data = {
          'filter': filters
        }
        subnets_list = get_list(
          self=self, url='azure_rm/v1/subnets/list', payload=data,
          user_spawned=user_spawned, recall=True)
        subnet_found = next((
          _subnet for _subnet in subnets_list
          if _subnet['status']['name'] == subnet_name), None)
        if subnet_found is None:
          _print(user_spawned, "Subnet with name [{0}] not "
                               "found".format(subnet_name))
          return None
        nic_info['subnet_name'] = subnet_name

        # 5. adding public ip info
        ip_name = nic.get('public_ip_name', DEFAULT_AZURE_PUBLIC_IP_NAME)
        ip_name += '-@@{calm_random_hash}@@-@@{calm_array_index}@@-'
        ip_name += '{0}'.format(str(nic_count))
        nic_info['public_ip_info']['ip_name'] = ip_name
        nic_info['public_ip_info']['ip_allocation_method'] = \
          nic.get('public_ip_allocation_method',
                  DEFAULT_AZURE_PUBLIC_IP_ALLOCATION_METHOD)
        dns_label = \
          nic.get('public_ip_dns_label', DEFAULT_AZURE_PUBLIC_IP_DNS_LABEL)
        dns_label += '-@@{calm_random_hash}@@-@@{calm_array_index}@@-'
        dns_label += '{0}'.format(str(nic_count))
        nic_info['public_ip_info']['dns_label'] = dns_label

        # 6. adding private ip info
        nic_info['private_ip_info']['ip_allocation_method'] = \
          nic.get('private_ip_allocation_method',
                  DEFAULT_AZURE_PRIVATE_IP_ALLOCATION_METHOD)

        nic_list.append(nic_info)
      resources_copy['nw_profile'] = {
        'nic_list': nic_list
      }

      # q. adding os profile
      if substrate_copy['os_type'] == 'Windows':
        provision_vm_agent = _substrate.get('provision_vm_agent', True)
        auto_update = _substrate.get('auto_update', False)
        resources_copy['os_profile']['windows_config'] = {
          'provision_vm_agent': provision_vm_agent,
          'auto_updates': auto_update
        }
      else:
        resources_copy['os_profile']['windows_config'] = {
          'provision_vm_agent': True
        }
      substrate_copy['create_spec']['resources'] = resources_copy
    elif substrate_copy['type'] == "K8S_POD":
      create_spec = {
        'account_uuid': '',
        'metadata': {
          'labels': {},
          'name': 'POD',
          'namespace': ''
        },
        'spec': {
          'restartPolicy': ''
        }
      }
      del substrate_copy['readiness_probe']['login_credential_local_reference']
      substrate_copy['type'] = 'K8S_POD'
      account_name = _substrate.get('account_name', \
        DEFAULT_GCP_ACCOUNT_NAME)
      data = {
        'filter': 'state!=DELETED;type==gcp'
      }
      account_list = get_list(self=self, url='accounts/list', payload=data,
                              user_spawned=user_spawned, recall=True)
      if account_list is None:
        return None

      account = next((account for account in account_list
                      if account['status']['name'] == account_name), None)
      if account is None:
        _print(user_spawned,
               "Account with name [{0}] not found".format(account_name))
        return None
      create_spec['account_uuid'] = account['metadata']['uuid']
      create_spec['spec']['restartPolicy'] = _substrate.get('restartpolicy', \
                                             NUCALM_KUBERNETES_RESTARTPOLICY)
      create_spec['metadata']['namespace'] = _substrate.get('namespace', \
                                             NUCALM_KUBERNETES_NAMESPACE)
      if _substrate.get('labels'):
        create_spec['metadata']['labels'] = _substrate.get('labels')
      else:
        _print(user_spawned, "ERROR: Unables to get labels for creating PODs")
        return None
      substrate_copy['create_spec'] = create_spec
    substrate_list.append(substrate_copy)
  return substrate_list

def add_images(self, **kwargs):
  """
  This method adds the images
  Args:
     kwargs:
      images_to_be_added(list): list of images to be added
      is_host_pc(bool): remote PC or host PC
      remote_pc_ip((str): PC ip of remote PC
      user_spawned(str): name of the locust user spawned

  Returns:
    image_list(list): list of all the images
                  or
    None if some images are not found
  """
  images_to_be_added = kwargs.get('images_to_be_added')
  is_host_pc = kwargs.get('is_host_pc', True)
  remote_pc_ip = kwargs.get('remote_pc_ip', '')
  user_spawned = kwargs.get('user_spawned', '')

  if len(images_to_be_added) == 0:
    images_to_be_added = [
      {
        "name": DEFAULT_AHV_BLUEPRINT_LINUX_IMAGE_NAME,
        "device_type": DEFAULT_AHV_BLUEPRINT_DISK_TYPE,
        "adapter_type": DEFAULT_AHV_BLUEPRINT_DEVICE_BUS
      }
    ]

  disk = {
    "data_source_reference": {
      "kind": "image",
      "name": "",
      "uuid": ""
    },
    "device_properties": {
      "device_type": "",
      "disk_address": {
        "device_index": 0,
        "adapter_type": ""
      }
    }
  }

  disk_list = []
  image_names_list = []
  images_not_found = []

  for _image in images_to_be_added:
    if not is_host_pc:
      url = "https://{}:9440/api/nutanix/v3/images/list".format(remote_pc_ip)
      response = self.client.post(url, data=json.dumps({}))
      response = response_check(response)
      if response is None:
        _print(user_spawned, "Error in response of url - [{0}]".format(url))
        return None
      images_list = response['entities']
    else:
      images_list = get_list(self=self, url='images/list', payload={})

    if images_list is None:
      return None
    image = next((image for image in images_list
                  if image['status']['name'] == _image.get('name')), None)
    if image is None:
      if not is_host_pc:
        print("images aren't found in remote_pc [{}]".format(remote_pc_ip))
      images_not_found.append(_image['name'])
      continue
    disk_copy = copy.deepcopy(disk)
    image_name = image['status']['name']
    if validate_if_duplicate_entity(
        entity_name=image_name, entity_names_list=image_names_list,
        entity_type='Image', user_spawned=user_spawned):
      return None
    image_names_list.append(image_name)
    disk_copy['data_source_reference']['name'] = image_name
    disk_copy['data_source_reference']['uuid'] = image['metadata']['uuid']
    disk_copy['device_properties']['device_type'] = _image.get('device_type')
    disk_copy['device_properties']['disk_address']['adapter_type'] = \
      _image.get('adapter_type')
    disk_list.append(disk_copy)

  if len(images_not_found) != 0:
    _print(user_spawned, "[{0}/{1}] images not found\nImages not found are "
                         "{2}".format(str(len(images_not_found)),
                                      str(len(images_to_be_added)),
                                      "\n".join(images_not_found)))
    return None
  return disk_list


def add_network_adapters(self, **kwargs):
  """
  This method adds the newtwork_adapters(NIC)
  Args:
    kwargs:
      nic_to_be_added(list): list of NIC to be added
      is_host_pc(bool): remote PC or host PC
      remote_pc_ip((str): PC ip of remote PC
      user_spawned(str): name of the locust user spawned
       vm_type(str): type of vm (single or multi)
  Returns:
    nic_list(list): list of all the nic's added
                    or
    None if some Nic's are not found
  """
  nic_to_be_added = kwargs.get('nic_to_be_added')
  user_spawned = kwargs.get('user_spawned', '')
  vm_type = kwargs.get('vm_type', 'multi')
  is_host_pc = kwargs.get('is_host_pc', True)
  remote_pc_ip = kwargs.get('remote_pc_ip', '')
  external_network_list = kwargs.get('external_network_list', [])
  subnet_reference_list = kwargs.get('subnet_reference_list', [])

  subnet_reference_list.extend(external_network_list)

  if len(nic_to_be_added) == 0:
    nic_to_be_added = [
      {
        "name": DEFAULT_AHV_BLUEPRINT_NIC
      }
    ]

  nic = {
    "subnet_reference": {
      "uuid": ""
    }
  }
  if vm_type == 'multi':
    nic["ip_endpoint_list"] = []

  nic_list = []
  nic_names_list = []
  subnets_not_found = []

  for _nic in nic_to_be_added:
    subnet_name = _nic.get('name')
    if validate_if_duplicate_entity(
        entity_name=subnet_name, entity_names_list=nic_names_list,
        entity_type='NIC', user_spawned=user_spawned):
      return None
    nic_names_list.append(subnet_name)
    pay = {
      "length":250,
      "offset":0,
      "filter":""
    }
    pro_subnets_list = []
    if not is_host_pc:
      url = "https://{}:9440/api/nutanix/v3/subnets/list".format(remote_pc_ip)
      response = self.client.post(url, data=json.dumps(pay))
      response = response_check(response)
      if response is None:
        _print(user_spawned, "Error in response of url - [{0}]".format(url))
        return None
      subnets_list = response['entities']
    else:
      subnets_list = get_list(self=self, url='subnets/list', payload=pay,
                              user_spawned=user_spawned)

    if subnets_list is None:
      return None

    not_added_subs = []
    for subnet in subnets_list:
      subnet_data = next((subnet for entity in subnet_reference_list \
                          if entity['uuid'] == subnet['metadata']['uuid']), \
                          None)
      if subnet_data is None:
        not_added_subs.append(subnet['status']['name'])
        continue
      pro_subnets_list.append(subnet)

    if len(not_added_subs) > 0:
      print("INFO: Subnets {} is/are not added in project" \
              .format(not_added_subs))

    subnet = next((subnet for subnet in pro_subnets_list
                   if subnet['status']['name'] == subnet_name), None)
    if subnet is None:
      subnets_not_found.append(_nic.get('name'))
      continue

    nic_copy = copy.deepcopy(nic)
    if 'SUBNET_UUID' in os.environ:
      subnet_uuid = os.environ['SUBNET_UUID']
    else:
      subnet_uuid = subnet['metadata']['uuid']
    nic_copy['subnet_reference']['uuid'] = subnet_uuid

    nic_list.append(nic_copy)

  if len(subnets_not_found) != 0:
    _print(user_spawned, "[{0}/{1}] subnets not found\nSubnets not found "
                         "are {2}".format(str(len(subnets_not_found)),
                                          str(len(nic_to_be_added)),
                                          "\n".join(subnets_not_found)))
    return None

  return nic_list

def add_security_groups(self, **kwargs):
  """
  This method adds the security groups
  Args:
    kwargs:
      security_groups_to_be_added(list): list of names of security groups to be
        added
      filters(string): filter string for list API call
      user_spawned(str): name of the locust user spawned

  Returns:
    security_groups(list): list of all the security groups added
                  or
    None
  """
  security_groups_to_be_added = kwargs.get('security_groups_to_be_added')
  filters = kwargs.get('filters')
  user_spawned = kwargs.get('user_spawned', '')
  if len(security_groups_to_be_added) == 0:
    security_groups_to_be_added = [DEFAULT_AWS_SECURITY_GROUP_NAME]
  data = {
    'filter': filters
  }
  security_groups_list = \
    get_list(self=self, url='aws/security_groups/list', payload=data,
             user_spawned=user_spawned, recall=True)
  if security_groups_list is None:
    return None
  if length_check(security_groups_list, 'security_group', user_spawned) is \
      None:
    return None

  security_groups = []
  security_groups_found = []
  security_groups_names_found = []
  security_groups_not_found = []

  for security_group in security_groups_list:
    if security_group['status']['name'] in security_groups_to_be_added:
      security_groups_found.append(security_group)
      security_groups_names_found.append(security_group['status']['name'])

  for security_group in security_groups_to_be_added:
    if security_group not in security_groups_names_found:
      security_groups_not_found.append(security_group)

  if len(security_groups_not_found) != 0:
    _print(
      user_spawned, "[{0}/{1}] security groups not found\n The security "
                    "groups not found are "
                    "{2}".format(len(security_groups_not_found),
                                 len(security_groups_to_be_added),
                                 "\n".join(security_groups_not_found)))
    return None

  for security_group in security_groups_found:
    security_groups.append({
      "security_group_id": security_group['status']['resources']['id']
    })
  return security_groups


def add_packages(**kwargs):
  """
  This method adds the packages
  Args:
    kwargs:
      packages_to_be_added(list): list of all the packages
      service_list(list): list of all the services
      credential_list(list): list of all the credentials
      user_spawned(str): name of the locust user spawned

  Returns:
    package_list(list): list of all the packages added
  """
  packages_to_be_added = kwargs.get('packages_to_be_added')
  service_list = kwargs.get('service_list')
  credential_list = kwargs.get('credential_list')
  user_spawned = kwargs.get('user_spawned', '')
  cloud = kwargs.get('cloud', None)
  package = {
    "type": "",
    "service_local_reference_list": [],
    "variable_list": [],
    "options": {},
    "name": "",
    "uuid": ""
  }

  services_with_packages = []
  package_list = []
  package_names_list = []
  package_not_supported_error_message = ""
  package_not_supported = False
  for _package in packages_to_be_added:
    package_name = _package.get('name')
    if validate_if_duplicate_entity(
        entity_name=package_name, entity_names_list=package_names_list,
        entity_type='Package', user_spawned=user_spawned):
      return None
    package_names_list.append(package_name)
    package_copy = copy.deepcopy(package)
    package_copy['name'] = package_name
    package_copy['uuid'] = str(uuid.uuid4())
    package_copy['type'] = _package.get('type')

    if package_copy['type'] in ['DEB', 'K8S_IMAGE']:
      # if pkg_type==DEB:
      service_name = _package.get('service_name')
      services_with_packages.append(service_name)
      service = next((service for service in service_list
                      if service.get('name') == service_name), None)
      if service is None:
        _print(user_spawned, "Service with name [{0}] not "
                             "found".format(service_name))
        return None
      service_local_reference = {
        "kind": "app_service",
        "uuid": service.get('uuid')
      }
      package_copy['service_local_reference_list']. \
        append(service_local_reference)

      # fixme: add code here for adding variables

      all_install_tasks_dependent = \
        _package.get('all_install_tasks_dependent', False)
      install_tasks_to_be_added = _package.get('install_tasks', [])
      if cloud:
        for _task in install_tasks_to_be_added:
          if cloud == 'AZURE':
            _task['credential_name'] = 'OS admin credential'
          elif cloud == 'AWS':
            _task['credential_name'] = 'centos'
          elif cloud == 'GCP':
            _task['credential_name'] = 'srinivasan'
          else:
            _task['credential_name'] = 'root'

      for _task in install_tasks_to_be_added:
        _task['service_name'] = service_name
      install_runbook = add_runbook(
        tasks_to_be_added=install_tasks_to_be_added, variables_to_be_added=[],
        task_uuid=package_copy['uuid'], kind_uuid=service.get('uuid'),
        credential_list=credential_list, service_list=service_list,
        main_task_kind='app_package', kind='app_service',
        all_tasks_dependent=all_install_tasks_dependent)
      if install_runbook is None:
        _print(user_spawned, "Failed to create install runbook for package "
                             "[{0}]".format(package_name))
        return None
      package_copy['options']['install_runbook'] = install_runbook

      all_uninstall_tasks_dependent = \
        _package.get('all_uninstall_tasks_dependent', False)
      uninstall_tasks_to_be_added = _package.get('uninstall_tasks', [])
      if cloud:
        for _task in uninstall_tasks_to_be_added:
          if cloud == 'AZURE':
            _task['credential_name'] = 'OS admin credential'
          elif cloud == 'AWS':
            _task['credential_name'] = 'centos'
          elif cloud == 'GCP':
            _task['credential_name'] = 'srinivasan.subramanian'
          else:
            _task['credential_name'] = 'root'

      for _task in uninstall_tasks_to_be_added:
        _task['service_name'] = service_name
      uninstall_runbook = add_runbook(
        main_task_kind='app_package', task_uuid=package_copy['uuid'],
        kind_uuid=service.get('uuid'), variables_to_be_added=[],
        kind='app_service', credential_list=credential_list,
        all_tasks_dependent=all_uninstall_tasks_dependent,
        tasks_to_be_added=uninstall_tasks_to_be_added,
        service_list=service_list)
      if uninstall_runbook is None:
        _print(user_spawned, "Failed to create uninstall runbook for package "
                             "[{0}]".format(package_name))
        return None
      package_copy['options']['uninstall_runbook'] = uninstall_runbook
      if package_copy['type'] == 'K8S_IMAGE':
        package_copy['image_spec'] = {
          'image': _package.get('image', NUCALM_KUBERNETES_IMAGE),
          'imagePullPolicy': 'IfNotPresent'
        }
        del package_copy['options']['uninstall_runbook']
        del package_copy['options']['install_runbook']

    elif package_copy['type'] == 'SUBSTRATE_IMAGE':
      # if pkg_type is SUBSTRATE_IMAGE
      new_options = {
        "name": _package.get('image_name', ''),
        "resources": {
          "image_type": _package.get('image_type', ''),
          "architecture": _package.get('image_architecture', ''),
          "source_uri": _package.get('image_source_uri', ''),
          "version": {
            "product_name": _package.get('product_name', ''),
            "product_version": _package.get('product_version', ''),
            "type": ""
          }
        }
      }
      if _package.get('image_type', '') == 'ISO_IMAGE':
        new_options['resources']['checksum'] = {
          "checksum_algorithm": _package.get('checksum_algorithm', ''),
          "checksum_value": _package.get('checksum_value', '')
        }
      package_copy['options'] = new_options

    else:
      package_not_supported = True
      package_not_supported_error_message += \
        "Package: [{0}] with package_type: [{1}] is not supported". \
          format(package_name, _package.get('type', ''))
    package_list.append(package_copy)
  for _service in service_list:
    service_name = _service.get('name')
    if service_name not in services_with_packages:
      service_local_reference = {
        "kind": "app_service",
        "uuid": _service.get('uuid')
      }
      package_copy = copy.deepcopy(package)
      package_copy['name'] = 'pkg_{0}'.format(service_name)
      package_copy['uuid'] = str(uuid.uuid4())
      package_copy['description'] = ''
      package_copy['type'] = 'DEB'
      package_copy['service_local_reference_list']. \
        append(service_local_reference)

      # fixme: add code here for adding variables
      install_runbook = add_runbook(
        tasks_to_be_added=[], variables_to_be_added=[],
        main_task_kind='app_package',
        main_task_kind_uuid=package_copy.get('uuid'),
        credential_list=credential_list, service_list=service_list,
        all_tasks_dependent=False)
      if install_runbook is None:
        _print(user_spawned, "Failed to create install runbook for package "
                             "of service [{0}]".format(_service['name']))
        return None
      package_copy['options']['install_runbook'] = install_runbook

      uninstall_runbook = add_runbook(
        tasks_to_be_added=[], variables_to_be_added=[],
        main_task_kind='app_package',
        main_task_kind_uuid=package_copy.get('uuid'),
        credential_list=credential_list, service_list=service_list,
        all_tasks_dependent=False)
      if uninstall_runbook is None:
        _print(user_spawned, "Failed to create uninstall runbook for package "
                             "in service [{0}]".format(_service['name']))
        return None
      package_copy['options']['uninstall_runbook'] = uninstall_runbook
      package_list.append(package_copy)
  if package_not_supported:
    _print(user_spawned, package_not_supported_error_message)
    return None
  return package_list


def add_deployments(**kwargs):
  """
  This method adds the deployments
  Args:
    kwargs:
      deployments_to_be_added(list): list of all the deployments
      substrate_list(list): list of all the substrates
      package_list(list): list of all the packages
      user_spawned(str): name of the locust user spawned
      published_service_definition_list(list): list of published services
      num_of_replicas(str): number of replicas per service in BP
  Returns:
    deployment_list(list):list of all the deployments added
  """
  deployments_to_be_added = kwargs.get('deployments_to_be_added')
  substrate_list = kwargs.get('substrate_list')
  package_list = kwargs.get('package_list', [])
  user_spawned = kwargs.get('user_spawned', '')
  published_services_list = kwargs.get( \
    'published_services_list', [])
  num_of_replicas = kwargs.get('num_of_replicas', '1')
  #if len(deployments_to_be_added) != len(substrate_list):
  #  _print(user_spawned, "SKIP: Add deployments for all the "
  #                       "substrates(services)")
  #  return None

  deployment = {
    "name": "",
    "min_replicas": "",
    "max_replicas": "",
    "variable_list": [],
    "default_replicas": num_of_replicas,
    "substrate_local_reference": {},
    "package_local_reference_list": [],
    "published_service_local_reference_list": [],
    "action_list": [],
    "uuid": ""
  }
  deployment['type'] = 'GREENFIELD'
  deployment_list = []
  deployment_names_list = []
  for _deployment in deployments_to_be_added:
    deployment_copy = copy.deepcopy(deployment)
    deployment_name = id_generator(8) + '_deployment'
    while deployment_name in deployment_names_list:
      deployment_name = id_generator(8) + '_deployment'
    deployment_names_list.append(deployment_name)
    deployment_copy['name'] = deployment_name
    deployment_copy['uuid'] = str(uuid.uuid4())

    # adding num of replicas
    deployment_copy['min_replicas'] = \
      _deployment.get('min_replicas', num_of_replicas)
    deployment_copy['max_replicas'] = \
      _deployment.get('max_replicas', DEFAULT_MAX_REPLICAS)

    # fixme: add code here for adding variables and actions

    deployment_copy['substrate_local_reference']['kind'] = 'app_substrate'
    substrate_name = _deployment.get('substrate_name')
    substrate = \
      next((substrate for substrate in substrate_list
            if substrate.get('name') == substrate_name), None)
    if substrate is None:
      _print(user_spawned, "Substrate with name [{0}] not "
                           "found".format(substrate_name))
      return None
    deployment_copy['substrate_local_reference']['uuid'] = \
      substrate.get('uuid')

    package_names = _deployment.get('package_name').split(',')
    for package_name in package_names:
      package_local_reference = {
        'kind': 'app_package',
        'uuid': ''
      }
      package = next((package for package in package_list
                      if package.get('name') == package_name), None)
      if package is None:
        _print(user_spawned, "Package with name [{0}] not "
                             "found".format(package_name))
        return None
      package_local_reference['uuid'] = package.get('uuid')
      deployment_copy['package_local_reference_list']. \
        append(package_local_reference)
    if _deployment.get('type') == 'K8S_DEPLOYMENT':
      deployment_copy['type'] = 'K8S_DEPLOYMENT'
      new_options = {
        "metadata": {
          "name": "",
          "namespace": ""
        },
        "spec": {
          "replicas": "1",
          "selector": {
            "matchLabels": {}
          }
        }
      }
      new_options['metadata']['name'] = "k8sdep" + id_generator(4) + \
        "-@@{calm_random_hash}@@"
      new_options['metadata']['namespace'] = _deployment.get( \
        'namespace', NUCALM_KUBERNETES_NAMESPACE)
      if _deployment.get('annotations'):
        new_options['metadata']['annotations'] = \
          _deployment.get('annotations')
      if _deployment.get('labels'):
        new_options['metadata']['labels'] = _deployment.get('labels')
      if _deployment.get('selector'):
        new_options['spec']['selector']['matchLabels'] = \
          _deployment.get('selector')
      else:
        _print(user_spawned, "ERROR: Unable to find selector to create POD")
        return None
      deployment_copy['options'] = new_options
      published_service_local_reference = {
        'kind': 'app_published_service',
        'uuid': ""
      }
      published_service_name = _deployment.get('published_service_name')
      published_service = \
        next((service for service in published_services_list
              if service.get('name') == \
                published_service_name), None)
      if published_service is None:
        _print(user_spawned, "published Service with name [{0}] not "
                             "found".format(published_service_name))
        return None
      published_service_local_reference['uuid'] = published_service.get('uuid')
      deployment_copy['published_service_local_reference_list'] \
        .append(published_service_local_reference)

    deployment_list.append(deployment_copy)
  return deployment_list


def load_payload_for_launch(**kwargs):
  """
  This method loads the payload for the launch
  Args:
    kwargs:
      blueprint(dict): object of BlueprintInfo
      api_version(str): api version used
      application_name(str): name of application
      app_profile_name(str, optional): name of app_profile
      user_spawned(str): name of the locust user spawned.

  Returns:
      payload(dict): payload for the launch or None is app_profile_uuid
      does not exist
  """
  blueprint = kwargs.get('blueprint')
  user_spawned = kwargs.get('user_spawned', '')
  payload = {
    "api_version": kwargs.get('api_version'),
    "metadata": blueprint['metadata'],
    "spec": blueprint['spec']
  }

  if payload['spec'].get('name', None) is not None:
    del payload['spec']['name']

  payload['spec']['application_name'] = kwargs.get('application_name')
  app_profile_name = \
    kwargs.get('app_profile_name', DEFAULT_APP_PROFILE_NAME)
  app_profile_uuid = \
    next((p.get('uuid')
          for p in payload['spec']['resources']['app_profile_list']
          if p.get('name') == app_profile_name), None)

  if app_profile_uuid is None:
    _print(user_spawned, "App Profile [{0}] does not"
                         " exist".format(app_profile_name))
    return None
  payload['spec']['app_profile_reference'] = {
    "kind": "app_profile",
    "uuid": app_profile_uuid
  }
  return payload


def generate_payload_for_publish(**kwargs):
  """
  This method generates the payload for publishing blueprint to
  marketplace manager
  Args:
    kwargs:
      api_version(str): API version used for the API call
      description(str, optional): descrition required
      mpi_bp_name(str): name of the marketplace blueprint
      version(str): version of the mpi blueprint to publish
      status(dict): status from the export_json API response of blueprint
        to publish
      spec(dict):spec from the export_json API response of blueprint to publish
      mpi_app_group_uuid(str, optional): app group uuid if any mpi with
        same name and different version already exists.
      mpi_change_log(str, optional): only if the mpi with same name but with
        different vesion exists.
      user_spawned(str): name of the locust user spawned.

  Returns:
    payload(dict): payload for the API call
  """
  api_version = kwargs.get('api_version', None)
  description = kwargs.get('description', None)
  mpi_bp_name = kwargs.get('mpi_bp_name', None)
  version = kwargs.get('version', None)
  status = kwargs.get('status', None)
  spec = kwargs.get('spec', None)
  mpi_app_group_uuid = kwargs.get('mpi_app_group_uuid', None)
  mpi_change_log = kwargs.get('mpi_change_log', None)
  user_spawned = kwargs.get('user_spawned', '')

  required_attributes = []
  if api_version is None:
    required_attributes.append('api_version')
  if mpi_bp_name is None:
    required_attributes.append('mpi_bp_name')
  if version is None:
    required_attributes.append('version')
  if status is None:
    required_attributes.append('status')
  if spec is None:
    required_attributes.append('spec')
  if mpi_app_group_uuid is None:
    mpi_app_group_uuid = str(uuid.uuid4())

  if len(required_attributes) != 0:
    _print(user_spawned, "SKIP: Some of the required attributes are not"
                         " provided.\nThey are "
                         "[{0}]".format(','.join(required_attributes)))
    return None

  payload = {
    "api_version": api_version,
    "metadata": {
      "kind": "marketplace_item"
    },
    "spec": {
      "name": mpi_bp_name
    }
  }

  if description is not None:
    payload['spec']['description'] = description

  resources = {
    "app_attribute_list": ["FEATURED"],
    "author": "admin",
    "app_blueprint_template": {
      "status": status,
      "spec": spec
    },
    "version": version,
    "app_group_uuid": mpi_app_group_uuid
  }
  payload['spec']['resources'] = resources

  if mpi_change_log is not None:
    payload['spec']['resources']['change_log'] = mpi_change_log
  return payload


def length_check(_list, kind, user_spawned=''):
  """
  This method checks if length of list is empty
  Args:
    _list(list): list to be checked
    kind(string): name of attribute kind
    user_spawned(str): name of the locust user spawned

  Returns:
    None if empty else empty string
  """
  if len(_list) == 0:
    _print(user_spawned, "Error in listing [{0}] API call".format(kind))
    return None
  return ""

def add_published_services(**kwargs):
  """
  This method adds the published services to the blueprint
  Args:
    kwargs:
      published_services_to_be_added(list): list of published services
        to be added.
      user_spawned(str): name of the locust user spawned

  Returns:
    published_service_list(list): list of all the services
                      or
    None if duplicate services
  """
  published_services_to_be_added = kwargs.get( \
    'published_services_to_be_added')
  user_spawned = kwargs.get('user_spawned', '')

  published_service = {
    "name": "",
    "type": "",
    "options": {
      "metadata": {
        "name": "",
        "namespace": "",
        "labels": {}
      },
      "spec": {
        "ports": [
          {
            "name": "",
            "protocol": "TCP",
            "port": 8080,
            "targetPort": 8080
          }
        ],
        "selector": {}
      }
    },
    "uuid": ""
  }

  published_service_list = []
  service_names_list = []

  for _service in published_services_to_be_added:
    service_copy = copy.deepcopy(published_service)
    service_name = _service.get('name')
    if validate_if_duplicate_entity(
        entity_name=service_name, entity_names_list=service_names_list,
        entity_type='Published Service', user_spawned=user_spawned):
      return None
    service_names_list.append(service_name)
    service_copy['name'] = service_name
    service_copy['uuid'] = str(uuid.uuid4())
    if _service.get('type', None):
      service_copy['type'] = _service.get('type')
    else:
      _print(user_spawned, "ERROR: Unable to find published service \
             type to create a POD")
    service_copy['options']['metadata']['name'] = \
      "container-service-" +"-@@{calm_random_hash}@@"
    service_copy['options']['metadata']['namespace'] = \
      _service.get('namespace', NUCALM_KUBERNETES_NAMESPACE)
    service_copy['options']['metadata']['labels'] = \
      _service.get('labels')
    if _service.get('selector', None) is not None:
      service_copy['options']['spec']['selector'] = \
        _service.get('selector')
    else:
      _print(user_spawned, "ERROR: Unable to find selectors to create a POD")
      return None

    published_service_list.append(service_copy)

  return published_service_list

def generate_payload_for_endpoint(self, **kwargs):
  """
  generate payload to create endpoint
  Args:
    kwargs:
      endpoint_name(str): name of the endpoint
      endpoint_type(str): type of the endpoint
      project_name(str): name of the project
      user_spawned(str): name of the user spawned
  Returns:
    payload(dict): payload for creating endpoint
  """
  endpoint_name = kwargs.get('endpoint_name')
  endpoint_type = kwargs.get('endpoint_type')
  project_name = kwargs.get('project_name')
  ip_list = kwargs.get('ip_list')
  spec_file = kwargs.get('spec_file')
  user_spawned = kwargs.get('user_spawned')
  port = kwargs.get('port')

  payload = {
    "api_version": "3.0",
    "metadata": {
      "kind": "endpoint",
      "project_reference": {
        "name": "",
        "kind": "project",
        "uuid": ""
      },
      "uuid": ""
    },
    "spec": {
      "resources": {
        "type": "",
        "value_type": "",
        "attrs": {
          "credential_definition_list": [],
          "login_credential_reference": {
            "name": "root",
            "kind": "app_credential",
            "uuid": ""
          },
          "values": [],
          "port": 0
        }
      },
      "name": ""
    }
  }

  spec_file_path = os.path.join(CONFIG_FOLDER, spec_file)
  try:
    json_file = open(spec_file_path)
  except IOError as file_not_found_error:
    _print(user_spawned, str(file_not_found_error))
    return None
  spec_file = json.load(json_file)

  project_list = get_list(self=self, url="projects/list", payload={},
                          user_spawned=user_spawned)

  project = next((project for project in project_list
                  if project['status']['name'] == project_name), None)

  payload['metadata']['project_reference']['name'] = project_name
  payload['metadata']['project_reference']['uuid'] = project['metadata']['uuid']
  payload['metadata']['uuid'] = str(uuid.uuid4())

  payload['spec']['name'] = endpoint_name
  payload['spec']['resources']['type'] = endpoint_type

  if endpoint_type == 'HTTP':
    http_attrs = spec_file.get('http_attrs', DEAFULT_HTTP_ATTRIBUTES)
    payload['spec']['resources']['attrs'] = http_attrs
    return payload
  credentials_to_be_added = spec_file.get('credential_list', [])
  credential_list = add_credentials(credentials_to_be_added, user_spawned)
  if credential_list is None:
    return None
  payload['spec']['resources']['attrs']['credential_definition_list'] = \
    credential_list

  default_credential_uuid = \
    next((credential.get('uuid') for credential in credential_list
          if credential.get('name') == payload['spec']['resources'] \
          ['attrs']['login_credential_reference']['name']), None)
  payload['spec']['resources']['attrs']['login_credential_reference'] \
    ['uuid'] = default_credential_uuid

  if endpoint_type in ('Linux', 'Windows'):
    payload['spec']['resources']['attrs']['values'] = ip_list
    payload['spec']['resources']['value_type'] = 'IP'
    if not port:
      if endpoint_type == 'Linux':
        port = DEFAULT_LINUX_PORT
      elif endpoint_type == 'Windows':
        port = DEFAULT_WINDOWS_PORT
        payload['spec']['resources']['attrs']['connection_protocol'] = "http"
    payload['spec']['resources']['attrs']['port'] = port
  return payload

def generate_payload_for_runbook(self, **kwargs):
  """
  generate payload to create endpoint
  Args:
    kwargs:
      endpoint_name(str): name of the endpoint
      runbook_name(str): name of the runbook
      project_name(str): name of the project
      user_spawned(str): name of the user spawned
      endpoint_type(str): typr of the endpoint
  Returns:
    payload(dict): payload for creating runbook
  """

  credentials_to_be_added = kwargs.get('credentials_to_be_added', [])
  project_name = kwargs.get('project_name')
  default_endpoint_uuid = kwargs.get('default_endpoint_uuid')
  runbook_name = kwargs.get('runbook_name')
  user_spawned = kwargs.get('user_spawned')
  spec_file = kwargs.get('spec_file')
  no_of_tasks = kwargs.get('no_of_tasks')
  task_type_list = kwargs.get('task_type_list')
  nested_tasks_count = kwargs.get('nested_tasks_count')

  global_tasks = ['WHILE_LOOP', 'DELAY']
  http_tasks = ['HTTP']
  Linux_Windows_tasks = ['EXEC', 'SET_VARIABLE', 'DECISION']

  payload = {
    "spec": {
      "resources": {
        "credential_definition_list": [],
        "endpoint_definition_list": [],
        "runbook": {},
        "default_target_reference": {}
      },
      "name": ""
    },
    "api_version": "3.0",
    "metadata": {
      "kind": "runbook",
      "project_reference": {
        "name": "",
        "kind": "project",
        "uuid": ""
      },
      "uuid": ""
    }
  }

  spec_file_path = os.path.join(CONFIG_FOLDER, spec_file)
  try:
    json_file = open(spec_file_path)
  except IOError as file_not_found_error:
    _print(user_spawned, str(file_not_found_error))
    return None
  spec_file = json.load(json_file)


  project_list = get_list(self=self, url="projects/list", payload={},
                          user_spawned=user_spawned)

  project = next((project for project in project_list
                  if project['status']['name'] == project_name), None)

  payload['metadata']['project_reference']['name'] = project_name
  payload['metadata']['project_reference']['uuid'] = project['metadata']['uuid']
  payload['metadata']['uuid'] = str(uuid.uuid4())

  payload['spec']['name'] = runbook_name

  credential_list = add_credentials(credentials_to_be_added, user_spawned)
  if credential_list is None:
    return None
  payload['spec']['resources']['credential_definition_list'] = credential_list

  default_endpoint_obj = get_entity(self=self, \
    url='endpoints/'+default_endpoint_uuid, api_name='/endpoint')

  default_target_reference = {
    "name": "",
    "kind": "app_endpoint",
    "uuid": ""
  }


  default_target_reference['uuid'] = default_endpoint_uuid
  default_target_reference['name'] = default_endpoint_obj['metadata']['name']
  payload['spec']['resources']['default_target_reference'] = \
    default_target_reference

  tasks = spec_file.get('tasks', [])
  task_uuid = str(uuid.uuid4())
  variables_to_be_added = spec_file.get('variables_to_be_added', [])
  kind = ''
  kind_uuid = ''
  main_task_kind = str(uuid.uuid4())

  task = tasks.get(default_endpoint_obj['spec'] \
    ['resources']['type']+'_tasks_to_be_added')

  if len(task_type_list) == 0:
    if default_endpoint_obj['spec']['resources']['type'] == 'Linux' \
        or default_endpoint_obj['spec']['resources']['type'] == 'Windows':
      task_type_list = Linux_Windows_tasks
    elif default_endpoint_obj['spec']['resources']['type'] == 'HTTP':
      task_type_list = http_tasks
    task_type_list.extend(global_tasks)

  tasks_to_be_added = tasks_cloner(self, task_type_list=task_type_list,
                                   no_of_tasks=no_of_tasks, task=task,
                                   nested_tasks_count=nested_tasks_count)

  time.sleep(10)
  runbook = add_runbook(tasks_to_be_added=tasks_to_be_added, \
    task_uuid=task_uuid, variables_to_be_added=variables_to_be_added, \
    kind=kind, kind_uuid=kind_uuid, credential_list=credential_list, \
    user_spawned=user_spawned, main_task_kind=main_task_kind)

  del runbook['task_definition_list'][0]['target_any_local_reference']
  del runbook['task_definition_list'][0]['variable_list']
  for count in range(1, len(runbook['task_definition_list'])):
    runbook['task_definition_list'][count]['target_any_local_reference'] = {}

  payload['spec']['resources']['runbook'] = runbook

  return payload

def tasks_cloner(self, **kwargs):
  """
  This method clones the tasks in task to upperlimit of
  no_of_tasks with task_type_list
  Args:
    kwargs:
      nested_count(int): starting position of nested loop
      nested_tasks_count(int): nested tasks count
      no_of_tasks(int): max limit of tasks to be clone
      task(dict): refference task for cloning
      task_type_list(list): list of task type

  Returns:
    list of tasks
  """

  nested_count = kwargs.get('nested_count', 0)
  nested_tasks_count = kwargs.get('nested_tasks_count', 1)
  no_of_tasks = kwargs.get('no_of_tasks')
  task = kwargs.get('task')
  task_type_list = kwargs.get('task_type_list')

  task_list = []
  count = 0
  while count < no_of_tasks:
    for task_copy in task:
      for task_type in task_type_list:
        if count >= no_of_tasks:
          break
        if task_type == 'EXEC':
          Task = copy.deepcopy(task_copy)
          Task["type"] = 'EXEC'
          Task['name'] = Task['name'] + Task["type"] + id_generator(4)
        elif task_type == 'SET_VARIABLE':
          Task = copy.deepcopy(task_copy)
          Task["type"] = 'SET_VARIABLE'
          Task['name'] = Task['name'] + Task["type"] + id_generator(4)
        elif task_type == 'DELAY':
          Task = copy.deepcopy(task_copy)
          Task["type"] = 'DELAY'
          Task['name'] = Task['name'] + Task["type"] + id_generator(4)
        elif task_type == 'HTTP':
          Task = copy.deepcopy(task_copy)
          Task["type"] = 'HTTP'
          Task['name'] = Task['name'] + Task["type"] + id_generator(4)
        elif task_type == 'WHILE_LOOP':
          Task = copy.deepcopy(task_copy)
          Task["type"] = 'WHILE_LOOP'
          Task['name'] = Task['name'] + Task["type"] + str(nested_count) + \
            id_generator(4)
          if nested_count+1 < nested_tasks_count:
            nested_while = tasks_cloner(self, task_type_list=['WHILE_LOOP'],
                                        nested_tasks_count=nested_tasks_count,
                                        nested_count=nested_count+1,
                                        no_of_tasks=1, task=task)
            Task['nested_while'] = nested_while
          else:
            while_task = tasks_cloner(self, task_type_list=['EXEC'],
                                      nested_count=nested_tasks_count,
                                      no_of_tasks=1, task=task)
            Task['while_task'] = while_task
        elif task_type == 'DECISION':
          Task = copy.deepcopy(task_copy)
          Task["type"] = 'DECISION'
          Task['name'] = Task['name'] + Task["type"] + id_generator(4)
          if nested_count+1 < nested_tasks_count:
            nested_dec = tasks_cloner(self, task_type_list=['DECISION'],
                                      nested_tasks_count=nested_tasks_count,
                                      nested_count=nested_count+1,
                                      no_of_tasks=2, task=task)
            Task['nested_dec'] = nested_dec
          else:
            decision_tasks = tasks_cloner(self, task_type_list=['EXEC'],
                                          nested_count=nested_tasks_count,
                                          no_of_tasks=2, task=task)
            Task['decision_tasks'] = decision_tasks
        task_list.append(Task)
        count += 1
  return task_list

def generate_payload_for_running_application_action(**kwargs):
  """
  This method generates payload for running the application action
  Args:
    application(json): ApplicationInfo
    action_type(str): action type

  Returns:
    payload(dict): payload for the running application action API call
  """
  application = kwargs.get('application')
  action_name = kwargs.get('action_name')
  action_type = kwargs.get('action_type', None)

  application = copy.deepcopy(application)
  payload = {
    "api_version": application['api_version'],
    "metadata": application['metadata']
  }

  payload['metadata']['uuid'] = str(uuid.uuid4())
  #del payload['metadata']['owner_reference']

  spec = {
    "target_uuid": application['metadata']['uuid'],
    "target_kind": "Application",
    "args": []
  }

  payload['spec'] = spec
  if action_type == 'spec_edit':
    patch = next((patch for patch in application['spec']['resources']\
                  ['patch_list'] if patch['name'] == action_name), None)
    if patch is None:
      return None
    payload['spec']['args'] = {}
    payload['spec']['args']['patch'] = patch
    payload['spec']['args']['variables'] = []
    del payload['spec']['args']['patch']['runbook']
    for attrs in payload['spec']['args']['patch']['attrs_list']:
      del attrs['target_type']

    payload['metadata']['uuid'] = str(uuid.uuid4())
  del payload['metadata']['owner_reference']
  return payload

def generate_payload_for_vm_image_create(**kwargs):
  """
  This method generates payload for running the application action
  Args:
    kwargs:
      vm_data(json): vm data

  Returns:
    payload(dict): payload for the running application action API call
  """
  vm_data = kwargs.get('vm_data')
  payload = {
    "api_version": "3.0",
    "metadata": {},
    "spec": {
      "image_details_list": []
    }
  }
  image_config = {
    "source_disk_uuid": "",
    "image_name": ""
  }
  app_name = vm_data['metadata']['categories']['CalmApplication']
  image_name = app_name + '_' + id_generator(4)

  payload['metadata'] = vm_data['metadata']
  payload['metadata']['name'] = app_name
  payload['metadata']['kind'] = 'app'

  for count, disc in enumerate(vm_data['spec']['resources']['disk_list']):
    image_details = copy.deepcopy(image_config)
    image_details['image_name'] = image_name + '_' + str(count)
    image_details['source_disk_uuid'] = disc['uuid']
    payload['spec']['image_details_list'].append(image_details)

  del payload['metadata']['categories']
  del payload['metadata']['categories_mapping']
  del payload['metadata']['owner_reference']

  return payload

def generate_spec_file(**kwargs):
  """
  This method generates spec_file for creating a blueprint
  Args:
    kwargs:
      num_of_services_per_bp(int): num of services per bp
      workflows(str): space separated workflow types
      os_types(str): space separated os types
      app_profile(dict, optional): app profiles
      account_names(dict, optional): account names
                                     (provider type should be in cap's)
                                     {'AHV': 'RPC_1'}
      num_of_replicas(str): num of replicas per service in BP
  Returns:
    spec_file in dictionary format
  """
  num_of_services_per_bp = kwargs.get('num_of_services_per_bp')
  workflows = kwargs.get('workflows')
  os_types = kwargs.get('os_types')
  app_profile = kwargs.get('app_profile', DEFAULT_APP_PROFILE)
  account_names = kwargs.get('account_names', {})
  no_of_app_profiles = kwargs.get('no_of_app_profiles', 1)
  num_of_replicas = kwargs.get('num_of_replicas', '1')
  scaling_count = kwargs.get('scaling_count', '2')
  spec_file = {
    "credential_list": [],
    "app_profile": [],
    "service": [],
    "substrate": [],
    "package": [],
    "deployment_list": []
  }

  service = {
    "name": ""
  }

  substance = {
    "service_name": "",
    "name": "",
    "type": "",
    "os_type": ""
  }

  package = {
    "name": "",
    "service_name": "",
    "type": "",
    "task": []
  }

  deployment_ele = {
    "app_profile_name": "",
    "deployments": []
  }

  deployments = {
    "substrate_name": "",
    "package_name": "",
    "min_replicas": "",
    "max_replicas": ""
  }

  published_service = {
    "name": "",
    "type": "",
    "labels": {},
    "selector": {}
  }

  app_profile = [
    {
      "name": DEFAULT_APP_PROFILE_NAME,
      "action": []
    }
  ]

  scale_action = [{
    "name": 'action_scale_out',
    "task": [{
      "name": 'scale_out',
      "type": 'SCALING',
      "scaling_type": 'SCALEOUT',
      "scaling_count": '',
      "substrate_name": ''
    }]
  },
  {
    "name": 'action_scale_in',
    "task": [{
      "name": 'scale_in',
      "type": 'SCALING',
      "scaling_type": 'SCALEIN',
      "scaling_count": '',
      "substrate_name": ''
    }]
  }]

  substrates = workflows.split()
  os_types = os_types.split()

  credentials_file_path = os.path.join(CONFIG_FOLDER, CREDENTIALS_FILE)
  credentials_file = open(credentials_file_path)
  credentials = json.load(credentials_file)

  count = 0
  substrates_list = []
  os_type_list = []
  while count < num_of_services_per_bp:
    for substrate in substrates:
      if count < num_of_services_per_bp:
        substrates_list.append(substrate)
        count += 1
      else:
        break

  count = 0
  while count < num_of_services_per_bp:
    for os_type in os_types:
      if count < num_of_services_per_bp:
        os_type_list.append(os_type)
        count += 1
      else:
        break

  spec_file_copy = copy.deepcopy(spec_file)
  credentials_list = []
  for creds in credentials:
    if credentials[creds] not in credentials_list:
      credentials_list.append(credentials[creds])

  spec_file_copy['credential_list'] = credentials_list

  count = 1
  for count in range(no_of_app_profiles - 1):
    app_profile.append({
      "name": 'app_profile_' + str(id_generator(4)),
      "action": []
    })

  spec_file_copy['app_profile'] = app_profile
  original_substrates_copy = []
  original_packages_copy = []

  count = 1
  while count <= num_of_services_per_bp:
    for _substrate, _os in zip(substrates_list, os_type_list):
      if count > num_of_services_per_bp:
        break

      if _substrate == 'K8S_POD' and _os == 'Windows':
        print("ERROR: Kubernetes on windows not yet configured")
        sys.exit()

      service_copy = copy.deepcopy(service)
      if _substrate == 'K8S_POD':
        service_copy['name'] = "container" + str(count)
        service_copy['type'] = _substrate
      else:
        service_copy['name'] = "service_" + str(count)
      spec_file_copy['service'].append(service_copy)

      substrate_copy = copy.deepcopy(substance)
      package_copy = copy.deepcopy(package)
      deployment_ele_copy = copy.deepcopy(deployment_ele)

      substrate_copy['service_name'] = service_copy['name']
      substrate_copy['type'] = _substrate
      if _substrate == 'K8S_POD':
        substrate_copy['name'] = "POD" + str(count)
        substrate_copy['os_type'] = "Linux"
        substrate_copy['labels'] = kwargs.get('lables', {"test": "test"})
      else:
        substrate_copy['name'] = "VM" + str(count)
        substrate_copy['os_type'] = _os
        substrate_copy['credential_name'] = \
        credentials[substrate_copy['type']]['name']

      package_copy['name'] = "pkg_service_" + str(count)
      package_copy['service_name'] = service_copy['name']

      image_data = {
        "name": "",
        "device_type": DEFAULT_AHV_BLUEPRINT_DISK_TYPE,
        "adapter_type": DEFAULT_AHV_BLUEPRINT_DEVICE_BUS
      }
      if _substrate == 'K8S_POD':
        package_copy['type'] = kwargs.get('k8_package_type',
                                          NUCALM_KUBERNETES_PACKAGE_TYPE)
      elif _os == 'Linux':
        package_copy['type'] = kwargs.get('windows_package_type',
                                          DEFAULT_LINUX_PACKAGE_TYPE)
        substrate_copy['credential_name'] = \
            credentials[substrate_copy['type']]['name']
        if substrate_copy['type'] == 'AHV':
          image_data["name"] = DEFAULT_AHV_BLUEPRINT_LINUX_IMAGE_NAME
          substrate_copy['image_list'] = [image_data]

      elif _os == 'Windows':
        if substrate_copy['type'] in ['AHV', 'AWS', 'EM', 'GCP']:
          substrate_copy['credential_name'] = \
            credentials[substrate_copy['type'] + '_WIN']['name']
          if substrate_copy['type'] == 'AHV':
            image_data["name"] = DEFAULT_AHV_BLUEPRINT_WINDOWS_IMAGE_NAME
            substrate_copy['image_list'] = [image_data]
        else:
          substrate_copy['credential_name'] = \
            credentials[substrate_copy['type']]['name']

          if substrate_copy['type'] == 'AZURE':
            substrate_copy['image_publisher_name'] = \
              kwargs.get('image_publisher_name',
                         DEFAULT_AZURE_WIN_IMAGE_PUBLISHER_NAME)
            substrate_copy['image_offer_name'] = \
              kwargs.get('image_offer_name',
                         DEFAULT_AZURE_WIN_IMAGE_OFFER_NAME)
            substrate_copy['image_sku_name'] = \
              kwargs.get('image_sku_name', DEFAULT_AZURE_WIN_IMAGE_SKU)
            substrate_copy['image_version'] = \
              kwargs.get('image_version', DEFAULT_AZURE_WIN_IMAGE_VERSION)
        package_copy['type'] = kwargs.get('windows_package_type',
                                          DEFAULT_WINDOWS_PACKAGE_TYPE)

      if substrate_copy['type'] == 'AHV':
        substrate_copy['ahv_instance_name'] = "ahv_bp_vm_" + str(count)
        if 'AHV' in account_names:
          substrate_copy['account_name'] = account_names['AHV']
      elif substrate_copy['type'] == 'AWS':
        substrate_copy['aws_instance_name'] = "aws_ins_delete_" + str(count)
        if 'AWS' in account_names:
          substrate_copy['account_name'] = account_names['AWS']
      elif substrate_copy['type'] == 'AZURE':
        substrate_copy['azure_instance_name'] = ''
        if 'AZURE' in account_names:
          substrate_copy['account_name'] = account_names['AZURE']
      elif substrate_copy['type'] == 'GCP':
        substrate_copy['address'] = "public"
        substrate_copy['ssh_keys'] = DEFAULT_GCP_SSH_KEYS
        if 'GCP' in account_names:
          substrate_copy['account_name'] = account_names['GCP']
      elif substrate_copy['type'] == 'VMWARE':
        if 'VMWARE' in account_names:
          substrate_copy['account_name'] = account_names['VMWARE']

      original_substrates_copy.append(substrate_copy)
      original_packages_copy.append(package_copy)
      count += 1

  bp_with_k8 = next((True for _substrate in original_substrates_copy
                     if _substrate['type'] == 'K8S_POD'), None)
  if bp_with_k8:
    spec_file_copy['published_services'] = []

  for _app_profile in spec_file_copy['app_profile']:
    substrates_copy = copy.deepcopy(original_substrates_copy)
    packages_copy = copy.deepcopy(original_packages_copy)
    for substrate, package in zip(substrates_copy, packages_copy):
      substrate['name'] = substrate['name'] + '_' + str(id_generator(4))
      package['name'] = package['name'] + '_' + str(id_generator(4))

    deployment_ele_copy = copy.deepcopy(deployment_ele)
    app_profile_name = _app_profile['name']
    for _substrate in substrates_copy:
      if _substrate['type'] == 'AHV':
        _substrate['ahv_instance_name'] = _substrate['ahv_instance_name'] + \
          '_' + str(id_generator(4))
      elif _substrate['type'] == 'AWS':
        _substrate['aws_instance_name'] = _substrate['aws_instance_name'] + \
          '_' + str(id_generator(4))
      deployments_copy = copy.deepcopy(deployments)
      deployments_copy['substrate_name'] = _substrate['name']
      package_name = \
        next((_package['name'] for _package in packages_copy
              if _package['service_name'] == _substrate['service_name']),
             None)
      deployments_copy['package_name'] = package_name

      scale_action_copy = copy.deepcopy(scale_action)
      for action in scale_action_copy:
        action['task'][0]['substrate_name'] = _substrate['name']
        action['task'][0]['scaling_count'] = scaling_count
        action['name'] += _substrate['name'] + str(id_generator(4))

      _app_profile["action"].extend(scale_action_copy)

      if _substrate['type'] == 'K8S_POD':
        published_service_copy = copy.deepcopy(published_service)
        published_service_copy['name'] = "published_service_" + \
          str(substrates_copy.index(_substrate) + 1) + '_' + \
          str(id_generator(4))

        published_service_copy['type'] = "K8S_SERVICE"
        published_service_copy['labels'] = kwargs.get('labels',
                                                      NUCALM_KUBERNETES_LABELS)
        published_service_copy['selector'] = kwargs.get('selectors', \
                                             NUCALM_KUBERNETES_SELECTORS)
        spec_file_copy['published_services'].append(published_service_copy)

        deployments_copy['type'] = 'K8S_DEPLOYMENT'
        deployments_copy['published_service_name'] = \
          published_service_copy['name']
        deployments_copy['selector'] = kwargs.get('selectors',
                                                  NUCALM_KUBERNETES_SELECTORS)

      deployments_copy['min_replicas'] = kwargs.get('min_replicas',
                                                    num_of_replicas)
      deployments_copy['max_replicas'] = kwargs.get('max_replicas',
                                                    DEFAULT_MAX_REPLICAS)

      deployment_ele_copy['deployments'].append(deployments_copy)
    deployment_ele_copy['app_profile_name'] = app_profile_name
    spec_file_copy['deployment_list'].append(deployment_ele_copy)
    spec_file_copy['substrate'].extend(substrates_copy)
    spec_file_copy['package'].extend(packages_copy)

  return spec_file_copy

def check_entity_creation(self, ** kwargs):
  """
  This method returns bool of entity value
  Args:
    kwargs:
      entity(str): entity entity type
      entity_uuid(str): entity uuid
      state(str): state to be validate
      is_host_pc(bool, optional): host pc or not
      pc_ip(str, optional): pc ip
  Returns:
    bool of entity value
  """
  entity = kwargs.get('entity')
  entity_uuid = kwargs.get('entity_uuid')
  state = kwargs.get('state', 'ACTIVE')
  is_remote_pc = kwargs.get('is_remote_pc', False)
  pc_ip = kwargs.get('pc_ip', None)

  time.sleep(5)
  update_wait_count = 0
  for _ in range(30):
    if is_remote_pc:
      pc = pc_ip
      url = 'https://{}:9440/' + V3 + entity + '/' + entity_uuid
      response = self.client.get(url.format(pc_ip),
                                 name=self.__class__.__name__ + '/' + entity)
    else:
      pc = 'host'
      response = self.client.get(V3 + entity + '/' + entity_uuid,
                                 name=self.__class__.__name__ + '/' + entity)
    response = response_check(response)
    if response is None:
      if update_wait_count < 6:
        print("Waiting 5sec for [{0}] task execution in cluster, "
              "task may be in pending state, loop [{1}]" \
              .format(entity, update_wait_count))
        update_wait_count += 1
        time.sleep(5)
        continue

      print("entity with uuid [{0}] not found in [{1}]" \
            .format(entity_uuid, entity))
      return None

    entity_name = response['spec'].get('name', "uuid with [{}]" \
                                       .format(entity_uuid))
    entity_state = response['status']['state']
    if entity_state == state:
      print("entity [{0}] created in [{1}] pc" \
        .format(entity_name, pc))
      return True
    if entity_state in ['DRAFT', 'ERROR']:
      print("ERROR: entity [{0}] is in [{1}] state" \
             .format(entity_name, entity_state))
      return False
    print("entity of {2} [{0}] is in [{1}] state" \
          .format(entity_name, entity_state, entity))
    time.sleep(5)

  return False

def get_idempotence_identifiers(self):
  """
  returns idempotence identifiers of cluster
  Args:
    None

  Returns:
    uuid list or None
  """
  payload = {
    "count":1,
    "client_identifier":str(uuid.uuid4())
  }
  response = self.client.post(V3 + 'idempotence_identifiers',
                              data=json.dumps(payload))
  if response.status_code == 200:
    response = json.loads(response.content)
    return response['uuid_list']
  print("Response failed with status code [{0}]".format(response.status_code))
  return None

def get_calm_users(self, **kwargs):
  """
  returns calm users list
  Args:
    kwargs:
      user_name_pattern(str): user name patter
      directory_name(str): name of the directory
      user_operation(str): user role

  Returns:
    returns calm users list
  """
  directory_name = kwargs.get('directory_name', DEFAULT_CALM_DIRECTORY)
  user_operation = kwargs.get('user_operation', 'ADD')
  num_of_users_per_project = kwargs.get('num_of_users_per_project', 1)
  user_name_pattern = kwargs.get('user_name_pattern',
                                 DEFAULT_CALM_ST_ADMIN_USER)

  user = {
    "metadata": {
      "kind": "user"
    },
    "operation": "ADD",
    "user": {
      "resources": {
        "directory_service_user": {
          "directory_service_reference": {
            "kind": "directory_service",
            "uuid": ""
          },
          "user_principal_name": ""
        }
      }
    }
  }

  # Get directorie services list
  directory_services = get_list(self=self, url="directory_services/list",
                                payload={}, recall=True)
  dir_uuid = None
  for _dir in directory_services:
    if _dir['spec']['name'] == directory_name:
      dir_uuid = _dir['metadata']['uuid']
      break

  user['user']['resources']['directory_service_user']\
    ['directory_service_reference']['uuid'] = dir_uuid
  user['operation'] = user_operation

  if dir_uuid is None:
    print("ERROR: directory [{}] isn't found".format(directory_name))
    return None

  # Get calm users list
  search_payload = {
    'query': user_name_pattern,
    'provider_uuid': dir_uuid,
    'user_type': 'ACTIVE_DIRECTORY',
    'is_wildcard_search': True
  }
  calm_users_list = get_calm_list(self, url='calm_users/search',
                                  payload=search_payload)
  user_list = []
  user_count = 0
  for user_data in calm_users_list:
    for attribute in user_data['attribute_list']:
      if attribute['name'] == 'userPrincipalName':
        user_list.extend(attribute['value_list'])
        user_count += 1
    if user_count >= num_of_users_per_project:
      break

  # Get users list in PC
  users_in_pc = get_list(self=self, url="users/list", payload={"length":1},
                         return_total_resp=True)
  total_users_in_pc = []
  for offset in range(0, users_in_pc['metadata']['total_matches'], 250):
    total_users_in_pc.extend(get_list(self=self, url="users/list",
                                      payload={"length":250, "offset":offset}))
  users_list = []
  for user_name in user_list:
    user_copy = copy.deepcopy(user)
    user_copy['user']['resources']['directory_service_user']\
      ['user_principal_name'] = user_name

    user_data = next((usr for usr in total_users_in_pc \
                       if usr['status']['name'] == user_name), False)
    ## Create user if not present in PC
    if not user_data:
      user_payload = {
        "metadata": user_copy['metadata'],
        "spec": user_copy['user']
      }
      response = self.client.post(V3 + 'users', data=json.dumps(user_payload))
      response = response_check(response, 202)
      if response is None:
        print("Error in response of user create")
        return None
      user_uuid = response['metadata']['uuid']
    else:
      user_uuid = user_data['metadata']['uuid']

    user_copy['metadata']['uuid'] = user_uuid
    users_list.append(user_copy)
  return users_list

def add_infra_inclusions(self, **kwargs):
  """
  returns infra inclusions list
  Args:
    kwargs:
      substrate_list(list): list environment substrate

  Returns:
    list of infra inclusionss
  """
  substrate_list = kwargs.get('substrate_list')
  infra_inclusion = {
    "account_reference": {
      "uuid": "",
      "kind": "account",
      "name": ""
    },
    "type": ""
  }

  acc_uuid_list = []
  subnet_uuid_list = []
  infra_inclusion_list = []
  for substrate in substrate_list:
    acc_uuid = substrate['create_spec']['resources']['account_uuid']
    if acc_uuid not in acc_uuid_list:
      acc_uuid_list.append(acc_uuid)
    if substrate['type'] == 'AHV_VM':
      for subnet in substrate['create_spec']['resources']['nic_list']:
        subnet_uuid_list.append({'uuid': subnet['subnet_reference']['uuid']})

  payload = {
    "length": 250,
    "offset": 0,
    "filter": "state!=DELETED;type!=nutanix"
  }
  accounts_list = get_list(self=self, url="accounts/list",
                           user_spawned='', payload=payload, recall=True)
  for account in accounts_list:
    if account['metadata']['uuid'] in acc_uuid_list or account['status'] \
        ['resources']['type'] == 'nutanix_pc':

      infra_inclusion_copy = copy.deepcopy(infra_inclusion)
      if account['status']['resources']['type'] == 'nutanix_pc' and \
          account['status']['resources']['data'] \
          ['cluster_account_reference_list'][0]['uuid'] not in acc_uuid_list:
        continue

      account_uuid = account['metadata']['uuid']
      infra_inclusion_copy['account_reference']['uuid'] = account_uuid
      infra_inclusion_copy['account_reference']['name'] = \
        account['metadata']['name']
      infra_inclusion_copy['type'] = account['status']['resources']['type']
      if infra_inclusion_copy['type'] == 'nutanix_pc':
        infra_inclusion_copy['subnet_references'] = subnet_uuid_list
      infra_inclusion_list.append(infra_inclusion_copy)

  return infra_inclusion_list

def get_default_filter(project_uuid):
  """
  This will return default filter for the all roles
  Args:
    project_uuid(str): project uuid
  Returns :
      dict : default filter
  """
  default_filter = {
    "entity_filter_expression_list": [
      {
        "left_hand_side": {
          "entity_type": "ALL"
        },
        "operator": "IN",
        "right_hand_side": {
          "collection": "ALL"
        }
      }
    ],
    "scope_filter_expression_list": [
      {
        "left_hand_side": "PROJECT",
        "operator": "IN",
        "right_hand_side": {
          "uuid_list": [project_uuid]
        }
      }
    ]
  }
  return default_filter

def get_default_additional_filter(project_uuid):
  """
  This will return default additional filter for the all roles
  Args:
    project_uuid(str): project uuid
  Returns :
      dict : default additional filter
  """
  default_additional_filter = {
    "entity_filter_expression_list": [
      {
        "left_hand_side": {
          "entity_type": "blueprint"
        },
        "operator": "IN",
        "right_hand_side": {
          "collection": "ALL"
        }
      },
      {
        "left_hand_side": {
          "entity_type": "environment"
        },
        "operator": "IN",
        "right_hand_side": {
          "collection": "ALL"
        }
      }
    ],
    "scope_filter_expression_list": [
      {
        "left_hand_side": "PROJECT",
        "operator": "IN",
        "right_hand_side": {
          "uuid_list": [project_uuid]
        }
      }
    ]
  }
  return default_additional_filter

def get_filter_list(**kwargs):
  """
  This will give the filter list for the role
  Args:
    kwargs:
      role (str): role assigned for user
      cluster_uuid(str):  cluster uuid
      project_uuid(str): uuid of project

  Returns:
      list:  filter list object
  """
  role = kwargs.get('role')
  cluster_uuid = kwargs.get('cluster_uuid')
  project_uuid = kwargs.get('project_uuid')

  filter_list = []
  filter_list.append(get_default_filter(project_uuid))
  entity_filter_expression_list = []

  #fixme: Please automate it for all role
  #for now it is only suits for 'Develeoper' role
  for entity in DEFAULT_ROLE_ENTITY_MAP[role]:
    if entity == "project":
      entity_filter_expression = {"operator": "IN",
                                  "left_hand_side": {"entity_type": entity},
                                  "right_hand_side": {
                                    "uuid_list": [project_uuid]
                                  }}
    elif cluster_uuid and entity == "cluster":
      entity_filter_expression = {"operator": "IN",
                                  "left_hand_side": {"entity_type": entity},
                                  "right_hand_side": {
                                    "uuid_list": [cluster_uuid]}}
    elif entity in ["environment", "marketplace_item", "app_task", \
        "app_variable"]:
      entity_filter_expression = {"operator": "IN",
                                  "left_hand_side": {"entity_type": entity},
                                  "right_hand_side": {
                                    "collection": "SELF_OWNED"}}
    else:
      entity_filter_expression = {"operator": "IN",
                                  "left_hand_side": {"entity_type": entity},
                                  "right_hand_side": {"collection": "ALL"}}
    entity_filter_expression_list.append(entity_filter_expression)

  entity_filter = {
    "entity_filter_expression_list": entity_filter_expression_list
  }
  filter_list.append(entity_filter)
  filter_list.append(get_default_additional_filter(project_uuid))
  return filter_list

def get_access_control_policy_list(self, **kwargs):
  """
  Returns acp for user role mapping
  Args:
    kwargs:
      user_role_map(dict): user role mapping
      cluster_uuid(str): cluster uuid
      project_uuid(str): uuid of project
      user_reference_list(list): list of user_reference
  Returns:
    list: access control policy list
    or None
  """
  user_role_map = kwargs.get('user_role_map')
  cluster_uuid = kwargs.get('cluster_uuid')
  project_uuid = kwargs.get('project_uuid')
  user_reference_list = kwargs.get('user_reference_list', {})

  access_control_policy_list = []
  roles_pair = get_role_uuid_pair(self)
  for user_role in user_role_map:
    metadata = {"kind": "access_control_policy"}
    acp = {}
    acp["name"] = "nuCalmAcp-" + str(uuid.uuid4())
    acp["description"] = "untitledAcp-" + str(uuid.uuid4())
    resources = {}
    role_reference = {
      "name": user_role,
      "uuid": '',
      "kind": "role"
    }
    if user_role in roles_pair:
      role_uuid = roles_pair[user_role]
    else:
      print("Role with name [{0}] not found".format(user_role))
      return None
    role_reference['uuid'] = role_uuid

    user_group_reference_list = []
    resources["role_reference"] = role_reference

    role_users_reference_list = [user_ref for user_ref in user_reference_list
                                 if user_ref['name'] in \
                                 user_role_map[user_role]]
    resources["user_reference_list"] = role_users_reference_list
    if resources["user_reference_list"] is None:
      print("User role [{0}] not found".format(user_role))
      return None

    resources["user_group_reference_list"] = user_group_reference_list
    resources["filter_list"] = {
      'context_list': get_filter_list(role=user_role,
                                      cluster_uuid=cluster_uuid,
                                      project_uuid=project_uuid)
    }
    acp["resources"] = resources
    acp_object = {}
    acp_object["acp"] = acp
    acp_object["metadata"] = metadata
    acp_object["operation"] = "ADD"
    access_control_policy_list.append(acp_object)
  return access_control_policy_list

def generate_payload_for_accepted_project(self, **kwargs):
  """
  generates payload for the project create
  Args:
    kwargs:
      project_name(str): name of project
      username(str): name of the user

  Returns:
    payload(dict): payload for creating project
  """

  project_name = kwargs.get('project_name', 'Nucalm_' + id_generator(4))
  #username = kwargs.get('user_name', DEFAULT_CALM_ST_ADMIN_USER)

  payload = {
    "api_version": "3.0",
    "metadata": {
      "kind": "project",
      "uuid": ""
    },
    "spec": {
      "project_detail": {
        "name": "",
        "resources": {
          "user_reference_list": [],
          "external_network_list": [],
          "account_reference_list": [],
          "external_user_group_reference_list": []
        }
      },
      "user_list": [],
      "user_group_list": [],
      "access_control_policy_list": []
    }
  }

  #fixme: please add project admin user while creating a project
  '''
  users_list = get_calm_users(self, user_name_pattern=username)
  user_uuid = None
  for user in users_list:
    if user['user']['resources']['directory_service_user'] \
        ['user_principal_name']:
      user_uuid = user['metadata']['uuid']
      break

  user_ref = {
    "name": username,
    "kind": "user",
    "uuid": user_uuid
  }
  payload['spec']['project_detail']['resources']['user_reference_list'] \
    .append(user_ref)
  '''

  idempotence_identifiers = get_idempotence_identifiers(self)
  payload['metadata']['uuid'] = idempotence_identifiers[0]
  payload['spec']['project_detail']['name'] = project_name
  return payload

def generate_payload_for_project(self, **kwargs):
  """
  return payload for project create
  Args
    payload(json): payload of accepted project
    user_role(str): user role
    num_of_subnets(int): number of subnets
    user_roles_list(list): list of user roles
    num_of_users_per_project(int): number of users in a project

  Returns:
    project payload
  """
  payload = kwargs.get('payload')
  num_of_subnets = kwargs.get('num_of_subnets', 50)
  user_roles_list = kwargs.get('user_roles_list', ['Developer'])
  num_of_users_per_project = kwargs.get('num_of_users_per_project', 10)
  saas = kwargs.get('saas', False)
  if saas:
    num_of_users_per_project = 0

  subnet_payload = {
    "spec": {
      "name": "",
      "cluster_reference": {
        "kind": "cluster",
        "uuid": ""
      },
      "resources": {
        "subnet_type": "VLAN",
        "ip_config": {},
        "vlan_id": None
      }
    },
    "metadata": {
      "kind": "subnet"
    },
    "api_version": "3.1.0"
  }

  subnet_list_pay = {
    "length":num_of_subnets,
    "offset":0,
    "filter":""
  }

  subnet_details = {
    "kind": "subnet",
    "name": "",
    "uuid": ""
  }

  project_ref = {
    "kind": "project",
    "name": "",
    "uuid": ""
  }

  acc_details = {
    "kind": "account",
    "uuid": ""
  }

  project_uuid = payload['metadata']['uuid']

  if payload is None:
    print("Accepted project payload is neccessary for project creation")
    return None

  # Add users

  count = 0
  user_roles_list_copy = []
  while count < num_of_users_per_project:
    for user_role in user_roles_list:
      if count < num_of_users_per_project:
        user_roles_list_copy.append(user_role)
        count += 1
      else:
        break

  user_count = 0
  user_reference_list = []
  user_role_map = {user_role: [] for user_role in user_roles_list}
  if not saas:
    users_list = get_calm_users(self, user_name_pattern='sspuser', \
                   num_of_users_per_project=num_of_users_per_project)
    for user, user_role in zip(users_list, user_roles_list_copy):
      user_name = user['user']['resources']['directory_service_user']\
        ['user_principal_name']
      user_reference = {}
      user_reference['name'] = user_name
      user_reference['kind'] = 'user'
      user_reference['uuid'] = user['metadata']['uuid']
      user_reference_list.append(user_reference)
      user_role_map[user_role].append(user_name)
      user_count += 1
      if user_count >= num_of_users_per_project:
        break
  payload['spec']['project_detail']['resources']['user_reference_list'] = \
    user_reference_list

  # Add access control policy
  access_control_policy_list = get_access_control_policy_list(self, \
      user_role_map=user_role_map, project_uuid=project_uuid, \
      num_of_users_per_project=num_of_users_per_project,\
      user_reference_list=user_reference_list)
  payload['spec']['access_control_policy_list'] = access_control_policy_list

  # Add account details and get cluster uuids
  accounts_list = get_list(self=self, url="accounts/list",
                           user_spawned='',
                           payload={
                             "length": 250,
                             "offset": 0,
                             "filter": "state==VERIFIED;type!=nutanix"
                           }, recall=True)
  remote_pcs = []
  host_cluster_uuid = ''
  remote_pc_cluster_uuids = {}
  for account in accounts_list:
    acc_details_copy = copy.deepcopy(acc_details)
    acc_details_copy['uuid'] = account['metadata']['uuid']
    payload['spec']['project_detail']['resources']['account_reference_list'] \
      .append(acc_details_copy)
    if 'host_pc' in account['status']['resources']['data']:
      if account['status']['resources']['data']['host_pc'] is False:
        remote_pc_ip = account['status']['resources']['data']['server']
        remote_cluster_uuid = account['status']['resources']['data'] \
                              ['cluster_account_reference_list'][0]\
                              ['resources']['data']['cluster_uuid']
        remote_pcs.append(remote_pc_ip)
        remote_pc_cluster_uuids[remote_pc_ip] = remote_cluster_uuid
    if account['status']['name'] == DEFAULT_LOCAL_NUTANIX_ACCOUNT_NAME:
      host_cluster_uuid = account['status']['resources']['data'] \
                          ['cluster_account_reference_list'][0]\
                          ['resources']['data']['cluster_uuid']

  # Add subnet reference list and default subnet reference
  host_subnet_list = []
  if not saas:
    temp_list_1 = get_list(self=self, url='subnets/list',
                                payload={"length":1}, recall=True,
                                return_total_resp=True)
    host_subnet_list = []
    for offset in range(0, temp_list_1['metadata']['total_matches'], 500):
      host_subnet_list.extend(get_list(self=self, url='subnets/list',
                              payload={"length":500, "offset":offset},
                              recall=True))
    if host_subnet_list is None:
      return None

    ## Create subnets in host pc if number is less than user requirement
    if len(host_subnet_list) < num_of_subnets:
      subnet_payload_copy = copy.deepcopy(subnet_payload)
      subnet_payload_copy['spec']['cluster_reference']['uuid'] = \
        host_cluster_uuid
      for count in range(len(host_subnet_list), num_of_subnets):
        subnet_payload_copy['spec']['name'] = "calm_st_" + str(count)
        subnet_payload_copy['spec']['resources']['vlan_id'] = count

        response = self.client.post(V3 + 'subnets', json=subnet_payload_copy)
        response = response_check(response, 202)
        if response is None:
          print("Failed to create subnets")
          continue
        entity_uuid = response['metadata']['uuid']
        subnet_created = check_entity_creation(self, entity='subnets',
                                               entity_uuid=entity_uuid,
                                               state='COMPLETE')
      if not subnet_created:
        print("failed to create subnet in host pc")
        return None
      host_subnet_list = get_list(self=self, url='subnets/list',
                                  payload=subnet_list_pay, recall=True)
      if host_subnet_list is None:
        return None

  default_subnet = {}
  subnet_reference_list = []
  for subnet in host_subnet_list:
    sub_copy = copy.deepcopy(subnet_details)
    sub_copy['name'] = subnet['spec']['name']
    sub_copy['uuid'] = subnet['metadata']['uuid']
    subnet_reference_list.append(copy.deepcopy(sub_copy))
    if subnet['spec']['name'] == DEFAULT_AHV_BLUEPRINT_NIC:
      del sub_copy['name']
      default_subnet = sub_copy

  payload['spec']['project_detail']['resources']['subnet_reference_list'] = \
    subnet_reference_list
  if not saas:
    payload['spec']['project_detail']['resources'] \
        ['default_subnet_reference'] = default_subnet

  # Add external networks list
  external_networks_list = []
  for remote_pc in remote_pcs:
    remote_network_url = "https://{}:9440/api/nutanix/v3/subnets" \
                         .format(remote_pc)
    response = self.client.post(remote_network_url + '/list',
                                data=json.dumps(subnet_list_pay))
    remote_network_ref_list = response_check(response)['entities']
    if remote_network_ref_list is None:
      return None

    ## Create networks if number is lessthan user requirements
    if len(remote_network_ref_list) < num_of_subnets:
      network_payload_copy = copy.deepcopy(subnet_payload)
      network_payload_copy['spec']['cluster_reference']['uuid'] = \
        remote_pc_cluster_uuids[remote_pc]
      for count in range(len(remote_network_ref_list), num_of_subnets):
        network_payload_copy['spec']['name'] = "calm_st_" + str(count)
        network_payload_copy['spec']['resources']['vlan_id'] = count
        response = self.client.post(remote_network_url,
                                    json=network_payload_copy)
        response = response_check(response, 202)
        if response is None:
          print("Failed to create networks in remote pc [{}]".format(remote_pc))
          return None
        network_created = check_entity_creation(self, \
                          entity='subnets', is_remote_pc=True, \
                          entity_uuid=response['metadata']['uuid'], \
                          state='COMPLETE', pc_ip=remote_pc)
        if not network_created:
          print("Failed to create networks in remote pc [{}]".format(remote_pc))
          return None

      response = self.client.post(url=remote_network_url + '/list',
                                  json=json.dumps(subnet_list_pay))
      remote_network_ref_list = response_check(response)
      if remote_network_ref_list is None:
        print("Error in response of [{}] url - [subnets/list]" \
              .format(remote_pc))
        return None

    for network in remote_network_ref_list:
      external_networks_list.append({
        "name": network['spec']['name'],
        "uuid": network['metadata']['uuid']
      })

  payload['spec']['project_detail']['resources']['external_network_list'] = \
    external_networks_list

  project_ref['name'] = payload['spec']['project_detail']['name']
  project_ref['uuid'] = project_uuid

  payload['metadata']['categories'] = {}
  payload['metadata']['categories_mapping'] = {}
  payload['metadata']['project_reference'] = project_ref
  payload['spec']['project_detail']['resources']['tunnel_reference_list'] = []
  payload['spec']['project_detail']['resources'] \
    ['environment_reference_list'] = []

  del payload['status']
  del payload['metadata']['use_categories_mapping']

  tunnel_list_to_add = []
  if saas:
    # Add tunnels
    ## adding first 20 tunnels to project, please parameterize if needed
    tunnel_pay = {
      "kind": "tunnel",
      "uuid": ""
    }
    tunnel_list = get_list(self=self, url="tunnels/list", \
                           payload={
                             "length": 20,
                             "offset": 0,
                           })
    for tunnel in tunnel_list:
      tunnel_pay_copy = copy.deepcopy(tunnel_pay)
      tunnel_pay_copy['uuid'] = tunnel['metadata']['uuid']
      tunnel_list_to_add.append(tunnel_pay_copy)

  payload['spec']['project_detail']['resources']['tunnel_reference_list'] = \
    tunnel_list_to_add

  return payload

def get_payload_for_environment_entry(self, **kwargs):
  """
  returns payload for environment entry in project
  Args:
    kwargs:
      project_uuid(str): uuid of project

  Returns:
    environment entry payload
  """
  project_uuid = kwargs.get('project_uuid')

  api_name = self.__class__.__name__ + '/' + 'projects_internal'
  response = self.client.get(V3 + 'projects_internal/' + project_uuid,
                             name=api_name)
  if response.status_code != 200:
    print("WARN: Error in API call. The response is {0}".format(response))
    return None

  response = json.loads(response.content.decode('utf-8'))

  payload = {
    'metadata': response['metadata'],
    'api_version': "3.1",
    'spec': response['spec']
  }

  del payload['metadata']['creation_time']
  del payload['metadata']['last_update_time']
  del payload['spec']['project_detail']['resources']['resource_domain']

  return payload

def generate_payload_for_environment(self, **kwargs):
  """
  return payload for environment create
  Args:
    kwargs:
      env_name(str): environment name
      env_uuid(str): uuid of environment
      pro_uuid(str): uuid of project
      pro_name(str): name of project
      account_names(list): types of the providers

  Returns:
    environemnt payload
  """
  env_name = kwargs.get('env_name')
  env_uuid = kwargs.get('env_uuid')
  pro_uuid = kwargs.get('pro_uuid')
  pro_name = kwargs.get('pro_name')
  account_names = kwargs.get('account_names')

  account_names = {name.replace('NUTANIX_PC', 'AHV'): account_names[name] \
                   for name in account_names}
  workflows = ' '.join(account_names)
  os_types = 'Linux '*len(account_names) + 'Windows '*len(account_names)
  spec_file = generate_spec_file(num_of_services_per_bp=len(account_names) * 2,
                                 os_types=os_types, workflows=workflows,
                                 account_names=account_names)

  credentials_to_be_added = spec_file.get('credential_list', None)
  credential_list = \
    add_credentials(credentials_to_be_added=credentials_to_be_added)
  if credential_list is None:
    print("ERROR: Unable to get the credentials")
    return None

  substrates_to_be_added = spec_file.get('substrate', None)
  substrate_list = add_substrates(self=self, \
    substrates_to_be_added=substrates_to_be_added, \
    credential_list=credential_list, project_uuid=pro_uuid)
  if substrates_to_be_added is None:
    print("ERROR: Unable to get substrate list")
    return None

  for substrate in substrate_list:
    if 'editables' in substrate:
      del substrate['editables']

  infra_inclusion_list = add_infra_inclusions(self,
                                              substrate_list=substrate_list)

  payload = {
    "api_version": '3.0',
    "metadata": {
      "kind": "environment",
      "project_reference": {
        "kind": "project",
        "name": pro_name,
        "uuid": pro_uuid
      },
      "uuid": env_uuid
    },
    "spec": {
      "description": "Nutanix-Calm",
      "name": env_name + '_' + id_generator(4),
      "resources": {
        "substrate_definition_list": substrate_list,
        "credential_definition_list": credential_list,
        "infra_inclusion_list": infra_inclusion_list
      }
    }
  }

  return payload

def generate_payload_for_cluster(self):
  """
  return payload for cluster information
  Args:
    None

  Returns:
    Cluster payload
  """

  payload = {
    "entity_type": "cluster",
    "query_name": "eb:data-1622564166151",
    "grouping_attribute": " ",
    "group_count": 3,
    "group_offset": 0,
    "group_attributes": [],
    "group_member_count": 40,
    "group_member_offset": 0,
    "group_member_sort_attribute": "cluster_name",
    "group_member_sort_order": "ASCENDING",
    "group_member_attributes": [
      { 
        "attribute": "cluster_name"
      }
    ]
  }

  return payload

def generate_payload_for_app_policies(self, **kwargs):
  """
  return payload for environment create
  Args:
    kwargs:
      env_name(str): environment name
      env_uuid(str): uuid of environment
      pro_uuid(str): uuid of project
      pro_name(str): name of project
      account_names(list): types of the providers
      policy_name(str): name of app protection policy
      policy_uuid: uuid of policy
      policy_expiry: expiry of policy
      
  Returns:
    app policy payload
  """
  env_name = kwargs.get('env_name')
  env_uuid = kwargs.get('env_uuid')
  pro_uuid = kwargs.get('pro_uuid')
  pro_name = kwargs.get('pro_name')
  account_names = kwargs.get('account_names')
  policy_name = kwargs.get('policy_name')
  policy_uuid = kwargs.get('policy_uuid')
  policy_expiry_days = kwargs.get('policy_expiry_days')
  accuuid = kwargs.get('accuuid')
  clu_uuid = kwargs.get('clu_uuid')

  payload = {
    "api_version": "3.0",
    "metadata": {
      "kind": "app_protection_policy",
      "project_reference": {
        "kind": "project",
        "name": pro_name,
        "uuid": pro_uuid
      },
      "uuid": policy_uuid
    },
    "spec": { 
      "name": policy_name,
      "description": "",
      "resources": {
        "is_default": False,
        "ordered_availability_site_list": [
          { 
            "environment_reference": {
              "kind": "environment",
              "uuid": env_uuid
            },
            "infra_inclusion_list": {
              "type": "nutanix_pc",
              "account_reference": {
                "kind": "account",
                "uuid": accuuid
              },
              "cluster_references": [
                { 
                  "kind": "cluster",
                  "uuid": clu_uuid
                }
              ]
            }
          }
        ],
        "app_protection_rule_list": [
          { 
            "name": "rule_"+str(id_generator(8)),
            "enabled": True,
            "local_snapshot_retention_policy": {
              "snapshot_expiry_policy": {
                "multiple": policy_expiry_days
              }
            },
            "first_availability_site_index": 0,
            "second_availability_site_index": 0,
            "recovery_point_objective_secs": -1,
            "uuid": str(uuid.uuid4())
          }
        ]
      }
    }
  }

  return payload


def generate_payload_for_policy_list(self, **kwargs):
  """
  This method returns app protection policy list
  Args:
    kwargs:
      pro_uuid(str): project uuid 

  Returns:
    list of policies or none
  """
  pro_uuid = kwargs.get('pro_uuid')

  payload = {
    "length": 250,
    "offset": 0,
    "filter": "project_reference==" + pro_uuid
  }

  return payload

def get_substrates_from_environment(self, **kwargs):
  """
  This method returns substrate list
  Args:
    kwargs:
      os_types(str): space separated os types
      workflows(str): space separated workflow types
      credential_list(list): list of credentials
      environment_uuid(str): uuid of environment
      num_of_services_per_bp(int): number of services per bp

  Returns:
    list of substrates or none
  """
  os_types = kwargs.get('os_types')
  workflows = kwargs.get('workflows')
  credential_list = kwargs.get('credential_list')
  environment_uuid = kwargs.get('environment_uuid')
  num_of_services_per_bp = kwargs.get('num_of_services_per_bp')

  workflows = workflows.split()
  os_types = os_types.split()

  credentials_file_path = os.path.join(CONFIG_FOLDER, CREDENTIALS_FILE)
  credentials_file = open(credentials_file_path)
  credentials = json.load(credentials_file)

  count = 0
  workflow_list = []
  os_type_list = []
  while count < num_of_services_per_bp:
    for workflow in workflows:
      if count < num_of_services_per_bp:
        workflow_list.append(workflow)
        count += 1
      else:
        break

  count = 0
  while count < num_of_services_per_bp:
    for os_type in os_types:
      if count < num_of_services_per_bp:
        os_type_list.append(os_type)
        count += 1
      else:
        break

  environment_data = get_entity(self=self, url='environments/' + \
                                environment_uuid, api_name='/environments')
  env_name = environment_data['metadata']['name']

  substrate_list = []
  count = 1
  while count <= num_of_services_per_bp:
    for _workflow, _os in zip(workflow_list, os_type_list):
      if count > num_of_services_per_bp:
        break

      substrate = next((substrate for substrate in environment_data['spec'] \
                        ['resources']['substrate_definition_list']
                        if _workflow in substrate['type'] and \
                        substrate['os_type'] == _os), None)
      if substrate is None:
        print("OS type [{0}] of workflow [{1}] isn't found in environment " \
              "[{2}].".format(_os, _workflow, env_name))
        return None

      substrate['uuid'] = str(uuid.uuid4())
      credential_uuid = next((credential['uuid'] for credential in \
                              credential_list if credentials[_workflow] \
                              ['name'] == credential['name']), None)
      if credential_uuid is None:
        print("Credential with name [{}] isn;t found in cred's list." \
              .format(credentials[_workflow]['name']))
        return None
      substrate['readiness_probe']['login_credential_local_reference']['uuid'] \
        = credential_uuid
      substrate['name'] = 'VM' + str(count)
      substrate_list.append(copy.deepcopy(substrate))
      count += 1

  return substrate_list

def generate_runbook_payload_for_publish(**kwargs):
  """
  This method generates the payload for publishing runbook to
  marketplace manager
  Args:
    kwargs:
      api_version(str): API version used for the API call
      description(str, optional): descrition required
      mpi_runbook_name(str): name of the marketplace blueprint
      version(str): version of the mpi runbook to publish
      status(dict): status from the export_json API response of runbook
        to publish
      spec(dict):spec from the export_json API response of runbook to publish
      mpi_app_group_uuid(str, optional): app group uuid if any mpi with
        same name and different version already exists.
      mpi_change_log(str, optional): only if the mpi with same name but with
        different vesion exists.
      user_spawned(str): name of the locust user spawned.

  Returns:
    payload(dict): payload for the API call
  """

  api_version = kwargs.get('api_version', None)
  description = kwargs.get('description', None)
  mpi_runbook_name = kwargs.get('mpi_runbook_name', None)
  version = kwargs.get('version', None)
  status = kwargs.get('status', None)
  spec = kwargs.get('spec', None)
  mpi_app_group_uuid = kwargs.get('mpi_app_group_uuid', None)
  mpi_change_log = kwargs.get('mpi_change_log', None)
  user_spawned = kwargs.get('user_spawned', '')
  runbook_name = kwargs.get('runbook_name', None)
  runbook_uuid = kwargs.get('runbook_uuid', None)

  required_attributes = []
  if api_version is None:
    required_attributes.append('api_version')
  if mpi_runbook_name is None:
    required_attributes.append('mpi_runbook_name')
  if version is None:
    required_attributes.append('version')
  if status is None:
    required_attributes.append('status')
  if spec is None:
    required_attributes.append('spec')
  if mpi_app_group_uuid is None:
    mpi_app_group_uuid = str(uuid.uuid4())

  if len(required_attributes) != 0:
    _print(user_spawned, "SKIP: Some of the required attributes are not"
                         " provided.\nThey are "
                         "[{0}]".format(','.join(required_attributes)))
    return None

  payload = {
    "api_version": api_version,
    "metadata": {
      "kind": "marketplace_item"
    },
    "spec": {
      "name": mpi_runbook_name
    }
  }

  if description is not None:
    payload['spec']['description'] = description

  resources = {
    "type": "runbook",
    "author": "admin",
    "runbook_template_info": {
      "source_runbook_reference": {
        "name": runbook_name,
        "kind": "runbook",
        "uuid": runbook_uuid
      },
      "is_published_with_endpoints": False,
      "is_published_with_secrets": False
    },
    "version": version,
    "app_group_uuid": mpi_app_group_uuid
  }
  payload['spec']['resources'] = resources


  if mpi_change_log is not None:
    payload['spec']['resources']['change_log'] = mpi_change_log

  return payload

def create_categories(self, no_of_categories=1, user_spawned=''):
  """
  This method creates categories
  Args:
    no_of_categories(int): no.of categories to create
    user_spawned(str): user spawned name
  Returns:
    dict of categories
  """
  filter_criteria = 'name!=CalmApplication;name!=CalmDeployment;'\
                    'name!=CalmService;name!=CalmPackage;name!=CalmProject;'\
                    'name!=CalmUser;name!=CalmVmUniqueIdentifier;'\
                    'name!=CalmClusterUuid'
  group_attributes = [
    {
      "attribute": "name",
      "ancestor_entity_type": "abac_category_key"
    }
  ]
  categories_list = get_grouped_list(self=self, entity_type='category',
                                     attributes=['name', 'value'],
                                     filter_criteria=filter_criteria,
                                     query_name='prism:CategoriesQueryModel',
                                     group_attributes=group_attributes,
                                     length=no_of_categories,
                                     grouping_attribute='abac_category_key',
                                     group_member_sort_attribute='value',
                                     group_result=True,
                                     user_spawned=user_spawned)
  count = len(categories_list)
  if count >= no_of_categories:
    pass
  while count < no_of_categories:
    count += 1
    cat_payload = {
      "name": 'category_' + str(count),
      "description": 'category_scale'
    }
    val_payload = {
      "name": 'value_' + str(count),
      "parentExtId": ''
    }
    url = PRISM_V2_A1 + 'config/categories'
    cat_create_resp = self.client.post(url, data=json.dumps(cat_payload))
    cat_create_resp = response_check(cat_create_resp, 201)
    if cat_create_resp is None:
      _print(user_spawned, "Error in response of prism call")
      print(cat_create_resp)
      return None
    val_payload['parentExtId'] = cat_create_resp['data']['extId']
    val_create_resp = self.client.post(url, data=json.dumps(val_payload))
    val_create_resp = response_check(val_create_resp, 201)
    if val_create_resp is None:
      _print(user_spawned, "Error in response of prism call")
      print(val_create_resp)
      return None

  categories = {}
  categories_list = get_grouped_list(self=self, entity_type='category',
                                     attributes=['name', 'value'],
                                     filter_criteria=filter_criteria,
                                     query_name='prism:CategoriesQueryModel',
                                     group_attributes=group_attributes,
                                     length=no_of_categories,
                                     grouping_attribute='abac_category_key',
                                     group_member_sort_attribute='value',
                                     group_result=True,
                                     user_spawned=user_spawned)
  for count, category in enumerate(categories_list):
    if count >= no_of_categories:
      break
    key = category['group_summaries']['sum:name']['values'][0]['values'][0]
    value = next((_data['values'][0]['values'][0] \
                  for _data in category['entity_results'][-1]['data'] \
                  if _data['name'] == 'value'), None)

    categories[key] = value

  return categories

def generate_payload_for_library_tasks(self, **kwargs):
  """
  generate payload for library tasks
  Args:
    kwargs:
      project_name(str): name of the project
      user_spawned(str): name of the user spawned
  Returns:
    payload for task creation
  """

  project_name = kwargs.get('project_name')
  user_spawned = kwargs.get('user_spawned')
  task_name = kwargs.get('task_name')

  payload = {
    "spec": {
      "resources": {},
      "name": ""
    },
    "api_version": "3.0",
    "metadata": {
      "kind": "app_task",
      "project_reference": {
        "name": "",
        "kind": "project",
        "uuid": ""
      },
      "uuid": ""
    }
  }

  project_list = get_list(self=self, url="projects/list", payload={},
                          user_spawned=user_spawned)

  if project_list is None:
    print("Failed to get project names")
    return None

  project = next((project for project in project_list
                  if project['status']['name'] == project_name), None)

  payload['metadata']['project_reference']['name'] = project_name
  payload['metadata']['project_reference']['uuid'] = project['metadata']['uuid']
  payload['metadata']['uuid'] = str(uuid.uuid4())

  payload['spec']['name'] = task_name

  return payload

def generate_payload_for_quota_enable(project_uuid=None, account_uuid=None,
                                      cluster=None):
  """
  This method returns payload for quota enablement
  Args:
    project_uuid(str): uuid of project
    account_uuid(str): uuid of account
    cluster(str): uuid of ahv cluster/ name of vmware cluster
  Returns:
    payload(dict)
  """

  payload = {
    "spec": {
      "resources": {
        "entities": {},
        "state": "enabled"
      }
    }
  }

  if project_uuid:
    payload['spec']['resources']['entities']['project'] = project_uuid
  if account_uuid:
    payload['spec']['resources']['entities']['account'] = account_uuid
  if cluster:
    payload['spec']['resources']['entities']['cluster'] = cluster

  return payload

def generate_payload_for_create_quota(self, project_uuid=None,
                                      project_name=None, account_uuid=None,
                                      cluster=None):
  """
  This method returns payload for quota creation
  Args:
    project_uuid(str): uuid of project
    project_name(str, optional): name of project
    account_uuid(str): uuid of account
    cluster(str): uuid of ahv cluster/ name of vmware cluster
  Returns:
    payload(dict)
  """
  _uuid = str(uuid.uuid4())
  if project_name is None and project_uuid:
    project_data = get_entity(self=self,
                              url='projects_internal/'+project_uuid,
                              api_name='/projects_internal')
    project_name = project_data['spec']['project_detail']['name']

  payload = {
    "metadata": {
      "kind": "quota",
      "uuid": _uuid
    },
    "spec": {
      "resources": {
        "data": {
          "disk": int(os.environ['QUOTA_DISK']) if 'QUOTA_DISK' in \
                  os.environ else DEFAULT_QUOTA_DISK,
          "vcpu": int(os.environ['QUOTA_VCPU']) if 'QUOTA_VCPU' in \
                  os.environ else DEFAULT_QUOTA_VCPU,
          "memory": int(os.environ['QUOTA_MEMORY']) if 'QUOTA_MEMORY' in \
                  os.environ else DEFAULT_QUOTA_MEMORY
        },
        "entities": {},
        "metadata": {},
        "uuid": _uuid
      }
    }
  }
  if project_uuid:
    payload['spec']['resources']['entities']['project'] = project_uuid
    payload['metadata']['project_reference'] = {
      "kind": "project",
      "name": project_name,
      "uuid": project_uuid
    }
  if account_uuid:
    payload['spec']['resources']['entities']['account'] = account_uuid
  if cluster:
    payload['spec']['resources']['entities']['cluster'] = cluster

  return payload
