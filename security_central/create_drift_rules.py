#!/usr/bin/env python3
"""Build one-condition drift queries from autocomplete, then create drift rules."""

import argparse
import base64
import json
import random
import re
import uuid
from pathlib import Path

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://ncm.services.nconprem-10-114-54-190.ccpnx.com/securitycentral"
AUTOCOMPLETE_URL = f"{BASE}/v2/drift/rule/autoComplete"
POLICY_URL = f"{BASE}/v2/drift/policy?policyTypes=CUSTOM"
CATEGORIES_URL = f"{BASE}/v2/drift/rule/categories?cloudProvider=NX"
RULE_URL = f"{BASE}/v2/drift/rule/"
QUERIES_FILE = Path(__file__).with_name("drift_rule_queries.json")

# How many drift rules to create from the query file.
RULES_TO_CREATE = 10000
# True reads drift_rule_queries.json. False calls autoComplete and rewrites that file.
USE_EXISTING_QUERIES = True
# "critical" is rejected by the API as a null severity.
SEVERITIES = ["low", "medium", "high"]

KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "NX", "(" , ")"}
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DATA_TYPES = {"boolean", "string", "long", "int", "integer", "double", "float", "date", "timestamp"}

client = requests.Session()
client.auth = HTTPBasicAuth("admin", "Nutanix.123")
client.headers = {"content-type": "application/json"}
client.verify = False


def b64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def suggestions(cursor):
    payload = {"queryTillCursor": b64(cursor), "query": b64(cursor)}
    response = client.post(AUTOCOMPLETE_URL, data=json.dumps(payload))
    response.raise_for_status()
    items = []
    for item in response.json().get("suggestion") or []:
        text = str(item.get("text") or "").strip()
        if text:
            items.append({"text": text, "type": str(item.get("type") or "")})
    return items


def quote_value(value):
    if re.fullmatch(r"-?\d+(\.\d+)?", value) or value.lower() in {"null", "true", "false"}:
        return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value
    return "'" + value.replace("'", "\\'") + "'"


def is_field(item):
    text = item["text"]
    if text.upper() in KEYWORDS or not IDENT_RE.match(text):
        return False
    if item["type"] in DATA_TYPES:
        return True
    return item["type"] == "" and text[:1].islower()


def is_related(item):
    text = item["text"]
    return item["type"] == "" and IDENT_RE.match(text) and text[:1].isupper() and text.upper() not in KEYWORDS


def where_targets(entity):
    targets = []
    for item in suggestions(f"From NX.{entity} WHERE "):
        if is_field(item):
            targets.append(item["text"])
        elif is_related(item):
            for field in suggestions(f"From NX.{entity} WHERE {item['text']}."):
                if is_field(field):
                    targets.append(f"{item['text']}.{field['text']}")
    return targets


def build_queries():
    queries = []
    for item in suggestions("From NX."):
        entity = item["text"]
        if not IDENT_RE.match(entity) or entity.upper() in KEYWORDS:
            continue
        for target in where_targets(entity):
            for op in suggestions(f"From NX.{entity} WHERE {target} "):
                if op["text"].upper() in KEYWORDS:
                    continue
                values = [
                    value["text"]
                    for value in suggestions(f"From NX.{entity} WHERE {target} {op['text']} ")
                    if value["text"].upper() not in KEYWORDS
                ]
                for value in values:
                    query = f"From NX.{entity} WHERE {target} {op['text']} {quote_value(value)}"
                    queries.append(query)
                    print(query)
    QUERIES_FILE.write_text(json.dumps(queries, indent=2) + "\n")
    print(f"wrote {len(queries)} queries to {QUERIES_FILE}")
    return queries


def list_policies():
    response = client.get(POLICY_URL)
    response.raise_for_status()
    return [item for item in response.json().get("items") or [] if item.get("id")]


def list_rule_domains():
    response = client.get(CATEGORIES_URL)
    response.raise_for_status()
    return [item["categoryName"] for item in response.json().get("items") or [] if item.get("categoryName")]


def create_rule(name, query, severity, category, policy_id):
    payload = {
        "name": name,
        "description": name,
        "severity": severity,
        "category": category,
        "policies": [policy_id],
        "definition": b64(query),
        "auditStatus": "DEPLOYED",
        "type": "CQL",
        "ruleType": "CUSTOM",
    }
    response = client.post(RULE_URL, data=json.dumps(payload))
    print(name, severity, category, policy_id, response.status_code, response.content)
    if response.ok:
        return True
    message = ""
    try:
        message = response.json().get("errorMessage") or ""
    except ValueError:
        message = response.text
    if "Severity cannot be null" in message and severity != "medium":
        print(f"{name} retrying with severity medium")
        return create_rule(name, query, "medium", category, policy_id)
    return False


def load_queries(use_existing):
    if use_existing:
        queries = json.loads(QUERIES_FILE.read_text())
        print(f"using {len(queries)} queries from {QUERIES_FILE}")
        return queries
    return build_queries()


parser = argparse.ArgumentParser()
parser.add_argument(
    "--fetch",
    action="store_true",
    help="call autoComplete and rewrite drift_rule_queries.json",
)
args = parser.parse_args()

queries = load_queries(USE_EXISTING_QUERIES and not args.fetch)
policies = list_policies()
domains = list_rule_domains()
if not policies or not domains:
    raise SystemExit(f"need policies ({len(policies)}) and rule domains ({len(domains)}) before creating rules")

created = 0
failed = 0
for query in queries:
    if created >= RULES_TO_CREATE:
        break
    name = f"rule_{created + 1}_{uuid.uuid4().hex[:8]}"
    if create_rule(name, query, random.choice(SEVERITIES), random.choice(domains), random.choice(policies)["id"]):
        created += 1
    else:
        failed += 1
print(f"created {created} drift rules, failed {failed}")
