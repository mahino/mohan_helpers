#!/usr/bin/env python3
"""
NCM Reports Downloader - Parallel TCO and UDM downloads
Downloads TCO and UDM reports simultaneously using threading
"""
import requests
import json
import time
import os
import urllib3
import threading
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration for TCO downloads
TCO_REPORTS_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/config/tco/purchases"
TCO_MAX_DOWNLOADS = 50000
TCO_RATE_LIMIT_SLEEP = 60
TCO_DOWNLOADS_PER_MINUTE = 50000
TCO_SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE = 60

# Configuration for UDM downloads
UDM_REPORTS_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/config/rate-cards/actions/download?cloud=Nutanix"
UDM_MAX_DOWNLOADS = 50000
UDM_RATE_LIMIT_SLEEP = 60
UDM_DOWNLOADS_PER_MINUTE = 50000
UDM_SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE = 60

# Create reports directory
os.makedirs("reports", exist_ok=True)

# Create session for TCO
tco_client = requests.Session()
tco_client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
tco_client.headers = {'content-type': 'application/json'}
tco_client.verify = False

# Create session for UDM
udm_client = requests.Session()
udm_client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
udm_client.headers = {'content-type': 'application/json'}
udm_client.verify = False


def download_tco_report():
    """Download a single TCO report"""
    try:
        response = tco_client.get(TCO_REPORTS_URL, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed: {e}")
        return None


def download_udm_report():
    """Download a single UDM report"""
    try:
        response = udm_client.get(UDM_REPORTS_URL, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed: {e}")
        return None


def run_tco_downloads():
    """Run TCO downloads in a loop"""
    download_count = 0
    sleep_count = 0
    start_time = datetime.now()
    
    print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting TCO downloads thread...")
    
    while download_count < TCO_MAX_DOWNLOADS:
        if download_count % TCO_DOWNLOADS_PER_MINUTE == 0 and download_count > 0:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {TCO_SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE} seconds after every {TCO_DOWNLOADS_PER_MINUTE} TCO Report downloads...")
            time.sleep(TCO_SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
        
        response = download_tco_report()
        if response is None:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed, retrying in 1 second...")
            time.sleep(1)
            continue

        if response.status_code == 429:
            sleep_count += 1
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rate limited (429). Sleeping for {TCO_RATE_LIMIT_SLEEP}s. "
                  f"Sleep count: {sleep_count}, Downloaded: {download_count}")
            time.sleep(TCO_RATE_LIMIT_SLEEP)

        elif response.status_code == 202 or response.status_code == 200:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ TCO Report {download_count}/{TCO_MAX_DOWNLOADS} successfully downloaded")
            download_count += 1
            sleep_count = 0
            time.sleep(0.5)
        else:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Download failed with status {response.status_code}: {response.text}...")
            time.sleep(1)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Completed {download_count} TCO downloads in {duration}")


def run_udm_downloads():
    """Run UDM downloads in a loop"""
    download_count = 0
    sleep_count = 0
    start_time = datetime.now()
    
    print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting UDM downloads thread...")
    
    while download_count < UDM_MAX_DOWNLOADS:
        if download_count % UDM_DOWNLOADS_PER_MINUTE == 0 and download_count > 0:
            print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {UDM_SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE} seconds after every {UDM_DOWNLOADS_PER_MINUTE} UDM Report downloads...")
            time.sleep(UDM_SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
        
        response = download_udm_report()
        if response is None:
            print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed, retrying in 1 second...")
            time.sleep(1)
            continue

        if response.status_code == 429:
            sleep_count += 1
            print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rate limited (429). Sleeping for {UDM_RATE_LIMIT_SLEEP}s. "
                  f"Sleep count: {sleep_count}, Downloaded: {download_count}")
            time.sleep(UDM_RATE_LIMIT_SLEEP)

        elif response.status_code == 202 or response.status_code == 200:
            print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ UDM Report {download_count}/{UDM_MAX_DOWNLOADS} successfully downloaded")
            download_count += 1
            sleep_count = 0
            time.sleep(0.5)
        else:
            print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Download failed with status {response.status_code}: {response.text}...")
            time.sleep(1)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"[UDM][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Completed {download_count} UDM downloads in {duration}")


if __name__ == "__main__":
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting parallel downloads...")
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TCO: {TCO_MAX_DOWNLOADS} downloads, {TCO_DOWNLOADS_PER_MINUTE} per minute")
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] UDM: {UDM_MAX_DOWNLOADS} downloads, {UDM_DOWNLOADS_PER_MINUTE} per minute")
    print("-" * 80)
    
    # Create threads for both download processes
    tco_thread = threading.Thread(target=run_tco_downloads, name="TCO-Download-Thread")
    udm_thread = threading.Thread(target=run_udm_downloads, name="UDM-Download-Thread")
    
    # Start both threads
    tco_thread.start()
    udm_thread.start()
    
    # Wait for both threads to complete
    tco_thread.join()
    udm_thread.join()
    
    print("-" * 80)
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All downloads completed!")

