"""
Copyright (c) 2021 Nutanix Inc. All rights reserved.
Author: jignesh.thakkar@nutanix.com
"""
# pylint: disable=invalid-name
# pylint: disable=no-name-in-module
# pylint: disable=wildcard-import
# pylint: disable=import-error
# pylint: disable=undefined-variable
# pylint: disable=line-too-long
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=too-many-branches
# pylint: disable=global-statement
# pylint: disable=no-member
# pylint: disable=bare-except
# pylint: disable=redefined-builtin
# pylint: disable=superfluous-parens



import ipfix # https://github.com/britram/python-ipfix
import socket
import random
import sys
import time
import os
import argparse
import ipaddress # https://docs.python.org/3/howto/ipaddress.html



# place for global vars
TMPL_DICT = {
  298: ('observationPointId', 'flowDirection', 'ethernetType', 'ethernetHeaderLength', 'vlanId', 'dot1qVlanId', 'dot1qPriority', 'ipVersion', 'ipTTL', 'protocolIdentifier', 'ipDiffServCodePoint', 'ipPrecedence', 'ipClassOfService', 'sourceIPv4Address', 'destinationIPv4Address', 'sourceTransportPort', 'destinationTransportPort', 'flowStartDeltaMicroseconds', 'flowEndDeltaMicroseconds', 'droppedPacketDeltaCount', 'droppedPacketTotalCount', 'packetDeltaCount', 'packetTotalCount', 'ingressUnicastPacketTotalCount', 'ingressMulticastPacketTotalCount', 'ingressBroadcastPacketTotalCount', 'egressUnicastPacketTotalCount', 'egressBroadcastPacketTotalCount', 'postMCastPacketDeltaCount', 'postMCastPacketTotalCount', 'layer2OctetDeltaCount', 'layer2OctetTotalCount', 'flowEndReason', 'droppedOctetDeltaCount', 'droppedOctetTotalCount', 'octetDeltaCount', 'octetTotalCount', 'octetDeltaSumOfSquares', 'octetTotalSumOfSquares', 'minimumIpTotalLength', 'maximumIpTotalLength', 'postMCastOctetDeltaCount', 'postMCastOctetTotalCount', 'tcpAckTotalCount', 'tcpFinTotalCount', 'tcpPshTotalCount', 'tcpRstTotalCount', 'tcpSynTotalCount', 'tcpUrgTotalCount')
}

PORTS = [80, 443, 3306, 587, 53, 123, 33060, 23, 860]
UNIDENTIFIED_PORTS = [random.randint(9901, 9999) for x in range(20)]


