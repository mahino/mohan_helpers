import requests
import subprocess
import json
import sys
import re
import time

task_count = 1
loop_count_int = int(sys.argv[1]) if len(sys.argv) == 2 else 1
all_erg_comp_task_count = {}
uuid_pattern = r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'

not_iden = []
for loop_count in range(loop_count_int):
  response = requests.get(
            f"http://pc-10-117-59-93.nutanixqa.com:2027/all_entities",
            params={"type": "category_association","offset": loop_count * 500, "limit":500},
            timeout=10
        )
  print(f"pc-10-117-59-93.nutanixqa.com:2027/all_entities?type=category_association&offset={loop_count * 500}&limit=500")
  s = response.text.strip().splitlines()
  t = []
  m = []
  for i in s[75:]:
    if '<td><p><a href=/entities?id=' in i:
      uuids = re.findall(uuid_pattern, i)
      m.append(uuids[0])

  for i in m:
    print(f"Fetching task uuid [{i}], count [{task_count}]")
    print(f"pc-10-117-59-93.nutanixqa.com:2027/entities?id={i}&type=category_association")
    response = requests.get(
            f"http://pc-10-117-59-93.nutanixqa.com:2027/entities",
            params={"id": i, "type": "category_association"},
            timeout=10
        )
    response.raise_for_status()
    s = response.text.strip().splitlines()
    for g, j in enumerate(s):
      if 'name: &quot;kind&quot;' in j:
        l = ''.join(s[g+3].split()[1:]) 
        if l in all_erg_comp_task_count:
          all_erg_comp_task_count[l] += 1
        else:
          all_erg_comp_task_count[l] = 1
    task_count += 1
  print("LOL")
print(json.dumps(all_erg_comp_task_count))