import json
import urllib3
import time
import warnings
import re
import random
import string
from logger_util import get_logger, LoggedRequests

# Disable all SSL warnings
urllib3.disable_warnings()
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Initialize logger
logger = get_logger(__file__, include_http_logs=True)
requests = LoggedRequests(logger)

c

def convert_to_case_insensitive_pattern(pattern):
    """Convert a string pattern to case-insensitive regex pattern.
    Example: 'tiny' -> '[t|T][i|I][n|N][y|Y]'
    """
    return ''.join([f'[{char.lower()}|{char.upper()}]' for char in pattern])

def generate_categories_mapping(vm_name, num_cats, num_vals_per_cat):
    """Generate categories_mapping dictionary based on number of categories and values per category.
    
    Args:
        vm_name: Name of the VM
        num_cats: Number of categories to create
        num_vals_per_cat: Number of values per category
    
    Returns:
        Dictionary with category keys and lists of values
    """
    categories_mapping = {}
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    logger.debug(f"Generated random suffix for {vm_name}: {random_suffix}")
    
    for cat_idx in range(1, num_cats + 1):
        category_key = f"{vm_name}_key{cat_idx}_{random_suffix}"
        category_values = [f"{vm_name}_value{cat_idx}_{val_idx}_{random_suffix}" for val_idx in range(1, num_vals_per_cat + 1)]
        categories_mapping[category_key] = category_values
        logger.debug(f"Generated category {cat_idx}: {category_key} with {len(category_values)} values")
    
    return categories_mapping

vm_name_filter = convert_to_case_insensitive_pattern(vm_name_pattern)

logger.info(f"Starting VM category creation and association process")
logger.info(f"Target VM pattern: {vm_name_pattern}")
logger.info(f"Number of categories per VM: {num_categories}")
logger.info(f"Number of values per category: {num_values_per_category}")
logger.info(f"Processing Prism Central IPs: {pc_ips}")

# Track overall statistics
total_vms_processed = 0
total_categories_created = 0
total_vms_failed = 0

