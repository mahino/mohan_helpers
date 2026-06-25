#!/usr/bin/env python3
"""Paginate Prism Groups API and count repeated titles for audit + event."""

from __future__ import annotations

import json
import math
import os
import queue
import re
import sys
import threading
import time
from collections import Counter
from typing import Any

import requests
import urllib3

from pc_cookie_auth import PrismCookieClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Hardcoded config (as requested)
BASE_URL = "https://ncm.services.nconprem-10-114-55-128.ccpnx.com/"
GROUPS_API = BASE_URL + "api/nutanix/v3/groups"
USERNAME = "admin"
PASSWORD = "Nutanix.123"
GROUP_MEMBER_COUNT = 500
REQUEST_TIMEOUT_SEC = 120
VERIFY_SSL = False
AUDIT_OUTPUT_FILE = "audit_title_counts.json"
EVENT_OUTPUT_FILE = "event_title_counts.json"
MAX_RETRIES_PER_PAGE = 5
RETRY_BACKOFF_SEC = 3
PAUSE_EVERY_PAGES = 20
PAUSE_SECONDS = 5
# Default behavior: normalize dynamic parts (UUID/time) so duplicate patterns collapse.
ENABLE_TITLE_NORMALIZATION = True
# Group counts by cluster_name (cluster -> title -> count).
GROUP_BY_CLUSTER_NAME = True
# Optional behavior: count only records from the last N hours as of script start.
LAST_N_HOURS_ONLY_ENABLED = False
LAST_N_HOURS = 8
# Adaptive skip while scanning ASCENDING data and still far older than cutoff.
ENABLE_DYNAMIC_OFFSET_SKIP = True
MAX_DYNAMIC_SKIP_PAGES = 500
# Conservative controls to avoid cutoff overshoot.
DYNAMIC_SKIP_SAFETY_DIVISOR = 2
DYNAMIC_SKIP_NEAR_CUTOFF_HOURS = 6
DYNAMIC_SKIP_NEAR_CUTOFF_MAX_PAGES = 3
DYNAMIC_SKIP_MID_CUTOFF_HOURS = 24
DYNAMIC_SKIP_MID_CUTOFF_MAX_PAGES = 10
# Optional aggressive optimization: seek directly near cutoff page first.
ENABLE_CUTOFF_PAGE_SEEK = True
# Resume support: set page offset per entity type (must be multiple of GROUP_MEMBER_COUNT).
RESUME_OFFSET_BY_ENTITY = {
    "audit": 0,
    "event": 0,
}
# If resuming and output file exists, preload old counts.
RESUME_FROM_EXISTING_OUTPUT = True
COOKIE_REFRESH_SEC = 300

client = requests.Session()
client.headers = {"content-type": "application/json"}
client.verify = VERIFY_SSL
cookie_client = PrismCookieClient(
    session=client,
    base_url=BASE_URL,
    username=USERNAME,
    password=PASSWORD,
    verify_ssl=VERIFY_SSL,
    timeout_sec=REQUEST_TIMEOUT_SEC,
    refresh_sec=COOKIE_REFRESH_SEC,
)

UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
# Example: 260521-091533 (ddmmyy-hhmmss style)
TS_COMPACT_RE = re.compile(r"\b\d{6}-\d{6}\b")
# Example: 2026-06-16T09:15:30Z or 2026-06-16 09:15:30
TS_ISO_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}Z?\b")
IP_PORT_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}:\d+\b")
VM_NAME_CONTEXT_RE = re.compile(r"(\bfor the VM\s+)(\S+)", re.IGNORECASE)
ENTITY_PREFIX_ANOMALY_RE = re.compile(r"^([^:]+)\s+:\s+(.+\sanomaly)$", re.IGNORECASE)
INTERNAL_ID_RE = re.compile(r"(\binternal ID\s+)(\S+)", re.IGNORECASE)
USER_RE = re.compile(r"(\buser\s+)([A-Za-z0-9_.@-]+)", re.IGNORECASE)
CLUSTER_RE = re.compile(r"(\bcluster\s+)([A-Za-z0-9_.:-]+)", re.IGNORECASE)
POOL_RE = re.compile(r"\bdefault-storage-pool-\d+\b", re.IGNORECASE)
CONTAINER_RE = re.compile(r"(\bStorage Container\s+)([A-Za-z0-9_.:-]+)", re.IGNORECASE)
PUBLIC_KEY_RE = re.compile(r"(\bPublic Key\s+)([A-Za-z0-9_.:-]+)(\s+added to Cluster\b)", re.IGNORECASE)
SOFTWARE_VER_RE = re.compile(r"(\bSoftware\s+)([A-Za-z0-9_.-]+)(\s+prism_central_deploy upload started\b)", re.IGNORECASE)
CREATED_IMAGE_RE = re.compile(r"^Created Image\s+.+$", re.IGNORECASE)
DELETED_IMAGE_RE = re.compile(r"^Deleted Image\s+.+$", re.IGNORECASE)
UPDATED_MARKETPLACE_ITEM_RE = re.compile(r"^Updated categories for marketplace_item\s+.+$", re.IGNORECASE)
ALERT_SCHEMA_CREATED_RE = re.compile(r"^Alert Schema\s+.+\s+Created by\s+.+$", re.IGNORECASE)
ALERT_SCHEMA_DELETED_RE = re.compile(r"^Alert Schema\s+.+\s+Deleted by\s+.+$", re.IGNORECASE)
CATEGORY_VALUE_CREATED_RE = re.compile(r"^Category\s+([A-Za-z0-9_.-]+):([A-Za-z0-9_.$-]+)\s+has been created$", re.IGNORECASE)
CATEGORY_KEY_CREATED_RE = re.compile(r"^Category key\s+.+\s+has been created$", re.IGNORECASE)
CATEGORY_KEY_VALUE_EXTID_CREATED_RE = re.compile(
    r"^Category\s+[^/\s]+/[^\s]+\s+with extId\s+\{uuid\}\s+has been Created$",
    re.IGNORECASE,
)
CATEGORY_CALMAPP_CREATED_RE = re.compile(
    r"^Category\s+CalmApplication/.+\s+with extId\s+\{uuid\}\s+has been Created$",
    re.IGNORECASE,
)
CATEGORY_CALMPROJECT_CREATED_RE = re.compile(
    r"^Category\s+CalmProject/.+\s+with extId\s+\{uuid\}\s+has been Created$",
    re.IGNORECASE,
)
UPDATED_VM_RP_RE = re.compile(r"^Updated categories for vm_recovery_point\s+.+$", re.IGNORECASE)
ADDED_NIC_TO_VM_RE = re.compile(r"^Added NIC\s+.+\s+to VM\s+.+\}?\s*$", re.IGNORECASE)
ADDED_DISK_TO_VM_RE = re.compile(r"^Added disk\s+.+\s+to VM\s+.+$", re.IGNORECASE)
CREATED_DASHBOARD_RE = re.compile(
    r"^User\s+\{username\}\s+has created a new dashboard\s+.+$",
    re.IGNORECASE,
)
UPDATED_DASHBOARD_RE = re.compile(
    r"^User\s+\{username\}\s+has updated the dashboard\s+.+$",
    re.IGNORECASE,
)


def _iso_utc(ts: float | None = None) -> str:
    if ts is None:
        ts = time.time()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _write_counts_file(output_file: str, counts: dict[str, Any]) -> None:
    output_text = json.dumps(counts, indent=2, ensure_ascii=False)
    tmp_path = f"{output_file}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(output_text + "\n")
    # Atomic replace to avoid partially-written files.
    os.replace(tmp_path, output_file)


def _writer_thread_loop(entity_type: str, output_file: str, q: "queue.Queue[dict[str, Any] | None]") -> None:
    while True:
        item = q.get()
        if item is None:
            q.task_done()
            break
        try:
            _write_counts_file(output_file, item)
        except Exception as exc:
            print(f"[WARN][{entity_type}] writer thread failed: {exc}", file=sys.stderr)
        finally:
            q.task_done()


AUDIT_ATTRIBUTES = [
    {"attribute": "title"},
    {"attribute": "user_name"},
    {"attribute": "target_entity_name"},
    {"attribute": "target_entity_type"},
    {"attribute": "operation_type"},
    {"attribute": "op_start_timestamp_usecs"},
    {"attribute": "provider_id"},
    {"attribute": "source_entity_account_uuid"},
    {"attribute": "cluster_name"},
    {"attribute": "param_name_list"},
    {"attribute": "param_value_list"},
    {"attribute": "target_entity_uuid"},
    {"attribute": "default_message"},
    {"attribute": "component"},
    {"attribute": "user"},
    {"attribute": "client_ip"},
    {"attribute": "status"},
    {"attribute": "type_id"},
    {"attribute": "entity_name_list"},
    {"attribute": "entity_type_list"},
    {"attribute": "entity_uuid_list"},
    {"attribute": "cluster"},
]


