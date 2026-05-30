#!/usr/bin/env python3
"""
Enhanced script to analyze logs - runs DIRECTLY on the machine (no Docker exec for styx).

CHANGES FROM V1:
    1. Direct path access for styx logs: /home/docker/nucalm/log/ (no docker exec)
    2. Handles both regular and .xz compressed files using xzgrep
    3. Maps APP-CREATE-START with corresponding APP-CREATE-END
    4. Extracts application name from APP-CREATE-END
    5. Finds next application after first one and gets its RR UUID
    6. Direct path access for durga logs: /home/docker/epsilon/log/ (no docker exec)
    7. Searches context UUID in indra_* files
    8. Extracts smsp_app_uuid from indra logs

USAGE (on the machine itself):
    # Standard usage with default log paths:
    python3 analyze_styx_logs_local_v2.py --api-host <API_HOST>
    
    # Usage with central directory (all log files in one location):
    python3 analyze_styx_logs_local_v2.py --api-host <API_HOST> --central-dir <CENTRAL_DIR>
    
    Examples:
    # Default paths (logs in their original locations):
    python3 analyze_styx_logs_local_v2.py --api-host 10.122.27.232
    
    # Central directory (all logs copied to one location):
    python3 analyze_styx_logs_local_v2.py --api-host 10.122.27.232 --central-dir /tmp/all_logs
    
    Note: When using --central-dir, copy all log files (styx.log*, durga_*, indra_*, 
          svcmgr pod logs, msp_controller.out*) to the central directory. The script
          will search for these files using their original patterns in the central directory.

CONFIGURATION:
    Edit paths at the top if needed
"""

import subprocess
import re
from datetime import datetime
from pathlib import Path
import sys
import json
import base64
import argparse
try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================
# All paths, patterns, and search strings are configurable here.
# Modify these values if your log locations or patterns differ.
#
# CENTRAL DIRECTORY OPTION:
# Instead of modifying paths here, you can use --central-dir command-line argument
# to specify a single directory containing all log files. When --central-dir is used,
# all log searches will use that directory instead of the individual paths below.
# This is useful when you copy all log files to one location for analysis.
# The core logic remains unchanged - only the paths are overridden.

# STYX Log Configuration
# STYX logs contain APP-CREATE-START and APP-CREATE-END entries
STYX_LOG_PATH = "/home/docker/nucalm/log"  # Direct path to styx logs (no docker exec needed)
STYX_LOG_PATTERN = "styx.log*"  # Pattern to match all styx log files (handles rotated logs)

# DURGA Log Configuration
# DURGA logs contain TRLID entries that link RR UUID to context UUID
DURGA_LOG_PATH = "/home/docker/epsilon/log"  # Direct path to durga logs (no docker exec needed)
DURGA_LOG_PATTERN = "durga_*"  # Pattern to match all durga log files
DURGA_SEARCH_STRING = "TRLID"  # String to search for in durga logs to find TRLID entries

# INDRA Log Configuration
# INDRA logs contain context UUID and smsp_app_uuid information
INDRA_LOG_PATH = "/home/docker/epsilon/log"  # Direct path to indra logs (no docker exec needed)
INDRA_LOG_PATTERN = "indra_*"  # Pattern to match all indra log files

# Service Manager Pod Log Configuration
# These logs contain task execution details
SVC_MGR_POD_LOG_PATH = "/home/nutanix/data/sys-storage/msp_partition/kubelet/pod_logs"  # Path for svcmgr pod logs
SVC_MGR_POD_LOG_PATTERN = "*svcmgr*"  # Pattern for svcmgr pod log files

# MSP Controller Log Configuration
# These logs contain mspUuid information for troubleshooting
MSP_CONTROLLER_LOG_PATH = "/home/nutanix/data/logs"  # Path for msp_controller logs
MSP_CONTROLLER_LOG_PATTERN = "msp_controller.out*"  # Pattern for msp_controller log files

# API Configuration
# Used for calling Service Manager APIs to get task and application details
API_USERNAME = "admin"  # Default username for API authentication
API_PASSWORD = "Nutanix.123"  # Default password for API authentication
API_PORT = 9440  # Default port for API calls

# ============================================================================
# REGEX PATTERNS FOR PARSING LOG ENTRIES
# ============================================================================
# These patterns extract specific information from log lines.
# All patterns are dynamic and based on actual log format.

UUID_PATTERN = r'==>([a-f0-9-]+)'  # Pattern to extract UUID after search string (e.g., APP-CREATE-START==>uuid)
TIMESTAMP_PATTERN = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+Z)\]'  # Pattern to extract timestamp from log lines
RR_PATTERN = r'\[rr:([a-f0-9-]+)\]'  # Pattern to extract RR UUID from log lines
END_PATTERN = r"APP-CREATE-END==>b'([a-f0-9-]+)::([^']+)'"  # Pattern to extract UUID and app name from APP-CREATE-END

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_cmd(cmd):
    """
    Simple command runner that executes shell commands.
    
    Args:
        cmd: Shell command string to execute
        
    Returns:
        Stripped stdout output from the command
        
    Note:
        Uses timeout of 600 seconds to prevent hanging on large log searches
    """
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    return result.stdout.strip()

def grep_with_xz(pattern, file_pattern, path):
    """
    Search for a pattern in both regular and .xz compressed log files.
    
    This function handles log rotation where older logs are compressed.
    It searches in both uncompressed and compressed files to ensure we don't miss data.
    
    Args:
        pattern: The search pattern (e.g., UUID, string to find)
        file_pattern: File pattern to match (e.g., "styx.log*", "durga_*")
        path: Directory path where logs are located
        
    Returns:
        Combined output from both regular and compressed file searches
        
    Logic:
        1. Search in regular (uncompressed) files using grep -r
           - Excludes .xz files to avoid double-processing
        2. Search in .xz compressed files using find + xzgrep
           - Finds all files matching pattern that end with .xz
        3. Combine both results
    """
    # Step 1: Grep in regular (uncompressed) files
    # Uses recursive grep to search all matching files
    # Filter out .xz files from results to avoid processing compressed files with regular grep
    # This handles: styx.log, styx.log.1, durga_0.log, etc. (but not .xz files)
    cmd1 = f"cd {path} && grep -r {pattern} {file_pattern} 2>/dev/null | grep -v '\\.xz:' 2>/dev/null || true"
    
    # Step 2: Grep in .xz compressed files
    # Find all files matching the pattern that end with .xz
    # Then use xzgrep to search within those compressed files
    # Examples:
    #   - file_pattern "styx.log*" -> finds "styx.log.1.xz", "styx.log.2.xz", etc.
    #   - file_pattern "durga_*" -> finds "durga_0.log.1.xz", "durga_1.log.2.xz", etc.
    base_pattern = file_pattern.rstrip('*')  # Remove trailing * if present
    if file_pattern.endswith('*'):
        # Pattern like "styx.log*" -> find files like "styx.log*.xz"
        # This matches: styx.log.1.xz, styx.log.2.xz, styx.log.3.20251110.xz, etc.
        cmd2 = f"cd {path} && find . -type f -name '{base_pattern}*.xz' -exec xzgrep -H {pattern} {{}} \\; 2>/dev/null"
    else:
        # Pattern without * -> just append .xz
        # This matches exact filename with .xz extension
        cmd2 = f"cd {path} && find . -type f -name '{file_pattern}.xz' -exec xzgrep -H {pattern} {{}} \\; 2>/dev/null"
    
    # Step 3: Combine both outputs
    output1 = run_cmd(cmd1)  # Results from regular (uncompressed) files
    output2 = run_cmd(cmd2)  # Results from compressed (.xz) files
    combined = output1 + "\n" + output2 if output2 else output1
    return combined.strip()

def grep_with_xz_context(pattern, file_pattern, path, context_lines=5):
    """
    Search for a pattern with context lines (for finding lines after match).
    
    This is useful when we need to see what comes after a match (e.g., finding
    task UUID after smsp_app_uuid in indra logs).
    
    Args:
        pattern: The search pattern to find
        file_pattern: File pattern to match
        path: Directory path where logs are located
        context_lines: Number of lines to show after the match (default: 5)
        
    Returns:
        Combined output with context lines from both regular and compressed files
        
    Logic:
        Similar to grep_with_xz but includes -A flag for context lines
        1. Search in regular (uncompressed) files with context
        2. Search in .xz compressed files with context
        3. Combine both results
    """
    # Step 1: Grep in regular (uncompressed) files with context (shows lines after match)
    # Filter out .xz files from results to avoid processing compressed files with regular grep
    # This handles: styx.log, styx.log.1, durga_0.log, etc. (but not .xz files)
    cmd1 = f"cd {path} && grep -r -A {context_lines} {pattern} {file_pattern} 2>/dev/null | grep -v '\\.xz:' 2>/dev/null || true"
    
    # Step 2: Grep in .xz compressed files with context
    # Find all files matching the pattern that end with .xz
    # Then use xzgrep with -A flag to get context lines
    # Examples:
    #   - file_pattern "styx.log*" -> finds "styx.log.1.xz", "styx.log.2.xz", etc.
    #   - file_pattern "durga_*" -> finds "durga_0.log.1.xz", "durga_1.log.2.xz", etc.
    base_pattern = file_pattern.rstrip('*')  # Remove trailing * if present
    if file_pattern.endswith('*'):
        # Pattern like "styx.log*" -> find files like "styx.log*.xz"
        # This matches: styx.log.1.xz, styx.log.2.xz, styx.log.3.20251110.xz, etc.
        cmd2 = f"cd {path} && find . -type f -name '{base_pattern}*.xz' -exec sh -c 'xzgrep -A {context_lines} {pattern} \"$1\"' _ {{}} \\; 2>/dev/null"
    else:
        # Pattern without * -> just append .xz
        # This matches exact filename with .xz extension
        cmd2 = f"cd {path} && find . -type f -name '{file_pattern}.xz' -exec sh -c 'xzgrep -A {context_lines} {pattern} \"$1\"' _ {{}} \\; 2>/dev/null"
    
    # Step 3: Combine both outputs
    output1 = run_cmd(cmd1)  # Results from regular (uncompressed) files
    output2 = run_cmd(cmd2)  # Results from compressed (.xz) files
    combined = output1 + "\n" + output2 if output2 else output1
    return combined.strip()

