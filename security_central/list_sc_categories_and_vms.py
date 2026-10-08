#!/usr/bin/env python3
"""List VMs for every Level-1 × Level-2 CATEGORY pair (keys must differ).

APIs from Security Planning HAR:
  1) GET  /securitycentral/v2/resourceGroups
  2) POST /securitycentral/v2/securityPlanning/dimensions/values  (keys=level1)
  3) POST /securitycentral/v2/securityPlanning/dimensions/values  (keys=level2)
  4) POST /securitycentral/v2/inventory/resources/nx/vms?action=groupByLevels
     grouping.level1 = CATEGORY, grouping.level2 = CATEGORY
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Config — edit these variables as needed
# ---------------------------------------------------------------------------
BASE_URL = "https://ncm.services.nconprem-10-114-54-190.ccpnx.com"
USERNAME = "admin"
PASSWORD = "Nutanix.123"
NCM_PROJECT_ID = "00000000-0000-0000-0000-000000000000"

# Optional PC resourceGroupId. Empty => use first NX_PC from resourceGroups API.
RESOURCE_GROUP_ID = ""

# Output file is rewritten after every category pair.
OUTPUT_JSON = str(Path(__file__).with_name("sc_categories_and_vms.json"))

SC_BASE = "/securitycentral/v2"

client = requests.Session()
client.auth = HTTPBasicAuth(USERNAME, PASSWORD)
client.headers = {"content-type": "application/json", "accept": "application/json"}
client.verify = False


class ApiMetrics:
    """Locust-style latency tracker for API calls."""

    SUCCESS_CODES = {200, 201, 202}

    def __init__(self) -> None:
        self.records: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

    def record(
        self,
        method: str,
        endpoint: str,
        elapsed_ms: float,
        status_code: Optional[int],
        error: bool = False,
    ) -> None:
        self.records[(method.upper(), endpoint)].append(
            {
                "elapsed_ms": float(elapsed_ms),
                "status_code": status_code,
                "error": error,
                "failed": error or (status_code not in self.SUCCESS_CODES if status_code else True),
            }
        )

    @staticmethod
    def _percentile(sorted_values: List[float], pct: float) -> float:
        if not sorted_values:
            return 0.0
        if len(sorted_values) == 1:
            return sorted_values[0]
        k = (len(sorted_values) - 1) * (pct / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_values) - 1)
        if f == c:
            return sorted_values[f]
        return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)

    def get_report(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for (method, endpoint), entries in self.records.items():
            times = sorted(e["elapsed_ms"] for e in entries)
            status_codes: Dict[str, int] = defaultdict(int)
            failures = 0
            errors = 0
            for e in entries:
                if e["status_code"] is None:
                    status_codes["EXC"] += 1
                else:
                    status_codes[str(e["status_code"])] += 1
                if e["failed"]:
                    failures += 1
                if e["error"]:
                    errors += 1
            rows.append(
                {
                    "method": method,
                    "endpoint": endpoint,
                    "count": len(entries),
                    "failures": failures,
                    "errors": errors,
                    "min_ms": times[0] if times else 0.0,
                    "max_ms": times[-1] if times else 0.0,
                    "avg_ms": (sum(times) / len(times)) if times else 0.0,
                    "p50_ms": self._percentile(times, 50),
                    "p90_ms": self._percentile(times, 90),
                    "p95_ms": self._percentile(times, 95),
                    "p98_ms": self._percentile(times, 98),
                    "status_codes": dict(status_codes),
                }
            )
        rows.sort(key=lambda r: r["count"], reverse=True)
        return rows

    def print_report(self) -> None:
        report = self.get_report()
        if not report:
            print("[INFO] No API calls recorded.", flush=True)
            return

        print("", flush=True)
        print("=" * 160, flush=True)
        print("API METRICS CONSOLIDATED REPORT", flush=True)
        print("=" * 160, flush=True)
        header = (
            f"{'Method':<8} | {'Endpoint':<50} | {'Count':>7} | {'Fail':>6} | "
            f"{'Min(ms)':>10} | {'Avg(ms)':>10} | {'Max(ms)':>10} | "
            f"{'P90(ms)':>10} | {'P95(ms)':>10} | {'P98(ms)':>10}"
        )
        print(header, flush=True)
        print("-" * 160, flush=True)
        for row in report:
            endpoint = row["endpoint"]
            endpoint_display = endpoint[:48] + ".." if len(endpoint) > 50 else endpoint
            fail_display = str(row["failures"]) if row["failures"] else "-"
            print(
                f"{row['method']:<8} | {endpoint_display:<50} | {row['count']:>7} | "
                f"{fail_display:>6} | {row['min_ms']:>10.2f} | {row['avg_ms']:>10.2f} | "
                f"{row['max_ms']:>10.2f} | {row['p90_ms']:>10.2f} | "
                f"{row['p95_ms']:>10.2f} | {row['p98_ms']:>10.2f}",
                flush=True,
            )
        print("-" * 160, flush=True)
        total_calls = sum(r["count"] for r in report)
        total_failures = sum(r["failures"] for r in report)
        total_errors = sum(r["errors"] for r in report)
        print(
            f"Total API Calls: {total_calls} | Unique Endpoints: {len(report)} | "
            f"Total Failures (non-200/202): {total_failures} | Exceptions: {total_errors}",
            flush=True,
        )
        print("=" * 160, flush=True)


METRICS = ApiMetrics()


def _normalize_endpoint(path: str) -> str:
    """Strip query string for stable Locust-style endpoint grouping."""
    parsed = urlparse(path)
    return parsed.path or path.split("?", 1)[0]


def _url(path: str) -> str:
    return f"{BASE_URL.rstrip('/')}{path}"


def _request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 180,
) -> Tuple[Dict[str, Any], float]:
    endpoint = _normalize_endpoint(path)
    started = time.perf_counter()
    status_code: Optional[int] = None
    error = False
    try:
        if method.upper() == "GET":
            resp = client.get(_url(path), timeout=timeout)
        else:
            resp = client.post(_url(path), data=json.dumps(payload or {}), timeout=timeout)
        status_code = resp.status_code
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        METRICS.record(method, endpoint, elapsed_ms, status_code, error=False)
        if resp.status_code != 200:
            raise RuntimeError(f"{method} {path} failed: {resp.status_code} {resp.text[:500]}")
        return (resp.json() if resp.text else {}), elapsed_ms
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if status_code is None:
            error = True
            METRICS.record(method, endpoint, elapsed_ms, None, error=True)
        raise


def list_resource_groups(ncm_project_id: str) -> Tuple[List[Dict[str, Any]], float]:
    data, elapsed_ms = _request(
        "GET", f"{SC_BASE}/resourceGroups?ncmProjectIds={ncm_project_id}", timeout=120
    )
    return data.get("items", []), elapsed_ms


def list_dimension_values(
    keys: List[str],
    resource_group_ids: List[str],
    ncm_project_ids: List[str],
    pc_project_ids: List[str],
) -> Tuple[Dict[str, Any], float]:
    payload = {
        "keys": keys,
        "resourceGroupIds": resource_group_ids,
        "ncmProjectIds": ncm_project_ids,
        "pcProjectIds": pc_project_ids,
    }
    return _request("POST", f"{SC_BASE}/securityPlanning/dimensions/values", payload)


def group_vms_by_levels(
    resource_group_ids: List[str],
    ncm_project_ids: List[str],
    pc_project_ids: List[str],
    level1: Dict[str, str],
    level2: Dict[str, str],
) -> Tuple[Dict[str, Any], float]:
    payload = {
        "resourceGroupIds": resource_group_ids,
        "ncmProjectIds": ncm_project_ids,
        "pcProjectIds": pc_project_ids,
        "filters": {},
        "grouping": {
            "level1": level1,
            "level2": level2,
        },
    }
    return _request(
        "POST",
        f"{SC_BASE}/inventory/resources/nx/vms?action=groupByLevels",
        payload,
        timeout=180,
    )


def category_only(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [i for i in items if i.get("type") == "CATEGORY" and i.get("key")]


def cat_label(item: Dict[str, Any]) -> str:
    name = str(item.get("displayName") or item.get("key") or "")
    return name.replace("Category: ", "").strip()


def extract_vms(group_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten VM entities from category×category groupByLevels response."""
    vms: List[Dict[str, Any]] = []
    seen = set()
    level1 = group_response.get("level1") or {}
    for l1_item in level1.get("items") or []:
        l2 = l1_item.get("level2") or {}
        for l2_item in l2.get("items") or []:
            for entity in l2_item.get("entities") or []:
                vm_info = entity.get("vmInfo") or {}
                vm_id = vm_info.get("vmId")
                if not vm_id or vm_id in seen:
                    continue
                seen.add(vm_id)
                vms.append(
                    {
                        "vm_id": vm_id,
                        "vm_name": vm_info.get("vmName"),
                        "ip": entity.get("ip"),
                        "vlan_id": entity.get("vlanId"),
                        "cluster_name": entity.get("clusterName"),
                        "cluster_id": entity.get("clusterId"),
                        "project_name": vm_info.get("projectName"),
                        "level1_assignment_status": l1_item.get("assignmentStatus"),
                        "level2_assignment_status": l2_item.get("assignmentStatus"),
                        "level2_assignment_value": l2_item.get("assignmentValue"),
                        "level2_assignment_value_display_name": l2_item.get(
                            "assignmentValueDisplayName"
                        ),
                        "categories": vm_info.get("categories") or [],
                    }
                )
    return vms


