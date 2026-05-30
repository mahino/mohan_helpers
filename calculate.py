## calculate_task_size.py
import re
import base64
import json

file = open('decoded.txt', 'r')
lines = file.readlines()

file1 = open('result3.txt', 'w')
file2 = open('diff.txt', 'w')

count = 0

for line in lines:
  length = len(line)
  body = "\"body\":\""
  words = line.split('"body":"')
  if len(words) > 2:
    count = count + 1
    word = words[2]
    word2 = word.split('","')[0]
    obj = json.loads(word2)
    final_str = ""
    if "params" in obj:
      if "params" in obj["params"][0]:
        int_param = obj["params"][0]["params"]
        final_str = int_param["az_task_type"]
      if "data" in obj["params"][0]:
        data_int = obj["params"][0]["data"]
        if data_int is not None:
          if "calm_entity_type" in data_int["calm_data"].keys():
            final_str = final_str + " ," + data_int["calm_data"]["calm_entity_type"]
          else:
            final_str = final_str + " ,"
        else:
            final_str = final_str + " ," + str(obj["params"][0])

      final_str = final_str + ", " + str(length) + ", " + str(count)
          #int_param = str(data["params"])
          #for p in obj2:
          #  print str(p["az_task_type"])
      file1.write(final_str)
          #file1.write(str(length))
      file1.write("\n")
    else:
      file2.write(decoded)