#!/usr/bin/env python3
"""
Business Unit Creation Script
Creates business units by grouping cost centers from the cost center list.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

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
BASE_URL = "https://ncm.services.nconprem-10-53-56-44.ccpnx.com"
REQUEST_TIMEOUT = 3000  # seconds

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}

# Business Unit configuration
NUM_BUSINESS_UNITS = 30  # Number of business units to create
COST_CENTERS_PER_BU = 2   # Number of cost centers per business unit


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


# =============================================================================
# Core Functions
# =============================================================================

def fetch_cost_centers(limit, offset):
    """
    Fetch a batch of cost centers from the API.
    
    Args:
        limit: Number of cost centers to fetch
        offset: Starting offset for pagination
    
    Returns:
        list: List of cost center items, or empty list on error
    """
    endpoint = f"/v1/cg/global/costCenters?limit={limit}&offset={offset}"
    
    try:
        response = api_get(endpoint)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch cost centers: HTTP {response.status_code}")
            return []
        
        data = response.json()
        items = data.get('items', [])
        logger.debug(f"Fetched {len(items)} cost centers (offset={offset})")
        return items
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cost centers response: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching cost centers: {e}")
        return []


def create_business_unit(name, cost_center_ids):
    """
    Create a business unit with the given cost centers.
    
    Args:
        name: Name for the business unit
        cost_center_ids: List of cost center IDs to include
    
    Returns:
        tuple: (success: bool, response_data: dict or error message)
    """

    endpoint = "/v1/cg/global/businessUnit"
    
    payload = {
        "name": name,
        "permissions": {},
        "costCenters": cost_center_ids
    }
    
    try:
        response = api_post(endpoint, data=payload)
        
        if response.status_code in (200, 202):
            logger.info(f"✓ Created Business Unit: {name} with {len(cost_center_ids)} cost centers")
            return True, response.json() if response.text else {}
        else:
            logger.error(f"✗ Failed to create {name}: HTTP {response.status_code} - {response.text}")
            return False, response.text
            
    except Exception as e:
        logger.error(f"✗ Error creating {name}: {e}")
        return False, str(e)


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution flow for business unit creation."""
    logger.info("=" * 80)
    logger.info("Starting Business Unit Creation Process")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Base URL: {BASE_URL}")
    logger.info(f"  - Business Units to create: {NUM_BUSINESS_UNITS}")
    logger.info(f"  - Cost Centers per BU: {COST_CENTERS_PER_BU}")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Counters for summary
    total_created = 0
    total_failed = 0
    total_cost_centers_assigned = 0
    
    for i in range(0,NUM_BUSINESS_UNITS):
        bu_number = i + 1
        offset = i * COST_CENTERS_PER_BU +1
        
        logger.info(f"\n[{bu_number}/{NUM_BUSINESS_UNITS}] Processing Business Unit...")
        
        # Fetch cost centers for this batch
        cost_centers = fetch_cost_centers(limit=COST_CENTERS_PER_BU, offset=offset)
        
        if not cost_centers:
            logger.warning(f"No cost centers found at offset {offset}, stopping.")
            break
        
        # Extract cost center IDs
        cost_center_ids = [cc['id'] for cc in cost_centers]
        
        # Create business unit
        bu_name = f"Business_Unit_{bu_number}"
        success, _ = create_business_unit(bu_name, cost_center_ids)
        
        if success:
            total_created += 1
            total_cost_centers_assigned += len(cost_center_ids)
        else:
            total_failed += 1
    
    # Print summary
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("EXECUTION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  Business Units created:     {total_created}")
    logger.info(f"  Business Units failed:      {total_failed}")
    logger.info(f"  Total Cost Centers assigned: {total_cost_centers_assigned}")
    logger.info(f"  Success rate:               {total_created}/{total_created + total_failed} ({100 * total_created / max(1, total_created + total_failed):.1f}%)")
    logger.info(f"  Total execution time:       {elapsed:.2f}s ({elapsed/60:.2f} min)")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
