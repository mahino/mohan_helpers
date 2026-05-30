from datetime import datetime
import time
import requests
import json
import threading
import urllib3
import warnings

# Disable SSL warnings
urllib3.disable_warnings()
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Configuration for TCO uploads
TCO_MAX_UPLOADS = 1000
TCO_UPLOADS_PER_MINUTE = 2
TCO_SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE = 60
TCO_RATE_LIMIT_SLEEP = 120

# Configuration for CC uploads
CC_MAX_UPLOADS = 1000
CC_UPLOADS_PER_MINUTE = 2
CC_SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE = 60
CC_RATE_LIMIT_SLEEP = 120

# Common headers
HEADERS_AUTH = {
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
    'Cookie': 'NTNX_CENTRAL_SESSION=FD6JYFOAD3PDB5Q6KBC6FWAZNWXA4RYYEDH6HU3JEERBFMAOPXIUYZRUX4LZPT4PEYUE7OJ3YBBLWMJI67ZZXI332NHLBGJQ74V4F7Q'
}


def upload_tco():
    """Upload a single TCO"""
    try:
        url = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/config/tco/purchases"
        payload = {}
        files = [
            ('file', ('Nutanix_TCO_Direct_Cost_Nutanix_Cost_Configuration_04-11-2025_16_40.xls',
                     open('/home/mohan.as/mohan_helpers/Nutanix_TCO_Direct_Cost_Nutanix_Cost_Configuration_04-11-2025_16_40.xls', 'rb'),
                     'application/vnd.ms-excel'))
        ]
        headers = HEADERS_AUTH.copy()
        
        response = requests.request("POST", url, headers=headers, data=payload, files=files, verify=False)
        if response.status_code == 200:
            response_data = json.loads(response.content)
            purchase = response_data['purchases']
            payload = json.dumps({
                "purchases": purchase
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': HEADERS_AUTH['Authorization'],
                'Cookie': HEADERS_AUTH['Cookie']
            }
            response = requests.request("PUT", url, headers=headers, data=payload, verify=False)
            return response
        else:
            return response
    except requests.exceptions.RequestException as e:
        print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed: {e}")
        return None


def upload_cc():
    """Upload a single CC"""
    try:
        payload = {}
        files = [
            ('file', ('1762250593474_CHARGEBACK_RESOURCES_BY_ACCOUNT_2025-11-04_10_03_08.csv',
                     open('/home/mohan.as/mohan_helpers/1762250593474_CHARGEBACK_RESOURCES_BY_ACCOUNT_2025-11-04_10_03_08.csv', 'rb'),
                     'text/csv'))
        ]
        headers = HEADERS_AUTH.copy()
        
        url = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/global/chargeback/uploadConfiguration"
        response = requests.request("POST", url, headers=headers, data=payload, files=files, verify=False)
        
        if response.status_code == 200:
            url = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/global/chargeback/getAllUploadConfig"
            count = 0
            while count < 10:
                resp = requests.request("GET", url, headers=headers, verify=False)
                count += 1
                
                resp = json.loads(resp.content)
                if resp[-1]['status'] == 'SUCCESS':
                    print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Upload successful, status: {resp[-1]['status']}")
                    break
                print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Latest upload record status: {resp[-1]['status']}")
                time.sleep(5)
            return response
        else:
            print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Upload failed with status {response.status_code}: {response.text}...")
            return response
    except requests.exceptions.RequestException as e:
        print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed: {e}")
        return None


def run_tco_uploads():
    """Run TCO uploads in a loop"""
    upload_count = 0
    sleep_count = 0
    start_time = datetime.now()
    
    print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting TCO uploads thread...")
    
    while upload_count < TCO_MAX_UPLOADS:
        if upload_count % TCO_UPLOADS_PER_MINUTE == 0:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {TCO_SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE} seconds after every {TCO_UPLOADS_PER_MINUTE} TCO uploads...")
            time.sleep(TCO_SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE)
        
        response = upload_tco()
        if response is None:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed, retrying in 1 second...")
            time.sleep(1)
            continue

        if response.status_code == 429:
            sleep_count += 1
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rate limited (429). Sleeping for {TCO_RATE_LIMIT_SLEEP}s. "
                  f"Sleep count: {sleep_count}, Uploaded: {upload_count}")
            time.sleep(TCO_RATE_LIMIT_SLEEP)
            
        elif response.status_code == 200:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ TCO {upload_count}/{TCO_MAX_UPLOADS} successfully uploaded, response: {response.text}")
            upload_count += 1
            sleep_count = 0
            time.sleep(0.5)
        else:
            print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Upload failed with status {response.status_code}: {response.text}...")
            time.sleep(1)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"[TCO][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Completed {upload_count} TCO uploads in {duration}")


def run_cc_uploads():
    """Run CC uploads in a loop"""
    upload_count = 0
    sleep_count = 0
    start_time = datetime.now()
    
    print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting CC uploads thread...")
    
    while upload_count < CC_MAX_UPLOADS:
        if upload_count % CC_UPLOADS_PER_MINUTE == 0:
            print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {CC_SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE} seconds after every {CC_UPLOADS_PER_MINUTE} CC uploads...")
            time.sleep(CC_SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE)
        
        response = upload_cc()
        if response is None:
            print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed, retrying in 1 second...")
            time.sleep(1)
            continue

        if response.status_code == 429:
            sleep_count += 1
            print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rate limited (429). Sleeping for {CC_RATE_LIMIT_SLEEP}s. "
                  f"Sleep count: {sleep_count}, Uploaded: {upload_count}")
            time.sleep(CC_RATE_LIMIT_SLEEP)
            
        elif response.status_code == 200:
            print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ CC {upload_count}/{CC_MAX_UPLOADS} successfully uploaded, response: {response.text}")
            upload_count += 1
            sleep_count = 0
            time.sleep(0.5)
        else:
            print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Upload failed with status {response.status_code}: {response.text}...")
            time.sleep(1)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"[CC][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Completed {upload_count} CC uploads in {duration}")


if __name__ == "__main__":
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting parallel uploads...")
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TCO: {TCO_MAX_UPLOADS} uploads, {TCO_UPLOADS_PER_MINUTE} per minute")
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CC: {CC_MAX_UPLOADS} uploads, {CC_UPLOADS_PER_MINUTE} per minute")
    print("-" * 80)
    
    # Create threads for both upload processes
    tco_thread = threading.Thread(target=run_tco_uploads, name="TCO-Thread")
    cc_thread = threading.Thread(target=run_cc_uploads, name="CC-Thread")
    
    # Start both threads
    tco_thread.start()
    cc_thread.start()
    
    # Wait for both threads to complete
    tco_thread.join()
    cc_thread.join()
    
    print("-" * 80)
    print(f"[MAIN][{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All uploads completed!")

