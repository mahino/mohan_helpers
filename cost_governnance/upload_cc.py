from datetime import datetime
import time
import requests
import json


MAX_UPLOADS = 1000
UPLOADS_PER_MINUTE = 2
SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE = 60
RATE_LIMIT_SLEEP = 120

upload_count = 0
sleep_count = 0
start_time = datetime.now()

def upload_cc():
    """Upload a single TCO"""
    try:
        payload = {}
        files=[
            ('file',('1762250593474_CHARGEBACK_RESOURCES_BY_ACCOUNT_2025-11-04_10_03_08.csv',open('/home/mohan.as/mohan_helpers/1762250593474_CHARGEBACK_RESOURCES_BY_ACCOUNT_2025-11-04_10_03_08.csv','rb'),'text/csv'))
        ]
        headers = {
            'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
            'Cookie': 'NTNX_CENTRAL_SESSION=FD6JYFOAD3PDB5Q6KBC6FWAZNWXA4RYYEDH6HU3JEERBFMAOPXIUYZRUX4LZPT4PEYUE7OJ3YBBLWMJI67ZZXI332NHLBGJQ74V4F7Q'
        }
        url = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/global/chargeback/uploadConfiguration"
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            url = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/global/chargeback/getAllUploadConfig"
            count = 0
            while count < 10:
                resp = requests.request("GET", url, headers=headers)
                count += 1
                
                resp = json.loads(resp.content)
                if resp[-1]['status'] == 'SUCCESS':
                    print("Upload successful, status: ", resp[-1]['status'])
                    break
                print("latest upload record status: ", resp[-1]['status'])
                time.sleep(5)
            return response
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Upload failed with status {response.status_code}: {response.text}...")
            return response
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed: {e}")
        return None

while upload_count < MAX_UPLOADS:
    if upload_count%UPLOADS_PER_MINUTE == 0 and upload_count > 0:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE} seconds after every {UPLOADS_PER_MINUTE} CC uploads...")
        time.sleep(SLEEP_AFTER_EVERY_UPLOADS_PER_MINUTE)
    response = upload_cc()
    if response is None:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Request failed, retrying in 1 second...")
        time.sleep(1)
        continue

    if response.status_code == 429:
        sleep_count += 1
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rate limited (429). Sleeping for {RATE_LIMIT_SLEEP}s. "
              f"Sleep count: {sleep_count}, Uploaded: {upload_count}")
        time.sleep(RATE_LIMIT_SLEEP)
        
    elif response.status_code == 200:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ TCO {upload_count}/{MAX_UPLOADS} successfully uploaded, response: {response.text}")
        upload_count += 1
        sleep_count = 0
        time.sleep(0.5) 
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Upload failed with status {response.status_code}: {response.text}...")
        time.sleep(1)