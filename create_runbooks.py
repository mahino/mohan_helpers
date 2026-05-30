""" Nucalm environment setup"""


import os
import sys
import json
import uuid
import time
import copy
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = f"https://{sys.argv[1]}:9440/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

V3 = 'api/nutanix/v3/'

URL = BASE_URL + V3

task_pay = {
    "variable_list": [],
    "attrs": {
        "script_type": "sh",
        "login_credential_local_reference": {
            "kind": "app_credential",
            "uuid": "00a68e94-00bc-d979-81e2-e9a1201d9da9"
        },
        "script": "date\necho \"sample text: installing random feature\"\ndate"
    },
    "name": "Task 10",
    "status_map_list": [],
    "inherit_target": False,
    "target_any_local_reference": {
        "kind": "app_endpoint",
        "name": "vpc_ep_10_10_10_97",
        "uuid": "8a4b538c-d3a8-4ce8-a159-ddbcf5a11afa"
    },
    "child_tasks_local_reference_list": [],
    "type": "EXEC",
    "uuid": "d9248aa4-1311-1c74-234f-31568906f06c"
}
rb_pay = {
    "spec": {
        "resources": {
            "credential_definition_list": [{"name":"admin","type":"PASSWORD","cred_class":"static","username":"root","secret":{"attrs":{"is_secret_modified":True},"value":"nutanix/4u"},"uuid":"35969953-7fc7-583c-b4f5-49ebb9dde5d1"}],
            "endpoint_definition_list": [],
            "runbook": {
                "name": "7a569433_runbook",
                "variable_list": [],
                "task_definition_list": [
                    {
                        "name": "6beb4ef6_dag",
                        "type": "DAG",
                        "child_tasks_local_reference_list": [
                            {
                                "kind": "app_task",
                                "uuid": "11347f51-4f78-5b27-05a5-e4c685d3a5f8"
                            }
                        ],
                        "attrs": {
                            "edges": []
                        },
                        "uuid": "060a8735-7383-ccda-6a8c-b75fb506997d"
                    },
                    {
                        "name": "Task 1",
                        "attrs": {
                            "script_type": "sh",
                            "script": "date"
                        },
                        "variable_list": [],
                        "child_tasks_local_reference_list": [],
                        "type": "EXEC",
                        "status_map_list": [],
                        "uuid": "11347f51-4f78-5b27-05a5-e4c685d3a5f8"
                    }
                ],
                "main_task_local_reference": {
                    "kind": "app_task",
                    "uuid": "060a8735-7383-ccda-6a8c-b75fb506997d"
                },
                "uuid": "c0b97ee8-5a41-4d85-b512-99e9f3cb5805"
            },
            "default_target_reference": {
                "name": "stress_single_vm",
                "kind": "app_endpoint",
                "uuid": "4da0cce5-94fa-9619-3b85-67a412a97bcf"
            }
        },
        "name": "vpc1"
    },
    "api_version": "3.0",
    "metadata": {
        "kind": "runbook",
        "project_reference": {
            "name": "vpc",
            "kind": "project",
            "uuid": "3d00e185-ba99-4a63-a7b8-9d3f290a1762"
        },
        "uuid": "50f58c1f-8465-e5aa-b39f-b0dbab9859a8"
    }
}

