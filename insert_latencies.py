import re
import sys
import copy
import json
import time
import datetime
from influxdb import InfluxDBClient

proxies = {}
try :
  if True:
    socks_url = "socks5://{0}:{1}".format('10.132.0.60', '46862')
    proxies = { "http": socks_url, "https": socks_url }
except NameError:
  pass

client = InfluxDBClient(host='10.46.8.64', port=8086, username='root', password='nutanix/4u', database='calm_st', proxies=proxies)

command_lines = {
  "algalon": "/algalon",
  "insights": "insights_(server|uploader) --insights",
  "hercules": "/hercules",
  "durga": "durga.py",
  "aplos": "aplos.uwsgi",
  "ergon": "python .*ergon",
  "zaffi": "zaffi.ini",
  "styx": "styx.ini",
  "gadarz": "/gadarz/",
  "indra": "/indra ",
  "narad": "narad.ini",
  "postgresql": "postgresql ",
  "redis": "redis-server ",
  "jove": "jove",
  "arjun": "/arjun ",
  "karan": "/karan ",
  "vajra": "/vajra ",
  "elastic_search": "/elasticsearch ",
  "cassandra": "/org.apache.cassandra.thrift.CassandraDaemon",
  "ergon": "-B.*ergon",
  "mahakaal": "mahakaal.ini",
  "superevents": "supervisorevents.py",
  "iris": "iris",
  "achilles": "achilles.ini"
}
data={
    "measurement": "testing",
    "tags": {
      "build_no":  sys.argv[2],
      "host": "ntnx-" + sys.argv[1].replace('.', '-') + "-a-pcvm"
    },
    "fields": {}
  }
count = 0
while count < 30:
  try:
    stats_file = open("csv").readlines()
    break
  except FileNotFoundError:
    print('WARN: Waiting 30sec for stats file creation. loop ' + str(count))
    time.sleep(30)
  count += 1
else:
  print("Failed to fetch latencies file")
  sys.exit()

stats_file[0] = stats_file[0].replace('Type', "'Typr'")
stats_file[0] = stats_file[0].replace('Name', "'Name'")
stats_file[0] = stats_file[0].replace('# reqs', "'#reqs'")
stats_file[0] = stats_file[0].replace('50%', "'50%'")
stats_file[0] = stats_file[0].replace('66%', "'66%'")
stats_file[0] = stats_file[0].replace('75%', "'75%'")
stats_file[0] = stats_file[0].replace('80%', "'80%'")
stats_file[0] = stats_file[0].replace('90%', "'90%'")
stats_file[0] = stats_file[0].replace('95%', "'95%'")
stats_file[0] = stats_file[0].replace('98%', "'98%'")
stats_file[0] = stats_file[0].replace(' 99%', "'99%'")
stats_file[0] = stats_file[0].replace('99.9%', "'99.9%'")
stats_file[0] = stats_file[0].replace('99.99%', "'99.99%'")
stats_file[0] = stats_file[0].replace('100%', "'100%'")
stats_file = [line.replace('POST', "'POST'") for line in stats_file]
stats_file = [line.replace('GET', "'GET'") for line in stats_file]
stats_file = [line.replace('PUST', "'PUT'") for line in stats_file]
stats_file = [line.replace('DeveloperUserBehavior', "'DeveloperUserBehavior") for line in stats_file]
stats_file = [line.replace('/api/', "'/api/") for line in stats_file]
stats_file = [line.replace('/list', "/list'") for line in stats_file]
stats_file = [line.replace('/status', "/status'") for line in stats_file]
stats_file = [line.replace('/groups', "/groups'") for line in stats_file]
stats_file = [line.replace('/action_restart', "/action_restart'") for line in stats_file]
stats_file = [line.replace('/action_scale_in', "/action_scale_in'") for line in stats_file]
stats_file = [line.replace('/action_scale_out', "/action_scale_out'") for line in stats_file]
stats_file = [line.replace('/action_start', "/action_start'") for line in stats_file]
stats_file = [line.replace('/action_stop', "/action_stop'") for line in stats_file]
stats_file = [line.replace('/api_keys ', "/api_keys'") for line in stats_file]
stats_file = [line.replace('/DISABLED', "/DISABLED'") for line in stats_file]
stats_file = [line.replace('/ENABLED', "/ENABLED'") for line in stats_file]
stats_file = [line.replace('/RESET', "/RESET'") for line in stats_file]
stats_file = [line.replace('/apps ', "/apps'") for line in stats_file]
stats_file = [line.replace('/apps_provisioning', "/apps_provisioning'") for line in stats_file]
stats_file = [line.replace('/blueprint_create', "/blueprint_create'") for line in stats_file]
stats_file = [line.replace('/blueprint_launch', "/blueprint_launch'") for line in stats_file]
stats_file = [line.replace('/blueprint_update', "/blueprint_update'") for line in stats_file]
stats_file = [line.replace('/blueprints ', "/blueprints'") for line in stats_file]
stats_file = [line.replace('/pending_launches', "/pending_launches'") for line in stats_file]
stats_file = [line.replace('/tunnels ', "/tunnels'") for line in stats_file]
compound_stats = [line.split() for line in stats_file]
stats=[]
for stat in compound_stats:
  stats.append([sub_stat.replace("\n","") for sub_stat in stat])
t_time = datetime.datetime.fromtimestamp(int(sys.argv[3])/1000).strftime('%Y-%m-%d %H:%M:%S')
data['measurement'] = 'api_latency_percentile_2'
data['time'] = t_time
for i in stats[1:]:
  ins_data=copy.deepcopy(data)
  for count, ele in enumerate(i):
    print(i[0])
    if eval(stats[0][count]) == "Name":
      ins_data['tags'][eval(stats[0][count])] = eval(ele)
    else:
      if eval(stats[0][count]) == '#reqs':
        ins_data['fields']['# requests'] = eval(ele)
        continue
      ins_data['fields'][eval(stats[0][count])] = eval(ele)
  client.write_points([ins_data])

