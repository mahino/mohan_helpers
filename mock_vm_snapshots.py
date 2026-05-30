#!/usr/bin/env python3
"""
Script to generate mock recovery point data with daily updates for the NDP table schema.

Day 1: Creates fresh recovery points (identical behavior to mock_recovery_points.py)
Day 2+: Generates incremental update events on existing recovery points:
  1. Size updates (recovery_point only): New row with same entity_id, updated size,
     creation_time preserved. Skipped for vm_recovery_point (no size field).
  2. Delete + create: Old RP marked is_deleted=True, new RP created with different UUID.

Replication Model (same as mock_recovery_points.py):
- First two clusters are Cluster A (source) and Cluster B (replica destination)
- VMs in Cluster A: 25 RPs locally + 25 replicated to Cluster B = 50 total
- VMs in Cluster B and other clusters: 50 RPs locally, no replication

Usage:
    python mock_recovery_points_with_updates.py --start-date 2025-10-01
    python mock_recovery_points_with_updates.py --start-date 2025-10-01 --days 30
    python mock_recovery_points_with_updates.py --start-date 2025-10-01 --skip-db-connection --seed 42
    python mock_recovery_points_with_updates.py --start-date 2025-10-01 --size-update-fraction 0.2 --delete-fraction 0.15
"""

import argparse
import copy
import csv
import gzip
import json
import os
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import sys

try:
    from clickhouse_connect import get_client  # type: ignore
except ImportError:
    print("Warning: clickhouse-connect package not installed. Use --skip-db-connection for sample data.")
    get_client = None

# --- Hardcoded constants ---
DAYS_OF_DATA = 5
OUTPUT_FOLDER = 'ndp_recovery_point_updates_output'
TARGET_RECOVERY_POINTS_PER_VM = 50
REPLICATED_RPS_PER_VM = 25
CG_VMS_PER_CLUSTER = 15
VG_DISK_RPS_PER_CLUSTER = 5

# Update fractions (for day 2+) — every mutable RP gets exactly one update type
SIZE_UPDATE_FRACTION = 0.5
DELETE_FRACTION = 0.5
UNTOUCHED_FRACTION = 0.1  # 10% of day-1 RPs are never updated
CHUNKS_PER_DAY = 5


# ---------------------------------------------------------------------------
# Helper functions (shared with mock_recovery_points.py)
# ---------------------------------------------------------------------------

def generate_uuid() -> str:
    return str(uuid.uuid4())


def convert_to_uuid_string(value) -> str:
    if isinstance(value, bytes):
        value = value.rstrip(b'\x00').decode('utf-8', errors='ignore')
    elif not isinstance(value, str):
        value = str(value)
    if value.startswith("b'") and value.endswith("'"):
        value = value[2:-1]
    return value.strip()


# ---------------------------------------------------------------------------
# DB fetch functions (identical to mock_recovery_points.py)
# ---------------------------------------------------------------------------

def fetch_vm_data_for_date(client, date: str) -> List[Dict]:
    query = f"""
    SELECT DISTINCT
        entity_id AS vmId,
        cluster_uuid,
        source_pc_cluster_uuid,
        cluster_name
    FROM ncm.config_history_vm_consolidated(startDate='{date}')
    """
    try:
        result = client.query(query)
        vms = []
        for row in result.result_rows:
            vms.append({
                'vmId': convert_to_uuid_string(row[0]),
                'cluster_uuid': convert_to_uuid_string(row[1]),
                'source_pc_cluster_uuid': convert_to_uuid_string(row[2]) if row[2] else '',
                'cluster_name': row[3] if row[3] else 'Unknown'
            })
        return vms
    except Exception as e:
        print(f"Error fetching VM data for date {date}: {e}")
        return []


def fetch_clusters_for_date(client, date: str) -> List[Dict]:
    cluster_names_query = f"""
    SELECT DISTINCT cluster_uuid, source_pc_cluster_uuid, cluster_name
    FROM ncm.config_history_cluster_consolidated(startDate='{date}')
    """
    cluster_names_map = {}
    try:
        result = client.query(cluster_names_query)
        for row in result.result_rows:
            cluster_uuid = convert_to_uuid_string(row[0])
            cluster_names_map[cluster_uuid] = {
                'source_pc_cluster_uuid': convert_to_uuid_string(row[1]) if row[1] else '',
                'cluster_name': row[2] if row[2] else 'Unknown'
            }
    except Exception as e:
        print(f"Warning: Error fetching cluster names for date {date}: {e}")

    nodes_query = f"""
    SELECT DISTINCT cluster_uuid, source_pc_cluster_uuid
    FROM ncm.config_history_node_consolidated(startDate='{date}')
    """
    clusters_with_nodes = {}
    try:
        result = client.query(nodes_query)
        for row in result.result_rows:
            cluster_uuid = convert_to_uuid_string(row[0])
            source_pc_cluster_uuid = convert_to_uuid_string(row[1]) if row[1] else ''
            clusters_with_nodes[cluster_uuid] = source_pc_cluster_uuid
    except Exception as e:
        print(f"Error fetching clusters with nodes for date {date}: {e}")
        return []

    disks_query = f"""
    SELECT DISTINCT cluster_uuid, source_pc_cluster_uuid
    FROM ncm.config_history_disk_consolidated(startDate='{date}')
    """
    clusters_with_disks = {}
    try:
        result = client.query(disks_query)
        for row in result.result_rows:
            cluster_uuid = convert_to_uuid_string(row[0])
            source_pc_cluster_uuid = convert_to_uuid_string(row[1]) if row[1] else ''
            clusters_with_disks[cluster_uuid] = source_pc_cluster_uuid
    except Exception as e:
        print(f"Error fetching clusters with disks for date {date}: {e}")
        return []

    clusters_with_both = set(clusters_with_nodes.keys()).intersection(set(clusters_with_disks.keys()))
    clusters = []
    for cluster_uuid in clusters_with_both:
        cluster_info = cluster_names_map.get(cluster_uuid, {})
        source_pc_cluster_uuid = cluster_info.get('source_pc_cluster_uuid') or clusters_with_nodes.get(cluster_uuid) or ''
        clusters.append({
            'cluster_uuid': cluster_uuid,
            'source_pc_cluster_uuid': source_pc_cluster_uuid,
            'cluster_name': cluster_info.get('cluster_name', f'Cluster-{cluster_uuid[:8]}')
        })
    return clusters


