#!/usr/bin/env python3
import json

# Raw data from the ClickHouse query results
table_data = [
    ['aiops_neuron_raw', '19.11 MiB'],
    ['cg_nx_billing_local', '402.71 KiB'],
    ['cg_nx_billing_temp', '402.71 KiB'],
    ['cg_nx_metrics_categories_config_local', '209.66 KiB'],
    ['cg_nx_metrics_cluster_config_local', '53.45 KiB'],
    ['cg_nx_metrics_cluster_hardware_config_local', '95.93 KiB'],
    ['cg_nx_metrics_vm_config_local', '80.40 KiB'],
    ['infra_configuration_history_common_local', '634.46 KiB'],
    ['infra_configuration_history_vm_local', '1.21 MiB'],
    ['infrastructure_cdc_local', '111.22 MiB'],
    ['infrastructure_historical_rollup_1hr_raw', '669.84 KiB'],
    ['infrastructure_latest_raw', '401.26 KiB'],
    ['infrastructure_raw', '179.44 MiB'],
    ['infrastructure_rollup_1hr_raw', '30.11 MiB'],
    ['labels_history_local', '1012.13 KiB'],
    ['ml_forecast_multi_cloud_local', '4.64 KiB'],
    ['schema_migrations', '707.00 B']
]

# Convert to JSON format - Option 1: Array of objects
json_array = []
for table_name, size in table_data:
    json_array.append({
        "table": table_name,
        "size_on_disk": size
    })

# Convert to JSON format - Option 2: Dictionary with table names as keys
json_dict = {}
for table_name, size in table_data:
    json_dict[table_name] = size

# Print both formats
print("=== JSON Array Format ===")
print(json.dumps(json_array, indent=2))

print("\n=== JSON Dictionary Format ===")
print(json.dumps(json_dict, indent=2))

# Save to files
with open('/home/mohan.as/mohan_helpers/table_sizes_array.json', 'w') as f:
    json.dump(json_array, f, indent=2)

with open('/home/mohan.as/mohan_helpers/table_sizes_dict.json', 'w') as f:
    json.dump(json_dict, f, indent=2)

print("\n=== Files saved ===")
print("- table_sizes_array.json (array format)")
print("- table_sizes_dict.json (dictionary format)")

