# import uuid
# import json
# import copy
# s = []

# k = []

# for i in range(1,501):
#     k.append({
#                         "attrs": {
#                             "type": "LOCAL"
#                         },
#                         "regex": {
#                             "value": "^.*$",
#                             "should_validate": False
#                         },
#                         "name": "variable_" + str(i),
#                         "data_type": "BASE",
#                         "value": "variable_value_" + str(i),
#                         "label": "",
#                         "val_type": "STRING",
#                         "type": "LOCAL",
#                         "description": "",
#                         "options": {
#                             "type": "PREDEFINED",
#                             "choices": []
#                         },
#                         "is_hidden": False,
#                         "uuid": str(uuid.uuid4())
#                     })
# print(json.dumps(k))
for i in range(1,501):
    print('echo "@@{variable_' + str(i) + '}@@"')