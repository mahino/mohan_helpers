"""Create Calm custom forms (POST api/calm/v3.0/custom_forms)."""

import copy
import json
import sys
import uuid

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://{}:9440/'.format(sys.argv[1])
NUM_TABS = 5

client = requests.Session()
client.auth = HTTPBasicAuth("admin", "Nutanix.123")
client.headers = {"content-type": "application/json"}
client.verify = False

custom_form_pay = {
    "api_version": "3.0",
    "metadata": {
        "kind": "custom_form",
        "project_reference": {
            "kind": "project",
            "uuid": "",
        },
        "uuid": "00000000-0000-0000-0000-000000000001",
    },
    "spec": {
        "name": "custom_form_placeholder",
        "description": "This is a custom form",
        "resources": {
            "uischema": {
                "type": "TabLayout",
                "elements": [
                    {
                        "title": "Tab 1",
                        "type": "Group",
                        "elements": [
                            {
                                "type": "Control",
                                "variant": "radio",
                                "label": "Radio Options",
                                "elements": [
                                    {"label": "Option 1", "value": "option1"},
                                    {"label": "Option 2", "value": "option2"},
                                    {"label": "Option 3", "value": "option3"},
                                ],
                                "id": "control_566502d9-ee66-fafa-24a9-a88a055f60c2",
                            },
                            {
                                "type": "Control",
                                "variant": "select",
                                "scope": "#",
                                "label": "Select",
                                "options": {
                                    "elements": [
                                        {"label": "Option 1", "value": "option1"},
                                        {"label": "Option 2", "value": "option2"},
                                    ]
                                },
                                "id": "control_b2d37df0-ca5c-532a-83bb-29c8a89820a5",
                            },
                            {
                                "type": "Control",
                                "variant": "checkbox-group",
                                "scope": "",
                                "label": "Checkbox Group",
                                "description": "",
                                "elements": [
                                    {"label": "Option 1", "value": "option1"},
                                    {"label": "Option 2", "value": "option2"},
                                ],
                                "id": "control_6689d613-89e3-547d-7de9-855f16f056c8",
                            },
                            {
                                "type": "Control",
                                "variant": "textarea",
                                "label": "Multi Line Text",
                                "options": {"multiline": True, "rows": 4},
                                "id": "control_ce79c050-85f2-fc1d-3931-5d18238328f9",
                            },
                            {
                                "type": "Control",
                                "variant": "number",
                                "label": "Number Input",
                                "options": {
                                    "min": 0,
                                    "step": "4",
                                    "max": "1000"
                                },
                                "id": "control_bec8d3ae-2280-e149-07a1-023a19315579",
                            },
                            {
                                "type": "Control",
                                "variant": "text",
                                "label": "Text Input",
                                "id": "control_8ea98106-c46d-2f82-8bff-82e2282f2af3",
                                "scope": "#/properties/y4eryt",
                                "validation": {"pattern": "^[\\\\s\\\\S]*$"},
                                "placeholder": "3ef",
                            },
                        ],
                        "id": "group_75e6d24b-0776-402a-4c4c-d1cdcdb0f4e2",
                    }
                ],
                "id": "tablayout_c8d42424-8f07-d547-dc3e-02560c5b1c79",
            },
            "schema": "",
        },
    },
}

def _regenerate_uischema_id(control_id):
    """Fresh UUID suffix for group_/control_/tablayout_ ids."""
    for prefix in ("group_", "control_", "tablayout_"):
        if not control_id.startswith(prefix):
            continue
        tail = control_id[len(prefix) :]
        try:
            uuid.UUID(tail)
        except (ValueError, TypeError, AttributeError):
            return control_id
        return prefix + str(uuid.uuid4())
    return control_id

def _regenerate_custom_form_uuids(node):
    """Replace spec uuid fields and uischema ids (must run while uischema is still a dict)."""
    if isinstance(node, dict):
        for key, val in node.items():
            if key == "uuid" and isinstance(val, str):
                try:
                    uuid.UUID(val)
                except (ValueError, TypeError, AttributeError):
                    _regenerate_custom_form_uuids(val)
                else:
                    node[key] = str(uuid.uuid4())
            elif key == "id" and isinstance(val, str):
                node[key] = _regenerate_uischema_id(val)
            else:
                _regenerate_custom_form_uuids(val)
    elif isinstance(node, list):
        for item in node:
            _regenerate_custom_form_uuids(item)


count = 0
bp_list_resp = client.post(BASE_URL + 'api/nutanix/v3/groups', data=json.dumps({"entity_type":"nucalm_app_blueprint","group_member_attributes":[{"attribute":"name"},{"attribute":"project_reference"}],"filter_criteria":"state!=DELETED;cloned!=true","group_member_offset":244,"group_member_count":500,"group_member_sort_order":"DESCENDING","group_member_sort_attribute":"_created_timestamp_usecs_"}))
bp_list_resp = json.loads(bp_list_resp.content)
for bp in bp_list_resp['group_results'][0]['entity_results']:
    custom_form_pay["metadata"]["uuid"] = str(uuid.uuid4())
    custom_form_pay["spec"]["name"] = bp['data'][0]['values'][0]['values'][0] + "_custom_form"
    pay = copy.deepcopy(custom_form_pay)
    pay["metadata"]["project_reference"]["uuid"] = bp['data'][1]['values'][0]['values'][0]
    uischema = pay["spec"]["resources"]["uischema"]
    tab_template = copy.deepcopy(uischema["elements"][0])
    uischema["elements"] = []
    for t in range(NUM_TABS):
        tab = copy.deepcopy(tab_template)
        tab["title"] = "Tab {}".format(t + 1)
        uischema["elements"].append(tab)

    _regenerate_custom_form_uuids(pay["spec"])

    pay["spec"]["resources"]["uischema"] = json.dumps(
        pay["spec"]["resources"]["uischema"]
    )
    resp = client.post(BASE_URL + 'api/calm/v3.0/custom_forms', data=json.dumps(pay))
    try:
        response = json.loads(resp.content)
    except json.JSONDecodeError:
        print(resp.status_code, resp.content)
        continue

    if resp.status_code != 200:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Custom form [{response['spec']['name']}] created successfully")
    print(f"Updating Blueprint [{bp['data'][0]['values'][0]['values'][0]}]")
    bp_pay_resp = client.get(BASE_URL + 'api/nutanix/v3/blueprints/' + bp['entity_id'])
    bp_pay_resp = json.loads(bp_pay_resp.content)
    payload = {
          'api_version': bp_pay_resp['api_version'],
          'metadata': bp_pay_resp['metadata'],
          'spec': bp_pay_resp['spec']
        }
    payload['spec']['resources']['app_profile_list'][0]['use_custom_form'] = True
    payload['spec']['resources']['app_profile_list'][0]['custom_form_reference'] = {
        "uuid": response['metadata']['uuid']
    }

    resp = client.put(BASE_URL + 'api/nutanix/v3/blueprints/' + bp['entity_id'], data=json.dumps(payload))
    if resp.status_code != 200:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Blueprint [{bp['data'][0]['values'][0]['values'][0]}] updated successfully, [{count}]")
    count += 1