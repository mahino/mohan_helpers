#!/usr/bin/env python3
"""Fetch VM IPs from PC and inject conntrack flows with 1:1, 1:N, or N:1 patterns."""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PAGE_SIZE = 500
LOG_FILE = "injected_conntrack_flows.log"
TCP_PORTS = [80, 443, 22, 3306]
UDP_PORTS = [53, 123, 161]


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


def fetch_all_vm_ips(pc_ip, username, password, page_size=PAGE_SIZE, log=None):
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
      log_and_print("total_entity_count = {}".format(total_entity_count), log)

    group_results = data.get("group_results") or []
    if not group_results:
      break

    entity_results = group_results[0].get("entity_results") or []
    if not entity_results:
      break

    hit_empty_ip = False
    for entity in entity_results:
      ips = extract_attr_values(entity, "ip_addresses")
      if not ips:
        hit_empty_ip = True
        break
      for ip in ips:
        if ip and ip not in vm_ips:
          vm_ips.append(ip)

    fetched = offset + len(entity_results)
    log_and_print(
      "fetched {} / {} VMs (unique IPs so far: {})".format(
        min(fetched, total_entity_count), total_entity_count, len(vm_ips)
      ),
      log,
    )

    if hit_empty_ip:
      log_and_print("empty ip_addresses hit; aborting further pagination", log)
      break

    offset += page_size
    if offset >= total_entity_count:
      break

  return vm_ips


def log_and_print(message, file_handle=None):
  print(message)
  if file_handle is not None:
    file_handle.write(message + "\n")
    file_handle.flush()


def make_flow(src, dst, proto, sport, dport, timeout, tcp_state, status):
  flow = {
    "proto": proto,
    "orig_src": src,
    "orig_dst": dst,
    "sport": str(sport),
    "dport": str(dport),
    "reply_src": dst,
    "reply_dst": src,
    "reply_sport": str(dport),
    "reply_dport": str(sport),
    "timeout": str(timeout),
  }
  if proto == "tcp":
    flow["state"] = tcp_state
  if status:
    flow["status"] = status
  return flow


def build_flows(vm_ips, pattern, n, proto, sport, dport, timeout, tcp_state, status):
  if len(vm_ips) < 2:
    raise RuntimeError("need at least 2 unique VM IPs to inject flows")

  n = max(1, min(n, len(vm_ips) - 1))
  ports = TCP_PORTS if proto == "tcp" else UDP_PORTS
  flows = []

  if pattern == "1:1":
    pair_count = len(vm_ips) // 2
    for i in range(pair_count):
      src = vm_ips[i * 2]
      dst = vm_ips[i * 2 + 1]
      use_sport = sport if sport else 40000 + (i % 10000)
      use_dport = dport if dport else ports[i % len(ports)]
      flows.append(make_flow(src, dst, proto, use_sport, use_dport, timeout, tcp_state, status))
  elif pattern == "1:n":
    src = vm_ips[0]
    dests = vm_ips[1:1 + n]
    for i, dst in enumerate(dests):
      use_sport = sport if sport else 41000 + i
      use_dport = dport if dport else ports[i % len(ports)]
      flows.append(make_flow(src, dst, proto, use_sport, use_dport, timeout, tcp_state, status))
  elif pattern == "n:1":
    dst = vm_ips[0]
    srcs = vm_ips[1:1 + n]
    for i, src in enumerate(srcs):
      use_sport = sport if sport else 42000 + i
      use_dport = dport if dport else ports[i % len(ports)]
      flows.append(make_flow(src, dst, proto, use_sport, use_dport, timeout, tcp_state, status))
  else:
    raise RuntimeError("unknown pattern {}".format(pattern))

  return flows


def inject_flow(flow):
    """Executes conntrack -I to inject a single flow."""
    cmd = [
        "sudo", "conntrack", "-I",
        "-p", flow["proto"],
        "--orig-src", flow["orig_src"],
        "--orig-dst", flow["orig_dst"],
        "--sport", flow["sport"],
        "--dport", flow["dport"],
        "--reply-src", flow["reply_src"],
        "--reply-dst", flow["reply_dst"],
        "--reply-port-src", flow["reply_sport"],
        "--reply-port-dst", flow["reply_dport"],
        "--timeout", flow["timeout"]
    ]
    
    # 1. Add TCP state if applicable
    if flow["proto"] == "tcp":
        cmd.extend(["--state", flow["state"]])

    # 2. Add Status flags (SEEN_REPLY, ASSURED) to strip [UNREPLIED]
    if "status" in flow:
        cmd.extend(["--status", flow["status"]])

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0, res.stderr.strip()