def write_output(path: str, payload: Dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ncm_project_ids = [NCM_PROJECT_ID]
    pc_project_ids = [NCM_PROJECT_ID]

    resource_groups, _ = list_resource_groups(NCM_PROJECT_ID)
    if not resource_groups:
        raise RuntimeError("No resource groups found")

    if RESOURCE_GROUP_ID:
        resource_group_ids = [RESOURCE_GROUP_ID]
    else:
        nx_pcs = [rg for rg in resource_groups if rg.get("resourceGroupType") == "NX_PC"]
        chosen = nx_pcs[0] if nx_pcs else resource_groups[0]
        resource_group_ids = [chosen["resourceGroupId"]]

    level1_resp, _ = list_dimension_values(
        ["level1"], resource_group_ids, ncm_project_ids, pc_project_ids
    )
    level2_resp, _ = list_dimension_values(
        ["level2"], resource_group_ids, ncm_project_ids, pc_project_ids
    )
    level1_items = category_only(level1_resp.get("level1") or [])
    level2_items = category_only(level2_resp.get("level2") or [])

    results: List[Dict[str, Any]] = []
    out = {
        "resource_group_ids": resource_group_ids,
        "level1_categories": [
            {"displayName": c.get("displayName"), "key": c.get("key"), "namespace": c.get("namespace")}
            for c in level1_items
        ],
        "level2_categories": [
            {"displayName": c.get("displayName"), "key": c.get("key"), "namespace": c.get("namespace")}
            for c in level2_items
        ],
        "pairs": results,
        "api_metrics": [],
    }
    write_output(OUTPUT_JSON, out)

    total_pairs = sum(1 for a in level1_items for b in level2_items if a.get("key") != b.get("key"))
    done = 0

    for cat1 in level1_items:
        for cat2 in level2_items:
            if cat1.get("key") == cat2.get("key"):
                continue

            c1_name = cat_label(cat1)
            c2_name = cat_label(cat2)
            print(f"[STARTED] cat1={c1_name} cat2={c2_name}", flush=True)

            pair: Dict[str, Any] = {
                "level1": {
                    "displayName": cat1.get("displayName"),
                    "key": cat1.get("key"),
                    "namespace": cat1.get("namespace"),
                },
                "level2": {
                    "displayName": cat2.get("displayName"),
                    "key": cat2.get("key"),
                    "namespace": cat2.get("namespace"),
                },
                "vms": [],
                "total_vms": 0,
                "time_taken_ms": None,
                "error": None,
            }

            try:
                group_resp, elapsed_ms = group_vms_by_levels(
                    resource_group_ids=resource_group_ids,
                    ncm_project_ids=ncm_project_ids,
                    pc_project_ids=pc_project_ids,
                    level1={"type": "CATEGORY", "key": cat1["key"]},
                    level2={"type": "CATEGORY", "key": cat2["key"]},
                )
                pair["time_taken_ms"] = round(elapsed_ms, 2)
                vms = extract_vms(group_resp)
                pair["vms"] = vms
                pair["total_vms"] = len(vms)
                pair["summary"] = {
                    "totalVMs": (group_resp.get("level1") or {}).get("totalVMs"),
                    "totalIPs": (group_resp.get("level1") or {}).get("totalIPs"),
                    "keyDisplayName": (group_resp.get("level1") or {}).get("keyDisplayName"),
                }
            except Exception as exc:  # pylint: disable=broad-except
                pair["error"] = str(exc)

            results.append(pair)
            out["api_metrics"] = METRICS.get_report()
            write_output(OUTPUT_JSON, out)

            done += 1
            time_txt = (
                f"{pair['time_taken_ms']:.2f}ms"
                if isinstance(pair["time_taken_ms"], (int, float))
                else "n/a"
            )
            print(
                f"[COMPLETED] cat1={c1_name} cat2={c2_name} "
                f"vms={pair['total_vms']} time={time_txt} ({done}/{total_pairs})",
                flush=True,
            )

    out["api_metrics"] = METRICS.get_report()
    write_output(OUTPUT_JSON, out)
    METRICS.print_report()


if __name__ == "__main__":
    main()
