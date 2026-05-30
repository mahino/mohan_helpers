#!/usr/bin/env python3
"""
NCM Cost Center Reports Downloader with Detailed API Metrics
Uses HTTP Basic Authentication and comprehensive logging

Supports two modes:
1. Sequential (default): Downloads one report at a time with rate limiting
2. Parallel (--parallel): Downloads in batches, waits for all to succeed before next batch
"""
import sys
import json
import time
import os
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import threading

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger, LoggedRequests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize logger
logger = get_logger(__file__)

# Initialize logged requests (automatically tracks API metrics)
requests = LoggedRequests(logger)

# Configuration
NCM_BASE_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com"
REPORTS_URL = f"{NCM_BASE_URL}/v1/reports/download"
STATUS_URL_TEMPLATE = f"{NCM_BASE_URL}/v1/reports/download/status?downloadId={{}}"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}

MAX_DOWNLOADS = 1000
RATE_LIMIT_SLEEP = 60
DOWNLOADS_PER_MINUTE = 3
SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE = 60
STATUS_CHECK_MAX_RETRIES = 20  # 20 * 30 seconds = 10 minutes
STATUS_CHECK_INTERVAL = 30  # 30 seconds between status checks

# Parallel mode settings
PARALLEL_BATCH_SIZE = 3
PARALLEL_RETRY_SLEEP = 60  # Sleep before retrying failed batch

os.makedirs("reports", exist_ok=True)

# Report payload
# REPORT_PAYLOAD = {
#     "reportConfig": {
#         "reportType": "CHARGEBACK_RESOURCES_BY_ACCOUNT",
#         "dataSource": {
#             "resourceGroupIds": [],
#             "resourceGroupType": "ALL"
#         },
#         "reportPeriod": {
#             "timeUnit": "POINT_IN_TIME"
#         },
#         "reportTemplateDetails": {
#             "fileType": "CSV"
#         }
#     }
# }

