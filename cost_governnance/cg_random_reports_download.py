#!/usr/bin/env python3
"""
NCM Reports Downloader with Parallel Processing Support
Downloads all report types with detailed metrics tracking and parallel processing capabilities

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

# Initialize logged requests
requests = LoggedRequests(logger)

# Configuration
NCM_BASE_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com"
REPORTS_URL = f"{NCM_BASE_URL}/v1/reports/download"
STATUS_URL_TEMPLATE = f"{NCM_BASE_URL}/v1/reports/download/status?downloadId={{}}"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}

# Rate limiting and processing settings
DOWNLOADS_PER_MINUTE = 3  # Rate limit: 3 requests per minute
RATE_LIMIT_SLEEP = 60
SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE = 60
STATUS_CHECK_MAX_RETRIES = 20  # 20 * 30 seconds = 10 minutes
STATUS_CHECK_INTERVAL = 30  # 30 seconds between status checks
API_TIMEOUT = 300

# Parallel mode settings
PARALLEL_BATCH_SIZE = 3
PARALLEL_RETRY_SLEEP = 60  # Sleep before retrying failed batch
PARALLEL_MAX_RETRIES = 1  # Maximum retries per batch before giving up

# Report configuration
Budget_UUID = "31e8c3f6-87bd-45c5-9981-c4840809eabb"
month_start_epoch_time = time.time() - 30 * 24 * 60 * 60
month_end_epoch_time = time.time()

os.makedirs("reports", exist_ok=True)

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
    
    def _calculate_stats(self, data):
        """Calculate comprehensive statistics for a dataset."""
        if not data:
            return {
                'count': 0, 'min': 0, 'max': 0, 'avg': 0, 'median': 0,
                'std_dev': 0, 'p90': 0, 'p95': 0, 'p99': 0, 'sum': 0
            }
        
        return {
            'count': len(data),
            'min': min(data),
            'max': max(data),
            'avg': sum(data) / len(data),
            'median': statistics.median(data),
            'std_dev': statistics.stdev(data) if len(data) > 1 else 0,
            'p90': sorted(data)[int(len(data) * 0.9)] if data else 0,
            'p95': sorted(data)[int(len(data) * 0.95)] if data else 0,
            'p99': sorted(data)[int(len(data) * 0.99)] if data else 0,
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
        logger.info("DOWNLOAD API METRICS")
        logger.info("-" * 80)
        
        download_stats = self._calculate_stats([t * 1000 for t in self.download_times])
        logger.info(f"Download API Response Times (ms):")
        logger.info(f"  Count: {download_stats['count']} | Avg: {download_stats['avg']:.2f} | P90: {download_stats['p90']:.2f} | P95: {download_stats['p95']:.2f}")
        
        logger.info("Download API Status Codes:")
        for code, count in sorted(self.download_status_codes.items()):
            percentage = (count / sum(self.download_status_codes.values())) * 100 if self.download_status_codes else 0
            status_emoji = "✓" if code in [200, 202] else "✗"
            logger.info(f"  {status_emoji} {code}: {count} ({percentage:.1f}%)")
        
        # Success/Failure Summary
        logger.info("")
        logger.info("-" * 80)
        logger.info("SUCCESS/FAILURE SUMMARY")
        logger.info("-" * 80)
        
        total_attempts = self.successful_downloads + self.failed_downloads
        success_rate = (self.successful_downloads / total_attempts * 100) if total_attempts > 0 else 0
        
        logger.info(f"Total Download Attempts: {total_attempts}")
        logger.info(f"✓ Successful: {self.successful_downloads} ({success_rate:.1f}%)")
        logger.info(f"✗ Failed: {self.failed_downloads}")
        logger.info(f"⚠ Rate Limited (429): {self.rate_limit_hits}")
        logger.info(f"⚠ Download API Errors: {self.download_errors}")
        
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
        
        logger.info("")
        logger.info("=" * 120)


# Initialize detailed metrics tracker
detailed_metrics = DetailedAPIMetrics()


# All report payloads in a list
REPORT_PAYLOADS = [
    # Current Spend Overview CSV
    {
        "name": "Current Spend Overview CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Current Spend Overview PDF
    {
        "name": "Current Spend Overview PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Current Spend Cluster CSV
    {
        "name": "Current Spend Cluster CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Current Spend Cluster PDF
    {
        "name": "Current Spend Cluster PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Current Spend Cost Center CSV
    {
        "name": "Current Spend Cost Center CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Current Spend Cost Center PDF
    {
        "name": "Current Spend Cost Center PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Current Spend Service Type CSV
    {
        "name": "Current Spend Service Type CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"serviceType","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Current Spend Service Type PDF
    {
        "name": "Current Spend Service Type PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"serviceType","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Current Spend Service CSV
    {
        "name": "Current Spend Service CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Current Spend Service PDF
    {
        "name": "Current Spend Service PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":"1764547140","usageStartTime":"1761955200"},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Resource Metering XLS
    {
        "name": "Resource Metering XLS",
        "payload": {"reportConfig":{"reportType":"NX_RESOURCE_METERING","reportPeriod":{"timeUnit":"CUSTOM"},"reportTemplateDetails":{"fileType":"XLS"},"dataSource":{"accountId":"00063ffe-e22c-90bf-45a6-7cc25530e846","clusterId":"00063ffe-e22c-90bf-45a6-7cc25530e846","timeUnit":"month","resourceGroupType":"NX_ACCOUNT","resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"]},"timeRange":{"usageStartTime":month_start_epoch_time,"usageEndTime":month_end_epoch_time}}}
    },
    # Compute Overview CSV
    {
        "name": "Compute Overview CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Compute Overview PDF
    {
        "name": "Compute Overview PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Compute Cluster CSV
    {
        "name": "Compute Cluster CSV",
            "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Compute Cluster PDF
    {
        "name": "Compute Cluster PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Compute Services CSV
    {
        "name": "Compute Services CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Compute Services PDF
    {
        "name": "Compute Services PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Compute Sub-Services CSV
    {
        "name": "Compute Sub-Services CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"subService","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Compute Sub-Services PDF
    {
        "name": "Compute Sub-Services PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"subService","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Compute Cost Center CSV
    {
        "name": "Compute Cost Center CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Compute Cost Center PDF
    {
        "name": "Compute Cost Center PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Compute Resource CSV
    {
        "name": "Compute Resource CSV",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"resource","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"CSV"}}}
    },
    # Compute Resource PDF
    {
        "name": "Compute Resource PDF",
        "payload": {"reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":["00063ffe-e22c-90bf-45a6-7cc25530e846"],"resourceGroupType":"NX_ACCOUNT","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"resource","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":month_end_epoch_time,"usageStartTime":month_start_epoch_time},"reportTemplateDetails":{"fileType":"PDF"}}}
    },
    # Global Chargeback XLS for all BU and CC
    {
        "name": "Global Chargeback XLS for all BU and CC",
        "payload": {"reportConfig":{"reportType":"GLOBAL_CHARGEBACK","dataSource":{"resourceGroupIds":[],"category":"ALLOCATED","resourceGroupType":"ALL_BU_CC","filters":{},"groupBy":"businessUnitsAndCostCenters"},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"startTime":month_start_epoch_time,"endTime":month_end_epoch_time},"reportTemplateDetails":{"fileType":"XLS"}}}
    },
    # Global Chargeback XLS for all BU
    {
        "name": "Global Chargeback XLS for all BU",
        "payload": {"reportConfig":{"reportType":"GLOBAL_CHARGEBACK","dataSource":{"resourceGroupIds":[],"category":"ALLOCATED","resourceGroupType":"ALL_BU","filters":{},"groupBy":"businessUnits"},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"startTime":month_start_epoch_time,"endTime":month_end_epoch_time},"reportTemplateDetails":{"fileType":"XLS"}}}
    },
    # Global Chargeback XLS for all CC
    {
        "name": "Global Chargeback XLS for all CC",
        "payload": {"reportConfig":{"reportType":"GLOBAL_CHARGEBACK","dataSource":{"resourceGroupIds":[],"category":"ALLOCATED","resourceGroupType":"ALL_CC","filters":{},"groupBy":"costCenters"},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"startTime":month_start_epoch_time,"endTime":month_end_epoch_time},"reportTemplateDetails":{"fileType":"XLS"}}}
    },
    # Global Chargeback XLS for all accounts UNALLOCATED
    {
        "name": "Global Chargeback XLS for all accounts UNALLOCATED",
        "payload": {"reportConfig":{"reportType":"GLOBAL_CHARGEBACK","dataSource":{"resourceGroupIds":[],"category":"UNALLOCATED","resourceGroupType":"ALL","filters":{},"groupBy":"accounts"},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"startTime":month_start_epoch_time,"endTime":month_end_epoch_time},"reportTemplateDetails":{"fileType":"XLS"}}}
    },
    # Budget Alerts XLS
    {
        "name": "Budget Alerts XLS"
    }
]
def get_budget_uuid():
    """Get the budget UUID for the current month."""
    response = requests.get(
        f"{NCM_BASE_URL}/v1/cg/budgets/analysis?search=&limit=15&offset=1",
        headers=HEADERS,
        auth=AUTH,
        verify=False,
        timeout=API_TIMEOUT
    )
    return json.loads(response.content)['budgets'][0]['id']


def download_report(report_config, cluster_id, report_num=None, total=None):
    """Download a single report and record metrics."""
    prefix = f"[{report_num}/{total}] " if report_num and total else ""
    start_time = time.time()
    
    try:
        # Prepare payload with deep copy to avoid modifying original
        import copy
        payload = copy.deepcopy(report_config['payload'])
        if 'reportConfig' in payload and 'dataSource' in payload['reportConfig']:
            payload['reportConfig']['dataSource']['resourceGroupIds'] = [cluster_id]
        
        url = REPORTS_URL
        if report_config['name'] == "Budget Alerts XLS":
            budget_uuid = get_budget_uuid()
            url = f"{NCM_BASE_URL}/v1/cg/budgets/{budget_uuid}/report/download"
            url = report_config.get('url')
        
        response = requests.post(
            url,
            json=payload,
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=API_TIMEOUT
        )
        elapsed = time.time() - start_time
        detailed_metrics.record_download_call(elapsed, response.status_code)
        logger.info(f"{prefix}[DOWNLOAD] {report_config['name']} | Cluster: {cluster_id} | Response: {response.status_code} | Time: {elapsed*1000:.2f}ms")
        return response
        
    except Exception as e:
        elapsed = time.time() - start_time
        detailed_metrics.record_download_call(elapsed, error=True)
        logger.error(f"{prefix}[DOWNLOAD] {report_config['name']} | Error: {e} | Time: {elapsed*1000:.2f}ms")
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
            timeout=API_TIMEOUT
        )
        elapsed = time.time() - start_time
        detailed_metrics.record_status_call(elapsed, response.status_code)
        logger.debug(f"{prefix}[STATUS] [dowID:{download_id}] Response: {response.status_code} | Time: {elapsed*1000:.2f}ms")
        return response
        
    except Exception as e:
        elapsed = time.time() - start_time
        detailed_metrics.record_status_call(elapsed, error=True)
        logger.error(f"{prefix}[STATUS] [dowID:{download_id}] Error: {e} | Time: {elapsed*1000:.2f}ms")
        return None


def process_single_report(report_config, cluster_id, report_num, total):
    """
    Process a single report download with status polling.
    Returns (success, download_id, processing_time, status_check_count)
    """
    report_start_time = time.time()
    status_check_count = 0
    download_id = None
    
    logger.info(f"[{report_num}/{total}] Starting: {report_config['name']} | Cluster: {cluster_id}")
    
    # Download report
    response = download_report(report_config, cluster_id, report_num, total)
    
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
        logger.error(f"[{report_num}/{total}] Failed with status {response.status_code}")
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
                logger.debug(f"[{report_num}/{total}] [STATUS CHECK {i+1}/{STATUS_CHECK_MAX_RETRIES}] [dowID:{download_id}] Status: PROCESSING")
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
    Processes all report types for all clusters in parallel batches.
    """
    logger.info("=" * 100)
    logger.info("NCM COST GOVERNANCE REPORTS DOWNLOAD SCRIPT - PARALLEL MODE")
    logger.info("=" * 100)
    logger.info(f"Target URL: {REPORTS_URL}")
    logger.info(f"Batch Size: {PARALLEL_BATCH_SIZE}")
    logger.info(f"Retry Sleep: {PARALLEL_RETRY_SLEEP}s")
    logger.info("=" * 100)
    
    detailed_metrics.start_session()
    
    try:
        # Get cluster list
        cluster_list_response = requests.post(
            f"{NCM_BASE_URL}/v1/cg/nutanix/metering/clusters?limit=500&offset=1",
            json={"timeUnit": "month", "timeRange": {"startTime": 1761955200, "endTime": 1764547140}, "resourceGroupType": "", "resourceGroupIds": [], "currencyType": "TARGET"},
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=API_TIMEOUT
        )
        cluster_list = json.loads(cluster_list_response.content)
        logger.info(f"Fetched cluster list: {len(cluster_list.get('items', [{}]))} clusters")
        cluster_list = [cluster['clusterId'] for cluster in cluster_list['items'][0]['data']]
        
        # Create all report tasks
        # Order tasks so that batches of 3 contain different report types
        # Pattern: Report1-Cluster1, Report2-Cluster1, Report3-Cluster1, Report4-Cluster1, etc.
        all_tasks = []
        task_id = 0
        
        # Calculate how many complete sets of reports we can make
        total_iterations = 1
        for _ in range(total_iterations):
            for report_config in REPORT_PAYLOADS:
                for cluster_id in cluster_list:
                    task_id += 1
                    all_tasks.append((task_id, report_config, cluster_id))
        
        total_tasks = len(all_tasks)
        logger.info(f"Total tasks to process: {total_tasks}")
        logger.info("=" * 100)
        
        completed_count = 0
        batch_num = 0
        
        # Process in batches
        for batch_start in range(0, total_tasks, PARALLEL_BATCH_SIZE):
            batch_num += 1
            batch_end = min(batch_start + PARALLEL_BATCH_SIZE, total_tasks)
            batch_tasks = all_tasks[batch_start:batch_end]
            batch_size = len(batch_tasks)
            
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"BATCH {batch_num} - Processing {batch_size} reports (Completed: {completed_count}/{total_tasks})")
            logger.info("=" * 80)
            
            batch_success = False
            retry_count = 0
            
            while not batch_success and retry_count < PARALLEL_MAX_RETRIES:
                # Run batch in parallel
                results = []
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = {}
                    for task_id, report_config, cluster_id in batch_tasks:
                        future = executor.submit(process_single_report, report_config, cluster_id, task_id, total_tasks)
                        futures[future] = (task_id, report_config['name'], cluster_id)
                    
                    for future in as_completed(futures):
                        task_id, report_name, cluster_id = futures[future]
                        try:
                            result = future.result()
                            results.append((task_id, result))
                        except Exception as e:
                            logger.error(f"[{task_id}/{total_tasks}] Thread exception: {e}")
                            results.append((task_id, (False, None, 0, 0)))
                
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
                    if completed_count < total_tasks:
                        logger.info(f"[BATCH {batch_num}] Sleeping {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE}s before next batch...")
                        time.sleep(SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
                else:
                    retry_count += 1
                    logger.warning(f"[BATCH {batch_num}] ✗ {fail_count} reports failed. Retry #{retry_count}/{PARALLEL_MAX_RETRIES} in {PARALLEL_RETRY_SLEEP}s...")
                    
                    # Log failed reports
                    for task_id, result in results:
                        if not result[0]:
                            download_id = result[1] or "N/A"
                            logger.warning(f"  - Task {task_id} [dowID:{download_id}] FAILED")
                    
                    # Check if we've hit the retry limit
                    if retry_count >= PARALLEL_MAX_RETRIES:
                        logger.error(f"[BATCH {batch_num}] ✗ Maximum retries ({PARALLEL_MAX_RETRIES}) reached. Moving on to next batch...")
                        logger.error(f"[BATCH {batch_num}] ✗ Skipping {fail_count} failed reports, continuing with {success_count} successful reports")
                        completed_count += success_count  # Count only successful reports
                        detailed_metrics.record_batch_completion(retried=True)
                        batch_success = True  # Force exit from retry loop to move to next batch
                        break
                    
                    time.sleep(PARALLEL_RETRY_SLEEP)
        
        # Log batch completion summary
        if retry_count > 0:
            if retry_count >= PARALLEL_MAX_RETRIES:
                logger.warning(f"[BATCH {batch_num}] SUMMARY: Completed with {success_count} successes, {fail_count} failures after {retry_count} retries (MAX REACHED)")
            else:
                logger.info(f"[BATCH {batch_num}] SUMMARY: Completed with all reports successful after {retry_count} retries")
        else:
            logger.info(f"[BATCH {batch_num}] SUMMARY: Completed successfully on first attempt")
    
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
        logger.info(f"Total Completed: {completed_count}")
        logger.info(f"Total Batches: {detailed_metrics.batch_count}")
        logger.info(f"Batch Retries: {detailed_metrics.batch_retries}")
        logger.info(f"Rate Limit Hits (429): {detailed_metrics.rate_limit_hits}")
        logger.info("=" * 100)
        
        # Print detailed API metrics report
        detailed_metrics.print_detailed_report(parallel_mode=True)


def run_sequential_mode():
    """Run downloads sequentially (original behavior with improvements)."""
    logger.info("=" * 100)
    logger.info("NCM COST GOVERNANCE REPORTS DOWNLOAD SCRIPT - SEQUENTIAL MODE")
    logger.info("=" * 100)
    logger.info(f"Target URL: {REPORTS_URL}")
    logger.info(f"Rate Limit: {DOWNLOADS_PER_MINUTE} requests, then sleep {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE}s")
    logger.info(f"Rate Limit Sleep (on 429): {RATE_LIMIT_SLEEP}s")
    logger.info("=" * 100)
    
    detailed_metrics.start_session()
    
    download_count = 0
    sleep_count = 0
    
    try:
        # Get cluster list
        cluster_list_response = requests.post(
            f"{NCM_BASE_URL}/v1/cg/nutanix/metering/clusters?limit=500&offset=1",
            json={"timeUnit": "month", "timeRange": {"startTime": 1761955200, "endTime": 1764547140}, "resourceGroupType": "", "resourceGroupIds": [], "currencyType": "TARGET"},
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=API_TIMEOUT
        )
        cluster_list = json.loads(cluster_list_response.content)
        logger.info(f"Fetched cluster list: {len(cluster_list.get('items', [{}]))} clusters")
        cluster_list = [cluster['clusterId'] for cluster in cluster_list['items'][0]['data']]
        
        # Calculate total reports
        total_reports = len(REPORT_PAYLOADS) * len(cluster_list) * 1  # 100 iterations
        logger.info(f"Total reports to process: {total_reports}")
        logger.info("=" * 100)
        
        report_num = 0
        
        for i in range(1):
            for cluster_id in cluster_list:
                for report_config in REPORT_PAYLOADS:
                    report_num += 1
                    
                    # Rate limiting - sleep after every N downloads
                    if report_num > 1 and (report_num - 1) % DOWNLOADS_PER_MINUTE == 0:
                        logger.info(f"[RATE LIMIT] Sleeping {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE}s after {DOWNLOADS_PER_MINUTE} downloads...")
                        time.sleep(SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
                    
                    logger.info("")
                    logger.info("-" * 60)
                    logger.info(f"REPORT {report_num}/{total_reports}")
                    logger.info(f"Cluster: {cluster_id} | Report: {report_config['name']}")
                    logger.info("-" * 60)
                    
                    # Process single report
                    success, download_id, processing_time, status_check_count = process_single_report(
                        report_config, cluster_id, report_num, total_reports
                    )
                    
                    if success:
                        download_count += 1
                        sleep_count = 0
                        logger.info(f"[REPORT {report_num}/{total_reports}] ✓ SUCCESS | Downloaded: {download_count}")
                    else:
                        if download_id is None:  # Likely rate limited
                            sleep_count += 1
                            logger.warning(f"[RATE LIMITED] Sleep count: {sleep_count}. Sleeping {RATE_LIMIT_SLEEP}s...")
                            time.sleep(RATE_LIMIT_SLEEP)
                            report_num -= 1  # Retry this report
                            continue
                        else:
                            logger.error(f"[REPORT {report_num}/{total_reports}] ✗ FAILED")
                    
                    time.sleep(0.5)  # Small delay between requests

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
        logger.info(f"Total Successful Downloads: {download_count}")
        logger.info(f"Rate Limit Hits (429): {detailed_metrics.rate_limit_hits}")
        logger.info("=" * 100)
        
        # Print detailed API metrics report
        detailed_metrics.print_detailed_report(parallel_mode=False)


def main():
    global PARALLEL_BATCH_SIZE, PARALLEL_RETRY_SLEEP, PARALLEL_MAX_RETRIES
    
    parser = argparse.ArgumentParser(
        description='NCM Cost Governance Reports Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cg_random_reports_download.py                    # Sequential mode (default)
  python cg_random_reports_download.py --parallel         # Parallel mode (3 at once, retry until all succeed)
  python cg_random_reports_download.py --parallel --batch-size 5 --max-retries 5  # Parallel with batch size 5, skip failed batches after 5 retries
        """
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Enable parallel mode: run multiple downloads at once, retry failed batches up to max-retries then move on'
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
        help=f'Maximum retries per batch before skipping failed reports and moving on (default: {PARALLEL_MAX_RETRIES})'
    )
    
    args = parser.parse_args()
    
    # Update global settings if provided
    PARALLEL_BATCH_SIZE = args.batch_size
    PARALLEL_RETRY_SLEEP = args.retry_sleep
    PARALLEL_MAX_RETRIES = args.max_retries
    
    if args.parallel:
        run_parallel_mode()
    else:
        run_sequential_mode()


if __name__ == "__main__":
    main()
