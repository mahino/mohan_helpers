#!/usr/bin/env python3
"""Call investigate autocomplete live and write every query the suggestions allow."""

import argparse
import base64
import json
import re
import time
from pathlib import Path

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://ncm.services.nconprem-10-114-54-190.ccpnx.com/securitycentral"

client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False
KEYWORDS = {
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "LIMIT", "ORDER", "BY",
    "GROUP", "ASC", "DESC", "IN", "LIKE", "AS", "NX", "AWS", "AZURE", "GCP",
}
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def b64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class AutoComplete:
    def __init__(self, dataset, pause=0.05):
        self.dataset = dataset
        self.pause = pause
        self.cache = {}
        self.calls = 0
        self.url = (
            f"{BASE}/v2/drift/rule/autoComplete"
            f"?dataset={dataset}&feature=INVESTIGATE"
        )

    def tokens(self, cursor):
        if cursor in self.cache:
            return self.cache[cursor]
        payload = {"queryTillCursor": b64(cursor), "query": b64(cursor)}
        response = client.post(self.url, data=json.dumps(payload))
        response.raise_for_status()
        body = response.json()
        texts = []
        for item in body.get("suggestion") or []:
            text = str(item.get("text") or "").strip()
            if text:
                texts.append(text)
        self.cache[cursor] = texts
        self.calls += 1
        time.sleep(self.pause)
        return texts


def entity_name(token):
    if "." in token:
        return token
    if IDENT_RE.match(token) and token.upper() not in KEYWORDS:
        return "NX." + token
    return ""


def append_query(output, dataset, query):
    with output.open("a") as handle:
        handle.write(json.dumps({"dataset": dataset, "query": query}) + "\n")
        handle.flush()
    print(query)


def queries_for_dataset(dataset, pause, output):
    api = AutoComplete(dataset, pause)
    count = 0
    for token in api.tokens("SELECT NX."):
        entity = entity_name(token)
        if not entity:
            continue
        for field in api.tokens(f"SELECT {entity}."):
            if field != "*" and not (IDENT_RE.match(field) and field.upper() not in KEYWORDS):
                continue
            query = f"SELECT {entity}.{field} FROM {entity}"
            append_query(output, dataset, query)
            count += 1
    return count, api.calls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", action="append",
        default=["INVENTORY_AND_CONFIGURATION", "NETWORK_LOGS"],
    )
    parser.add_argument("-o", "--output", type=Path, default=Path("autocomplete_queries.json"))
    parser.add_argument("--pause", type=float, default=0.05)
    args = parser.parse_args()

    args.output.write_text("")
    total = 0
    for dataset in args.dataset:
        count, calls = queries_for_dataset(dataset, args.pause, args.output)
        print(f"{dataset}: {calls} live calls, {count} queries")
        total += count
    print(f"wrote {total} queries to {args.output}")


if __name__ == "__main__":
    main()