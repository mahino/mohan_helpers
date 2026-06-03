import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Match create_cost_center_v2.py request target.
NCM_BASE_URL = "https://ncm.services.nconprem-10-114-55-128.ccpnx.com"

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}

API_TIMEOUT = 30

DEFAULT_DURATION_SECONDS = 3600
DEFAULT_INTERVAL_SECONDS = 10
DEFAULT_OUTPUT_FILE = "cluster_cost_timeseries.json"
DEFAULT_START_EPOCH = 1780272000
DEFAULT_END_EPOCH = 1782863940


def fetch_clusters_snapshot(start_epoch: int, end_epoch: int, limit: int = 500, offset: int = 1) -> dict:
    url = f"{NCM_BASE_URL}/v1/cg/nutanix/metering/clusters?limit={limit}&offset={offset}"
    payload = {
        "timeUnit": "month",
        "timeRange": {
            "startTime": start_epoch,
            "endTime": end_epoch,
        },
        "resourceGroupType": "",
        "resourceGroupIds": [],
        "currencyType": "TARGET",
    }
    # Use same request structure as create_cost_center_v2.py (data=json.dumps).
    response = requests.post(url, data=json.dumps(payload), headers=HEADERS, verify=False, timeout=API_TIMEOUT)
    response.raise_for_status()
    return response.json()


def extract_clusters(payload: dict):
    """
    Extract cluster rows from possible API shapes.
    Expected primary shape:
      { items: [ { date: "...", data: [ {clusterName, cost...}, ... ] } ] }
    """
    extracted = []
    items = payload.get("items", [])
    if isinstance(items, list):
        for item in items:
            item_date = item.get("date")
            for cluster in item.get("data", []) or []:
                extracted.append(
                    {
                        "item_date": item_date,
                        "cluster_id": cluster.get("clusterId"),
                        "cluster_name": cluster.get("clusterName") or "unknown-cluster",
                        "cost": cluster.get("cost"),
                    }
                )
    return extracted


def monitor_loop(duration_seconds: int, interval_seconds: int, output_file: str, start_epoch: int, end_epoch: int) -> int:
    output_path = Path(output_file).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    started_at = time.time()
    poll_index = 0
    cluster_cost_history = {}

    print("=" * 90)
    print("Cluster Cost Monitor")
    print(f"Duration: {duration_seconds}s | Interval: {interval_seconds}s | Output: {output_path}")
    print("=" * 90)

    try:
        while True:
            elapsed = time.time() - started_at
            if elapsed >= duration_seconds:
                print("Duration complete. Stopping monitor.")
                break

            poll_index += 1
            poll_time = datetime.utcnow().isoformat() + "Z"
            timelapse_seconds = int(elapsed)
            print(f"[POLL {poll_index}] Fetching clusters... (timelapse={timelapse_seconds}s)")

            try:
                data = fetch_clusters_snapshot(start_epoch=start_epoch, end_epoch=end_epoch)
            except Exception as exc:
                print(f"[POLL {poll_index}] API error: {exc}")
                time.sleep(interval_seconds)
                continue

            clusters = extract_clusters(data)
            poll_cluster_count = len(clusters)

            # Update per-cluster cost history on every poll.
            for cluster in clusters:
                key = cluster.get("cluster_id") or cluster.get("cluster_name")
                if key not in cluster_cost_history:
                    cluster_cost_history[key] = {
                        "cluster_id": cluster.get("cluster_id"),
                        "cluster_name": cluster.get("cluster_name") or str(key),
                        "history": [],
                    }
                cluster_cost_history[key]["history"].append(
                    {
                        "poll_index": poll_index,
                        "timelapse_seconds": timelapse_seconds,
                        "gmt": poll_time,
                        "cost": cluster.get("cost"),
                    }
                )

            snapshot = {
                "updated_at_gmt": poll_time,
                "poll_index": poll_index,
                "timelapse_seconds": timelapse_seconds,
                "poll_cluster_count": poll_cluster_count,
                "clusters": sorted(
                    cluster_cost_history.values(),
                    key=lambda x: (x.get("cluster_name") or "").lower()
                ),
            }
            output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
            print(f"[POLL {poll_index}] Updated JSON with {poll_cluster_count} clusters -> {output_path}")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("Aborted by user (Ctrl+C).")

    print(f"Done. Polls={poll_index}, file={output_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll clusters API and store specs time series.")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_SECONDS, help="Monitor duration in seconds")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS, help="Poll frequency in seconds")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_FILE, help="Output CSV path")
    parser.add_argument("--start-epoch", type=int, default=DEFAULT_START_EPOCH, help="API timeRange.startTime")
    parser.add_argument("--end-epoch", type=int, default=DEFAULT_END_EPOCH, help="API timeRange.endTime")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration <= 0:
        print("Error: --duration must be > 0")
        return 1
    if args.interval <= 0:
        print("Error: --interval must be > 0")
        return 1
    return monitor_loop(
        duration_seconds=args.duration,
        interval_seconds=args.interval,
        output_file=args.output,
        start_epoch=args.start_epoch,
        end_epoch=args.end_epoch,
    )


if __name__ == "__main__":
    sys.exit(main())