EVENT_ATTRIBUTES = [
    {"attribute": "title"},
    {"attribute": "source_entity_name"},
    {"attribute": "provider_id"},
    {"attribute": "source_entity_account_uuid"},
    {"attribute": "classification"},
    {"attribute": "cluster_name"},
    {"attribute": "_created_timestamp_usecs_"},
    {"attribute": "default_message"},
    {"attribute": "param_name_list"},
    {"attribute": "param_value_list"},
    {"attribute": "source_entity_uuid"},
    {"attribute": "source_entity_type"},
    {"attribute": "cluster"},
]


def build_payload(
    entity_type: str,
    attributes: list[dict[str, str]],
    group_member_count: int,
    group_member_offset: int,
    sort_attr: str,
    sort_order: str,
) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "group_member_attributes": attributes,
        "group_member_count": group_member_count,
        "group_member_offset": group_member_offset,
        "group_member_sort_attribute": sort_attr,
        "group_member_sort_order": sort_order,
    }


def extract_title(entity_result: dict[str, Any]) -> str | None:
    data = entity_result.get("data") or []
    if not isinstance(data, list):
        return None

    title_value = None
    default_value = None

    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        values_rows = item.get("values") or []
        if not isinstance(values_rows, list) or not values_rows:
            continue
        first_row = values_rows[0] if isinstance(values_rows[0], dict) else {}
        values = first_row.get("values") or []
        if not isinstance(values, list) or not values:
            continue
        value = str(values[0]).strip()
        if not value:
            continue
        if name == "title":
            title_value = value
        elif name == "default_message":
            default_value = value

    return title_value or default_value


def extract_attribute_value(entity_result: dict[str, Any], attr_name: str) -> str | None:
    data = entity_result.get("data") or []
    if not isinstance(data, list):
        return None

    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("name") != attr_name:
            continue
        values_rows = item.get("values") or []
        if not isinstance(values_rows, list) or not values_rows:
            continue
        first_row = values_rows[0] if isinstance(values_rows[0], dict) else {}
        values = first_row.get("values") or []
        if not isinstance(values, list) or not values:
            continue
        value = str(values[0]).strip()
        if value:
            return value
    return None