def send_all_templates():
  """
  Send the ipfix template to pc
  Returns:
    None
  """
  global TEMPLATE_SEND_TIMESTAMP
  if TEMPLATE_SEND_TIMESTAMP is not None:
    if time.time() - TEMPLATE_SEND_TIMESTAMP < 300:
      return
  for k, v in list(TMPL_DICT.items()):
    MSG.begin_export(OBS_DOM_ID)
    tmpl = ipfix.template.from_ielist(k, ipfix.ie.spec_list(v))
    MSG.add_template(tmpl)
    ipfixpayload = MSG.to_bytes()
    try:
      SOCK.sendall(ipfixpayload)
    except socket.error as e:
      raise Exception("Sending all templates failed (socket error): {}".format(e))

  TEMPLATE_SEND_TIMESTAMP = time.time()
  print('Sending all Ipfix templates at time = ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(TEMPLATE_SEND_TIMESTAMP)))

def prepare_data298(vlanid, src_port, dest_port, src_ip, dest_ip):
  """
  Prepare the template 298 of ipfix to send the ipfix traffic to pc
  Args:
    vlanid(str): vlan id
    src_port(str): source port
    dest_port(str): destination port
    src_ip(str): source ip
    dest_ip(str): destination ip
  Returns:
    rec(dict)
  """
  rec = dict()

  for my_ie in ipfix.ie.spec_list(TMPL_DICT[298]):
    if my_ie.name == 'protocolIdentifier':
      rec[my_ie.name] = 17
    elif my_ie.name == 'flowStartDeltaMicroseconds':
      rec[my_ie.name] = 300000
    elif my_ie.name == 'flowEndDeltaMicroseconds':
      rec[my_ie.name] = 5000
    elif my_ie.name == 'sourceTransportPort':
      rec[my_ie.name] = src_port
    elif my_ie.name == 'destinationTransportPort':
      rec[my_ie.name] = dest_port
    elif my_ie.name == 'destinationIPv4Address':
      rec[my_ie.name] = ipaddress.ip_address(dest_ip)
    elif my_ie.name == 'sourceIPv4Address':
      rec[my_ie.name] = ipaddress.ip_address(src_ip)
    elif my_ie.name == 'octetDeltaCount':
      rec[my_ie.name] = random.randint(1, 1400)
    elif my_ie.name == 'packetDeltaCount':
      rec[my_ie.name] = random.randint(1, 100)
    elif my_ie.name == 'ipTTL':
      rec[my_ie.name] = random.randint(1, 254)
    elif my_ie.name == 'observationPointId':
      rec[my_ie.name] = 1023
    elif my_ie.name == 'flowDirection':
      rec[my_ie.name] = 1
    elif my_ie.name == 'dot1qVlanId':
      rec[my_ie.name] = vlanid
    elif my_ie.name == 'vlanId':
      rec[my_ie.name] = vlanid
    else:
      if 'unsigned' in str(my_ie.type):
        rec[my_ie.name] = 0
      else:
        print('the name is ' + my_ie.name + ' and the type is ' + str(my_ie.type))
        sys.exit()

  return rec


def send_data298(vlanid, src_port, dest_port, src_ip, dest_ip):
  """
  Sending data template 298
  Args:
    vlanid(str): vlan id
    src_port(str): source port
    dest_port(str): destination port
    src_ip(str): source ip
    dest_ip(str): destination ip
  Returns:
    numRecPerPkt(list)
  """
  print('Sending data from {}:{} to {}:{} for template 298 at time {} '.format(
    ipaddress.ip_address(src_ip), src_port, ipaddress.ip_address(dest_ip), dest_port,
    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))))
  rec = dict()

  MSG.begin_export(OBS_DOM_ID)
  MSG.export_ensure_set(298)

  numRecPerPkt = random.choice([4, 5]) # Use 5

  for i in range(numRecPerPkt):
    try:
      MSG.export_namedict(prepare_data298(vlanid=vlanid, src_port=src_port+i, dest_port=dest_port+i, src_ip=src_ip, dest_ip=dest_ip))
    except:
      sys.exit('Threw an exception ' + str(rec))

  ipfixpayload = MSG.to_bytes()
  try:
    SOCK.sendall(ipfixpayload)
  except socket.error as e:
    raise Exception("Sending template data failed (socket error): {}".format(e))

  print('Payload len - ' + str(len(ipfixpayload)))
  sleep_to_enforce_pps = 0.001# previous 0.005# or 0.0001
  time.sleep(sleep_to_enforce_pps)
  return numRecPerPkt


def get_all_vm_ips_on_host():
  """
  Get the list of ips from the host
  Returns:
     ip_address_list(list): List of ips
  """
  cur_dir = os.path.dirname(os.path.abspath(__file__))
  file = open('{}/ips_on_host.txt'.format(cur_dir))
  ip_address_list = file.readline().strip()
  ip_address_list = list(str(ip_address_list).split())
  return ip_address_list


