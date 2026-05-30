import requests
import json
import random
import sys


lol = {
  "metadata": {
    "kind": "project",
    "uuid": "7ad3887e-0abe-442b-9b2f-8a3a33e19539",
    "owner_reference": {
      "kind": "user",
      "uuid": "00000000-0000-0000-0000-000000000000",
      "name": "admin"
    },
    "spec_version": 0,
    "categories": {},
    "categories_mapping": {},
    "project_reference": {
      "kind": "project",
      "name": "Nucalm_38in",
      "uuid": "7ad3887e-0abe-442b-9b2f-8a3a33e19539"
    }
  },
  "api_version": "3.1",
  "spec": {
    "access_control_policy_list": [
      {
        "acp": {
          "name": "nuCalmAcp-128c4006-cd01-442f-aaef-d752be5a90df",
          "description": "untitledAcp-7ca5ed5a-31cf-4b71-81d8-bbf9a46b50d1",
          "resources": {
            "role_reference": {
              "name": "Developer",
              "uuid": "d902dc55-a6d8-4d25-7e32-4bbc7b0c5a9f",
              "kind": "role"
            },
            "user_reference_list": [
              {
                "name": "sspuser1@systest.nutanix.com",
                "kind": "user",
                "uuid": "1fe4f328-6d03-5211-8125-081267f9615d"
              },
              {
                "name": "sspuser10@systest.nutanix.com",
                "kind": "user",
                "uuid": "ba158f55-7453-5fbc-9c21-ea5b971796e3"
              },
              {
                "name": "sspuser100@systest.nutanix.com",
                "kind": "user",
                "uuid": "fa2450d6-a7d6-5c13-85ab-288b527ca73c"
              },
              {
                "name": "sspuser1000@systest.nutanix.com",
                "kind": "user",
                "uuid": "fc137c2b-a384-5cf7-87a8-7343f123e820"
              },
              {
                "name": "sspuser10000@systest.nutanix.com",
                "kind": "user",
                "uuid": "d1ed625c-a3b9-563c-bf99-ccd73f0cdf7d"
              },
              {
                "name": "sspuser1000001@systest.nutanix.com",
                "kind": "user",
                "uuid": "d6e48c44-bcca-5d81-9291-712f7eaa4451"
              },
              {
                "name": "sspuser10001@systest.nutanix.com",
                "kind": "user",
                "uuid": "e2dc6fb9-0086-506e-a15d-40de30a9d6ca"
              },
              {
                "name": "sspuser10002@systest.nutanix.com",
                "kind": "user",
                "uuid": "6104bc5f-c45c-5797-a97f-a1c9871db7f1"
              },
              {
                "name": "sspuser10003@systest.nutanix.com",
                "kind": "user",
                "uuid": "719ec6cd-f14d-5633-818c-9e50d30f07f5"
              },
              {
                "name": "sspuser10004@systest.nutanix.com",
                "kind": "user",
                "uuid": "2fd320a9-e307-5994-92c5-85ee3bc5bf25"
              }
            ],
            "user_group_reference_list": [],
            "filter_list": {
              "context_list": [
                {
                  "entity_filter_expression_list": [
                    {
                      "left_hand_side": {
                        "entity_type": "ALL"
                      },
                      "operator": "IN",
                      "right_hand_side": {
                        "collection": "ALL"
                      }
                    }
                  ],
                  "scope_filter_expression_list": [
                    {
                      "left_hand_side": "PROJECT",
                      "operator": "IN",
                      "right_hand_side": {
                        "uuid_list": [
                          "7ad3887e-0abe-442b-9b2f-8a3a33e19539"
                        ]
                      }
                    }
                  ]
                },
                {
                  "entity_filter_expression_list": [
                    {
                      "operator": "IN",
                      "left_hand_side": {
                        "entity_type": "image"
                      },
                      "right_hand_side": {
                        "collection": "ALL"
                      }
                    },
                    {
                      "operator": "IN",
                      "left_hand_side": {
                        "entity_type": "marketplace_item"
                      },
                      "right_hand_side": {
                        "collection": "SELF_OWNED"
                      }
                    },
                    {
                      "operator": "IN",
                      "left_hand_side": {
                        "entity_type": "app_icon"
                      },
                      "right_hand_side": {
                        "collection": "ALL"
                      }
                    },
                    {
                      "operator": "IN",
                      "left_hand_side": {
                        "entity_type": "category"
                      },
                      "right_hand_side": {
                        "collection": "ALL"
                      }
                    },
                    {
                      "operator": "IN",
                      "left_hand_side": {
                        "entity_type": "app_task"
                      },
                      "right_hand_side": {
                        "collection": "SELF_OWNED"
                      }
                    },
                    {
                      "operator": "IN",
                      "left_hand_side": {
                        "entity_type": "app_variable"
                      },
                      "right_hand_side": {
                        "collection": "SELF_OWNED"
                      }
                    }
                  ]
                },
                {
                  "entity_filter_expression_list": [
                    {
                      "left_hand_side": {
                        "entity_type": "blueprint"
                      },
                      "operator": "IN",
                      "right_hand_side": {
                        "collection": "ALL"
                      }
                    },
                    {
                      "left_hand_side": {
                        "entity_type": "environment"
                      },
                      "operator": "IN",
                      "right_hand_side": {
                        "collection": "ALL"
                      }
                    }
                  ],
                  "scope_filter_expression_list": [
                    {
                      "left_hand_side": "PROJECT",
                      "operator": "IN",
                      "right_hand_side": {
                        "uuid_list": [
                          "7ad3887e-0abe-442b-9b2f-8a3a33e19539"
                        ]
                      }
                    }
                  ]
                }
              ]
            }
          }
        },
        "metadata": {
          "kind": "access_control_policy"
        },
        "operation": "ADD"
      }
    ],
    "project_detail": {
      "name": "Nucalm_38in",
      "resources": {
        "account_reference_list": [
          {
            "kind": "account",
            "uuid": "e6e7428d-1471-42f8-b192-bf38d40f7a2b"
          },
          {
            "kind": "account",
            "uuid": "266aae25-00e8-4eb1-babc-1f605add5ab4"
          },
          {
            "kind": "account",
            "uuid": "4ec8e950-5e33-4632-87aa-e98b5d4a44c7"
          },
          {
            "kind": "account",
            "uuid": "52f3f838-aae1-4832-9678-c40a744ed136"
          },
          {
            "kind": "account",
            "uuid": "71594615-a859-468e-ba0e-0142728209f5"
          }
        ],
        "user_reference_list": [
          {
            "name": "sspuser1@systest.nutanix.com",
            "kind": "user",
            "uuid": "1fe4f328-6d03-5211-8125-081267f9615d"
          },
          {
            "name": "sspuser10@systest.nutanix.com",
            "kind": "user",
            "uuid": "ba158f55-7453-5fbc-9c21-ea5b971796e3"
          },
          {
            "name": "sspuser100@systest.nutanix.com",
            "kind": "user",
            "uuid": "fa2450d6-a7d6-5c13-85ab-288b527ca73c"
          },
          {
            "name": "sspuser1000@systest.nutanix.com",
            "kind": "user",
            "uuid": "fc137c2b-a384-5cf7-87a8-7343f123e820"
          },
          {
            "name": "sspuser10000@systest.nutanix.com",
            "kind": "user",
            "uuid": "d1ed625c-a3b9-563c-bf99-ccd73f0cdf7d"
          },
          {
            "name": "sspuser1000001@systest.nutanix.com",
            "kind": "user",
            "uuid": "d6e48c44-bcca-5d81-9291-712f7eaa4451"
          },
          {
            "name": "sspuser10001@systest.nutanix.com",
            "kind": "user",
            "uuid": "e2dc6fb9-0086-506e-a15d-40de30a9d6ca"
          },
          {
            "name": "sspuser10002@systest.nutanix.com",
            "kind": "user",
            "uuid": "6104bc5f-c45c-5797-a97f-a1c9871db7f1"
          },
          {
            "name": "sspuser10003@systest.nutanix.com",
            "kind": "user",
            "uuid": "719ec6cd-f14d-5633-818c-9e50d30f07f5"
          },
          {
            "name": "sspuser10004@systest.nutanix.com",
            "kind": "user",
            "uuid": "2fd320a9-e307-5994-92c5-85ee3bc5bf25"
          }
        ],
        "external_user_group_reference_list": [],
        "external_network_list": [],
        "enable_directory_and_identity_provider_shortlist": false,
        "subnet_reference_list": [
          {
            "kind": "subnet",
            "name": "vlan.114",
            "uuid": "f9b8781c-77df-44c6-880a-c4e20d0dec9c"
          },
          {
            "kind": "subnet",
            "name": "calm_st_1",
            "uuid": "ed2a4445-30e0-4018-91de-f65bfbb46191"
          },
          {
            "kind": "subnet",
            "name": "calm_st_2",
            "uuid": "6149b765-7b11-4345-8a68-13d525c53280"
          },
          {
            "kind": "subnet",
            "name": "calm_st_3",
            "uuid": "5522c730-58aa-4b7a-8927-e1f7e7dd3a49"
          },
          {
            "kind": "subnet",
            "name": "calm_st_4",
            "uuid": "fd281b60-7314-40eb-bc58-c3a4371f40df"
          },
          {
            "kind": "subnet",
            "name": "calm_st_5",
            "uuid": "ce821050-c78e-42be-9096-4116eb368cae"
          },
          {
            "kind": "subnet",
            "name": "calm_st_6",
            "uuid": "4e24a1e3-23a2-4fce-9c58-c32e9f22b38d"
          },
          {
            "kind": "subnet",
            "name": "calm_st_7",
            "uuid": "5cffc5fc-d1a4-4029-bd31-cf55b8877e77"
          },
          {
            "kind": "subnet",
            "name": "calm_st_8",
            "uuid": "2c5363f3-34a3-4fa5-b975-7d7af40b978a"
          },
          {
            "kind": "subnet",
            "name": "calm_st_9",
            "uuid": "1828e713-bf2e-42cd-ae0b-a9525640395f"
          },
          {
            "kind": "subnet",
            "name": "calm_st_10",
            "uuid": "291009a2-ff3a-48c4-86b7-e2438382c19e"
          },
          {
            "kind": "subnet",
            "name": "calm_st_11",
            "uuid": "1587c1b4-23cf-4370-95e7-9aa9daa1f3ee"
          },
          {
            "kind": "subnet",
            "name": "calm_st_12",
            "uuid": "93b9184a-d0b2-4b79-8a9f-48bcf02e409f"
          },
          {
            "kind": "subnet",
            "name": "calm_st_13",
            "uuid": "b419ad3f-80fe-4e4a-ac8f-7f44f9118957"
          },
          {
            "kind": "subnet",
            "name": "calm_st_14",
            "uuid": "5ee09abf-9f22-44d4-b5a5-390cf8511515"
          },
          {
            "kind": "subnet",
            "name": "calm_st_15",
            "uuid": "ad27a1bf-2b71-4dcc-ac9d-c22953c1a950"
          },
          {
            "kind": "subnet",
            "name": "calm_st_16",
            "uuid": "a3f9edc8-3399-4e13-a793-8fb4ecf9c2a1"
          },
          {
            "kind": "subnet",
            "name": "calm_st_17",
            "uuid": "39f03a3a-b3ec-4015-a95b-1a9388e9d10d"
          },
          {
            "kind": "subnet",
            "name": "calm_st_18",
            "uuid": "10b1316e-649c-4207-bb56-60967a156f31"
          },
          {
            "kind": "subnet",
            "name": "calm_st_19",
            "uuid": "b022317b-8834-432b-bbe0-3289f7de2ede"
          },
          {
            "kind": "subnet",
            "name": "calm_st_20",
            "uuid": "62e7bcd1-1f4c-4187-a96f-ae5b6bae34cd"
          },
          {
            "kind": "subnet",
            "name": "calm_st_21",
            "uuid": "8585b91f-da21-4bad-bfd9-debbe1d4e8d2"
          },
          {
            "kind": "subnet",
            "name": "calm_st_22",
            "uuid": "9fae4074-76fe-496f-a53e-50ddb1b6d7a1"
          },
          {
            "kind": "subnet",
            "name": "calm_st_23",
            "uuid": "31e25533-a70d-4ebd-8f56-202cbc61c88f"
          },
          {
            "kind": "subnet",
            "name": "calm_st_24",
            "uuid": "b3462e5a-9d53-44a6-8908-85d03ee74e45"
          },
          {
            "kind": "subnet",
            "name": "calm_st_25",
            "uuid": "6c1a8cc9-1b51-4700-a215-d8344819ac80"
          },
          {
            "kind": "subnet",
            "name": "calm_st_26",
            "uuid": "272b1d13-6a5f-4904-8d9d-3f8ff17b2816"
          },
          {
            "kind": "subnet",
            "name": "calm_st_27",
            "uuid": "9566cd49-1b63-4b37-a79c-3e66cd2be221"
          },
          {
            "kind": "subnet",
            "name": "calm_st_28",
            "uuid": "5b45468f-1efc-4c1e-91bd-fbf9cc46602f"
          },
          {
            "kind": "subnet",
            "name": "calm_st_29",
            "uuid": "cf425585-062b-4536-bcb8-0170c71973fd"
          },
          {
            "kind": "subnet",
            "name": "calm_st_30",
            "uuid": "42901280-478e-41a5-8d85-6290d3f9f5f1"
          },
          {
            "kind": "subnet",
            "name": "calm_st_31",
            "uuid": "36132bdd-2163-4ade-b300-3523e5d7ee9e"
          },
          {
            "kind": "subnet",
            "name": "calm_st_32",
            "uuid": "239f87c9-84c6-47f7-b7a9-911a6200d847"
          },
          {
            "kind": "subnet",
            "name": "calm_st_33",
            "uuid": "3079ce05-d02f-479b-ae0b-ff2ea86010a5"
          },
          {
            "kind": "subnet",
            "name": "calm_st_34",
            "uuid": "ed269048-0d1e-4c2d-a55e-3d29cb1f7118"
          },
          {
            "kind": "subnet",
            "name": "calm_st_35",
            "uuid": "a74c4ad9-346c-4953-bb21-f4e4964ee33d"
          },
          {
            "kind": "subnet",
            "name": "calm_st_36",
            "uuid": "b77d7dbb-2142-47b7-8391-1d52464fa40f"
          },
          {
            "kind": "subnet",
            "name": "calm_st_37",
            "uuid": "d63f72f0-8c71-4e99-8bd6-740c13244f13"
          },
          {
            "kind": "subnet",
            "name": "calm_st_38",
            "uuid": "848a5343-6e0c-4e01-a5f0-a77dc9d2472d"
          },
          {
            "kind": "subnet",
            "name": "calm_st_39",
            "uuid": "41d32765-87a7-4dd0-93bd-ebb8b7a7cb83"
          },
          {
            "kind": "subnet",
            "name": "calm_st_40",
            "uuid": "5d3f2449-ac59-46da-8477-50596e358aea"
          },
          {
            "kind": "subnet",
            "name": "calm_st_41",
            "uuid": "7bbca613-4d39-47af-8476-8370c8310472"
          },
          {
            "kind": "subnet",
            "name": "calm_st_42",
            "uuid": "3ca34f58-3c8f-4587-9357-db73751afca1"
          },
          {
            "kind": "subnet",
            "name": "calm_st_43",
            "uuid": "bb7a1981-2550-4c58-816d-961133e958de"
          },
          {
            "kind": "subnet",
            "name": "calm_st_44",
            "uuid": "08d2230a-4d80-44e5-a4a7-09762a3cd701"
          },
          {
            "kind": "subnet",
            "name": "calm_st_45",
            "uuid": "5d996ea8-e7f0-497a-a884-6533b1342b8d"
          },
          {
            "kind": "subnet",
            "name": "calm_st_46",
            "uuid": "3e94fa39-f69b-4494-9887-7dd1fd8263f3"
          },
          {
            "kind": "subnet",
            "name": "calm_st_47",
            "uuid": "35f9355f-5a55-4c72-aa16-0b480ecce272"
          },
          {
            "kind": "subnet",
            "name": "calm_st_48",
            "uuid": "839e71c4-e2a8-41ee-87ab-a9576347db0d"
          },
          {
            "kind": "subnet",
            "name": "calm_st_49",
            "uuid": "33f2b798-d0ba-45bd-83ac-064712b8e8a7"
          }
        ],
        "default_subnet_reference": {
          "kind": "subnet",
          "uuid": "f9b8781c-77df-44c6-880a-c4e20d0dec9c"
        },
        "tunnel_reference_list": [],
        "environment_reference_list": []
      }
    },
    "user_list": [],
    "user_group_list": []
  }
}

