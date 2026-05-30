import requests
import json
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import urllib3
import time
import numpy as np

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
NUM_THREADS = 5
BASE_URL = "https://10.115.150.47:9440"
USERNAME = "admin"
PASSWORD = "Nutanix.123"

# Thread-local storage for session
thread_local = threading.local()

def get_session():
    """Get or create a session for the current thread"""
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
        thread_local.session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
        thread_local.session.headers = {'content-type': 'application/json'}
        thread_local.session.verify = False
    return thread_local.session

def fetch_app_groups(offset):
    """Fetch app groups for a given offset"""
    client = get_session()
    
    app_groups_payload = {
        "length": 100,
        "offset": offset,
        "sort": "created_on",
        "sort_order": "DESCENDING",
        "fields": [
            "app_name", "uuid", "categories", "project_name", "account_names",
            "substrate_types", "source_marketplace_name", "state", "environment",
            "marketplace_version", "vm_names", "owner", "app_url", "created_on",
            "updated_on", "protection_status", "failover_status"
        ],
        "filter": "app_family==Other_Apps;(source_marketplace_name!=NCM_APP;source_marketplace_name!=MST_APP;source_marketplace_name!=NC_APP;source_marketplace_name!=NDB_APP;source_marketplace_name!=DL_APP);state!=deleted;app_family==Other_Apps"
    }
    
    start_time = time.time()
    try:
        response = client.post(
            f"{BASE_URL}/api/calm/v3.0/groups",
            data=json.dumps(app_groups_payload),
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            error_msg = f"Status {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg += f": {error_data['message']}"
                elif 'error' in error_data:
                    error_msg += f": {error_data['error']}"
            except:
                error_msg += f": {response.text[:200]}"
            
            print(f"[Thread-{threading.current_thread().name}] ✗ Fetch apps failed at offset {offset} ({elapsed:.2f}s): {error_msg}")
            return offset, [], elapsed, error_msg
        
        response_data = response.json()
        
        # Extract UUIDs
        apps_uuid_list = []
        if 'group_results' in response_data and len(response_data['group_results']) > 0:
            for entity in response_data['group_results'][0].get('entity_results', []):
                apps_uuid_list.append(entity['uuid'])
        
        print(f"[Thread-{threading.current_thread().name}] ✓ Fetched {len(apps_uuid_list)} apps at offset {offset} ({elapsed:.2f}s)")
        return offset, apps_uuid_list, elapsed, None
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[Thread-{threading.current_thread().name}] ✗ Exception at offset {offset} ({elapsed:.2f}s): {error_msg}")
        return offset, [], elapsed, error_msg

def process_consumption(offset, apps_uuid_list):
    """Process consumption for a batch of app UUIDs"""
    if not apps_uuid_list:
        print(f"[Thread-{threading.current_thread().name}] ⚠ No apps to process at offset {offset}")
        return offset, False, 0, "No apps found"
    
    client = get_session()
    
    payload = json.dumps({
        "time_unit": "month",
        "filters": {
            "entity_ids": apps_uuid_list
        }
    })
    
    start_time = time.time()
    try:
        response = client.post(
            f"{BASE_URL}/api/nutanix/v3/apps/consumption_list",
            data=payload
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"[Thread-{threading.current_thread().name}] ✓ Processed offset {offset} ({len(apps_uuid_list)} apps) ({elapsed:.2f}s)")
            return offset, True, elapsed, None
        else:
            error_msg = f"Status {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg += f": {error_data['message']}"
                elif 'error' in error_data:
                    error_msg += f": {error_data['error']}"
                else:
                    error_msg += f": {json.dumps(error_data)}"
            except:
                error_msg += f": {response.text[:200]}"
            
            print(f"[Thread-{threading.current_thread().name}] ✗ Error at offset {offset} ({elapsed:.2f}s): {error_msg}")
            return offset, False, elapsed, error_msg
            
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[Thread-{threading.current_thread().name}] ✗ Exception processing offset {offset} ({elapsed:.2f}s): {error_msg}")
        return offset, False, elapsed, error_msg

def process_batch(offset):
    """Process a single batch: fetch apps and process consumption"""
    batch_start = time.time()
    
    # Step 1: Fetch app groups
    offset_val, apps_uuid_list, fetch_time, fetch_error = fetch_app_groups(offset)
    
    # Step 2: Process consumption if we have apps
    if apps_uuid_list:
        offset_val, success, process_time, process_error = process_consumption(offset_val, apps_uuid_list)
        total_time = time.time() - batch_start
        return {
            'offset': offset_val,
            'success': success,
            'fetch_time': fetch_time,
            'process_time': process_time,
            'total_time': total_time,
            'error': process_error,
            'app_count': len(apps_uuid_list)
        }
    else:
        total_time = time.time() - batch_start
        return {
            'offset': offset_val,
            'success': False,
            'fetch_time': fetch_time,
            'process_time': 0,
            'total_time': total_time,
            'error': fetch_error or "No apps found",
            'app_count': 0
        }

def main():
    print("="*80)
    print("App Consumption Processing (Multithreaded)")
    print(f"Threads: {NUM_THREADS}")
    print(f"Range: 0 to 800 (step 100)")
    print("="*80)
    
    # Generate all offsets
    offsets = list(range(0, 3000, 100))
    offsets.extend(list(range(0, 3000, 100)))
    offsets.extend(list(range(0, 3000, 100)))
    success_count = 0
    failed_count = 0
    total_fetch_time = 0
    total_process_time = 0
    total_apps = 0
    failed_batches = []
    all_response_times = []  # Track all API response times for percentiles
    
    start_time = time.time()
    
    # Process batches concurrently
    with ThreadPoolExecutor(max_workers=NUM_THREADS, thread_name_prefix="Worker") as executor:
        # Submit all tasks
        future_to_offset = {executor.submit(process_batch, offset): offset for offset in offsets}
        
        # Process completed tasks
        for future in as_completed(future_to_offset):
            offset = future_to_offset[future]
            try:
                result = future.result()
                
                if result['success']:
                    success_count += 1
                    total_apps += result['app_count']
                else:
                    failed_count += 1
                    failed_batches.append({
                        'offset': result['offset'],
                        'error': result['error'],
                        'time': result['total_time']
                    })
                
                total_fetch_time += result['fetch_time']
                total_process_time += result['process_time']
                
                # Track response times for percentile calculations
                all_response_times.append(result['fetch_time'] * 1000)  # Convert to ms
                all_response_times.append(result['process_time'] * 1000)  # Convert to ms
                
            except Exception as e:
                print(f"✗ Task for offset {offset} generated an exception: {type(e).__name__}: {str(e)}")
                failed_count += 1
                failed_batches.append({
                    'offset': offset,
                    'error': f"{type(e).__name__}: {str(e)}",
                    'time': 0
                })
    
    total_elapsed = time.time() - start_time
    
    # Calculate metrics
    total_requests = len(offsets) * 2  # Each batch has 2 API calls (fetch + process)
    requests_per_second = total_requests / total_elapsed if total_elapsed > 0 else 0
    avg_response_time = np.mean(all_response_times) if all_response_times else 0
    error_rate = (failed_count / len(offsets) * 100) if len(offsets) > 0 else 0
    
    # Calculate percentiles
    if all_response_times:
        p90 = np.percentile(all_response_times, 90)
        p95 = np.percentile(all_response_times, 95)
        p99 = np.percentile(all_response_times, 99)
    else:
        p90 = p95 = p99 = 0
    
    # Final statistics
    print("\n" + "="*80)
    print("PERFORMANCE METRICS")
    print("="*80)
    
    print(f"\n{'Request Statistics:':<30}")
    print(f"  {'Total requests sent:':<28} {total_requests}")
    print(f"  {'Requests/second:':<28} {requests_per_second:.2f}")
    print(f"  {'Total batches:':<28} {len(offsets)}")
    print(f"  {'Successful:':<28} {success_count}")
    print(f"  {'Failed:':<28} {failed_count}")
    print(f"  {'Total apps processed:':<28} {total_apps}")
    
    print(f"\n{'Response Time Metrics:':<30}")
    print(f"  {'Avg. response time:':<28} {avg_response_time:,.0f} ms")
    print(f"  {'P90:':<28} {p90:,.0f} ms")
    print(f"  {'P95:':<28} {p95:,.0f} ms")
    print(f"  {'P99:':<28} {p99:,.0f} ms")
    
    print(f"\n{'Error & Timing:':<30}")
    print(f"  {'Error rate:':<28} {error_rate:.2f} %")
    print(f"  {'Total elapsed time:':<28} {total_elapsed:.2f}s")
    print(f"  {'Avg fetch time:':<28} {total_fetch_time/len(offsets):.2f}s")
    print(f"  {'Avg process time:':<28} {total_process_time/success_count if success_count > 0 else 0:.2f}s")
    print(f"  {'Total API time:':<28} {total_fetch_time + total_process_time:.2f}s")
    
    if failed_batches:
        print(f"\n{'='*80}")
        print(f"FAILED BATCHES ({len(failed_batches)})")
        print("="*80)
        for fb in failed_batches:
            print(f"  Offset {fb['offset']:4d} ({fb['time']:.2f}s): {fb['error']}")
    
    print("="*80)

if __name__ == "__main__":
    main()