# eps = [["vpc_ep_10_10_10_95", "0e166c7d-b93b-4064-9c25-a10fc53f84a7"], ["vpc_ep_10_10_10_93", "30384915-428f-408a-b784-66fce9276573"], ["vpc_ep_10_10_10_91", "808152b3-7b6c-48a7-b1c1-4a222c4805c9"], ["vpc_ep_10_10_10_88", "388dd279-ece3-4dc2-913d-1323ae65cef4"], ["vpc_ep_10_10_10_87", "e0436c54-129f-4c2f-b798-f2fd8316ea04"], ["vpc_ep_10_10_10_82", "d1206cfa-33c1-4546-b49c-edc7e6e657ae"], ["vpc_ep_10_10_10_8", "bff302a6-42ca-433c-88f4-efcf78c4d7f0"], ["vpc_ep_10_10_10_76", "243028a6-4923-4df0-a8e0-f52cce39a865"], ["vpc_ep_10_10_10_75", "eead7adf-eafc-4dd4-9ca0-3373cabc80f2"], ["vpc_ep_10_10_10_74", "058b7b6e-7f0c-4df5-822f-3a4ecfae1bc9"], ["vpc_ep_10_10_10_73", "bd934ccf-a6b0-4085-90fd-32662df01dfb"], ["vpc_ep_10_10_10_72", "cadb7a55-72d9-46a3-bfac-3d85eff87d9f"], ["vpc_ep_10_10_10_70", "e9da9b5a-7141-46f5-895f-111e0ef4171b"], ["vpc_ep_10_10_10_68", "de23802a-3784-4a82-88ac-67c3bec2a410"], ["vpc_ep_10_10_10_67", "cf54a2c4-18fb-41e2-9084-435d6f757590"], ["vpc_ep_10_10_10_65", "e95cc257-b146-4894-bf10-abe84bcd863b"], ["vpc_ep_10_10_10_62", "d02d39a8-b1c8-4eec-bea9-b505ad0e175b"], ["vpc_ep_10_10_10_60", "f41f3c90-9d8c-4251-ac19-dccaf807903c"], ["vpc_ep_10_10_10_56", "4fedf78b-67b0-4a0d-8189-af6771293b50"], ["vpc_ep_10_10_10_51", "1fb65d20-a4ae-49ec-ae14-3ab59e9dd6c8"], ["vpc_ep_10_10_10_5", "ba1b6d65-9656-4d8e-be89-1a4f7245fbc0"], ["vpc_ep_10_10_10_49", "0d938d78-ce3d-409e-84f2-21aae06dcc6f"], ["vpc_ep_10_10_10_48", "249cc7aa-2ea0-4c34-8ada-fe297bbb8d93"], ["vpc_ep_10_10_10_47", "238ec5e9-3659-4f2d-823b-994c7d0f44a7"], ["vpc_ep_10_10_10_43", "27ea3a68-77bb-477c-a099-350a4082fa88"], ["vpc_ep_10_10_10_42", "d13bc65b-3d04-4519-8a40-be5320b87a28"], ["vpc_ep_10_10_10_41", "dfd36f43-dd43-477b-ae08-1ed628bd440b"], ["vpc_ep_10_10_10_35", "1bc6f6a0-9e0a-4c7d-96b9-6df255dddc59"], ["vpc_ep_10_10_10_32", "80cded65-f7ff-4484-ba34-bd23cbed24bd"], ["vpc_ep_10_10_10_30", "b5ec8134-3637-47af-8c96-8e824e8fe5d1"], ["vpc_ep_10_10_10_25", "c1c94c33-b894-458a-b6da-c6bf3a40e32a"], ["vpc_ep_10_10_10_247", "f4b8d8c4-b805-4e89-b8f6-e37f09173523"], ["vpc_ep_10_10_10_246", "32a91061-e99a-4739-9875-190c2a6bfae5"], ["vpc_ep_10_10_10_243", "1c401f8d-a6b6-42b3-ab93-006e735b93af"], ["vpc_ep_10_10_10_242", "418f4dbb-d873-46d8-961b-ba435ab733ca"], ["vpc_ep_10_10_10_239", "97567b52-8f65-44fc-8960-7e7ab0ff5f6a"], ["vpc_ep_10_10_10_238", "3dda8165-1c0e-4596-a794-578e1517fdef"], ["vpc_ep_10_10_10_234", "f4cc60c2-e37f-4af5-9ebc-5e34a6c4be5f"], ["vpc_ep_10_10_10_232", "abbf3e61-bde6-4b93-a8a7-ec6b373e7d26"], ["vpc_ep_10_10_10_231", "1def1f4a-9a74-4221-a197-ed789d767bc9"], ["vpc_ep_10_10_10_229", "dfb2bcdb-a6f5-4746-8afe-452c46ccca09"], ["vpc_ep_10_10_10_226", "da648521-bfba-4c97-9f83-e18e0610e185"], ["vpc_ep_10_10_10_225", "faa37f78-41ca-4400-9a4d-a252d1198691"], ["vpc_ep_10_10_10_223", "e6e91917-dcb7-4ca0-838b-7cc4172abf8e"], ["vpc_ep_10_10_10_222", "e098aeb6-21fc-4e79-be4c-a61c3507982e"], ["vpc_ep_10_10_10_221", "ff32cdf4-b623-456d-90db-0a15c3593fce"], ["vpc_ep_10_10_10_216", "ea4e47c9-35e3-457d-a4cf-8fcffc8c2b08"], ["vpc_ep_10_10_10_214", "60e3e8ef-2c54-4d07-bf10-a51d1207436e"], ["vpc_ep_10_10_10_210", "843b4d21-7b37-462d-a21a-d93b6675ecb7"], ["vpc_ep_10_10_10_21", "760e5146-4a8d-45c0-a85d-c930926b9865"], ["vpc_ep_10_10_10_208", "e3f44635-e791-4a37-a2ef-e83923761ea8"], ["vpc_ep_10_10_10_204", "e4128efe-7242-4afc-aab6-f10469468ed3"], ["vpc_ep_10_10_10_202", "6b5182d3-023f-4f16-9615-4eda4d73f724"], ["vpc_ep_10_10_10_20", "48bc04cd-ca0e-43b6-94b8-07f010c33ab8"], ["vpc_ep_10_10_10_198", "d03f4bdc-0512-40bd-bfd1-019e962bbd22"], ["vpc_ep_10_10_10_191", "a771662c-7892-4d3f-bd63-91033c3932fc"], ["vpc_ep_10_10_10_19", "7087ecf8-6f93-41b3-b5e7-b5b30541a6a9"], ["vpc_ep_10_10_10_187", "4111cd08-0f4c-4293-916c-290f6712c70d"], ["vpc_ep_10_10_10_185", "c6fc6b09-75d4-4c2f-b619-0cbb975618a0"], ["vpc_ep_10_10_10_184", "3fa4d9d2-124f-48e5-841c-31b6d5cd63ce"], ["vpc_ep_10_10_10_180", "2ce85165-9151-4856-86fb-4483169fab06"], ["vpc_ep_10_10_10_18", "ff01d581-3bbc-424f-b683-687e1dd317f7"], ["vpc_ep_10_10_10_178", "150d7cf9-79d6-4964-8411-ec325934be87"], ["vpc_ep_10_10_10_175", "ad0f8abf-a4bc-4d24-afa8-ed9748bdd529"], ["vpc_ep_10_10_10_17", "cc02cb64-6d57-4105-b570-db256b459e84"], ["vpc_ep_10_10_10_169", "2062e999-e858-48aa-be10-c635f64bcc5d"], ["vpc_ep_10_10_10_167", "ad80e93b-17e5-43c0-967c-f299edfaacfe"], ["vpc_ep_10_10_10_165", "3b41ea7a-afa5-45d4-9bd1-18909e152917"], ["vpc_ep_10_10_10_163", "213ebd91-cc8f-4a61-bf33-90fa2aa72bdb"], ["vpc_ep_10_10_10_161", "c41598e5-b124-44d6-a00f-5e5e61ffb9b6"], ["vpc_ep_10_10_10_16", "7299ed68-e4bf-4e03-bf95-feda992efbbc"], ["vpc_ep_10_10_10_159", "09c86aa0-9f35-4e35-ad6e-10297b18fff6"], ["vpc_ep_10_10_10_158", "16de9ab1-2f50-4b5c-9e9c-02b558fed9a8"], ["vpc_ep_10_10_10_156", "18abaeed-30cf-4a95-be28-216afda83a73"], ["vpc_ep_10_10_10_153", "9a366328-2f80-4890-bc3f-a64d89bf5249"], ["vpc_ep_10_10_10_151", "544475f3-6116-41fa-bf4b-f906149656c8"], ["vpc_ep_10_10_10_150", "8f2cf1f4-a2d6-4f9b-9a99-0597db08dffc"], ["vpc_ep_10_10_10_144", "b4be3e5a-5f1d-41be-88cb-c88c5097fd52"], ["vpc_ep_10_10_10_143", "86ecf1ca-8bef-4f42-ac52-c278bfbac813"], ["vpc_ep_10_10_10_14", "d31dfd20-f2dc-47dd-b7fb-2d8f25625a2c"], ["vpc_ep_10_10_10_139", "95937602-e5b5-4a15-9b4e-ad797da148db"], ["vpc_ep_10_10_10_138", "f5f49551-1d5b-4fd2-958e-f3cb0aab9d2d"], ["vpc_ep_10_10_10_137", "e764cbde-af40-4d66-8424-63843f45d527"], ["vpc_ep_10_10_10_134", "b5635bd8-8da5-4a62-b5f2-32961b025720"], ["vpc_ep_10_10_10_133", "3008b82a-2f32-4180-b7d8-85f23034b20f"], ["vpc_ep_10_10_10_132", "a2293127-79d7-4eed-bde0-ab8335981bda"], ["vpc_ep_10_10_10_131", "f31a3596-e861-485d-9d2f-14f22d791b27"], ["vpc_ep_10_10_10_130", "71f95e3b-0620-42a7-8827-2bf7bdfb81c1"], ["vpc_ep_10_10_10_125", "930bc20d-b942-4788-9711-189e51d9a4c8"], ["vpc_ep_10_10_10_120", "43ee56a4-c7c2-4564-a127-85934f011424"], ["vpc_ep_10_10_10_12", "40cf3cf5-a8a2-4552-b757-4b845e4f306c"], ["vpc_ep_10_10_10_116", "18dbbb6a-082b-407e-a4eb-c7de036168d0"], ["vpc_ep_10_10_10_114", "f5ea9b8d-5680-46c8-b1d0-276317cf0a5f"], ["vpc_ep_10_10_10_113", "0f1be8d1-4e01-4735-802e-93404047062e"], ["vpc_ep_10_10_10_111", "36a72e8c-2e10-4f8c-af10-53fb1fe9e931"], ["vpc_ep_10_10_10_110", "3950fcf4-efde-473d-a5ff-252cfdfdd829"], ["vpc_ep_10_10_10_109", "f321370b-c65e-4999-9d41-1beb0a57e402"], ["vpc_ep_10_10_10_107", "5b63308c-d5ae-4784-b3ed-4d009728c1d3"], ["vpc_ep_10_10_10_103", "826033da-ae32-47ef-8976-387cdb6c92f8"], ["vpc_ep_10_10_10_102", "aa9e6493-1600-4242-afb6-50310ffcabc5"]]
eps = [["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"], ["stress_single_vm", "4da0cce5-94fa-9619-3b85-67a412a97bcf"]]
for i in range(5):
    cred_uuid = str(uuid.uuid4())
    # j = i*10
    task_list = []
    rb_pay['spec']['resources']['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'] = []
    for ep_name, ep_uuid in eps:
        task_copy = copy.deepcopy(task_pay)
        task_copy['uuid'] = str(uuid.uuid4())
        task_copy['name'] = 'task_' + ep_name + task_copy['uuid'][:8]
        task_copy['attrs']['login_credential_local_reference']['uuid'] = cred_uuid
        task_copy['target_any_local_reference']['name'] = ep_name
        task_copy['target_any_local_reference']['uuid'] = ep_uuid
        task_list.append(task_copy)
    rb_pay['spec']['resources']['runbook']['task_definition_list'][1:] = task_list
    main_task_uuid = str(uuid.uuid4())
    rb_pay['spec']['resources']['credential_definition_list'][0]['uuid'] = cred_uuid
    rb_pay['spec']['resources']['runbook']['task_definition_list'][0]['uuid'] = main_task_uuid
    rb_pay['spec']['resources']['runbook']['main_task_local_reference']['uuid'] = main_task_uuid
    for r in rb_pay['spec']['resources']['runbook']['task_definition_list'][1:]:
        rb_pay['spec']['resources']['runbook']['task_definition_list'][0]['child_tasks_local_reference_list'].append({
                                "kind": "app_task",
                                "uuid": r['uuid']
                            })
    rb_pay['spec']['resources']['runbook']['uuid'] = str(uuid.uuid4())
    rb_pay['metadata']['uuid'] = str(uuid.uuid4())
    rb_pay['spec']['name'] = "stress_single_vm_10ep_" + str(i)
    resp = client.post(URL + 'runbooks', data=json.dumps(rb_pay))
    response = json.loads(resp.content)
    if resp.status_code != 200:
        print(json.dumps(response))
        print(resp.status_code)
        continue
    print(f"Runbook [{response['spec']['name']}] created sucessfully.")
    time.sleep(2)
