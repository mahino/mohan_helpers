#!/usr/bin/env python3
"""
Compare all projects against a reference project and identify missing resources.

This script:
1. Loads a reference project (from del.json or from live project)
2. Gets all projects from PC
3. Compares each project's accounts, networks, and clusters against reference
4. Generates a report showing what's missing in each project
"""

import os
import sys
import json
import requests
import urllib3
from typing import Dict, List, Set, Tuple
from requests.auth import HTTPBasicAuth
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION - Hardcoded values
# ============================================================================
BASE_URL = "https://dm.services.nconprem-10-114-55-128.ccpnx.com/"
USERNAME = 'admin'
PASSWORD = 'Nutanix.123'

# Reference project source (choose one)
REFERENCE_FILE = '/home/mohan.as1/mohan_helpers/del.json'  # Path to reference project JSON file
REFERENCE_UUID = None  # Or set UUID to fetch from live PC: 'dbd4a6f8-244e-432f-b7a0-b013ec6e802c'

# Output settings
OUTPUT_FILE = 'project_comparison_report.json'
PROJECT_FILTER = None  # Set to filter projects by name, e.g., 'Nucalm_10'
# ============================================================================


class ProjectComparer:
    """Compare projects and identify missing resources"""
    
    def __init__(self, base_url: str, username: str = 'admin', password: str = 'Nutanix.123'):
        """Initialize the comparer"""
        # API URLs
        v3_path = 'api/nutanix/v3/'
        v4_multidomain_path = 'api/multidomain/v4.3.b1/config/'
        
        # Construct URLs similar to update_environments.py
        # Example: https://dm.services.HOST/ -> https://dm.services.HOST/api/nutanix/v3/
        self.pc_base_url = base_url + v3_path
        # Example: https://dm.services.HOST/ -> https://ncm.services.HOST/api/nutanix/v3/
        self.ncm_base_url = base_url.replace('dm', 'ncm') + v3_path
        # Example: https://dm.services.HOST/ -> https://projects.services.HOST/api/multidomain/v4.3.b1/config/
        self.v4_project_url = base_url.replace('dm', 'projects') + v4_multidomain_path
        
        self.client = requests.Session()
        self.client.auth = HTTPBasicAuth(username, password)
        self.client.headers = {'content-type': 'application/json'}
        self.client.verify = False
        
        self.reference_accounts = set()
        self.reference_networks = set()
        self.reference_clusters = set()
        self.reference_project_name = None
    
    def load_reference_from_json(self, filepath: str) -> bool:
        """
        Load reference project from JSON file
        
        Args:
            filepath: Path to reference project JSON file
            
        Returns:
            True if loaded successfully
        """
        if not os.path.exists(filepath):
            print(f"[ERROR] Reference file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                ref_project = json.load(f)
            
            # Get project name from spec.project_detail.name (not metadata.name)
            self.reference_project_name = ref_project['spec']['project_detail']['name']
            resources = ref_project['spec']['project_detail']['resources']
            
            # Extract account UUIDs
            for acc in resources.get('account_reference_list', []):
                self.reference_accounts.add(acc['uuid'])
            
            # Extract network UUIDs
            for net in resources.get('external_network_list', []):
                self.reference_networks.add(net['uuid'])
            
            # Extract cluster UUIDs
            for clust in resources.get('cluster_reference_list', []):
                self.reference_clusters.add(clust['uuid'])
            
            print(f"[INFO] Loaded reference project: {self.reference_project_name}")
            print(f"  - Accounts: {len(self.reference_accounts)}")
            print(f"  - Networks: {len(self.reference_networks)}")
            print(f"  - Clusters: {len(self.reference_clusters)}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load reference project: {e}")
            return False
    
    def load_reference_from_live(self, project_uuid: str) -> bool:
        """
        Load reference project from live PC
        
        Args:
            project_uuid: UUID of reference project
            
        Returns:
            True if loaded successfully
        """
        try:
            url = f"{self.pc_base_url}projects_internal/{project_uuid}"
            resp = self.client.get(url)
            resp.raise_for_status()
            
            ref_project = resp.json()
            # Get project name from spec.project_detail.name
            self.reference_project_name = ref_project['spec']['project_detail']['name']
            resources = ref_project['spec']['project_detail']['resources']
            
            # Extract UUIDs
            for acc in resources.get('account_reference_list', []):
                self.reference_accounts.add(acc['uuid'])
            
            for net in resources.get('external_network_list', []):
                self.reference_networks.add(net['uuid'])
            
            for clust in resources.get('cluster_reference_list', []):
                self.reference_clusters.add(clust['uuid'])
            
            print(f"[INFO] Loaded reference project: {self.reference_project_name}")
            print(f"  - Accounts: {len(self.reference_accounts)}")
            print(f"  - Networks: {len(self.reference_networks)}")
            print(f"  - Clusters: {len(self.reference_clusters)}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load reference project: {e}")
            return False
    
    def get_projects_v4(self, page=1, limit=50):
        """Get list of projects using v4 multidomain API (from update_environments.py)"""
        filter_str = quote("(isSystemDefined ne true and isDefault ne true)")
        url = f"{self.v4_project_url}projects?$filter={filter_str}&$limit={limit}&$orderby=name asc&$page={page}"
        
        print(f"[INFO] Fetching projects from v4 API (page {page})...")
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            projects = data.get('data', [])
            print(f"[INFO] Found {len(projects)} project(s) on page {page}")
            return projects
        except Exception as e:
            print(f"[ERROR] Failed to get projects: {e}")
            return []

    def get_all_projects(self):
        """Get all projects across multiple pages (from update_environments.py)"""
        all_projects = []
        page = 0
        limit = 100
        
        while True:
            projects = self.get_projects_v4(page=page, limit=limit)
            if not projects:
                break
            all_projects.extend(projects)
            
            if len(projects) < limit:
                break
            page += 1
        
        print(f"[INFO] Total projects fetched: {len(all_projects)}")
        return all_projects
    
    def get_project_details(self, project_uuid: str) -> Dict:
        """
        Get detailed project configuration
        
        Args:
            project_uuid: Project UUID
            
        Returns:
            Project spec dict or None
        """
        try:
            url = f"{self.pc_base_url}projects_internal/{project_uuid}"
            resp = self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[ERROR] Failed to get project {project_uuid}: {e}")
            return None
    
    def compare_project(self, project: Dict) -> Dict[str, List[str]]:
        """
        Compare a project against reference and find missing resources
        
        Args:
            project: Project spec dict
            
        Returns:
            Dict with missing_accounts, missing_networks, missing_clusters
        """
        resources = project['spec']['project_detail']['resources']
        
        # Get current project's resources
        current_accounts = {acc['uuid'] for acc in resources.get('account_reference_list', [])}
        current_networks = {net['uuid'] for net in resources.get('external_network_list', [])}
        current_clusters = {clust['uuid'] for clust in resources.get('cluster_reference_list', [])}
        
        # Find missing resources
        missing = {
            'missing_accounts': list(self.reference_accounts - current_accounts),
            'missing_networks': list(self.reference_networks - current_networks),
            'missing_clusters': list(self.reference_clusters - current_clusters)
        }
        
        return missing
    
    def generate_report(self, output_file: str = 'project_comparison_report.json',
                       project_filter: str = None):
        """
        Generate comparison report for all projects
        
        Args:
            output_file: Output file path
            project_filter: Optional name filter
        """
        print("\n" + "="*80)
        print("PROJECT COMPARISON REPORT")
        print("="*80)
        print(f"Reference Project: {self.reference_project_name}")
        print(f"Reference Resources:")
        print(f"  - Accounts: {len(self.reference_accounts)}")
        print(f"  - Networks: {len(self.reference_networks)}")
        print(f"  - Clusters: {len(self.reference_clusters)}")
        print("="*80)
        
        # Get all projects using v4 API (same as update_environments.py)
        projects = self.get_all_projects()
        
        if not projects:
            print("[ERROR] No projects found")
            return
        
        # Apply filter if specified
        if project_filter:
            projects = [p for p in projects if project_filter.lower() in p.get('name', '').lower()]
            print(f"[INFO] Filtered to {len(projects)} project(s) matching '{project_filter}'")
        
        # Compare each project
        report = {
            'reference_project': {
                'name': self.reference_project_name,
                'accounts': list(self.reference_accounts),
                'networks': list(self.reference_networks),
                'clusters': list(self.reference_clusters)
            },
            'projects': [],
            'summary': {
                'total_projects': 0,
                'projects_missing_resources': 0,
                'projects_complete': 0
            }
        }
        
        print(f"\n[INFO] Comparing {len(projects)} project(s)...\n")
        
        for idx, proj_summary in enumerate(projects, 1):
            # Extract project info from v4 API response
            project_name = proj_summary.get('name', 'Unknown')
            project_uuid = proj_summary.get('extId')
            
            print(f"[{idx}/{len(projects)}] Checking: {project_name}")
            
            # Get project details
            project = self.get_project_details(project_uuid)
            if not project:
                continue
            
            # Compare against reference
            missing = self.compare_project(project)
            
            has_missing = (len(missing['missing_accounts']) > 0 or 
                          len(missing['missing_networks']) > 0 or 
                          len(missing['missing_clusters']) > 0)
            
            project_report = {
                'name': project_name,
                'uuid': project_uuid,
                'missing_accounts': missing['missing_accounts'],
                'missing_networks': missing['missing_networks'],
                'missing_clusters': missing['missing_clusters'],
                'missing_accounts_count': len(missing['missing_accounts']),
                'missing_networks_count': len(missing['missing_networks']),
                'missing_clusters_count': len(missing['missing_clusters'])
            }
            
            report['projects'].append(project_report)
            report['summary']['total_projects'] += 1
            
            if has_missing:
                report['summary']['projects_missing_resources'] += 1
                print(f"  ❌ Missing: {len(missing['missing_accounts'])} accounts, "
                      f"{len(missing['missing_networks'])} networks, "
                      f"{len(missing['missing_clusters'])} clusters")
            else:
                report['summary']['projects_complete'] += 1
                print(f"  ✅ Complete (all resources present)")
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total projects checked:        {report['summary']['total_projects']}")
        print(f"Projects missing resources:    {report['summary']['projects_missing_resources']}")
        print(f"Projects complete:             {report['summary']['projects_complete']}")
        print("="*80)
        print(f"\nDetailed report saved to: {output_file}")
        
        # Print missing resources summary
        self.print_missing_summary(report)
    
    def print_missing_summary(self, report: Dict):
        """Print a summary of which projects are missing what"""
        print("\n" + "="*80)
        print("PROJECTS WITH MISSING RESOURCES")
        print("="*80)
        
        for proj in report['projects']:
            if (proj['missing_accounts_count'] > 0 or 
                proj['missing_networks_count'] > 0 or 
                proj['missing_clusters_count'] > 0):
                
                print(f"\nProject: {proj['name']}")
                print(f"  UUID: {proj['uuid']}")
                
                if proj['missing_accounts_count'] > 0:
                    print(f"  Missing Accounts ({proj['missing_accounts_count']}):")
                    for acc_uuid in proj['missing_accounts'][:5]:  # Show first 5
                        print(f"    - {acc_uuid}")
                    if proj['missing_accounts_count'] > 5:
                        print(f"    ... and {proj['missing_accounts_count'] - 5} more")
                
                if proj['missing_networks_count'] > 0:
                    print(f"  Missing Networks ({proj['missing_networks_count']}):")
                    for net_uuid in proj['missing_networks'][:5]:  # Show first 5
                        print(f"    - {net_uuid}")
                    if proj['missing_networks_count'] > 5:
                        print(f"    ... and {proj['missing_networks_count'] - 5} more")
                
                if proj['missing_clusters_count'] > 0:
                    print(f"  Missing Clusters ({proj['missing_clusters_count']}):")
                    for clust_uuid in proj['missing_clusters'][:5]:  # Show first 5
                        print(f"    - {clust_uuid}")
                    if proj['missing_clusters_count'] > 5:
                        print(f"    ... and {proj['missing_clusters_count'] - 5} more")


def main():
    print("="*80)
    print("CONFIGURATION")
    print("="*80)
    print(f"Base URL:          {BASE_URL}")
    print(f"Username:          {USERNAME}")
    print(f"Reference File:    {REFERENCE_FILE}")
    print(f"Reference UUID:    {REFERENCE_UUID}")
    print(f"Output File:       {OUTPUT_FILE}")
    print(f"Project Filter:    {PROJECT_FILTER}")
    print("="*80)
    print()
    
    # Create comparer
    comparer = ProjectComparer(
        base_url=BASE_URL,
        username=USERNAME,
        password=PASSWORD
    )
    
    # Load reference project
    if REFERENCE_FILE:
        if not comparer.load_reference_from_json(REFERENCE_FILE):
            return 1
    elif REFERENCE_UUID:
        if not comparer.load_reference_from_live(REFERENCE_UUID):
            return 1
    else:
        print("[ERROR] Either REFERENCE_FILE or REFERENCE_UUID must be set in configuration")
        return 1
    
    # Generate report
    comparer.generate_report(
        output_file=OUTPUT_FILE,
        project_filter=PROJECT_FILTER
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
