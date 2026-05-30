#!/usr/bin/env python3
"""
Nutanix PE-PC Registration Script
This script registers Prism Elements (PE) to Prism Central (PC) and monitors the registration status.
"""

import requests
import json
import time
import sys
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

class PEPCRegistration:
    def __init__(self, pe_ip, pc_ip, pe_username="admin", pe_password="Nutanix.123", 
                 pc_username="admin", pc_password="Nutanix.123"):
        self.pe_ip = pe_ip
        self.pc_ip = pc_ip
        self.pe_username = pe_username
        self.pe_password = pe_password
        self.pc_username = pc_username
        self.pc_password = pc_password
        self.session = requests.Session()
        self.session.verify = False
        self.task_uuid = None
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] PE {self.pe_ip}: {message}")
        
    def test_connectivity(self):
        """Test connectivity to PE"""
        try:
            url = f"https://{self.pe_ip}:9440/PrismGateway/services/rest/v1/cluster"
            response = self.session.get(url, auth=(self.pe_username, self.pe_password), timeout=10)
            if response.status_code == 200:
                self.log("✅ Connectivity test successful")
                return True
            else:
                self.log(f"❌ Connectivity test failed: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Connectivity test failed: {str(e)}", "ERROR")
            return False
            
    def register_to_pc(self):
        """Register PE to PC"""
        try:
            url = f"https://{self.pe_ip}:9440/PrismGateway/services/rest/v1/multicluster/prism_central/register"
            
            payload = {
                "username": self.pc_username,
                "password": self.pc_password,
                "port": None,
                "ipAddresses": [self.pc_ip]
            }
            
            self.log(f"🔄 Starting registration to PC {self.pc_ip}")
            self.log(f"Registration URL: {url}")
            self.log(f"Payload: {json.dumps({**payload, 'password': '***'}, indent=2)}")
            
            response = self.session.post(
                url,
                json=payload,
                auth=(self.pe_username, self.pe_password),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.task_uuid = result.get("taskUuid")
                self.log(f"✅ Registration initiated successfully")
                self.log(f"Task UUID: {self.task_uuid}")
                return True
            else:
                self.log(f"❌ Registration failed: HTTP {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration failed: {str(e)}", "ERROR")
            return False
            
    def get_task_status(self):
        """Get registration task status"""
        if not self.task_uuid:
            self.log("❌ No task UUID available", "ERROR")
            return None
            
        try:
            url = f"https://{self.pe_ip}:9440/PrismGateway/services/rest/v1/progress_monitors"
            params = {
                "count": 500,
                "page": 1,
                "filterCriteria": f"uuid=={self.task_uuid}"
            }
            
            response = self.session.get(
                url,
                params=params,
                auth=(self.pe_username, self.pe_password),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                entities = result.get("entities", [])
                if entities:
                    task = entities[0]
                    return {
                        "status": task.get("status"),
                        "percentage": task.get("percentageCompleted", 0),
                        "task_name": task.get("taskName"),
                        "sub_task_message": task.get("subTaskMessage"),
                        "error_code": task.get("errorCode", 0)
                    }
                else:
                    self.log("❌ No task found with given UUID", "ERROR")
                    return None
            else:
                self.log(f"❌ Failed to get task status: HTTP {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Failed to get task status: {str(e)}", "ERROR")
            return None
            
    def monitor_registration(self, timeout_minutes=10):
        """Monitor registration progress"""
        if not self.task_uuid:
            self.log("❌ No task UUID to monitor", "ERROR")
            return False
            
        self.log(f"🔄 Monitoring registration progress (timeout: {timeout_minutes} minutes)")
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            status_info = self.get_task_status()
            
            if status_info:
                status = status_info["status"]
                percentage = status_info["percentage"]
                task_name = status_info["task_name"]
                
                self.log(f"📊 Status: {status} | Progress: {percentage}% | Task: {task_name}")
                
                if status == "succeeded":
                    self.log("✅ Registration completed successfully!")
                    return True
                elif status == "failed":
                    error_code = status_info.get("error_code", 0)
                    self.log(f"❌ Registration failed with error code: {error_code}", "ERROR")
                    return False
                elif status == "running":
                    self.log(f"🔄 Registration in progress: {percentage}%")
                else:
                    self.log(f"⚠️ Unknown status: {status}", "WARN")
            else:
                self.log("⚠️ Could not retrieve task status", "WARN")
                
            time.sleep(10)  # Check every 10 seconds
            
        self.log(f"⏰ Registration monitoring timed out after {timeout_minutes} minutes", "WARN")
        return False
        
    def register_and_monitor(self, timeout_minutes=10):
        """Complete registration process with monitoring"""
        self.log("=" * 60)
        self.log(f"Starting PE-PC registration process")
        self.log(f"PE: {self.pe_ip} -> PC: {self.pc_ip}")
        self.log("=" * 60)
        
        # Test connectivity
        if not self.test_connectivity():
            return False
            
        # Register to PC
        if not self.register_to_pc():
            return False
            
        # Monitor progress
        return self.monitor_registration(timeout_minutes)

def process_single_registration(pe_config):
    """Process a single PE registration"""
    pe_ip = pe_config["pe_ip"]
    pc_ip = pe_config["pc_ip"]
    pe_username = pe_config.get("pe_username", "admin")
    pe_password = pe_config.get("pe_password", "Nutanix.123")
    pc_username = pe_config.get("pc_username", "admin")
    pc_password = pe_config.get("pc_password", "Nutanix.123")
    timeout = pe_config.get("timeout_minutes", 10)
    
    registration = PEPCRegistration(
        pe_ip=pe_ip,
        pc_ip=pc_ip,
        pe_username=pe_username,
        pe_password=pe_password,
        pc_username=pc_username,
        pc_password=pc_password
    )
    
    success = registration.register_and_monitor(timeout)
    return {
        "pe_ip": pe_ip,
        "pc_ip": pc_ip,
        "success": success
    }

def parse_range(range_str, max_len):
    """Parse range string like '1-5' or '1,3,5' into list of indices"""
    if not range_str:
        return list(range(max_len))
    
    indices = []
    for part in range_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            indices.extend(range(start-1, min(end, max_len)))  # Convert to 0-based indexing
        else:
            idx = int(part) - 1  # Convert to 0-based indexing
            if 0 <= idx < max_len:
                indices.append(idx)
    return indices

def create_pe_pc_mappings(pe_list, pc_list, mapping_strategy="round-robin"):
    """Create PE-PC mappings based on strategy"""
    mappings = []
    
    if mapping_strategy == "round-robin":
        # Distribute PEs across PCs in round-robin fashion
        for i, pe_ip in enumerate(pe_list):
            pc_ip = pc_list[i % len(pc_list)]
            mappings.append((pe_ip, pc_ip))
    
    elif mapping_strategy == "sequential":
        # Map PEs to PCs sequentially (multiple PEs per PC)
        pes_per_pc = len(pe_list) // len(pc_list) + (1 if len(pe_list) % len(pc_list) else 0)
        for i, pe_ip in enumerate(pe_list):
            pc_idx = i // pes_per_pc
            if pc_idx < len(pc_list):
                pc_ip = pc_list[pc_idx]
                mappings.append((pe_ip, pc_ip))
    
    elif mapping_strategy == "random":
        # Random mapping (with potential duplicates)
        import random
        for pe_ip in pe_list:
            pc_ip = random.choice(pc_list)
            mappings.append((pe_ip, pc_ip))
    
    return mappings

def main():
    # Predefined PE and PC lists
    PE_LIST = ["10.115.150.117", "10.115.150.217", "10.115.150.135", "10.115.150.26", "10.115.150.157", 
               "10.115.150.151", "10.115.151.14", "10.115.150.221", "10.115.151.21", "10.115.151.24", 
               "10.122.30.193", "10.122.31.48", "10.122.31.44", "10.122.30.153", "10.122.30.249", 
               "10.122.30.167", "10.122.31.40", "10.122.30.220", "10.122.30.24", "10.122.30.181"]
    
    PC_LIST = ["10.122.28.13", "10.122.28.15", "10.122.28.20", "10.122.28.22", "10.122.28.23", 
               "10.122.28.27", "10.122.28.28", "10.122.28.32", "10.122.28.71", "10.122.28.73", 
               "10.122.28.177", "10.122.28.179", "10.122.28.181", "10.122.28.183", "10.122.28.185", 
               "10.122.28.187", "10.122.28.190", "10.122.28.192", "10.122.27.185", "10.122.28.218"]

    parser = argparse.ArgumentParser(description="Nutanix PE-PC Registration Script")
    parser.add_argument("--config", "-c", help="JSON config file with PE-PC mappings")
    parser.add_argument("--pe", help="Single PE IP address")
    parser.add_argument("--pc", help="Single PC IP address")
    parser.add_argument("--use-lists", action="store_true", help="Use predefined PE-PC lists for bulk registration")
    parser.add_argument("--mapping", choices=["round-robin", "sequential", "random"], default="round-robin", 
                       help="PE-PC mapping strategy (default: round-robin)")
    parser.add_argument("--pe-range", help="PE range (e.g., 1-5 for first 5 PEs from list)")
    parser.add_argument("--pc-range", help="PC range (e.g., 1-3 for first 3 PCs from list)")
    parser.add_argument("--pe-user", default="admin", help="PE username (default: admin)")
    parser.add_argument("--pe-pass", default="Nutanix.123", help="PE password (default: Nutanix.123)")
    parser.add_argument("--pc-user", default="admin", help="PC username (default: admin)")
    parser.add_argument("--pc-pass", default="Nutanix.123", help="PC password (default: Nutanix.123)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in minutes (default: 10)")
    parser.add_argument("--parallel", type=int, default=5, help="Max parallel registrations (default: 5)")
    
    args = parser.parse_args()

    # Configuration examples
    if not args.config and not (args.pe and args.pc) and not args.use_lists:
        print("=" * 80)
        print("  Nutanix PE-PC Registration Script")
        print("=" * 80)
        print()
        print("Available PEs:", len(PE_LIST))
        print("Available PCs:", len(PC_LIST))
        print()
        print("Usage examples:")
        print()
        print("1. Single PE-PC registration:")
        print(f"   python3 {sys.argv[0]} --pe 10.115.150.117 --pc 10.122.28.13")
        print()
        print("2. Use predefined lists (all PEs to all PCs round-robin):")
        print(f"   python3 {sys.argv[0]} --use-lists")
        print()
        print("3. Use predefined lists with range (first 5 PEs to first 3 PCs):")
        print(f"   python3 {sys.argv[0]} --use-lists --pe-range 1-5 --pc-range 1-3")
        print()
        print("4. Use predefined lists with specific mapping:")
        print(f"   python3 {sys.argv[0]} --use-lists --mapping sequential --parallel 3")
        print()
        print("5. Multiple registrations from config file:")
        print(f"   python3 {sys.argv[0]} --config pe_pc_config.json")
        print()
        print("6. With custom credentials:")
        print(f"   python3 {sys.argv[0]} --pe 10.115.150.117 --pc 10.122.28.13 \\")
        print("                        --pe-user admin --pe-pass MyPassword123 \\")
        print("                        --pc-user admin --pc-pass MyPCPassword123")
        print()
        print("Mapping strategies:")
        print("  - round-robin: Distribute PEs evenly across PCs")
        print("  - sequential: Group PEs to PCs sequentially")
        print("  - random: Random PE-PC assignments")
        print()
        print("Range format:")
        print("  - '1-5': Items 1 through 5")
        print("  - '1,3,5': Specific items 1, 3, and 5")
        print("  - '1-3,7-9': Items 1-3 and 7-9")
        print()
        print("Config file format (pe_pc_config.json):")
        print(json.dumps({
            "registrations": [
                {
                    "pe_ip": "10.115.150.117",
                    "pc_ip": "10.122.28.13",
                    "pe_username": "admin",
                    "pe_password": "Nutanix.123",
                    "pc_username": "admin", 
                    "pc_password": "Nutanix.123",
                    "timeout_minutes": 10
                },
                {
                    "pe_ip": "10.115.150.217",
                    "pc_ip": "10.122.28.15",
                    "pe_username": "admin",
                    "pe_password": "Nutanix.234",
                    "pc_username": "admin",
                    "pc_password": "Nutanix.234",
                    "timeout_minutes": 15
                }
            ]
        }, indent=4))
        print()
        return 1
    
    registrations = []
    registrations = []
    
    # Single registration
    if args.pe and args.pc:
        registrations.append({
            "pe_ip": args.pe,
            "pc_ip": args.pc,
            "pe_username": args.pe_user,
            "pe_password": args.pe_pass,
            "pc_username": args.pc_user,
            "pc_password": args.pc_pass,
            "timeout_minutes": args.timeout
        })
    
    # Use predefined lists
    elif args.use_lists:
        # Parse ranges
        pe_indices = parse_range(args.pe_range, len(PE_LIST))
        pc_indices = parse_range(args.pc_range, len(PC_LIST))
        
        # Get selected PEs and PCs
        selected_pes = [PE_LIST[i] for i in pe_indices]
        selected_pcs = [PC_LIST[i] for i in pc_indices]
        
        print(f"Selected PEs ({len(selected_pes)}): {selected_pes[:5]}{'...' if len(selected_pes) > 5 else ''}")
        print(f"Selected PCs ({len(selected_pcs)}): {selected_pcs[:5]}{'...' if len(selected_pcs) > 5 else ''}")
        print(f"Mapping strategy: {args.mapping}")
        print()
        
        # Create mappings
        pe_pc_mappings = create_pe_pc_mappings(selected_pes, selected_pcs, args.mapping)
        
        # Create registration configs
        for pe_ip, pc_ip in pe_pc_mappings:
            registrations.append({
                "pe_ip": pe_ip,
                "pc_ip": pc_ip,
                "pe_username": args.pe_user,
                "pe_password": args.pe_pass,
                "pc_username": args.pc_user,
                "pc_password": args.pc_pass,
                "timeout_minutes": args.timeout
            })
        
        # Show mapping preview
        print("PE-PC Mappings:")
        for i, (pe_ip, pc_ip) in enumerate(pe_pc_mappings[:10], 1):  # Show first 10
            print(f"  {i:2d}. PE {pe_ip} -> PC {pc_ip}")
        if len(pe_pc_mappings) > 10:
            print(f"  ... and {len(pe_pc_mappings) - 10} more mappings")
        print()
    
    # Config file
    elif args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
                registrations = config.get("registrations", [])
        except Exception as e:
            print(f"❌ Error reading config file: {e}")
            return 1
    
    if not registrations:
        print("❌ No registrations configured")
        return 1
    
    print("=" * 80)
    print("  Starting PE-PC Registration Process")
    print(f"  Total registrations: {len(registrations)}")
    print(f"  Max parallel jobs: {args.parallel}")
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Process registrations in parallel
    results = []
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        future_to_config = {
            executor.submit(process_single_registration, config): config 
            for config in registrations
        }
        
        for future in as_completed(future_to_config):
            result = future.result()
            results.append(result)
    
    # Final summary
    print()
    print("=" * 80)
    print("  FINAL SUMMARY")
    print(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"Total registrations: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print()
        print("✅ Successful registrations:")
        for result in successful:
            print(f"  - PE {result['pe_ip']} -> PC {result['pc_ip']}")
    
    if failed:
        print()
        print("❌ Failed registrations:")
        for result in failed:
            print(f"  - PE {result['pe_ip']} -> PC {result['pc_ip']}")
    
    print("=" * 80)
    
    return 0 if len(failed) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())