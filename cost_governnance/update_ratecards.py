#!/usr/bin/env python3
"""
Update TCO Direct Cost Configurations via API
Updates TCO direct cost configurations using the NCM API.
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
BASE_URL = "https://ncm.services.nconprem-10-114-55-128.ccpnx.com"
REQUEST_TIMEOUT = 30  # seconds

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}

tco_type = ["direct", "indirect"]  # Types of TCO configs to fetch and update
add_clusters = ["00065031-3c14-1b72-7e15-7cc2558641c8"]  # Add cluster UUIDs here to extend resources->clusters list
# Example: add_clusters = ["00065035-b0c9-5144-07ad-7cc255864212", "00065035-daa1-70e4-7faf-ac1f6b61e0cf"]

# Filter configuration - modify these to target specific configs
UPDATE_TEST_CONFIGS_ONLY = True  # Set to False to update all configs
TEST_CONFIG_PATTERN = "test_tco_config"  # Pattern to identify test configs

# Update payload - modify these fields as needed
# Set to None to preserve from original GET response
# Only set specific values you want to change
UPDATE_PAYLOAD = {
    "description": None,      # Preserved from GET
    "costHead": None,         # Preserved from GET (cannot be updated per API)
    "properties": None,       # Preserved from GET (or set specific sub-fields to update)
    "meteringUnit": None,     # Preserved from GET
    "costPerMeter": None,     # Preserved from GET
    "resources": None         # Preserved from GET
}

# Example: To update specific fields, uncomment and modify:
# UPDATE_PAYLOAD = {
#     "description": None,
#     "costHead": None,
#     "properties": {
#         "applicability": "CAPEX",
#         "startDate": 1777593600,
#         "termInMonths": 1
#     },
#     "meteringUnit": "NODE",
#     "costPerMeter": 1,
#     "resources": [
#         {
#             "clusters": ["00065035-b0c9-5144-07ad-7cc255864212"],
#             "categories": []
#         }
#     ]
# }


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


def api_put(endpoint, data=None, **kwargs):
    """Execute PUT request with standard configuration."""
    url = f"{BASE_URL}{endpoint}"
    kwargs.setdefault('verify', False)
    kwargs.setdefault('headers', HEADERS)
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    
    if data is not None:
        return requests.put(url, data=json.dumps(data), **kwargs)
    return requests.put(url, **kwargs)


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

def fetch_tco_configs(tco_type_str, limit=100, offset=0):
    """
    Fetch TCO cost configurations from the API.
    
    Args:
        tco_type_str: Type of TCO config ('direct' or 'indirect')
        limit: Number of configs to fetch
        offset: Starting offset for pagination
    
    Returns:
        tuple: (configs_list, total_count) or ([], 0) on error
    """

    endpoint = f"/v1/cg/config/tco/configs?limit={limit}&offset={offset}&costHeadAction={tco_type_str}"
    #https://ncm.services.nconprem-10-114-55-128.ccpnx.com/v1/cg/config/rate-cards/actions/get-rate-cards?limit=10&offset=10
    
    try:
        # Use POST with filters as shown in your example
        response = api_post(endpoint, data={"filters": []})
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch TCO configs for {tco_type_str}: HTTP {response.status_code}")
            return [], 0
        
        data = response.json()
        configs = data.get('data', [])
        total_count = data.get('totalCount', 0)
        
        logger.debug(f"Fetched {len(configs)} {tco_type_str} configs (offset={offset}, total={total_count})")
        return configs, total_count
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse TCO configs response: {e}")
        return [], 0
    except Exception as e:
        logger.error(f"Error fetching TCO configs: {e}")
        return [], 0


def get_all_tco_configs():
    """
    Get all TCO configurations with pagination for all tco_type values.
    
    Returns:
        list: All TCO configurations across all types
    """
    all_configs = []
    
    # Loop through each tco_type
    for type_str in tco_type:
        logger.info(f"Fetching {type_str} TCO configurations...")
        offset = 0
        limit = 100
        
        while True:
            configs, total_count = fetch_tco_configs(type_str, limit=limit, offset=offset)
            
            if not configs:
                break
            
            all_configs.extend(configs)
            
            # Check if we've got all configs for this type
            if offset + len(configs) >= total_count:
                break
            
            offset += limit
            time.sleep(0.1)  # Small delay to avoid overwhelming API
        
        logger.info(f"Retrieved {offset + len(configs)} {type_str} TCO configurations")
    
    logger.info(f"Retrieved {len(all_configs)} total TCO configurations across all types")
    return all_configs


def filter_configs(configs):
    """
    Filter configurations based on UPDATE_TEST_CONFIGS_ONLY setting.
    
    Args:
        configs: List of all configurations
    
    Returns:
        list: Filtered configurations to update
    """
    if not UPDATE_TEST_CONFIGS_ONLY:
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
    """Display summary of configurations to be updated."""
    if not configs:
        logger.info("No configurations to update")
        return
    
    logger.info(f"\nConfigurations to update ({len(configs)}):")
    logger.info("-" * 80)
    
    total_monthly_cost = 0
    for i, config in enumerate(configs, 1):
        config_id = config.get('configId', 'N/A')
        description = config.get('description', 'N/A')
        cost_type = config.get('costType', 'N/A')
        cost_head = config.get('costHead', 'N/A')
        monthly_cost = config.get('monthlyCost', 0)
        created_by = config.get('createdBy', {}).get('name', 'N/A')
        
        total_monthly_cost += monthly_cost
        
        logger.info(f"{i:3d}. {description} (ID: {config_id[:8]}...)")
        logger.info(f"     Current: {cost_head}/{cost_type} | Monthly Cost: ${monthly_cost} | Created by: {created_by}")
    
    logger.info(f"\nTotal Monthly Cost Impact: ${total_monthly_cost:,.2f}")
    logger.info("-" * 80)


def get_tco_config(config_id):
    """
    Get a single TCO configuration by ID.
    
    Args:
        config_id: Configuration ID to fetch
    
    Returns:
        dict: Configuration data or None on error
    """
    endpoint = f"/v1/cg/config/tco/configs/{config_id}"
    
    try:
        response = api_get(endpoint)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get config {config_id}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting config {config_id}: {e}")
        return None


def extend_clusters_in_resources(resources):
    """
    Extend clusters in resources with clusters from add_clusters list.
    Avoids duplicates.
    
    Args:
        resources: List of resource objects from config
    
    Returns:
        list: Updated resources with extended clusters
    """
    if not add_clusters or not resources:
        return resources
    
    # Work on a copy to avoid modifying original
    updated_resources = []
    
    for resource in resources:
        resource_copy = resource.copy()
        existing_clusters = resource_copy.get('clusters', [])
        
        # Extend with new clusters (avoid duplicates)
        for cluster_uuid in add_clusters:
            if cluster_uuid not in existing_clusters:
                existing_clusters.append(cluster_uuid)
                logger.debug(f"Added cluster {cluster_uuid} to resources")
        
        resource_copy['clusters'] = existing_clusters
        updated_resources.append(resource_copy)
    
    return updated_resources


def merge_update_payload(original_config, update_payload):
    """
    Merge update payload with original config, preserving fields set to None in update_payload.
    Only includes fields that are in UPDATE_PAYLOAD - no extra fields from GET response.
    Also extends clusters if add_clusters is configured.
    
    Args:
        original_config: Original configuration from GET
        update_payload: Update payload template
    
    Returns:
        dict: Merged update payload with only the specified fields
    """
    merged = {}
    
    for key, value in update_payload.items():
        if value is None:
            # Preserve original value
            merged[key] = original_config.get(key)
        elif isinstance(value, dict) and key in original_config and isinstance(original_config[key], dict):
            # Deep merge for nested dicts (like properties)
            merged[key] = {**original_config[key], **value}
        else:
            # Use update value
            merged[key] = value
    
    # Extend clusters if add_clusters is configured
    if add_clusters and 'resources' in merged:
        merged['resources'] = extend_clusters_in_resources(merged['resources'])
    
    # IMPORTANT: Only return fields that are in UPDATE_PAYLOAD
    # Do NOT include fields like configId, costType, createdBy, createdAt, 
    # lastModifiedAt, lastModifiedBy, monthlyCost, configuration, etc.
    return merged


def update_tco_config(config_id, description, original_config):
    """
    Update a single TCO configuration.
    
    Args:
        config_id: Configuration ID to update
        description: Configuration description for logging
        original_config: Original configuration data
    
    Returns:
        bool: True if successful, False otherwise
    """
    endpoint = f"/v1/cg/config/tco/configs/{config_id}"
    
    try:
        # Merge update payload with original config
        update_data = merge_update_payload(original_config, UPDATE_PAYLOAD)
        
        logger.debug(f"Update payload for {description}: {json.dumps(update_data, indent=2)}")
        
        response = api_put(endpoint, data=update_data)
        
        if response.status_code in (200, 204):
            logger.info(f"✓ Updated: {description}")
            return True
        else:
            logger.error(f"✗ Failed to update {description}: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error updating {description}: {e}")
        return False


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution flow for TCO configuration update."""
    logger.info("=" * 80)
    logger.info("Starting TCO Cost Configuration Update")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Base URL: {BASE_URL}")
    logger.info(f"  - TCO Types: {', '.join(tco_type)}")
    if add_clusters:
        logger.info(f"  - Add Clusters: {len(add_clusters)} cluster(s) will be added to resources")
        for cluster_uuid in add_clusters:
            logger.info(f"    • {cluster_uuid}")
    else:
        logger.info(f"  - Add Clusters: None (clusters will be preserved from original)")
    logger.info(f"  - Update test configs only: {UPDATE_TEST_CONFIGS_ONLY}")
    if UPDATE_TEST_CONFIGS_ONLY:
        logger.info(f"  - Test config pattern: '{TEST_CONFIG_PATTERN}'")
    logger.info(f"\nUpdate Payload:")
    logger.info(f"{json.dumps(UPDATE_PAYLOAD, indent=2)}")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Fetch all configurations
    logger.info("Fetching TCO configurations...")
    all_configs = get_all_tco_configs()
    
    if not all_configs:
        logger.warning("No TCO configurations found")
        return
    
    # Filter configurations
    configs_to_update = filter_configs(all_configs)
    
    if not configs_to_update:
        logger.info("No configurations match update criteria")
        return
    
    # Display summary
    display_config_summary(configs_to_update)
    
    # Confirm update
    response = input(f"\nDo you want to update these {len(configs_to_update)} configurations? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        logger.info("Update cancelled by user")
        return
    
    # Update configurations
    logger.info(f"\nStarting update of {len(configs_to_update)} configurations...")
    
    total_updated = 0
    total_failed = 0
    
    for i, config in enumerate(configs_to_update, 1):
        config_id = config.get('configId')
        description = config.get('description', f'Config-{i}')
        
        logger.info(f"\n[{i}/{len(configs_to_update)}] Processing: {description}")
        
        if not config_id:
            logger.error(f"✗ Missing configId for: {description}")
            total_failed += 1
            continue
        
        # Get full config details
        logger.debug(f"Fetching full config for {config_id}...")
        full_config = get_tco_config(config_id)
        
        if not full_config:
            logger.error(f"✗ Failed to fetch config for: {description}")
            total_failed += 1
            continue
        
        # Update the config
        if update_tco_config(config_id, description, full_config):
            total_updated += 1
        else:
            total_failed += 1
        
        # Small delay between updates
        time.sleep(0.2)
    
    # Print summary
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("UPDATE SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  Configurations updated:     {total_updated}")
    logger.info(f"  Configurations failed:      {total_failed}")
    logger.info(f"  Success rate:               {total_updated}/{total_updated + total_failed} ({100 * total_updated / max(1, total_updated + total_failed):.1f}%)")
    logger.info(f"  Total execution time:       {elapsed:.2f}s")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()