#!/usr/bin/env python3
"""
Get Storage Statistics from Prism Central/Element using v1 REST API

Usage:
    python3 get_storage_stats.py <pc_or_pe_ip> [cluster_uuid]
    
Example:
    python3 get_storage_stats.py 10.46.208.63
    python3 get_storage_stats.py 10.122.28.170 00065035-daa1-70e4-7faf-ac1f6b61e0cf
"""

import sys
import json
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if len(sys.argv) < 2:
    print("Usage: python3 get_storage_stats.py <pc_or_pe_ip> [cluster_uuid]")
    print("\nExample:")
    print("  python3 get_storage_stats.py 10.46.208.63")
    print("  python3 get_storage_stats.py 10.122.28.170 00065035-daa1-70e4-7faf-ac1f6b61e0cf")
    sys.exit(1)

# Configuration
PC_IP = sys.argv[1]
CLUSTER_UUID = sys.argv[2] if len(sys.argv) > 2 else None
BASE_URL = f"https://{PC_IP}:9440"
USERNAME = "admin"
PASSWORD = "Nutanix.123"

# Create session
client = requests.Session()
client.auth = HTTPBasicAuth(USERNAME, PASSWORD)
client.headers = {'Accept': 'application/json'}
client.verify = False


def bytes_to_gib(bytes_val):
    """Convert bytes to GiB"""
    return bytes_val / (1024**3)


def bytes_to_tib(bytes_val):
    """Convert bytes to TiB"""
    return bytes_val / (1024**4)


def format_bytes(bytes_val):
    """Format bytes to human readable"""
    tib = bytes_to_tib(bytes_val)
    if tib >= 1:
        return f"{tib:.2f} TiB"
    else:
        return f"{bytes_to_gib(bytes_val):.2f} GiB"


