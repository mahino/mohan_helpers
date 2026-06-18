#!/usr/bin/env python3
"""
Update Calm app protection snapshot expiry for all projects.

Flow (derived from HAR APIs):
1) List projects            : GET  /api/multidomain/v4.3.b1/config/projects
2) Get project              : GET  /api/multidomain/v4.3.b1/config/projects/{project_ext_id}
3) List project snapshots   : POST /api/calm/v3.0/app_protection_policies/list
4) Get snapshot/policy      : GET  /api/calm/v3.0/app_protection_policies/{policy_uuid}
5) Update snapshot/policy   : PUT  /api/calm/v3.0/app_protection_policies/{policy_uuid}
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Iterable, List, Optional

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def _build_session(username: str, password: str) -> requests.Session:
    """Keep the same session pattern used by delete_bps.py."""
    client = requests.Session()
    client.auth = HTTPBasicAuth(username, password)
    client.headers = {"content-type": "application/json"}
    client.verify = False
    return client


def list_projects(
    session: requests.Session,
    projects_base_url: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    projects: List[Dict[str, Any]] = []
    page = 0
    while True:
        url = (
            f"{projects_base_url}/api/multidomain/v4.3.b1/config/projects"
            f"?%24filter=(isSystemDefined%20ne%20true%20and%20isDefault%20ne%20true)"
            f"&%24limit={limit}&%24orderby=name%20asc&%24page={page}"
        )
        resp = session.get(url, timeout=600)
        resp.raise_for_status()
        data = json.loads(resp.content or "{}")
        page_items = data.get("data") or []
        projects.extend(page_items)
        if len(page_items) < limit:
            break
        page += 1
        break
    return projects


def get_project(
    session: requests.Session,
    projects_base_url: str,
    project_ext_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Project-detail endpoint is inferred from the same v4 base path.
    If unavailable in some environments, caller can continue with list data.
    """
    url = f"{projects_base_url}/api/multidomain/v4.3.b1/config/projects/{project_ext_id}"
    resp = session.get(url, timeout=60)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    payload = resp.json()
    if isinstance(payload, dict) and payload.get("data"):
        return payload["data"]
    return payload if isinstance(payload, dict) else None


def list_project_policies(
    session: requests.Session,
    ncm_base_url: str,
    project_ext_id: str,
) -> List[Dict[str, Any]]:
    url = f"{ncm_base_url}/api/calm/v3.0/app_protection_policies/list"
    payload = {"filter": f"project_reference=={project_ext_id}", "length": 200, "offset": 0}
    resp = session.post(url, data=json.dumps(payload), timeout=90)
    resp.raise_for_status()
    data = json.loads(resp.content or "{}")
    return data.get("entities") or []


def get_policy(
    session: requests.Session,
    ncm_base_url: str,
    policy_uuid: str,
) -> Dict[str, Any]:
    url = f"{ncm_base_url}/api/calm/v3.0/app_protection_policies/{policy_uuid}"
    resp = session.get(url, timeout=90)
    resp.raise_for_status()
    return json.loads(resp.content or "{}")


def _iter_policy_rules(spec: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    return (spec.get("resources") or {}).get("app_protection_rule_list") or []


def build_policy_update_payload(
    policy_obj: Dict[str, Any],
    expiry_days: int,
) -> Dict[str, Any]:
    metadata = dict(policy_obj.get("metadata") or {})
    spec = dict(policy_obj.get("spec") or {})
    resources = dict(spec.get("resources") or {})
    rules = resources.get("app_protection_rule_list") or []

    new_rules: List[Dict[str, Any]] = []
    for rule in rules:
        updated = dict(rule)
        lsrp = dict(updated.get("local_snapshot_retention_policy") or {})
        sep = dict(lsrp.get("snapshot_expiry_policy") or {})
        sep["multiple"] = expiry_days
        sep["interval_type"] = "DAYS"
        lsrp["snapshot_expiry_policy"] = sep
        updated["local_snapshot_retention_policy"] = lsrp
        new_rules.append(updated)

    resources["app_protection_rule_list"] = new_rules
    spec["resources"] = resources

    return {
        "spec": spec,
        "api_version": policy_obj.get("api_version", "3.0"),
        "metadata": metadata,
    }


def update_policy(
    session: requests.Session,
    ncm_base_url: str,
    policy_uuid: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    url = f"{ncm_base_url}/api/calm/v3.0/app_protection_policies/{policy_uuid}"
    resp = session.put(url, data=json.dumps(payload), timeout=90)
    resp.raise_for_status()
    return json.loads(resp.content or "{}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Update project snapshot expiry to 30 days (or custom).")
    p.add_argument("--projects-base-url", default="https://projects.services.nconprem-10-114-55-128.ccpnx.com", help="Hardcoded default projects URL")
    p.add_argument("--ncm-base-url", default="https://ncm.services.nconprem-10-114-55-128.ccpnx.com", help="Hardcoded default NCM URL")
    p.add_argument("--username", default="admin", help="Hardcoded default username")
    p.add_argument("--password", default="Nutanix.123", help="Hardcoded default password")
    p.add_argument("--expiry-days", type=int, default=30, help="Snapshot expiry days (default: 30)")
    p.add_argument("--dry-run", action="store_true", help="Print intended updates without PUT")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    projects_base_url = _normalize_base_url(args.projects_base_url)
    ncm_base_url = _normalize_base_url(args.ncm_base_url)

    session = _build_session(args.username, args.password)

    print("Listing projects...")
    projects = list_projects(session, projects_base_url)
    print(f"Found {len(projects)} project(s)")

    updated_policies = 0
    skipped_projects = 0

    for proj in projects:
        project_ext_id = proj.get("extId") or proj.get("id")
        project_name = proj.get("name") or project_ext_id
        if not project_ext_id:
            skipped_projects += 1
            continue

        project_detail = get_project(session, projects_base_url, project_ext_id)
        if project_detail is None:
            print(f"- Project detail endpoint unavailable for {project_name} ({project_ext_id}); continuing")
        else:
            project_name = project_detail.get("name") or project_name

        print(f"\nProject: {project_name} ({project_ext_id})")
        policies = list_project_policies(session, ncm_base_url, project_ext_id)
        print(f"  Policies/Snapshots found: {len(policies)}")

        for policy in policies:
            policy_uuid = (policy.get("metadata") or {}).get("uuid")
            policy_name = (policy.get("metadata") or {}).get("name") or policy_uuid
            if not policy_uuid:
                continue

            policy_full = get_policy(session, ncm_base_url, policy_uuid)
            update_payload = build_policy_update_payload(policy_full, args.expiry_days)
            rule_count = len(list(_iter_policy_rules(update_payload.get("spec") or {})))

            if args.dry_run:
                print(f"    [DRY-RUN] Would update policy {policy_name} ({policy_uuid}) with {rule_count} rule(s)")
                continue

            update_policy(session, ncm_base_url, policy_uuid, update_payload)
            updated_policies += 1
            print(f"    Updated policy {policy_name} ({policy_uuid}) -> expiry {args.expiry_days} days")

    print("\nDone.")
    print(f"Projects processed: {len(projects)} | skipped: {skipped_projects}")
    if args.dry_run:
        print("Dry-run only; no changes applied.")
    else:
        print(f"Policies updated: {updated_policies}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.HTTPError as exc:
        response_text = ""
        if exc.response is not None:
            response_text = exc.response.text[:1000]
        print(f"HTTP error: {exc}\n{response_text}", file=sys.stderr)
        raise
