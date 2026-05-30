"""
Copyright (c) 2017 Nutanix Inc. All rights reserved.
Author: ram.daga@nutanix.com
"""

V0 = "api/nutanix/v0.8/"
V1 = "PrismGateway/services/rest/v1/"
V2 = "PrismGateway/services/rest/v2.0/"
V3 = "api/nutanix/v3/"
LOGIN = "admin"
PWD = "Nutanix.123"
SSPADMINLOGIN = "sspadmin@perf-ssp.com"
SSPADMINPWD = "nutanix/4u"
SSPDEVUSER1 = "user1@perf-ssp.com"
SSPDEVUSER2 = "user2@perf-ssp.com"
SSPDEVUSER3 = "user3@perf-ssp.com"
SSPDEVUSER4 = "user4@perf-ssp.com"
ADUSERPWD = "nutanix/4u"
VMS_URL = "api/nutanix/v3/vms"

VMBULKCOUNT = 2
TIMEOUT = 180
# Update PES_LIST_CSV with a csv string of clusters like "cool05,sabine17"
PES_LIST_CSV = "babysean01,cool07,cool08,ehonda02"

# Specify the disk details for the clusters in PES_LIST_CSV. For FIO workload,
# we need to clone the FIO disk and allocate storage on container. FIO image
# should be present on the respective PE. We will need the vmdisk_uuid for
# FIO image and storage_container_uuid for storage allocation
VMDISKCLONE = {"cool07": "154195e9-3949-4fc1-9251-b13ddb6b186a",
               "ehonda02": "1a754d61-f3cd-40c2-b15d-5b7c5272191f",
               "watermelon02": "83073ddb-13e2-446e-893e-184fdac5c184",
               "babysean01": "7533fa17-b958-4216-abf6-0da494a61c34",
               "cool06": "85fad81f-e078-422a-8eb9-5494fa7afc19",
               "cool08": "88db517d-4185-45fb-b111-5c8869a41dd1"}

VMDISKCREATE = {"cool07": "d35b1ba5-b49f-40f7-bb00-69773249b0d2",
                "ehonda02": "d686b319-715e-4411-a037-ca815ada2933",
                "babysean01": "11f3ce66-bb4a-4c33-949f-635feb44dcbc",
                "watermelon02": "c1de7427-4abc-47c9-bb7c-f147c35a1929",
                "cool06": "bbafae0d-c6ab-447e-bf9c-a20c42de76a9",
                "cool08": "11be31d1-be4d-4048-9b31-3797c95d7eaa"}

# Specify the network details for the clusters in PES_LIST_CSV
VMNICINFO = {"cool07": "67ef5572-9928-41b6-a86c-7154343430c3",
             "ehonda02": "ea3af7b8-b025-417d-9332-81883109639a",
             "cool06": "a98dee0f-ea0d-4a80-ad75-8cda82779f00",
             "babysean01": "bdb280e9-6c35-4614-8157-e0c6bb806af7",
             "watermelon02": "49f4a24d-60bd-4d1e-9b4c-2841fdcbca2f",
             "cool08": "74414943-3f65-4ff6-ac5c-3957cc7d7814",
             "WINDU1215": "95bd191a-2229-4cfa-ad28-452c438e826e"}

CLUSTERINFO = {"WINDU1215": "00056818-8458-2700-2109-0cc47ac579e6"}

SBTSKTRUE = V1 + "progress_monitors?hasSubTaskDetail=true&count=500&page=1&" \
       "filterCriteria=(status%3D%3DkRunning%2Ccomplete_time_usecs%3Dgt%3D"

SBTSKFLSE = V1 + \
            "progress_monitors?hasSubTaskDetail=false&count=500&page=1&" \
            "filterCriteria=component!%3Daplos%3Binternal_task%3D%3Dfalse%3B" \
            "display_failures!%3Dfalse%3B(status%3D%3DkRunning%2C" \
            "complete_time_usecs%3Dgt%3D"

OLDPRGTRUE = V1 + \
             "progress_monitors?oldProgressOnly=true&" \
             "proxyClusterUuid=all_clusters&count=500&page=1&" \
             "filterCriteria=component!%3Daplos%3Binternal_task%3D%3Dfalse%3B" \
             "display_failures!%3Dfalse%3B(status%3D%3DkRunning%2C" \
             "complete_time_usecs%3Dgt%3D"

