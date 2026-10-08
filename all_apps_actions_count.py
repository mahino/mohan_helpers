#!/usr/bin/env python3
"""Aggregate action counts across all Calm apps.

Outputs, per action name:
1) app_count: number of distinct apps containing that action
2) total_action_count: total occurrences across all apps
"""

import argparse
import json
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_BASE_URL = "https://ncm.services.nconprem-10-114-55-128.ccpnx.com/"
V3 = "api/nutanix/v3/"


def build_session(base_url: str, username: str, password: str) -> requests.Session:
    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)
    session.headers = {"content-type": "application/json"}
    session.verify = False
    session.base_url = base_url if base_url.endswith("/") else base_url + "/"
    return session


def list_all_apps(session: requests.Session, page_size: int = 200) -> list:
    """Fetch all apps using v3 apps/list pagination."""
    apps = []
    offset = 0

    while True:
        payload = {"kind": "app", "offset": offset, "length": page_size}
        print(f"[INFO] Fetching apps page: offset={offset}, length={page_size}", flush=True)
        resp = session.post(session.base_url + V3 + "apps/list", data=json.dumps(payload), timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"apps/list failed at offset={offset}: {resp.status_code} {resp.text}")

        body = resp.json()
        entities = body.get("entities", [])
        if not entities:
            break

        apps.extend(entities)
        print(f"[INFO] Received {len(entities)} apps (running total={len(apps)})", flush=True)
        if len(entities) < page_size:
            break
        offset += page_size

    return apps


def get_app_details(session: requests.Session, app_uuid: str) -> dict:
    resp = session.get(session.base_url + V3 + f"apps/{app_uuid}", timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"apps/{app_uuid} failed: {resp.status_code} {resp.text}")
    return resp.json()


def aggregate_actions(session: requests.Session, app_refs: list, max_workers: int = 5) -> tuple:
    action_to_apps = defaultdict(set)
    action_to_total = defaultdict(int)
    processed = 0
    failed = 0
    start_time = time.time()

    app_items = []
    for app in app_refs:
        app_uuid = app.get("metadata", {}).get("uuid") or app.get("status", {}).get("uuid")
        app_name = app.get("metadata", {}).get("name", "unknown")
        if not app_uuid:
            failed += 1
            continue
        app_items.append((app_uuid, app_name))

    total_apps = len(app_items)
    workers = max(1, int(max_workers))
    print(f"[INFO] Starting parallel fetch with workers={workers}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_app = {
            executor.submit(get_app_details, session, app_uuid): (app_uuid, app_name)
            for app_uuid, app_name in app_items
        }
        for index, future in enumerate(as_completed(future_to_app), start=1):
            app_uuid, app_name = future_to_app[future]
            if index == 1 or index % 25 == 0 or index == total_apps:
                elapsed = max(0.001, time.time() - start_time)
                rate = index / elapsed
                remaining = max(0, total_apps - index)
                eta_sec = int(remaining / rate) if rate > 0 else 0
                print(
                    f"[INFO] Processing app {index}/{total_apps}: {app_name} | "
                    f"processed={processed} failed={failed} rate={rate:.2f}/s eta={eta_sec}s",
                    flush=True,
                )
            try:
                detail = future.result()
                actions = detail.get("spec", {}).get("resources", {}).get("action_list", [])
                for action in actions:
                    action_name = action.get("name", "UNKNOWN_ACTION")
                    action_to_total[action_name] += 1
                    action_to_apps[action_name].add(app_uuid)
                processed += 1
            except Exception as exc:  # pylint: disable=broad-except
                failed += 1
                print(f"[WARN] Skipping app={app_name} uuid={app_uuid}: {exc}", flush=True)

    total_elapsed = time.time() - start_time
    print(
        f"[INFO] Aggregation complete in {total_elapsed:.2f}s "
        f"(processed={processed}, failed={failed})",
        flush=True,
    )

    rows = []
    for action_name in sorted(action_to_total.keys(), key=str.lower):
        rows.append(
            {
                "action_name": action_name,
                "app_count": len(action_to_apps[action_name]),
                "total_action_count": action_to_total[action_name],
            }
        )

    return rows, processed, failed


def print_report(rows: list, processed: int, failed: int) -> None:
    print("")
    print("Actions Summary (All Apps)")
    print("=" * 90)
    print(f"Apps processed: {processed} | Apps failed: {failed} | Unique actions: {len(rows)}")
    print("-" * 90)
    print(f"{'ACTION NAME':40} {'APP COUNT':>12} {'TOTAL ACTIONS':>16}")
    print("-" * 90)
    for row in rows:
        print(f"{row['action_name'][:40]:40} {row['app_count']:>12} {row['total_action_count']:>16}")
    print("-" * 90)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Count all actions across all apps")
    parser.add_argument("--base-url", default=os.getenv("NCM_BASE_URL", DEFAULT_BASE_URL), help="NCM base URL")
    parser.add_argument("--username", default=os.getenv("NCM_USERNAME", "admin"), help="NCM username")
    parser.add_argument("--password", default=os.getenv("NCM_PASSWORD", "Nutanix.123"), help="NCM password")
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write JSON summary (action_name, app_count, total_action_count)",
    )
    parser.add_argument("--page-size", type=int, default=200, help="apps/list page size")
    parser.add_argument("--workers", type=int, default=5, help="Parallel workers for app detail fetch")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    session = build_session(args.base_url, args.username, args.password)

    app_refs = list_all_apps(session, page_size=args.page_size)
    print(f"[INFO] Found {len(app_refs)} apps. Aggregating actions...")

    rows, processed, failed = aggregate_actions(session, app_refs, max_workers=args.workers)
    print_report(rows, processed, failed)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "apps_processed": processed,
                    "apps_failed": failed,
                    "unique_actions": len(rows),
                    "rows": rows,
                },
                f,
                indent=2,
            )
        print(f"[INFO] Wrote JSON summary to: {args.output_json}")


if __name__ == "__main__":
    main()
