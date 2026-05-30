#!/usr/bin/env python3
"""
NCM Reports Downloader using HTTP Basic Authentication
Similar to create_endpoints.py pattern
"""
import requests
import json
import time
import urllib3
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Disable SSL warnings (like in create_endpoints.py)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
TCOs_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/tco/configs?limit=1&offset=10&costHeadAction=direct"

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False



total_tcos = {"direct": {"total": 0, "total_HARDWARE": 0, "total_SOFTWARE": 0, "total_other": 0}, "indirect": {"total": 0, "total_FACILITIES": 0, "total_PEOPLE": 0, "total_SERVICES": 0, "total_TELECOM": 0, "total_other": 0}}
for tco_type in ["direct", "indirect"]:
    if tco_type == "direct":
        response = client.post(f"https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/tco/configs?limit=1&offset=0&costHeadAction=direct", data=json.dumps({"filters": []}))
    else:
        response = client.post(f"https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/tco/configs?limit=1&offset=0&costHeadAction=indirect", data=json.dumps({"filters": []}))
    tco_max_offset = json.loads(response.content)['totalCount']
    print(f"Total {tco_type} TCOs: {tco_max_offset}")
    for offset in range(0, tco_max_offset, 100):
        if tco_type == "direct":
            response = client.post(f"https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/tco/configs?limit=100&offset={offset}&costHeadAction=direct", data=json.dumps({"filters": []}))
        else:
            response = client.post(f"https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/tco/configs?limit=100&offset={offset}&costHeadAction=indirect", data=json.dumps({"filters": []}))
        response_data = json.loads(response.content)
        for tco in response_data['data']:
            if tco['resources'][0]['clusters'][0] in total_tcos[tco_type]:
                total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['count'] += 1
                if 'HARDWARE' == tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['HARDWARE'] += 1
                    total_tcos[tco_type]['total_HARDWARE'] += 1
                elif 'SOFTWARE' == tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['SOFTWARE'] += 1
                    total_tcos[tco_type]['total_SOFTWARE'] += 1
                elif 'FACILITIES' == tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['FACILITIES'] += 1
                    total_tcos[tco_type]['total_FACILITIES'] += 1
                elif 'PEOPLE' == tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['PEOPLE'] += 1
                    total_tcos[tco_type]['total_PEOPLE'] += 1
                elif 'SERVICES' == tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['SERVICES'] += 1
                    total_tcos[tco_type]['total_SERVICES'] += 1
                elif 'TELECOM' == tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['TELECOM'] += 1
                    total_tcos[tco_type]['total_TELECOM'] += 1
                else:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['other'] += 1
                    total_tcos[tco_type]['total_other'] += 1
            else:
                if tco_type == "direct":
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]] = {'count': 1, 'costHead': {'HARDWARE': 0, 'SOFTWARE': 0, 'other': 0}}
                else:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]] = {'count': 1, 'costHead': {'FACILITIES': 0, 'PEOPLE': 0, 'SERVICES': 0, 'TELECOM': 0, 'other': 0}}
                if 'HARDWARE' in tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['HARDWARE'] = 1
                    total_tcos[tco_type]['total_HARDWARE'] += 1
                elif 'SOFTWARE' in tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['SOFTWARE'] = 1
                    total_tcos[tco_type]['total_SOFTWARE'] += 1
                elif 'FACILITIES' in tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['FACILITIES'] = 1
                    total_tcos[tco_type]['total_FACILITIES'] += 1
                elif 'PEOPLE' in tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['PEOPLE'] = 1
                    total_tcos[tco_type]['total_PEOPLE'] += 1
                elif 'SERVICES' in tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['SERVICES'] = 1
                    total_tcos[tco_type]['total_SERVICES'] += 1
                elif 'TELECOM' in tco['costHead']:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['costHead']['TELECOM'] = 1
                    total_tcos[tco_type]['total_TELECOM'] += 1
                else:
                    total_tcos[tco_type][tco['resources'][0]['clusters'][0]]['other'] = 1
                    total_tcos[tco_type]['total_other'] += 1
            total_tcos[tco_type]['total'] += 1
        
print(json.dumps(total_tcos))