# ---------------------------------------------------------------------------
# Sample data generation (identical to mock_recovery_points.py)
# ---------------------------------------------------------------------------

def generate_sample_data_once(num_vms: int = 40, num_clusters: int = 4, num_pcs: int = 2) -> Tuple[List[Dict], List[Dict]]:
    clusters = []
    vms = []
    pc_uuids = [generate_uuid() for _ in range(num_pcs)]
    for i in range(num_clusters):
        cluster_uuid = generate_uuid()
        pc_uuid = pc_uuids[i % num_pcs]
        clusters.append({
            'cluster_uuid': cluster_uuid,
            'source_pc_cluster_uuid': pc_uuid,
            'cluster_name': f'Sample-Cluster-{i + 1}'
        })
    for i in range(num_vms):
        cluster = clusters[i % num_clusters]
        vms.append({
            'vmId': generate_uuid(),
            'cluster_uuid': cluster['cluster_uuid'],
            'source_pc_cluster_uuid': cluster['source_pc_cluster_uuid'],
            'cluster_name': cluster['cluster_name']
        })
    return vms, clusters


def generate_timestamps_for_day(base_date: datetime, count: int) -> List[datetime]:
    if count <= 0:
        return []
    interval_seconds = (24 * 60 * 60) // count
    timestamps = []
    for i in range(count):
        offset_seconds = i * interval_seconds + random.randint(0, interval_seconds // 2)
        timestamps.append(base_date + timedelta(seconds=offset_seconds))
    return timestamps


# ---------------------------------------------------------------------------
# Entry creation functions (identical to mock_recovery_points.py)
# ---------------------------------------------------------------------------

def create_vm_recovery_point_entry(
    entity_id: str, domain_id: str, account_id: str, provider_id: str,
    timestamp: datetime, name: str, backend_snapshot_uuid: str,
    source_cluster_uuid: str, cluster_uuid: str, entity_uuid: str,
    created_timestamp_usecs: str
) -> Dict:
    processed_timestamp = timestamp + timedelta(minutes=random.randint(1, 30))
    payload = {
        "name": name,
        "backend_snapshot_uuid": backend_snapshot_uuid,
        "source_cluster_uuid": source_cluster_uuid,
        "cluster_uuid": cluster_uuid,
        "entity_uuid": entity_uuid,
        "creation_time_usecs": int(created_timestamp_usecs)
    }
    return {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        '__processed_timestamp': processed_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'entity_id': entity_id,
        'entity_type': 'vm_recovery_point',
        'domain_id': domain_id,
        'account_id': account_id,
        'provider_id': provider_id,
        'is_deleted': False,
        'collection_timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'payload': payload
    }


def create_recovery_point_entry(
    entity_id: str, domain_id: str, account_id: str, provider_id: str,
    timestamp: datetime, name: str, vm_recovery_point_uuid_list: List[str],
    location_agnostic_uuid: str, vm_recovery_point_total_exclusive_usage_bytes: List[str],
    source_cluster_uuid: str, source_domain_manager_uuid: str,
    vm_live_entity_uuid_list: List[str], creation_time: str, rp_uuid: str
) -> Dict:
    processed_timestamp = timestamp + timedelta(minutes=random.randint(1, 30))
    payload = {
        "name": name,
        "vm_recovery_point_uuid_list": vm_recovery_point_uuid_list,
        "location_agnostic_uuid": location_agnostic_uuid,
        "vm_recovery_point_total_exclusive_usage_bytes": [int(x) for x in vm_recovery_point_total_exclusive_usage_bytes],
        "source_cluster_uuid": source_cluster_uuid,
        "source_domain_manager_uuid": source_domain_manager_uuid,
        "vm_live_entity_uuid_list": vm_live_entity_uuid_list,
        "creation_time": int(creation_time),
        "uuid": rp_uuid
    }
    return {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        '__processed_timestamp': processed_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'entity_id': entity_id,
        'entity_type': 'recovery_point',
        'domain_id': domain_id,
        'account_id': account_id,
        'provider_id': provider_id,
        'is_deleted': False,
        'collection_timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'payload': payload
    }


def create_vg_disk_recovery_point_entry(
    entity_id: str, domain_id: str, account_id: str, provider_id: str,
    timestamp: datetime, name: str, location_agnostic_uuid: str,
    source_cluster_uuid: str, source_domain_manager_uuid: str,
    creation_time: str, rp_uuid: str
) -> Dict:
    processed_timestamp = timestamp + timedelta(minutes=random.randint(1, 30))
    payload = {
        "name": name,
        "vm_recovery_point_uuid_list": [],
        "location_agnostic_uuid": location_agnostic_uuid,
        "vm_recovery_point_total_exclusive_usage_bytes": [],
        "source_cluster_uuid": source_cluster_uuid,
        "source_domain_manager_uuid": source_domain_manager_uuid,
        "vm_live_entity_uuid_list": [],
        "creation_time": int(creation_time),
        "uuid": rp_uuid
    }
    return {
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        '__processed_timestamp': processed_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'entity_id': entity_id,
        'entity_type': 'recovery_point',
        'domain_id': domain_id,
        'account_id': account_id,
        'provider_id': provider_id,
        'is_deleted': False,
        'collection_timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'payload': payload
    }


# ---------------------------------------------------------------------------
# Day-1 RP generation functions (identical to mock_recovery_points.py,
# except generate_ndp_recovery_points_for_day also returns final rp_index)
# ---------------------------------------------------------------------------

def generate_rps_for_single_vm(
    vm: Dict, timestamps: List[datetime], account_id: str, provider_id: str,
    is_replicated: bool, cluster_b_uuid: Optional[str],
    cluster_b_pc_uuid: Optional[str], rp_start_index: int
) -> Tuple[List[Dict], List[Dict], int]:
    rp_entries = []
    vm_rp_entries = []
    rp_index = rp_start_index

    source_cluster_uuid = vm['cluster_uuid']
    source_pc_uuid = vm['source_pc_cluster_uuid']
    vm_id = vm['vmId']
    cluster_short_id = source_cluster_uuid

    for ts in timestamps:
        vm_rp_uuid = generate_uuid()
        rp_uuid = generate_uuid()
        location_agnostic_uuid = generate_uuid()
        backend_snapshot_uuid = generate_uuid()
        creation_time_usecs = str(int(ts.timestamp() * 1000000))
        creation_time = creation_time_usecs
        snapshot_usage = str(random.randint(100 * 1024 * 1024, 10 * 1024 * 1024 * 1024))
        name = f"singleVMRecoveryPoint{rp_index}_src_{cluster_short_id}"

        vm_rp_entries.append(create_vm_recovery_point_entry(
            entity_id=vm_rp_uuid, domain_id=source_pc_uuid,
            account_id=account_id, provider_id=provider_id, timestamp=ts,
            name=name, backend_snapshot_uuid=backend_snapshot_uuid,
            source_cluster_uuid=source_cluster_uuid,
            cluster_uuid=source_cluster_uuid, entity_uuid=vm_id,
            created_timestamp_usecs=creation_time_usecs
        ))
        rp_entries.append(create_recovery_point_entry(
            entity_id=rp_uuid, domain_id=source_pc_uuid,
            account_id=account_id, provider_id=provider_id, timestamp=ts,
            name=name, vm_recovery_point_uuid_list=[vm_rp_uuid],
            location_agnostic_uuid=location_agnostic_uuid,
            vm_recovery_point_total_exclusive_usage_bytes=[snapshot_usage],
            source_cluster_uuid=source_cluster_uuid,
            source_domain_manager_uuid=source_pc_uuid,
            vm_live_entity_uuid_list=[vm_id],
            creation_time=creation_time, rp_uuid=rp_uuid
        ))
        rp_index += 1

    if is_replicated and cluster_b_uuid and cluster_b_pc_uuid:
        cluster_b_short_id = cluster_b_uuid[:8]
        for ts in timestamps:
            replica_vm_rp_uuid = generate_uuid()
            replica_rp_uuid = generate_uuid()
            location_agnostic_uuid = generate_uuid()
            backend_snapshot_uuid = generate_uuid()
            creation_time_usecs = str(int(ts.timestamp() * 1000000))
            creation_time = creation_time_usecs
            snapshot_usage = str(random.randint(100 * 1024 * 1024, 10 * 1024 * 1024 * 1024))
            name = f"singleVMRecoveryPoint{rp_index}_src_{cluster_short_id}_replica_{cluster_b_short_id}"

            vm_rp_entries.append(create_vm_recovery_point_entry(
                entity_id=replica_vm_rp_uuid, domain_id=cluster_b_pc_uuid,
                account_id=account_id, provider_id=provider_id, timestamp=ts,
                name=name, backend_snapshot_uuid=backend_snapshot_uuid,
                source_cluster_uuid=source_cluster_uuid,
                cluster_uuid=cluster_b_uuid, entity_uuid=vm_id,
                created_timestamp_usecs=creation_time_usecs
            ))
            rp_entries.append(create_recovery_point_entry(
                entity_id=replica_rp_uuid, domain_id=cluster_b_pc_uuid,
                account_id=account_id, provider_id=provider_id, timestamp=ts,
                name=name, vm_recovery_point_uuid_list=[replica_vm_rp_uuid],
                location_agnostic_uuid=location_agnostic_uuid,
                vm_recovery_point_total_exclusive_usage_bytes=[snapshot_usage],
                source_cluster_uuid=source_cluster_uuid,
                source_domain_manager_uuid=source_pc_uuid,
                vm_live_entity_uuid_list=[vm_id],
                creation_time=creation_time, rp_uuid=replica_rp_uuid
            ))
            rp_index += 1

    return rp_entries, vm_rp_entries, rp_index


def generate_rps_for_consistency_group(
    cg_vms: List[Dict], timestamps: List[datetime], account_id: str,
    provider_id: str, is_replicated: bool, cluster_b_uuid: Optional[str],
    cluster_b_pc_uuid: Optional[str], rp_start_index: int
) -> Tuple[List[Dict], List[Dict], int]:
    rp_entries = []
    vm_rp_entries = []
    rp_index = rp_start_index

    if not cg_vms:
        return rp_entries, vm_rp_entries, rp_index

    ref_vm = cg_vms[0]
    source_cluster_uuid = ref_vm['cluster_uuid']
    source_pc_uuid = ref_vm['source_pc_cluster_uuid']
    cluster_short_id = source_cluster_uuid[:8]

    for ts in timestamps:
        rp_uuid = generate_uuid()
        location_agnostic_uuid = generate_uuid()
        creation_time_usecs = str(int(ts.timestamp() * 1000000))
        creation_time = creation_time_usecs
        name = f"multiVMCGRecoveryPoint{rp_index}_src_{cluster_short_id}"

        vm_rp_uuid_list = []
        vm_live_entity_uuid_list = []
        vm_rp_usage_bytes_list = []

        for vm in cg_vms:
            vm_rp_uuid = generate_uuid()
            backend_snapshot_uuid = generate_uuid()
            snapshot_usage = str(random.randint(100 * 1024 * 1024, 10 * 1024 * 1024 * 1024))
            vm_rp_uuid_list.append(vm_rp_uuid)
            vm_live_entity_uuid_list.append(vm['vmId'])
            vm_rp_usage_bytes_list.append(snapshot_usage)
            vm_rp_entries.append(create_vm_recovery_point_entry(
                entity_id=vm_rp_uuid, domain_id=source_pc_uuid,
                account_id=account_id, provider_id=provider_id, timestamp=ts,
                name=name, backend_snapshot_uuid=backend_snapshot_uuid,
                source_cluster_uuid=source_cluster_uuid,
                cluster_uuid=source_cluster_uuid, entity_uuid=vm['vmId'],
                created_timestamp_usecs=creation_time_usecs
            ))

        rp_entries.append(create_recovery_point_entry(
            entity_id=rp_uuid, domain_id=source_pc_uuid,
            account_id=account_id, provider_id=provider_id, timestamp=ts,
            name=name, vm_recovery_point_uuid_list=vm_rp_uuid_list,
            location_agnostic_uuid=location_agnostic_uuid,
            vm_recovery_point_total_exclusive_usage_bytes=vm_rp_usage_bytes_list,
            source_cluster_uuid=source_cluster_uuid,
            source_domain_manager_uuid=source_pc_uuid,
            vm_live_entity_uuid_list=vm_live_entity_uuid_list,
            creation_time=creation_time, rp_uuid=rp_uuid
        ))
        rp_index += 1

    if is_replicated and cluster_b_uuid and cluster_b_pc_uuid:
        cluster_b_short_id = cluster_b_uuid[:8]
        for ts in timestamps:
            replica_rp_uuid = generate_uuid()
            location_agnostic_uuid = generate_uuid()
            creation_time_usecs = str(int(ts.timestamp() * 1000000))
            creation_time = creation_time_usecs
            name = f"multiVMCGRecoveryPoint{rp_index}_src_{cluster_short_id}_replica_{cluster_b_short_id}"

            replica_vm_rp_uuid_list = []
            vm_live_entity_uuid_list = []
            vm_rp_usage_bytes_list = []

            for vm in cg_vms:
                replica_vm_rp_uuid = generate_uuid()
                backend_snapshot_uuid = generate_uuid()
                snapshot_usage = str(random.randint(100 * 1024 * 1024, 10 * 1024 * 1024 * 1024))
                replica_vm_rp_uuid_list.append(replica_vm_rp_uuid)
                vm_live_entity_uuid_list.append(vm['vmId'])
                vm_rp_usage_bytes_list.append(snapshot_usage)
                vm_rp_entries.append(create_vm_recovery_point_entry(
                    entity_id=replica_vm_rp_uuid, domain_id=cluster_b_pc_uuid,
                    account_id=account_id, provider_id=provider_id, timestamp=ts,
                    name=name, backend_snapshot_uuid=backend_snapshot_uuid,
                    source_cluster_uuid=source_cluster_uuid,
                    cluster_uuid=cluster_b_uuid, entity_uuid=vm['vmId'],
                    created_timestamp_usecs=creation_time_usecs
                ))

            rp_entries.append(create_recovery_point_entry(
                entity_id=replica_rp_uuid, domain_id=cluster_b_pc_uuid,
                account_id=account_id, provider_id=provider_id, timestamp=ts,
                name=name, vm_recovery_point_uuid_list=replica_vm_rp_uuid_list,
                location_agnostic_uuid=location_agnostic_uuid,
                vm_recovery_point_total_exclusive_usage_bytes=vm_rp_usage_bytes_list,
                source_cluster_uuid=source_cluster_uuid,
                source_domain_manager_uuid=source_pc_uuid,
                vm_live_entity_uuid_list=vm_live_entity_uuid_list,
                creation_time=creation_time, rp_uuid=replica_rp_uuid
            ))
            rp_index += 1

    return rp_entries, vm_rp_entries, rp_index


def generate_ndp_recovery_points_for_day(
    vms: List[Dict], clusters: List[Dict], current_date: datetime,
    cluster_a_uuid: Optional[str], cluster_b_uuid: Optional[str],
    cg_vm_ids_by_cluster: Dict[str, Set[str]], account_id: str,
    provider_id: str, verbose: bool = False
) -> Tuple[List[Dict], str, str, Dict[str, Set[str]], int]:
    """Returns (all_entries, cluster_a_uuid, cluster_b_uuid, cg_vm_ids_by_cluster, final_rp_index)."""
    all_entries = []
    cluster_uuids = {c['cluster_uuid'] for c in clusters}

    if cluster_a_uuid not in cluster_uuids or cluster_b_uuid not in cluster_uuids:
        if len(clusters) >= 2:
            cluster_a_uuid = clusters[0]['cluster_uuid']
            cluster_b_uuid = clusters[1]['cluster_uuid']
            if verbose:
                print(f"    Selected Cluster A: {cluster_a_uuid[:8]}... and B: {cluster_b_uuid[:8]}...")
        elif len(clusters) == 1:
            cluster_a_uuid = clusters[0]['cluster_uuid']
            cluster_b_uuid = None
            if verbose:
                print(f"    Only one cluster available, no replication")
        else:
            print(f"    No clusters available!")
            return all_entries, cluster_a_uuid, cluster_b_uuid, cg_vm_ids_by_cluster, 1

    cluster_b_pc_uuid = None
    for c in clusters:
        if c['cluster_uuid'] == cluster_b_uuid:
            cluster_b_pc_uuid = c['source_pc_cluster_uuid']
            break

    vms_by_cluster = defaultdict(list)
    for vm in vms:
        if vm.get('source_pc_cluster_uuid', '').strip():
            vms_by_cluster[vm['cluster_uuid']].append(vm)

    rp_index = 1

    for cluster in clusters:
        cluster_uuid = cluster['cluster_uuid']
        cluster_vms = vms_by_cluster.get(cluster_uuid, [])
        if not cluster_vms:
            continue

        is_replicated = (cluster_uuid == cluster_a_uuid and cluster_b_uuid is not None)
        rps_per_vm = REPLICATED_RPS_PER_VM if is_replicated else TARGET_RECOVERY_POINTS_PER_VM

        current_vm_ids = {vm['vmId'] for vm in cluster_vms}
        existing_cg_ids = cg_vm_ids_by_cluster.get(cluster_uuid, set())
        valid_existing_cg_ids = existing_cg_ids.intersection(current_vm_ids)
        cg_vm_count = min(CG_VMS_PER_CLUSTER, len(cluster_vms))
        needed_count = cg_vm_count - len(valid_existing_cg_ids)
        if needed_count > 0:
            non_cg_vms = [vm for vm in cluster_vms if vm['vmId'] not in valid_existing_cg_ids]
            random.shuffle(non_cg_vms)
            new_cg_ids = {vm['vmId'] for vm in non_cg_vms[:needed_count]}
            valid_existing_cg_ids = valid_existing_cg_ids.union(new_cg_ids)
        cg_vm_ids_by_cluster[cluster_uuid] = valid_existing_cg_ids

        cg_vms = [vm for vm in cluster_vms if vm['vmId'] in valid_existing_cg_ids]
        individual_vms = [vm for vm in cluster_vms if vm['vmId'] not in valid_existing_cg_ids]

        if verbose:
            cluster_type = "A (replicated)" if is_replicated else ("B (replica dest)" if cluster_uuid == cluster_b_uuid else "other")
            print(f"    Cluster {cluster_uuid[:8]}... ({cluster_type}):")
            print(f"      Total VMs: {len(cluster_vms)}, CG VMs: {len(cg_vms)}, Individual VMs: {len(individual_vms)}")
            print(f"      RPs per VM: {rps_per_vm} (x2 if replicated)")

        timestamps = generate_timestamps_for_day(current_date, rps_per_vm)

        if cg_vms:
            rp_entries, vm_rp_entries, rp_index = generate_rps_for_consistency_group(
                cg_vms, timestamps, account_id, provider_id,
                is_replicated, cluster_b_uuid, cluster_b_pc_uuid, rp_index
            )
            all_entries.extend(rp_entries)
            all_entries.extend(vm_rp_entries)
            for vm in cg_vms:
                rp_entries, vm_rp_entries, rp_index = generate_rps_for_single_vm(
                    vm, timestamps, account_id, provider_id,
                    is_replicated, cluster_b_uuid, cluster_b_pc_uuid, rp_index
                )
                all_entries.extend(rp_entries)
                all_entries.extend(vm_rp_entries)

        for vm in individual_vms:
            rp_entries, vm_rp_entries, rp_index = generate_rps_for_single_vm(
                vm, timestamps, account_id, provider_id,
                is_replicated, cluster_b_uuid, cluster_b_pc_uuid, rp_index
            )
            all_entries.extend(rp_entries)
            all_entries.extend(vm_rp_entries)

        source_pc_uuid = cluster['source_pc_cluster_uuid']
        vg_timestamps = generate_timestamps_for_day(current_date, VG_DISK_RPS_PER_CLUSTER)
        cluster_short_id = cluster_uuid[:8]
        for i, ts in enumerate(vg_timestamps):
            vg_rp_uuid = generate_uuid()
            location_agnostic_uuid = generate_uuid()
            creation_time_usecs = str(int(ts.timestamp() * 1000000))
            name = f"testVGDiskRecoveryPoint{rp_index}_src_{cluster_short_id}"
            all_entries.append(create_vg_disk_recovery_point_entry(
                entity_id=vg_rp_uuid, domain_id=source_pc_uuid,
                account_id=account_id, provider_id=provider_id, timestamp=ts,
                name=name, location_agnostic_uuid=location_agnostic_uuid,
                source_cluster_uuid=cluster_uuid,
                source_domain_manager_uuid=source_pc_uuid,
                creation_time=creation_time_usecs, rp_uuid=vg_rp_uuid
            ))
            rp_index += 1

    return all_entries, cluster_a_uuid, cluster_b_uuid, cg_vm_ids_by_cluster, rp_index


# ---------------------------------------------------------------------------
# Tracking groups — links each recovery_point to its child vm_recovery_points
# ---------------------------------------------------------------------------

def build_tracked_groups(entries: List[Dict], account_id: str, provider_id: str) -> List[Dict]:
    """
    Post-process day-1 entries to build tracking groups.
    Each group = one recovery_point entry + its associated vm_recovery_point entries.
    """
    vm_rp_by_id: Dict[str, Dict] = {}
    for entry in entries:
        if entry['entity_type'] == 'vm_recovery_point':
            vm_rp_by_id[entry['entity_id']] = entry

    tracked_groups: List[Dict] = []
    for entry in entries:
        if entry['entity_type'] != 'recovery_point':
            continue
        payload = entry['payload']
        vm_rp_uuids = payload.get('vm_recovery_point_uuid_list', [])
        vm_rp_entries = [vm_rp_by_id[uid] for uid in vm_rp_uuids if uid in vm_rp_by_id]

        tracked_groups.append({
            'rp_entry': entry,
            'vm_rp_entries': vm_rp_entries,
            'context': {
                'vm_ids': payload.get('vm_live_entity_uuid_list', []),
                'source_cluster_uuid': payload.get('source_cluster_uuid', ''),
                'source_domain_manager_uuid': payload.get('source_domain_manager_uuid', entry['domain_id']),
                'domain_id': entry['domain_id'],
                'account_id': account_id,
                'provider_id': provider_id,
                'is_vg_disk': len(vm_rp_uuids) == 0,
            }
        })

    return tracked_groups


# ---------------------------------------------------------------------------
# Day 2+ update generation
# ---------------------------------------------------------------------------

def _generate_size_update(group: Dict, timestamp: datetime) -> Tuple[List[Dict], Dict]:
    """
    Emit a new row for the recovery_point with updated sizes.
    creation_time is preserved. vm_recovery_point entries are not touched.
    Returns (entries_to_emit, updated_group).
    """
    updated_rp = copy.deepcopy(group['rp_entry'])
    processed_timestamp = timestamp + timedelta(minutes=random.randint(1, 30))

    updated_rp['timestamp'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    updated_rp['__processed_timestamp'] = processed_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    updated_rp['collection_timestamp'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    old_sizes = updated_rp['payload']['vm_recovery_point_total_exclusive_usage_bytes']
    updated_rp['payload']['vm_recovery_point_total_exclusive_usage_bytes'] = [
        max(1, int(s * random.uniform(0.8, 1.2))) for s in old_sizes
    ]
    # creation_time is NOT changed

    updated_group = copy.deepcopy(group)
    updated_group['rp_entry'] = updated_rp

    return [updated_rp], updated_group


def _generate_delete_entries(group: Dict, timestamp: datetime) -> List[Dict]:
    """Emit is_deleted=True rows for the recovery_point and all its vm_recovery_points."""
    entries: List[Dict] = []
    processed_timestamp = timestamp + timedelta(minutes=random.randint(1, 30))
    ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    pts_str = processed_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    deleted_rp = copy.deepcopy(group['rp_entry'])
    deleted_rp['timestamp'] = ts_str
    deleted_rp['__processed_timestamp'] = pts_str
    deleted_rp['collection_timestamp'] = ts_str
    deleted_rp['is_deleted'] = True
    entries.append(deleted_rp)

    for vm_rp in group['vm_rp_entries']:
        deleted_vm_rp = copy.deepcopy(vm_rp)
        deleted_vm_rp['timestamp'] = ts_str
        deleted_vm_rp['__processed_timestamp'] = pts_str
        deleted_vm_rp['collection_timestamp'] = ts_str
        deleted_vm_rp['is_deleted'] = True
        entries.append(deleted_vm_rp)

    return entries


def _create_replacement_group(
    old_group: Dict, timestamp: datetime, rp_index: int
) -> Tuple[Dict, List[Dict], int]:
    """
    Create a brand-new RP group to replace a deleted one.
    New UUIDs, new creation_time matching the current timestamp.
    Same VMs, same clusters, same domain.
    Returns (new_group, entries_to_emit, next_rp_index).
    """
    ctx = old_group['context']
    entries: List[Dict] = []

    source_cluster_uuid = ctx['source_cluster_uuid']
    domain_id = ctx['domain_id']
    account_id = ctx['account_id']
    provider_id = ctx['provider_id']
    source_domain_manager_uuid = ctx['source_domain_manager_uuid']

    old_name = old_group['rp_entry']['payload']['name']
    if 'multiVMCG' in old_name:
        name_prefix = 'multiVMCGRecoveryPoint'
    elif 'testVGDisk' in old_name:
        name_prefix = 'testVGDiskRecoveryPoint'
    else:
        name_prefix = 'singleVMRecoveryPoint'

    cluster_short_id = source_cluster_uuid[:8]
    is_replica = '_replica_' in old_name
    name = f"{name_prefix}{rp_index}_src_{cluster_short_id}"
    if is_replica:
        replica_suffix = old_name.split('_replica_')[-1]
        name += f"_replica_{replica_suffix}"

    creation_time_usecs = str(int(timestamp.timestamp() * 1000000))

    # --- VG / disk-only RP (no vm_recovery_points) ---
    if ctx['is_vg_disk']:
        rp_uuid = generate_uuid()
        location_agnostic_uuid = generate_uuid()
        rp_entry = create_vg_disk_recovery_point_entry(
            entity_id=rp_uuid, domain_id=domain_id,
            account_id=account_id, provider_id=provider_id,
            timestamp=timestamp, name=name,
            location_agnostic_uuid=location_agnostic_uuid,
            source_cluster_uuid=source_cluster_uuid,
            source_domain_manager_uuid=source_domain_manager_uuid,
            creation_time=creation_time_usecs, rp_uuid=rp_uuid
        )
        entries.append(rp_entry)
        new_group = {
            'rp_entry': rp_entry,
            'vm_rp_entries': [],
            'context': ctx.copy(),
        }
        return new_group, entries, rp_index + 1

    # --- Regular RP (single VM or CG) ---
    vm_ids = ctx['vm_ids']
    rp_uuid = generate_uuid()
    location_agnostic_uuid = generate_uuid()

    vm_rp_cluster_uuid = source_cluster_uuid
    if old_group['vm_rp_entries']:
        vm_rp_cluster_uuid = old_group['vm_rp_entries'][0]['payload']['cluster_uuid']

    vm_rp_entries: List[Dict] = []
    vm_rp_uuid_list: List[str] = []
    vm_rp_usage_bytes_list: List[str] = []

    for vm_id in vm_ids:
        vm_rp_uuid = generate_uuid()
        backend_snapshot_uuid = generate_uuid()
        snapshot_usage = str(random.randint(100 * 1024 * 1024, 10 * 1024 * 1024 * 1024))
        vm_rp_uuid_list.append(vm_rp_uuid)
        vm_rp_usage_bytes_list.append(snapshot_usage)

        vm_rp_entry = create_vm_recovery_point_entry(
            entity_id=vm_rp_uuid, domain_id=domain_id,
            account_id=account_id, provider_id=provider_id,
            timestamp=timestamp, name=name,
            backend_snapshot_uuid=backend_snapshot_uuid,
            source_cluster_uuid=source_cluster_uuid,
            cluster_uuid=vm_rp_cluster_uuid, entity_uuid=vm_id,
            created_timestamp_usecs=creation_time_usecs
        )
        vm_rp_entries.append(vm_rp_entry)
        entries.append(vm_rp_entry)

    rp_entry = create_recovery_point_entry(
        entity_id=rp_uuid, domain_id=domain_id,
        account_id=account_id, provider_id=provider_id,
        timestamp=timestamp, name=name,
        vm_recovery_point_uuid_list=vm_rp_uuid_list,
        location_agnostic_uuid=location_agnostic_uuid,
        vm_recovery_point_total_exclusive_usage_bytes=vm_rp_usage_bytes_list,
        source_cluster_uuid=source_cluster_uuid,
        source_domain_manager_uuid=source_domain_manager_uuid,
        vm_live_entity_uuid_list=vm_ids,
        creation_time=creation_time_usecs, rp_uuid=rp_uuid
    )
    entries.append(rp_entry)

    new_group = {
        'rp_entry': rp_entry,
        'vm_rp_entries': vm_rp_entries,
        'context': ctx.copy(),
    }
    return new_group, entries, rp_index + 1


def generate_updates_for_day(
    tracked_groups: List[Dict],
    frozen_group_ids: Set[str],
    current_date: datetime,
    rp_index_start: int,
    size_update_frac: float,
    delete_frac: float,
    verbose: bool = False
) -> Tuple[List[Dict], List[Dict], int]:
    """
    Generate update entries for all tracked groups on a subsequent day.
    Groups whose rp entity_id is in frozen_group_ids are kept as-is (no updates ever).
    Returns (day_entries, updated_tracked_groups, next_rp_index).
    """
    entries: List[Dict] = []
    new_tracked_groups: List[Dict] = []
    rp_index = rp_index_start

    size_update_count = 0
    delete_count = 0
    frozen_count = 0

    # Normalise so the two fractions always sum to 1.0
    total = size_update_frac + delete_frac
    size_threshold = size_update_frac / total if total > 0 else 0.5

    for group in tracked_groups:
        rp_id = group['rp_entry']['entity_id']

        if rp_id in frozen_group_ids:
            new_tracked_groups.append(group)
            frozen_count += 1
            continue

        ts = current_date + timedelta(seconds=random.randint(0, 86399))
        is_vg_disk = group['context']['is_vg_disk']

        # VG/disk RPs have no size field, so they always get delete+create
        if is_vg_disk or random.random() >= size_threshold:
            delete_entries = _generate_delete_entries(group, ts)
            entries.extend(delete_entries)
            new_group, create_entries, rp_index = _create_replacement_group(group, ts, rp_index)
            entries.extend(create_entries)
            new_tracked_groups.append(new_group)
            delete_count += 1
        else:
            update_entries, updated_group = _generate_size_update(group, ts)
            entries.extend(update_entries)
            new_tracked_groups.append(updated_group)
            size_update_count += 1

    if verbose:
        print(f"    Updates: {size_update_count} size, {delete_count} delete+create, {frozen_count} frozen")

    return entries, new_tracked_groups, rp_index


# ---------------------------------------------------------------------------
# Output writing (identical to mock_recovery_points.py)
# ---------------------------------------------------------------------------

def write_output_json(entries: List[Dict], output_path: str):
    if not output_path.endswith('.gz'):
        output_path = output_path + '.gz'
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, separators=(',', ':')) + '\n')
    print(f"  Written {len(entries)} entries to {output_path}")
    return output_path


def write_output_csv(entries: List[Dict], output_path: str):
    if not entries:
        print(f"  No entries to write to {output_path}")
        return output_path
    if not output_path.endswith('.gz'):
        output_path = output_path + '.gz'
    fieldnames = [
        'timestamp', '__processed_timestamp', 'entity_id', 'entity_type',
        'domain_id', 'account_id', 'provider_id', 'is_deleted',
        'collection_timestamp', 'payload'
    ]
    with gzip.open(output_path, 'wt', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            row = {k: entry.get(k, '') for k in fieldnames}
            if 'is_deleted' in row:
                row['is_deleted'] = 'true' if row['is_deleted'] else 'false'
            writer.writerow(row)
    print(f"  Written {len(entries)} entries to {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Starting NDP Recovery Point Mock Data Generator (with updates)...")
    parser = argparse.ArgumentParser(
        description='Generate mock NDP recovery point data with daily updates'
    )
    parser.add_argument('--start-date', type=str, required=True,
                        help='Start date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, default=DAYS_OF_DATA,
                        help=f'Number of days to generate (default: {DAYS_OF_DATA})')
    parser.add_argument('--format', type=str, choices=['json', 'csv'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file base name')
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=8123)
    parser.add_argument('--username', type=str, default='nutanix')
    parser.add_argument('--password', type=str, default='nutanix')
    parser.add_argument('--database', type=str, default='ncm')
    parser.add_argument('--skip-db-connection', action='store_true',
                        help='Skip database connection and generate sample data')
    parser.add_argument('--num-sample-vms', type=int, default=40,
                        help='Number of sample VMs (with --skip-db-connection)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    parser.add_argument('--size-update-fraction', type=float, default=SIZE_UPDATE_FRACTION,
                        help=f'Fraction of RPs that get size updates per day (default: {SIZE_UPDATE_FRACTION})')
    parser.add_argument('--delete-fraction', type=float, default=DELETE_FRACTION,
                        help=f'Fraction of RPs that get deleted per day (default: {DELETE_FRACTION})')
    parser.add_argument('--untouched-fraction', type=float, default=UNTOUCHED_FRACTION,
                        help=f'Fraction of day-1 RPs that are never updated (default: {UNTOUCHED_FRACTION})')
    parser.add_argument('--chunks-per-day', type=int, default=CHUNKS_PER_DAY,
                        help=f'Split each day\'s output into N chunk files (default: {CHUNKS_PER_DAY})')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print detailed output')

    args = parser.parse_args()
    days_of_data = args.days

    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")

    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    except ValueError:
        print(f"Error: Invalid date format '{args.start_date}'. Use YYYY-MM-DD format.")
        sys.exit(1)

    account_id = generate_uuid()
    provider_id = generate_uuid()

    extension = args.format
    if args.output is None:
        args.output = f'ndp_recovery_point_updates_mock_data.{extension}.gz'

    if args.verbose:
        print(f"=== Configuration ===")
        print(f"Start date: {args.start_date}")
        print(f"Days of data: {days_of_data}")
        print(f"Size-update fraction (day 2+): {args.size_update_fraction}")
        print(f"Delete fraction (day 2+): {args.delete_fraction}")
        print(f"Untouched fraction: {args.untouched_fraction}")
        print(f"Chunks per day: {args.chunks_per_day}")
        print(f"Target RPs per VM per day: {TARGET_RECOVERY_POINTS_PER_VM}")
        print(f"CG VMs per cluster: {CG_VMS_PER_CLUSTER}")
        print(f"VG/Disk RPs per cluster: {VG_DISK_RPS_PER_CLUSTER}")
        print()

    # --- Set up data source ---
    client = None
    sample_vms = None
    sample_clusters = None

    if not args.skip_db_connection:
        if get_client is None:
            print("Error: clickhouse-connect not installed. Use --skip-db-connection or install it.")
            sys.exit(1)
        if args.verbose:
            print(f"Connecting to ClickHouse at {args.host}:{args.port}...")
        try:
            client = get_client(
                host=args.host, port=args.port,
                username=args.username, password=args.password,
                database=args.database
            )
            if args.verbose:
                print("Connected successfully!")
        except Exception as e:
            print(f"Error connecting to ClickHouse: {e}")
            print("Use --skip-db-connection to generate sample data")
            sys.exit(1)
    else:
        if args.verbose:
            print("Generating sample data (stable across all days)...")
        sample_vms, sample_clusters = generate_sample_data_once(num_vms=args.num_sample_vms)
        if args.verbose:
            print(f"  Generated {len(sample_vms)} sample VMs, {len(sample_clusters)} clusters")

    # --- Output bookkeeping ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Output folder: {OUTPUT_FOLDER}/")

    base_output = args.output
    if base_output.endswith('.gz'):
        base_output = base_output[:-3]
    if base_output.endswith('.json') or base_output.endswith('.csv'):
        base_output = base_output.rsplit('.', 1)[0]
    base_output = os.path.basename(base_output)

    total_entries = 0
    total_rp_count = 0
    total_vm_rp_count = 0
    file_count = 0
    output_files: List[str] = []

    cluster_a_uuid: Optional[str] = None
    cluster_b_uuid: Optional[str] = None
    cg_vm_ids_by_cluster: Dict[str, Set[str]] = {}
    tracked_groups: List[Dict] = []
    frozen_group_ids: Set[str] = set()
    rp_index = 1

    for day_offset in range(days_of_data):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')

        if day_offset == 0:
            # ====== DAY 1: full creation ======
            if args.skip_db_connection:
                vms, clusters = sample_vms, sample_clusters
            else:
                if args.verbose:
                    print(f"  Fetching clusters...")
                clusters = fetch_clusters_for_date(client, date_str)
                if not clusters:
                    print(f"  Warning: No clusters found for {date_str}, skipping day")
                    continue
                if args.verbose:
                    print(f"  Fetching VMs...")
                vms = fetch_vm_data_for_date(client, date_str)
                if not vms:
                    print(f"  Warning: No VMs found for {date_str}, skipping day")
                    continue
                valid_cluster_ids = {c['cluster_uuid'] for c in clusters}
                vms = [vm for vm in vms if vm['cluster_uuid'] in valid_cluster_ids]

            day_entries, cluster_a_uuid, cluster_b_uuid, cg_vm_ids_by_cluster, rp_index = \
                generate_ndp_recovery_points_for_day(
                    vms, clusters, current_date, cluster_a_uuid, cluster_b_uuid,
                    cg_vm_ids_by_cluster, account_id, provider_id, args.verbose
                )

            tracked_groups = build_tracked_groups(day_entries, account_id, provider_id)

            # Freeze a fraction of day-1 groups so they are never updated
            frozen_count = int(len(tracked_groups) * args.untouched_fraction)
            frozen_sample = random.sample(tracked_groups, frozen_count)
            frozen_group_ids = {g['rp_entry']['entity_id'] for g in frozen_sample}
            print(f"  Tracking {len(tracked_groups)} RP groups ({frozen_count} frozen, "
                  f"{len(tracked_groups) - frozen_count} mutable)")
        else:
            # ====== DAY 2+: incremental updates ======
            day_entries, tracked_groups, rp_index = generate_updates_for_day(
                tracked_groups, frozen_group_ids, current_date, rp_index,
                args.size_update_fraction, args.delete_fraction, args.verbose
            )

        day_rp_count = sum(1 for e in day_entries if e['entity_type'] == 'recovery_point')
        day_vm_rp_count = sum(1 for e in day_entries if e['entity_type'] == 'vm_recovery_point')
        day_rp_deleted = sum(1 for e in day_entries if e['entity_type'] == 'recovery_point' and e.get('is_deleted'))
        day_vm_rp_deleted = sum(1 for e in day_entries if e['entity_type'] == 'vm_recovery_point' and e.get('is_deleted'))
        mode = "CREATION" if day_offset == 0 else "UPDATES"
        print(f"Day {day_offset + 1}/{days_of_data} ({date_str}) [{mode}]: "
              f"{day_rp_count} recovery_point ({day_rp_deleted} deleted), "
              f"{day_vm_rp_count} vm_recovery_point ({day_vm_rp_deleted} deleted)")

        # Write day entries split into chunks
        chunks = args.chunks_per_day
        chunk_size = (len(day_entries) + chunks - 1) // chunks if chunks > 1 else len(day_entries)

        for chunk_idx in range(chunks):
            chunk_start = chunk_idx * chunk_size
            chunk_end = min(chunk_start + chunk_size, len(day_entries))
            chunk_entries = day_entries[chunk_start:chunk_end]
            if not chunk_entries:
                break

            if chunks == 1:
                output_filename = os.path.join(
                    OUTPUT_FOLDER,
                    f"{base_output}_day_{day_offset + 1:03d}_{date_str}.{args.format}.gz"
                )
            else:
                output_filename = os.path.join(
                    OUTPUT_FOLDER,
                    f"{base_output}_day_{day_offset + 1:03d}_{date_str}_chunk_{chunk_idx + 1:03d}.{args.format}.gz"
                )

            if args.format == 'json':
                write_output_json(chunk_entries, output_filename)
            else:
                write_output_csv(chunk_entries, output_filename)

            output_files.append(os.path.basename(output_filename))
            file_count += 1

        total_entries += len(day_entries)
        total_rp_count += day_rp_count
        total_vm_rp_count += day_vm_rp_count

    print(f"\n=== Summary ===")
    print(f"Files created: {file_count}")
    print(f"Total entries: {total_entries} ({total_rp_count} recovery_point, {total_vm_rp_count} vm_recovery_point)")
    if args.verbose:
        print(f"\nOutput files:")
        for f in output_files:
            print(f"  {f}")
    print(f"Done!")


if __name__ == '__main__':
    main()
