"""
Generic logging utility for all Python scripts.
Creates a logs folder in the same directory as the calling script.
Log file format: scriptname_YYYYMMDD_HHMMSS.log
"""

import os
import sys
import logging
import time
import atexit
from datetime import datetime
from pathlib import Path
from functools import wraps
from collections import defaultdict


class ScriptLogger:
    """
    Generic logger that creates logs in a 'logs' folder relative to the calling script.
    
    Usage:
        from logger_util import get_logger
        
        logger = get_logger(__file__)
        logger.info("This is an info message")
        logger.error("This is an error message")
    """
    
    def __init__(self, script_path, log_level=logging.INFO, include_http_logs=False):
        """
        Initialize logger for the given script.
        
        Args:
            script_path: Path to the calling script (use __file__)
            log_level: Logging level (default: logging.INFO)
            include_http_logs: If True, capture HTTP request/response logs from requests library
        """
        self.script_path = Path(script_path).resolve()
        self.script_dir = self.script_path.parent
        self.script_name = self.script_path.stem  # filename without extension
        
        # Create logs directory in the same folder as the script
        self.logs_dir = self.script_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{self.script_name}_{timestamp}.log"
        self.log_file_path = self.logs_dir / log_filename
        
        # Setup logger
        self.logger = logging.getLogger(self.script_name)
        self.logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler - detailed logs
        file_handler = logging.FileHandler(self.log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler - simplified output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Configure HTTP logging if requested
        if include_http_logs:
            self._setup_http_logging(file_handler, console_handler, log_level)
        
        # Log initialization
        self.logger.info(f"=" * 80)
        self.logger.info(f"Script: {self.script_name}")
        self.logger.info(f"Log file: {self.log_file_path}")
        if include_http_logs:
            self.logger.info(f"HTTP logging: ENABLED")
        self.logger.info(f"=" * 80)
    
    def _setup_http_logging(self, file_handler, console_handler, log_level):
        """Configure logging for HTTP requests (urllib3/requests)."""
        # Enable urllib3 logging (used by requests library)
        urllib3_logger = logging.getLogger('urllib3')
        urllib3_logger.setLevel(logging.DEBUG)
        urllib3_logger.handlers.clear()
        urllib3_logger.addHandler(file_handler)
        # Add console handler only for INFO and above
        urllib3_console = logging.StreamHandler(sys.stdout)
        urllib3_console.setLevel(logging.INFO)
        urllib3_console.setFormatter(logging.Formatter(
            '%(asctime)s - [HTTP] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        urllib3_logger.addHandler(urllib3_console)
        
        # Enable requests logging
        requests_logger = logging.getLogger('requests')
        requests_logger.setLevel(logging.DEBUG)
        requests_logger.handlers.clear()
        requests_logger.addHandler(file_handler)
        
        # Enable http.client logging (low-level HTTP details)
        http_client_logger = logging.getLogger('http.client')
        http_client_logger.setLevel(logging.DEBUG)
        http_client_logger.handlers.clear()
        http_client_logger.addHandler(file_handler)
        
        # Enable HTTPConnection debug logging
        import http.client as http_client_module
        http_client_module.HTTPConnection.debuglevel = 1
    
    def get_logger(self):
        """Return the configured logger instance."""
        return self.logger
    
    def get_log_file_path(self):
        """Return the path to the current log file."""
        return str(self.log_file_path)


def get_logger(script_path, log_level=logging.INFO, include_http_logs=False):
    """
    Convenience function to get a logger for a script.
    
    Args:
        script_path: Path to the calling script (use __file__)
        log_level: Logging level (default: logging.INFO)
        include_http_logs: If True, capture HTTP request/response logs (default: False)
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        from logger_util import get_logger
        
        # Basic usage
        logger = get_logger(__file__)
        logger.info("Script started")
        
        # With HTTP logging
        logger = get_logger(__file__, include_http_logs=True)
        logger.info("Script started")
    """
    script_logger = ScriptLogger(script_path, log_level, include_http_logs)
    return script_logger.get_logger()


def get_logger_with_path(script_path, log_level=logging.INFO, include_http_logs=False):
    """
    Get both logger and log file path.
    
    Args:
        script_path: Path to the calling script (use __file__)
        log_level: Logging level (default: logging.INFO)
        include_http_logs: If True, capture HTTP request/response logs (default: False)
    
    Returns:
        tuple: (logger, log_file_path)
    
    Example:
        from logger_util import get_logger_with_path
        
        logger, log_path = get_logger_with_path(__file__, include_http_logs=True)
        logger.info(f"Logging to: {log_path}")
    """
    script_logger = ScriptLogger(script_path, log_level, include_http_logs)
    return script_logger.get_logger(), script_logger.get_log_file_path()


# ============================================
# API Metrics Tracker
# ============================================

class APIMetrics:
    """
    Tracks API call metrics for generating consolidated reports.
    """
    
    # Status codes considered as success
    SUCCESS_STATUS_CODES = {200, 202}
    
    def __init__(self):
        # Store response times: {(method, endpoint): [times]}
        self.response_times = defaultdict(list)
        # Store status codes: {(method, endpoint): {status_code: count}}
        self.status_codes = defaultdict(lambda: defaultdict(int))
        # Store error counts (exceptions)
        self.errors = defaultdict(int)
        # Store failure counts (non-200/202 responses)
        self.failures = defaultdict(int)
    
    def record(self, method, url, elapsed_time, status_code=None, error=False):
        """Record an API call metric."""
        # Extract endpoint (remove query params and normalize)
        endpoint = self._normalize_url(url)
        key = (method.upper(), endpoint)
        
        self.response_times[key].append(elapsed_time)
        
        if status_code:
            self.status_codes[key][status_code] += 1
            # Track failures (non-200/202)
            if status_code not in self.SUCCESS_STATUS_CODES:
                self.failures[key] += 1
        
        if error:
            self.errors[key] += 1
    
    def _normalize_url(self, url):
        """Normalize URL by removing query parameters and replacing UUIDs."""
        import re
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path
        
        # Replace UUIDs with '{uuid}' placeholder
        # UUID pattern: 8-4-4-4-12 hex characters (with or without dashes)
        uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
        path = re.sub(uuid_pattern, '{uuid}', path)
        
        # Also match UUIDs without dashes (32 hex chars)
        uuid_no_dash_pattern = r'[0-9a-fA-F]{32}'
        path = re.sub(uuid_no_dash_pattern, '{uuid}', path)
        
        # Return just the path (without hostname)
        return path
    
    def _percentile(self, data, percentile):
        """Calculate percentile of a list."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]
    
    def get_report(self):
        """Generate a consolidated report of all API metrics."""
        report_data = []
        
        for key, times in self.response_times.items():
            method, endpoint = key
            
            if not times:
                continue
            
            # Calculate statistics
            count = len(times)
            min_time = min(times) * 1000  # Convert to ms
            max_time = max(times) * 1000
            avg_time = (sum(times) / count) * 1000
            p90 = self._percentile(times, 90) * 1000
            p95 = self._percentile(times, 95) * 1000
            p98 = self._percentile(times, 98) * 1000
            
            # Get status code summary
            status_summary = dict(self.status_codes[key])
            error_count = self.errors[key]
            failure_count = self.failures[key]
            
            report_data.append({
                'method': method,
                'endpoint': endpoint,
                'count': count,
                'min_ms': min_time,
                'max_ms': max_time,
                'avg_ms': avg_time,
                'p90_ms': p90,
                'p95_ms': p95,
                'p98_ms': p98,
                'status_codes': status_summary,
                'errors': error_count,
                'failures': failure_count
            })
        
        # Sort by count (most called first)
        report_data.sort(key=lambda x: x['count'], reverse=True)
        return report_data
    
    def print_report(self, logger):
        """Print a formatted report table."""
        report = self.get_report()
        
        if not report:
            logger.info("No API calls recorded.")
            return
        
        logger.info("")
        logger.info("=" * 160)
        logger.info("API METRICS CONSOLIDATED REPORT")
        logger.info("=" * 160)
        
        # Header
        header = f"{'Method':<8} | {'Endpoint':<50} | {'Count':>7} | {'Fail':>6} | {'Min(ms)':>10} | {'Max(ms)':>10} | {'P90(ms)':>10} | {'P95(ms)':>10} | {'P98(ms)':>10}"
        logger.info(header)
        logger.info("-" * 160)
        
        # Data rows
        for row in report:
            endpoint_display = row['endpoint'][:48] + '..' if len(row['endpoint']) > 50 else row['endpoint']
            failure_display = str(row['failures']) if row['failures'] > 0 else "-"
            
            line = f"{row['method']:<8} | {endpoint_display:<50} | {row['count']:>7} | {failure_display:>6} | {row['min_ms']:>10.2f} | {row['max_ms']:>10.2f} | {row['p90_ms']:>10.2f} | {row['p95_ms']:>10.2f} | {row['p98_ms']:>10.2f}"
            logger.info(line)
        
        logger.info("-" * 160)
        
        # Summary
        total_calls = sum(r['count'] for r in report)
        total_endpoints = len(report)
        total_failures = sum(r['failures'] for r in report)
        total_errors = sum(r['errors'] for r in report)
        logger.info(f"Total API Calls: {total_calls} | Unique Endpoints: {total_endpoints} | Total Failures (non-200/202): {total_failures} | Exceptions: {total_errors}")
        logger.info("=" * 160)
        
        # Failures breakdown (only if there are failures)
        failed_endpoints = [r for r in report if r['failures'] > 0]
        if failed_endpoints:
            logger.info("")
            logger.info("FAILED REQUESTS (non-200/202):")
            logger.info("-" * 100)
            logger.info(f"{'Method':<8} | {'Endpoint':<50} | {'Failures':>10} | {'Status Codes':<30}")
            logger.info("-" * 100)
            for row in failed_endpoints:
                endpoint_display = row['endpoint'][:48] + '..' if len(row['endpoint']) > 50 else row['endpoint']
                # Show only non-success status codes
                failed_codes = {code: count for code, count in row['status_codes'].items() if code not in self.SUCCESS_STATUS_CODES}
                status_str = ", ".join([f"{code}: {count}" for code, count in sorted(failed_codes.items())])
                logger.info(f"{row['method']:<8} | {endpoint_display:<50} | {row['failures']:>10} | {status_str:<30}")
            logger.info("=" * 100)
        
        # Status code breakdown
        logger.info("")
        logger.info("STATUS CODE BREAKDOWN:")
        logger.info("-" * 100)
        for row in report:
            if row['status_codes']:
                status_str = ", ".join([f"{code}: {count}" for code, count in sorted(row['status_codes'].items())])
                endpoint_display = row['endpoint'][:40] + '..' if len(row['endpoint']) > 40 else row['endpoint']
                logger.info(f"{row['method']:<6} {endpoint_display:<42} | {status_str}")
        logger.info("=" * 160)


# ============================================
# HTTP Request Logging Wrapper
# ============================================

class LoggedRequests:
    """
    Wrapper for requests library that automatically logs all HTTP calls.
    
    Usage:
        from logger_util import get_logger, LoggedRequests
        
        logger = get_logger(__file__)
        requests = LoggedRequests(logger)
        
        # Use it exactly like the requests library
        response = requests.get(url, headers=headers)
        response = requests.post(url, data=data, headers=headers)
        
        # Print consolidated report at the end
        requests.print_report()
    """
    
    def __init__(self, logger):
        """
        Initialize the logged requests wrapper.
        
        Args:
            logger: Logger instance from get_logger()
        """
        self.logger = logger
        self.metrics = APIMetrics()
        
        try:
            import requests
            self._requests = requests
        except ImportError:
            self.logger.error("requests library not installed. Install with: pip install requests")
            raise
        
        # Register atexit handler to print report on script exit
        atexit.register(self._print_report_on_exit)
    
    def _print_report_on_exit(self):
        """Print the API metrics report when script exits."""
        self.print_report()
    
    def print_report(self):
        """Print the consolidated API metrics report."""
        self.metrics.print_report(self.logger)
    
    def get_metrics(self):
        """Get the raw metrics data."""
        return self.metrics.get_report()
    
    def _log_request(self, method, url, **kwargs):
        """Log and execute an HTTP request."""
        import json
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"[API REQUEST] {method.upper()} {url}")
        
        # Log request payload
        self._log_request_payload(kwargs)
        
        try:
            # Make the actual request
            response = getattr(self._requests, method.lower())(url, **kwargs)
            
            # Calculate time taken
            elapsed_time = time.time() - start_time
            
            # Record metrics
            self.metrics.record(method, url, elapsed_time, response.status_code)
            
            # Log the response
            self.logger.info(f"[API RESPONSE] {method.upper()} {url}")
            self.logger.info(f"[STATUS CODE] {response.status_code}")
            self.logger.info(f"[TIME TAKEN] {elapsed_time:.4f} seconds ({elapsed_time * 1000:.2f} ms)")
            
            # Log response payload
            self._log_response_payload(response)
            
            return response
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            
            # Record error metrics
            self.metrics.record(method, url, elapsed_time, error=True)
            
            self.logger.error(f"[API ERROR] {method.upper()} {url}")
            self.logger.error(f"[ERROR MESSAGE] {str(e)}")
            self.logger.error(f"[TIME TAKEN] {elapsed_time:.4f} seconds ({elapsed_time * 1000:.2f} ms)")
            raise
    
    def _log_request_payload(self, kwargs):
        """Log the request payload (data, json, params)."""
        import json
        
        # Log query parameters
        if 'params' in kwargs and kwargs['params']:
            try:
                params_str = json.dumps(kwargs['params'], indent=2, default=str)
                self.logger.info(f"[REQUEST PARAMS]\n{params_str}")
            except:
                self.logger.info(f"[REQUEST PARAMS] {kwargs['params']}")
        
        # Log JSON payload
        if 'json' in kwargs and kwargs['json']:
            try:
                json_str = json.dumps(kwargs['json'], indent=2, default=str)
                self.logger.info(f"[REQUEST JSON PAYLOAD]\n{json_str}")
            except:
                self.logger.info(f"[REQUEST JSON PAYLOAD] {kwargs['json']}")
        
        # Log form data
        if 'data' in kwargs and kwargs['data']:
            try:
                if isinstance(kwargs['data'], dict):
                    data_str = json.dumps(kwargs['data'], indent=2, default=str)
                    self.logger.info(f"[REQUEST DATA PAYLOAD]\n{data_str}")
                else:
                    # Truncate if too long
                    data_preview = str(kwargs['data'])[:1000]
                    if len(str(kwargs['data'])) > 1000:
                        data_preview += "... (truncated)"
                    self.logger.info(f"[REQUEST DATA PAYLOAD] {data_preview}")
            except:
                self.logger.info(f"[REQUEST DATA PAYLOAD] {kwargs['data']}")
        
        # Log files (just indicate presence, not content)
        if 'files' in kwargs and kwargs['files']:
            file_names = list(kwargs['files'].keys()) if isinstance(kwargs['files'], dict) else "files attached"
            self.logger.info(f"[REQUEST FILES] {file_names}")
    
    def _log_response_payload(self, response):
        """Log the response payload."""
        import json
        
        # Log response headers (content-type)
        content_type = response.headers.get('Content-Type', '')
        self.logger.info(f"[RESPONSE CONTENT-TYPE] {content_type}")
        
        # Try to log response body
        try:
            if 'application/json' in content_type:
                # JSON response
                response_json = response.json()
                json_str = json.dumps(response_json, indent=2, default=str)
                # Truncate if too long
                if len(json_str) > 2000:
                    json_str = json_str[:2000] + "\n... (truncated)"
                self.logger.info(f"[RESPONSE PAYLOAD]\n{json_str}")
            else:
                # Non-JSON response - log first 1000 chars
                response_text = response.text[:1000]
                if len(response.text) > 1000:
                    response_text += "... (truncated)"
                if response_text.strip():
                    self.logger.info(f"[RESPONSE PAYLOAD] {response_text}")
        except Exception as e:
            self.logger.debug(f"[RESPONSE PAYLOAD] Could not parse response: {str(e)}")
    
    def get(self, url, **kwargs):
        """HTTP GET request with logging."""
        return self._log_request('get', url, **kwargs)
    
    def post(self, url, **kwargs):
        """HTTP POST request with logging."""
        return self._log_request('post', url, **kwargs)
    
    def put(self, url, **kwargs):
        """HTTP PUT request with logging."""
        return self._log_request('put', url, **kwargs)
    
    def patch(self, url, **kwargs):
        """HTTP PATCH request with logging."""
        return self._log_request('patch', url, **kwargs)
    
    def delete(self, url, **kwargs):
        """HTTP DELETE request with logging."""
        return self._log_request('delete', url, **kwargs)
    
    def head(self, url, **kwargs):
        """HTTP HEAD request with logging."""
        return self._log_request('head', url, **kwargs)
    
    def options(self, url, **kwargs):
        """HTTP OPTIONS request with logging."""
        return self._log_request('options', url, **kwargs)
