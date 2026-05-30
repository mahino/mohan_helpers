#!/usr/bin/env python3
"""
NCM Reports Downloader using HTTP Basic Authentication
With Status API polling functionality, parallel processing support, and logging

Supports two modes:
1. Sequential (default): Downloads one report at a time with rate limiting
2. Parallel (--parallel): Downloads in batches, waits for all to succeed before next batch
"""
import sys
import time
import os
import argparse
import urllib3
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger, LoggedRequests

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize logger
logger = get_logger(__file__)

# Initialize logged requests (will auto-print API metrics on exit)
requests = LoggedRequests(logger)

# Configuration
NCM_BASE_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com"
REPORTS_URL = f"{NCM_BASE_URL}/v1/reports/download"
STATUS_URL_TEMPLATE = f"{NCM_BASE_URL}/v1/reports/download/status?downloadId={{}}"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}

# Download settings
MAX_DOWNLOADS = 1000
RATE_LIMIT_SLEEP = 60
DOWNLOADS_PER_MINUTE = 3

# Status check settings
STATUS_CHECK_MAX_RETRIES = 20  # 20 * 10 seconds = ~3.3 minutes max wait
STATUS_CHECK_INTERVAL = 10    # 10 seconds between status checks
API_TIMEOUT = 300

# Parallel mode settings
PARALLEL_BATCH_SIZE = 3
PARALLEL_RETRY_SLEEP = 60  # Sleep before retrying failed batch
PARALLEL_MAX_RETRIES = 3   # Maximum retries per batch before giving up
SLEEP_AFTER_BATCH = 60     # Sleep after each successful batch

# Thread-safe lock for logging
log_lock = threading.Lock()

os.makedirs("reports", exist_ok=True)

PAYLOAD = {
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
            "startTime": 1769904000,
            "endTime": 1772323199
        },
        "reportTemplateDetails": {
            "fileType": "XLS"
        }
    }
}


def log(message, level="info"):
    """Thread-safe logging"""
    with log_lock:
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        elif level == "debug":
            logger.debug(message)


def download_report():
    """Download a single report - initiates the download and returns response with download ID"""
    try:
        response = requests.post(
            REPORTS_URL,
            json=PAYLOAD,
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=API_TIMEOUT
        )
        return response
    except Exception as e:
        log(f"Request failed: {e}", "error")
        return None


def check_status(download_id):
    """Check the status of a report download"""
    url = STATUS_URL_TEMPLATE.format(download_id)
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=API_TIMEOUT
        )
        return response
    except Exception as e:
        log(f"Status check failed for {download_id}: {e}", "error")
        return None


def wait_for_completion(download_id, report_num, total=None):
    """
    Poll the status API until the report is COMPLETED or FAILED.
    Returns (success, download_duration)
    """
    prefix = f"[{report_num}/{total}]" if total else f"[{report_num}]"
    download_start = time.time()
    
    for i in range(STATUS_CHECK_MAX_RETRIES):
        status_response = check_status(download_id)
        
        if status_response is None:
            log(f"{prefix} [STATUS {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Failed to get status", "warning")
            time.sleep(STATUS_CHECK_INTERVAL)
            continue
        
        try:
            status_json = status_response.json()
            status = status_json.get('status', 'UNKNOWN')
            
            if status == 'PROCESSING':
                log(f"{prefix} [STATUS {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Status: PROCESSING...", "debug")
                time.sleep(STATUS_CHECK_INTERVAL)
                continue
            elif status == 'COMPLETED':
                download_duration = time.time() - download_start
                log(f"{prefix} [STATUS {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] ✓ COMPLETED in {download_duration:.2f}s")
                return (True, download_duration)
            elif status == 'FAILED':
                log(f"{prefix} [STATUS {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] ✗ FAILED", "error")
                return (False, None)
            else:
                log(f"{prefix} [STATUS {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Unknown status: {status}", "warning")
                time.sleep(STATUS_CHECK_INTERVAL)
        
        except Exception as e:
            log(f"{prefix} [STATUS {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Failed to parse status: {e}", "error")
            time.sleep(STATUS_CHECK_INTERVAL)
    
    log(f"{prefix} [dowID:{download_id}] ✗ Timed out after {STATUS_CHECK_MAX_RETRIES * STATUS_CHECK_INTERVAL}s", "error")
    return (False, None)


def process_single_report(report_num, total=None):
    """
    Process a single report: initiate download and wait for completion.
    Returns (success, download_id, processing_time)
    """
    prefix = f"[{report_num}/{total}]" if total else f"[{report_num}]"
    start_time = time.time()
    
    # Initiate download
    response = download_report()
    
    if response is None:
        return (False, None, time.time() - start_time)
    
    if response.status_code == 429:
        log(f"{prefix} Rate limited (429)", "warning")
        return (False, "RATE_LIMITED", time.time() - start_time)
    
    if response.status_code not in [200, 202]:
        log(f"{prefix} ✗ Download failed with status {response.status_code}: {response.text}", "error")
        return (False, None, time.time() - start_time)
    
    # Get download ID from response
    try:
        response_json = response.json()
        download_id = response_json.get('id')
        log(f"{prefix} [dowID:{download_id}] Download initiated, waiting for completion...")
    except Exception as e:
        log(f"{prefix} Failed to parse response: {e}", "error")
        return (False, None, time.time() - start_time)
    
    # Wait for completion
    success, _ = wait_for_completion(download_id, report_num, total)
    processing_time = time.time() - start_time
    return (success, download_id, processing_time)


