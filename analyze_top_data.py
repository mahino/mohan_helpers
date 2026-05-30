import json
s = []
with open('all_crons.txt', 'r') as f:
  r = f.readlines()
  for i in r:
    if 'KiB Swap:' in i:
      s.append([])
      continue
    t = i.split()
    if len(t)> 12  and (t[12] in ['/home/calm/venv/bin/consumption.py','/home/calm/venv/bin/policy_engine_version.py','/home/calm/venv/bin/beam_connectivity.py','/home/calm/venv/bin/ncm_license.py','/home/calm/venv/bin/ncm_license_alerts.py', '/home/calm/venv/bin/policy_engine_status.py', './consumption.py']):
      s[-1].append(t)

s = [i for i in s if i]

d = []
for i in s:
  d.append([])
  for j in i:
    memo = j[5]
    if 'm' in memo:
      memo = str(eval(memo[:-1]) * 1024)
    elif 'g' in memo:
      memo = str(eval(memo[:-1]) * 1024 * 1024)
    d[-1].append([j[-1], eval(memo)])

s = d
d = []
k = {}
for i in s:
  d.append(sum([j[-1] for j in i])) 
  for j in i:
    if j[0] in k:
      k[j[0]].append(j[-1])
    else:
      k[j[0]] = [j[-1]]
    

print(max(d))
print(sum(d)/len(d))
for i in k:
  print(i, max(k[i]))


# # max of sum all 1081244
# # policy_engine_version


