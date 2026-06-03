#!/bin/bash

echo "=========================================="
echo "                PC VERSION                "
echo "=========================================="
ncli cluster info

echo ""
echo "=========================================="
echo "              NC/NCM VERSIONS             "
echo "=========================================="

curl -X GET 'https://localhost:9440/api/lifecycle/v4.0/svcmgr/applications?$limit=100' \
  -u 'admin:Nutanix.123' -k -s \
  | python3 -c "
import sys, json

NCM_VERSION_KEY = 'initContainers.ncmReleaseConfig.version'


def find_ncm_release_config_version(node):
    '''
    Walk the response recursively and return the value of the first
    CustomValueItem with key == NCM_VERSION_KEY.
    '''
    if isinstance(node, dict):
        if node.get('key') == NCM_VERSION_KEY and 'value' in node:
            return node.get('value')
        if (node.get('\$objectType', '').endswith('CustomValueItem')
                and node.get('key') == NCM_VERSION_KEY):
            return node.get('value')
        for v in node.values():
            found = find_ncm_release_config_version(v)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = find_ncm_release_config_version(item)
            if found is not None:
                return found
    return None


try:
    raw = json.load(sys.stdin)
    data = raw.get('data', []) if isinstance(raw, dict) else []
    versions = {}

    for app in data:
        if app.get('name') == 'nutanix-central':
            versions[app['name']] = app.get('version')
        for service in app.get('subServices', []) or []:
            if service.get('name') == 'nutanix-central':
                versions[service['name']] = service.get('version')

    ncm_release_config_version = find_ncm_release_config_version(raw)

    print(f'nutanix-central:                       '
          f'{versions.get(\"nutanix-central\", \"Not Found\")}')
    print(f'ncmReleaseConfig.version (NCM):        '
          f'{ncm_release_config_version if ncm_release_config_version is not None else \"Not Found\"}')

except Exception as e:
    print(f'Error parsing JSON: {e}', file=sys.stderr)
"

echo ""
echo "=========================================="
echo "          COMMIT IDs FROM NCM              "
echo "=========================================="

mspctl cls ssh nc 2>&1 <<'EOF' | grep -v "^=" | grep -v "Pseudo-terminal" | grep -v "WARNING" | grep -v "NASTY" | grep -v "eavesdropping" | grep -v "host key" | grep -v "fingerprint" | grep -v "system administrator" | grep -v "known_hosts" | grep -v "Offending" | grep -v "Password authentication" | grep -v "Keyboard-interactive" | grep -v "sign_and_send_pubkey" | grep -v "^@"

echo ""
echo "--- Calm Commit IDs ---"
kubectl exec -n ntnx-ncm-self-service ncm-calm-0 -- cat /home/calm/conf/commit_ids.txt 2>/dev/null || echo "Failed to read Calm commit_ids.txt"

echo ""
echo "--- Epsilon Commit IDs ---"
kubectl exec -n ntnx-ncm-common ncm-epsilon-0 -- cat /home/epsilon/conf/commit_ids.txt 2>/dev/null || echo "Failed to read Epsilon commit_ids.txt"

echo ""
echo "--- Domain Manager Commit IDs ---"
kubectl exec -n domain-manager domain-manager-0 -- cat /home/calm/conf/commit_ids.txt 2>/dev/null || echo "Failed to read Domain Manager commit_ids.txt"

EOF