def call_svcmgr_api(api_host, task_uuid, auth_header):
    """
    Call Service Manager API to get task details.
    
    This function retrieves task information including status, subtasks, and error messages.
    Used to get detailed information about parent and subtask execution.
    
    Args:
        api_host: API hostname or IP address
        task_uuid: UUID of the task to query
        auth_header: Authorization header (Basic auth)
        
    Returns:
        Tuple of (response_json, error_message)
        - If successful: (json_data, None)
        - If failed: (None, error_string)
        
    API Endpoint:
        GET /api/lifecycle/v4.1/svcmgr/tasks/{task_uuid}
    """
    if not REQUESTS_AVAILABLE:
        return None, "requests module not available"
    
    # Construct API URL for task details
    api_url = f"https://{api_host}:{API_PORT}/api/lifecycle/v4.1/svcmgr/tasks/{task_uuid}"
    
    try:
        # Make GET request to Service Manager API
        response = requests.get(
            api_url,
            headers={'Authorization': auth_header},
            verify=False,  # Disable SSL verification (common in internal environments)
            timeout=30  # 30 second timeout
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def extract_filename_from_line(line):
    """
    Extract filename from log line output.
    
    Grep output format is typically: "filename:log_content" or "path/filename:log_content"
    This function extracts just the filename part (without path).
    
    Args:
        line: Log line that may contain filename prefix (e.g., "styx.log.1:2024-01-01...")
        
    Returns:
        Filename if found, 'N/A' otherwise
        
    Example:
        Input: "styx.log.1:2024-01-01 10:00:00.123Z [INFO] ..."
        Output: "styx.log.1"
        
        Input: "/path/to/styx.log.1:2024-01-01 10:00:00.123Z [INFO] ..."
        Output: "styx.log.1"
    """
    if not line or not line.strip():
        return 'N/A'
    
    # Check if line contains colon (grep output format: "filename:content")
    if ':' in line:
        parts = line.split(':', 1)  # Split on first colon only
        filename_part = parts[0].strip()
        
        # Extract just the filename (remove path if present)
        if '/' in filename_part:
            filename_part = filename_part.split('/')[-1]
        
        # Return filename if it looks valid (not empty, not just whitespace)
        if filename_part and filename_part != '':
            return filename_part
    
    # If no colon found, try to extract filename from path-like strings
    # This handles cases where the line might just be a path
    if '/' in line:
        parts = line.split('/')
        if parts:
            last_part = parts[-1].strip()
            if last_part:
                return last_part
    
    return 'N/A'

def process_application_analysis(app_entry, app_name, section_prefix, run_dir, api_host=None):
    """
    Process a single application through the complete analysis pipeline.
    
    This is the core function that performs the full analysis for any application.
    It follows this flow:
    1. Search RR UUID in durga logs to find all occurrences
    2. Filter TRLID entries from durga logs
    3. Extract context UUID from TRLID entries
    4. Search context UUID in indra logs
    5. Extract smsp_app_uuid from indra logs
    6. Make API call to get application details and sub-services
    7. Find parent task UUID from indra logs
    8. Call Service Manager API to get task details (parent + subtasks)
    
    Args:
        app_entry: Dictionary containing 'start' and 'end' entries for the application
        app_name: Name of the application (e.g., 'nc-cpaas', 'ncm-base')
        section_prefix: Prefix for output messages (e.g., 'SECTION A', 'STEP 3')
        run_dir: Directory where debug files will be saved
        api_host: API hostname/IP for making API calls (optional)
        
    Returns:
        Dictionary containing all extracted data:
        - app_name: Application name
        - app_entry: Original entry data
        - rr_uuid: RR UUID used for searching
        - rr_lines: All lines containing RR UUID in durga logs
        - trlid_lines: Filtered TRLID entries from durga logs
        - context_uuid: Extracted context UUID from TRLID
        - indra_lines: All lines containing context UUID in indra logs
        - smsp_uuids: List of smsp_app_uuid values found
        - parsed_services: List of sub-services from API call
        - parent_task_uuid: Parent task UUID found in indra logs
        - svcmgr_tasks: List of parent and subtask details from API
    """
    # Initialize result dictionary to store all extracted data
    result = {
        'app_name': app_name,
        'app_entry': app_entry,
        'rr_uuid': app_entry['start']['rr'],  # Extract RR UUID from start entry
        'rr_lines': [],  # Will store all durga log lines containing RR UUID
        'trlid_lines': [],  # Will store filtered TRLID entries
        'context_uuid': None,  # Will store extracted context UUID
        'indra_lines': [],  # Will store all indra log lines containing context UUID
        'smsp_uuids': [],  # Will store all smsp_app_uuid values found
        'parsed_services': [],  # Will store sub-services from API response
        'parent_task_uuid': None,  # Will store parent task UUID
        'svcmgr_tasks': []  # Will store parent and subtask details
    }
    
    rr_uuid = result['rr_uuid']
    
    # ========================================================================
    # STEP 1: Search RR UUID in durga_* files
    # ========================================================================
    # Purpose: Find all occurrences of RR UUID in durga logs
    # This helps us understand what operations were performed with this RR UUID
    print(f"\n{section_prefix} STEP: Searching RR UUID in durga_* files")
    print("=" * 80)
    print(f"Application: {app_name}")
    print(f"RR UUID: {rr_uuid}")
    print(f"Path: {DURGA_LOG_PATH}")
    print(f"Pattern: {DURGA_LOG_PATTERN}")
    print("")
    
    local_rr_file = run_dir / f"{section_prefix.lower()}_rr_uuid_grep_{rr_uuid[:8]}.txt"
    rr_output = grep_with_xz(rr_uuid, DURGA_LOG_PATTERN, DURGA_LOG_PATH)
    with open(local_rr_file, 'w', encoding='utf-8') as f:
        f.write(rr_output)
    result['rr_lines'] = [l.strip() for l in rr_output.split('\n') if l.strip()]
    print(f"✓ Found {len(result['rr_lines'])} lines → saved to {local_rr_file}")
    
    # ========================================================================
    # STEP 2: Filter TRLID entries from durga logs
    # ========================================================================
    # Purpose: TRLID entries contain the context UUID we need
    # We filter the RR UUID results to only keep lines containing "TRLID"
    # This narrows down to the relevant entries that link RR UUID to context UUID
    print(f"\n{section_prefix} STEP: Filtering TRLID entries")
    print("=" * 80)
    local_trlid_file = run_dir / f"{section_prefix.lower()}_trlid_entries_{rr_uuid[:8]}.txt"
    # Filter: Keep only lines that contain "TRLID" (case-insensitive)
    result['trlid_lines'] = [l.strip() for l in result['rr_lines'] if DURGA_SEARCH_STRING.upper() in l.upper()]
    with open(local_trlid_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result['trlid_lines']))
    print(f"✓ Found {len(result['trlid_lines'])} TRLID entries → saved to {local_trlid_file}")
    
    # Early return if no TRLID entries found (can't proceed without context UUID)
    if not result['trlid_lines']:
        print("WARNING: No TRLID entries found for this application!")
        return result
    
    # ========================================================================
    # STEP 3: Parse TRLID entry and extract context UUID
    # ========================================================================
    # Purpose: Extract the context UUID from TRLID entries
    # The pattern "Setting TRLID from context <uuid>" gives us the context UUID
    # This context UUID is the key to finding information in indra logs
    print(f"\n{section_prefix} STEP: Parsing first TRLID entry and extracting context")
    print("=" * 80)
    context_pattern = r'Setting TRLID from context ([a-f0-9-]+)'  # Pattern to extract context UUID
    # Search through TRLID lines to find the context UUID
    for line in result['trlid_lines']:
        context_match = re.search(context_pattern, line)
        if context_match:
            result['context_uuid'] = context_match.group(1)  # Extract UUID from first match
            break  # Stop after finding first match
    
    # Early return if context UUID not found (can't proceed to indra search)
    if not result['context_uuid']:
        print("WARNING: No TRLID entry found with 'Setting TRLID from context' pattern!")
        return result
    
    print(f"Context UUID: {result['context_uuid']}")
    
    # ========================================================================
    # STEP 4: Search context UUID in indra_* files
    # ========================================================================
    # Purpose: Find all occurrences of context UUID in indra logs
    # Indra logs contain smsp_app_uuid and task information linked to this context
    print(f"\n{section_prefix} STEP: Searching context UUID in indra_* files")
    print("=" * 80)
    local_indra_file = run_dir / f"{section_prefix.lower()}_indra_context_{result['context_uuid'][:8]}.txt"
    indra_output = grep_with_xz(result['context_uuid'], INDRA_LOG_PATTERN, INDRA_LOG_PATH)
    with open(local_indra_file, 'w', encoding='utf-8') as f:
        f.write(indra_output)
    result['indra_lines'] = [l.strip() for l in indra_output.split('\n') if l.strip()]
    print(f"✓ Found {len(result['indra_lines'])} lines → saved to {local_indra_file}")
    
    # ========================================================================
    # STEP 5: Search for smsp_app_uuid in indra logs
    # ========================================================================
    # Purpose: Extract smsp_app_uuid from indra log lines
    # smsp_app_uuid is the application UUID used in Service Manager API calls
    # Format in logs: "smsp_app_uuid":"<uuid>"
    print(f"\n{section_prefix} STEP: Searching for smsp_app_uuid in indra results")
    print("=" * 80)
    smsp_uuid_pattern = r'"smsp_app_uuid":"([a-f0-9-]+)"'  # Pattern to extract smsp_app_uuid
    # Search through all indra lines for smsp_app_uuid
    for line in result['indra_lines']:
        if 'smsp_app_uuid' in line:  # Quick check before regex (performance optimization)
            smsp_match = re.search(smsp_uuid_pattern, line)
            if smsp_match:
                result['smsp_uuids'].append(smsp_match.group(1))  # Collect all found UUIDs
    
    if result['smsp_uuids']:
        print(f"✓ Found {len(result['smsp_uuids'])} smsp_app_uuid values")
        for i, uuid in enumerate(result['smsp_uuids'], 1):
            print(f"  {i}. {uuid}")
    else:
        print("No smsp_app_uuid found")
    
    # ========================================================================
    # STEP 6: Make API call to get application details (if smsp_uuid available)
    # ========================================================================
    # Purpose: Call Service Manager API to get application details and sub-services
    # This gives us information about the application status and its sub-services
    # API Endpoint: GET /api/lifecycle/v4.0/svcmgr/applications/{smsp_uuid}
    if result['smsp_uuids']:
        smsp_uuid = result['smsp_uuids'][0]
        
        if not api_host:
            print(f"⚠ {section_prefix} STEP: api_host not provided, skipping API call")
        elif not REQUESTS_AVAILABLE:
            print(f"⚠ {section_prefix} STEP: requests module not available, skipping API call")
        elif api_host and REQUESTS_AVAILABLE:
            print(f"\n{section_prefix} STEP: Making API call with smsp_app_uuid")
            print("=" * 80)
            api_url = f"https://{api_host}:{API_PORT}/api/lifecycle/v4.0/svcmgr/applications/{smsp_uuid}"
            credentials = f"{API_USERNAME}:{API_PASSWORD}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            auth_header = f"Basic {encoded_credentials}"
            
            try:
                response = requests.get(api_url, headers={'Authorization': auth_header}, verify=False, timeout=30)
                if response.status_code == 200:
                    api_data = response.json()
                    if 'data' in api_data and 'subServices' in api_data['data']:
                        sub_services = api_data['data']['subServices']
                        for service in sub_services:
                            result['parsed_services'].append({
                                'name': service.get('name', 'N/A'),
                                'status': service.get('status', 'N/A'),
                                'uuid': service.get('uuid', 'N/A'),
                                'version': service.get('version', 'N/A'),
                                'clusterUuid': service.get('clusterUuid', 'N/A'),
                                'createdTimestamp': service.get('createdTimestamp', 'N/A'),
                                'time_to_complete': 'N/A'  # Simplified for now
                            })
                        print(f"✓ Successfully parsed {len(result['parsed_services'])} subServices")
                    else:
                        print(f"⚠ API response does not contain 'data.subServices'")
                else:
                    print(f"⚠ API call failed with status code: {response.status_code}")
            except Exception as e:
                print(f"⚠ API call failed with error: {str(e)}")
    
    # ========================================================================
    # STEP 7: Find Service Manager Parent Task UUID from indra logs
    # ========================================================================
    # Purpose: Extract parent task UUID from indra logs
    # The task UUID appears in indra logs after smsp_app_uuid in a specific pattern:
    # - Look for ">>>>> Step 2: Polling Task" after smsp_app_uuid
    # - Then find "GET https://.../tasks/<uuid>" in subsequent lines
    # This task UUID is used to get detailed task information from Service Manager API
    if result['smsp_uuids']:
        smsp_uuid = result['smsp_uuids'][0]  # Use first smsp_app_uuid found
        # Search for smsp_uuid with context to find task UUID in nearby lines
        smsp_context_output = grep_with_xz_context(smsp_uuid, INDRA_LOG_PATTERN, INDRA_LOG_PATH, context_lines=5)
        if smsp_context_output:
            lines = smsp_context_output.split('\n')
            # Search through lines to find the task UUID pattern
            for i, line in enumerate(lines):
                if smsp_uuid in line:  # Found line with smsp_uuid
                    # Look ahead up to 10 lines for "Step 2: Polling Task"
                    for j in range(i+1, min(i+10, len(lines))):
                        if '>>>>> Step 2: Polling Task' in lines[j]:
                            # Look ahead up to 5 lines for GET request with task UUID
                            for k in range(j+1, min(j+5, len(lines))):
                                if 'GET https://' in lines[k] or 'GET http://' in lines[k]:
                                    # Extract task UUID from URL pattern: /tasks/<uuid>
                                    task_match = re.search(r'/tasks/([a-f0-9-]+)', lines[k])
                                    if task_match:
                                        result['parent_task_uuid'] = task_match.group(1)
                                        break
                            break
                    if result['parent_task_uuid']:
                        break  # Stop searching once we found the task UUID
        
        # ========================================================================
        # STEP 8: Call Service Manager API to get task details
        # ========================================================================
        # Purpose: Get detailed information about parent task and all subtasks
        # This includes task status, error messages (if failed), and subtask details
        # API Endpoint: GET /api/lifecycle/v4.1/svcmgr/tasks/{task_uuid}
        if result['parent_task_uuid']:
            if api_host and REQUESTS_AVAILABLE:
                # Prepare authentication header (Basic Auth)
                credentials = f"{API_USERNAME}:{API_PASSWORD}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                auth_header = f"Basic {encoded_credentials}"
                
                # Step 8a: Get parent task details
                parent_data, parent_error = call_svcmgr_api(api_host, result['parent_task_uuid'], auth_header)
                if parent_data and 'data' in parent_data:
                    parent_task_info = parent_data['data']
                    # Extract parent task information
                    parent_entry = {
                        'type': 'parent',  # Mark as parent task
                        'extId': parent_task_info.get('extId', 'N/A'),
                        'name': parent_task_info.get('name', 'N/A'),
                        'operation': parent_task_info.get('operation', 'N/A'),
                        'operationDescription': parent_task_info.get('operationDescription', 'N/A'),
                        'status': parent_task_info.get('status', 'N/A'),  # SUCCEEDED, FAILED, etc.
                        'mspUuid': parent_task_info.get('mspUuid', 'N/A')
                    }
                    # Step 8b: Extract error messages if task failed
                    # Error messages contain detailed failure information (code, message, severity)
                    if parent_task_info.get('status') == 'FAILED' and 'errorMessages' in parent_task_info:
                        error_messages = parent_task_info.get('errorMessages', [])
                        if error_messages:
                            parent_entry['errorMessages'] = []
                            for err_msg in error_messages:
                                err_entry = {
                                    'code': err_msg.get('code', 'N/A'),  # Error code (e.g., 95300)
                                    'errorGroup': err_msg.get('errorGroup', 'N/A'),  # Error group (e.g., SERVICE_MANAGER_APPLICATION_INSTALL_ERROR)
                                    'message': err_msg.get('message', 'N/A'),  # Error message
                                    'severity': err_msg.get('severity', 'N/A')  # ERROR, WARNING, etc.
                                }
                                # Extract status from argumentsMap if available
                                args_map = err_msg.get('argumentsMap', {})
                                if isinstance(args_map, dict):
                                    err_entry['status'] = args_map.get('status', 'N/A')
                                else:
                                    err_entry['status'] = 'N/A'
                                parent_entry['errorMessages'].append(err_entry)
                    result['svcmgr_tasks'].append(parent_entry)
                    
                    # Step 8c: Get subtask details
                    # Parent task contains references to subtasks, we need to fetch each one
                    sub_tasks = parent_task_info.get('subTasks', [])
                    if sub_tasks:
                        for i, subtask_ref in enumerate(sub_tasks, 1):
                            # Extract subtask UUID (can be dict with extId or direct UUID string)
                            subtask_uuid = subtask_ref.get('extId') if isinstance(subtask_ref, dict) else subtask_ref
                            if not subtask_uuid:
                                continue  # Skip if no UUID found
                            
                            # Call API for each subtask
                            subtask_data, subtask_error = call_svcmgr_api(api_host, subtask_uuid, auth_header)
                            if subtask_data and 'data' in subtask_data:
                                subtask_info = subtask_data['data']
                                # Extract subtask information
                                task_entry = {
                                    'type': 'subtask',  # Mark as subtask
                                    'index': i,  # Subtask index (1, 2, 3, ...)
                                    'extId': subtask_info.get('extId', 'N/A'),
                                    'name': subtask_info.get('name', 'N/A'),
                                    'operation': subtask_info.get('operation', 'N/A'),
                                    'operationDescription': subtask_info.get('operationDescription', 'N/A'),
                                    'status': subtask_info.get('status', 'N/A'),
                                    'mspUuid': subtask_info.get('mspUuid', 'N/A')
                                }
                                # Extract error messages if subtask failed
                                if subtask_info.get('status') == 'FAILED' and 'errorMessages' in subtask_info:
                                    error_messages = subtask_info.get('errorMessages', [])
                                    if error_messages:
                                        task_entry['errorMessages'] = []
                                        for err_msg in error_messages:
                                            err_entry = {
                                                'code': err_msg.get('code', 'N/A'),
                                                'errorGroup': err_msg.get('errorGroup', 'N/A'),
                                                'message': err_msg.get('message', 'N/A'),
                                                'severity': err_msg.get('severity', 'N/A')
                                            }
                                            # Extract status from argumentsMap if available
                                            args_map = err_msg.get('argumentsMap', {})
                                            if isinstance(args_map, dict):
                                                err_entry['status'] = args_map.get('status', 'N/A')
                                            else:
                                                err_entry['status'] = 'N/A'
                                            task_entry['errorMessages'].append(err_entry)
                                result['svcmgr_tasks'].append(task_entry)
    
    return result  # Return complete result dictionary with all extracted data