if __name__ == '__main__':

  # python3 mock_ipfix.py --dest_pc_ip 10.10.10.10 --vlanid 100 --flows_per_sec 10 --flow_duration 10 --offset 10
  # python3 mock_ipfix.py --dest_pc_ip 10.114.54.190 --vlanid 352 --flows_per_sec 10 --packets_per_sec 0.0167 --flow_duration 10 --offset 10
  parser = argparse.ArgumentParser(description='Generate IPFIX load')
  parser.add_argument('--dest_pc_ip', dest='dest_pc_ip', required=True, help='scalanytics IP address')
  parser.add_argument('--dest_port', type=int, dest='dest_port', default=10000, help='scalanytics IPFIX port (Default value = 10000)')
  parser.add_argument('--vlanid', dest='vlanid', required=True, help='VLAN ID for the traffic')

  parser.add_argument('--flows_per_sec', type=int, dest='flows_per_sec', default=10000, help='number of flows per second (Default value = 10000)')
  parser.add_argument('--packets_per_sec', type=float, dest='packets_per_sec', default=1.0/60, help='number of IPFIX UDP packets per second (default value = 0.0167, i.e. 1/60)')
  parser.add_argument('--flow_duration', type=int, dest='flow_duration', default=100, help='duration of each flow (Default value = 100)')
  parser.add_argument('--offset', type=int, dest='offset', default=100, help='number of distinct vlanIdi (Default value = 100), per vlanId script will create [num_flows/offset] records')
  parser.add_argument('--usetcp', action='store_true', dest='usetcp', default=False, help='Send data using IPFIX over TCP')

  ARGS = parser.parse_args()
  OBS_DOM_ID = 20000
  DEST_IP = ARGS.dest_pc_ip
  DEST_PORT = int(ARGS.dest_port)
  VLAN_ID = int(ARGS.vlanid)
  FLOW_DURATION = int(ARGS.flow_duration)
  PACKETS_PER_SEC = ARGS.packets_per_sec
  MSG = ipfix.message.MessageBuffer()
  MAX_ITERATIONS = 10

  ipfix.ie.use_iana_default()

  if ARGS.usetcp:
    SOCK = socket.create_connection((DEST_IP, DEST_PORT), 6)
  else:
    SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SOCK.connect((DEST_IP, DEST_PORT))

  FLOWS_PER_SEC = int(ARGS.flows_per_sec)
  offset = int(ARGS.offset)
  maxSleepTm = 1

  global_start_time = time.time()
  TEMPLATE_SEND_TIMESTAMP = None
  send_all_templates()

  sleepTm = maxSleepTm
  # Get the currently active flow window.
  def get_num_active_flows(using_cps):
    """
    Get active flows
    Args:
      using_cps(str)
    Returns:
      int()
    """
    return int((FLOW_DURATION * using_cps) * sleepTm)
  current_flows = max(10, FLOWS_PER_SEC) # in order to avoid blow up of topology data, we start with very small CPS (this limits IP address range)

  ip_address_list = get_all_vm_ips_on_host()
  ip_addresses = [ipaddress.ip_address(ip_addr) for ip_addr in ip_address_list]
  port_list = [random.choice(PORTS + UNIDENTIFIED_PORTS) for _ in range(len(ip_addresses))]

  for iteration in range(MAX_ITERATIONS):
    # in order to reuse IP addresses and avoid blow up of the topology data, we limit our range
    print('Iteration {}/{} Current flows - {} Window size - {} Total IP list length is {}'.format(
      iteration + 1, MAX_ITERATIONS, current_flows,
      get_num_active_flows(current_flows), len(ip_addresses)))
    send_all_templates()
    numRecordsSent = 0 # debug
    numPktsSent = 0 # debug
    start_time = time.time()
    loopEndIP_index = len(ip_addresses)
    loop_range = loopEndIP_index
    startIP_index = 0
    while startIP_index < loopEndIP_index:
      src_ip = ip_addresses[startIP_index]
      dest_ip = ip_addresses[(startIP_index+1)%loopEndIP_index]
      port = port_list[(startIP_index+1)%loopEndIP_index]
      # flow from A->B
      numRecordsSent += send_data298(vlanid=VLAN_ID, src_port=port, dest_port=port, src_ip=src_ip, dest_ip=dest_ip)
      numPktsSent += 1
      # flow from B->A
      numRecordsSent += send_data298(vlanid=VLAN_ID, src_port=port, dest_port=port, src_ip=dest_ip, dest_ip=src_ip)
      numPktsSent += 1
      startIP_index += 1
    elapsed_time = time.time() - start_time
    print('At ' + str(time.asctime()) + ' between  ' + str(loop_range) +
          ' Ip addresses' +  ' numRecordsSent ' + str(numRecordsSent) +
          ' numPktsSent ' + str(numPktsSent) + ' elapsed_time ' + str(elapsed_time) + ' secs '
          ' requested PACKETS_PER_SEC ' + str(PACKETS_PER_SEC) + ' actual_pps ' +
          str((1.0 * numPktsSent)/elapsed_time))
  print('Finished {} iterations'.format(MAX_ITERATIONS))