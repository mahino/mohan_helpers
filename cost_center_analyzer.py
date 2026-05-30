#!/usr/bin/env python3
"""
Cost Center and Business Unit Analyzer
Analyzes cost center definitions and groups them by parent account.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent))
from logger_util import get_logger

# Initialize logger
logger = get_logger(__file__)


def analyze_cost_centers(cost_centers_data):
    """
    Analyze cost center definitions and group by parent account.
    
    Args:
        cost_centers_data: Dictionary containing cost center items
    
    Returns:
        dict: Analysis results grouped by parent account
    """
    results = defaultdict(list)
    processed_count = 0
    deleted_count = 0
    
    logger.info("Analyzing cost center definitions...")
    
    for item in cost_centers_data.get("items", []):
        # Skip deleted items
        if item.get('isDeleted', False):
            deleted_count += 1
            logger.debug(f"Skipping deleted cost center: {item.get('name', 'Unknown')}")
            continue
        
        processed_count += 1
        
        try:
            # Extract parent account
            definitions = item.get("definitions", [])
            if not definitions:
                logger.warning(f"No definitions found for cost center: {item.get('name', 'Unknown')}")
                continue
            
            parent_account = definitions[0].get("parentAccount", "Unknown")
            
            # Build cost center info
            cost_center_info = [item.get("name", "Unknown")]
            
            # Extract tag filters
            filters = definitions[0].get("filters", {})
            tags = filters.get("tags", [])
            
            for tag in tags:
                keys = tag.get("keys", [])
                values = tag.get("values", [])
                operator = tag.get("operator", "")
                
                if keys and values:
                    tag_info = f"{keys[0]}={values[0]}={operator}"
                    cost_center_info.append(tag_info)
            
            results[parent_account].append(cost_center_info)
            
            logger.debug(f"Processed cost center: {item.get('name')} under {parent_account}")
            
        except Exception as e:
            logger.error(f"Error processing cost center {item.get('name', 'Unknown')}: {e}")
    
    logger.info(f"Analysis complete: {processed_count} processed, {deleted_count} deleted")
    
    return dict(results)


def print_analysis_summary(results):
    """Print formatted analysis summary."""
    logger.info("=" * 80)
    logger.info("COST CENTER ANALYSIS SUMMARY")
    logger.info("=" * 80)
    
    total_accounts = len(results)
    total_cost_centers = sum(len(cost_centers) for cost_centers in results.values())
    
    logger.info(f"Total parent accounts: {total_accounts}")
    logger.info(f"Total cost centers: {total_cost_centers}")
    logger.info("")
    
    # Show breakdown by parent account
    for parent_account, cost_centers in results.items():
        logger.info(f"Parent Account: {parent_account}")
        logger.info(f"  Cost Centers: {len(cost_centers)}")
        
        # Show first few cost centers as examples
        for i, cc_info in enumerate(cost_centers[:3]):
            cc_name = cc_info[0] if cc_info else "Unknown"
            tag_count = len(cc_info) - 1 if len(cc_info) > 1 else 0
            logger.info(f"    - {cc_name} ({tag_count} tags)")
        
        if len(cost_centers) > 3:
            logger.info(f"    ... and {len(cost_centers) - 3} more")
        logger.info("")
    
    logger.info("=" * 80)


def main():
    """Main execution function."""
    # Sample data structure - replace with actual data source
    sample_data = {
        "items": [
            {
                "name": "CC_Example_1",
                "isDeleted": False,
                "definitions": [
                    {
                        "parentAccount": "account_123",
                        "filters": {
                            "tags": [
                                {
                                    "keys": ["environment"],
                                    "values": ["production"],
                                    "operator": "equals"
                                },
                                {
                                    "keys": ["team"],
                                    "values": ["engineering"],
                                    "operator": "equals"
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "name": "CC_Example_2",
                "isDeleted": False,
                "definitions": [
                    {
                        "parentAccount": "account_456",
                        "filters": {
                            "tags": [
                                {
                                    "keys": ["department"],
                                    "values": ["marketing"],
                                    "operator": "equals"
                                }
                            ]
                        }
                    }
                ]
            },
            {
                "name": "CC_Deleted",
                "isDeleted": True,
                "definitions": []
            }
        ]
    }
    
    logger.info("Starting Cost Center Analysis")
    
    # TODO: Replace with actual data loading from API or file
    # For now, using sample data
    cost_centers_data = sample_data
    
    # Analyze cost centers
    results = analyze_cost_centers(cost_centers_data)
    
    # Print summary
    print_analysis_summary(results)
    
    # Output detailed results as JSON
    print("\nDetailed Results:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