def run_sequential_mode():
    """Run downloads sequentially with rate limiting."""
    log("=" * 80)
    log("NCM SYSTEM REPORTS DOWNLOAD - SEQUENTIAL MODE")
    log("=" * 80)
    log(f"Target: {REPORTS_URL}")
    log(f"Max Downloads: {MAX_DOWNLOADS}")
    log(f"Rate Limit: {DOWNLOADS_PER_MINUTE} per minute")
    log("=" * 80)
    
    download_count = 0
    completed_count = 0
    failed_count = 0
    sleep_count = 0
    start_time = datetime.now()
    count = 0
    rate_limit_hit = False
    
    try:
        while download_count < MAX_DOWNLOADS:
            
            # Rate limiting - sleep after every N downloads
            if count % DOWNLOADS_PER_MINUTE == 0 and not rate_limit_hit and count > 0:
                log(f"Sleeping for 60 seconds after every {DOWNLOADS_PER_MINUTE} downloads...")
                time.sleep(60)
            
            download_count += 1
            rate_limit_hit = False
            
            # Process the report (initiate + wait for completion)
            success, download_id, _ = process_single_report(download_count, MAX_DOWNLOADS)
            
            if download_id == "RATE_LIMITED":
                sleep_count += 1
                count = 0
                rate_limit_hit = True
                download_count -= 1  # Retry this report
                log(f"Rate limited (429). Sleeping for {RATE_LIMIT_SLEEP}s. Sleep count: {sleep_count}, Completed: {completed_count}", "warning")
                time.sleep(RATE_LIMIT_SLEEP)
                continue
            
            if success:
                completed_count += 1
                count += 1
                sleep_count = 0
                log(f"✓ Report {download_count}/{MAX_DOWNLOADS} completed successfully")
            else:
                failed_count += 1
                log(f"✗ Report {download_count}/{MAX_DOWNLOADS} failed", "error")
            
            time.sleep(0.5)  # Small delay between requests
    
    except KeyboardInterrupt:
        log("")
        log("=" * 60)
        log("Script interrupted by user (Ctrl+C)")
        log("=" * 60)
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log("")
    log("=" * 80)
    log("FINAL SUMMARY - SEQUENTIAL MODE")
    log("=" * 80)
    log(f"Total Duration: {duration:.2f}s ({duration/60:.2f} minutes)")
    log(f"Total Initiated: {download_count}")
    log(f"✓ Completed: {completed_count}")
    log(f"✗ Failed: {failed_count}")
    log(f"Rate Limit Hits: {sleep_count}")
    log("=" * 80)


