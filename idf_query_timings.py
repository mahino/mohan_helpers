# CALM-21015

# IDF log parser:

# temporary files generated: It will create tmp.txt, tmp_2.txt for query counts, and tmp_time.txt,

#            tmp_time_2.txt for time mappings.

# Final:

# dictfile.log

# It will create a mpaaping of each table, and attributes used for where clause and total time taken for them

# ```python
"""
Copyright (c) 2021 Nutanix Inc. All rights reserved.

Authors : aryan.rai@nutanix.com

"""
# pylint: disable=all
# nulint: disable=DocstringValidator
# nulint: disable=ImportsValidator
# nulint: disable=FunctionOrderingValidator
# nulint: disable=ExceptionTypeValidator
# nulint: disable=MetadataValidator

import os
import pprint

os.popen(r'grep "where_clause" ./insights_server.ntnx*INFO* > tmp.txt').read()
os.popen(r'grep -nshoP "Request id: .*?. |entity_type_name: \".*?\"|leaf { column: \".*?\"" ./tmp.txt > tmp2.txt').read()

os.popen(r'grep -P "RPC GetEntities.* entity_type_name: \"nucalm_.*?\"" ./insights_server.ntnx*INFO* > tmp_calm_requests.txt').read()
os.popen(r'grep -nshoP "Request id: .*?. |entity_type_name: \".*?\"" ./tmp_calm_requests.txt > tmp_calm_requests_2.txt').read()

# For time queries
os.popen(r'grep -P "RPC GetEntities.* Done. Took .*?s" ./insights_server*INFO* > tmp_time.txt').read()
os.popen(r'grep -nshoP "Took .*?s|Request id: .*?. " ./tmp_time.txt > tmp_time_2.txt').read()

# ----------------------- START ----IDF to find mapping of request id and time taken by it -------------------- 

query_time_data = {}
with open('tmp_time_2.txt', "r") as fh:
  for each in fh.readlines():
    nkey = int(each.split(":")[0])
    if not query_time_data.get(nkey, False):
      query_time_data[nkey] = {} 
    try:
      if 'Request id' in each:
        try:
          query_time_data[nkey]['request_id'] = str(each.split(': ')[1][:-3])
        except Exception as exp:
          import pdb; pdb.set_trace()
      elif "Took" in each:
        _t1 = each.split("Took ")[1]
        t2 = _t1.split(" ")
        query_time_data[nkey]["time"] = {
          "count": t2[0],
          "unit": t2[1][:-1]
        }
    except Exception as err:
      print each
      print err
  
query_time_in_us_map = {}
for qd in query_time_data.values():
  try:
    tius = int(qd["time"]["count"])
    if qd["time"]["unit"] == "us":
      tius = tius
    elif qd["time"]["unit"] == "ms":
      tius = tius*1000
    elif qd["time"]["unit"] == "s":
      tius = tius*1000*1000
    query_time_in_us_map[qd["request_id"]] = tius
  except Exception as exp:
    print exp

# ----------------------- END ----IDF to find mapping of request id and time taken by it -------------------- 

# ----------------------- START ----IDF request time and count checks having where clause -------------------- 

abc = {}

with open('tmp2.txt', "r") as fh:
  for each in fh.readlines():
    nkey = int(each.split(":")[0])
    if not abc.get(nkey, False):
      abc[nkey] = {}    # abc[1] = {}, abc[2] = {}
    if nkey in abc:
      try:
        if 'entity_type_name' in each:
          abc[nkey]['entity_type_name'] = str(each.split('"')[1])
        elif 'Request id' in each:
          req_id = str(each.split(': ')[1][:-3])
          abc[nkey]['request_id'] = req_id
          if query_time_in_us_map.get(req_id):
            abc[nkey]['time_in_us'] = query_time_in_us_map[req_id]
          else:
            abc[nkey]['time_in_us'] = -1
        else:
          if abc[nkey].get('filter_clause', False):
            abc[nkey]['filter_clause'].append(str(each.split('"')[1]))
          else:
            abc[nkey]['filter_clause'] = []
            abc[nkey]['filter_clause'].append(str(each.split('"')[1]))
      except Exception as err:
        print each
        print err

nabc = {}
"""
Response = {
  "<entity_type>": {
    "Filter_Clause_With_Where_Clause_1": <Count_1>,
    "Filter_Clause_With_Where_Clause_2": <Count_2>,
    "time_in_us": "<Total time taken by all the queries for given entity type (including all type of filter clauses)>",
    "unknown_time_queries": "<no. of quesies, whose response time not found>"
  }
}
"""

