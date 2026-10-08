#!/usr/bin/env python3
"""
Budget Creation Script
Creates budgets for business units and cost centers with randomized alert configurations.
"""

import json
import random
import sys
import time
import copy
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
BASE_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com"
REQUEST_TIMEOUT = 3000  # seconds

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}

# Budget configuration
BUDGET_NAME_PREFIX = "budget_1"
RECIPIENTS_PER_BUDGET = 5

# Default payload template
DEFAULT_PAYLOAD = {
    "budgetName": "",
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

def fetch_resource_groups():
    """
    Fetch list of resource groups (business units and cost centers) available for budgeting.
    
    Returns:
        list: List of resource group items, or empty list on error
    """
    endpoint = "/v1/cg/global/budgets/listResourceGroups"
    
    try:
        response = api_get(endpoint)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch resource groups: HTTP {response.status_code}")
            try:
                logger.error(f"Response: {response.json()}")
            except:
                logger.error(f"Response: {response.text}")
            return []
        
        data = response.json()
        items = data.get('data', [])
        logger.info(f"Fetched {len(items)} resource groups")
        return items
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse resource groups response: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching resource groups: {e}")
        return []


def fetch_user_list():
    """
    Fetch list of users for budget alert recipients.
    
    Returns:
        list: List of user emails, or empty list on error
    """
    endpoint = "/v1/cg/users/list"
    
    try:
        response = api_get(endpoint)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch user list: HTTP {response.status_code}")
            try:
                logger.error(f"Response: {response.json()}")
            except:
                logger.error(f"Response: {response.text}")
            return []
        
        data = response.json()
        users = data.get('users', [])
        user_emails = [user["email"] for user in users]
        logger.info(f"Fetched {len(user_emails)} users for recipients")
        return user_emails
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse user list response: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching user list: {e}")
        return []


def build_budget_payload(budget_name, resource_type, resource_id, user_list):
    """
    Build a budget payload with randomized alert thresholds.
    
    Args:
        budget_name: Name for the budget
        resource_type: 'businessUnit' or 'costCenters'
        resource_id: ID of the resource to budget
        user_list: List of user emails for recipients
    
    Returns:
        dict: Budget payload
    """
    payload = copy.deepcopy(DEFAULT_PAYLOAD)
    payload["budgetName"] = budget_name
    payload["resourceGroups"][resource_type] = [resource_id]
    payload["financialYearStartMonth"] = str(random.randint(1, 12))
    payload["budgetAlert"]["configuration"]["monthly"][0]["thresholdPercent"] = random.randint(65, 75)
    payload["budgetAlert"]["configuration"]["quarterly"][0]["thresholdPercent"] = random.randint(75, 85)
    payload["budgetAlert"]["configuration"]["yearly"][0]["thresholdPercent"] = random.randint(85, 95)
    
    # Select random recipients
    if user_list:
        num_recipients = min(RECIPIENTS_PER_BUDGET, len(user_list))
        payload["budgetAlert"]["recipients"] = ["mohan.as1@nutanix.com","kodumuri.sowjanya@nutanix.com","abhinav.prashar@nutanix.com"]
    
    return payload


def create_budget(payload):
    """
    Create a budget via API.
    
    Args:
        payload: Budget configuration payload
    
    Returns:
        tuple: (success: bool, response_data: dict or error message)
    """
    endpoint = "/v1/cg/global/budgets"
    budget_name = payload.get("budgetName", "Unknown")
    
    try:
        response = api_post(endpoint, data=payload)
        
        if response.status_code in (200, 201, 202):
            logger.info(f"✓ Created budget: {budget_name}")
            return True, response.json() if response.text else {}
        else:
            error_msg = response.text
            try:
                error_msg = response.json()
            except:
                pass
            logger.error(f"✗ Failed to create budget '{budget_name}': HTTP {response.status_code} - {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.error(f"✗ Error creating budget '{budget_name}': {e}")
        return False, str(e)


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main execution flow for budget creation."""
    logger.info("=" * 80)
    logger.info("Starting Budget Creation Process")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Base URL: {BASE_URL}")
    logger.info(f"  - Budget name prefix: {BUDGET_NAME_PREFIX}")
    logger.info(f"  - Recipients per budget: {RECIPIENTS_PER_BUDGET}")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Fetch resource groups
    logger.info("Fetching resource groups...")
    resource_groups = fetch_resource_groups()
    if not resource_groups:
        logger.error("No resource groups found. Exiting.")
        return
    
    # Fetch user list
    logger.info("Fetching user list...")
    user_list = fetch_user_list()
    if not user_list:
        logger.warning("No users found for recipients. Budgets will be created without recipients.")
    
    # Count totals for summary
    total_bu_budgets = sum(1 for rg in resource_groups if rg['buId'] is not None)
    total_cc_budgets = sum(len(rg.get("ccUnits", [])) for rg in resource_groups)
    logger.info(f"Planning to create: {total_bu_budgets} BU budgets + {total_cc_budgets} CC budgets = {total_bu_budgets + total_cc_budgets} total")
    logger.info("=" * 80)
    
    # Counters for summary
    bu_created = 0
    bu_failed = 0
    cc_created = 0
    cc_failed = 0
    processed = 0
    total = total_bu_budgets + total_cc_budgets
    
    for resource_group in resource_groups:
        bu_id = resource_group.get("buId", "")
        bu_name = resource_group.get("buName", "Unknown")
        
        # Create budget for Business Unit (if valid ID)
        if bu_id is not None:
            processed += 1
            budget_name = f"{BUDGET_NAME_PREFIX}_{bu_name}"
            logger.info(f"[{processed}/{total}] Creating BU budget: {budget_name}")
            
            payload = build_budget_payload(budget_name, "businessUnit", bu_id, user_list)
            success, _ = create_budget(payload)
            
            if success:
                bu_created += 1
            else:
                bu_failed += 1
        
        # Create budgets for each Cost Center
        for cc in resource_group.get("ccUnits", []):
            processed += 1
            cc_id = cc.get("ccId", "")
            cc_name = cc.get("ccName", "Unknown")
            budget_name = f"{BUDGET_NAME_PREFIX}_{cc_name}"
            
            logger.info(f"[{processed}/{total}] Creating CC budget: {budget_name}")
            
            payload = build_budget_payload(budget_name, "costCenters", cc_id, user_list)
            success, _ = create_budget(payload)
            
            if success:
                cc_created += 1
            else:
                cc_failed += 1
    
    # Print summary
    elapsed = time.time() - start_time
    total_created = bu_created + cc_created
    total_failed = bu_failed + cc_failed
    total_attempted = total_created + total_failed
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("EXECUTION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  Business Unit budgets created: {bu_created}")
    logger.info(f"  Business Unit budgets failed:  {bu_failed}")
    logger.info(f"  Cost Center budgets created:   {cc_created}")
    logger.info(f"  Cost Center budgets failed:    {cc_failed}")
    logger.info("-" * 40)
    logger.info(f"  Total budgets created:         {total_created}")
    logger.info(f"  Total budgets failed:          {total_failed}")
    logger.info(f"  Success rate:                  {total_created}/{total_attempted} ({100 * total_created / max(1, total_attempted):.1f}%)")
    logger.info(f"  Total execution time:          {elapsed:.2f}s ({elapsed/60:.2f} min)")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