def inspect_target_flows(target_flows, log_file_handle):
  cmd = ["sudo", "conntrack", "-L", "-o", "extended"]
  res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

  if res.returncode != 0:
    log_and_print(
      "[{}] ERROR querying conntrack: {}".format(datetime.datetime.now(), res.stderr.strip()),
      log_file_handle,
    )
    return

  lines = res.stdout.strip().split("\n") if res.stdout.strip() else []
  pairs = {(flow["orig_src"], flow["orig_dst"]) for flow in target_flows}

  header = "{:<10} {:<25} {:<25} {:<10} {:<10} {}".format(
    "PROTOCOL", "SRC IP:PORT", "DST IP:PORT", "PACKETS", "BYTES", "TYPE"
  )
  separator = "=" * 88
  log_and_print(header, log_file_handle)
  log_and_print(separator, log_file_handle)

  found_count = 0
  for line in lines:
    src_match = re.search(r"src=([\d\.]+)", line)
    dst_match = re.search(r"dst=([\d\.]+)", line)
    if not src_match or not dst_match:
      continue
    if (src_match.group(1), dst_match.group(1)) not in pairs:
      continue

    found_count += 1
    proto_match = re.search(r"^(\w+)\s+", line)
    sport_match = re.search(r"sport=(\d+)", line)
    dport_match = re.search(r"dport=(\d+)", line)
    pkt_match = re.search(r"packets=(\d+)", line)
    byte_match = re.search(r"bytes=(\d+)", line)

    proto = proto_match.group(1).upper() if proto_match else "N/A"
    src = "{}:{}".format(src_match.group(1), sport_match.group(1) if sport_match else "?")
    dst = "{}:{}".format(dst_match.group(1), dport_match.group(1) if dport_match else "?")
    pkts = int(pkt_match.group(1)) if pkt_match else 0
    bytes_cnt = int(byte_match.group(1)) if byte_match else 0
    flow_type = "Mock (0 bytes)" if pkts == 0 and bytes_cnt == 0 else "Real Traffic"
    log_and_print(
      "{:<10} {:<25} {:<25} {:<10} {:<10} {}".format(proto, src, dst, pkts, bytes_cnt, flow_type),
      log_file_handle,
    )

  if found_count == 0:
    log_and_print("No matching injected flows found in active conntrack table.", log_file_handle)
  else:
    log_and_print("Matched {} conntrack entries.".format(found_count), log_file_handle)


def main():
  parser = argparse.ArgumentParser(
    description="Fetch VM IPs from PC and inject conntrack flows"
  )
  parser.add_argument("--pc_ip", default="10.114.54.190", help="Prism Central IP")
  parser.add_argument("--username", default="admin", help="PC username")
  parser.add_argument("--password", default="Nutanix.123", help="PC password")
  parser.add_argument("--page_size", type=int, default=PAGE_SIZE, help="groups page size")
  parser.add_argument(
    "--ips_file",
    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "ips_on_host.txt"),
    help="Write/read space-separated VM IPs",
  )
  parser.add_argument(
    "--skip_fetch",
    action="store_true",
    help="Use --ips_file instead of calling PC groups API",
  )
  parser.add_argument(
    "--pattern",
    choices=["1:1", "1:n", "n:1"],
    default="1:1",
    help="Flow pattern: 1vm:1vm (default), 1vm:n vm, n vms:1 vm",
  )
  parser.add_argument(
    "--n",
    type=int,
    default=10,
    help="N for 1:n and n:1 patterns (default 10)",
  )
  parser.add_argument("--proto", choices=["tcp", "udp"], default="tcp")
  parser.add_argument("--sport", type=int, default=0, help="Fixed source port; 0 auto-assigns")
  parser.add_argument("--dport", type=int, default=0, help="Fixed dest port; 0 rotates common ports")
  parser.add_argument("--timeout", type=int, default=120)
  parser.add_argument("--tcp_state", default="ESTABLISHED")
  parser.add_argument("--status", default="SEEN_REPLY,ASSURED", help="Status flags to add to flows")
  parser.add_argument("--inspect_only", action="store_true", help="Skip inject; only inspect")
  args = parser.parse_args()

  with open(LOG_FILE, "a") as log:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_and_print("\n--- INGEST & INSPECT RUN: {} ---".format(timestamp), log)
    log_and_print("pattern={} n={} proto={}".format(args.pattern, args.n, args.proto), log)

    if args.skip_fetch:
      if not os.path.exists(args.ips_file):
        log_and_print("ERROR: ips file not found: {}".format(args.ips_file), log)
        sys.exit(1)
      with open(args.ips_file) as fh:
        vm_ips = fh.read().split()
      log_and_print("Loaded {} IPs from {}".format(len(vm_ips), args.ips_file), log)
    else:
      try:
        vm_ips = fetch_all_vm_ips(
          args.pc_ip, args.username, args.password, args.page_size, log
        )
      except Exception as exc:
        log_and_print("ERROR fetching VM IPs: {}".format(exc), log)
        sys.exit(1)
      with open(args.ips_file, "w") as fh:
        fh.write(" ".join(vm_ips) + "\n")
      log_and_print("Wrote {} IPs to {}".format(len(vm_ips), args.ips_file), log)

    try:
      target_flows = build_flows(
        vm_ips, args.pattern, args.n, args.proto,
        args.sport or None, args.dport or None, args.timeout, args.tcp_state,
        args.status,
    )
    except Exception as exc:
      log_and_print("ERROR building flows: {}".format(exc), log)
      sys.exit(1)

    log_and_print("Built {} flows for pattern {}".format(len(target_flows), args.pattern), log)

    if not args.inspect_only:
      log_and_print("[1/2] Injecting mock flows into conntrack...", log)
      for flow in target_flows:
        success, err = inject_flow(flow)
        status = "SUCCESS" if success else "FAILED ({})".format(err)
        log_and_print(
          " -> [{}] Injected {} {}:{} -> {}:{}".format(
            status, flow["proto"].upper(),
            flow["orig_src"], flow["sport"],
            flow["orig_dst"], flow["dport"],
          ),
          log,
        )
    else:
      log_and_print("[1/2] Skipping inject (--inspect_only)", log)

    log_and_print("\n[2/2] Inspecting only injected flows from active table...", log)
    inspect_target_flows(target_flows, log)
    log_and_print("\n[COMPLETE] Results logged to: {}\n".format(os.path.abspath(LOG_FILE)), log)


if __name__ == "__main__":
  main()