def extract_timestamp_usecs(entity_result: dict[str, Any], timestamp_attr: str) -> int | None:
    raw = extract_attribute_value(entity_result, timestamp_attr)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def normalize_title(title: str) -> str:
    text = str(title or "").strip()
    if not text:
        return text
    if not ENABLE_TITLE_NORMALIZATION:
        return text
    text = UUID_RE.sub("{uuid}", text)
    text = TS_COMPACT_RE.sub("{time_stamp}", text)
    text = TS_ISO_RE.sub("{time_stamp}", text)
    text = IP_PORT_RE.sub("{ip_port}", text)
    text = VM_NAME_CONTEXT_RE.sub(r"\1{vm_name}", text)
    text = INTERNAL_ID_RE.sub(r"\1{uuid}", text)
    text = USER_RE.sub(r"\1{username}", text)
    text = CLUSTER_RE.sub(r"\1{cluster_name}", text)
    text = POOL_RE.sub("{storage_pool}", text)
    text = CONTAINER_RE.sub(r"\1{container_name}", text)
    text = PUBLIC_KEY_RE.sub(r"\1{public_key_name}\3", text)
    text = SOFTWARE_VER_RE.sub(r"\1{software_version}\3", text)
    text = CREATED_IMAGE_RE.sub("Created Image {image_name}", text)
    text = DELETED_IMAGE_RE.sub("Deleted Image {image_name}", text)
    text = UPDATED_MARKETPLACE_ITEM_RE.sub(
        "Updated categories for marketplace_item {marketplace_item}",
        text,
    )
    text = ALERT_SCHEMA_CREATED_RE.sub(
        "Alert Schema {alert_schema} Created by {service_name}",
        text,
    )
    text = ALERT_SCHEMA_DELETED_RE.sub(
        "Alert Schema {alert_schema} Deleted by {service_name}",
        text,
    )
    text = CATEGORY_VALUE_CREATED_RE.sub(
        r"Category \1:{category_value} has been created",
        text,
    )
    text = CATEGORY_KEY_CREATED_RE.sub(
        "Category key {key} has been created",
        text,
    )
    text = CATEGORY_KEY_VALUE_EXTID_CREATED_RE.sub(
        "Category {key}/{value} with extId {uuid} has been Created",
        text,
    )
    text = CATEGORY_CALMAPP_CREATED_RE.sub(
        "Category CalmApplication/{app_name} with extId {uuid} has been Created",
        text,
    )
    text = CATEGORY_CALMPROJECT_CREATED_RE.sub(
        "Category CalmProject/{project_name} with extId {uuid} has been Created",
        text,
    )
    text = UPDATED_VM_RP_RE.sub(
        "Updated categories for vm_recovery_point {bulk_operation}",
        text,
    )
    text = ADDED_NIC_TO_VM_RE.sub(
        "Added NIC {suitalbe_name} to VM {vm_name}",
        text,
    )
    text = ADDED_DISK_TO_VM_RE.sub(
        "Added disk {disc_name} to VM {vm_name}",
        text,
    )
    text = CREATED_DASHBOARD_RE.sub(
        "User {username} has created a new dashboard {dashboard_name}",
        text,
    )
    text = UPDATED_DASHBOARD_RE.sub(
        "User {username} has updated the dashboard {dashboard_name}",
        text,
    )

    # Generic anomaly shape: "<entity> : <metric> anomaly" -> "{entity_name} : <metric> anomaly"
    m = ENTITY_PREFIX_ANOMALY_RE.match(text)
    if m:
        text = "{entity_name} : " + m.group(2)

    # Catch vm-123-... style names anywhere else.
    text = re.sub(r"\bvm-\d+(?:-[^\s:]+)?\b", "{vm_name}", text, flags=re.IGNORECASE)
    text = re.sub(r"\bahv_[^\s:]+(?:-\d+)?(?:-{time_stamp})?\b", "{vm_name}", text, flags=re.IGNORECASE)
    return text


def fetch_page(
    entity_type: str,
    attributes: list[dict[str, str]],
    group_member_count: int,
    group_member_offset: int,
    sort_attr: str,
    sort_order: str,
    timeout: int,
) -> dict[str, Any]:
    payload = build_payload(
        entity_type=entity_type,
        attributes=attributes,
        group_member_count=group_member_count,
        group_member_offset=group_member_offset,
        sort_attr=sort_attr,
        sort_order=sort_order,
    )
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES_PER_PAGE + 1):
        try:
            resp = cookie_client.request(
                "POST",
                GROUPS_API,
                data=json.dumps(payload),
                timeout=timeout,
            )
            # Retry for throttling or transient server errors.
            if resp.status_code == 429 or resp.status_code >= 500:
                raise requests.HTTPError(
                    f"HTTP {resp.status_code} for offset={group_member_offset}",
                    response=resp,
                )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt >= MAX_RETRIES_PER_PAGE:
                break
            sleep_s = RETRY_BACKOFF_SEC * attempt
            print(
                f"[WARN][{entity_type}] page fetch failed at offset={group_member_offset}, "
                f"attempt={attempt}/{MAX_RETRIES_PER_PAGE}, retrying in {sleep_s}s: {exc}",
                file=sys.stderr,
            )
            time.sleep(sleep_s)
    raise RuntimeError(
        f"[{entity_type}] failed to fetch page at offset={group_member_offset} "
        f"after {MAX_RETRIES_PER_PAGE} attempts"
    ) from last_error


