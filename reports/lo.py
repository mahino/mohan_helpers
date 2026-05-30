import sys

client = InfluxDBClient(host='10.46.8.64', port=8086, username='root', password='nutanix/4u', database='reports')

data={
    "measurement": "api_latency_percentile",
    "tags": {
      'calm_version': '3.3.0',
      'provider': 'EM'
    },
    "fields": {}
  }

stats_file = open("csv").readlines()
try:
  q=int(sys.argv[1])
except IndexError:
  q=14
for i in stats_file:
  i = i.split()
  data['tags']['Name'] = i[2]
  i[q] = float(i[q])
  if i[q+1] == 's':
    i[q] = i[q]*1000
  if i[q+1] == 'min':
    m,s= i.split()
    i[q] = int(m)*60 + int(s)*0.6
  data['fields']['90%'] = i[q]
  data['fields']['Type'] = i[3]
  data['fields']['requests'] = float(i[4])
  if q == 14:
    data['fields']['failures'] = float(i[q])
  else:
    data['fields']['failures'] = 0.0
  data['time'] = i[0] + ' ' + i[1]
  client.write_points([data])

