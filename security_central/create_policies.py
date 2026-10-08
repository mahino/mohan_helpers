#!/usr/bin/env python3
"""List deployed drift audits, then create policies from a random subset."""

import json
import random
import uuid
from pathlib import Path

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://ncm.services.nconprem-10-114-54-190.ccpnx.com/securitycentral"
AUDITS_URL = f"{BASE}/v2/drift/rule/filtered?offset=0&limit=1500"
POLICY_URL = f"{BASE}/v2/drift/policy"
AUDITS_FILE = Path(__file__).with_name("audits_list.json")
NCM_PROJECT_ID = "00000000-0000-0000-0000-000000000000"

# How many audits to attach to each policy, and how many policies to create.
AUDITS_PER_POLICY = 100
POLICIES_TO_CREATE = 100

client = requests.Session()
client.auth = HTTPBasicAuth("admin", "Nutanix.123")
client.headers = {"content-type": "application/json"}
client.verify = False


def list_audits():
    response = client.post(AUDITS_URL, data=json.dumps({"status": "DEPLOYED"}))
    response.raise_for_status()
    audits = response.json()
    AUDITS_FILE.write_text(json.dumps(audits, indent=2) + "\n")
    print(f"stored {audits.get('count', len(audits.get('items', [])))} audits in {AUDITS_FILE}")
    return audits


def create_policy(name, audit_ids):
    payload = {
        "name": name,
        "description": name,
        "auditIds": audit_ids,
        "policyType": "CUSTOM",
        "ncmProjectIds": [NCM_PROJECT_ID],
    }
    response = client.post(POLICY_URL, data=json.dumps(payload))
    print(name, response.status_code, response.content)
    response.raise_for_status()
    return response.json()


audits = list_audits()
audit_ids = [item["id"] for item in audits.get("items", []) if item.get("id")]
sample_size = min(AUDITS_PER_POLICY, len(audit_ids))

for index in range(1, POLICIES_TO_CREATE + 1):
    chosen = random.sample(audit_ids, sample_size)
    policy_name = f"policy_{index}_{uuid.uuid4().hex[:8]}"
    create_policy(policy_name, chosen)
