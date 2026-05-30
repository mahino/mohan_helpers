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
stats_file = [line.replace('/validate_launch ', "/validate_launch'") for line in stats_file]
stats_file = [line.replace('/export_json ', "/export_json'") for line in stats_file]

compound_stats = [line.split() for line in stats_file]
stats=[]
for k in [2,7]:
  for i in ['apps/list', 'blueprints/list', 'blueprint_create', 'blueprint_launch', 'blueprint_update', 'blueprints', 'apps', 'validate_launch', 'export_json', 'lol', 'lol', 'action_restart', 'action_scale_in', 'action_scale_out', 'action_start', 'action_stop']:
    for stat in compound_stats:
      if i in stat[1]:
        if i in ['apps', 'blueprints']:
          if stat[0] == 'POST':continue
        if k == 7:
          print(round(float(int(stat[k])/1000), 3))
        else:
          print(stat[k])
        break
      if i == 'lol':
        print('')
        break
  print('-'*100)
for stat in compound_stats[1:]:
  if round(float(int(stat[k])/1000), 3) >= 15:
    print(stat[1], round(float(int(stat[k])/1000), 3))