url = "https://10.36.199.14:9440/api/nutanix/v3/projects_internal/7ad3887e-0abe-442b-9b2f-8a3a33e19539"
for i in range(11,100):
  payload = json.dumps(lol)
  headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
    'Cookie': 'NTNX_IAM_SESSION=eyJhbGciOiJSUzI1NiIsImtpZCI6IjNkNWRkZTNmMzNjNDc1ZTdiM2E3YjE2ZTI1OWUwNTgwM2U3YzE1MTkifQ.eyJpc3MiOiJodHRwczovLzEwLjM2LjE5OS4yMTo5NDQwL2FwaS9pYW0vYXV0aG4iLCJzdWIiOiJhZG1pbiIsInN1Yl90eXBlIjoibG9jYWwiLCJhdWQiOiJkYzE2ZTgyMy0yZmIxLTViNTktODJlZi0yYmZhODQ0YjlkODgiLCJleHAiOjE3MDA4OTAwMjAsImlhdCI6MTcwMDg4OTEyMCwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm5hbWUiOiJhZG1pbiIsInVzZXJfdXVpZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsImNvbm5lY3Rvcl91dWlkIjoiMzdmMzAxMzUtNDU1Yi01ZWJkLTk5NWYtYjQ3ZTgxN2E1OWYyIiwidGVuYW50Ijp7InV1aWQiOiI1OWQ1ZGU3OC1hOTY0LTU3NDYtOGM2ZS02NzdjNGM3YTc5ZGYiLCJuYW1lIjoiaWFtdjJpbmZyYSJ9LCJsZWdhY3lfcm9sZXMiOlsiUk9MRV9DTFVTVEVSX0FETUlOIiwiUk9MRV9DTFVTVEVSX1ZJRVdFUiIsIlJPTEVfVVNFUl9BRE1JTiJdLCJ1c2VyX3Byb2ZpbGUiOiJ7XCJ1c2VybmFtZVwiOlwiYWRtaW5cIixcImRvbWFpblwiOlwiXCIsXCJsZWdhY3lfYWRtaW5fYXV0aG9yaXRpZXNcIjpbXCJST0xFX0NMVVNURVJfQURNSU5cIixcIlJPTEVfQ0xVU1RFUl9WSUVXRVJcIixcIlJPTEVfVVNFUl9BRE1JTlwiXSxcImF1dGhlbnRpY2F0ZWRcIjp0cnVlLFwidXNlcnR5cGVcIjpcImxvY2FsXCIsXCJhdXRoX2luZm9cIjp7XCJ1c2VybmFtZVwiOlwiYWRtaW5cIixcInVzZXJfdXVpZFwiOlwiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwXCIsXCJ1c2VyX2dyb3VwX3V1aWRzXCI6W10sXCJ0ZW5hbnRfdXVpZFwiOlwiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwXCIsXCJ0b2tlbl9hdWRpZW5jZVwiOlwiXCIsXCJ0b2tlbl9pc3N1ZXJcIjpcIlwiLFwicmVtb3RlX2F1dGhvcml6YXRpb25cIjpcIlwiLFwicmVtb3RlX2F1dGhfanNvblwiOlwiXCJ9fSIsImxlZ2FjeV90ZW5hbnRfaWQiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDAifQ.b7HrrEGiAZcO8Wb6w0oR-fiGi1leUD8Us8EvFmfDSgN8XzVjLSBfLmo7KKH1IKfhv8j1LAhAaokDDA__89k28rQRdu1X0bTdDKQh6xPrW65kHwzJMNDaexk6BluG2mmmRfnDiAlGHyHknEiQMF44AlegwwQuxawKo8B6UW4j9XtzScU162c3IeAGYs_mgh3UK28KELnUKlMexbCFSLZZY-uDKc4pvld_FYRoW_er6RsHAweDZ6lCM9X5bVIvPxvbQuqj31oaFjxZVgI-PwIX1o1gDuwiHDRGoou18g2YjrnmQzBDtMK8rpW-bHElMg0G78VUzkM2D6HNhC_oSrWHHw; NTNX_MERCURY_IAM_REFRESH_TOKEN=ChloZHZtdHN5cGZkanp5aW5yZWNzZnR2YnlmEhljc3huZ2E0Z2JqbWVlbGJ6cTJ1Z2RiajM3; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCki4arBhoHTWVyY3VyeSAAKigzZDVkZGUzZjMzYzQ3NWU3YjNhN2IxNmUyNTllMDU4MDNlN2MxNTE5|PgAHNLseq9x1sam01MPnwqmC93vB/bmZggMmKi+mXQo='
  }

  response = requests.request("PUT", url, headers=headers, data=payload, verify=False)
  print(i)