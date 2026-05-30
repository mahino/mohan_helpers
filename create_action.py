'''
This Script will take grafana url and outputs 90 % Percentile time of Create_action 
along with Count of Entities for that Time Frame
python3 create_action.py "<Grafana_Url>"
'''
import sys 
from influxdb import InfluxDBClient
INFLUXDB_HOST = '10.46.8.64'
INFLUXDB_DBNAME = 'calm_st_4'
INFLUXDB_USERNAME = 'admin'
INFLUXDB_PASSWORD = 'nutanix/4u'
client = InfluxDBClient(INFLUXDB_HOST, 8086, INFLUXDB_USERNAME, INFLUXDB_PASSWORD, INFLUXDB_DBNAME)

#url = 'http://.36nutanix.com:3000/d/rau1r2eww/new-system_test-dashboard?orgId=1&var-datasource=Calm_ST_4&var-pc=ntnx-10-36-0-33-a-pcvm&var-build_no=91&from=1666935409173&to=1666939902600'

url = sys.argv[1]
l=url.split("&")
PC_HOST = l[2].split("=")[1]
BUILD_NO = l[3].split("=")[1]
START_TIME = l[4].split("=")[1]
END_TIME = l[5].split("=")[1]


# Provision timings
string = 'Provision timings'
print('-'*len(string), 'Provision timings', '-'*len(string), '\n')
#action = ['create_action', 'restart_action', 'scale_in_action', 'scale_out_action', 'start_action', 'stop_action', 'app_config_spec_action', 'snapshot_action', 'restore_action', 'image_create_action']
ACTION = 'create_action'
prov_time = client.query('select "provisioning_time" from app_provisioning where (host=\'{0}\' and build_no=\'{1}\' and runlog_type=\'{4}\' and runlog_status=\'SUCCESS\') and time >= {2}ms and time <= {3}ms'.format(PC_HOST, BUILD_NO, START_TIME, END_TIME, ACTION))
prov_time = list(prov_time.get_points(measurement='app_provisioning'))
if len(prov_time)!=0:
	prov_time_list = [float(i['provisioning_time']) for i in prov_time]
	prov_time_list = (sorted(prov_time_list, key=float))
	percentile = float((prov_time_list[round(0.90 * len(prov_time_list)) - 1])/60)
	print(ACTION, len(prov_time_list), percentile)
else:
	print(f"No data with create_action found in this time frame....")

# Calm entities
string = 'Calm entities'
print('-'*len(string), 'Calm entities', '-'*len(string), '\n')
for entity in ['apps', 'blueprints', 'runbooks', 'endpoints']:
  count = client.query('select last("metadata_total_matches") FROM "http" where (host=\'{0}\' and url=\'https://localhost:9440/api/nutanix/v3/{4}/list\' and build_no=\'{1}\') and time >= {2}ms and time <= {3}ms'.format(PC_HOST, BUILD_NO, START_TIME, END_TIME, entity))
  count = list(count.get_points(measurement='http'))
  print(entity, int(count[0]['last']))
for entity in ['project']:
  count = client.query('select last("metadata_total_matches") FROM "http" where (host=\'{0}\' and url=\'https://localhost:9440/api/nutanix/v3/groups\' and build_no=\'{1}\' and entity=\'{4}\') and time >= {2}ms and time <= {3}ms'.format(PC_HOST, BUILD_NO, START_TIME, END_TIME, entity))
  count = list(count.get_points(measurement='http'))
  print(entity, int(count[0]['last']))




