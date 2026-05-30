"""Prism Element (PE): bulk VM power on, power off, or toggle (on/off).

Uses PE REST:
  - List: GET .../PrismGateway/services/rest/v1/vms (guest VMs, non-CVM)
  - Change: POST .../PrismGateway/services/rest/v2.0/vms/{uuid}/set_power_state
    body: {"transition":"on"|"off"}

Environment (optional):
  PE_URL / PRISM_ELEMENT_URL - base URL, e.g. https://10.46.209.189:9440
  PE_POWER_ACTION - default for --action: on | off | toggle
  NUTANIX_USER / NUTANIX_PASSWORD - HTTP basic (defaults admin / Nutanix.123)
  VM_PE_POWER_PARALLEL - max concurrent power operations (default 4, max 32)
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
import requests.auth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PE_BASE = (
    os.environ.get("PE_URL")
    or os.environ.get("PRISM_ELEMENT_URL")
    or "https://10.46.209.189:9440"
).rstrip("/")
POWER_PARALLEL = max(1, min(int(os.environ.get("VM_PE_POWER_PARALLEL", "4")), 32))

# Match other helpers: env overrides, then common lab default.
_NUSER = os.environ.get("NUTANIX_USER") or os.environ.get("PRISM_USER") or "admin"
_NPASS = os.environ.get("NUTANIX_PASSWORD") or os.environ.get("PRISM_PASSWORD") or "Nutanix.123"
_AUTH = requests.auth.HTTPBasicAuth(_NUSER, _NPASS)

GUEST_VM_FILTER = "is_control_domain!=1;is_cvm==0"
LIST_PAGE_SIZE = min(500, max(50, int(os.environ.get("VM_PE_LIST_PAGE_SIZE", "500") or "500")))

_log_lock = threading.Lock()
_log_file = open(
    f"vm_power_on_pe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", "a", encoding="utf-8"
)


def log_print(msg: object) -> None:
    line = str(msg)
    with _log_lock:
        print(line)
        _log_file.write(line + "\n")
        _log_file.flush()


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "ntnx-request-id": str(uuid.uuid4()),
    }


def _get_vm_pe_info(pe_base: str, vm_uuid: str) -> tuple[str | None, str | None]:
    """Return (power_state_lower_or_None, vmName_or_None) from GET v1/vms/{uuid}."""
    url = f"{pe_base}/PrismGateway/services/rest/v1/vms/{vm_uuid}"
    r = requests.get(url, headers=_headers(), auth=_AUTH, verify=False, timeout=120)
    if r.status_code != 200:
        log_print(f"WARN: GET vms/{vm_uuid[:8]}... HTTP {r.status_code}: {r.text[:200]!r}")
        return None, None
    try:
        body = json.loads(r.content)
    except (json.JSONDecodeError, TypeError):
        return None, None
    ps = str(body.get("powerState") or "").strip().lower() or None
    name = body.get("vmName") or body.get("vm_name")
    name_s = str(name).strip() if name else None
    return ps, name_s


def _set_power_transition(pe_base: str, vm_uuid: str, transition: str) -> bool:
    """transition: 'on' or 'off' (PE v2.0)."""
    url = f"{pe_base}/PrismGateway/services/rest/v2.0/vms/{vm_uuid}/set_power_state"
    r = requests.post(
        url,
        headers=_headers(),
        auth=_AUTH,
        verify=False,
        timeout=120,
        json={"transition": transition},
    )
    if r.status_code not in (200, 201, 202):
        log_print(
            f"ERROR: set_power_state {transition!r} for {vm_uuid[:8]}... "
            f"HTTP {r.status_code}: {r.text[:300]!r}"
        )
        return False
    return True


def _wait_power_state(
    pe_base: str, vm_uuid: str, want: str, *, attempts: int = 60, sleep_s: float = 2.0
) -> bool:
    """Wait until v1 vm powerState matches want ('on' or 'off')."""
    want_l = want.lower()
    for i in range(attempts):
        ps, _ = _get_vm_pe_info(pe_base, vm_uuid)
        if ps == want_l:
            return True
        log_print(
            f"INFO: wait power {want_l!r} for {vm_uuid[:8]}... (got {ps!r}, attempt {i + 1}/{attempts})"
        )
        time.sleep(sleep_s)
    return False


def _list_guest_vms_paginated(pe_base: str) -> list[dict]:
    """Return v1 /vms entities (each has uuid, vmName, powerState, ...)."""
    out: list[dict] = []
    page = 1
    while True:
        params = {
            "count": LIST_PAGE_SIZE,
            "page": page,
            "filterCriteria": GUEST_VM_FILTER,
        }
        url = f"{pe_base}/PrismGateway/services/rest/v1/vms"
        r = requests.get(url, headers=_headers(), auth=_AUTH, params=params, verify=False, timeout=180)
        if r.status_code != 200:
            log_print(f"ERROR: list vms page {page} → HTTP {r.status_code}: {r.text[:400]!r}")
            break
        try:
            body = json.loads(r.content)
        except json.JSONDecodeError:
            log_print(f"ERROR: list vms page {page}: invalid JSON")
            break
        entities = body.get("entities") or []
        if not entities:
            break
        out.extend(entities)
        meta = body.get("metadata") or {}
        total = int(meta.get("totalEntities") or meta.get("grandTotalEntities") or 0)
        end_idx = int(meta.get("endIndex") or 0)
        if total and end_idx + 1 >= total:
            break
        if len(entities) < LIST_PAGE_SIZE:
            break
        page += 1
    return out


def _parse_args() -> argparse.Namespace:
    default_action = (os.environ.get("PE_POWER_ACTION") or "on").strip().lower()
    if default_action not in ("on", "off", "toggle"):
        default_action = "on"
    p = argparse.ArgumentParser(
        description="Prism Element: power guest VMs on, off, or toggle (flip on/off)."
    )
    p.add_argument(
        "--pe-url",
        default=PE_BASE,
        help=f"PE base URL (default: env PE_URL or {PE_BASE!r})",
    )
    p.add_argument(
        "--action",
        choices=("on", "off", "toggle"),
        default=default_action,
        help="on: only off->on | off: only on->off | toggle: flip each VM. "
        "Default: env PE_POWER_ACTION or on.",
    )
    p.add_argument(
        "--vm-uuid",
        dest="vm_uuids",
        action="append",
        default=[],
        help="Restrict to this VM UUID (repeatable). If omitted, all guest VMs on PE are scanned.",
    )
    p.add_argument(
        "--parallel",
        type=int,
        default=POWER_PARALLEL,
        help=f"Max concurrent power ops (default env VM_PE_POWER_PARALLEL or {POWER_PARALLEL})",
    )
    return p.parse_args()


def _desired_transition_for_vm(action: str, current: str | None) -> str | None:
    cur = (current or "").strip().lower()
    if action == "on":
        return "on" if cur == "off" else None
    if action == "off":
        return "off" if cur == "on" else None
    if action == "toggle":
        if cur == "on":
            return "off"
        if cur == "off":
            return "on"
        return None
    return None


def _worker(pe_base: str, vm_uuid: str, vm_name: str, transition: str) -> tuple[str, str, bool]:
    ok_post = _set_power_transition(pe_base, vm_uuid, transition)
    if not ok_post:
        return vm_uuid, vm_name, False
    ok_wait = _wait_power_state(pe_base, vm_uuid, transition)
    return vm_uuid, vm_name, ok_wait


def _run(args: argparse.Namespace) -> None:
    pe_base = str(args.pe_url).rstrip("/")
    par = max(1, min(int(args.parallel or POWER_PARALLEL), 32))
    action = args.action

    log_print("=" * 72)
    log_print("vm_power_on_pe — Prism Element VM power")
    log_print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log_print(f"PE: {pe_base}")
    log_print(f"Action: {action}")
    log_print(f"Parallel: {par}")
    log_print("=" * 72)

    if args.vm_uuids:
        vms: list[tuple[str, str, str | None]] = []
        for u in args.vm_uuids:
            uid = (u or "").strip()
            if not uid:
                continue
            ps, vname = _get_vm_pe_info(pe_base, uid)
            label = vname or uid
            vms.append((uid, label, ps))
    else:
        log_print("Listing guest VMs (non-CVM)...")
        entities = _list_guest_vms_paginated(pe_base)
        vms = []
        for e in entities:
            uid = (e.get("uuid") or "").strip()
            if not uid:
                continue
            name = (e.get("vmName") or e.get("vm_name") or uid) or uid
            ps = (e.get("powerState") or "").strip().lower() or None
            vms.append((uid, str(name), ps))

    jobs: list[tuple[str, str, str]] = []
    skipped = 0
    for vm_uuid, vm_name, ps in vms:
        trans = _desired_transition_for_vm(action, ps)
        if trans is None:
            skipped += 1
            log_print(f"SKIP [{vm_name}] powerState={ps!r} (no change for action={action!r})")
            continue
        jobs.append((vm_uuid, vm_name, trans))

    log_print(f"Queued: {len(jobs)} VM(s); skipped: {skipped}")

    ok_c = fail_c = 0
    try:
        with ThreadPoolExecutor(max_workers=min(par, max(1, len(jobs)))) as pool:
            futures = {
                pool.submit(_worker, pe_base, ju, jn, jt): (ju, jn, jt)
                for ju, jn, jt in jobs
            }
            for fut in as_completed(futures):
                ju, jn, jt = futures[fut]
                try:
                    _, name, ok = fut.result()
                except Exception as ex:
                    ok = False
                    log_print(f"ERROR worker {jn}: {ex}")
                if ok:
                    ok_c += 1
                    log_print(f"OK [{name}] → {jt}")
                else:
                    fail_c += 1
                    log_print(f"FAIL [{name}] → {jt}")
    except KeyboardInterrupt:
        log_print("Interrupted.")

    log_print("=" * 72)
    log_print(f"Done. Succeeded: {ok_c}  Failed: {fail_c}  Skipped: {skipped}")
    log_print("=" * 72)
    _log_file.close()


if __name__ == "__main__":
    _run(_parse_args())