def run_title_count_job(
    *,
    entity_type: str,
    attributes: list[dict[str, str]],
    sort_attr: str,
    sort_order: str,
    output_file: str,
) -> int:
    run_start_ts = time.time()
    run_start_iso = _iso_utc(run_start_ts)

    start_offset = int(RESUME_OFFSET_BY_ENTITY.get(entity_type, 0) or 0)
    if start_offset < 0:
        start_offset = 0
    if start_offset % GROUP_MEMBER_COUNT != 0:
        aligned = (start_offset // GROUP_MEMBER_COUNT) * GROUP_MEMBER_COUNT
        print(
            f"[WARN][{entity_type}] resume offset {start_offset} is not aligned; using {aligned}",
            file=sys.stderr,
        )
        start_offset = aligned

    counter: Counter[str] = Counter()
    cluster_counters: dict[str, Counter[str]] = {}
    window_start_usecs: int | None = None
    if LAST_N_HOURS_ONLY_ENABLED:
        window_start_usecs = int(time.time() * 1_000_000) - int(LAST_N_HOURS * 3_600 * 1_000_000)
        print(
            f"[INFO][{entity_type}] last-{LAST_N_HOURS}h-only enabled, cutoff_usecs={window_start_usecs}",
            file=sys.stderr,
        )

    if start_offset > 0 and RESUME_FROM_EXISTING_OUTPUT and output_file and os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                prev = json.load(f)
            if isinstance(prev, dict):
                prev_counts_obj: Any = prev.get("counts") if "counts" in prev else prev
                if GROUP_BY_CLUSTER_NAME:
                    if not isinstance(prev_counts_obj, dict):
                        prev_counts_obj = {}
                    for cluster_name, title_map in prev_counts_obj.items():
                        if not isinstance(title_map, dict):
                            continue
                        ckey = str(cluster_name or "unknown_cluster")
                        cctr = cluster_counters.setdefault(ckey, Counter())
                        for title_key, count_val in title_map.items():
                            try:
                                inc = int(count_val)
                            except (TypeError, ValueError):
                                continue
                            tkey = str(title_key)
                            cctr[tkey] += inc
                            counter[tkey] += inc
                    print(
                        f"[INFO][{entity_type}] preloaded {len(cluster_counters)} clusters from {output_file}",
                        file=sys.stderr,
                    )
                else:
                    if not isinstance(prev_counts_obj, dict):
                        prev_counts_obj = {}
                    safe_prev: dict[str, int] = {}
                    for k, v in prev_counts_obj.items():
                        try:
                            safe_prev[str(k)] = int(v)
                        except (TypeError, ValueError):
                            continue
                    counter.update(safe_prev)
                    print(
                        f"[INFO][{entity_type}] preloaded {len(safe_prev)} patterns from {output_file}",
                        file=sys.stderr,
                    )
        except Exception as exc:
            print(f"[WARN][{entity_type}] failed to preload {output_file}: {exc}", file=sys.stderr)

    writer_q: "queue.Queue[dict[str, Any] | None]" = queue.Queue()
    writer_t = threading.Thread(
        target=_writer_thread_loop,
        args=(entity_type, output_file, writer_q),
        daemon=True,
        name=f"title-writer-{entity_type}",
    )
    writer_t.start()

    # First page for this run starts at configured resume offset.
    first = fetch_page(
        entity_type=entity_type,
        attributes=attributes,
        group_member_count=GROUP_MEMBER_COUNT,
        group_member_offset=start_offset,
        sort_attr=sort_attr,
        sort_order=sort_order,
        timeout=REQUEST_TIMEOUT_SEC,
    )
    filtered_entity_count = int(first.get("filtered_entity_count") or 0)
    total_pages = max(1, math.ceil(filtered_entity_count / GROUP_MEMBER_COUNT))
    start_page_idx = (start_offset // GROUP_MEMBER_COUNT) + 1
    print(
        f"[INFO][{entity_type}] filtered_entity_count={filtered_entity_count}, page_size={GROUP_MEMBER_COUNT}, "
        f"pages={total_pages}, resume_offset={start_offset}",
        file=sys.stderr,
    )

    def extract_response_timestamps(obj: dict[str, Any]) -> list[int]:
        timestamps: list[int] = []
        groups = obj.get("group_results") or []
        if not isinstance(groups, list):
            return timestamps
        for group in groups:
            if not isinstance(group, dict):
                continue
            entities = group.get("entity_results") or []
            if not isinstance(entities, list):
                continue
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                ts = extract_timestamp_usecs(entity, sort_attr)
                if ts is not None:
                    timestamps.append(ts)
        return timestamps

    def process_response(obj: dict[str, Any]) -> tuple[int, int, list[int]]:
        kept = 0
        skipped_old = 0
        timestamps = extract_response_timestamps(obj)
        groups = obj.get("group_results") or []
        if not isinstance(groups, list):
            return kept, skipped_old, timestamps
        for group in groups:
            if not isinstance(group, dict):
                continue
            entities = group.get("entity_results") or []
            if not isinstance(entities, list):
                continue
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                ts = extract_timestamp_usecs(entity, sort_attr)
                if window_start_usecs is not None:
                    if ts is None or ts < window_start_usecs:
                        skipped_old += 1
                        continue
                title = extract_title(entity)
                if title:
                    norm_title = normalize_title(title)
                    if GROUP_BY_CLUSTER_NAME:
                        cluster_name = extract_attribute_value(entity, "cluster_name") or "unknown_cluster"
                        cluster_key = str(cluster_name).strip() or "unknown_cluster"
                        cluster_counters.setdefault(cluster_key, Counter())[norm_title] += 1
                    counter[norm_title] += 1
                    kept += 1
        return kept, skipped_old, timestamps

    def build_result_snapshot(end_time_iso: str | None = None) -> dict[str, Any]:
        if end_time_iso is None:
            end_time_iso = _iso_utc()
        overall_total = int(sum(counter.values()))
        title_totals_obj: dict[str, int] = dict(counter.most_common())
        if not GROUP_BY_CLUSTER_NAME:
            counts_obj: dict[str, Any] = dict(counter.most_common())
            cluster_totals_obj: dict[str, int] = {}
        else:
            counts_obj = {}
            cluster_totals_obj = {}
            for cluster_name in sorted(cluster_counters.keys()):
                cluster_counter = cluster_counters[cluster_name]
                counts_obj[cluster_name] = dict(cluster_counter.most_common())
                cluster_totals_obj[cluster_name] = int(sum(cluster_counter.values()))
        return {
            "start_time_utc": run_start_iso,
            "end_time_utc": end_time_iso,
            "total": overall_total,
            "title_totals": title_totals_obj,
            "cluster_totals": cluster_totals_obj,
            "counts": counts_obj,
        }

    first_timestamps = extract_response_timestamps(first)
    first_page_max_ts = max(first_timestamps) if first_timestamps else None

    prefetched_page = first
    offset = start_offset
    page_idx = start_page_idx
    prev_page_max_ts = None

    if (
        LAST_N_HOURS_ONLY_ENABLED
        and ENABLE_CUTOFF_PAGE_SEEK
        and sort_order.upper() == "ASCENDING"
        and window_start_usecs is not None
        and first_page_max_ts is not None
        and first_page_max_ts < window_start_usecs
        and filtered_entity_count > 0
    ):
        last_offset = ((filtered_entity_count - 1) // GROUP_MEMBER_COUNT) * GROUP_MEMBER_COUNT
        low_idx = start_offset // GROUP_MEMBER_COUNT
        high_idx: int | None = None
        high_page: dict[str, Any] | None = None
        step_pages = 1

        # Exponential probe to find first page-range that crosses cutoff.
        while low_idx + step_pages <= (last_offset // GROUP_MEMBER_COUNT):
            probe_idx = low_idx + step_pages
            probe_offset = probe_idx * GROUP_MEMBER_COUNT
            probe_page = fetch_page(
                entity_type=entity_type,
                attributes=attributes,
                group_member_count=GROUP_MEMBER_COUNT,
                group_member_offset=probe_offset,
                sort_attr=sort_attr,
                sort_order=sort_order,
                timeout=REQUEST_TIMEOUT_SEC,
            )
            probe_timestamps = extract_response_timestamps(probe_page)
            probe_max_ts = max(probe_timestamps) if probe_timestamps else None
            print(
                f"[INFO][{entity_type}] cutoff-seek probe page={probe_idx + 1}, "
                f"offset={probe_offset}, page_max_ts={probe_max_ts}",
                file=sys.stderr,
            )
            if probe_max_ts is not None and probe_max_ts >= window_start_usecs:
                high_idx = probe_idx
                high_page = probe_page
                break
            low_idx = probe_idx
            step_pages = min(step_pages * 2, MAX_DYNAMIC_SKIP_PAGES)

        if high_idx is None:
            # Exponential probing may stop before probing the very last page.
            # Validate the last page before concluding everything is older.
            last_page = fetch_page(
                entity_type=entity_type,
                attributes=attributes,
                group_member_count=GROUP_MEMBER_COUNT,
                group_member_offset=last_offset,
                sort_attr=sort_attr,
                sort_order=sort_order,
                timeout=REQUEST_TIMEOUT_SEC,
            )
            last_timestamps = extract_response_timestamps(last_page)
            last_max_ts = max(last_timestamps) if last_timestamps else None
            print(
                f"[INFO][{entity_type}] cutoff-seek final-check page={(last_offset // GROUP_MEMBER_COUNT) + 1}, "
                f"offset={last_offset}, page_max_ts={last_max_ts}",
                file=sys.stderr,
            )
            if last_max_ts is not None and last_max_ts >= window_start_usecs:
                high_idx = last_offset // GROUP_MEMBER_COUNT
                high_page = last_page
            else:
                print(
                    f"[INFO][{entity_type}] cutoff-seek: all pages are older than cutoff, returning empty result",
                    file=sys.stderr,
                )
                result = build_result_snapshot(_iso_utc())
                writer_q.put(result)
                writer_q.put(None)
                writer_q.join()
                writer_t.join(timeout=5)
                print(f"[INFO][{entity_type}] wrote output to {output_file}", file=sys.stderr)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return 0

        # Binary search between low_idx (older) and high_idx (crosses cutoff).
        while high_idx - low_idx > 1:
            mid_idx = (low_idx + high_idx) // 2
            mid_offset = mid_idx * GROUP_MEMBER_COUNT
            mid_page = fetch_page(
                entity_type=entity_type,
                attributes=attributes,
                group_member_count=GROUP_MEMBER_COUNT,
                group_member_offset=mid_offset,
                sort_attr=sort_attr,
                sort_order=sort_order,
                timeout=REQUEST_TIMEOUT_SEC,
            )
            mid_timestamps = extract_response_timestamps(mid_page)
            mid_max_ts = max(mid_timestamps) if mid_timestamps else None
            print(
                f"[INFO][{entity_type}] cutoff-seek bisect page={mid_idx + 1}, "
                f"offset={mid_offset}, page_max_ts={mid_max_ts}",
                file=sys.stderr,
            )
            if mid_max_ts is not None and mid_max_ts >= window_start_usecs:
                high_idx = mid_idx
                high_page = mid_page
            else:
                low_idx = mid_idx

        if high_page is not None:
            prefetched_page = high_page
            page_idx = high_idx + 1
            offset = high_idx * GROUP_MEMBER_COUNT
            print(
                f"[INFO][{entity_type}] cutoff-seek start page resolved to {page_idx}/{total_pages} "
                f"(offset={offset})",
                file=sys.stderr,
            )

    writer_q.put(build_result_snapshot())

    while offset < filtered_entity_count:
        if prefetched_page is not None:
            page = prefetched_page
            prefetched_page = None
        else:
            page = fetch_page(
                entity_type=entity_type,
                attributes=attributes,
                group_member_count=GROUP_MEMBER_COUNT,
                group_member_offset=offset,
                sort_attr=sort_attr,
                sort_order=sort_order,
                timeout=REQUEST_TIMEOUT_SEC,
            )
        kept, skipped_old, timestamps = process_response(page)
        page_min_ts = min(timestamps) if timestamps else None
        page_max_ts = max(timestamps) if timestamps else None

        if window_start_usecs is not None:
            print(
                f"[INFO][{entity_type}] page {page_idx}/{total_pages}: offset={offset}, kept={kept}, "
                f"skipped_old={skipped_old}, page_min_ts={page_min_ts}, page_max_ts={page_max_ts}",
                file=sys.stderr,
            )

        if (
            LAST_N_HOURS_ONLY_ENABLED
            and ENABLE_DYNAMIC_OFFSET_SKIP
            and sort_order.upper() == "ASCENDING"
            and window_start_usecs is not None
            and page_max_ts is not None
            and page_max_ts < window_start_usecs
        ):
            estimated_pages_to_skip = 0
            if prev_page_max_ts is not None and page_max_ts > prev_page_max_ts:
                delta_ts_per_page = page_max_ts - prev_page_max_ts
                if delta_ts_per_page > 0:
                    remaining_gap = window_start_usecs - page_max_ts
                    # Apply safety divisor so we under-jump and refine gradually.
                    conservative_delta = max(1, delta_ts_per_page * DYNAMIC_SKIP_SAFETY_DIVISOR)
                    estimated_pages_to_skip = max(0, int(remaining_gap // conservative_delta) - 1)

                    # Use tiered cap: large jumps when very old, tiny jumps near cutoff.
                    remaining_gap_hours = remaining_gap / (3_600 * 1_000_000)
                    tier_cap = MAX_DYNAMIC_SKIP_PAGES
                    if remaining_gap_hours <= DYNAMIC_SKIP_NEAR_CUTOFF_HOURS:
                        tier_cap = DYNAMIC_SKIP_NEAR_CUTOFF_MAX_PAGES
                    elif remaining_gap_hours <= DYNAMIC_SKIP_MID_CUTOFF_HOURS:
                        tier_cap = DYNAMIC_SKIP_MID_CUTOFF_MAX_PAGES
                    estimated_pages_to_skip = min(estimated_pages_to_skip, tier_cap)
            if estimated_pages_to_skip > 0:
                estimated_pages_to_skip = min(estimated_pages_to_skip, MAX_DYNAMIC_SKIP_PAGES)
                # Never jump beyond available pages.
                pages_remaining_after_next = max(
                    0,
                    ((filtered_entity_count - 1) - (offset + GROUP_MEMBER_COUNT)) // GROUP_MEMBER_COUNT,
                )
                estimated_pages_to_skip = min(estimated_pages_to_skip, pages_remaining_after_next)
                if estimated_pages_to_skip <= 0:
                    prev_page_max_ts = page_max_ts
                    offset += GROUP_MEMBER_COUNT
                    page_idx += 1
                    continue

                skipped_records = estimated_pages_to_skip * GROUP_MEMBER_COUNT
                next_offset = offset + GROUP_MEMBER_COUNT + skipped_records
                print(
                    f"[INFO][{entity_type}] dynamic skip: page_max_ts below cutoff, "
                    f"jumping +{estimated_pages_to_skip} pages "
                    f"(offset {offset} -> {next_offset})",
                    file=sys.stderr,
                )
                offset = next_offset
                page_idx += estimated_pages_to_skip + 1
                prev_page_max_ts = page_max_ts
                continue

        if (
            LAST_N_HOURS_ONLY_ENABLED
            and sort_order.upper() == "DESCENDING"
            and window_start_usecs is not None
            and page_max_ts is not None
            and page_max_ts < window_start_usecs
        ):
            print(
                f"[INFO][{entity_type}] reached pages fully older than cutoff at page {page_idx}, stopping early",
                file=sys.stderr,
            )
            break

        # Update output file on every page through writer thread.
        writer_q.put(build_result_snapshot())
        if page_idx % PAUSE_EVERY_PAGES == 0:
            print(
                f"[INFO][{entity_type}] cooling down {PAUSE_SECONDS}s after {page_idx} pages",
                file=sys.stderr,
            )
            time.sleep(PAUSE_SECONDS)
        if page_idx % 50 == 0 or page_idx == total_pages:
            print(f"[INFO][{entity_type}] processed page {page_idx}/{total_pages}", file=sys.stderr)
        prev_page_max_ts = page_max_ts
        offset += GROUP_MEMBER_COUNT
        page_idx += 1

    result = build_result_snapshot(_iso_utc())
    # Ensure final snapshot is persisted and writer exits cleanly.
    writer_q.put(result)
    writer_q.put(None)
    writer_q.join()
    writer_t.join(timeout=5)
    print(f"[INFO][{entity_type}] wrote output to {output_file}", file=sys.stderr)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    if GROUP_MEMBER_COUNT <= 0:
        print("group-member-count must be > 0", file=sys.stderr)
        return 2

    AUDIT_ENABLED = True
    EVENT_ENABLED = False

    if AUDIT_ENABLED:
        print("Running audit title count job...")
        audit_rc = run_title_count_job(
            entity_type="audit",
            attributes=AUDIT_ATTRIBUTES,
            sort_attr="op_start_timestamp_usecs",
            sort_order="ASCENDING",
            output_file=AUDIT_OUTPUT_FILE,
        )
        if audit_rc != 0:
            return audit_rc
        else:
            print("Audit title count job completed successfully")

    if EVENT_ENABLED:
        print("Running event title count job...")
        event_rc = run_title_count_job(
            entity_type="event",
            attributes=EVENT_ATTRIBUTES,
            sort_attr="_created_timestamp_usecs_",
            sort_order="DESCENDING",
            output_file=EVENT_OUTPUT_FILE,
        )
        if event_rc != 0:
            return event_rc
        else:
            print("Event title count job completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
