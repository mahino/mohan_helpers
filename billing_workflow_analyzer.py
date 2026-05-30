#!/usr/bin/env python3
"""
Billing Workflow Duration Analyzer
Analyzes NxBillingWorkflow execution times and provides statistics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent))
from logger_util import get_logger

# Initialize logger
logger = get_logger(__file__)


def parse_time(timestamp):
    """
    Parse ISO 8601 timestamp format.
    
    Args:
        timestamp: ISO 8601 formatted timestamp string
    
    Returns:
        datetime: Parsed datetime object
    """
    # Handle ISO 8601 format: 2025-12-27T14:52:06.549344Z
    timestamp = timestamp.replace('Z', '')
    if '.' in timestamp:
        return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')


def analyze_workflow_durations(workflows_data):
    """
    Analyze workflow durations and generate statistics.
    
    Args:
        workflows_data: Dictionary containing workflows list
    
    Returns:
        dict: Analysis results with durations, statistics, and completed workflows
    """
    completed_workflows = []
    durations_minutes = []
    
    logger.info("Analyzing workflow durations...")
    
    for workflow in workflows_data.get("workflows", []):
        if workflow["status"] == "Completed":
            workflow_info = {
                "name": workflow['name'],
                "runId": workflow['runId'],
                "startTime": workflow['startTime'],
                "endTime": workflow['endTime']
            }
            completed_workflows.append(workflow_info)
            
            try:
                start_time = parse_time(workflow['startTime'])
                end_time = parse_time(workflow['endTime'])
                duration_minutes = (end_time - start_time).total_seconds() / 60
                durations_minutes.append(duration_minutes)
                
                logger.debug(f"Workflow {workflow['runId']}: {duration_minutes:.2f} minutes")
                
            except Exception as e:
                logger.error(f"Error parsing times for workflow {workflow['runId']}: {e}")
    
    # Calculate statistics
    if durations_minutes:
        avg_minutes = sum(durations_minutes) / len(durations_minutes)
        avg_hours = avg_minutes / 60
        min_duration = min(durations_minutes)
        max_duration = max(durations_minutes)
        total_duration = sum(durations_minutes)
    else:
        avg_minutes = avg_hours = min_duration = max_duration = total_duration = 0
    
    results = {
        "completed_workflows": completed_workflows,
        "durations_minutes": durations_minutes,
        "statistics": {
            "count": len(durations_minutes),
            "average_minutes": avg_minutes,
            "average_hours": avg_hours,
            "min_minutes": min_duration,
            "max_minutes": max_duration,
            "total_minutes": total_duration,
            "total_hours": total_duration / 60
        }
    }
    
    return results


def print_analysis_report(results):
    """Print formatted analysis report."""
    stats = results["statistics"]
    
    logger.info("=" * 80)
    logger.info("BILLING WORKFLOW ANALYSIS REPORT")
    logger.info("=" * 80)
    logger.info(f"Total completed workflows: {stats['count']}")
    
    if stats['count'] > 0:
        logger.info(f"Average duration: {stats['average_minutes']:.2f} minutes ({stats['average_hours']:.2f} hours)")
        logger.info(f"Shortest duration: {stats['min_minutes']:.2f} minutes")
        logger.info(f"Longest duration: {stats['max_minutes']:.2f} minutes")
        logger.info(f"Total execution time: {stats['total_minutes']:.2f} minutes ({stats['total_hours']:.2f} hours)")
    else:
        logger.info("No completed workflows found")
    
    logger.info("=" * 80)


def main():
    """Main execution function."""
    # Sample data structure - replace with actual data source
    sample_workflows = {
        "workflows": [
            {
                "name": "NxBillingWorkflow",
                "id": "nx_billing",
                "runId": "accee512-4c4f-41f3-a942-49cf88d273b8",
                "startTime": "2025-12-27T08:51:15.407489Z",
                "endTime": "2025-12-27T13:47:47.216061Z",
                "status": "Completed"
            },
            {
                "name": "NxBillingWorkflow",
                "id": "nx_billing",
                "runId": "7051a80f-d4bc-448e-9cf3-5dff77ae5262",
                "startTime": "2025-12-27T01:00:26.240521Z",
                "endTime": "2025-12-27T06:03:05.067181Z",
                "status": "Completed"
            }
        ]
    }
    
    logger.info("Starting Billing Workflow Analysis")
    
    # TODO: Replace with actual data loading from API or file
    # For now, using sample data
    workflows_data = sample_workflows
    
    # Analyze workflows
    results = analyze_workflow_durations(workflows_data)
    
    # Print report
    print_analysis_report(results)
    
    # Output detailed results as JSON
    print("\nDetailed Results:")
    print(json.dumps(results["completed_workflows"], indent=2))
    print(f"\nDurations (minutes): {results['durations_minutes']}")


if __name__ == "__main__":
    main()
