#!/usr/bin/env python3
"""
NCM UDM Reports Downloader using HTTP Basic Authentication
"""
import sys
import time
import os
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
REPORTS_URL = "https://ncm.services.nconprem-10-53-58-35.ccpnx.com/v1/cg/config/rate-cards/actions/download?cloud=Nutanix"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}

MAX_DOWNLOADS = 500
RATE_LIMIT_SLEEP = 60
DOWNLOADS_PER_MINUTE = 100
SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE = 60

os.makedirs("reports", exist_ok=True)


def download_report():
    """Download a single report"""
    try:
        response = requests.get(REPORTS_URL, headers=HEADERS, auth=AUTH, verify=False, timeout=30)
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None


def main():
    logger.info("=" * 80)
    logger.info("NCM UDM Reports Download Script Started")
    logger.info(f"Max Downloads: {MAX_DOWNLOADS}")
    logger.info(f"Rate Limit: {DOWNLOADS_PER_MINUTE} requests per minute")
    logger.info("=" * 80)

    download_count = 0
    sleep_count = 0
    
    while download_count < MAX_DOWNLOADS:
        
        if download_count % DOWNLOADS_PER_MINUTE == 0 and download_count > 0:
            logger.info(f"Sleeping for {SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE} seconds after every {DOWNLOADS_PER_MINUTE} UDM Report downloads...")
            time.sleep(SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE)
        
        response = download_report()
        if response is None:
            logger.error("Request failed, retrying in 1 second...")
            time.sleep(1)
            continue

        if response.status_code == 429:
            sleep_count += 1
            logger.warning(f"Rate limited (429). Sleeping for {RATE_LIMIT_SLEEP}s. Sleep count: {sleep_count}, Downloaded: {download_count}")
            time.sleep(RATE_LIMIT_SLEEP)

        elif response.status_code in [200, 202]:
            download_count += 1
            logger.info(f"✓ UDM Report {download_count}/{MAX_DOWNLOADS} successfully downloaded")
            sleep_count = 0
            time.sleep(0.5)
        else:
            logger.error(f"✗ Download failed with status {response.status_code}")
            time.sleep(1)

    logger.info("=" * 80)
    logger.info(f"Download completed! Total: {download_count}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
