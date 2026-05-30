"""
Delete approval policies matching a name pattern.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent))
from logger_util import get_logger, LoggedRequests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize logger
logger = get_logger(__file__)

# Initialize logged requests
requests = LoggedRequests(logger)

# Configuration
BASE_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/api/nutanix/v3/policies/"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}
NAME_PATTERN = ".*[n|N][u|U][c|C][a|A][l|L][m|M].*"  # Matches "nucalm" case-insensitive
BATCH_SIZE = 20


def list_approval_policies(offset=0):
    """Fetch approval policies matching the name pattern."""
    payload = {
        "length": BATCH_SIZE,
        "offset": offset,
        "filter": f"name=={NAME_PATTERN};type==APPROVAL"
    }
    
    response = requests.post(
        BASE_URL + 'list',
        json=payload,
        headers=HEADERS,
        auth=AUTH,
        verify=False
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to list policies: {response.status_code}")
        return None
    
    return response.json()


def delete_policy(policy_uuid, policy_name, count):
    """Delete a single approval policy."""
    response = requests.delete(
        BASE_URL + policy_uuid,
        json={},
        headers=HEADERS,
        auth=AUTH,
        verify=False
    )
    
    if response.status_code in [200, 202, 204]:
        logger.info(f"✓ [{count}] Deleted: {policy_name}")
        return True
    else:
        logger.error(f"✗ [{count}] Failed to delete: {policy_name} (Status: {response.status_code})")
        return False


def main():
    logger.info("Starting approval policy deletion")
    logger.info(f"Target URL: {BASE_URL}")
    logger.info(f"Name pattern: {NAME_PATTERN}")
    
    deleted_count = 0
    error_count = 0
    offset = 0
    
    for _ in range(1):
        # Fetch policies
        result = list_approval_policies(offset=0)  # Always use offset 0 since we're deleting
        
        if result is None:
            logger.error("Failed to fetch policies. Exiting.")
            break
        
        policies = result.get('entities', [])
        total = result.get('metadata', {}).get('total_matches', 0)
        
        if not policies:
            logger.info("No more policies to delete.")
            break
        
        logger.info(f"Found {len(policies)} policies (Total matching: {total})")
        
        # Delete each policy
        for policy in policies:
            policy_uuid = policy['metadata']['uuid']
            policy_name = policy['metadata']['name']
            
            if delete_policy(policy_uuid, policy_name, deleted_count + error_count + 1):
                deleted_count += 1
            else:
                error_count += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("Deletion Summary")
    logger.info(f"  Total deleted: {deleted_count}")
    logger.info(f"  Total errors: {error_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
