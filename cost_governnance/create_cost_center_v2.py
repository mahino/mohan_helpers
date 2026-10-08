#!/usr/bin/env python3
"""
Cost Center Creation Script v2
Creates cost centers for all PCs, clusters, and tags following a clean structure.
"""

import json
from random import random
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import logger_util
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger_util import get_logger, LoggedRequests

# Initialize logger
logger = get_logger(__file__)

# Initialize logged requests
requests = LoggedRequests(logger)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com"
REQUEST_TIMEOUT = 30
MAX_CC_PER_ACCOUNT = 80  # Limit cost centers per account (set to None for unlimited)
MAX_ACCOUNTS = 6  # Limit accounts to process (set to None for all)

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}


def api_get(endpoint, **kwargs):
    """GET request with timing"""
    url = f"{BASE_URL}{endpoint}"
    kwargs.setdefault('verify', False)
    kwargs.setdefault('headers', HEADERS)
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    
    start = time.time()
    response = requests.get(url, **kwargs)
    logger.debug(f"GET {endpoint} - {time.time() - start:.3f}s")
    return response


def api_post(endpoint, data=None, **kwargs):
    """POST request with timing"""
    url = f"{BASE_URL}{endpoint}"
    kwargs.setdefault('verify', False)
    kwargs.setdefault('headers', HEADERS)
    kwargs.setdefault('timeout', REQUEST_TIMEOUT)
    
    start = time.time()
    response = requests.post(url, data=json.dumps(data) if data else None, **kwargs)
    logger.debug(f"POST {endpoint} - {time.time() - start:.3f}s")
    return response


def get_all_pcs():
    """Get all available PC accounts"""
    # Get available accounts
    resp = api_get("/v1/cg/global/chargeback/availableAccounts")
    available = resp.json()
    pc_uuids = available.get('nx', [])
    
    # Get account details to map names
    resp = api_post("/api/nutanix/v3/accounts/list", data={
        "length": 250,
        "offset": 0,
        "filter": "state!=DELETED;type==nutanix_pc;offboarding==True"
    })
    
    if resp.status_code != 200:
        logger.error(f"Failed to get accounts list: {resp.status_code}")
        return {}
    
    accounts = resp.json()
    
    # Map PC name -> PC UUID
    pcs = {}
    for pc_uuid in pc_uuids:
        for entity in accounts.get('entities', []):
            if entity['status']['resources']['data'].get('pc_uuid') == pc_uuid:
                pc_name = entity['status']['name']
                pcs[pc_name] = pc_uuid
                break
    
    logger.info(f"Found {len(pcs)} PCs: {list(pcs.keys())}")
    return pcs


def get_clusters_for_pc(pc_uuid):
    """Get all clusters for a PC"""
    resp = api_get(f"/v1/cg/global/chargeback/availableAccounts/usedTags?provider=nx&parentAccount={pc_uuid}")
    data = resp.json()
    
    # Extract cluster UUIDs (skip 'parentAccount' key)
    clusters = [key for key in data.keys() if key != 'parentAccount']
    logger.info(f"  Found {len(clusters)} clusters")
    return clusters, data


def get_all_tags_for_pc(pc_uuid):
    """Get all available tag keys for a PC"""
    resp = api_get(f"/v1/cg/nx/analysis/dimensions/values?resourceGroupIds={pc_uuid}&dimensions=tagKeys&resourceGroupType=billingAccount")
    data = resp.json()
    tags = data.get('tagKeys', [])
    logger.info(f"  Found {len(tags)} tag keys")
    return tags


def get_tag_values(pc_uuid, tag_key):
    """Get values for a specific tag key"""
    # URL encode the tag key (nx:TagName -> tag.nx%253ATagName)
    tag_suffix = tag_key.split(':')[1] if ':' in tag_key else tag_key
    encoded_tag = f"tag.nx%253A{tag_suffix}"
    
    resp = api_get(f"/v1/cg/nx/analysis/dimensions/values?resourceGroupIds={pc_uuid}&dimensions={encoded_tag}&resourceGroupType=billingAccount")
    data = resp.json()
    
    # Return values for this tag
    return data.get(tag_key, [])


def get_used_tags_for_cluster(used_tags_data, cluster_uuid):
    """Extract used tags for a specific cluster from the usedTags response"""
    return used_tags_data.get(cluster_uuid, [])


