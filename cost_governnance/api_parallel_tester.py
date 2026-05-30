#!/usr/bin/env python3
"""
NCM Cost Governance API Parallel Tester
Tests multiple APIs in parallel with configurable options for same API or different APIs
Supports 5 parallel workers with detailed metrics tracking
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
import random

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
NCM_BASE_URL = "https://ncm.services.nconprem-10-53-55-30.ccpnx.com"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}
API_TIMEOUT = 300
PARALLEL_WORKERS = 5

# Thread-safe lock for metrics
metrics_lock = threading.Lock()

# Comprehensive API List from Cost Governance Scripts
API_ENDPOINTS = {
    # Reports APIs
    "reports_download": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/reports/download",
        "payload": {
            "reportConfig": {
                "reportType": "GLOBAL_CHARGEBACK",
                "dataSource": {
                    "resourceGroupIds": [],
                    "category": "ALLOCATED",
                    "resourceGroupType": "ALL_BU_CC",
                    "filters": {},
                    "groupBy": "businessUnitsAndCostCenters"
                },
                "reportPeriod": {"timeUnit": "CUSTOM"},
                "timeRange": {"startTime": 1767225600, "endTime": 1769903999},
                "reportTemplateDetails": {"fileType": "XLS"}
            }
        }
    },
    "reports_status": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/reports/download/status",
        "params": {"downloadId": "DOW123"}  # Will be replaced with actual ID
    },
    "reports_share": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/reports/share",
        "payload": {
            "reportConfig": {
                "reportType": "GLOBAL_CHARGEBACK",
                "dataSource": {
                    "resourceGroupIds": [],
                    "category": "ALLOCATED",
                    "resourceGroupType": "ALL_BU_CC",
                    "filters": {},
                    "groupBy": "businessUnitsAndCostCenters"
                },
                "reportPeriod": {"timeUnit": "CUSTOM"},
                "timeRange": {"startTime": 1767225600, "endTime": 1769903999},
                "reportTemplateDetails": {"fileType": "XLS"}
            }
        }
    },
    
    # Budget APIs
    "budgets_list_resource_groups": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/global/budgets/listResourceGroups"
    },
    "budgets_analysis": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/budgets/analysis",
        "params": {"search": "", "limit": 15, "offset": 1}
    },
    "budgets_create": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/cg/global/budgets",
        "payload": {
            "budgetName": "test_budget",
            "financialYearStartMonth": "2",
            "resourceGroups": {},
            "systemEstimate": True,
            "budgetAlert": {
                "configuration": {
                    "monthly": [{"thresholdPercent": 70, "isDisabled": False}],
                    "quarterly": [{"thresholdPercent": 80, "isDisabled": False}],
                    "yearly": [{"thresholdPercent": 90, "isDisabled": False}]
                },
                "recipients": [],
                "isDisabled": False
            }
        }
    },
    "budget_report_download": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/cg/budgets/{{budget_uuid}}/report/download"
    },
    
    # Cost Center APIs
    "cost_centers_list": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/global/costCenters",
        "params": {"limit": 100, "offset": 0}
    },
    "cost_center_create": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/cg/global/costCenter",
        "payload": {
            "name": "test_cost_center",
            "description": "Test cost center",
            "resourceGroups": []
        }
    },
    
    # Business Unit APIs
    "business_unit_create": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/cg/global/businessUnit",
        "payload": {
            "name": "test_business_unit",
            "description": "Test business unit",
            "costCenters": []
        }
    },
    
    # Chargeback APIs
    "chargeback_configuration": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/global/chargeback/configuration"
    },
    "chargeback_available_accounts": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/global/chargeback/availableAccounts"
    },
    "chargeback_upload_config": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/cg/global/chargeback/uploadConfiguration"
    },
    "chargeback_get_upload_config": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/global/chargeback/getAllUploadConfig"
    },
    
    # Metering APIs
    "metering_clusters": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/cg/nutanix/metering/clusters",
        "params": {"limit": 500, "offset": 1},
        "payload": {
            "timeUnit": "month",
            "timeRange": {"startTime": 1761955200, "endTime": 1764547140},
            "resourceGroupType": "",
            "resourceGroupIds": [],
            "currencyType": "TARGET"
        }
    },
    
    # Analysis APIs
    "analysis_dimensions_values": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/nx/analysis/dimensions/values",
        "params": {
            "resourceGroupIds": "test-uuid",
            "dimensions": "tagKeys",
            "resourceGroupType": "billingAccount"
        }
    },
    
    # Rate Cards APIs
    "rate_cards_list": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/config/rate-cards"
    },
    "rate_cards_download": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/config/rate-cards/actions/download",
        "params": {"cloud": "Nutanix"}
    },
    
    # TCO APIs
    "tco_purchases": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/config/tco/purchases"
    },
    "tco_configs": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/v1/cg/config/tco/configs",
        "params": {"limit": 100, "offset": 0, "costHeadAction": "direct"},
        "payload": {"filters": []}
    },
    
    # User APIs
    "users_list": {
        "method": "GET",
        "url": f"{NCM_BASE_URL}/v1/cg/users/list"
    },
    
    # Nutanix v3 APIs
    "accounts_list": {
        "method": "POST",
        "url": f"{NCM_BASE_URL}/api/nutanix/v3/accounts/list",
        "payload": {}
    }
}


class APIMetrics:
    """Thread-safe API metrics tracker for parallel testing."""
    
    def __init__(self):
        self.api_times = defaultdict(list)  # API name -> list of response times
        self.api_status_codes = defaultdict(lambda: defaultdict(int))  # API name -> status code -> count
        self.api_errors = defaultdict(int)  # API name -> error count
        self.successful_calls = defaultdict(int)  # API name -> success count
        self.failed_calls = defaultdict(int)  # API name -> failure count
        self.download_durations = defaultdict(list)  # API name -> list of download durations (for report APIs)
        self.status_check_counts = defaultdict(list)  # API name -> list of status check counts
        self.rate_limit_hits = defaultdict(int)  # API name -> rate limit count
        self.start_time = None
        self.end_time = None
        self.total_calls = 0
    
    def start_session(self):
        """Mark the start of the testing session."""
        self.start_time = datetime.now()
        logger.info(f"API Testing Session started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def end_session(self):
        """Mark the end of the testing session."""
        self.end_time = datetime.now()
        logger.info(f"API Testing Session ended at: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def record_api_call(self, api_name, elapsed_time, status_code=None, error=False, download_duration=None, status_checks=None):
        """Record metrics for an API call (thread-safe)."""
        with metrics_lock:
            self.total_calls += 1
            self.api_times[api_name].append(elapsed_time)
            if status_code:
                self.api_status_codes[api_name][status_code] += 1
                if status_code == 429:
                    self.rate_limit_hits[api_name] += 1
                if status_code in [200, 201, 202, 204]:
                    self.successful_calls[api_name] += 1
                else:
                    self.failed_calls[api_name] += 1
            if error:
                self.api_errors[api_name] += 1
                self.failed_calls[api_name] += 1
            if download_duration is not None:
                self.download_durations[api_name].append(download_duration)
            if status_checks is not None:
                self.status_check_counts[api_name].append(status_checks)
    
    def _calculate_stats(self, data):
        """Calculate comprehensive statistics for a dataset."""
        if not data:
            return {'count': 0, 'min': 0, 'max': 0, 'avg': 0, 'median': 0, 'p90': 0, 'p95': 0, 'p99': 0}
        
        sorted_data = sorted(data)
        return {
            'count': len(data),
            'min': min(data),
            'max': max(data),
            'avg': sum(data) / len(data),
            'median': statistics.median(data),
            'p90': sorted_data[int(len(data) * 0.9)] if data else 0,
            'p95': sorted_data[int(len(data) * 0.95)] if data else 0,
            'p99': sorted_data[int(len(data) * 0.99)] if data else 0
        }
    
    def print_detailed_report(self):
        """Print comprehensive API testing metrics report."""
        logger.info("")
        logger.info("=" * 120)
        logger.info("API PARALLEL TESTING METRICS REPORT")
        logger.info("=" * 120)
        
        # Session Duration
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            logger.info(f"Session Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
            logger.info(f"Total API Calls: {self.total_calls}")
            if duration > 0:
                logger.info(f"Calls per Second: {self.total_calls / duration:.2f}")
        
        # Per-API Metrics
        for api_name in sorted(self.api_times.keys()):
            logger.info("")
            logger.info("-" * 80)
            logger.info(f"API: {api_name.upper()}")
            logger.info("-" * 80)
            
            # Response Times
            times_ms = [t * 1000 for t in self.api_times[api_name]]
            stats = self._calculate_stats(times_ms)
            logger.info(f"Response Times (ms): Count: {stats['count']} | Avg: {stats['avg']:.2f} | P90: {stats['p90']:.2f} | P95: {stats['p95']:.2f}")
            
            # Status Codes
            logger.info("Status Codes:")
            for code, count in sorted(self.api_status_codes[api_name].items()):
                total_calls = sum(self.api_status_codes[api_name].values())
                percentage = (count / total_calls * 100) if total_calls > 0 else 0
                status_emoji = "✓" if code in [200, 201, 202, 204] else "✗"
                logger.info(f"  {status_emoji} {code}: {count} ({percentage:.1f}%)")
            
            # Success/Failure Summary
            success_count = self.successful_calls[api_name]
            failure_count = self.failed_calls[api_name]
            error_count = self.api_errors[api_name]
            total_attempts = success_count + failure_count
            success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 0
            
            logger.info(f"Success Rate: {success_count}/{total_attempts} ({success_rate:.1f}%)")
            if error_count > 0:
                logger.info(f"⚠ Errors: {error_count}")
            if self.rate_limit_hits[api_name] > 0:
                logger.info(f"⚠ Rate Limited (429): {self.rate_limit_hits[api_name]}")
            
            # Report-specific metrics
            if api_name in ["reports_download", "reports_share"] and self.download_durations[api_name]:
                duration_stats = self._calculate_stats(self.download_durations[api_name])
                logger.info(f"Download Duration (s): Avg: {duration_stats['avg']:.2f} | P90: {duration_stats['p90']:.2f} | P95: {duration_stats['p95']:.2f}")
                
            if self.status_check_counts[api_name]:
                check_stats = self._calculate_stats(self.status_check_counts[api_name])
                logger.info(f"Status Checks: Avg: {check_stats['avg']:.1f} | Max: {check_stats['max']:.0f}")
        
        logger.info("")
        logger.info("=" * 120)


# Initialize metrics tracker
api_metrics = APIMetrics()


def check_report_status(download_id, call_id, max_retries=20, check_interval=30):
    """Check report status with polling similar to cc_reports_download.py"""
    status_url = f"{NCM_BASE_URL}/v1/reports/download/status?downloadId={download_id}"
    
    for i in range(max_retries):
        try:
            start_time = time.time()
            response = requests.get(
                status_url,
                headers=HEADERS,
                auth=AUTH,
                verify=False,
                timeout=API_TIMEOUT
            )
            elapsed = time.time() - start_time
            
            logger.info(f"[{call_id}] [STATUS CHECK {i+1}/{max_retries}] [dowID:{download_id}] Response: {response.status_code} | Time: {elapsed*1000:.2f}ms")
            
            if response.status_code != 200:
                logger.warning(f"[{call_id}] [STATUS CHECK {i+1}/{max_retries}] [dowID:{download_id}] Non-200 status: {response.status_code}")
                time.sleep(check_interval)
                continue
            
            status_json = response.json()
            status = status_json.get('status', 'UNKNOWN')
            
            if status in ['PROCESSING', 'NEW']:
                logger.info(f"[{call_id}] [STATUS CHECK {i+1}/{max_retries}] [dowID:{download_id}] Status: {status}, waiting {check_interval}s...")
                time.sleep(check_interval)
                continue
            elif status == 'COMPLETED':
                logger.info(f"[{call_id}] [STATUS CHECK {i+1}/{max_retries}] [dowID:{download_id}] ✓ Status: COMPLETED")
                return (True, i + 1)  # Return success and number of status checks
            elif status == 'FAILED':
                logger.error(f"[{call_id}] [STATUS CHECK {i+1}/{max_retries}] [dowID:{download_id}] ✗ Status: FAILED")
                return (False, i + 1)
            else:
                logger.warning(f"[{call_id}] [STATUS CHECK {i+1}/{max_retries}] [dowID:{download_id}] Unknown status: {status}")
                time.sleep(check_interval)
                
        except Exception as e:
            logger.error(f"[{call_id}] [STATUS CHECK {i+1}/{max_retries}] [dowID:{download_id}] Error: {e}")
            time.sleep(check_interval)
    
    logger.error(f"[{call_id}] [dowID:{download_id}] ✗ Status check timeout after {max_retries} attempts")
    return (False, max_retries)


def make_api_call(api_name, api_config, call_id):
    """Make a single API call and record metrics."""
    start_time = time.time()
    
    try:
        # Prepare request parameters
        method = api_config["method"]
        url = api_config["url"]
        
        # Handle URL templating (e.g., budget_uuid)
        if "{{" in url and "}}" in url:
            # For now, skip templated URLs that need dynamic values
            logger.warning(f"[{call_id}] Skipping templated URL: {api_name}")
            return (False, "Templated URL", 0)
        
        kwargs = {
            'headers': HEADERS,
            'auth': AUTH,
            'verify': False,
            'timeout': API_TIMEOUT
        }
        
        # Add payload for POST requests
        if method == "POST" and "payload" in api_config:
            kwargs['json'] = api_config["payload"]
        
        # Add query parameters
        if "params" in api_config:
            kwargs['params'] = api_config["params"]
        
        # Make the API call
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, **kwargs)
        else:
            logger.error(f"[{call_id}] Unsupported method: {method}")
            return (False, "Unsupported method", 0)
        
        elapsed = time.time() - start_time
        api_metrics.record_api_call(api_name, elapsed, response.status_code)
        
        # Handle report download APIs specially
        if api_name in ["reports_download", "reports_share"] and response.status_code in [200, 202]:
            try:
                response_json = response.json()
                download_id = response_json.get('id')
                
                if download_id:
                    logger.info(f"[{call_id}] {api_name} | {method} | Status: {response.status_code} | Time: {elapsed*1000:.2f}ms | [dowID:{download_id}] Download initiated")
                    
                    # Track download start time for duration calculation
                    download_start_time = time.time()
                    
                    # Poll for status
                    status_success, status_checks = check_report_status(download_id, call_id)
                    
                    if status_success:
                        download_duration = time.time() - download_start_time
                        total_time = time.time() - start_time
                        # Record additional metrics for successful downloads
                        api_metrics.record_api_call(api_name, 0, None, False, download_duration, status_checks)
                        logger.info(f"[{call_id}] {api_name} | [dowID:{download_id}] ✓ Completed in {total_time:.2f}s ({status_checks} status checks) (download took {download_duration:.2f}s)")
                        return (True, response.status_code, total_time)
                    else:
                        total_time = time.time() - start_time
                        # Record status check count even for failed downloads
                        api_metrics.record_api_call(api_name, 0, None, False, None, status_checks)
                        logger.error(f"[{call_id}] {api_name} | [dowID:{download_id}] ✗ Failed after {total_time:.2f}s ({status_checks} status checks)")
                        return (False, response.status_code, total_time)
                else:
                    logger.warning(f"[{call_id}] {api_name} | No download ID in response")
                    logger.info(f"[{call_id}] {api_name} | {method} | Status: {response.status_code} | Time: {elapsed*1000:.2f}ms")
                    return (response.status_code in [200, 201, 202, 204], response.status_code, elapsed)
                    
            except Exception as e:
                logger.error(f"[{call_id}] {api_name} | Failed to parse download response: {e}")
                logger.info(f"[{call_id}] {api_name} | {method} | Status: {response.status_code} | Time: {elapsed*1000:.2f}ms")
                return (False, response.status_code, elapsed)
        
        # Handle rate limiting (429)
        elif response.status_code == 429:
            logger.warning(f"[{call_id}] {api_name} | {method} | Status: {response.status_code} (Rate Limited) | Time: {elapsed*1000:.2f}ms")
            # For rate limiting, we could implement backoff, but for now just mark as failed
            return (False, response.status_code, elapsed)
        
        # Regular API call handling
        else:
            logger.info(f"[{call_id}] {api_name} | {method} | Status: {response.status_code} | Time: {elapsed*1000:.2f}ms")
            return (response.status_code in [200, 201, 202, 204], response.status_code, elapsed)
        
    except Exception as e:
        elapsed = time.time() - start_time
        api_metrics.record_api_call(api_name, elapsed, error=True)
        logger.error(f"[{call_id}] {api_name} | Error: {e} | Time: {elapsed*1000:.2f}ms")
        return (False, str(e), elapsed)


def run_parallel_api_test(mode, iterations=None, duration=None, api_iterations=1, api_list=None):
    """
    Run parallel API testing.
    
    Args:
        mode: "same" or "different" - whether all workers use same API or different APIs
        iterations: Number of iterations to run (None if using duration)
        duration: Duration in seconds to run (None if using iterations)
        api_iterations: Number of times to test each API within each iteration
        api_list: List of API names to test (None for all)
    """
    logger.info("=" * 100)
    logger.info("NCM COST GOVERNANCE API PARALLEL TESTER")
    logger.info("=" * 100)
    logger.info(f"Mode: {mode.upper()}")
    logger.info(f"Parallel Workers: {PARALLEL_WORKERS}")
    logger.info(f"API Iterations per Loop: {api_iterations}")
    if duration:
        logger.info(f"Duration: {duration} seconds ({duration/60:.1f} minutes)")
    else:
        logger.info(f"Iterations: {iterations}")
    logger.info("=" * 100)
    
    api_metrics.start_session()
    
    # Filter APIs if specific list provided
    if api_list:
        available_apis = {k: v for k, v in API_ENDPOINTS.items() if k in api_list}
    else:
        available_apis = API_ENDPOINTS
    
    if not available_apis:
        logger.error("No valid APIs found to test!")
        return
    
    logger.info(f"Testing {len(available_apis)} APIs: {list(available_apis.keys())}")
    
    try:
        completed_calls = 0
        iteration = 0
        
        # Determine when to stop
        if duration:
            end_time = time.time() + duration
            logger.info(f"Running for {duration} seconds until {datetime.fromtimestamp(end_time).strftime('%H:%M:%S')}")
        else:
            end_time = None
        
        while True:
            iteration += 1
            
            # Check stopping condition
            if duration:
                if time.time() >= end_time:
                    logger.info(f"Duration of {duration} seconds reached. Stopping...")
                    break
                logger.info("")
                logger.info("=" * 80)
                remaining_time = end_time - time.time()
                logger.info(f"ITERATION {iteration} | Remaining: {remaining_time:.1f}s")
                logger.info("=" * 80)
            else:
                if iteration > iterations:
                    logger.info(f"Completed {iterations} iterations. Stopping...")
                    break
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"ITERATION {iteration}/{iterations}")
                logger.info("=" * 80)
            
            # Prepare tasks for this iteration with API iterations
            tasks = []
            
            if mode == "same":
                # All workers use the same API (randomly selected for each iteration)
                selected_api = random.choice(list(available_apis.keys()))
                logger.info(f"All workers will test: {selected_api} ({api_iterations} times each)")
                
                for worker_id in range(PARALLEL_WORKERS):
                    for api_iter in range(api_iterations):
                        call_id = f"I{iteration}-W{worker_id+1}-A{api_iter+1}"
                        tasks.append((selected_api, available_apis[selected_api], call_id))
            
            else:  # mode == "different"
                # Each worker uses different APIs, cycling through available APIs
                api_names = list(available_apis.keys())
                logger.info(f"Workers will test different APIs ({api_iterations} times each)")
                
                for worker_id in range(PARALLEL_WORKERS):
                    for api_iter in range(api_iterations):
                        # Cycle through APIs for each worker and API iteration
                        api_index = (worker_id * api_iterations + api_iter) % len(api_names)
                        selected_api = api_names[api_index]
                        call_id = f"I{iteration}-W{worker_id+1}-A{api_iter+1}"
                        tasks.append((selected_api, available_apis[selected_api], call_id))
            
            # Execute tasks in parallel (now with API iterations)
            total_tasks = len(tasks)
            logger.info(f"Executing {total_tasks} API calls in parallel...")
            results = []
            with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
                futures = {}
                for api_name, api_config, call_id in tasks:
                    future = executor.submit(make_api_call, api_name, api_config, call_id)
                    futures[future] = (api_name, call_id)
                
                for future in as_completed(futures):
                    api_name, call_id = futures[future]
                    try:
                        result = future.result()
                        results.append((call_id, api_name, result))
                    except Exception as e:
                        logger.error(f"[{call_id}] Thread exception: {e}")
                        results.append((call_id, api_name, (False, str(e), 0)))
            
            # Log iteration results
            success_count = sum(1 for _, _, (success, _, _) in results if success)
            total_calls_this_iteration = len(results)
            logger.info(f"[ITERATION {iteration}] Results: {success_count}/{total_calls_this_iteration} API calls succeeded")
            
            completed_calls += len(results)
            
            # Check if we should continue (for duration mode)
            if duration and time.time() >= end_time:
                logger.info("Duration reached during iteration. Stopping...")
                break
            
            # Sleep between iterations (but not if we're about to stop)
            should_continue = True
            if duration:
                should_continue = time.time() < end_time - 2  # Don't sleep if less than 2s remaining
            else:
                should_continue = iteration < iterations
            
            if should_continue:
                logger.info("Sleeping 2s before next iteration...")
                time.sleep(2)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Testing interrupted by user (Ctrl+C)")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        api_metrics.end_session()
        
        # Print summary
        logger.info("")
        logger.info("=" * 100)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 100)
        logger.info(f"Total API Calls Completed: {completed_calls}")
        logger.info(f"Total Iterations Completed: {iteration - 1}")  # Subtract 1 because iteration is incremented before the break
        if duration:
            actual_duration = (api_metrics.end_time - api_metrics.start_time).total_seconds()
            logger.info(f"Requested Duration: {duration}s | Actual Duration: {actual_duration:.1f}s")
        logger.info("=" * 100)
        
        # Print detailed API metrics report
        api_metrics.print_detailed_report()


def main():
    parser = argparse.ArgumentParser(
        description='NCM Cost Governance API Parallel Tester',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cost_governnance/api_parallel_tester.py --mode same --iterations 10
  python3 cost_governnance/api_parallel_tester.py --mode different --iterations 5
  python3 cost_governnance/api_parallel_tester.py --mode same --duration 300  # Run for 5 minutes
  python3 cost_governnance/api_parallel_tester.py --mode different --duration 60 --apis reports_download,budgets_analysis
  python3 cost_governnance/api_parallel_tester.py --mode same --iterations 5 --api-iterations 3  # Each API tested 3 times per iteration
        """
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['same', 'different'],
        default='different',
        help='Test mode: "same" (all workers use same API) or "different" (each worker uses different API)'
    )
    parser.add_argument(
        '--iterations', '-i',
        type=int,
        help='Number of iterations to run (default: 5 if no duration specified)'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        help='Duration in seconds to run the test (alternative to iterations)'
    )
    parser.add_argument(
        '--api-iterations', '-ai',
        type=int,
        default=1,
        help='Number of times to test each API within each iteration (default: 1)'
    )
    parser.add_argument(
        '--apis', '-a',
        type=str,
        help='Comma-separated list of specific APIs to test (default: all APIs)'
    )
    parser.add_argument(
        '--list-apis', '-l',
        action='store_true',
        help='List all available APIs and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_apis:
        logger.info("Available APIs:")
        for api_name, api_config in API_ENDPOINTS.items():
            method = api_config["method"]
            url = api_config["url"]
            logger.info(f"  {api_name}: {method} {url}")
        return
    
    # Validate arguments
    if args.duration and args.iterations:
        logger.error("Cannot specify both --duration and --iterations. Choose one.")
        return
    
    if not args.duration and not args.iterations:
        args.iterations = 5  # Default value
    
    # Parse API list if provided
    api_list = None
    if args.apis:
        api_list = [api.strip() for api in args.apis.split(',')]
        invalid_apis = [api for api in api_list if api not in API_ENDPOINTS]
        if invalid_apis:
            logger.error(f"Invalid APIs specified: {invalid_apis}")
            logger.info(f"Available APIs: {list(API_ENDPOINTS.keys())}")
            return
    
    run_parallel_api_test(args.mode, args.iterations, args.duration, args.api_iterations, api_list)


if __name__ == "__main__":
    main()