def print_tree_representation(oldest_entry, oldest_app_name, next_app_entry, next_app_name, 
                             next_rr_uuid, trlid_lines, context_uuid, indra_lines, 
                             smsp_uuids, parsed_services, run_dir, all_last_date_entries=None,
                             svcmgr_tasks=None, parent_task_uuid=None, section_b_result=None):
    """Print a clean tree representation of the complete analysis flow"""
    print("\n" + "=" * 80)
    print("📊 TREE REPRESENTATION: Complete Analysis Flow")
    print("=" * 80)
    print("")
    
    # Extract filenames
    durga_filename = extract_filename_from_line(trlid_lines[0] if trlid_lines else '')
    indra_filename = extract_filename_from_line(indra_lines[0] if indra_lines else '')
    
    # Level 1: APP-CREATE-START (Root) - Show ALL applications from last occurrence date
    print("┌─ APP-CREATE-START (Root)")
    
    if all_last_date_entries:
        # Sort by timestamp to show in chronological order
        sorted_entries = sorted(all_last_date_entries, key=lambda x: x['start']['timestamp'])
        
        for i, mapped_entry in enumerate(sorted_entries, 1):
            app_name = mapped_entry['app_name']
            start_entry = mapped_entry['start']
            # Extract filename from the stored line
            # The line should contain "filename:content" format from grep output
            filename = extract_filename_from_line(start_entry.get('line', ''))
            
            # Fallback: If filename extraction failed, try to get from log_file field if it exists
            if filename == 'N/A' and 'log_file' in start_entry:
                filename = start_entry['log_file']
            elif filename == 'N/A':
                # Last resort: try to extract from any path-like string in the line
                line_content = start_entry.get('line', '')
                if line_content:
                    # Look for common log file patterns in the line
                    log_patterns = [
                        r'(styx\.log[^:\s]*)',
                        r'([^/:\s]+\.log[^:\s]*)',
                        r'([^/:\s]+\.log\.\d+[^:\s]*)',
                        r'([^/:\s]+\.log\.\d+\.\d+[^:\s]*)'
                    ]
                    for pattern in log_patterns:
                        match = re.search(pattern, line_content)
                        if match:
                            filename = match.group(1)
                            break
            
            # Check if this is used for durga logs (Section A or Section B)
            is_durga_app_a = (mapped_entry['start']['uuid'] == next_app_entry['start']['uuid'])
            is_durga_app_b = False
            if section_b_result and section_b_result['app_entry']:
                is_durga_app_b = (mapped_entry['start']['uuid'] == section_b_result['app_entry']['start']['uuid'])
            is_durga_app = is_durga_app_a or is_durga_app_b
            
            # Determine connector
            if i == len(sorted_entries):
                connector = "└─"
                sub_connector = "   "
            else:
                connector = "├─"
                sub_connector = "│  "
            
            # Highlight if used for durga (Section A or B)
            if is_durga_app_a:
                app_display = f"{app_name} ⬅️ [SECTION A - USED FOR DURGA LOGS]"
                rr_display = f"{start_entry['rr']} ⬅️ [SEARCH KEY]"
            elif is_durga_app_b:
                app_display = f"{app_name} ⬅️ [SECTION B - USED FOR DURGA LOGS]"
                rr_display = f"{start_entry['rr']} ⬅️ [SEARCH KEY]"
            else:
                app_display = app_name
                rr_display = start_entry['rr']
            
            print(f"{sub_connector}{connector} Application {i}: {app_display}")
            print(f"{sub_connector}   ├─ UUID: {start_entry['uuid']}")
            print(f"{sub_connector}   ├─ RR UUID: {rr_display}")
            print(f"{sub_connector}   ├─ Timestamp: {start_entry['timestamp']}")
            print(f"{sub_connector}   ├─ BP: {start_entry['bp']}")
            print(f"{sub_connector}   ├─ cr: {start_entry['cr']}")
            print(f"{sub_connector}   ├─ pr: {start_entry['pr']}")
            print(f"{sub_connector}   └─ Log File: {filename}")
            
            if i < len(sorted_entries):
                print(f"{sub_connector}")
    else:
        # Fallback to old display if all_last_date_entries not provided
        styx_filename = extract_filename_from_line(oldest_entry.get('line', ''))
        print(f"│  └─ Application: {oldest_app_name}")
        print(f"     ├─ UUID: {oldest_entry['uuid']}")
        print(f"     ├─ RR UUID: {oldest_entry['rr']}")
        print(f"     ├─ Timestamp: {oldest_entry['timestamp']}")
        print(f"     └─ Log File: {styx_filename}")
    
    # Determine connector for next level
    has_children = (trlid_lines and context_uuid) or True
    connector = "├─" if has_children else "└─"
    
    # Level 2: TRLID (Durga) - Child of APP-CREATE-START
    if trlid_lines and context_uuid:
        # Extract first TRLID timestamp and T (task) ID
        first_trlid_ts = 'N/A'
        first_trlid_t = 'N/A'
        if trlid_lines:
            ts_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+Z)', trlid_lines[0])
            if ts_match:
                first_trlid_ts = ts_match.group(1)
            t_match = re.search(r'\[T:([a-f0-9-]+)\]', trlid_lines[0])
            if t_match:
                first_trlid_t = t_match.group(1)
        
        print(f"{connector}")
        print(f"│  └─ TRLID (Durga Logs) ⬅️ [SEARCHED WITH RR UUID: {next_rr_uuid}]")
        print(f"│     ├─ Context UUID (TRLID): {context_uuid} ⬅️ [EXTRACTED FROM TRLID]")
        print(f"│     ├─ Task ID (T): {first_trlid_t}")
        print(f"│     ├─ RR UUID: {next_rr_uuid}")
        print(f"│     ├─ Total TRLID entries: {len(trlid_lines)}")
        print(f"│     ├─ First TRLID timestamp: {first_trlid_ts}")
        print(f"│     └─ Log File: {durga_filename}")
        
        # Level 3: Indra - Sub-child of TRLID
        if indra_lines:
            # Extract IDs from indra logs
            indra_ids = []
            for line in indra_lines[:5]:  # Check first 5 lines for IDs
                # Try to extract various ID patterns
                id_patterns = [
                    r'\[R:([a-f0-9-]+)\]',
                    r'\[T:([a-f0-9-]+)\]',
                    r'\[cr:([a-f0-9-]+)\]',
                    r'\[pr:([a-f0-9-]+)\]',
                    r'\[rr:([a-f0-9-]+)\]'
                ]
                for pattern in id_patterns:
                    match = re.search(pattern, line)
                    if match:
                        indra_ids.append(f"{pattern[1:3]}: {match.group(1)}")
                        break
            
            print(f"│     │")
            print(f"│     └─ INDRA Logs")
            print(f"│        ├─ Context UUID: {context_uuid}")
            print(f"│        ├─ Total matches: {len(indra_lines)}")
            if indra_ids:
                print(f"│        ├─ Sample IDs: {', '.join(indra_ids[:3])}")
            print(f"│        └─ Log File: {indra_filename}")
            
            # Level 4: smsp_app_uuid - Sub-child of Indra
            # Show Section B first, then Section A
            if section_b_result and section_b_result.get('smsp_uuids'):
                # Section B (nc-cpaas) - Show first
                print(f"│        │")
                print(f"│        ├─ SECTION B: nc-cpaas Analysis")
                print(f"│        │  └─ smsp_app_uuid (Fetched App ID)")
                print(f"│        │     ├─ UUID: {section_b_result['smsp_uuids'][0]}")
                print(f"│        │     └─ Source: Indra logs")
                
                # Section B API Response
                if section_b_result.get('parsed_services'):
                    print(f"│        │     │")
                    print(f"│        │     ├─ API Response (JSON Output)")
                    print(f"│        │     │  ├─ Total subServices: {len(section_b_result['parsed_services'])}")
                    print(f"│        │     │  └─ SubServices Details:")
                    for i, service in enumerate(section_b_result['parsed_services'], 1):
                        is_last_service = (i == len(section_b_result['parsed_services']))
                        service_connector = "└─" if is_last_service else "├─"
                        print(f"│        │     │     {service_connector} {service['name']}")
                        print(f"│        │     │        ├─ Status: {service['status']}")
                        print(f"│        │     │        ├─ UUID: {service['uuid']}")
                        print(f"│        │     │        ├─ Version: {service['version']}")
                        print(f"│        │     │        ├─ Cluster UUID: {service['clusterUuid']}")
                        print(f"│        │     │        ├─ Created: {service['createdTimestamp']}")
                        print(f"│        │     │        └─ Time to complete: {service['time_to_complete']}")
                        if not is_last_service:
                            print(f"│        │     │        │")
                else:
                    print(f"│        │     │")
                    print(f"│        │     ├─ API Response: No subServices parsed")
                
                # Section B Service Manager Tasks
                if section_b_result.get('parent_task_uuid') and section_b_result.get('svcmgr_tasks'):
                    print(f"│        │     │")
                    print(f"│        │     └─ Service Manager Tasks")
                    print(f"│        │        ├─ Parent Task UUID: {section_b_result['parent_task_uuid']}")
                    
                    parent_task_b = next((t for t in section_b_result['svcmgr_tasks'] if t['type'] == 'parent'), None)
                    if parent_task_b:
                        print(f"│        │        ├─ Parent Task:")
                        print(f"│        │        │  ├─ name: {parent_task_b['name']}")
                        print(f"│        │        │  ├─ operation: {parent_task_b['operation']}")
                        print(f"│        │        │  ├─ status: {parent_task_b['status']}")
                        print(f"│        │        │  └─ extId: {parent_task_b['extId']}")
                    
                    subtasks_b = [t for t in section_b_result['svcmgr_tasks'] if t['type'] == 'subtask']
                    if subtasks_b:
                        print(f"│        │        ├─ SubTasks: {len(subtasks_b)}")
                        for i, subtask in enumerate(subtasks_b, 1):
                            if 'error' not in subtask:
                                is_last_subtask = (i == len(subtasks_b))
                                subtask_connector = "└─" if is_last_subtask else "├─"
                                print(f"│        │        │  {subtask_connector} SubTask {subtask['index']}: {subtask['name']} ({subtask['status']})")
                                print(f"│        │        │     └─ extId: {subtask['extId']}")
                                if not is_last_subtask:
                                    print(f"│        │        │     │")
                    else:
                        print(f"│        │        └─ No subtasks found")
            
            # Section A - Show after Section B
            if smsp_uuids:
                print(f"│        │")
                print(f"│        └─ SECTION A: {next_app_name} Analysis")
                print(f"│           └─ smsp_app_uuid (Fetched App ID)")
                print(f"│              ├─ UUID: {smsp_uuids[0]}")
                print(f"│              └─ Source: Indra logs")
                
                # Level 5: API Response (subServices) - Sub-child of smsp_app_uuid
                if parsed_services:
                    print(f"│              │")
                    print(f"│              ├─ API Response (JSON Output)")
                    print(f"│              │  ├─ Total subServices: {len(parsed_services)}")
                    print(f"│              │  └─ SubServices Details:")
                    for i, service in enumerate(parsed_services, 1):
                        is_last_service = (i == len(parsed_services))
                        service_connector = "└─" if is_last_service else "├─"
                        print(f"│              │     {service_connector} {service['name']}")
                        print(f"│              │        ├─ Status: {service['status']}")
                        print(f"│              │        ├─ UUID: {service['uuid']}")
                        print(f"│              │        ├─ Version: {service['version']}")
                        print(f"│              │        ├─ Cluster UUID: {service['clusterUuid']}")
                        print(f"│              │        ├─ Created: {service['createdTimestamp']}")
                        print(f"│              │        └─ Time to complete: {service['time_to_complete']}")
                        if not is_last_service:
                            print(f"│              │        │")
                else:
                    print(f"│              │")
                    print(f"│              ├─ API Response: No subServices parsed")
                
                # Level 6: Service Manager Tasks - Sub-child of smsp_app_uuid
                if parent_task_uuid and svcmgr_tasks:
                    print(f"│              │")
                    print(f"│              └─ Service Manager Tasks")
                    print(f"│                 ├─ Parent Task UUID: {parent_task_uuid}")
                    
                    parent_task = next((t for t in svcmgr_tasks if t['type'] == 'parent'), None)
                    if parent_task:
                        print(f"│                 ├─ Parent Task:")
                        print(f"│                 │  ├─ name: {parent_task['name']}")
                        print(f"│                 │  ├─ operation: {parent_task['operation']}")
                        print(f"│                 │  ├─ status: {parent_task['status']}")
                        print(f"│                 │  └─ extId: {parent_task['extId']}")
                    
                    subtasks = [t for t in svcmgr_tasks if t['type'] == 'subtask']
                    if subtasks:
                        print(f"│                 ├─ SubTasks: {len(subtasks)}")
                        for i, subtask in enumerate(subtasks, 1):
                            if 'error' not in subtask:
                                is_last_subtask = (i == len(subtasks))
                                subtask_connector = "└─" if is_last_subtask else "├─"
                                print(f"│                 │  {subtask_connector} SubTask {subtask['index']}: {subtask['name']} ({subtask['status']})")
                                print(f"│                 │     └─ extId: {subtask['extId']}")
                                if not is_last_subtask:
                                    print(f"│                 │     │")
                    else:
                        print(f"│                 └─ No subtasks found")
            else:
                if not (section_b_result and section_b_result.get('smsp_uuids')):
                    print(f"│        │")
                    print(f"│        └─ smsp_app_uuid: Not found")
        else:
            print(f"│     │")
            print(f"│     └─ INDRA Logs: No matches found")
    else:
        print(f"{connector}")
        print(f"│  └─ TRLID: Not found or context UUID not extracted")
    
    # Section B tree is now displayed above in the INDRA section (removed duplicate)
    
    print("")
    print("=" * 80)

