#!/usr/bin/env python3
"""
NCM Reports Share using HTTP Basic Authentication
Similar to create_endpoints.py pattern
"""
import requests
import json
import time
import os
import urllib3
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Disable SSL warnings (like in create_endpoints.py)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
REPORTS_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/reports/share"

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

MAX_SHARES = 1000
RATE_LIMIT_SLEEP = 60
SHARE_PER_MINUTE = 3

os.makedirs("reports", exist_ok=True)

payload = json.dumps({
    "reportName": "nx-cluster-daily-Sun Feb 01 2026 12:59:34 GMT+0530 (India Standard Time)",
    "reportConfig": {
        "reportType": "NX_RESOURCE_METERING",
        "reportPeriod": {
            "timeUnit": "CUSTOM"
        },
        "reportTemplateDetails": {
            "fileType": "XLS"
        },
        "dataSource": {
            "accountId": "6d915317-d32b-4093-a6fa-b225f59a7522",
            "clusterId": "00064002-1290-400a-0000-0000000193e1",
            "timeUnit": "month",
            "resourceGroupType": "NX_BILLING_ACCOUNT",
            "resourceGroupIds": [
                "6d915317-d32b-4093-a6fa-b225f59a7522"
            ]
        },
        "timeRange": {
            "usageStartTime": 1767225600,
            "usageEndTime": 1769903940
        }
    },
    "shareConfig": {
        "mode": "EMAIL",
        "recipients": [
            "mohan.as1@nutanix.com"
        ]
    }
})

def share_report():
    """Share a single report"""
    try:
        response = client.post(REPORTS_URL, data=payload, timeout=30, verify=False)
        return response
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed: {e}")
        return None

share_count = 0
sleep_count = 0
start_time = datetime.now()
count = 0
rate_limit_hit = False
while share_count < MAX_SHARES:
    
    if count%SHARE_PER_MINUTE == 0 and rate_limit_hit == False:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for 60 seconds after every {SHARE_PER_MINUTE} System Report shares...")
        time.sleep(60)
    response = share_report()
    rate_limit_hit = False
    if response is None:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] System Report Request failed, retrying in 1 second...")
        time.sleep(1)
        continue

    if response.status_code == 429:
        sleep_count += 1
        count = 0
        rate_limit_hit = True
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] System Report Rate limited (429). Sleeping for {RATE_LIMIT_SLEEP}s. "
              f"Sleep count: {sleep_count}, Shared: {share_count}")
        time.sleep(RATE_LIMIT_SLEEP)
        
    elif response.status_code == 202:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ System Report {share_count}/{MAX_SHARES} successfully shared, response: {response.text}")
        share_count += 1
        count += 1
        sleep_count = 0
        time.sleep(0.5)
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ System Report Share failed with status {response.status_code}: {response.text}...")
        time.sleep(1)