def run_parallel_mode():
    """Run downloads in parallel batches."""
    log("=" * 80)
    log("NCM SYSTEM REPORTS DOWNLOAD - PARALLEL MODE")
    log("=" * 80)
    log(f"Target: {REPORTS_URL}")
    log(f"Max Downloads: {MAX_DOWNLOADS}")
    log(f"Batch Size: {PARALLEL_BATCH_SIZE}")
    log(f"Max Retries per Batch: {PARALLEL_MAX_RETRIES}")
    log(f"Sleep after Batch: {SLEEP_AFTER_BATCH}s")
    log("=" * 80)
    
    start_time = datetime.now()
    completed_count = 0
    failed_count = 0
    batch_count = 0
    batch_retries = 0
    rate_limit_hits = 0
    
    # Create all tasks
    all_tasks = list(range(1, MAX_DOWNLOADS + 1))
    total_tasks = len(all_tasks)
    
    try:
        # Process in batches
        for batch_start in range(0, total_tasks, PARALLEL_BATCH_SIZE):
            batch_count += 1
            batch_end = min(batch_start + PARALLEL_BATCH_SIZE, total_tasks)
            batch_tasks = all_tasks[batch_start:batch_end]
            batch_size = len(batch_tasks)
            
            log("")
            log("=" * 60)
            log(f"BATCH {batch_count} - Processing {batch_size} reports (Completed: {completed_count}/{total_tasks})")
            log("=" * 60)
            
            batch_success = False
            retry_count = 0
            
            while not batch_success and retry_count <= PARALLEL_MAX_RETRIES:
                # Run batch in parallel
                results = []
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = {}
                    for task_num in batch_tasks:
                        future = executor.submit(process_single_report, task_num, total_tasks)
                        futures[future] = task_num
                    
                    for future in as_completed(futures):
                        task_num = futures[future]
                        try:
                            result = future.result()
                            results.append((task_num, result))
                        except Exception as e:
                            log(f"[{task_num}/{total_tasks}] Thread exception: {e}", "error")
                            results.append((task_num, (False, None, 0)))
                
                # Check results
                success_count = sum(1 for _, r in results if r[0])
                fail_count = batch_size - success_count
                rate_limited = any(r[1] == "RATE_LIMITED" for _, r in results)
                
                if rate_limited:
                    rate_limit_hits += 1
                
                log(f"[BATCH {batch_count}] Results: {success_count}/{batch_size} succeeded, {fail_count} failed")
                
                if success_count == batch_size:
                    batch_success = True
                    completed_count += batch_size
                    log(f"[BATCH {batch_count}] ✓ All {batch_size} reports completed successfully!")
                    
                    # Sleep before next batch
                    if completed_count < total_tasks:
                        log(f"[BATCH {batch_count}] Sleeping {SLEEP_AFTER_BATCH}s before next batch...")
                        time.sleep(SLEEP_AFTER_BATCH)
                else:
                    retry_count += 1
                    if retry_count <= PARALLEL_MAX_RETRIES:
                        batch_retries += 1
                        log(f"[BATCH {batch_count}] ✗ {fail_count} failed. Retry {retry_count}/{PARALLEL_MAX_RETRIES} in {PARALLEL_RETRY_SLEEP}s...", "warning")
                        time.sleep(PARALLEL_RETRY_SLEEP)
                    else:
                        # Max retries reached, count partial success
                        completed_count += success_count
                        failed_count += fail_count
                        log(f"[BATCH {batch_count}] ✗ Max retries reached. Moving on with {success_count} successes, {fail_count} failures", "error")
                        batch_success = True  # Exit retry loop
                        
                        if completed_count < total_tasks:
                            log(f"[BATCH {batch_count}] Sleeping {SLEEP_AFTER_BATCH}s before next batch...")
                            time.sleep(SLEEP_AFTER_BATCH)
    
    except KeyboardInterrupt:
        log("")
        log("=" * 60)
        log("Script interrupted by user (Ctrl+C)")
        log("=" * 60)
    
    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log("")
    log("=" * 80)
    log("FINAL SUMMARY - PARALLEL MODE")
    log("=" * 80)
    log(f"Total Duration: {duration:.2f}s ({duration/60:.2f} minutes)")
    log(f"Total Batches: {batch_count}")
    log(f"Batch Retries: {batch_retries}")
    log(f"✓ Completed: {completed_count}")
    log(f"✗ Failed: {failed_count}")
    log(f"Rate Limit Hits: {rate_limit_hits}")
    log("=" * 80)


def main():
    global PARALLEL_BATCH_SIZE, PARALLEL_RETRY_SLEEP, PARALLEL_MAX_RETRIES, MAX_DOWNLOADS, SLEEP_AFTER_BATCH
    
    parser = argparse.ArgumentParser(
        description='NCM System Reports Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python system_reports_download.py                           # Sequential mode (default)
  python system_reports_download.py --parallel                # Parallel mode (3 at once)
  python system_reports_download.py --parallel --batch-size 5 # Parallel with batch size 5
  python system_reports_download.py --max-downloads 100       # Download only 100 reports
        """
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Enable parallel mode: run multiple downloads at once in batches'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=PARALLEL_BATCH_SIZE,
        help=f'Batch size for parallel mode (default: {PARALLEL_BATCH_SIZE})'
    )
    parser.add_argument(
        '--retry-sleep', '-r',
        type=int,
        default=PARALLEL_RETRY_SLEEP,
        help=f'Sleep seconds before retrying failed batch (default: {PARALLEL_RETRY_SLEEP})'
    )
    parser.add_argument(
        '--max-retries', '-mr',
        type=int,
        default=PARALLEL_MAX_RETRIES,
        help=f'Maximum retries per batch (default: {PARALLEL_MAX_RETRIES})'
    )
    parser.add_argument(
        '--max-downloads', '-m',
        type=int,
        default=MAX_DOWNLOADS,
        help=f'Maximum number of downloads (default: {MAX_DOWNLOADS})'
    )
    parser.add_argument(
        '--sleep-after-batch', '-s',
        type=int,
        default=SLEEP_AFTER_BATCH,
        help=f'Sleep seconds after each successful batch (default: {SLEEP_AFTER_BATCH})'
    )
    
    args = parser.parse_args()
    
    # Update global settings
    PARALLEL_BATCH_SIZE = args.batch_size
    PARALLEL_RETRY_SLEEP = args.retry_sleep
    PARALLEL_MAX_RETRIES = args.max_retries
    MAX_DOWNLOADS = args.max_downloads
    SLEEP_AFTER_BATCH = args.sleep_after_batch
    
    if args.parallel:
        run_parallel_mode()
    else:
        run_sequential_mode()


if __name__ == "__main__":
    main()
