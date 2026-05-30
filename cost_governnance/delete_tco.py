#!/usr/bin/env python3
"""
Delete TCO Direct Cost Configurations via API
Deletes TCO direct cost configurations using the NCM API.
"""

import json
import sys
import time
from pathlib import Path

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger, LoggedRequests

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize logger
logger = get_logger(__file__)

# Initialize logged requests (replaces standard requests with automatic logging)
requests = LoggedRequests(logger)

# =============================================================================
# Configuration
# =============================================================================
BASE_URL = "https://ncm.services.nconprem-10-122-27-229.ccpnx.com"
REQUEST_TIMEOUT = 30  # seconds

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}

# Filter configuration - modify these to target specific configs
DELETE_TEST_CONFIGS_ONLY = True  # Set to False to delete all configs
TEST_CONFIG_PATTERN = "test_tco_config"  # Pattern to identify test configs


# =============================================================================
# API Helper Functions
# =============================================================================

def api_get(endpoint, **kwargs):
    """Execute GET request with standard configuration."""
    url = f"{BASE_URL}{endpoint}"
    kwargs.setdefault('verify', False)
    kwargs.setdefault('headers', HEADERS)
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    return requests.get(url, **kwargs)


def api_post(endpoint, data=None, **kwargs):
    """Execute POST request with standard configuration."""
    url = f"{BASE_URL}{endpoint}"
    kwargs.setdefault('verify', False)
    kwargs.setdefault('headers', HEADERS)
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    
    if data is not None:
        return requests.post(url, data=json.dumps(data), **kwargs)
    return requests.post(url, **kwargs)


def api_delete(endpoint, **kwargs):
    """Execute DELETE request with standard configuration."""
    url = f"{BASE_URL}{endpoint}"
    kwargs.setdefault('verify', False)
    kwargs.setdefault('headers', HEADERS)
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    return requests.delete(url, **kwargs)


# =============================================================================
# Core Functions
# =============================================================================

def fetch_tco_configs(limit=100, offset=0):
    """
    Fetch TCO direct cost configurations from the API.
    
    Args:
        limit: Number of configs to fetch
        offset: Starting offset for pagination
    
    Returns:
        tuple: (configs_list, total_count) or ([], 0) on error
    """

    endpoint = f"/v1/cg/config/tco/configs?limit={limit}&offset={offset}&costHeadAction=direct"
    
    try:
        # Use POST with filters as shown in your example
        response = api_post(endpoint, data={"filters": []})
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch TCO configs: HTTP {response.status_code}")
            return [], 0
        
        data = response.json()
        configs = data.get('data', [])
        total_count = data.get('totalCount', 0)
        
        logger.debug(f"Fetched {len(configs)} configs (offset={offset}, total={total_count})")
        return configs, total_count
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse TCO configs response: {e}")
        return [], 0
    except Exception as e:
        logger.error(f"Error fetching TCO configs: {e}")
        return [], 0


def get_all_tco_configs():
    """
    Get all TCO configurations with pagination.
    
    Returns:
        list: All TCO configurations
    """
    all_configs = []
    offset = 0
    limit = 100
    
    while True:
        configs, total_count = fetch_tco_configs(limit=limit, offset=offset)
        
        if not configs:
            break
        
        all_configs.extend(configs)
        
        # Check if we've got all configs
        if len(all_configs) >= total_count:
            break
        
        offset += limit
        time.sleep(0.1)  # Small delay to avoid overwhelming API
    
    logger.info(f"Retrieved {len(all_configs)} total TCO configurations")
    return all_configs


def filter_configs(configs):
    """
    Filter configurations based on DELETE_TEST_CONFIGS_ONLY setting.
    
    Args:
        configs: List of all configurations
    
    Returns:
        list: Filtered configurations to delete
    """
    if not DELETE_TEST_CONFIGS_ONLY:
        return configs
    
    # Filter for test configs only
    test_configs = []
    for config in configs:
        description = config.get('description', '').lower()
        if TEST_CONFIG_PATTERN.lower() in description:
            test_configs.append(config)
    
    logger.info(f"Filtered to {len(test_configs)} test configurations")
    return test_configs