def get_storage_stats(cluster_uuid=None):
    """Get storage usage statistics"""
    url = f"{BASE_URL}/PrismGateway/services/rest/v1/clusters"
    params = {'projection': 'usage_stats'}
    
    if cluster_uuid:
        params['proxyClusterUuid'] = cluster_uuid
    
    print("="*80)
    print(f"Fetching storage stats from {BASE_URL}")
    if cluster_uuid:
        print(f"Cluster UUID: {cluster_uuid}")
    print("="*80)
    
    try:
        response = client.get(url, params=params)
        
        if response.status_code != 200:
            print(f"ERROR: Status {response.status_code}")
            print(response.content.decode('utf-8')[:500])
            return None
        
        data = response.json()
        
        if not data.get('entities'):
            print("ERROR: No cluster entities found in response")
            return None
        
        # Process each cluster
        for cluster in data['entities']:
            print_cluster_storage(cluster)
            print()
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def print_cluster_storage(cluster):
    """Print storage statistics for a cluster"""
    cluster_name = cluster.get('name', 'Unknown')
    cluster_uuid = cluster.get('uuid', 'Unknown')
    usage_stats = cluster.get('usageStats', {})
    
    if not usage_stats:
        print(f"Cluster: {cluster_name} ({cluster_uuid})")
        print("  No usage statistics available")
        return
    
    # Extract key metrics (all in bytes)
    total_capacity = int(usage_stats.get('storage.capacity_bytes', 0))
    used_capacity = int(usage_stats.get('storage.usage_bytes', 0))
    free_space = int(usage_stats.get('storage.free_bytes', 0))
    logical_usage = int(usage_stats.get('storage.logical_usage_bytes', 0))
    snapshot_reclaimable = int(usage_stats.get('storage.snapshot_reclaimable_bytes', 0))
    recycle_bin = int(usage_stats.get('storage.recycle_bin_usage_bytes', 0))
    reserved = int(usage_stats.get('storage.reserved_usage_bytes', 0))
    
    # Data reduction stats
    overall_saved = int(usage_stats.get('data_reduction.overall.saved_bytes', 0))
    overall_ratio_ppm = int(usage_stats.get('data_reduction.overall.saving_ratio_ppm', 0))
    compression_saved = int(usage_stats.get('data_reduction.compression.saved_bytes', 0))
    dedup_saved = int(usage_stats.get('data_reduction.dedup.saved_bytes', 0))
    thin_provision_saved = int(usage_stats.get('data_reduction.thin_provision.saved_bytes', 0))
    clone_saved = int(usage_stats.get('data_reduction.clone.saved_bytes', 0))
    
    # Storage tier stats (if available)
    ssd_capacity = int(usage_stats.get('storage_tier.ssd.capacity_bytes', 0))
    ssd_usage = int(usage_stats.get('storage_tier.ssd.usage_bytes', 0))
    ssd_free = int(usage_stats.get('storage_tier.ssd.free_bytes', 0))
    
    hdd_capacity = int(usage_stats.get('storage_tier.das-sata.capacity_bytes', 0))
    hdd_usage = int(usage_stats.get('storage_tier.das-sata.usage_bytes', 0))
    hdd_free = int(usage_stats.get('storage_tier.das-sata.free_bytes', 0))
    
    # Calculate percentages
    usage_pct = (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
    overall_ratio = overall_ratio_ppm / 1_000_000 if overall_ratio_ppm > 0 else 1.0
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"Cluster: {cluster_name}")
    print(f"UUID: {cluster_uuid}")
    print(f"{'='*80}")
    
    print(f"\n📊 Storage Summary")
    print(f"  Total Capacity:        {format_bytes(total_capacity):>15}  ({total_capacity:,} bytes)")
    print(f"  Used Capacity:         {format_bytes(used_capacity):>15}  ({usage_pct:.1f}%)")
    print(f"  Free Space:            {format_bytes(free_space):>15}")
    print(f"  Logical Usage:         {format_bytes(logical_usage):>15}")
    
    if snapshot_reclaimable > 0:
        print(f"  Recovery Points:       {format_bytes(snapshot_reclaimable):>15}")
    
    if recycle_bin > 0:
        print(f"  Recycle Bin:           {format_bytes(recycle_bin):>15}")
    
    if reserved > 0:
        print(f"  Reserved:              {format_bytes(reserved):>15}")
    
    # Storage tiers
    if ssd_capacity > 0 or hdd_capacity > 0:
        print(f"\n💾 Storage Tiers")
        if ssd_capacity > 0:
            ssd_pct = (ssd_usage / ssd_capacity * 100) if ssd_capacity > 0 else 0
            print(f"  SSD Tier:")
            print(f"    Capacity:            {format_bytes(ssd_capacity):>15}")
            print(f"    Used:                {format_bytes(ssd_usage):>15}  ({ssd_pct:.1f}%)")
            print(f"    Free:                {format_bytes(ssd_free):>15}")
        
        if hdd_capacity > 0:
            hdd_pct = (hdd_usage / hdd_capacity * 100) if hdd_capacity > 0 else 0
            print(f"  HDD Tier:")
            print(f"    Capacity:            {format_bytes(hdd_capacity):>15}")
            print(f"    Used:                {format_bytes(hdd_usage):>15}  ({hdd_pct:.1f}%)")
            print(f"    Free:                {format_bytes(hdd_free):>15}")
    
    # Data reduction
    if overall_saved > 0:
        print(f"\n📉 Data Reduction")
        print(f"  Overall Savings:       {format_bytes(overall_saved):>15}  ({overall_ratio:.1f}x)")
        
        if compression_saved > 0:
            print(f"  Compression Saved:     {format_bytes(compression_saved):>15}")
        
        if dedup_saved > 0:
            print(f"  Deduplication Saved:   {format_bytes(dedup_saved):>15}")
        
        if thin_provision_saved > 0:
            print(f"  Thin Provision Saved:  {format_bytes(thin_provision_saved):>15}")
        
        if clone_saved > 0:
            print(f"  Clone Saved:           {format_bytes(clone_saved):>15}")
    
    print(f"\n{'='*80}")


def list_all_clusters():
    """List all clusters without detailed stats"""
    url = f"{BASE_URL}/PrismGateway/services/rest/v1/clusters"
    
    print("="*80)
    print(f"Listing all clusters on {BASE_URL}")
    print("="*80)
    
    try:
        response = client.get(url)
        
        if response.status_code != 200:
            print(f"ERROR: Status {response.status_code}")
            print(response.content.decode('utf-8')[:500])
            return
        
        data = response.json()
        
        if not data.get('entities'):
            print("No clusters found")
            return
        
        print(f"\nFound {len(data['entities'])} cluster(s):\n")
        for cluster in data['entities']:
            name = cluster.get('name', 'Unknown')
            uuid = cluster.get('uuid', 'Unknown')
            version = cluster.get('version', 'Unknown')
            num_nodes = cluster.get('numNodes', 'Unknown')
            print(f"  • {name}")
            print(f"    UUID:       {uuid}")
            print(f"    Version:    {version}")
            print(f"    Nodes:      {num_nodes}")
            print()
    
    except Exception as e:
        print(f"ERROR: {e}")


# Main execution
if __name__ == "__main__":
    # If no cluster UUID provided, list all clusters first
    if not CLUSTER_UUID:
        list_all_clusters()
        print("\nTip: To get detailed storage stats, provide cluster UUID:")
        print(f"     python3 get_storage_stats.py {PC_IP} <cluster-uuid>\n")
    
    # Get storage stats
    get_storage_stats(CLUSTER_UUID)
