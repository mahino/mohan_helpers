#!/usr/bin/env python3
"""
NCM Reports Downloader using HTTP Basic Authentication
Similar to create_endpoints.py pattern
"""
import requests
import json
import time
import os
import urllib3
import sys
from datetime import datetime
import pytz
from requests.auth import HTTPBasicAuth

# Disable SSL warnings (like in create_endpoints.py)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize logging with timestamped filename
script_start_time = datetime.now()
log_filename = f"{script_start_time.strftime('%Y%m%d_%H%M%S')}_cc_reports_share_execution.log"
log_filepath = os.path.join("logs", log_filename)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Store original print function before overriding
original_print = print

# Custom print function that writes to both console and log file
def log_print(message):
    """Print to console and write to log file with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    
    # Print to console using original print
    original_print(log_message)
    
    # Write to log file
    with open(log_filepath, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')

# Log script start
log_print(f"Script execution started at {script_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
log_print(f"Log file: {log_filepath}")

# Override the built-in print function for this script
print = log_print

def get_ist_timestamp():
    """Get current timestamp in IST format"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')

# Configuration
NCM_BASE_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com"
REPORTS_URL = f"{NCM_BASE_URL}/v1/reports/share"

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

MAX_SHARE = 10000 
RATE_LIMIT_SLEEP = 600

os.makedirs("reports", exist_ok=True)

payload = json.dumps({
    "reportName": f"[{get_ist_timestamp()}]Business Units / Cost Centers Summary",
    "reportConfig": {
        "reportType": "GLOBAL_CHARGEBACK",
        "dataSource": {
            "resourceGroupIds": [],
            "category": "ALLOCATED",
            "resourceGroupType": "ALL_BU_CC",
            "filters": {},
            "groupBy": "businessUnitsAndCostCenters"
        },
        "reportPeriod": {
            "timeUnit": "CUSTOM"
        },
        "timeRange": {
            "startTime": 1759276800,
            "endTime": 1761955199
        },
        "reportTemplateDetails": {
            "fileType": "XLS"
        }
    },
    "shareConfig": {
        "mode": "EMAIL",
        "recipients": [
            "mohan.as1@nutanix.com",
            "as.mohan9999@gmail.com"
        ],
        "subject": "sacxzefwdsc" * 100
    }
})

def share_report():
    """Download a single report"""
    try:
        response = client.post(REPORTS_URL, data=payload, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        print(f"[{get_ist_timestamp()}] Request failed: {e}")
        return None

share_count = 0
sleep_count = 0
start_time = datetime.now()

while share_count < MAX_SHARE:
    if share_count%1 == 0:
        print(f"[{get_ist_timestamp()}] Sleeping for 60 seconds after every 1 shares...")
        time.sleep(60)
    response = share_report()

    if response is None:
        print(f"[{get_ist_timestamp()}] Request failed, retrying in 1 second...")
        time.sleep(1)
        continue

    if response.status_code == 429:
        sleep_count += 1
        print(f"[{get_ist_timestamp()}] Rate limited (429). Sleeping for {RATE_LIMIT_SLEEP}s. "
              f"Sleep count: {sleep_count}, Shared: {share_count}")
        time.sleep(RATE_LIMIT_SLEEP)
        
    elif response.status_code == 202:
        print(f"[{get_ist_timestamp()}] ✓ Report {share_count}/{MAX_SHARE} successfully shared, response: {response.text}")
        share_count += 1
        sleep_count = 0
        time.sleep(0.5)

    else:
        print(f"[{get_ist_timestamp()}] ✗ Share failed with status {response.status_code}: {response.text}...")
        time.sleep(1)

# Log script completion
script_end_time = datetime.now()
execution_duration = script_end_time - script_start_time
print(f"Script execution completed at {script_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total execution time: {execution_duration}")
print(f"Total reports shared: {share_count}")
print(f"Total rate limit sleeps: {sleep_count}")