REPORT_PAYLOAD = {
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


# Thread-safe lock for metrics
metrics_lock = threading.Lock()


class DetailedAPIMetrics:
    """
    Enhanced API metrics tracker for detailed performance analysis.
    Tracks timing, success/failure rates, percentiles, and more.
    Thread-safe for parallel operations.
    """
    
    def __init__(self):
        self.download_times = []  # Time for download API calls
        self.status_times = []    # Time for status check API calls
        self.download_status_codes = defaultdict(int)
        self.status_check_status_codes = defaultdict(int)
        self.download_errors = 0
        self.status_check_errors = 0
        self.rate_limit_hits = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.processing_times = []  # Time from request to completion
        self.download_durations = []  # Time from download API success to status COMPLETED
        self.status_check_counts = []  # Number of status checks per report
        self.start_time = None
        self.end_time = None
        self.batch_count = 0
        self.batch_retries = 0
    
    def start_session(self):
        """Mark the start of the download session."""
        self.start_time = datetime.now()
        logger.info(f"Session started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def end_session(self):
        """Mark the end of the download session."""
        self.end_time = datetime.now()
        logger.info(f"Session ended at: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def record_download_call(self, elapsed_time, status_code=None, error=False):
        """Record metrics for a download API call (thread-safe)."""
        with metrics_lock:
            self.download_times.append(elapsed_time)
            if status_code:
                self.download_status_codes[status_code] += 1
                if status_code == 429:
                    self.rate_limit_hits += 1
            if error:
                self.download_errors += 1
    
    def record_status_call(self, elapsed_time, status_code=None, error=False):
        """Record metrics for a status check API call (thread-safe)."""
        with metrics_lock:
            self.status_times.append(elapsed_time)
            if status_code:
                self.status_check_status_codes[status_code] += 1
            if error:
                self.status_check_errors += 1
    
    def record_report_completion(self, success, processing_time, status_check_count, download_duration=None):
        """Record metrics for a completed report (thread-safe)."""
        with metrics_lock:
            if success:
                self.successful_downloads += 1
                if download_duration is not None:
                    self.download_durations.append(download_duration)
            else:
                self.failed_downloads += 1
            self.processing_times.append(processing_time)
            self.status_check_counts.append(status_check_count)
    
    def record_batch_completion(self, retried=False):
        """Record batch completion."""
        with metrics_lock:
            self.batch_count += 1
            if retried:
                self.batch_retries += 1
    
    def _percentile(self, data, p):
        """Calculate percentile."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]
    
    def _calculate_stats(self, data):
        """Calculate comprehensive statistics for a dataset."""
        if not data:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'avg': 0,
                'median': 0,
                'std_dev': 0,
                'p50': 0,
                'p75': 0,
                'p90': 0,
                'p95': 0,
                'p98': 0,
                'p99': 0,
                'sum': 0
            }
        
        return {
            'count': len(data),
            'min': min(data),
            'max': max(data),
            'avg': sum(data) / len(data),
            'median': statistics.median(data),
            'std_dev': statistics.stdev(data) if len(data) > 1 else 0,
            'p50': self._percentile(data, 50),
            'p75': self._percentile(data, 75),
            'p90': self._percentile(data, 90),
            'p95': self._percentile(data, 95),
            'p98': self._percentile(data, 98),
            'p99': self._percentile(data, 99),
            'sum': sum(data)
        }
    
    def print_detailed_report(self, parallel_mode=False):
        """Print comprehensive API metrics report."""
        logger.info("")
        logger.info("=" * 120)
        logger.info("DETAILED API PERFORMANCE METRICS REPORT")
        logger.info("=" * 120)
        
        # Session Duration
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            logger.info(f"Session Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        # Parallel mode stats
        if parallel_mode:
            logger.info("")
            logger.info("-" * 80)
            logger.info("PARALLEL MODE STATISTICS")
            logger.info("-" * 80)
            logger.info(f"Batch Size: {PARALLEL_BATCH_SIZE}")
            logger.info(f"Total Batches: {self.batch_count}")
            logger.info(f"Batch Retries: {self.batch_retries}")
        
        # Download API Metrics
        logger.info("")
        logger.info("-" * 80)
        logger.info("DOWNLOAD API (/v1/reports/download) METRICS")
        logger.info("-" * 80)
        
        download_stats = self._calculate_stats([t * 1000 for t in self.download_times])  # Convert to ms
        self._print_timing_stats("Download API Response Times", download_stats)
        
        logger.info("")
        logger.info("Download API Status Codes:")
        for code, count in sorted(self.download_status_codes.items()):
            percentage = (count / sum(self.download_status_codes.values())) * 100 if self.download_status_codes else 0
            status_emoji = "✓" if code in [200, 202] else "✗"
            logger.info(f"  {status_emoji} {code}: {count} ({percentage:.1f}%)")
        
        # Status Check API Metrics
        logger.info("")
        logger.info("-" * 80)
        logger.info("STATUS CHECK API (/v1/reports/download/status) METRICS")
        logger.info("-" * 80)
        
        status_stats = self._calculate_stats([t * 1000 for t in self.status_times])  # Convert to ms
        self._print_timing_stats("Status API Response Times", status_stats)
        
        logger.info("")
        logger.info("Status API Status Codes:")
        for code, count in sorted(self.status_check_status_codes.items()):
            percentage = (count / sum(self.status_check_status_codes.values())) * 100 if self.status_check_status_codes else 0
            logger.info(f"  HTTP {code}: {count} ({percentage:.1f}%)")
        
        # Processing Time Metrics (end-to-end)
        logger.info("")
        logger.info("-" * 80)
        logger.info("END-TO-END REPORT PROCESSING METRICS")
        logger.info("-" * 80)
        
        processing_stats = self._calculate_stats([t * 1000 for t in self.processing_times])  # Convert to ms
        self._print_timing_stats("Report Processing Times", processing_stats)
        
        # Status Check Count per Report
        if self.status_check_counts:
            logger.info("")
            logger.info("Status Checks per Report:")
            check_stats = self._calculate_stats(self.status_check_counts)
            logger.info(f"  Min: {check_stats['min']:.0f} | Max: {check_stats['max']:.0f} | Avg: {check_stats['avg']:.1f} | P90: {check_stats['p90']:.0f}")
        
        # Success/Failure Summary
        logger.info("")
        logger.info("-" * 80)
        logger.info("SUCCESS/FAILURE SUMMARY")
        logger.info("-" * 80)
        
        total_attempts = self.successful_downloads + self.failed_downloads
        success_rate = (self.successful_downloads / total_attempts * 100) if total_attempts > 0 else 0
        failure_rate = (self.failed_downloads / total_attempts * 100) if total_attempts > 0 else 0
        
        logger.info(f"Total Download Attempts: {total_attempts}")
        logger.info(f"✓ Successful: {self.successful_downloads} ({success_rate:.1f}%)")
        logger.info(f"✗ Failed: {self.failed_downloads} ({failure_rate:.1f}%)")
        logger.info(f"⚠ Rate Limited (429): {self.rate_limit_hits}")
        logger.info(f"⚠ Download API Errors: {self.download_errors}")
        logger.info(f"⚠ Status Check API Errors: {self.status_check_errors}")
        
        # Download Duration Metrics (API success to completion)
        if self.download_durations:
            logger.info("")
            logger.info("-" * 80)
            logger.info("DOWNLOAD DURATION METRICS (API Success to Completion)")
            logger.info("-" * 80)
            
            duration_stats = self._calculate_stats([t for t in self.download_durations])
            logger.info(f"Download Duration (seconds):")
            logger.info(f"  Count: {duration_stats['count']} | Min: {duration_stats['min']:.2f} | Max: {duration_stats['max']:.2f}")
            logger.info(f"  Avg: {duration_stats['avg']:.2f} | Median: {duration_stats['median']:.2f}")
            logger.info(f"  P90: {duration_stats['p90']:.2f} | P95: {duration_stats['p95']:.2f} | P99: {duration_stats['p99']:.2f}")
        
        # API Call Counts
        logger.info("")
        logger.info("-" * 80)
        logger.info("API CALL COUNTS")
        logger.info("-" * 80)
        logger.info(f"Total Download API Calls: {len(self.download_times)}")
        logger.info(f"Total Status Check API Calls: {len(self.status_times)}")
        logger.info(f"Total API Calls: {len(self.download_times) + len(self.status_times)}")
        
        # Throughput
        if self.start_time and self.end_time:
            duration_minutes = (self.end_time - self.start_time).total_seconds() / 60
            if duration_minutes > 0:
                logger.info("")
                logger.info("-" * 80)
                logger.info("THROUGHPUT METRICS")
                logger.info("-" * 80)
                logger.info(f"Reports per Minute: {self.successful_downloads / duration_minutes:.2f}")
                logger.info(f"API Calls per Minute: {(len(self.download_times) + len(self.status_times)) / duration_minutes:.2f}")
        
        logger.info("")
        logger.info("=" * 120)
    
    def _print_timing_stats(self, title, stats):
        """Print formatted timing statistics."""
        logger.info(f"{title} (ms):")
        logger.info(f"  Count: {stats['count']}")
        logger.info(f"  Min: {stats['min']:.2f} | Max: {stats['max']:.2f} | Avg: {stats['avg']:.2f}")
        logger.info(f"  Median (P50): {stats['median']:.2f} | Std Dev: {stats['std_dev']:.2f}")
        logger.info(f"  P75: {stats['p75']:.2f} | P90: {stats['p90']:.2f} | P95: {stats['p95']:.2f} | P98: {stats['p98']:.2f} | P99: {stats['p99']:.2f}")
        logger.info(f"  Total Time: {stats['sum']:.2f} ms ({stats['sum']/1000:.2f} s)")


# Initialize detailed metrics tracker
detailed_metrics = DetailedAPIMetrics()


def download_report(report_num=None, total=None):
    """Download a single report and record metrics."""
    prefix = f"[{report_num}/{total}] " if report_num and total else ""
    start_time = time.time()
    try:
        response = requests.post(
            REPORTS_URL,
            json=REPORT_PAYLOAD,
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=300
        )
        elapsed = time.time() - start_time
        detailed_metrics.record_download_call(elapsed, response.status_code)
        logger.info(f"{prefix}[DOWNLOAD] Response: {response.status_code} | Time: {elapsed*1000:.2f}ms")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        detailed_metrics.record_download_call(elapsed, error=True)
        logger.error(f"{prefix}[DOWNLOAD] Error: {e} | Time: {elapsed*1000:.2f}ms")
        return None


def check_status(download_id, report_num=None, total=None):
    """Check the status of a report download and record metrics."""
    prefix = f"[{report_num}/{total}] " if report_num and total else ""
    url = STATUS_URL_TEMPLATE.format(download_id)
    start_time = time.time()
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=300
        )
        elapsed = time.time() - start_time
        detailed_metrics.record_status_call(elapsed, response.status_code)
        logger.info(f"{prefix}[STATUS] [dowID:{download_id}] Response: {response.status_code} | Time: {elapsed*1000:.2f}ms")
        return response
    except Exception as e:
        elapsed = time.time() - start_time
        detailed_metrics.record_status_call(elapsed, error=True)
        logger.error(f"{prefix}[STATUS] [dowID:{download_id}] Error checking status: {e} | Time: {elapsed*1000:.2f}ms")
        return None


def process_single_report(report_num, total):
    """
    Process a single report download with status polling.
    Returns (success, download_id, processing_time, status_check_count)
    """
    report_start_time = time.time()
    status_check_count = 0
    download_id = None
    
    logger.info(f"[{report_num}/{total}] Starting download...")
    
    # Download report
    response = download_report(report_num, total)
    
    if response is None:
        processing_time = time.time() - report_start_time
        detailed_metrics.record_report_completion(False, processing_time, status_check_count)
        logger.error(f"[{report_num}/{total}] Download request failed")
        return (False, None, processing_time, status_check_count)
    
    if response.status_code == 429:
        processing_time = time.time() - report_start_time
        logger.warning(f"[{report_num}/{total}] Rate limited (429)")
        detailed_metrics.record_report_completion(False, processing_time, status_check_count)
        return (False, None, processing_time, status_check_count)
    
    if response.status_code not in [200, 202]:
        processing_time = time.time() - report_start_time
        detailed_metrics.record_report_completion(False, processing_time, status_check_count)
        logger.error(f"[{report_num}/{total}] Failed with status {response.status_code}: {response.text[:200]}")
        return (False, None, processing_time, status_check_count)
    
    # Get download ID
    try:
        response_json = response.json()
        download_id = response_json.get('id')
        logger.info(f"[{report_num}/{total}] [dowID:{download_id}] Download initiated")
        download_start_time = time.time()  # Track when download API succeeded
    except Exception as e:
        processing_time = time.time() - report_start_time
        detailed_metrics.record_report_completion(False, processing_time, status_check_count)
        logger.error(f"[{report_num}/{total}] Failed to parse response: {e}")
        return (False, None, processing_time, status_check_count)
    
    # Poll for status
    report_success = False
    download_duration = None
    for i in range(STATUS_CHECK_MAX_RETRIES):
        status_check_count += 1
        status_response = check_status(download_id, report_num, total)
        
        if status_response is None:
            logger.error(f"[{report_num}/{total}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Failed to get status")
            time.sleep(STATUS_CHECK_INTERVAL)
            continue
        
        try:
            status_json = status_response.json()
            status = status_json.get('status', 'UNKNOWN')
            
            if status == 'PROCESSING':
                logger.info(f"[{report_num}/{total}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Status: PROCESSING, waiting {STATUS_CHECK_INTERVAL}s...")
                time.sleep(STATUS_CHECK_INTERVAL)
                continue
            elif status == 'COMPLETED':
                report_success = True
                download_duration = time.time() - download_start_time  # Calculate download duration
                logger.info(f"[{report_num}/{total}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] ✓ Status: COMPLETED")
                break
            elif status == 'FAILED':
                logger.error(f"[{report_num}/{total}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] ✗ Status: FAILED")
                break
            else:
                logger.warning(f"[{report_num}/{total}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Unknown status: {status}")
                time.sleep(STATUS_CHECK_INTERVAL)
        
        except Exception as e:
            logger.error(f"[{report_num}/{total}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Failed to parse status: {e}")
            time.sleep(STATUS_CHECK_INTERVAL)
    
    processing_time = time.time() - report_start_time
    detailed_metrics.record_report_completion(report_success, processing_time, status_check_count, download_duration)
    
    if report_success:
        duration_msg = f" (download took {download_duration:.2f}s)" if download_duration else ""
        logger.info(f"[{report_num}/{total}] [dowID:{download_id}] ✓ Completed in {processing_time:.2f}s ({status_check_count} status checks){duration_msg}")
    else:
        logger.error(f"[{report_num}/{total}] [dowID:{download_id}] ✗ Failed after {processing_time:.2f}s ({status_check_count} status checks)")
    
    return (report_success, download_id, processing_time, status_check_count)


def run_parallel_mode():
    """
    Run downloads in parallel batches.
    Triggers next batch only after all in current batch succeed.
    Retries failed batch after 60 seconds.
    """
    logger.info("=" * 100)
    logger.info("NCM COST CENTER REPORTS DOWNLOAD SCRIPT - PARALLEL MODE")
    logger.info("=" * 100)
    logger.info(f"Target URL: {REPORTS_URL}")
    logger.info(f"Max Downloads: {MAX_DOWNLOADS}")
    logger.info(f"Batch Size: {PARALLEL_BATCH_SIZE}")
    logger.info(f"Retry Sleep: {PARALLEL_RETRY_SLEEP}s")
    logger.info("=" * 100)
    
    detailed_metrics.start_session()
    
    completed_count = 0
    batch_num = 0
    
    try:
        while completed_count < MAX_DOWNLOADS:
            batch_num += 1
            batch_size = min(PARALLEL_BATCH_SIZE, MAX_DOWNLOADS - completed_count)
            
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"BATCH {batch_num} - Processing {batch_size} reports (Completed: {completed_count}/{MAX_DOWNLOADS})")
            logger.info("=" * 80)
            
            batch_success = False
            retry_count = 0
            
            while not batch_success:
                # Run batch in parallel
                results = []
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = {}
                    for i in range(batch_size):
                        report_num = completed_count + i + 1
                        future = executor.submit(process_single_report, report_num, MAX_DOWNLOADS)
                        futures[future] = report_num
                    
                    for future in as_completed(futures):
                        report_num = futures[future]
                        try:
                            result = future.result()
                            results.append((report_num, result))
                        except Exception as e:
                            logger.error(f"[{report_num}/{MAX_DOWNLOADS}] Thread exception: {e}")
                            results.append((report_num, (False, None, 0, 0)))
                
                # Check if all succeeded
                all_success = all(r[1][0] for r in results)
                success_count = sum(1 for r in results if r[1][0])
                fail_count = batch_size - success_count
                
                logger.info("")
                logger.info(f"[BATCH {batch_num}] Results: {success_count}/{batch_size} succeeded, {fail_count} failed")
                
                if all_success:
                    batch_success = True
                    completed_count += batch_size
                    detailed_metrics.record_batch_completion(retried=(retry_count > 0))
                    logger.info(f"[BATCH {batch_num}] ✓ All {batch_size} reports completed successfully!")
                    
                    # Sleep before next batch (rate limiting)
                    if completed_count < MAX_DOWNLOADS:
                        logger.info(f"[BATCH {batch_num}] Sleeping {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE}s before next batch...")
                        time.sleep(SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
                else:
                    retry_count += 1
                    logger.warning(f"[BATCH {batch_num}] ✗ {fail_count} reports failed. Retry #{retry_count} in {PARALLEL_RETRY_SLEEP}s...")
                    
                    # Log failed reports
                    for report_num, result in results:
                        if not result[0]:
                            download_id = result[1] or "N/A"
                            logger.warning(f"  - Report {report_num} [dowID:{download_id}] FAILED")
                    
                    time.sleep(PARALLEL_RETRY_SLEEP)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Script interrupted by user (Ctrl+C)")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        detailed_metrics.end_session()
        
        # Print summary
        logger.info("")
        logger.info("=" * 100)
        logger.info("FINAL SUMMARY - PARALLEL MODE")
        logger.info("=" * 100)
        logger.info(f"Total Completed: {completed_count}/{MAX_DOWNLOADS}")
        logger.info(f"Total Batches: {detailed_metrics.batch_count}")
        logger.info(f"Batch Retries: {detailed_metrics.batch_retries}")
        logger.info(f"Rate Limit Hits (429): {detailed_metrics.rate_limit_hits}")
        logger.info("=" * 100)
        
        # Print detailed API metrics report
        detailed_metrics.print_detailed_report(parallel_mode=True)


def run_sequential_mode():
    """Run downloads sequentially (original behavior)."""
    logger.info("=" * 100)
    logger.info("NCM COST CENTER REPORTS DOWNLOAD SCRIPT - SEQUENTIAL MODE")
    logger.info("=" * 100)
    logger.info(f"Target URL: {REPORTS_URL}")
    logger.info(f"Max Downloads: {MAX_DOWNLOADS}")
    logger.info(f"Rate Limit: {DOWNLOADS_PER_MINUTE} requests, then sleep {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE}s")
    logger.info(f"Rate Limit Sleep (on 429): {RATE_LIMIT_SLEEP}s")
    logger.info("=" * 100)
    
    detailed_metrics.start_session()
    
    download_count = 0
    sleep_count = 0
    
    try:
        while download_count < MAX_DOWNLOADS:
            # Rate limiting - sleep after every N downloads
            if download_count > 0 and download_count % DOWNLOADS_PER_MINUTE == 0:
                logger.info(f"[RATE LIMIT] Sleeping {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE}s after {DOWNLOADS_PER_MINUTE} downloads...")
                time.sleep(SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
            
            report_start_time = time.time()
            status_check_count = 0
            
            logger.info("")
            logger.info("-" * 60)
            logger.info(f"REPORT {download_count + 1}/{MAX_DOWNLOADS}")
            logger.info("-" * 60)
            
            # Download report
            response = download_report(download_count + 1, MAX_DOWNLOADS)
            
            if response is None:
                detailed_metrics.record_report_completion(False, time.time() - report_start_time, status_check_count)
                logger.error(f"[REPORT {download_count + 1}] Download request failed")
                download_count += 1
                time.sleep(1)
                continue
            
            if response.status_code == 429:
                sleep_count += 1
                logger.warning(f"[RATE LIMITED] 429 received. Sleep count: {sleep_count}. Sleeping {RATE_LIMIT_SLEEP}s...")
                time.sleep(RATE_LIMIT_SLEEP)
                continue
            
            if response.status_code not in [200, 202]:
                detailed_metrics.record_report_completion(False, time.time() - report_start_time, status_check_count)
                logger.error(f"[REPORT {download_count + 1}] Failed with status {response.status_code}: {response.text[:200]}")
                time.sleep(1)
                continue
            
            # Get download ID and check status
            try:
                response_json = response.json()
                download_id = response_json.get('id')
                logger.info(f"[REPORT {download_count + 1}] Download ID: {download_id}")
                download_start_time = time.time()  # Track when download API succeeded
            except Exception as e:
                detailed_metrics.record_report_completion(False, time.time() - report_start_time, status_check_count)
                logger.error(f"[REPORT {download_count + 1}] Failed to parse response: {e}")
                continue
            
            download_count += 1
            # Poll for status
            report_success = False
            download_duration = None
            for i in range(STATUS_CHECK_MAX_RETRIES):
                status_check_count += 1
                status_response = check_status(download_id, download_count, MAX_DOWNLOADS)
                
                if status_response is None:
                    logger.error(f"[{download_count}/{MAX_DOWNLOADS}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Failed to get status")
                    time.sleep(STATUS_CHECK_INTERVAL)
                    continue
                
                try:
                    status_json = status_response.json()
                    status = status_json.get('status', 'UNKNOWN')
                    
                    if status == 'PROCESSING':
                        logger.info(f"[{download_count}/{MAX_DOWNLOADS}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Status: PROCESSING, waiting {STATUS_CHECK_INTERVAL}s...")
                        time.sleep(STATUS_CHECK_INTERVAL)
                        continue
                    elif status == 'COMPLETED':
                        report_success = True
                        download_duration = time.time() - download_start_time  # Calculate download duration
                        logger.info(f"[{download_count}/{MAX_DOWNLOADS}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] ✓ Status: COMPLETED")
                        break
                    elif status == 'FAILED':
                        logger.error(f"[{download_count}/{MAX_DOWNLOADS}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] ✗ Status: FAILED")
                        break
                    else:
                        logger.warning(f"[{download_count}/{MAX_DOWNLOADS}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Unknown status: {status}")
                        time.sleep(STATUS_CHECK_INTERVAL)
                
                except Exception as e:
                    logger.error(f"[{download_count}/{MAX_DOWNLOADS}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Failed to parse status: {e}")
                    time.sleep(STATUS_CHECK_INTERVAL)
            
            # Record report completion
            processing_time = time.time() - report_start_time
            detailed_metrics.record_report_completion(report_success, processing_time, status_check_count, download_duration)
            
            if report_success:
                sleep_count = 0
                duration_msg = f" (download took {download_duration:.2f}s)" if download_duration else ""
                logger.info(f"[REPORT {download_count}/{MAX_DOWNLOADS}] [dowID:{download_id}] ✓ Completed in {processing_time:.2f}s ({status_check_count} status checks){duration_msg}")
            else:
                logger.error(f"[REPORT {download_count}/{MAX_DOWNLOADS}] [dowID:{download_id}] ✗ Failed after {processing_time:.2f}s ({status_check_count} status checks)")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Script interrupted by user (Ctrl+C)")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        detailed_metrics.end_session()
        
        # Print summary
        logger.info("")
        logger.info("=" * 100)
        logger.info("FINAL SUMMARY - SEQUENTIAL MODE")
        logger.info("=" * 100)
        logger.info(f"Total Successful Downloads: {download_count}/{MAX_DOWNLOADS}")
        logger.info(f"Rate Limit Hits (429): {detailed_metrics.rate_limit_hits}")
        logger.info("=" * 100)
        
        # Print detailed API metrics report
        detailed_metrics.print_detailed_report(parallel_mode=False)


def main():
    global PARALLEL_BATCH_SIZE, PARALLEL_RETRY_SLEEP
    
    parser = argparse.ArgumentParser(
        description='NCM Cost Center Reports Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cc_reports_download.py                    # Sequential mode (default)
  python cc_reports_download.py --parallel         # Parallel mode (3 at once, retry until all succeed)
  python cc_reports_download.py --parallel --batch-size 5  # Parallel with batch size 5
        """
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Enable parallel mode: run 3 downloads at once, retry batch until all succeed'
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
    
    args = parser.parse_args()
    
    # Update global settings if provided
    PARALLEL_BATCH_SIZE = args.batch_size
    PARALLEL_RETRY_SLEEP = args.retry_sleep
    
    if args.parallel:
        run_parallel_mode()
    else:
        run_sequential_mode()


if __name__ == "__main__":
    main()
