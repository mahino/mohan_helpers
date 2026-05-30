import requests
import json
import os
import sys
import urllib3
from datetime import datetime
from requests.auth import HTTPBasicAuth
import time
import logging
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from statistics import mean, median
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
NCM_BASE_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com"

HEADERS = {
    'Content-Type': 'application/json',
    'Accept-Language': 'application/json'
}

AUTH = HTTPBasicAuth('admin', 'Nutanix.123')
API_TIMEOUT = 300

# Status checking configuration
STATUS_CHECK_MAX_RETRIES = 20  # 20 retries * 30 seconds = 10 minutes max
STATUS_CHECK_INTERVAL = 30  # Check every 30 seconds

# Parallel processing configuration
PARALLEL_BATCH_SIZE = 3  # Number of parallel downloads
PARALLEL_RETRY_SLEEP = 30  # Sleep between retries (seconds)
PARALLEL_MAX_RETRIES = 5  # Maximum retries per batch

# Rate limiting configuration
RATE_LIMIT_SLEEP = 30  # Sleep when hitting rate limits
SLEEP_BETWEEN_CLUSTERS = 1  # Sleep between individual cluster requests

# Initialize logger (explicitly disable HTTP logging)
logger = get_logger(__file__, include_http_logs=False)

# Disable any existing HTTP loggers to prevent verbose request/response logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('http.client').setLevel(logging.WARNING)
class DetailedAPIMetrics:
    """Track detailed metrics for API calls and downloads"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None
        
        # API call metrics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.response_times = []
        self.status_codes = defaultdict(int)
        self.rate_limit_hits = 0
        
        # Download specific metrics
        self.download_durations = []
        self.status_check_counts = []
        self.completed_downloads = 0
        self.failed_downloads = 0
        
        # Error tracking
        self.errors = defaultdict(int)
    
    def start_session(self):
        self.start_time = time.time()
        logger.info("Starting metrics collection session")
    
    def end_session(self):
        self.end_time = time.time()
        logger.info("Ending metrics collection session")
    
    def record_api_call(self, response_time, status_code, success=True, error=None):
        with self.lock:
            self.total_calls += 1
            self.response_times.append(response_time)
            self.status_codes[status_code] += 1
            
            if success:
                self.successful_calls += 1
            else:
                self.failed_calls += 1
                if error:
                    self.errors[str(error)] += 1
            
            if status_code == 429:
                self.rate_limit_hits += 1
    
    def record_download_completion(self, download_duration, status_checks, success=True):
        with self.lock:
            if success:
                self.completed_downloads += 1
                self.download_durations.append(download_duration)
            else:
                self.failed_downloads += 1
            self.status_check_counts.append(status_checks)
    
    def print_detailed_report(self):
        if not self.start_time or not self.end_time:
            logger.warning("Session not properly started/ended")
            return
        
        total_duration = self.end_time - self.start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("DETAILED PERFORMANCE METRICS")
        logger.info("=" * 80)
        
        # Session info
        logger.info(f"Total Session Duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
        
        # API call metrics
        logger.info("\nAPI CALL METRICS:")
        logger.info(f"  Total API Calls: {self.total_calls}")
        logger.info(f"  Successful: {self.successful_calls}")
        logger.info(f"  Failed: {self.failed_calls}")
        logger.info(f"  Success Rate: {(self.successful_calls/self.total_calls*100):.1f}%" if self.total_calls > 0 else "  Success Rate: N/A")
        logger.info(f"  Rate Limit Hits (429): {self.rate_limit_hits}")
        
        if self.response_times:
            logger.info(f"  Response Time - Mean: {mean(self.response_times):.2f}s")
            logger.info(f"  Response Time - Median: {median(self.response_times):.2f}s")
            logger.info(f"  Response Time - Min: {min(self.response_times):.2f}s")
            logger.info(f"  Response Time - Max: {max(self.response_times):.2f}s")
        
        # Status code breakdown
        logger.info("\nSTATUS CODE BREAKDOWN:")
        for code, count in sorted(self.status_codes.items()):
            logger.info(f"  {code}: {count}")
        
        # Download metrics
        if self.download_durations:
            logger.info("\nDOWNLOAD DURATION METRICS:")
            logger.info(f"  Completed Downloads: {self.completed_downloads}")
            logger.info(f"  Failed Downloads: {self.failed_downloads}")
            logger.info(f"  Average Duration: {mean(self.download_durations):.2f}s")
            logger.info(f"  Median Duration: {median(self.download_durations):.2f}s")
            logger.info(f"  Min Duration: {min(self.download_durations):.2f}s")
            logger.info(f"  Max Duration: {max(self.download_durations):.2f}s")
        
        if self.status_check_counts:
            logger.info("\nSTATUS CHECK METRICS:")
            logger.info(f"  Average Status Checks: {mean(self.status_check_counts):.1f}")
            logger.info(f"  Max Status Checks: {max(self.status_check_counts)}")
        
        # Error breakdown
        if self.errors:
            logger.info("\nERROR BREAKDOWN:")
            for error, count in sorted(self.errors.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {error}: {count}")
        
        logger.info("=" * 80)


def fetch_cluster_list():
    """Fetch the list of clusters with proper error handling"""
    logger.info("Fetching cluster list...")
    
    try:
        start_time = time.time()
        cluster_list_response = requests.post(
            f"{NCM_BASE_URL}/v1/cg/nutanix/metering/clusters?limit=500&offset=1",
            json={"timeUnit": "month", "timeRange": {"startTime": 1761955200, "endTime": 1764547140}, "resourceGroupType": "", "resourceGroupIds": [], "currencyType": "TARGET"},
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=API_TIMEOUT
        )
        response_time = time.time() - start_time
        
        if cluster_list_response.status_code == 200:
            cluster_data = cluster_list_response.json()
            cluster_list = [cluster['clusterId'] for cluster in cluster_data['items'][0]['data']]
            logger.info(f"✓ Successfully fetched {len(cluster_list)} clusters in {response_time:.2f}s")
            return cluster_list, response_time, True
        else:
            logger.error(f"✗ Failed to fetch cluster list: HTTP {cluster_list_response.status_code}")
            logger.error(f"Response: {cluster_list_response.text}")
            return [], response_time, False
            
    except requests.exceptions.Timeout:
        logger.error(f"✗ Timeout while fetching cluster list (>{API_TIMEOUT}s)")
        return [], API_TIMEOUT, False
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Request error while fetching cluster list: {e}")
        return [], 0, False
    except Exception as e:
        logger.error(f"✗ Unexpected error while fetching cluster list: {e}")
        return [], 0, False

def create_report_payload(cluster_id):
    """Create report payload for a specific cluster"""
    return {
        "reportConfig": {
            "reportType": "NX_ANALYZE",
            "dataSource": {
                "clusterId": cluster_id,
                "resourceGroupIds": [],
                "resourceGroupType": "NX_OVERVIEW",
                "timeUnit": "month",
                "mergeSpendAsOthersAfter": -1,
                "groupBy": "costCenter",
                "currencyType": "TARGET",
                "filters": {}
            },
            "reportPeriod": {"timeUnit": "CUSTOM"},
            "timeRange": {
                "usageEndTime": "1769903940",
                "usageStartTime": "1767225600"
            },
            "reportTemplateDetails": {"fileType": "CSV"}
        }
    }

def process_single_cluster(cluster_id, metrics, status_retries=STATUS_CHECK_MAX_RETRIES):
    """Process a single cluster report download with proper error handling and status checking"""
    logger.info(f"[CLUSTER {cluster_id}] Starting report download...")
    
    try:
        # Step 1: Initiate download
        payload = create_report_payload(cluster_id)
        
        start_time = time.time()
        response = requests.post(
            f"{NCM_BASE_URL}/v1/reports/download",
            json=payload,
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=API_TIMEOUT
        )
        response_time = time.time() - start_time
        
        # Record API call metrics
        success = response.status_code in [200, 202]
        error = None if success else f"HTTP {response.status_code}"
        metrics.record_api_call(response_time, response.status_code, success, error)
        
        logger.info(f"[CLUSTER {cluster_id}] Download API response: {response.status_code} ({response_time:.2f}s)")
        
        if response.status_code == 429:
            logger.warning(f"[CLUSTER {cluster_id}] Rate limited (429), sleeping {RATE_LIMIT_SLEEP}s...")
            time.sleep(RATE_LIMIT_SLEEP)
            return False, None
        
        if response.status_code not in [200, 202]:
            logger.error(f"[CLUSTER {cluster_id}] ✗ Download failed: HTTP {response.status_code}")
            logger.error(f"[CLUSTER {cluster_id}] Response: {response.text}")
            return False, None
        
        # Get download ID
        try:
            response_data = response.json()
            download_id = response_data.get('downloadId') or response_data.get('id')
            if not download_id:
                logger.error(f"[CLUSTER {cluster_id}] ✗ No downloadId or id found in response: {list(response_data.keys())}")
                return False, None
            logger.info(f"[CLUSTER {cluster_id}] ✓ Download initiated, ID: {download_id}")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"[CLUSTER {cluster_id}] ✗ Failed to parse download ID: {e}")
            logger.error(f"[CLUSTER {cluster_id}] Response text: {response.text}")
            return False, None
        
        # Step 2: Poll status until completion
        download_start_time = time.time()
        status_checks = 0
        
        for attempt in range(status_retries):
            status_checks += 1
            time.sleep(STATUS_CHECK_INTERVAL)
            
            try:
                status_start = time.time()
                status_response = requests.get(
                    f"{NCM_BASE_URL}/v1/reports/download/status?downloadId={download_id}",
                    headers=HEADERS,
                    auth=AUTH,
                    verify=False,
                    timeout=API_TIMEOUT
                )
                status_response_time = time.time() - status_start
                
                # Record status API call
                status_success = status_response.status_code == 200
                status_error = None if status_success else f"HTTP {status_response.status_code}"
                metrics.record_api_call(status_response_time, status_response.status_code, status_success, status_error)
                
                if status_response.status_code == 429:
                    logger.warning(f"[CLUSTER {cluster_id}] Status check rate limited, sleeping {RATE_LIMIT_SLEEP}s...")
                    time.sleep(RATE_LIMIT_SLEEP)
                    continue
                
                if status_response.status_code != 200:
                    logger.error(f"[CLUSTER {cluster_id}] Status check failed: HTTP {status_response.status_code}")
                    continue
                
                status_data = status_response.json()
                status = status_data.get('status', 'UNKNOWN')
                
                logger.info(f"[CLUSTER {cluster_id}] Status check #{status_checks}: {status} ({status_response_time:.2f}s)")
                
                if status == 'COMPLETED':
                    download_duration = time.time() - download_start_time
                    logger.info(f"[CLUSTER {cluster_id}] ✓ Report completed in {download_duration:.2f}s after {status_checks} checks")
                    metrics.record_download_completion(download_duration, status_checks, True)
                    return True, download_id
                
                elif status in ['FAILED', 'ERROR', 'CANCELLED']:
                    logger.error(f"[CLUSTER {cluster_id}] ✗ Report failed with status: {status}")
                    metrics.record_download_completion(0, status_checks, False)
                    return False, download_id
                
                # Status is still PROCESSING or PENDING, continue polling
                
            except requests.exceptions.Timeout:
                logger.warning(f"[CLUSTER {cluster_id}] Status check timeout (>{API_TIMEOUT}s)")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"[CLUSTER {cluster_id}] Status check request error: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"[CLUSTER {cluster_id}] Status check JSON decode error: {e}")
                continue
        
        # If we get here, we've exceeded max retries
        logger.error(f"[CLUSTER {cluster_id}] ✗ Status check timeout after {status_retries} attempts ({status_retries * STATUS_CHECK_INTERVAL / 60:.1f} minutes)")
        metrics.record_download_completion(0, status_checks, False)
        return False, download_id
        
    except requests.exceptions.Timeout:
        logger.error(f"[CLUSTER {cluster_id}] ✗ Download API timeout (>{API_TIMEOUT}s)")
        metrics.record_api_call(API_TIMEOUT, 0, False, "Timeout")
        return False, None
    except requests.exceptions.RequestException as e:
        logger.error(f"[CLUSTER {cluster_id}] ✗ Download API request error: {e}")
        metrics.record_api_call(0, 0, False, str(e))
        return False, None
    except Exception as e:
        logger.error(f"[CLUSTER {cluster_id}] ✗ Unexpected error: {e}")
        metrics.record_api_call(0, 0, False, str(e))
        return False, None


def run_sequential_mode(cluster_list, metrics, status_retries=STATUS_CHECK_MAX_RETRIES):
    """Process clusters sequentially"""
    logger.info(f"Starting SEQUENTIAL processing of {len(cluster_list)} clusters...")
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, cluster_id in enumerate(cluster_list, 1):
        logger.info(f"\n[{i}/{len(cluster_list)}] Processing cluster {cluster_id}...")
        
        success, download_id = process_single_cluster(cluster_id, metrics, status_retries)
        
        if success:
            successful_downloads += 1
            logger.info(f"[{i}/{len(cluster_list)}] ✓ Cluster {cluster_id} completed successfully")
        else:
            failed_downloads += 1
            logger.error(f"[{i}/{len(cluster_list)}] ✗ Cluster {cluster_id} failed")
        
        # Sleep between clusters to avoid rate limiting
        if i < len(cluster_list):
            logger.info(f"Sleeping {SLEEP_BETWEEN_CLUSTERS}s before next cluster...")
            time.sleep(SLEEP_BETWEEN_CLUSTERS)
    
    logger.info(f"\nSequential processing completed: {successful_downloads} successful, {failed_downloads} failed")
    return successful_downloads, failed_downloads


def run_parallel_mode(cluster_list, metrics, batch_size=PARALLEL_BATCH_SIZE, max_retries=PARALLEL_MAX_RETRIES, status_retries=STATUS_CHECK_MAX_RETRIES):
    """Process clusters in parallel batches"""
    logger.info(f"Starting PARALLEL processing of {len(cluster_list)} clusters (batch size: {batch_size})...")
    
    total_successful = 0
    total_failed = 0
    
    # Process in batches
    for batch_start in range(0, len(cluster_list), batch_size):
        batch_end = min(batch_start + batch_size, len(cluster_list))
        batch_clusters = cluster_list[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        
        logger.info(f"\n[BATCH {batch_num}] Processing clusters {batch_start + 1}-{batch_end} ({len(batch_clusters)} clusters)...")
        
        # Retry logic for the batch
        retry_count = 0
        batch_success = False
        
        while not batch_success and retry_count < max_retries:
            batch_successful = 0
            batch_failed = 0
            
            with ThreadPoolExecutor(max_workers=len(batch_clusters)) as executor:
                # Submit all tasks in the batch
                future_to_cluster = {
                    executor.submit(process_single_cluster, cluster_id, metrics, status_retries): cluster_id 
                    for cluster_id in batch_clusters
                }
                
                # Collect results
                for future in as_completed(future_to_cluster):
                    cluster_id = future_to_cluster[future]
                    try:
                        success, download_id = future.result()
                        if success:
                            batch_successful += 1
                        else:
                            batch_failed += 1
                    except Exception as e:
                        logger.error(f"[BATCH {batch_num}] Exception processing cluster {cluster_id}: {e}")
                        batch_failed += 1
            
            if batch_failed == 0:
                batch_success = True
                total_successful += batch_successful
                logger.info(f"[BATCH {batch_num}] ✓ All {len(batch_clusters)} clusters completed successfully!")
            else:
                retry_count += 1
                total_failed += batch_failed
                
                if retry_count >= max_retries:
                    logger.error(f"[BATCH {batch_num}] ✗ Maximum retries ({max_retries}) reached. Moving on to next batch...")
                    logger.error(f"[BATCH {batch_num}] ✗ Skipping {batch_failed} failed clusters, continuing with {batch_successful} successful clusters")
                    total_successful += batch_successful
                    batch_success = True  # Force exit from retry loop
                else:
                    logger.warning(f"[BATCH {batch_num}] ✗ {batch_failed} clusters failed. Retry #{retry_count}/{max_retries} in {PARALLEL_RETRY_SLEEP}s...")
                    time.sleep(PARALLEL_RETRY_SLEEP)
        
        # Log batch summary
        if retry_count > 0:
            if retry_count >= max_retries:
                logger.warning(f"[BATCH {batch_num}] SUMMARY: Completed with some failures after {retry_count} retries (MAX REACHED)")
            else:
                logger.info(f"[BATCH {batch_num}] SUMMARY: Completed successfully after {retry_count} retries")
        else:
            logger.info(f"[BATCH {batch_num}] SUMMARY: Completed successfully on first attempt")
    
    logger.info(f"\nParallel processing completed: {total_successful} successful, {total_failed} failed")
    return total_successful, total_failed


def main():
    """Main function with argument parsing and execution"""
    parser = argparse.ArgumentParser(
        description='NCM Cluster Reports Downloader - Improved Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python del.py                                    # Sequential mode (default)
  python del.py --parallel                         # Parallel mode (3 clusters at once)
  python del.py --parallel --batch-size 5         # Parallel with batch size 5
  python del.py --parallel --max-retries 3        # Parallel with max 3 retries per batch
        """
    )
    
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Enable parallel mode: process multiple clusters at once'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=PARALLEL_BATCH_SIZE,
        help=f'Batch size for parallel mode (default: {PARALLEL_BATCH_SIZE})'
    )
    parser.add_argument(
        '--max-retries', '-mr',
        type=int,
        default=PARALLEL_MAX_RETRIES,
        help=f'Maximum retries per batch before skipping failed clusters (default: {PARALLEL_MAX_RETRIES})'
    )
    parser.add_argument(
        '--status-retries', '-sr',
        type=int,
        default=STATUS_CHECK_MAX_RETRIES,
        help=f'Maximum status check retries per cluster (default: {STATUS_CHECK_MAX_RETRIES})'
    )
    
    args = parser.parse_args()
    
    # Update configuration based on arguments
    batch_size = args.batch_size
    max_retries = args.max_retries
    status_retries = args.status_retries
    
    # Initialize metrics
    metrics = DetailedAPIMetrics()
    metrics.start_session()
    
    try:
        # Step 1: Fetch cluster list
        logger.info("=" * 80)
        logger.info("NCM CLUSTER REPORTS DOWNLOADER - IMPROVED VERSION")
        logger.info("=" * 80)
        
        cluster_list, fetch_time, fetch_success = fetch_cluster_list()
        metrics.record_api_call(fetch_time, 200 if fetch_success else 500, fetch_success, None if fetch_success else "Cluster list fetch failed")
        
        if not fetch_success or not cluster_list:
            logger.error("Failed to fetch cluster list. Exiting.")
            return 1
        
        logger.info(f"Found {len(cluster_list)} clusters to process")
        logger.info(f"Mode: {'PARALLEL' if args.parallel else 'SEQUENTIAL'}")
        if args.parallel:
            logger.info(f"Batch size: {args.batch_size}, Max retries: {args.max_retries}")
        logger.info(f"Status check timeout: {status_retries * STATUS_CHECK_INTERVAL / 60:.1f} minutes")
        
        # Step 2: Process clusters
        if args.parallel:
            successful, failed = run_parallel_mode(cluster_list, metrics, batch_size, max_retries, status_retries)
        else:
            successful, failed = run_sequential_mode(cluster_list, metrics, status_retries)
        
        # Step 3: Final summary
        logger.info("\n" + "=" * 80)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Clusters Processed: {len(cluster_list)}")
        logger.info(f"Successful Downloads: {successful}")
        logger.info(f"Failed Downloads: {failed}")
        logger.info(f"Success Rate: {(successful/(successful+failed)*100):.1f}%" if (successful + failed) > 0 else "Success Rate: N/A")
        logger.info("=" * 80)
        
        return 0 if failed == 0 else 1
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Script interrupted by user (Ctrl+C)")
        logger.info("=" * 60)
        return 130
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    finally:
        metrics.end_session()
        metrics.print_detailed_report()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)