#!/usr/bin/env python3
"""
Delete Rate Cards via API
Deletes rate cards using the NCM API.
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
BASE_URL = "https://ncm.services.nconprem-10-53-55-33.nxncm.com"
REQUEST_TIMEOUT = 30  # seconds

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}

# Filter configuration - modify these to target specific configs
DELETE_TEST_CONFIGS_ONLY = True  # Set to False to delete all configs
TEST_CONFIG_PATTERN = "st_testing"  # Pattern to identify test rate cards


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

def fetch_rate_cards(limit=100, offset=0):
    """
    Fetch rate cards from the API.
    
    Args:
        limit: Number of configs to fetch
        offset: Starting offset for pagination
    
    Returns:
        tuple: (configs_list, total_count) or ([], 0) on error
    """

    endpoint = f"/v1/cg/config/rate-cards/actions/get-rate-cards?limit={limit}&offset={offset}"
    #https://ncm.services.nconprem-10-114-55-128.ccpnx.com/v1/cg/config/rate-cards/actions/get-rate-cards?limit=10&offset=10
    
    try:
        # Use POST with filters as shown in your example
        response = api_post(endpoint, data={"filters": []})
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch rate cards: HTTP {response.status_code}")
            return [], 0
        
        data = response.json()
        configs = data.get('data', [])
        total_count = data.get('totalCount', 0)
        
        logger.debug(f"Fetched {len(configs)} configs (offset={offset}, total={total_count})")
        return configs, total_count
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse rate cards response: {e}")
        return [], 0
    except Exception as e:
        logger.error(f"Error fetching rate cards: {e}")
        return [], 0


def get_all_rate_cards():
    """
    Get all rate cards with pagination.
    
    Returns:
        list: All rate cards
    """
    all_configs = []
    offset = 0
    limit = 100
    
    while True:
        configs, total_count = fetch_rate_cards(limit=limit, offset=offset)
        
        if not configs:
            break
        
        all_configs.extend(configs)
        
        # Check if we've got all configs
        if len(all_configs) >= total_count:
            break
        
        offset += limit
        time.sleep(0.1)  # Small delay to avoid overwhelming API
    
    logger.info(f"Retrieved {len(all_configs)} total rate cards")
    return all_configs


def filter_configs(all_rate_cards):
    """
    Filter rate cards based on DELETE_TEST_CONFIGS_ONLY setting.
    
    Args:
        all_rate_cards: List of all rate cards
    
    Returns:
        list: Filtered rate cards to delete
    """
    if not DELETE_TEST_CONFIGS_ONLY:
        return all_rate_cards
    
    # Filter for test rate cards only
    test_rate_cards = []
    for rate_card in all_rate_cards:
        description = rate_card.get('rateCardName', '').lower()
        if TEST_CONFIG_PATTERN.lower() in description:
            test_rate_cards.append(rate_card)
    
    logger.info(f"Filtered to {len(test_rate_cards)} test rate cards")
    return test_rate_cards


def display_rate_card_summary(rate_cards):
    """Display summary of rate cards to be deleted."""
    if not rate_cards:
        logger.info("No rate cards to delete")
        return
    
    logger.info(f"\nRate cards to delete ({len(rate_cards)}):")
    logger.info("-" * 80)
    
    total_monthly_cost = 0
    for i, rate_card in enumerate(rate_cards, 1):
        rate_card_id = rate_card.get('rateCardId', 'N/A')
        rate_card_name = rate_card.get('rateCardName', 'N/A')
        cost_type = rate_card.get('costType', 'N/A')
        monthly_cost = rate_card.get('monthlyCost', 0)
        created_by = rate_card.get('createdBy', {}).get('name', 'N/A')
        
        total_monthly_cost += monthly_cost
        
        logger.info(f"{i:3d}. {rate_card_name} (ID: {rate_card_id[:8]}...)")
        logger.info(f"     Type: {cost_type} | Monthly Cost: ${monthly_cost} | Created by: {created_by}")
    
    logger.info(f"\nTotal Monthly Cost Impact: ${total_monthly_cost:,.2f}")
    logger.info("-" * 80)


def delete_rate_card(rate_card_id, rate_card_name):
    """
    Delete a single rate card.
    
    Args:
        rate_card_id: Rate card ID to delete
        rate_card_name: Rate card name for logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    endpoint = f"/v1/cg/config/rate-cards?rateCardIds={rate_card_id}"
    
    
    try:
        response = api_delete(endpoint)
        
        if response.status_code in (200, 204):
            logger.info(f"✓ Deleted: {rate_card_name}")
            return True
        else:
            logger.error(f"✗ Failed to delete {rate_card_name}: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error deleting {rate_card_name}: {e}")
        return False


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution flow for rate card deletion."""
    logger.info("=" * 80)
    logger.info("Starting rate card deletion")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Base URL: {BASE_URL}")
    logger.info(f"  - Delete test configs only: {DELETE_TEST_CONFIGS_ONLY}")
    if DELETE_TEST_CONFIGS_ONLY:
        logger.info(f"  - Test config pattern: '{TEST_CONFIG_PATTERN}'")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Fetch all configurations
    logger.info("Fetching rate cards...")
    all_rate_cards = get_all_rate_cards()
    
    if not all_rate_cards:
        logger.warning("No rate cards found")
        return
    
    # Filter configurations
    rate_cards_to_delete = filter_configs(all_rate_cards)
    
    if not rate_cards_to_delete:
        logger.info("No rate cards match deletion criteria")
        return
    
    # Display summary
    display_rate_card_summary(rate_cards_to_delete)
    
    # Confirm deletion
    response = input(f"\nDo you want to delete these {len(rate_cards_to_delete)} rate cards? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        logger.info("Deletion cancelled by user")
        return
    # Delete rate cards
    logger.info(f"\nStarting deletion of {len(rate_cards_to_delete)} rate cards...")
    
    total_deleted = 0
    total_failed = 0
    
    for rate_card in rate_cards_to_delete:
        rate_card_id = rate_card.get('rateCardId')
        rate_card_name = rate_card.get('rateCardName')
        
        logger.info(f"Processing: {rate_card_name}")
        
        if not rate_card_id:
            logger.error(f"✗ Missing rateCardId for: {rate_card_name}")
            total_failed += 1
            continue
        
        if delete_rate_card(rate_card_id, rate_card_name):
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
    logger.info(f"  Rate cards deleted:     {total_deleted}")
    logger.info(f"  Rate cards failed:      {total_failed}")
    logger.info(f"  Success rate:               {total_deleted}/{total_deleted + total_failed} ({100 * total_deleted / max(1, total_deleted + total_failed):.1f}%)")
    logger.info(f"  Total execution time:       {elapsed:.2f}s")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()