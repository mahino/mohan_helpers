#!/usr/bin/env python3
"""
Script to fetch storage summary from Nutanix Prism Element.
Matches the data shown in the Storage Summary UI.

Usage:
    python get_storage_summary.py --pe-ip 10.46.117.165 --username admin --password nutanix/4u
"""

import requests
import argparse
import json
from requests.auth import HTTPBasicAuth

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


def bytes_to_tib(bytes_val):
    """Convert bytes to TiB."""
    return bytes_val / (1024 ** 4)


def bytes_to_gib(bytes_val):
    """Convert bytes to GiB."""
    return bytes_val / (1024 ** 3)


def get_cluster_info(pe_ip, username, password):
    """Get basic cluster information including UUID."""
    base_url = f"https://{pe_ip}:9440"
    auth = HTTPBasicAuth(username, password)
    url = f"{base_url}/PrismGateway/services/rest/v1/clusters"
    
    try:
        response = requests.get(url, auth=auth, verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("entities"):
            return None
        return data["entities"][0]
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch cluster info: {e}")
        return None


def get_storage_metric(pe_ip, cluster_uuid, metric_name, username, password):
    """Fetch a specific storage metric."""
    base_url = f"https://{pe_ip}:9440"
    auth = HTTPBasicAuth(username, password)
    url = f"{base_url}/PrismGateway/services/rest/v1/clusters/{cluster_uuid}/stats"
    params = {"metrics": metric_name}
    
    try:
        response = requests.get(url, auth=auth, params=params, verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data["statsSpecificResponses"][0]["successful"]:
            return data["statsSpecificResponses"][0]["values"][0]
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch {metric_name}: {e}")
        return None


def get_storage_summary(pe_ip, username, password):
    """
    Fetch storage summary from Prism Element using 3 specific APIs.
    
    Args:
        pe_ip (str): Prism Element IP address
        username (str): Username for authentication
        password (str): Password for authentication
    
    Returns:
        dict: Storage statistics including capacity, usage, and recovery points
    """
    print(f"[INFO] Fetching storage summary from {pe_ip}...")
    
    # Step 1: Get cluster info (for UUID and basic details)
    cluster = get_cluster_info(pe_ip, username, password)
    if not cluster:
        print("[ERROR] Failed to get cluster information")
        return None
    
    cluster_uuid = cluster.get("uuid")
    print(f"[INFO] Cluster UUID: {cluster_uuid}")
    
    # Step 2: Fetch the 3 storage metrics
    print(f"[INFO] Fetching storage.capacity_bytes...")
    total_capacity_bytes = get_storage_metric(pe_ip, cluster_uuid, "storage.capacity_bytes", username, password)
    
    print(f"[INFO] Fetching storage.usage_bytes...")
    total_usage_bytes = get_storage_metric(pe_ip, cluster_uuid, "storage.usage_bytes", username, password)
    
    print(f"[INFO] Fetching storage.snapshot_reclaimable_bytes...")
    snapshot_reclaimable_bytes = get_storage_metric(pe_ip, cluster_uuid, "storage.snapshot_reclaimable_bytes", username, password)
    
    if total_capacity_bytes is None or total_usage_bytes is None or snapshot_reclaimable_bytes is None:
        print("[ERROR] Failed to fetch one or more storage metrics")
        return None
    
    # Calculate free space
    free_bytes = total_capacity_bytes - total_usage_bytes
    
    storage_summary = {
        "cluster_name": cluster.get("name"),
        "cluster_uuid": cluster_uuid,
        "cluster_ip": cluster.get("clusterExternalIPAddress"),
        "storage_type": cluster.get("storageType"),
        "num_nodes": cluster.get("numNodes"),
        "version": cluster.get("version"),
        
        # Storage metrics (bytes)
        "total_capacity_bytes": total_capacity_bytes,
        "total_usage_bytes": total_usage_bytes,
        "free_bytes": free_bytes,
        "snapshot_reclaimable_bytes": snapshot_reclaimable_bytes,
        
        # Storage metrics (human-readable)
        "total_capacity_tib": bytes_to_tib(total_capacity_bytes),
        "total_usage_tib": bytes_to_tib(total_usage_bytes),
        "free_tib": bytes_to_tib(free_bytes),
        "recovery_points_gib": bytes_to_gib(snapshot_reclaimable_bytes),
    }
    
    return storage_summary


def display_storage_summary(summary):
    """
    Display storage summary in a formatted manner matching the UI.
    Shows only the 3 main metrics from the APIs.
    """
    if not summary:
        print("[ERROR] No summary data to display")
        return
    
    print("\n" + "="*60)
    print("STORAGE SUMMARY")
    print("="*60)
    
    print(f"\nCluster Information:")
    print(f"  Name:         {summary['cluster_name']}")
    print(f"  IP:           {summary['cluster_ip']}")
    print(f"  UUID:         {summary['cluster_uuid']}")
    print(f"  Version:      {summary['version']}")
    print(f"  Storage Type: {summary['storage_type']}")
    print(f"  Nodes:        {summary['num_nodes']}")
    
    print(f"\n{'Storage Summary (3 Key Metrics)':^60}")
    print("-"*60)
    print(f"  Total Capacity:      {summary['total_capacity_tib']:.2f} TiB")
    print(f"                       ({summary['total_capacity_bytes']:,} bytes)")
    print()
    print(f"  Total Usage:         {summary['total_usage_tib']:.2f} TiB")
    print(f"                       ({summary['total_usage_bytes']:,} bytes)")
    print()
    print(f"  Recovery Points:     {summary['recovery_points_gib']:.2f} GiB")
    print(f"                       ({summary['snapshot_reclaimable_bytes']:,} bytes)")
    
    # Calculate usage percentage
    if summary['total_capacity_bytes'] > 0:
        usage_pct = (summary['total_usage_bytes'] / summary['total_capacity_bytes']) * 100
        print(f"\n  Usage Percentage:    {usage_pct:.2f}%")
        print(f"  Free Space:          {summary['free_tib']:.2f} TiB ({summary['free_bytes']:,} bytes)")
        
        # Visual bar (similar to UI)
        bar_length = 50
        filled = int(bar_length * usage_pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n  [{bar}]")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Fetch storage summary from Nutanix Prism Element")
    parser.add_argument("--pe-ip", required=True, help="Prism Element IP address")
    parser.add_argument("--username", default="admin", help="Username (default: admin)")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    summary = get_storage_summary(args.pe_ip, args.username, args.password)
    
    if summary:
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            display_storage_summary(summary)
    else:
        exit(1)


if __name__ == "__main__":
    main()
