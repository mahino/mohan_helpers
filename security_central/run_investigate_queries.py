#!/usr/bin/env python3
"""Post the autocomplete query list to the investigate save API."""

import base64
import json
import uuid
from collections import Counter
from pathlib import Path

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

QUERY_LIST = Path(__file__).with_name("autocomplete_queries.json")
URL = "https://ncm.services.nconprem-10-114-54-190.ccpnx.com/securitycentral/v2/investigate"

client = requests.Session()
client.auth = HTTPBasicAuth("admin", "Nutanix.123")
client.headers = {"content-type": "application/json"}
client.verify = False


def load_queries(path):
    text = path.read_text().strip()
    if text.endswith(","):
        text = text[:-1]
    text = text.replace("},\n]", "}\n]")
    return json.loads(text)


queries = load_queries(QUERY_LIST)
success = 0
failed = Counter()

for item in queries:
    payload = {
        "name": item["dataset"] + "_" + str(uuid.uuid4())[:8],
        "description": item["query"],
        "definition": base64.b64encode(item["query"].encode("utf-8")).decode("utf-8"),
        "dataset": item["dataset"],
    }
    print(json.dumps(payload))
    response = client.post(URL, data=json.dumps(payload))
    print(response.content)
    try:
        body = response.json()
    except ValueError:
        body = {}
    if isinstance(body, dict) and body.get("errorMessage"):
        failed[body["errorMessage"]] += 1
    elif not response.ok:
        failed[response.reason or f"HTTP {response.status_code}"] += 1
    else:
        success += 1

print(json.dumps({"success": success, "failed": dict(failed)}, indent=2))
