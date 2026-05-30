import sys
from influxdb import InfluxDBClient
client = InfluxDBClient('10.46.8.64', 8086, 'admin', 'nutanix/4u', 'calm_st')

host = 'ntnx-' + sys.argv[1].replace('.', '-') + '-a-pcvm'
build_no = sys.argv[2]
start_time = int(sys.argv[3]) - 1000
end_time = int(sys.argv[4]) - 1000

# Provision timings
string = 'Provision timings'
print('-'*len(string), 'Provision timings', '-'*len(string), '\n')
actions = ['create_action', 'restart_action', 'scale_in_action', 'scale_out_action', 'start_action', 'stop_action']
for action in actions:
  try:
    print('select "provisioning_time" from app_provisioning where (host=\'{0}\' and build_no=\'{1}\' and runlog_type=\'{4}\') and time >= {2}ms and time <= {3}ms'.format(host, build_no, start_time, end_time, action))
    prov_time = client.query('select "provisioning_time" from app_provisioning where (host=\'{0}\' and build_no=\'{1}\' and runlog_type=\'{4}\') and time >= {2}ms and time <= {3}ms'.format(host, build_no, start_time, end_time, action))
    prov_time = list(prov_time.get_points(measurement='app_provisioning'))
    prov_time_list = [float(i['provisioning_time']) for i in prov_time]
    prov_time_list = (sorted(prov_time_list, key=float))
    print(prov_time_list)
    percentile = float((prov_time_list[round(0.90 * len(prov_time_list)) - 1])/60)
    print(action, len(prov_time_list), percentile)
  except IndexError:
    pass
print()