def create_cost_center(pc_name, pc_uuid, cluster_uuid, tag_key, tag_value, exclude_tags, random_suffix):
    """Create a single cost center"""
    cluster_short = cluster_uuid[-5:]
    tag_short = tag_key.split(':')[1] if ':' in tag_key else tag_key
    
    cc_name = f"CC_{pc_name}_{cluster_short}_{tag_short}_{tag_value}_{random_suffix}"
    
    # Build payload
    payload = {
        "name": cc_name,
        "definitions": [{
            "provider": "nx",
            "parentAccount": pc_uuid,
            "filters": {
                "childAccounts": [cluster_uuid],
                "tags": [
                    {
                        "keys": [tag_key],
                        "values": [tag_value],
                        "operator": "in"
                    }
                ]
            }
        }],
        "permissions": {},
        "months": [datetime.now().strftime("%Y-%m")]
    }
    
    # Add exclusion tags (notIn) - deduplicate by (key, value) tuple
    seen_tags = set()
    seen_tags.add((tag_key, tag_value))  # Don't exclude the tag we're including
    
    for exclude in exclude_tags:
        if 'keys' not in exclude or 'values' not in exclude:
            continue
        if not exclude['keys'] or not exclude['values']:
            continue
            
        exc_key = exclude['keys'][0]
        exc_value = exclude['values'][0]
        
        # Skip if already added (deduplicate)
        tag_tuple = (exc_key, exc_value)
        if tag_tuple in seen_tags:
            logger.debug(f"  Skipping duplicate exclude tag: {exc_key}={exc_value}")
            continue
        
        seen_tags.add(tag_tuple)
        payload['definitions'][0]['filters']['tags'].append({
            "keys": [exc_key],
            "values": [exc_value],
            "operator": "notIn"
        })
    
    logger.debug(f"Creating cost center payload: {json.dumps(payload, indent=2)}")
    
    resp = api_post("/v1/cg/global/costCenter", data=payload)
    
    if resp.status_code == 200:
        logger.info(f"  ✓ Created: {cc_name}")
        return True
    else:
        logger.error(f"  ✗ Failed to create {cc_name}: {resp.status_code} - {resp.text}")
        return False


def main():
    """Main execution flow"""
    logger.info("=" * 80)
    logger.info("Starting Cost Center Creation v2")
    logger.info("=" * 80)
    
    start_time = time.time()
    random_suffix = int(random() * 1000000)
    
    total_created = 0
    total_errors = 0
    total_skipped = 0
    
    # Step 1: Get all PCs
    pcs = get_all_pcs()
    
    account_count = 0
    for pc_name, pc_uuid in pcs.items():
        # Limit accounts if configured
        if MAX_ACCOUNTS and account_count >= MAX_ACCOUNTS:
            logger.info(f"Reached account limit ({MAX_ACCOUNTS}), stopping")
            break
        account_count += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing PC: {pc_name} ({pc_uuid})")
        logger.info(f"{'='*60}")
        
        cc_count_for_account = 0
        
        # Step 2: Get clusters for this PC
        clusters, used_tags_data = get_clusters_for_pc(pc_uuid)
        
        # Step 3: Get all tags for this PC
        all_tags = get_all_tags_for_pc(pc_uuid)
        
        # Track used tags across all clusters for this PC
        used_tags_set = set()
        for cluster_uuid in clusters:
            cluster_used = get_used_tags_for_cluster(used_tags_data, cluster_uuid)
            for tag_info in cluster_used:
                if 'keys' in tag_info and tag_info['keys']:
                    used_tags_set.add(tag_info['keys'][0])
        
        logger.info(f"  Already used tags: {len(used_tags_set)}")
        
        # Track tags created during this run (per cluster) for exclusion
        # Structure: {cluster_uuid: [{'keys': [key], 'values': [value]}, ...]}
        created_tags_per_cluster = {cluster_uuid: [] for cluster_uuid in clusters}
        
        # Step 4: For each tag not in used tags
        for tag_key in all_tags:
            # Check account limit
            if MAX_CC_PER_ACCOUNT and cc_count_for_account >= MAX_CC_PER_ACCOUNT:
                logger.info(f"  Reached CC limit per account ({MAX_CC_PER_ACCOUNT})")
                break
            
            # Skip if tag already used
            if tag_key in used_tags_set:
                logger.debug(f"  Skipping used tag: {tag_key}")
                total_skipped += 1
                continue
            
            # Get values for this tag
            tag_values = get_tag_values(pc_uuid, tag_key)
            if not tag_values:
                logger.debug(f"  No values for tag: {tag_key}")
                continue
            
            tag_value = tag_values[0]  # Use first value
            
            # Step 5: Create CC for each cluster
            for cluster_uuid in clusters:
                # Check account limit again
                if MAX_CC_PER_ACCOUNT and cc_count_for_account >= MAX_CC_PER_ACCOUNT:
                    break
                
                # Get exclusion tags for this cluster (from API + created during this run)
                cluster_used_tags = get_used_tags_for_cluster(used_tags_data, cluster_uuid)
                # Combine with tags created during this run
                all_cluster_used_tags = cluster_used_tags + created_tags_per_cluster[cluster_uuid]
                exclude_tags = [t for t in all_cluster_used_tags if t.get('values', [None])[0] != tag_value]
                
                # Create cost center
                success = create_cost_center(
                    pc_name=pc_name,
                    pc_uuid=pc_uuid,
                    cluster_uuid=cluster_uuid,
                    tag_key=tag_key,
                    tag_value=tag_value,
                    exclude_tags=exclude_tags,
                    random_suffix=random_suffix
                )
                
                if success:
                    total_created += 1
                    cc_count_for_account += 1
                    # Track this tag as created for this cluster
                    created_tags_per_cluster[cluster_uuid].append({
                        'keys': [tag_key],
                        'values': [tag_value]
                    })
                else:
                    total_errors += 1
            
            # Step 6: Add tag to used tags
            used_tags_set.add(tag_key)
        
        logger.info(f"  Account summary: {cc_count_for_account} cost centers created")
    
    # Final summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  PCs processed:        {account_count}")
    logger.info(f"  Cost centers created: {total_created}")
    logger.info(f"  Errors:               {total_errors}")
    logger.info(f"  Tags skipped (used):  {total_skipped}")
    logger.info(f"  Total time:           {elapsed:.2f}s ({elapsed/60:.2f} min)")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

