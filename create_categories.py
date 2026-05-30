#!/usr/bin/env python3
"""
Create categories in Prism Central using v4 API

Usage:
    python3 create_categories.py <pc_ip_or_fqdn>
    
Example:
    python3 create_categories.py 10.122.28.170
    python3 create_categories.py pc-10-114-55-127-domain.domains.nconprem-10-114-55-128.ccpnx.com

Configuration:
    - Edit categories_config list below to define key-value pairs
    - Set CREATE_SHARED=True to create categories shared with all projects
    - Set CREATE_SHARED=False to create per-project categories
    - Edit username/password in HTTPBasicAuth if needed
"""

import sys
import json
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if len(sys.argv) < 2:
    print("Usage: python3 create_categories.py <pc_ip_or_fqdn>")
    print("\nExample:")
    print("  python3 create_categories.py 10.122.28.170")
    sys.exit(1)

BASE_URL = f"https://{sys.argv[1]}:9440/"
client = requests.Session()
client.auth = HTTPBasicAuth('admin', 'Nutanix.123')
client.headers = {'content-type': 'application/json'}
client.verify = False

################################################################################
# CONFIGURATION - Edit these values as needed
################################################################################

# Define categories to create (key-value pairs)
# Each category will be created for all projects (if CREATE_SHARED=False)
# or as a shared category (if CREATE_SHARED=True)
categories_config = [
    {"key": "Environment", "value": "Production"},
    {"key": "Environment", "value": "Development"},
    {"key": "Environment", "value": "Testing"},
    {"key": "AppType", "value": "Database"},
    {"key": "AppType", "value": "WebServer"},
    {"key": "AppType", "value": "AppServer"},
    {"key": "Owner", "value": "TeamA"},
    {"key": "Owner", "value": "TeamB"},
]

# CREATE_SHARED: 
#   True  = Create categories shared with all projects (ignore per-project creation)
#   False = Create separate category instances for each project
CREATE_SHARED = False

# If you want to create for specific projects only, uncomment and edit:
# SPECIFIC_PROJECTS = ["000584bf-e316-4965-8892-62e879f560ee"]  # List of project extIds
# Otherwise, all non-system projects will be used

################################################################################

project_ext_ids = []  # Will be fetched from PC

print("="*80)
print(f"Fetching projects from {BASE_URL}")

# Fetch projects using v4 API
projects_url = BASE_URL + "api/multidomain/v4.3.b1/config/projects?$limit=100"
try:
    resp = client.get(projects_url)
    if resp.status_code == 200:
        projects_data = json.loads(resp.content)
        projects = projects_data.get('data', [])
        # Filter out system/internal projects
        user_projects = [p for p in projects if not p.get('isSystemDefined', False)]
        print(f"Found {len(user_projects)} user projects")
        
        # Check if specific projects were requested
        if 'SPECIFIC_PROJECTS' in globals():
            project_ext_ids = SPECIFIC_PROJECTS
            print(f"Using {len(project_ext_ids)} specific project(s) from config")
        else:
            project_ext_ids = [p['extId'] for p in user_projects]
        
        for p in user_projects:
            if p['extId'] in project_ext_ids:
                print(f"  ✓ {p['name']} ({p['extId']})")
            else:
                print(f"    {p['name']} ({p['extId']}) [skipped]")
    else:
        print(f"ERROR: Failed to fetch projects. Status: {resp.status_code}")
        print(resp.content)
        if not CREATE_SHARED:
            sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to fetch projects: {e}")
    if not CREATE_SHARED:
        sys.exit(1)

print("="*80)

# Create categories
categories_url = BASE_URL + "api/prism/v4.3/config/categories"

created_count = 0
failed_count = 0

for category in categories_config:
    key = category['key']
    value = category['value']
    
    if CREATE_SHARED:
        # Create shared category (available to all projects)
        print(f"\nCreating shared category: {key}={value}")
        payload = {
            "$objectType": "prism.v4.config.Category",
            "$reserved": {"$fv": "v4.r3"},
            "$unknownFields": {},
            "key": key,
            "value": value,
            "description": f"Category: {key} with value: {value}",
            "isSharedWithAllProjects": True,
            "type": "USER"
        }
        
        try:
            resp = client.post(categories_url, data=json.dumps(payload))
            if resp.status_code in [200, 201]:
                created_count += 1
                response_data = json.loads(resp.content)
                ext_id = response_data.get('data', {}).get('extId', 'unknown')
                print(f"  ✓ Created: {key}={value} (extId: {ext_id})")
            else:
                failed_count += 1
                print(f"  ✗ Failed: {resp.status_code}")
                print(f"  Response: {resp.content.decode('utf-8')[:200]}")
        except Exception as e:
            failed_count += 1
            print(f"  ✗ Exception: {e}")
    
    else:
        # Create category for each project
        for project_id in project_ext_ids:
            print(f"\nCreating category for project {project_id}: {key}={value}")
            payload = {
                "$objectType": "prism.v4.config.Category",
                "$reserved": {"$fv": "v4.r3"},
                "$unknownFields": {},
                "key": key,
                "value": value,
                "description": f"Category: {key} with value: {value}",
                "projectExtId": project_id,
                "isSharedWithAllProjects": False,
                "type": "USER"
            }
            
            try:
                resp = client.post(categories_url, data=json.dumps(payload))
                if resp.status_code in [200, 201]:
                    created_count += 1
                    response_data = json.loads(resp.content)
                    ext_id = response_data.get('data', {}).get('extId', 'unknown')
                    print(f"  ✓ Created: {key}={value} (extId: {ext_id})")
                else:
                    failed_count += 1
                    print(f"  ✗ Failed: {resp.status_code}")
                    error_msg = resp.content.decode('utf-8')[:200]
                    print(f"  Response: {error_msg}")
            except Exception as e:
                failed_count += 1
                print(f"  ✗ Exception: {e}")

print("\n" + "="*80)
print(f"Summary: {created_count} created, {failed_count} failed")
print("="*80)