def main():
    """
    Main function that orchestrates the entire log analysis workflow.
    
    Processing Flow:
    1. Extract APP-CREATE-START entries from styx logs
    2. Extract APP-CREATE-END entries and map with START entries
    3. Process oldest entry (always runs)
    4. Check for nc-cpaas application (optional)
    5. Check for ncm-base application (optional)
    6. For each application found:
       - Search RR UUID in durga logs
       - Extract TRLID and context UUID
       - Search context UUID in indra logs
       - Extract smsp_app_uuid
       - Make API calls
       - Get Service Manager task details
    7. Print tree representation
    8. Print Service Manager task details
    9. Search task IDs in svcmgr pod logs
    10. Search mspUuid in msp_controller logs
    11. Print summary
    """
    # ========================================================================
    # Parse command-line arguments
    # ========================================================================
    parser = argparse.ArgumentParser(description='Analyze Styx logs and related services')
    parser.add_argument('--api-host', required=True, help='API host (e.g., 10.122.27.232)')
    parser.add_argument('--central-dir', required=False, 
                       help='Central directory containing all log files (styx, durga, indra, svcmgr, msp_controller). '
                            'If provided, all log searches will use this directory instead of individual paths.')
    args = parser.parse_args()
    
    api_host = args.api_host
    central_dir = args.central_dir
    
    # ========================================================================
    # Handle central directory option
    # ========================================================================
    # BEHAVIOR:
    # - By default (no --central-dir): Uses individual paths defined at top of file
    #   (STYX_LOG_PATH, DURGA_LOG_PATH, INDRA_LOG_PATH, etc.)
    # - With --central-dir: Overrides ALL paths to use the central directory
    # - All parsing logic remains UNTOUCHED - only the search paths change
    # - File patterns (styx.log*, durga_*, indra_*, etc.) remain the same
    global STYX_LOG_PATH, DURGA_LOG_PATH, INDRA_LOG_PATH, SVC_MGR_POD_LOG_PATH, MSP_CONTROLLER_LOG_PATH
    
    if central_dir:
        # ====================================================================
        # CENTRAL DIRECTORY MODE: Override all paths to use central directory
        # ====================================================================
        # Validate that central directory exists
        central_path = Path(central_dir)
        if not central_path.exists():
            print(f"ERROR: Central directory does not exist: {central_dir}")
            sys.exit(1)
        if not central_path.is_dir():
            print(f"ERROR: Central directory path is not a directory: {central_dir}")
            sys.exit(1)
        
        # Override all log paths to use central directory
        # Note: File patterns remain the same (styx.log*, durga_*, etc.)
        # The script will search for these patterns in the central directory
        # All parsing logic is UNTOUCHED - only paths change
        print("=" * 80)
        print(f"Using central directory for all log files: {central_dir}")
        print("=" * 80)
        print("")
        
        STYX_LOG_PATH = str(central_path)
        DURGA_LOG_PATH = str(central_path)
        INDRA_LOG_PATH = str(central_path)
        SVC_MGR_POD_LOG_PATH = str(central_path)
        MSP_CONTROLLER_LOG_PATH = str(central_path)
    else:
        # ====================================================================
        # DEFAULT MODE: Use individual paths as defined at top of file
        # ====================================================================
        # Uses the paths you have maintained in the configuration section
        # No changes to paths - uses original individual directory paths
        print("=" * 80)
        print("Using default log paths (individual directories)")
        print("=" * 80)
        print(f"  STYX:     {STYX_LOG_PATH}")
        print(f"  DURGA:    {DURGA_LOG_PATH}")
        print(f"  INDRA:    {INDRA_LOG_PATH}")
        print(f"  SVC_MGR:  {SVC_MGR_POD_LOG_PATH}")
        print(f"  MSP_CTRL: {MSP_CONTROLLER_LOG_PATH}")
        print("=" * 80)
        print("")
    # Create output directory in same location as script
    script_dir = Path(__file__).parent.absolute()
    run_dir = script_dir / "debug-analysis" / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = run_dir / "complete_analysis_output.txt"
    
    # Redirect output
    class Tee:
        def __init__(self, f):
            self.file = open(f, 'w', encoding='utf-8')
            self.stdout = sys.stdout
        def write(self, s):
            self.file.write(s)
            self.stdout.write(s)
            self.file.flush()
        def flush(self):
            self.file.flush()
    
    tee = Tee(output_file)
    sys.stdout = tee
    sys.stderr = tee
    
    try:
        # ======================================================================
        # STEP 1: Grep APP-CREATE-START from styx logs (direct path, handles .xz)
        # ======================================================================
        print("=" * 80)
        print("STEP 1: Extracting APP-CREATE-START entries from styx.log* files")
        print("=" * 80)
        print(f"Path: {STYX_LOG_PATH}")
        print(f"Pattern: {STYX_LOG_PATTERN}")
        print("(Handling both regular and .xz compressed files)")
        print("")
        
        start_output = grep_with_xz("APP-CREATE-START", STYX_LOG_PATTERN, STYX_LOG_PATH)
        
        # Parse all lines - extract full details (BP, cr, pr, rr, timestamp, uuid)
        bp_pattern = r'\[BP-([^\]]+)\]'
        cr_pattern = r'\[cr:([a-f0-9-]+)\]'
        pr_pattern = r'\[pr:([a-f0-9-]+)\]'
        
        start_entries = []
        for line in start_output.split('\n'):
            if not line.strip():
                continue
            # Dynamic extraction: UUID, timestamp, RR, BP, cr, pr
            uuid_regex = re.escape("APP-CREATE-START") + UUID_PATTERN
            uuid_match = re.search(uuid_regex, line)
            ts_match = re.search(TIMESTAMP_PATTERN, line)
            rr_match = re.search(RR_PATTERN, line)
            bp_match = re.search(bp_pattern, line)
            cr_match = re.search(cr_pattern, line)
            pr_match = re.search(pr_pattern, line)
            
            if uuid_match and ts_match and rr_match:
                start_entries.append({
                    'uuid': uuid_match.group(1),
                    'timestamp': ts_match.group(1),
                    'rr': rr_match.group(1),
                    'bp': bp_match.group(1) if bp_match else 'N/A',
                    'cr': cr_match.group(1) if cr_match else 'N/A',
                    'pr': pr_match.group(1) if pr_match else 'N/A',
                    'line': line
                })
        
        print(f"Found {len(start_entries)} valid APP-CREATE-START entries")
        
        if not start_entries:
            print("No valid entries found!")
            return
        
        # ======================================================================
        # STEP 2: Grep APP-CREATE-END and map with START entries
        # ======================================================================
        print("\n" + "=" * 80)
        print("STEP 2: Extracting APP-CREATE-END entries and mapping with START")
        print("=" * 80)
        
        end_output = grep_with_xz("APP-CREATE-END", STYX_LOG_PATTERN, STYX_LOG_PATH)
        
        # Parse END entries and create mapping by UUID
        end_entries = {}  # uuid -> list of end entries
        for line in end_output.split('\n'):
            if not line.strip():
                continue
            end_match = re.search(END_PATTERN, line)
            ts_match = re.search(TIMESTAMP_PATTERN, line)
            if end_match and ts_match:
                uuid = end_match.group(1)
                app_name = end_match.group(2)
                if uuid not in end_entries:
                    end_entries[uuid] = []
                end_entries[uuid].append({
                    'uuid': uuid,
                    'app_name': app_name,
                    'timestamp': ts_match.group(1),
                    'line': line
                })
        
        print(f"Found {len(end_entries)} unique APP-CREATE-END entries")
        
        # Map START with END and extract application names
        mapped_entries = []
        for start_entry in start_entries:
            uuid = start_entry['uuid']
            end_entry = end_entries.get(uuid, [None])[0] if uuid in end_entries else None
            mapped_entries.append({
                'start': start_entry,
                'end': end_entry,
                'app_name': end_entry['app_name'] if end_entry else 'N/A'
            })
        
        # ======================================================================
        # DEBUG: Write all APP-CREATE-START and APP-CREATE-END entries to file
        # ======================================================================
        debug_file = run_dir / "all_app_create_entries_debug.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("DEBUG: All APP-CREATE-START and APP-CREATE-END Entries\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total START entries: {len(start_entries)}\n")
            f.write(f"Total END entries: {len(end_entries)}\n")
            f.write(f"Total mapped entries: {len(mapped_entries)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort all entries by timestamp
            sorted_mapped_entries = sorted(mapped_entries, key=lambda x: x['start']['timestamp'])
            
            # Group by date for better organization
            entries_by_date_debug = {}
            for mapped in sorted_mapped_entries:
                ts = mapped['start']['timestamp']
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', ts)
                if date_match:
                    date = date_match.group(1)
                    if date not in entries_by_date_debug:
                        entries_by_date_debug[date] = []
                    entries_by_date_debug[date].append(mapped)
            
            # Write entries grouped by date
            for date in sorted(entries_by_date_debug.keys(), reverse=True):
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"DATE: {date} ({len(entries_by_date_debug[date])} entries)\n")
                f.write("=" * 80 + "\n\n")
                
                for i, mapped_entry in enumerate(entries_by_date_debug[date], 1):
                    start_entry = mapped_entry['start']
                    end_entry = mapped_entry['end']
                    app_name = mapped_entry['app_name']
                    
                    f.write(f"Entry {i}:\n")
                    f.write(f"  Application Name: {app_name}\n")
                    f.write(f"  UUID:             {start_entry['uuid']}\n")
                    f.write(f"  Timestamp:        {start_entry['timestamp']}\n")
                    f.write(f"  BP:               {start_entry['bp']}\n")
                    f.write(f"  cr:               {start_entry['cr']}\n")
                    f.write(f"  pr:               {start_entry['pr']}\n")
                    f.write(f"  rr:               {start_entry['rr']}\n")
                    
                    # Extract filename from log line
                    filename = extract_filename_from_line(start_entry.get('line', ''))
                    
                    # Fallback: If filename extraction failed, try to get from log_file field if it exists
                    if filename == 'N/A' and 'log_file' in start_entry:
                        filename = start_entry['log_file']
                    elif filename == 'N/A':
                        # Last resort: try to extract from any path-like string in the line
                        line_content = start_entry.get('line', '')
                        if line_content:
                            # Look for common log file patterns in the line
                            log_patterns = [
                                r'(styx\.log[^:\s]*)',
                                r'([^/:\s]+\.log[^:\s]*)',
                                r'([^/:\s]+\.log\.\d+[^:\s]*)',
                                r'([^/:\s]+\.log\.\d+\.\d+[^:\s]*)'
                            ]
                            for pattern in log_patterns:
                                match = re.search(pattern, line_content)
                                if match:
                                    filename = match.group(1)
                                    break
                    
                    if filename != 'N/A':
                        f.write(f"  START Log File:   {filename}\n")
                    else:
                        f.write(f"  START Log File:   N/A (could not extract from line)\n")
                        # Write the raw line for debugging
                        f.write(f"  Raw Line (first 200 chars): {start_entry.get('line', '')[:200]}\n")
                    
                    if end_entry:
                        f.write(f"  APP-CREATE-END:   ✓ FOUND\n")
                        f.write(f"    END Timestamp:  {end_entry['timestamp']}\n")
                        end_filename = extract_filename_from_line(end_entry.get('line', ''))
                        if end_filename != 'N/A':
                            f.write(f"    END Log File:   {end_filename}\n")
                    else:
                        f.write(f"  APP-CREATE-END:   ✗ MISSING\n")
                    
                    f.write("\n")
            
            # Summary section
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUMMARY BY APPLICATION NAME\n")
            f.write("=" * 80 + "\n\n")
            
            app_name_counts = {}
            for mapped in mapped_entries:
                app_name = mapped['app_name']
                if app_name not in app_name_counts:
                    app_name_counts[app_name] = {'total': 0, 'with_end': 0, 'without_end': 0}
                app_name_counts[app_name]['total'] += 1
                if mapped['end']:
                    app_name_counts[app_name]['with_end'] += 1
                else:
                    app_name_counts[app_name]['without_end'] += 1
            
            for app_name in sorted(app_name_counts.keys()):
                counts = app_name_counts[app_name]
                f.write(f"{app_name}:\n")
                f.write(f"  Total entries:     {counts['total']}\n")
                f.write(f"  With END:          {counts['with_end']}\n")
                f.write(f"  Without END:       {counts['without_end']}\n")
                f.write("\n")
        
        print(f"\n✓ Debug file created: {debug_file}")
        print(f"  Contains all {len(mapped_entries)} APP-CREATE-START and APP-CREATE-END entries")
        
        # Group entries by date (extract date from timestamp)
        entries_by_date = {}
        for mapped in mapped_entries:
            ts = mapped['start']['timestamp']
            # Extract date part: YYYY-MM-DD from timestamp
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', ts)
            if date_match:
                date = date_match.group(1)
                if date not in entries_by_date:
                    entries_by_date[date] = []
                entries_by_date[date].append(mapped)
        
        # Find the LAST (most recent) date
        if not entries_by_date:
            print("ERROR: No valid dates found in entries!")
            return
        
        last_date = max(entries_by_date.keys())
        print(f"\nLast occurrence date: {last_date} ({len(entries_by_date[last_date])} entries)")
        
        # Within the last date, find the oldest entry (earliest timestamp)
        last_date_entries = entries_by_date[last_date]
        last_date_entries.sort(key=lambda x: x['start']['timestamp'])
        
        # Find oldest entry within last date (first in sorted list for that date)
        oldest_mapped = last_date_entries[0]
        oldest = oldest_mapped['start']
        oldest_app_name = oldest_mapped['app_name']
        
        print(f"\nOldest APP-CREATE-START entry (within last occurrence date {last_date}):")
        print(f"  UUID: {oldest['uuid']}")
        print(f"  Timestamp: {oldest['timestamp']}")
        print(f"  RR UUID: {oldest['rr']}")
        print(f"  Application: {oldest_app_name}")
        
        # ======================================================================
        # STEP 3: Process oldest entry first (ALWAYS RUNS - INDEPENDENT PROCESSING)
        # ======================================================================
        print("\n" + "=" * 80)
        print("=" * 80)
        print("STEP 3: Processing oldest entry (Application: {})".format(oldest_app_name))
        print("=" * 80)
        print("=" * 80)
        print("NOTE: This step ALWAYS runs independently to process the oldest entry.")
        print("      It will NOT stop if subsequent applications are not found.")
        print("=" * 80)
        
        # Create a mapped entry structure for the oldest entry
        oldest_debug_entry = {
            'start': oldest,
            'end': oldest_mapped.get('end'),
            'app_name': oldest_app_name
        }
        
        # Run the full analysis pipeline for oldest entry
        print(f"\nProcessing Application: {oldest_app_name}")
        print(f"RR UUID: {oldest['rr']}")
        print("")
        
        oldest_debug_result = process_application_analysis(
            app_entry=oldest_debug_entry,
            app_name=oldest_app_name,
            section_prefix="STEP 3",
            run_dir=run_dir,
            api_host=api_host
        )
        
        # Print summary for oldest entry
        print("\n" + "=" * 80)
        print("STEP 3: Analysis Summary for Oldest Entry")
        print("=" * 80)
        print(f"Application: {oldest_app_name}")
        print(f"RR UUID: {oldest['rr']}")
        print(f"RR UUID matches in durga: {len(oldest_debug_result.get('rr_lines', []))}")
        print(f"TRLID entries found: {len(oldest_debug_result.get('trlid_lines', []))}")
        print(f"Context UUID: {oldest_debug_result.get('context_uuid', 'N/A')}")
        print(f"Indra matches: {len(oldest_debug_result.get('indra_lines', []))}")
        print(f"smsp_app_uuid found: {len(oldest_debug_result.get('smsp_uuids', []))}")
        if oldest_debug_result.get('smsp_uuids'):
            print(f"smsp_app_uuid values: {', '.join(oldest_debug_result['smsp_uuids'])}")
        print(f"Sub-services parsed: {len(oldest_debug_result.get('parsed_services', []))}")
        if oldest_debug_result.get('parsed_services'):
            print("\nSub-services details:")
            for i, service in enumerate(oldest_debug_result['parsed_services'], 1):
                print(f"  {i}. {service['name']} - Status: {service['status']} - UUID: {service['uuid']}")
        print(f"Parent task UUID: {oldest_debug_result.get('parent_task_uuid', 'N/A')}")
        print(f"Service Manager tasks: {len(oldest_debug_result.get('svcmgr_tasks', []))}")
        print("=" * 80)
        print("✓ STEP 3 completed successfully - continuing to check for other applications...")
        print("=" * 80)
        
        # ======================================================================
        # STEP 4: Find nc-cpaas application from last occurrence date (OPTIONAL)
        # ======================================================================
        print("\n" + "=" * 80)
        print("STEP 4: Checking for 'nc-cpaas' application (OPTIONAL - will continue if not found)")
        print("=" * 80)
        
        nc_cpaas_entry = None
        for mapped_entry in last_date_entries:
            if mapped_entry['app_name'] == 'nc-cpaas':
                nc_cpaas_entry = mapped_entry
                break
        
        if nc_cpaas_entry:
            print(f"✓ Found nc-cpaas application:")
            print(f"  UUID:        {nc_cpaas_entry['start']['uuid']}")
            print(f"  Timestamp:   {nc_cpaas_entry['start']['timestamp']}")
            print(f"  RR UUID:     {nc_cpaas_entry['start']['rr']}")
            print(f"  Application: nc-cpaas")
        else:
            print("⚠ nc-cpaas application not found in last occurrence date")
            print("  Continuing with other applications...")
        
        # ======================================================================
        # STEP 5: Find "Nutanix Cloud Manager" and next application (ncm-base)
        # ======================================================================
        print("\n" + "=" * 80)
        print("STEP 5: Finding 'Nutanix Cloud Manager' and next application")
        print("=" * 80)
        
        # Sort all entries by timestamp to find sequence
        all_sorted_entries = sorted(mapped_entries, key=lambda x: x['start']['timestamp'])
        
        # Find position of oldest entry
        oldest_index = None
        for i, mapped in enumerate(all_sorted_entries):
            if mapped['start']['uuid'] == oldest['uuid']:
                oldest_index = i
                break
        
        # Find next entry after oldest that has app_name == "Nutanix Cloud Manager"
        nutanix_cloud_manager_entry = None
        next_app_entry = None
        next_app_name = None
        next_rr_uuid = None
        
        if oldest_index is not None:
            for mapped in all_sorted_entries[oldest_index + 1:]:
                if mapped['end'] and mapped['app_name'] == "Nutanix Cloud Manager":
                    nutanix_cloud_manager_entry = mapped
                    break
            
            if nutanix_cloud_manager_entry:
                ncm_start = nutanix_cloud_manager_entry['start']
                # Find position of Nutanix Cloud Manager entry
                ncm_index = None
                for i, mapped in enumerate(all_sorted_entries):
                    if mapped['start']['uuid'] == ncm_start['uuid']:
                        ncm_index = i
                        break
                
                # Find immediate next entry after Nutanix Cloud Manager
                if ncm_index is not None and ncm_index + 1 < len(all_sorted_entries):
                    next_app_entry = all_sorted_entries[ncm_index + 1]
                    if next_app_entry:
                        next_app_name = next_app_entry['app_name']
                        next_rr_uuid = next_app_entry['start']['rr']
                        print(f"✓ Found application after Nutanix Cloud Manager:")
                        print(f"  Application: {next_app_name}")
                        print(f"  RR UUID:     {next_rr_uuid}")
            else:
                print("⚠ 'Nutanix Cloud Manager' entry not found after oldest entry")
        else:
            print("⚠ Could not find oldest entry position in sorted list")
        
        # ======================================================================
        # SECTION B: Process nc-cpaas Application (if found)
        # ======================================================================
        section_b_result = None
        if nc_cpaas_entry:
            print("\n" + "=" * 80)
            print("=" * 80)
            print("SECTION B: Processing nc-cpaas Application")
            print("=" * 80)
            print("=" * 80)
            
            # Process nc-cpaas using the helper function
            section_b_result = process_application_analysis(
                app_entry=nc_cpaas_entry,
                app_name='nc-cpaas',
                section_prefix="SECTION B",
                run_dir=run_dir,
                api_host=api_host
            )
        else:
            print("\n" + "=" * 80)
            print("SECTION B: Skipping nc-cpaas (not found)")
            print("=" * 80)
        
        # ======================================================================
        # SECTION A: Process Application after Nutanix Cloud Manager (if found)
        # ======================================================================
        section_a_result = None
        if next_app_entry and next_app_name:
            print("\n" + "=" * 80)
            print("=" * 80)
            print("SECTION A: Processing Application after Nutanix Cloud Manager")
            print(f"Application: {next_app_name}")
            print("=" * 80)
            print("=" * 80)
            
            # Process next_app_entry using the helper function
            section_a_result = process_application_analysis(
                app_entry=next_app_entry,
                app_name=next_app_name,
                section_prefix="SECTION A",
                run_dir=run_dir,
                api_host=api_host
            )
        else:
            print("\n" + "=" * 80)
            print("SECTION A: Skipping (application after Nutanix Cloud Manager not found)")
            print("=" * 80)
        
        # Use Section A results as primary if available, otherwise use oldest entry results
        if section_a_result:
            rr_uuid_a = section_a_result['rr_uuid']
            rr_lines_a = section_a_result['rr_lines']
            trlid_lines_a = section_a_result['trlid_lines']
            context_uuid_a = section_a_result['context_uuid']
            indra_lines_a = section_a_result['indra_lines']
            smsp_uuids_a = section_a_result['smsp_uuids']
            parsed_services_a = section_a_result['parsed_services']
            parent_task_uuid_a = section_a_result['parent_task_uuid']
            svcmgr_tasks_a = section_a_result['svcmgr_tasks']
            
            # Keep old variable names for backward compatibility with existing code
            rr_uuid = rr_uuid_a
            rr_lines = rr_lines_a
            trlid_lines = trlid_lines_a
            context_uuid = context_uuid_a
            indra_lines = indra_lines_a
            smsp_uuids = smsp_uuids_a
            parsed_services = parsed_services_a
            parent_task_uuid = parent_task_uuid_a
            svcmgr_tasks = svcmgr_tasks_a
        else:
            # Fallback to oldest entry results if Section A not available
            rr_uuid = oldest['rr']
            rr_lines = oldest_debug_result.get('rr_lines', [])
            trlid_lines = oldest_debug_result.get('trlid_lines', [])
            context_uuid = oldest_debug_result.get('context_uuid')
            indra_lines = oldest_debug_result.get('indra_lines', [])
            smsp_uuids = oldest_debug_result.get('smsp_uuids', [])
            parsed_services = oldest_debug_result.get('parsed_services', [])
            parent_task_uuid = oldest_debug_result.get('parent_task_uuid')
            svcmgr_tasks = oldest_debug_result.get('svcmgr_tasks', [])
            
            # Set Section A variables to empty for compatibility
            rr_uuid_a = rr_uuid
            rr_lines_a = rr_lines
            trlid_lines_a = trlid_lines
            context_uuid_a = context_uuid
            indra_lines_a = indra_lines
            smsp_uuids_a = smsp_uuids
            parsed_services_a = parsed_services
            parent_task_uuid_a = parent_task_uuid
            svcmgr_tasks_a = svcmgr_tasks
        
        # ======================================================================
        # STEP 12: Print Tree Representation
        # ======================================================================
        # Get parsed_services if available (from STEP 9)
        parsed_services = []
        if smsp_uuids:
            # Check if we have parsed services from API call
            local_services_file = run_dir / f"subservices_{smsp_uuids[0][:8]}.json"
            if local_services_file.exists():
                try:
                    with open(local_services_file, 'r', encoding='utf-8') as f:
                        parsed_services = json.load(f)
                except:
                    pass
        
        print_tree_representation(
            oldest_entry=oldest,
            oldest_app_name=oldest_app_name,
            next_app_entry=next_app_entry if next_app_entry else oldest_debug_entry,
            next_app_name=next_app_name if next_app_name else oldest_app_name,
            next_rr_uuid=next_rr_uuid if next_rr_uuid else oldest['rr'],
            trlid_lines=trlid_lines_a,
            context_uuid=context_uuid_a,
            indra_lines=indra_lines_a,
            smsp_uuids=smsp_uuids_a,
            parsed_services=parsed_services_a,
            run_dir=run_dir,
            all_last_date_entries=last_date_entries,
            svcmgr_tasks=svcmgr_tasks_a,
            parent_task_uuid=parent_task_uuid_a,
            section_b_result=section_b_result
        )
        
        # ======================================================================
        # STEP 13: Print SVC MGR Section
        # ======================================================================
        print("\n" + "=" * 80)
        print("SVC MGR: Service Manager Task Details")
        print("=" * 80)
        
        if parent_task_uuid:
            print(f"\nParent Task UUID: {parent_task_uuid}")
            print("")
            
            if svcmgr_tasks:
                # Print parent task
                parent_task = next((t for t in svcmgr_tasks if t['type'] == 'parent'), None)
                if parent_task:
                    print("Parent Task:")
                    print(f"  extId:                {parent_task['extId']}")
                    print(f"  name:                 {parent_task['name']}")
                    print(f"  operation:            {parent_task['operation']}")
                    print(f"  operationDescription: {parent_task['operationDescription']}")
                    print(f"  status:               {parent_task['status']}")
                    print(f"  mspUuid:              {parent_task['mspUuid']}")
                    
                    # Print errorMessages if status is FAILED
                    if parent_task.get('status') == 'FAILED' and 'errorMessages' in parent_task:
                        print(f"  Error Messages:")
                        for err_idx, err_msg in enumerate(parent_task['errorMessages'], 1):
                            print(f"    Error {err_idx}:")
                            print(f"      code:        {err_msg.get('code', 'N/A')}")
                            print(f"      errorGroup:  {err_msg.get('errorGroup', 'N/A')}")
                            print(f"      message:     {err_msg.get('message', 'N/A')}")
                            print(f"      severity:    {err_msg.get('severity', 'N/A')}")
                            print(f"      status:      {err_msg.get('status', 'N/A')}")
                    print("")
                
                # Print subtasks
                subtasks = [t for t in svcmgr_tasks if t['type'] == 'subtask']
                if subtasks:
                    print(f"SubTasks ({len(subtasks)}):")
                    print("")
                    for subtask in subtasks:
                        if 'error' in subtask:
                            print(f"SubTask {subtask['index']}:")
                            print(f"  extId: {subtask['extId']}")
                            print(f"  ERROR: {subtask['error']}")
                        else:
                            print(f"SubTask {subtask['index']}:")
                            print(f"  extId:                {subtask['extId']}")
                            print(f"  name:                 {subtask['name']}")
                            print(f"  operation:            {subtask['operation']}")
                            print(f"  operationDescription: {subtask['operationDescription']}")
                            print(f"  status:               {subtask['status']}")
                            print(f"  mspUuid:              {subtask['mspUuid']}")
                            
                            # Print errorMessages if status is FAILED
                            if subtask.get('status') == 'FAILED' and 'errorMessages' in subtask:
                                print(f"  Error Messages:")
                                for err_idx, err_msg in enumerate(subtask['errorMessages'], 1):
                                    print(f"    Error {err_idx}:")
                                    print(f"      code:        {err_msg.get('code', 'N/A')}")
                                    print(f"      errorGroup:  {err_msg.get('errorGroup', 'N/A')}")
                                    print(f"      message:     {err_msg.get('message', 'N/A')}")
                                    print(f"      severity:    {err_msg.get('severity', 'N/A')}")
                                    print(f"      status:      {err_msg.get('status', 'N/A')}")
                        print("")
                else:
                    print("No subtasks found")
            else:
                print("No task details available")
        else:
            print("No parent task UUID found")
        
        print("=" * 80)
        
        # ======================================================================
        # STEP 13b: Print SVC MGR Section for Section B (nc-cpaas)
        # ======================================================================
        if section_b_result and section_b_result['parent_task_uuid']:
            print("\n" + "=" * 80)
            print("SVC MGR (SECTION B - nc-cpaas): Service Manager Task Details")
            print("=" * 80)
            
            print(f"\nParent Task UUID: {section_b_result['parent_task_uuid']}")
            print("")
            
            if section_b_result['svcmgr_tasks']:
                # Print parent task
                parent_task_b = next((t for t in section_b_result['svcmgr_tasks'] if t['type'] == 'parent'), None)
                if parent_task_b:
                    print("Parent Task:")
                    print(f"  extId:                {parent_task_b['extId']}")
                    print(f"  name:                 {parent_task_b['name']}")
                    print(f"  operation:            {parent_task_b['operation']}")
                    print(f"  operationDescription: {parent_task_b['operationDescription']}")
                    print(f"  status:               {parent_task_b['status']}")
                    print(f"  mspUuid:              {parent_task_b['mspUuid']}")
                    
                    # Print errorMessages if status is FAILED
                    if parent_task_b.get('status') == 'FAILED' and 'errorMessages' in parent_task_b:
                        print(f"  Error Messages:")
                        for err_idx, err_msg in enumerate(parent_task_b['errorMessages'], 1):
                            print(f"    Error {err_idx}:")
                            print(f"      code:        {err_msg.get('code', 'N/A')}")
                            print(f"      errorGroup:  {err_msg.get('errorGroup', 'N/A')}")
                            print(f"      message:     {err_msg.get('message', 'N/A')}")
                            print(f"      severity:    {err_msg.get('severity', 'N/A')}")
                            print(f"      status:      {err_msg.get('status', 'N/A')}")
                    print("")
                
                # Print subtasks
                subtasks_b = [t for t in section_b_result['svcmgr_tasks'] if t['type'] == 'subtask']
                if subtasks_b:
                    print(f"SubTasks ({len(subtasks_b)}):")
                    print("")
                    for subtask in subtasks_b:
                        if 'error' in subtask:
                            print(f"SubTask {subtask['index']}:")
                            print(f"  extId: {subtask['extId']}")
                            print(f"  ERROR: {subtask['error']}")
                        else:
                            print(f"SubTask {subtask['index']}:")
                            print(f"  extId:                {subtask['extId']}")
                            print(f"  name:                 {subtask['name']}")
                            print(f"  operation:            {subtask['operation']}")
                            print(f"  operationDescription: {subtask['operationDescription']}")
                            print(f"  status:               {subtask['status']}")
                            print(f"  mspUuid:              {subtask['mspUuid']}")
                            
                            # Print errorMessages if status is FAILED
                            if subtask.get('status') == 'FAILED' and 'errorMessages' in subtask:
                                print(f"  Error Messages:")
                                for err_idx, err_msg in enumerate(subtask['errorMessages'], 1):
                                    print(f"    Error {err_idx}:")
                                    print(f"      code:        {err_msg.get('code', 'N/A')}")
                                    print(f"      errorGroup:  {err_msg.get('errorGroup', 'N/A')}")
                                    print(f"      message:     {err_msg.get('message', 'N/A')}")
                                    print(f"      severity:    {err_msg.get('severity', 'N/A')}")
                                    print(f"      status:      {err_msg.get('status', 'N/A')}")
                        print("")
                else:
                    print("No subtasks found")
            else:
                print("No task details available")
        else:
            if section_b_result:
                print("\n" + "=" * 80)
                print("SVC MGR (SECTION B - nc-cpaas): Service Manager Task Details")
                print("=" * 80)
                print("No parent task UUID found")
                print("=" * 80)
        
        # ======================================================================
        # STEP 14: Grep task IDs in svcmgr pod logs (Section A)
        # ======================================================================
        if svcmgr_tasks_a:
            print("\n" + "=" * 80)
            print("STEP 14: Searching task IDs in svcmgr pod logs (Section A)")
            print("=" * 80)
            print(f"Application: {next_app_name}")
            print(f"Path: {SVC_MGR_POD_LOG_PATH}")
            print(f"Pattern: {SVC_MGR_POD_LOG_PATTERN}")
            print("")
            
            # Collect all task IDs (parent + all subtasks)
            all_task_ids = []
            if parent_task_uuid_a:
                all_task_ids.append(('parent', parent_task_uuid_a))
            
            for task in svcmgr_tasks_a:
                if task['type'] == 'subtask' and 'extId' in task and task['extId'] != 'N/A':
                    all_task_ids.append(('subtask', task['extId']))
            
            print(f"Searching for {len(all_task_ids)} task IDs in svcmgr pod logs...")
            print("")
            
            for task_type, task_id in all_task_ids:
                print(f"Searching for {task_type} task ID: {task_id}")
                
                # Grep task ID in svcmgr pod logs (handling compressed/uncompressed)
                pod_log_output = grep_with_xz(task_id, SVC_MGR_POD_LOG_PATTERN, SVC_MGR_POD_LOG_PATH)
                
                # Save to file named with task ID
                task_log_file = run_dir / f"section_a_svcmgr_pod_logs_{task_id}.txt"
                with open(task_log_file, 'w', encoding='utf-8') as f:
                    f.write(pod_log_output)
                
                pod_log_lines = [l.strip() for l in pod_log_output.split('\n') if l.strip()]
                print(f"  ✓ Found {len(pod_log_lines)} lines → saved to {task_log_file}")
            
            print("")
            print("=" * 80)
            
            # ======================================================================
            # STEP 14b: Grep mspUuid from parent task and subtasks in msp_controller.out* files (Section A)
            # ======================================================================
            print("\n" + "=" * 80)
            print("STEP 14b: Searching mspUuid from parent task and subtasks in msp_controller.out* files (Section A)")
            print("=" * 80)
            print(f"Path: {MSP_CONTROLLER_LOG_PATH}")
            print(f"Pattern: {MSP_CONTROLLER_LOG_PATTERN}")
            print("")
            
            # Collect all mspUuid from parent task and subtasks
            all_msp_uuids = []
            
            # Add parent task mspUuid
            parent_task_a = next((t for t in svcmgr_tasks_a if t['type'] == 'parent'), None)
            if parent_task_a and 'mspUuid' in parent_task_a and parent_task_a['mspUuid'] != 'N/A':
                all_msp_uuids.append(('parent', parent_task_a['mspUuid'], parent_task_a.get('extId', 'N/A')))
            
            # Add subtask mspUuids
            for task in svcmgr_tasks_a:
                if task['type'] == 'subtask' and 'mspUuid' in task and task['mspUuid'] != 'N/A':
                    all_msp_uuids.append(('subtask', task['index'], task['mspUuid'], task.get('extId', 'N/A')))
            
            if all_msp_uuids:
                print(f"Searching for {len(all_msp_uuids)} mspUuid values in msp_controller logs...")
                print("")
                
                for msp_entry in all_msp_uuids:
                    if msp_entry[0] == 'parent':
                        task_type, msp_uuid, task_extid = msp_entry
                        print(f"Searching for Parent Task mspUuid: {msp_uuid}")
                    else:
                        task_type, subtask_idx, msp_uuid, task_extid = msp_entry
                        print(f"Searching for SubTask {subtask_idx} mspUuid: {msp_uuid}")
                    
                    # Grep mspUuid in msp_controller logs (handling compressed/uncompressed)
                    msp_log_output = grep_with_xz(msp_uuid, MSP_CONTROLLER_LOG_PATTERN, MSP_CONTROLLER_LOG_PATH)
                    
                    # Save to file named with mspUuid
                    if msp_entry[0] == 'parent':
                        msp_log_file = run_dir / f"section_a_msp_controller_logs_parent_{msp_uuid}.txt"
                    else:
                        msp_log_file = run_dir / f"section_a_msp_controller_logs_{msp_uuid}.txt"
                    with open(msp_log_file, 'w', encoding='utf-8') as f:
                        f.write(msp_log_output)
                    
                    msp_log_lines = [l.strip() for l in msp_log_output.split('\n') if l.strip()]
                    print(f"  ✓ Found {len(msp_log_lines)} lines → saved to {msp_log_file}")
            else:
                print("No mspUuid values found in parent task or subtasks")
            
            print("")
            print("=" * 80)
        
        # ======================================================================
        # STEP 14c: Grep task IDs in svcmgr pod logs (Section B - nc-cpaas)
        # ======================================================================
        if section_b_result and section_b_result['svcmgr_tasks']:
            print("\n" + "=" * 80)
            print("STEP 14c: Searching task IDs in svcmgr pod logs (Section B - nc-cpaas)")
            print("=" * 80)
            print(f"Application: nc-cpaas")
            print(f"Path: {SVC_MGR_POD_LOG_PATH}")
            print(f"Pattern: {SVC_MGR_POD_LOG_PATTERN}")
            print("")
            
            # Collect all task IDs (parent + all subtasks)
            all_task_ids_b = []
            if section_b_result['parent_task_uuid']:
                all_task_ids_b.append(('parent', section_b_result['parent_task_uuid']))
            
            for task in section_b_result['svcmgr_tasks']:
                if task['type'] == 'subtask' and 'extId' in task and task['extId'] != 'N/A':
                    all_task_ids_b.append(('subtask', task['extId']))
            
            print(f"Searching for {len(all_task_ids_b)} task IDs in svcmgr pod logs...")
            print("")
            
            for task_type, task_id in all_task_ids_b:
                print(f"Searching for {task_type} task ID: {task_id}")
                
                # Grep task ID in svcmgr pod logs (handling compressed/uncompressed)
                pod_log_output = grep_with_xz(task_id, SVC_MGR_POD_LOG_PATTERN, SVC_MGR_POD_LOG_PATH)
                
                # Save to file named with task ID
                task_log_file = run_dir / f"section_b_svcmgr_pod_logs_{task_id}.txt"
                with open(task_log_file, 'w', encoding='utf-8') as f:
                    f.write(pod_log_output)
                
                pod_log_lines = [l.strip() for l in pod_log_output.split('\n') if l.strip()]
                print(f"  ✓ Found {len(pod_log_lines)} lines → saved to {task_log_file}")
            
            print("")
            print("=" * 80)
            
            # ======================================================================
            # STEP 14d: Grep mspUuid from parent task and subtasks in msp_controller.out* files (Section B)
            # ======================================================================
            print("\n" + "=" * 80)
            print("STEP 14d: Searching mspUuid from parent task and subtasks in msp_controller.out* files (Section B)")
            print("=" * 80)
            print(f"Path: {MSP_CONTROLLER_LOG_PATH}")
            print(f"Pattern: {MSP_CONTROLLER_LOG_PATTERN}")
            print("")
            
            # Collect all mspUuid from parent task and subtasks
            all_msp_uuids_b = []
            
            # Add parent task mspUuid
            parent_task_b = next((t for t in section_b_result['svcmgr_tasks'] if t['type'] == 'parent'), None)
            if parent_task_b and 'mspUuid' in parent_task_b and parent_task_b['mspUuid'] != 'N/A':
                all_msp_uuids_b.append(('parent', parent_task_b['mspUuid'], parent_task_b.get('extId', 'N/A')))
            
            # Add subtask mspUuids
            for task in section_b_result['svcmgr_tasks']:
                if task['type'] == 'subtask' and 'mspUuid' in task and task['mspUuid'] != 'N/A':
                    all_msp_uuids_b.append(('subtask', task['index'], task['mspUuid'], task.get('extId', 'N/A')))
            
            if all_msp_uuids_b:
                print(f"Searching for {len(all_msp_uuids_b)} mspUuid values in msp_controller logs...")
                print("")
                
                for msp_entry in all_msp_uuids_b:
                    if msp_entry[0] == 'parent':
                        task_type, msp_uuid, task_extid = msp_entry
                        print(f"Searching for Parent Task mspUuid: {msp_uuid}")
                    else:
                        task_type, subtask_idx, msp_uuid, task_extid = msp_entry
                        print(f"Searching for SubTask {subtask_idx} mspUuid: {msp_uuid}")
                    
                    # Grep mspUuid in msp_controller logs (handling compressed/uncompressed)
                    msp_log_output = grep_with_xz(msp_uuid, MSP_CONTROLLER_LOG_PATTERN, MSP_CONTROLLER_LOG_PATH)
                    
                    # Save to file named with mspUuid
                    if msp_entry[0] == 'parent':
                        msp_log_file = run_dir / f"section_b_msp_controller_logs_parent_{msp_uuid}.txt"
                    else:
                        msp_log_file = run_dir / f"section_b_msp_controller_logs_{msp_uuid}.txt"
                    with open(msp_log_file, 'w', encoding='utf-8') as f:
                        f.write(msp_log_output)
                    
                    msp_log_lines = [l.strip() for l in msp_log_output.split('\n') if l.strip()]
                    print(f"  ✓ Found {len(msp_log_lines)} lines → saved to {msp_log_file}")
            else:
                print("No mspUuid values found in parent task or subtasks")
            
            print("")
            print("=" * 80)
        
        # ======================================================================
        # COMPREHENSIVE REPORT
        # ======================================================================
        print("\n" + "=" * 80)
        print("COMPREHENSIVE REPORT: Complete Analysis Flow")
        print("=" * 80)
        print("")
        
        print("=" * 80)
        print("PART A: STYX LOG ANALYSIS")
        print("=" * 80)
        print(f"Oldest APP-CREATE-START Entry:")
        print(f"  UUID:        {oldest['uuid']}")
        print(f"  Timestamp:   {oldest['timestamp']}")
        print(f"  BP:          {oldest['bp']}")
        print(f"  cr:          {oldest['cr']}")
        print(f"  pr:          {oldest['pr']}")
        print(f"  rr:          {oldest['rr']}")
        print(f"  Application: {oldest_app_name}")
        if oldest_mapped['end']:
            print(f"  APP-CREATE-END: Found")
            print(f"    END Timestamp: {oldest_mapped['end']['timestamp']}")
        else:
            print(f"  APP-CREATE-END: MISSING")
        print("")
        
        print(f"Next Application (used for analysis):")
        print(f"  Application: {next_app_name}")
        print(f"  RR UUID:     {next_rr_uuid}")
        print("")
        
        print("=" * 80)
        print("PART B: DURGA LOG ANALYSIS")
        print("=" * 80)
        print(f"RR UUID searched: {rr_uuid}")
        print(f"Total RR UUID matches: {len(rr_lines)}")
        print(f"TRLID entries found: {len(trlid_lines)}")
        if context_uuid:
            print(f"Context UUID extracted: {context_uuid}")
        print("")
        
        print("=" * 80)
        print("PART C: INDRA LOG ANALYSIS")
        print("=" * 80)
        print(f"Context UUID searched: {context_uuid}")
        print(f"Total indra matches: {len(indra_lines)}")
        print(f"smsp_app_uuid entries found: {len(smsp_uuids)}")
        if smsp_uuids:
            print(f"smsp_app_uuid values: {', '.join(smsp_uuids)}")
        print("")
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Oldest Application: {oldest_app_name}")
        if next_app_name:
            print(f"Next Application: {next_app_name}")
        print(f"RR UUID (from next app): {rr_uuid}")
        print(f"Context UUID: {context_uuid}")
        if smsp_uuids:
            print(f"smsp_app_uuid: {smsp_uuids[0] if smsp_uuids else 'N/A'}")
        
        # Add Service Manager Task Details to Summary
        print("\n" + "=" * 80)
        print("SERVICE MANAGER TASK DETAILS (Summary)")
        print("=" * 80)
        
        # Section A (if available)
        if section_a_result and parent_task_uuid_a and svcmgr_tasks_a:
            parent_task_a = next((t for t in svcmgr_tasks_a if t['type'] == 'parent'), None)
            if parent_task_a:
                print(f"\nSection A - Parent Task:")
                print(f"  extId:                {parent_task_a['extId']}")
                print(f"  name:                 {parent_task_a['name']}")
                print(f"  operation:            {parent_task_a['operation']}")
                print(f"  status:               {parent_task_a['status']}")
                
                # Print errorMessages if status is FAILED
                if parent_task_a.get('status') == 'FAILED' and 'errorMessages' in parent_task_a:
                    print(f"  Error Messages:")
                    for err_idx, err_msg in enumerate(parent_task_a['errorMessages'], 1):
                        print(f"    Error {err_idx}:")
                        print(f"      code:        {err_msg.get('code', 'N/A')}")
                        print(f"      errorGroup:  {err_msg.get('errorGroup', 'N/A')}")
                        print(f"      message:     {err_msg.get('message', 'N/A')}")
                        print(f"      severity:    {err_msg.get('severity', 'N/A')}")
                        print(f"      status:      {err_msg.get('status', 'N/A')}")
                
                # Check for failed subtasks
                subtasks_a = [t for t in svcmgr_tasks_a if t['type'] == 'subtask']
                failed_subtasks_a = [t for t in subtasks_a if t.get('status') == 'FAILED']
                if failed_subtasks_a:
                    print(f"\n  Failed SubTasks ({len(failed_subtasks_a)}):")
                    for subtask in failed_subtasks_a:
                        print(f"    SubTask {subtask['index']}: {subtask.get('name', 'N/A')} - {subtask.get('extId', 'N/A')}")
                        if 'errorMessages' in subtask:
                            for err_idx, err_msg in enumerate(subtask['errorMessages'], 1):
                                print(f"      Error {err_idx}: {err_msg.get('message', 'N/A')}")
        
        # Section B (if available)
        if section_b_result and section_b_result.get('parent_task_uuid') and section_b_result.get('svcmgr_tasks'):
            parent_task_b = next((t for t in section_b_result['svcmgr_tasks'] if t['type'] == 'parent'), None)
            if parent_task_b:
                print(f"\nSection B (nc-cpaas) - Parent Task:")
                print(f"  extId:                {parent_task_b['extId']}")
                print(f"  name:                 {parent_task_b['name']}")
                print(f"  operation:            {parent_task_b['operation']}")
                print(f"  status:               {parent_task_b['status']}")
                
                # Print errorMessages if status is FAILED
                if parent_task_b.get('status') == 'FAILED' and 'errorMessages' in parent_task_b:
                    print(f"  Error Messages:")
                    for err_idx, err_msg in enumerate(parent_task_b['errorMessages'], 1):
                        print(f"    Error {err_idx}:")
                        print(f"      code:        {err_msg.get('code', 'N/A')}")
                        print(f"      errorGroup:  {err_msg.get('errorGroup', 'N/A')}")
                        print(f"      message:     {err_msg.get('message', 'N/A')}")
                        print(f"      severity:    {err_msg.get('severity', 'N/A')}")
                        print(f"      status:      {err_msg.get('status', 'N/A')}")
                
                # Check for failed subtasks
                subtasks_b = [t for t in section_b_result['svcmgr_tasks'] if t['type'] == 'subtask']
                failed_subtasks_b = [t for t in subtasks_b if t.get('status') == 'FAILED']
                if failed_subtasks_b:
                    print(f"\n  Failed SubTasks ({len(failed_subtasks_b)}):")
                    for subtask in failed_subtasks_b:
                        print(f"    SubTask {subtask['index']}: {subtask.get('name', 'N/A')} - {subtask.get('extId', 'N/A')}")
                        if 'errorMessages' in subtask:
                            for err_idx, err_msg in enumerate(subtask['errorMessages'], 1):
                                print(f"      Error {err_idx}: {err_msg.get('message', 'N/A')}")
        
        # Oldest entry (STEP 3) - if available
        if oldest_debug_result and oldest_debug_result.get('parent_task_uuid') and oldest_debug_result.get('svcmgr_tasks'):
            parent_task_oldest = next((t for t in oldest_debug_result['svcmgr_tasks'] if t['type'] == 'parent'), None)
            if parent_task_oldest:
                print(f"\nOldest Entry ({oldest_app_name}) - Parent Task:")
                print(f"  extId:                {parent_task_oldest['extId']}")
                print(f"  name:                 {parent_task_oldest['name']}")
                print(f"  operation:            {parent_task_oldest['operation']}")
                print(f"  status:               {parent_task_oldest['status']}")
                
                # Print errorMessages if status is FAILED
                if parent_task_oldest.get('status') == 'FAILED' and 'errorMessages' in parent_task_oldest:
                    print(f"  Error Messages:")
                    for err_idx, err_msg in enumerate(parent_task_oldest['errorMessages'], 1):
                        print(f"    Error {err_idx}:")
                        print(f"      code:        {err_msg.get('code', 'N/A')}")
                        print(f"      errorGroup:  {err_msg.get('errorGroup', 'N/A')}")
                        print(f"      message:     {err_msg.get('message', 'N/A')}")
                        print(f"      severity:    {err_msg.get('severity', 'N/A')}")
                        print(f"      status:      {err_msg.get('status', 'N/A')}")
                
                # Check for failed subtasks
                subtasks_oldest = [t for t in oldest_debug_result['svcmgr_tasks'] if t['type'] == 'subtask']
                failed_subtasks_oldest = [t for t in subtasks_oldest if t.get('status') == 'FAILED']
                if failed_subtasks_oldest:
                    print(f"\n  Failed SubTasks ({len(failed_subtasks_oldest)}):")
                    for subtask in failed_subtasks_oldest:
                        print(f"    SubTask {subtask['index']}: {subtask.get('name', 'N/A')} - {subtask.get('extId', 'N/A')}")
                        if 'errorMessages' in subtask:
                            for err_idx, err_msg in enumerate(subtask['errorMessages'], 1):
                                print(f"      Error {err_idx}: {err_msg.get('message', 'N/A')}")
        
        print(f"\nFiles saved in: {run_dir}")
        print("=" * 80)
        
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        tee.file.close()

if __name__ == "__main__":
    main()

