#!/usr/bin/env python3
"""
NCM Reports Sharer using HTTP Basic Authentication
Shares all report types sequentially with rate limiting
"""
import sys
import json
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
NCM_BASE_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com"
REPORTS_URL = f"{NCM_BASE_URL}/v1/reports/share"
AUTH = ('admin', 'Nutanix.123')
HEADERS = {'Content-Type': 'application/json'}

SHARES_PER_MINUTE = 3  # Rate limit: 3 requests per minute

os.makedirs("reports", exist_ok=True)

# All report payloads in a list
REPORT_PAYLOADS = [
    # Current Spend Overview CSV
    {
        "name": "Current Spend Overview CSV",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["testing@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Overview PDF
    {
        "name": "Current Spend Overview PDF",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["testing@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Cluster CSV
    {
        "name": "Current Spend Cluster CSV",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["tesing@nutanix.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Cluster PDF
    {
        "name": "Current Spend Cluster PDF",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["tesing@nutanix.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Cost Center CSV
    {
        "name": "Current Spend Cost Center CSV",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["testing@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Cost Center PDF
    {
        "name": "Current Spend Cost Center PDF",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["testing@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Service Type CSV
    {
        "name": "Current Spend Service Type CSV",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"serviceType","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["tesitng@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Service Type PDF
    {
        "name": "Current Spend Service Type PDF",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"serviceType","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["tesitng@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Service CSV
    {
        "name": "Current Spend Service CSV",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["tesitng@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Current Spend Service PDF
    {
        "name": "Current Spend Service PDF",
        "payload": {"reportName":"Current Spending Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["tesitng@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Resource Metering XLS
    {
        "name": "Resource Metering XLS",
        "payload": {"reportName":"tesitng","reportConfig":{"reportType":"NX_RESOURCE_METERING","reportPeriod":{"timeUnit":"CUSTOM"},"reportTemplateDetails":{"fileType":"XLS"},"dataSource":{"accountId":"","clusterId":"00064002-1290-400a-0000-0000000193e1","timeUnit":"month","resourceGroupType":"NX_OVERVIEW","resourceGroupIds":[]},"timeRange":{"usageStartTime":1761955200,"usageEndTime":1764547140}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Overview CSV
    {
        "name": "Compute Overview CSV",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Overview PDF
    {
        "name": "Compute Overview PDF",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Cluster CSV
    {
        "name": "Compute Cluster CSV",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Cluster PDF
    {
        "name": "Compute Cluster PDF",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"account","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Services CSV
    {
        "name": "Compute Services CSV",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Services PDF
    {
        "name": "Compute Services PDF",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"service","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Sub-Services CSV
    {
        "name": "Compute Sub-Services CSV",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"subService","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Sub-Services PDF
    {
        "name": "Compute Sub-Services PDF",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"subService","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Cost Center CSV
    {
        "name": "Compute Cost Center CSV",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Cost Center PDF
    {
        "name": "Compute Cost Center PDF",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"costCenter","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Share the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Resource CSV
    {
        "name": "Compute Resource CSV",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"resource","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"CSV"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Download the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    },
    # Compute Resource PDF
    {
        "name": "Compute Resource PDF",
        "payload": {"reportName":"NX Compute Report","reportConfig":{"reportType":"NX_ANALYZE","dataSource":{"resourceGroupIds":[],"resourceGroupType":"NX_OVERVIEW","timeUnit":"month","mergeSpendAsOthersAfter":-1,"groupBy":"resource","currencyType":"TARGET","filters":{"services":{"operator":"in","values":["Nutanix Virtual Machine","Nutanix End User","Nutanix Edge"]}}},"reportPeriod":{"timeUnit":"CUSTOM"},"timeRange":{"usageEndTime":1764547140,"usageStartTime":1761955200},"reportTemplateDetails":{"fileType":"PDF"}},"shareConfig":{"mode":"EMAIL","recipients":["mohan@gmail.com"],"subject":"Download the data as per the applied filters in CSV format A report in PDF format that keeps the same visual structure of the UI while retaining all the applied filters Press Enter Space after input to add emails You can also add multiple emails separated by comma or semicolon"}}
    }
]


def main():
    logger.info("=" * 80)
    logger.info("NCM Cost Governance Reports Share Script Started")
    logger.info(f"Total Reports to Share: {len(REPORT_PAYLOADS)}")
    logger.info(f"Rate Limit: {SHARES_PER_MINUTE} requests per minute")
    logger.info("=" * 80)

    # Statistics tracking
    stats = {
        'total': len(REPORT_PAYLOADS),
        'success': 0,
        'failed': 0,
        'rate_limited': 0
    }

    share_count = 0
    
    try:
        # Get cluster list
        cluster_list_response = requests.post(
            f"{NCM_BASE_URL}/v1/cg/nutanix/metering/clusters?limit=500&offset=1",
            json={"timeUnit": "month", "timeRange": {"startTime": 1761955200, "endTime": 1764547140}, "resourceGroupType": "", "resourceGroupIds": [], "currencyType": "TARGET"},
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=30
        )
        cluster_list = json.loads(cluster_list_response.content)
        logger.info(f"Cluster list: {cluster_list}")
        cluster_list = [cluster['clusterId'] for cluster in cluster_list['items'][0]['data']]
        
        for i in range(100000):
            for cluster_id in cluster_list:
                for idx, report_config in enumerate(REPORT_PAYLOADS, 1):
                    logger.info("=" * 80)
                    logger.info(f"Cluster [{idx}/{stats['total']}]: {cluster_id}")
                    logger.info(f"Report [{idx}/{stats['total']}]: {report_config['name']}")
                    logger.info("=" * 80)
                    
                    try:
                        # Make API call
                        payload = report_config['payload']
                        response = requests.post(REPORTS_URL, json=payload, headers=HEADERS, auth=AUTH, verify=False, timeout=30)
                        
                        if response.status_code == 429:
                            stats['rate_limited'] += 1
                            logger.warning("Rate limited (429). Waiting 60 seconds before retry...")
                            time.sleep(60)
                            # Retry once
                            response = requests.post(REPORTS_URL, json=payload, headers=HEADERS, auth=AUTH, verify=False, timeout=30)
                        
                        if response.status_code in [200, 202]:
                            share_count += 1
                            stats['success'] += 1
                            logger.info(f"✓ Report request accepted (Status: {response.status_code})")
                            logger.info(f"Shared: {share_count}")
                        else:
                            stats['failed'] += 1
                            logger.error(f"✗ Failed: Status {response.status_code}")
                    
                    except Exception as e:
                        stats['failed'] += 1
                        logger.error(f"ERROR: Request failed - {str(e)}")
                    
                    # Rate limiting
                    if idx < stats['total']:
                        if idx % SHARES_PER_MINUTE == 0:
                            logger.info(f"Rate Limit: Waiting 60 seconds after {SHARES_PER_MINUTE} requests...")
                            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"FATAL ERROR: {str(e)}")
    finally:
        # Print final statistics
        logger.info("=" * 80)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total Reports: {stats['total']}")
        logger.info(f"Successful: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Rate Limited: {stats['rate_limited']}")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