for pc_ip in pc_ips:
    url = f"https://{pc_ip}:9440/api/prism/v4.2/config/categories"
    vm_list_group_url = f"https://{pc_ip}:9440/api/nutanix/v3/groups"
    vm_list_group_pay = {
        "entity_type": "mh_vm",
        "query_name": "",
        "grouping_attribute": " ",
        "group_count": 20,
        "group_offset": 0,
        "group_attributes": [],
        "group_member_count": 100,
        "group_member_offset": 0,
        "group_member_sort_attribute": "vm_name",
        "group_member_sort_order": "ASCENDING",
        "group_member_attributes": [
            {
                "attribute": "vm_name"
            },
            {
                "attribute": "power_state"
            },
            {
                "attribute": "num_vcpus"
            },
            {
                "attribute": "memory_size_bytes"
            },
            {
                "attribute": "ip_addresses"
            },
            {
                "attribute": "cluster_name"
            },
            {
                "attribute": "hypervisor_type"
            },
            {
                "attribute": "guest_os_name"
            },
            {
                "attribute": "project_name"
            },
            {
                "attribute": "owner_username"
            },
            {
                "attribute": "project_reference"
            },
            {
                "attribute": "owner_reference"
            },
            {
                "attribute": "categories"
            },
            {
                "attribute": "cluster"
            },
            {
                "attribute": "state"
            },
            {
                "attribute": "message"
            },
            {
                "attribute": "reason"
            },
            {
                "attribute": "is_cvm"
            },
            {
                "attribute": "is_acropolis_vm"
            },
            {
                "attribute": "ngt.installed_version"
            },
            {
                "attribute": "is_live_migratable"
            },
            {
                "attribute": "gpus_in_use"
            },
            {
                "attribute": "network_security_rule_id_list"
            },
            {
                "attribute": "zone_type"
            },
            {
                "attribute": "vm_annotation"
            },
            {
                "attribute": "vm_type"
            },
            {
                "attribute": "capacity.policy_anomaly_detail"
            },
            {
                "attribute": "capacity.policy_efficiency_detail"
            },
            {
                "attribute": "protection_type"
            },
            {
                "attribute": "memory_overcommit"
            },
            {
                "attribute": "ngt.guest_os"
            },
            {
                "attribute": "ngt.enabled_applications"
            },
            {
                "attribute": "ngt.cluster_version"
            },
            {
                "attribute": "node_name"
            },
            {
                "attribute": "node"
            },
            {
                "attribute": "is_agent_vm"
            },
            {
                "attribute": "volume_group"
            },
            {
                "attribute": "protection_policy_state"
            },
            {
                "attribute": "cbr_not_capable_reason"
            },
            {
                "attribute": "ngt.communication_active"
            },
            {
                "attribute": "ngt.communication_over_serial_port_active"
            },
            {
                "attribute": "vpc_name"
            },
            {
                "attribute": "ngt.enabled"
            },
            {
                "attribute": "ngt.iso_mounted"
            },
            {
                "attribute": "memory_usage_ppm"
            },
            {
                "attribute": "storage_cluster_uuid"
            },
            {
                "attribute": "vga_console_enabled"
            },
            {
                "attribute": "hydration_status"
            },
            {
                "attribute": "hydration_remaining_bytes"
            }
        ],
        "filter_criteria": f"vm_name==.*{vm_name_filter}.*"
    }
    headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM=',
                'Cookie': 'NTNX_IAM_SESSION=CgVhZG1pbhCo2qPIBhoHTWVyY3VyeSAAKig0NDlkMDQyMzM1Yzg3ZjY5ZmQ5OTIzNzI1YWZiNGZiZjFiZDhkMTE0|C5B+BUMKsrJC7cWgky2DByU3S7b7/a4Vy6gaysGPl/c=; NTNX_MERCURY_IAM_REFRESH_TOKEN=Chl4enFiY3Z0dnhmaGNwanNzYXNmZXdkcTQzEhlqenB6amJ6c2EydGRwZm9yZm56M2llNGxy; NTNX_MERCURY_IAM_SESSION=CgVhZG1pbhCo2qPIBhoHTWVyY3VyeSAAKig0NDlkMDQyMzM1Yzg3ZjY5ZmQ5OTIzNzI1YWZiNGZiZjFiZDhkMTE0|C5B+BUMKsrJC7cWgky2DByU3S7b7/a4Vy6gaysGPl/c='
            }
    continue_flag = False
    batch_count = 0

    logger.info(f"Processing Prism Central: {pc_ip}")
    for i in range(1):
        logger.info(f"Processing batch {i}")
        logger.info("-" * 50)
        # vm list
        vm_list_group_pay['group_member_offset'] = i * 20
        vm_list_group_response = requests.post(vm_list_group_url, headers=headers, data=json.dumps(vm_list_group_pay), verify=False)
        vm_list_group_response = json.loads(vm_list_group_response.content)
        vm_list = vm_list_group_response['group_results'][0]['entity_results']
        vm_count = 0
        for vm in vm_list:
            cluster_name = ""
            project_name = ""
            project_uuid = ""
            cluster_uuid = ""
            continue_flag = False
            for tm_data in vm['data']:
                try:
                    if tm_data['name'] == 'cluster_name':
                        cluster_name = tm_data['values'][0]['values'][0]
                    elif tm_data['name'] == 'project_name':
                        if len(tm_data['values']) == 0:
                            continue_flag = True
                            break
                        project_name = tm_data['values'][0]['values'][0]
                        
                    elif tm_data['name'] == 'project_reference':
                        project_uuid = tm_data['values'][0]['values'][0]
                    elif tm_data['name'] == 'cluster':
                        cluster_uuid = tm_data['values'][0]['values'][0]
                except Exception as e:
                    logger.error(f"Exception occurred: {e}")
                    logger.error(f"Error processing VM [{vm['data'][0]['values'][0]['values'][0]}]")
                    continue_flag = True
                    break
            if continue_flag:
                total_vms_failed += 1
                continue
            logger.info(f"VM Details - Cluster: {cluster_name}, Project: {project_name}, Project UUID: {project_uuid}, Cluster UUID: {cluster_uuid}")
            vm_count += 1
            total_vms_processed += 1
            logger.info(f"Processing VM {vm_count} of {len(vm_list)}")
            continue_flag = False
            vm_name = vm['data'][0]['values'][0]['values'][0]
            vm_uuid = vm['entity_id']
            logger.info(f"Processing VM: {vm_name} (UUID: {vm_uuid})")
            # create categories
            categories_mapping = generate_categories_mapping(vm_name, num_categories, num_values_per_category)
            logger.info(f"Generated categories mapping: {categories_mapping}")
            
            category_creation_count = 0
            cat_key_count = 0
            for category_key, category_values in categories_mapping.items():
                cat_key_count += 1
                logger.info(f"Creating category key: {category_key} with {len(category_values)} values")
                value_count = 0
                for category_value in category_values:
                    value_count += 1
                    category_creation_count += 1
                    logger.info(f"Processing cat {cat_key_count} - cat asso {value_count}")
                    
                    payload = json.dumps({
                        "key": category_key,
                        "value": category_value,
                        "type": "USER",
                        "description": "",
                        "$reserved": {
                        "$fv": "v4.r2"
                        },
                        "$objectType": "prism.v4.config.Category",
                        "$unknownFields": {}
                    })
                    response = requests.post(url, headers=headers, data=payload, verify=False)
                    
                    if response.status_code not in [200, 201, 409]:  # 409 might be duplicate category
                        logger.warning(f"Category creation returned status {response.status_code} for {category_key}:{category_value}")
                    else:
                        logger.debug(f"Successfully created category {category_key}:{category_value}")
            
            logger.info(f"Created {category_creation_count} categories for VM {vm_name}")
            total_categories_created += category_creation_count
            # vm categruy update
            update_pay = {
                "action_on_failure": "CONTINUE",
                "execution_order": "NON_SEQUENTIAL",
                "api_request_list": [
                    {
                        "operation": "PUT",
                        "path_and_params": f"/api/nutanix/v3/mh_vms/{vm_uuid}",
                        "body": {
                            "spec": {
                                "resources": {},
                                "cluster_reference": {
                                    "kind": "cluster",
                                    "name": cluster_name,
                                    "uuid": cluster_uuid
                                }
                            },
                            "api_version": "3.1",
                            "metadata": {
                                "kind": "mh_vm",
                                "project_reference": {
                                    "kind": "project",
                                    "name": project_name,
                                    "uuid": project_uuid
                                },
                                "uuid": vm_uuid,
                                "spec_version": 1,
                                "categories": {},
                                "categories_mapping": categories_mapping,
                                "creation_time": vm['data'][0]['values'][0]['values'][0],
                                "last_update_time": vm['data'][0]['values'][0]['values'][0],
                                "owner_reference": {
                                    "kind": "user",
                                    "name": "admin",
                                    "uuid": "00000000-0000-0000-0000-000000000000"
                                },
                                "use_categories_mapping": True
                            }
                        }
                    }
                ],
                "api_version": "3.0"
            }
            retry_count = 0
            logger.info(f"Starting VM category association for {vm_name}")
            
            while True and retry_count < 3:
                update_url = f"https://{pc_ip}:9440/api/nutanix/v3/batch"
                update_response = requests.post(update_url, headers=headers, data=json.dumps(update_pay), verify=False)
                
                if update_response.status_code != 200:
                    logger.error(f"Batch API returned status {update_response.status_code}: {update_response.content}")
                    break
                    
                update_response = json.loads(update_response.content)
                logger.debug(f"Batch API response: {update_response}")
                
                if update_response['api_response_list'][0]['status'] == '202':
                    logger.info(f"Successfully associated categories to VM {vm_name}")
                    break
                elif update_response['api_response_list'][0]['api_response']['message_list'][0]['reason'] == 'SPEC_VERSION_MISMATCH':
                    error_message = update_response['api_response_list'][0]['api_response']['message_list'][0]['message']
                    logger.warning(f"SPEC_VERSION_MISMATCH detected for {vm_name}: {error_message}")
                    # Extract required spec_version from error message: "required X"
                    match = re.search(r'required (\d+)', error_message)
                    if match:
                        required_spec_version = int(match.group(1))
                        logger.info(f"Updating spec_version to required value: {required_spec_version}")
                        update_pay['api_request_list'][0]['body']['metadata']['spec_version'] = required_spec_version
                        retry_count += 1
                        continue
                    else:
                        logger.error("Could not extract required spec_version from error message")
                        continue_flag = True
                        break
                else:
                    error_reason = update_response['api_response_list'][0]['api_response']['message_list'][0]['reason']
                    logger.error(f"Batch API error for {vm_name}: {error_reason}")
                    continue_flag = True
                    break
            if continue_flag:
                logger.warning(f"Skipping VM {vm_name} due to errors, waiting 10 seconds before continuing")
                total_vms_failed += 1
                time.sleep(10)
                continue
            
            logger.info(f"Completed processing VM {vm_name}, waiting 1 second before next VM")
            time.sleep(1)
            
        if continue_flag:
            logger.info(f"Taking 5 second break before processing next batch, current batch count: {batch_count}")
            time.sleep(5)
            continue
        batch_count += 1

logger.info("=" * 80)
logger.info("VM CATEGORY CREATION AND ASSOCIATION PROCESS COMPLETED")
logger.info("=" * 80)
logger.info(f"SUMMARY STATISTICS:")
logger.info(f"  Total VMs Processed: {total_vms_processed}")
logger.info(f"  Total VMs Failed: {total_vms_failed}")
logger.info(f"  Total Categories Created: {total_categories_created}")
logger.info(f"  Success Rate: {((total_vms_processed - total_vms_failed) / max(total_vms_processed, 1)) * 100:.1f}%")
logger.info("=" * 80)
logger.info("API METRICS SUMMARY:")
requests.print_report()
