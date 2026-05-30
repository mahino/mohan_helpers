
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
      "build_no":  sys.argv[3],
      "host": "ntnx-" + sys.argv[1].replace('.', '-') + "-a-pcvm"
    },
    "fields": {}
  }

if sys.argv[2] == 'PC':
  t_time = datetime.datetime.fromtimestamp(int(sys.argv[3])).strftime('%Y-%m-%d %H:%M:%S')
  data['time'] = t_time
  ins_data = copy.deepcopy(data)
  ins_data['measurement'] = 'mem'
  ins_data['fields']['used_percent'] = float(sys.argv[4])
  ins_data['fields']['used'] = int(sys.argv[6])*1024
  client.write_points([ins_data])

  ins_data = copy.deepcopy(data)
  ins_data['measurement'] = 'cpu'
  ins_data['fields']['usage_user'] = float(sys.argv[5])
  client.write_points([ins_data])
  sys.exit()

elif sys.argv[2] == 'docker':
  t_time = datetime.datetime.fromtimestamp(int(sys.argv[3])).strftime('%Y-%m-%d %H:%M:%S')
  data['time'] = t_time
  data['tags']['container_name'] = sys.argv[4]

  ins_data = copy.deepcopy(data)
  ins_data['measurement'] = 'docker_container_mem'
  usage_perc=re.findall(r"\d\.\d+", sys.argv[5])
  ins_data['fields']['usage_percent'] = float(usage_perc[0])
  rss=re.findall(r"\d\.\d+", sys.argv[7])
  ins_data['fields']['rss'] = int(float(rss[0])*1024*1024*1024)
  client.write_points([ins_data])

  ins_data = copy.deepcopy(data)
  ins_data['measurement'] = 'docker_container_cpu'
  cpu_perc=re.findall(r"\d\.\d+", sys.argv[6])
  ins_data['fields']['usage_percent'] = float(cpu_perc[0])
  client.write_points([ins_data])
  sys.exit()

elif sys.argv[2] in ['calm', 'epsilon', 'services']:
  process_data = sys.argv[4].rsplit(':',1)
  process = process_data[len(process_data)-1]
  if len(re.findall('[0-9]', process)):
    process = process.rsplit('_', 1)[0]
  if process in ['jove', 'superevents']:
    cmdline = sys.argv[2] + '\/bin\/' + command_lines[process]
    cmdline = command_lines[process]
  else:
    cmdline = command_lines[process]
  data['measurement'] = 'procstat'
  data['tags']['cmdline'] = cmdline
  data['tags']['pid'] = sys.argv[5]
  data['tags']['process_name'] = process
  data['fields']['memory_usage'] = float(sys.argv[6])
  data['fields']['cpu_usage'] = float(sys.argv[7])
  if process == 'insights':
    memory_rss=re.findall(r"\d\.\d+", sys.argv[8])
    data['fields']['memory_rss'] = float(memory_rss[0])*1024*1024*1024
  else:
    data['fields']['memory_rss'] = int(sys.argv[8])*1024
  if any(pro in process for pro in ["arjun", "karan", "gadarz", "indra", "durga", "hercules"]):
    data['tags']['process_num'] = sys.argv[9]
  elif any(pro in process for pro in ["styx", "iris", "zaffi"]):
    if len(sys.argv) == 10:
      data['tags']['type'] = sys.argv[9]
  t_time = datetime.datetime.fromtimestamp(int(sys.argv[3])).strftime('%Y-%m-%d %H:%M:%S')
  data['time'] = t_time

elif sys.argv[2] == 'idf_entities':
  data_file = {}
  try:
    data_file = open(sys.argv[4])
    data_file = json.load(data_file)
  except IOError as file_not_found_error:
    pass

  for entity in data_file:
    data['fields'][entity] = float(data_file[entity])
  data['measurement'] = 'idf_entities'
  t_time = datetime.datetime.fromtimestamp(int(sys.argv[3])).strftime('%Y-%m-%d %H:%M:%S')
  data['time'] = t_time

elif sys.argv[2] == 'http':
  data['measurement'] = 'http'
  data_file = json.loads(sys.argv[6])
  data['tags']['url'] = sys.argv[5]
  if sys.argv[4] == 'list_call':
    data['fields']['metadata_total_matches'] = float(data_file['metadata']['total_matches'])
  elif sys.argv[4] == 'group_call':
    data['tags']['entity'] = sys.argv[7]
    data['fields']['metadata_total_matches'] = float(data_file['filtered_entity_count'])
  t_time = datetime.datetime.fromtimestamp(int(sys.argv[3])).strftime('%Y-%m-%d %H:%M:%S')
  data['time'] = t_time

elif sys.argv[2] == 'latencies':
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
  sys.exit()

elif sys.argv[2] == 'load_average':
  data['measurement'] = 'system'
  data['fields']['load1'] = float(sys.argv[4].replace(',', ''))
  data['fields']['load5'] = float(sys.argv[5].replace(',', ''))
  data['fields']['load15'] = float(sys.argv[6].replace(',', ''))
  t_time = datetime.datetime.fromtimestamp(int(sys.argv[3])).strftime('%Y-%m-%d %H:%M:%S')
  data['time'] = t_time

client.write_points([data])
