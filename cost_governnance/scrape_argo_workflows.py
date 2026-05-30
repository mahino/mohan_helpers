#!/usr/bin/env python3
"""
Fetch Argo Workflows data using the Argo API
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

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
ARGO_BASE_URL = "http://10.53.60.167:30325"
NAMESPACE = "ncm-cg"
WORKFLOWS_API = f"{ARGO_BASE_URL}/api/v1/workflows/{NAMESPACE}"


def parse_duration(start_str, end_str):
    """Parse start and end time strings and calculate duration in seconds"""
    try:
        if not start_str or not end_str:
            return None
        
        # Parse ISO format timestamps
        start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        
        duration = (end_time - start_time).total_seconds()
        return duration if duration >= 0 else None
    except Exception as e:
        logger.debug(f"Error parsing duration: {e}")
        return None


def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds is None:
        return "N/A"
    
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


def percentile(sorted_data, p):
    """Calculate percentile from sorted data"""
    if not sorted_data:
        return 0
    index = int(len(sorted_data) * p / 100)
    index = min(index, len(sorted_data) - 1)
    return sorted_data[index]


def calculate_workflow_timings(workflows):
    """Calculate timing statistics for each workflow type"""
    # Group workflows by type (labels or name pattern)
    type_timings = defaultdict(list)
    
    for wf in workflows:
        metadata = wf.get('metadata', {})
        status = wf.get('status', {})
        
        # Get workflow type from labels or name
        labels = metadata.get('labels', {})
        workflow_type = labels.get('workflows.argoproj.io/workflow-template', 
                        labels.get('app', 
                        metadata.get('generateName', 'Unknown').rstrip('-')))
        
        started = status.get('startedAt', '')
        finished = status.get('finishedAt', '')
        
        duration = parse_duration(started, finished)
        if duration is not None:
            type_timings[workflow_type].append({
                'duration': duration,
                'name': metadata.get('name', ''),
                'phase': status.get('phase', ''),
                'started': started,
                'finished': finished
            })
    
    # Calculate statistics for each type
    timing_stats = {}
    
    for wf_type, entries in type_timings.items():
        durations = [e['duration'] for e in entries]
        if not durations:
            continue
        
        sorted_durations = sorted(durations)
        count = len(durations)
        
        timing_stats[wf_type] = {
            'count': count,
            'total_time_seconds': sum(durations),
            'total_time_formatted': format_duration(sum(durations)),
            'min_seconds': min(durations),
            'min_formatted': format_duration(min(durations)),
            'max_seconds': max(durations),
            'max_formatted': format_duration(max(durations)),
            'avg_seconds': sum(durations) / count,
            'avg_formatted': format_duration(sum(durations) / count),
            'p90_seconds': percentile(sorted_durations, 90),
            'p90_formatted': format_duration(percentile(sorted_durations, 90)),
            'p95_seconds': percentile(sorted_durations, 95),
            'p95_formatted': format_duration(percentile(sorted_durations, 95)),
            'p98_seconds': percentile(sorted_durations, 98),
            'p98_formatted': format_duration(percentile(sorted_durations, 98)),
            'workflows': entries
        }
    
    return timing_stats


def print_timing_report(timing_stats):
    """Print a formatted timing report table"""
    if not timing_stats:
        logger.info("No timing data available")
        return
    
    logger.info("")
    logger.info("=" * 160)
    logger.info("WORKFLOW TYPE TIMING REPORT")
    logger.info("=" * 160)
    
    # Header
    header = f"{'Type':<40} | {'Count':>7} | {'Total':>12} | {'Min':>10} | {'Max':>10} | {'Avg':>10} | {'P90':>10} | {'P95':>10} | {'P98':>10}"
    logger.info(header)
    logger.info("-" * 160)
    
    # Sort by count (most frequent first)
    sorted_types = sorted(timing_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for wf_type, stats in sorted_types:
        type_display = wf_type[:38] + '..' if len(wf_type) > 40 else wf_type
        
        line = f"{type_display:<40} | {stats['count']:>7} | {stats['total_time_formatted']:>12} | {stats['min_formatted']:>10} | {stats['max_formatted']:>10} | {stats['avg_formatted']:>10} | {stats['p90_formatted']:>10} | {stats['p95_formatted']:>10} | {stats['p98_formatted']:>10}"
        logger.info(line)
    
    logger.info("-" * 160)
    
    # Grand totals
    total_workflows = sum(s['count'] for s in timing_stats.values())
    total_time = sum(s['total_time_seconds'] for s in timing_stats.values())
    
    logger.info(f"Total Workflows: {total_workflows} | Total Time: {format_duration(total_time)} | Unique Types: {len(timing_stats)}")
    logger.info("=" * 160)


def fetch_workflows(limit=500):
    """Fetch workflows from Argo API"""
    all_workflows = []
    
    try:
        # Fetch workflows list
        url = f"{WORKFLOWS_API}?listOptions.limit={limit}"
        response = requests.get(url, verify=False, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            all_workflows.extend(items)
            logger.info(f"Fetched {len(items)} workflows")
            
            # Handle pagination if needed
            continue_token = data.get('metadata', {}).get('continue', '')
            while continue_token:
                url = f"{WORKFLOWS_API}?listOptions.limit={limit}&listOptions.continue={continue_token}"
                response = requests.get(url, verify=False, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    all_workflows.extend(items)
                    logger.info(f"Fetched {len(items)} more workflows (total: {len(all_workflows)})")
                    continue_token = data.get('metadata', {}).get('continue', '')
                else:
                    break
        else:
            logger.error(f"Failed to fetch workflows: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error fetching workflows: {e}")
    
    return all_workflows


def main():
    logger.info("=" * 80)
    logger.info("Argo Workflows API Fetcher")
    logger.info(f"Target: {WORKFLOWS_API}")
    logger.info("=" * 80)
    
    # Fetch workflows from API
    workflows = fetch_workflows()
    
    if not workflows:
        logger.warning("No workflows fetched. Check API connectivity.")
        return
    
    logger.info(f"Total workflows fetched: {len(workflows)}")
    
    # Extract workflow info
    workflow_list = []
    nx_billing_workflows = []
    
    for wf in workflows:
        metadata = wf.get('metadata', {})
        status = wf.get('status', {})
        labels = metadata.get('labels', {})
        
        wf_info = {
            'name': metadata.get('name', ''),
            'namespace': metadata.get('namespace', ''),
            'phase': status.get('phase', ''),
            'started': status.get('startedAt', ''),
            'finished': status.get('finishedAt', ''),
            'workflow_type': labels.get('workflows.argoproj.io/workflow-template', 
                            labels.get('app', 
                            metadata.get('generateName', 'Unknown').rstrip('-'))),
            'labels': labels
        }
        
        # Calculate duration
        duration = parse_duration(wf_info['started'], wf_info['finished'])
        wf_info['duration_seconds'] = duration
        wf_info['duration_formatted'] = format_duration(duration)
        
        workflow_list.append(wf_info)
        
        # Check for nx_billing workflows
        name_lower = wf_info['name'].lower()
        type_lower = wf_info['workflow_type'].lower()
        if 'nx_billing' in name_lower or 'billing' in name_lower or 'nx_billing' in type_lower:
            nx_billing_workflows.append(wf_info)
    
    # Calculate timing statistics by workflow type
    timing_stats = calculate_workflow_timings(workflows)
    
    # Print timing report
    print_timing_report(timing_stats)
    
    # Save results to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"argo_workflows_{timestamp}.json"
    
    # Convert timing stats for JSON (remove workflow details to reduce size)
    timing_stats_json = {}
    for wf_type, stats in timing_stats.items():
        timing_stats_json[wf_type] = {k: v for k, v in stats.items() if k != 'workflows'}
    
    results = {
        'fetch_time': datetime.now().isoformat(),
        'api_url': WORKFLOWS_API,
        'total_workflows': len(workflow_list),
        'timing_stats': timing_stats_json,
        'nx_billing_workflows': nx_billing_workflows,
        'all_workflows': workflow_list
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total workflows: {len(workflow_list)}")
    logger.info(f"Unique workflow types: {len(timing_stats)}")
    logger.info(f"NX Billing workflows: {len(nx_billing_workflows)}")
    
    if nx_billing_workflows:
        logger.info("\nNX Billing Workflows:")
        for wf in nx_billing_workflows[:10]:  # Show first 10
            logger.info(f"  - {wf['name']} ({wf['phase']}) - Duration: {wf['duration_formatted']}")
        if len(nx_billing_workflows) > 10:
            logger.info(f"  ... and {len(nx_billing_workflows) - 10} more")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
