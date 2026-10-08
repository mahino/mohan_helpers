#!/usr/bin/env python3
"""Fetch all VM IPs from PC groups API (mh_vm_ui) with pagination."""

import argparse
import json
import os
import sys

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PAGE_SIZE = 500


def build_payload(offset, page_size=PAGE_SIZE):
  return {
    "entity_type": "mh_vm_ui",
    "query_name": "",
    "grouping_attribute": " ",
    "group_count": 20,
    "group_offset": 0,
    "group_attributes": [],
    "group_member_count": page_size,
    "group_member_offset": offset,
    "group_member_sort_attribute": "ip_addresses",
    "group_member_sort_order": "DESCENDING",
    "group_member_attributes": [
      {"attribute": "vm_name"},
      {"attribute": "ip_addresses"},
    ],
    "filter_criteria": "is_cvm==0",
  }


def extract_attr_values(entity, attr_name):
  for item in entity.get("data", []):
    if item.get("name") != attr_name:
      continue
    values = []
    for value_block in item.get("values", []):
      values.extend(value_block.get("values", []))
    return values
  return []


def fetch_all_vm_ips(pc_ip, username, password, page_size=PAGE_SIZE):
  url = "https://{}:9440/api/nutanix/v3/groups".format(pc_ip)
  session = requests.Session()
  session.auth = HTTPBasicAuth(username, password)
  session.headers = {"content-type": "application/json"}
  session.verify = False

  offset = 0
  total_entity_count = None
  vm_ips = []

  while True:
    payload = build_payload(offset, page_size)
    resp = session.post(url, data=json.dumps(payload), timeout=120)
    if resp.status_code != 200:
      raise RuntimeError(
        "groups API failed at offset={} status={} body={}".format(
          offset, resp.status_code, resp.text[:500]
        )
      )

    data = resp.json()
    if total_entity_count is None:
      total_entity_count = data.get("total_entity_count")
      if total_entity_count is None:
        raise RuntimeError("total_entity_count missing in response")
      print("total_entity_count = {}".format(total_entity_count))

    group_results = data.get("group_results") or []
    if not group_results:
      break

    entity_results = group_results[0].get("entity_results") or []
    if not entity_results:
      break

    hit_empty_ip = False
    for entity in entity_results:
      ips = extract_attr_values(entity, "ip_addresses")
      # Sorted DESC by ip_addresses: first empty means remaining VMs have no IPs.
      if not ips:
        hit_empty_ip = True
        break
      for ip in ips:
        if ip and ip not in vm_ips:
          vm_ips.append(ip)

    fetched = offset + len(entity_results)
    print("fetched {} / {} VMs (unique IPs so far: {})".format(
      min(fetched, total_entity_count), total_entity_count, len(vm_ips)
    ))

    if hit_empty_ip:
      print("empty ip_addresses hit; aborting further pagination")
      break

    offset += page_size
    if offset >= total_entity_count:
      break

  return vm_ips


def main():
  parser = argparse.ArgumentParser(description="List all VM IPs from PC groups API")
  parser.add_argument("--pc_ip", default="10.114.54.220", help="Prism Central IP")
  parser.add_argument("--username", default="admin", help="PC username")
  parser.add_argument("--password", default="Nutanix.123", help="PC password")
  parser.add_argument("--page_size", type=int, default=PAGE_SIZE, help="group_member_count")
  parser.add_argument(
    "--output",
    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "ips_on_host.txt"),
    help="File to write space-separated IPs (for mock_ipfix.py)",
  )
  args = parser.parse_args()

  try:
    vm_ips = fetch_all_vm_ips(args.pc_ip, args.username, args.password, args.page_size)
  except Exception as exc:
    print("ERROR: {}".format(exc), file=sys.stderr)
    sys.exit(1)

  print("\n=== VM IPs ({}) ===".format(len(vm_ips)))
  for ip in vm_ips:
    print(ip)

  with open(args.output, "w") as fh:
    fh.write(" ".join(vm_ips) + "\n")
  print("\nWrote {} IPs to {}".format(len(vm_ips), args.output))


if __name__ == "__main__":
  main()