def display_config_summary(configs):
    """Display summary of configurations to be deleted."""
    if not configs:
        logger.info("No configurations to delete")
        return
    
    logger.info(f"\nConfigurations to delete ({len(configs)}):")
    logger.info("-" * 80)
    
    total_monthly_cost = 0
    for i, config in enumerate(configs, 1):
        config_id = config.get('configId', 'N/A')
        description = config.get('description', 'N/A')
        cost_type = config.get('costType', 'N/A')
        monthly_cost = config.get('monthlyCost', 0)
        created_by = config.get('createdBy', {}).get('name', 'N/A')
        
        total_monthly_cost += monthly_cost
        
        logger.info(f"{i:3d}. {description} (ID: {config_id[:8]}...)")
        logger.info(f"     Type: {cost_type} | Monthly Cost: ${monthly_cost} | Created by: {created_by}")
    
    logger.info(f"\nTotal Monthly Cost Impact: ${total_monthly_cost:,.2f}")
    logger.info("-" * 80)


def delete_tco_config(config_id, description):
    """
    Delete a single TCO configuration.
    
    Args:
        config_id: Configuration ID to delete
        description: Configuration description for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    endpoint = f"/v1/cg/config/tco/configs/{config_id}"
    
    try:
        response = api_delete(endpoint)
        
        if response.status_code in (200, 204):
            logger.info(f"✓ Deleted: {description}")
            return True
        else:
            logger.error(f"✗ Failed to delete {description}: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error deleting {description}: {e}")
        return False


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution flow for TCO configuration deletion."""
    logger.info("=" * 80)
    logger.info("Starting TCO Direct Cost Configuration Deletion")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Base URL: {BASE_URL}")
    logger.info(f"  - Delete test configs only: {DELETE_TEST_CONFIGS_ONLY}")
    if DELETE_TEST_CONFIGS_ONLY:
        logger.info(f"  - Test config pattern: '{TEST_CONFIG_PATTERN}'")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Fetch all configurations
    logger.info("Fetching TCO configurations...")
    all_configs = get_all_tco_configs()
    
    if not all_configs:
        logger.warning("No TCO configurations found")
        return
    
    # Filter configurations
    configs_to_delete = filter_configs(all_configs)
    
    if not configs_to_delete:
        logger.info("No configurations match deletion criteria")
        return
    
    # Display summary
    display_config_summary(configs_to_delete)
    
    # Confirm deletion
    response = input(f"\nDo you want to delete these {len(configs_to_delete)} configurations? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        logger.info("Deletion cancelled by user")
        return
    
    # Delete configurations
    logger.info(f"\nStarting deletion of {len(configs_to_delete)} configurations...")
    
    total_deleted = 0
    total_failed = 0
    
    for i, config in enumerate(configs_to_delete, 1):
        config_id = config.get('configId')
        description = config.get('description', f'Config-{i}')
        
        logger.info(f"[{i}/{len(configs_to_delete)}] Processing: {description}")
        
        if not config_id:
            logger.error(f"✗ Missing configId for: {description}")
            total_failed += 1
            continue
        
        if delete_tco_config(config_id, description):
            total_deleted += 1
        else:
            total_failed += 1
        
        # Small delay between deletions
        time.sleep(0.2)
    
    # Print summary
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("DELETION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  Configurations deleted:     {total_deleted}")
    logger.info(f"  Configurations failed:      {total_failed}")
    logger.info(f"  Success rate:               {total_deleted}/{total_deleted + total_failed} ({100 * total_deleted / max(1, total_deleted + total_failed):.1f}%)")
    logger.info(f"  Total execution time:       {elapsed:.2f}s")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()