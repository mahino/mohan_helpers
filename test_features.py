# -*- coding: utf-8 -*-
"""Calm feature"""

import json
import time
from default_infra_host import CALM_V3, TIME_OUT

class TestFeatures():
  """Calm features"""
  def __init__(self, client, base_url=''):
    self.client = client
    if base_url:
      global CALM_V3
      CALM_V3 = base_url + CALM_V3

  def feature_policy_get(self, download_logs=True, prechecks=True, output=True):
    """
      This method returns policy response
      Args:
        download_logs(bool): trigger download_logs api or not
      Returns:
        response of policy or False
    """
    url = CALM_V3 + 'features/policy'
    response = self.client.get(url)
    print(url)
    if response.status_code != 200:
      print("ERROR: error in feature policy get API")
      print(response.content)
      return False
    response = json.loads(response.content)
    if download_logs:
      URL = url + '/download_logs'
      self.client.get(URL)
    if output:
      URL = url + '/output'
      self.client.get(URL)
    if prechecks:
      URL = url + '/prechecks'
      self.client.get(URL)
    return response

  def feature_policy_update(self, policy, enable_policy=False):
    """
    This method updates the policy
    Args:
      policy(dict): get response content of policy
    Returns:
      boolean of update status
    """

    url = CALM_V3 + 'features/policy'
    policy_payload = {
      'spec': policy['spec'],
      'api_version': policy['api_version'],
      'metadata': policy['metadata']
    }
    if enable_policy:
      vm_ip = get_free_ip()
      if not vm_ip:
        return False
      policy_payload['spec']['feature_status']['config']['data'] = {
        'ip_list': [vm_ip],
        'migrate_vms': True
      }
      policy_payload['spec']['feature_status']['is_enabled'] = True
    response = self.client.put(url, data=json.dumps(policy_payload))
    if response.status_code != 200:
      print("ERROR: error in feature policy get API")
      print(response.content)
      return False
    time.sleep(10)
    if self.feature_status_check():
      return True
    return False

  def feature_status_check(self):
    """
    This method checks status of feature
    """
    url = CALM_V3 + 'features/policy' 
    for _ in range(0, TIME_OUT, 5):
      response = self.client.get(url)
      if response.status_code != 200:
        print("ERROR: error in feature policy get API")
        print(response.content)
        return False
      response = json.loads(response.content)
      state = response['status']['feature_status']['config']['state']
      if state == 'COMPLETED':
        return True

      print('policy enablement current progress',
            response['status']['feature_status']['config']['progress'])
      time.sleep(10)
    print("ERROR:failed to update in 1 hour")
    return False

  def is_policy_enabled(self):
    """
    This method returns boolean wheather policy enabled or not
    """
    resp = self.feature_policy_get(download_logs=False, prechecks=False,
                                   output=False)
    try:
      if resp['status']['feature_status']['is_enabled']:
        return True
    except KeyError:
      pass
    print("ERROR: policy isn't enabled")
    return False

