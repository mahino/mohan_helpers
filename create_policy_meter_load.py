#!/usr/bin/env python

import requests
import time
import uuid

true=True
false=False

i = 1

for i in range(i, 50):
        quota_uuid = str(uuid.uuid4())
        task = [{
    "uuid": quota_uuid,
    "entity_type": "VM",
    "resource_type": "disk",
    "value": 21474836480.000000,
    "state": "reserved",
    "tags": {
        "account": "ec1cadbb-e5fb-42fd-8bb7-8e49f3095273",
        "app": "4090a72d-654a-4b59-a114-2243171e97f6",
        "cluster": "0005aecc-16a4-bd62-0000-0000000085f5",
        "project": "97fedbf2-06a9-4906-b23f-65281e6d32d4",
        "runlog": "2ddf7773-860d-4a0e-8864-b5f898c5ee8e",
        "substrate_cfg": "d2f3b854-fbce-4559-98fd-86e17c46df1f"
    }
}]
        resp = requests.post('http://10.36.198.89:4211/reservations', auth=('admin', 'Nutanix.123'), json=task, verify=False)

        print resp.content
        i += 1