for each in abc:
  try:
    if abc[each]['entity_type_name'] not in nabc:
      nabc[abc[each]['entity_type_name']] = {"time_in_us": 0, "unknown_time_queries": 0}
      if str(abc[each]['filter_clause']) not in nabc[abc[each]['entity_type_name']].keys():
        nabc[abc[each]['entity_type_name']][str(abc[each]['filter_clause'])] = 1
      else:
        nabc[abc[each]['entity_type_name']][str(abc[each]['filter_clause'])] += 1
    else:
      if str(abc[each]['filter_clause']) not in nabc[abc[each]['entity_type_name']].keys():
        nabc[abc[each]['entity_type_name']][str(abc[each]['filter_clause'])] = 1
      else:
        nabc[abc[each]['entity_type_name']][str(abc[each]['filter_clause'])] += 1
    
    if abc[each]["time_in_us"] == -1:
      nabc[abc[each]['entity_type_name']]["unknown_time_queries"] += 1
    else:
      nabc[abc[each]['entity_type_name']]["time_in_us"] += abc[each]["time_in_us"]
  except Exception as err:
    print each
    print err

# ----------------------- END ----IDF request time and count checks having where clause -------------------- 

# ----------------------- START ----Calm request time and count checks -------------------- 

tmp_calm_request_map = {}
"""
Response = {
  1: {
    "request_id": "dfbgef"
    "entity_type": "nucalm_task"
  }
}
"""
with open('tmp_calm_requests_2.txt', 'r') as fh:
  for each in fh.readlines():
    nkey = int(each.split(":")[0])
    if not tmp_calm_request_map.get(nkey, False):
      tmp_calm_request_map[nkey] = {}
    try:
      if 'Request id' in each:
        tmp_calm_request_map[nkey]['request_id'] = str(each.split(': ')[1][:-3])
      elif "entity_type_name" in each:
        tmp_calm_request_map[nkey]['entity_type'] = str(each.split('"')[1])
    except Exception as err:
      print each
      print err

calm_request_map = {}
"""
Response: {
  "<entity_type>" : {
    "count": <count>
    "time_in_us": "<time_in_micro_seconds>"
    "unknown_time_queries": "no. of quesies, whose response time not found"
  }
}
"""
for _calmdata in tmp_calm_request_map.values():
  try:
    entity_type = _calmdata["entity_type"]
    req_id = _calmdata["request_id"]
    if entity_type not in calm_request_map:
      calm_request_map[entity_type] = {
        "count": 0,
        "time_in_us": 0,
        "unknown_time_queries": 0
      }
    calm_request_map[entity_type]["count"] += 1

    if query_time_in_us_map.get(req_id):
      calm_request_map[entity_type]["time_in_us"] += query_time_in_us_map[req_id]
    else:
      calm_request_map[entity_type]["unknown_time_queries"] += 1
  except Exception as exp:
    import pdb; pdb.set_trace()
  

# ----------------------- END ----Calm request time and count checks -------------------- 

time_list = []
with open('tmp.txt', "r") as fh:
  for each in fh.readlines():
    try:
      _date = str(each.split(" ")[0][1:])
      _time = str(each.split(" ")[1].split(".")[0])
      time_list.append("{}-{}". format(_date, _time))
    except:
      pass

time_list = sorted(time_list)
start = "START TIME : " + time_list[0]
end = "END TIME : " + time_list[-1]

with open("dictfile.log", "w") as log_file:
  pprint.pprint(nabc, log_file)
  pprint.pprint(start, log_file)
  pprint.pprint(end, log_file) 

with open("dictfile_calm.log", "w") as log_file:
  pprint.pprint(calm_request_map, log_file)
# ```

# Styx logs parser:

# ```python
"""
Script to get the count of db query for 

"""

import os
import pprint

os.popen('grep -shoE  "Db_Query_Session_Id.*?" ./styx.log > tmp_calm_styx.txt').read()
styx_query_data = {}

with open('tmp_calm_styx.txt', "r") as fh:
    for each in fh.readlines():
        _db_log = each.split("; ")
        session_id = _db_log[0].split(":")[1]
        if not styx_query_data.get(session_id):
            styx_query_data[session_id] = {}
        query_type = _db_log[1].split(":")[1]
        if query_type == "GetEntities":
            entity_type = _db_log[2].split(":")[1].split("_pb2.")[1].split("'")[0]
            if entity_type not in styx_query_data[session_id]:
                styx_query_data[session_id][entity_type] = {
                    "count": 0,
                    "type": "GetEntities",
                    "entities": []
                }
            styx_query_data[session_id][entity_type]["count"] += 1
            styx_query_data[session_id][entity_type]["entities"].append(_db_log[3].split(":")[1])
        elif query_type == "Query_With_Total_Matches":
            entity_type = _db_log[2].split(":")[-1].split('"')[1]
            if entity_type not in styx_query_data[session_id]:
                styx_query_data[session_id][entity_type] = {
                    "count": 0,
                    "type": "Query",
                }
            styx_query_data[session_id][entity_type]["count"] += 1
        else:

query_total_cnt_map = {}
for qd in styx_query_data.values():
    for _k, _v in qd.items():
        if _k == "query_type":
            continue
        if not query_total_cnt_map.get(_k):
            query_total_cnt_map[_k] = 0
        query_total_cnt_map[_k] += _v["count"]

# styx_query_data["TOTAL_QUERIES_MAP"] = query_total_cnt_map

with open("styx_dict.log", "w") as log_file:
    pprint.pprint(styx_query_data, log_file)

with open("styx_query_count_dict.log", "w") as log_file:
    pprint.pprint(query_total_cnt_map, log_file)
