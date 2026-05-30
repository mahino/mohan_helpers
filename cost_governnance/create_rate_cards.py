#!/usr/bin/env python3
"""
Create rate cards in NCM Cost Governance
"""
import sys
import json
import random
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
URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/rate-cards"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}

rc_payload = {
    "rateCards": [
        {
            "rateCardName": "fravdfs",
            "meteringRates": {
                "vm": {
                    "vCpu": {"unit": "HOUR", "rate": 10},
                    "vRam": {"unit": "HOUR", "rate": 1},
                    "vStorage": {"unit": "GIB", "rate": 1},
                    "customConfigs": [
                        {"description": "1", "value": {"unit": "DAY", "rate": 1}},
                        {"description": "11", "value": {"unit": "DAY", "rate": 11}},
                        {"description": "2", "value": {"unit": "DAY", "rate": 2}},
                        {"description": "3", "value": {"unit": "DAY", "rate": 3}},
                        {"description": "4", "value": {"unit": "DAY", "rate": 4}}
                    ]
                }
            },
            "resources": []
        }
    ]
}


def main():
    logger.info("=" * 80)
    logger.info("Create Rate Cards Script Started")
    logger.info("=" * 80)

    rate_card_name = "st_testing" + str(random.randint(1, 1000000)) + "_"
    created_count = 0
    error_count = 0
    rate_limit_count = 0

    for i in range(10000):
        rc_payload['rateCards'][0]['rateCardName'] = rate_card_name + str(i)
        rc_payload['rateCards'][0]['meteringRates']['vm']['vCpu']['rate'] = random.randint(1, 100)
        rc_payload['rateCards'][0]['meteringRates']['vm']['vRam']['rate'] = random.randint(1, 100)
        rc_payload['rateCards'][0]['meteringRates']['vm']['vStorage']['rate'] = random.randint(1, 100)
        
        for j in range(5):
            rc_payload['rateCards'][0]['meteringRates']['vm']['customConfigs'][j]['description'] = rate_card_name + str(j)
            rc_payload['rateCards'][0]['meteringRates']['vm']['customConfigs'][j]['value']['rate'] = random.randint(1, 100)
        
        resp = requests.post(URL, json=rc_payload, headers=HEADERS, auth=AUTH, verify=False)
        
        if resp.status_code == 200:
            created_count += 1
            logger.info(f"✓ [{created_count}] Created rate card: {rc_payload['rateCards'][0]['rateCardName']}")
        elif resp.status_code == 429:
            rate_limit_count += 1
            logger.warning("Rate limit breached, deleting rate cards...")
            
            # Delete rate cards
            rc_list = requests.post(URL + "/actions/get-rate-cards?limit=100&offset=0", json={"filters": []}, headers=HEADERS, auth=AUTH, verify=False)
            rc_list = json.loads(rc_list.content)
            
            # for rc in rc_list.get('data', []):
            #     logger.info(f"Deleting rate card: {rc['rateCardName']}")
            #     requests.delete(URL + "?rateCardIds=" + rc['rateCardId'], headers=HEADERS, auth=AUTH, verify=False)
            #     logger.info(f"✓ Deleted rate card: {rc['rateCardName']}")
        else:
            error_count += 1
            logger.error(f"✗ Failed to create rate card (Status: {resp.status_code})")

    logger.info("=" * 80)
    logger.info("Rate Card Creation Summary")
    logger.info(f"  Total created: {created_count}")
    logger.info(f"  Total errors: {error_count}")
    logger.info(f"  Rate limit hits: {rate_limit_count}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
