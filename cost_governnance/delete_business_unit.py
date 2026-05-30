#!/usr/bin/env python3
"""
Delete all business units from NCM Cost Governance
"""
import sys
import json
from pathlib import Path

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
BASE_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}
V3 = 'v1/cg/global/'
URL = BASE_URL + V3
DELETE_ITEM = "COST_CENTER" #"BUSINESS_UNIT"

def main():
    logger.info("=" * 80)
    logger.info("Delete Business Units Script Started")
    logger.info("=" * 80)

    # Get chargeback configuration
    logger.info("Fetching chargeback configuration...")
    cb_list = requests.get(URL + "chargeback/configuration", headers=HEADERS, auth=AUTH, verify=False)
    cb_list = json.loads(cb_list.content)

    deleted_count = 0
    error_count = 0

    if DELETE_ITEM == "COST_CENTER":
        delete_url = URL + "costCenter/"
    else:
        delete_url = URL + "businessUnit/"
    for cb in cb_list.get('items', []):
        if cb['type'] == DELETE_ITEM:
            bu_name = cb['name']
            bu_id = cb['id']
            logger.info(f"Deleting business unit: {bu_name}")
            
            resp = requests.delete(delete_url + bu_id, headers=HEADERS, auth=AUTH, verify=False)
            
            if resp.status_code in [200, 202, 204]:
                logger.info(f"✓ Deleted business unit: {bu_name}")
                deleted_count += 1
            else:
                logger.error(f"✗ Failed to delete business unit: {bu_name} (Status: {resp.status_code})")
                error_count += 1

    logger.info("=" * 80)
    logger.info("Deletion Summary")
    logger.info(f"  Total deleted: {deleted_count}")
    logger.info(f"  Total errors: {error_count}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
