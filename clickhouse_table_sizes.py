 2025-10-21 10:39:22,718Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'aiops_neuron' AND active = 1 GROUP BY table;
2025-10-21 10:39:23,385Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:23,386Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'aiops_neuron_raw' AND active = 1 GROUP BY table;
2025-10-21 10:39:24,039Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['aiops_neuron_raw', '19.11 MiB']]
[['aiops_neuron_raw', '19.11 MiB']]
2025-10-21 10:39:24,039Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_billing' AND active = 1 GROUP BY table;
2025-10-21 10:39:25,693Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:25,694Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_billing_local' AND active = 1 GROUP BY table;
2025-10-21 10:39:26,604Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['cg_nx_billing_local', '402.71 KiB']]
[['cg_nx_billing_local', '402.71 KiB']]
2025-10-21 10:39:26,605Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_billing_temp' AND active = 1 GROUP BY table;
2025-10-21 10:39:27,549Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['cg_nx_billing_temp', '402.71 KiB']]
[['cg_nx_billing_temp', '402.71 KiB']]
2025-10-21 10:39:27,550Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_categories_config' AND active = 1 GROUP BY table;
2025-10-21 10:39:28,174Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:28,175Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_categories_config_local' AND active = 1 GROUP BY table;
2025-10-21 10:39:29,215Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['cg_nx_metrics_categories_config_local', '209.66 KiB']]
[['cg_nx_metrics_categories_config_local', '209.66 KiB']]
2025-10-21 10:39:29,215Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_cluster_config' AND active = 1 GROUP BY table;
2025-10-21 10:39:29,937Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:29,937Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_cluster_config_local' AND active = 1 GROUP BY table;
2025-10-21 10:39:30,956Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['cg_nx_metrics_cluster_config_local', '53.45 KiB']]
[['cg_nx_metrics_cluster_config_local', '53.45 KiB']]
2025-10-21 10:39:30,956Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_cluster_hardware_config' AND active = 1 GROUP BY table;
2025-10-21 10:39:31,682Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:31,683Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_cluster_hardware_config_local' AND active = 1 GROUP BY table;
2025-10-21 10:39:32,597Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['cg_nx_metrics_cluster_hardware_config_local', '95.93 KiB']]
[['cg_nx_metrics_cluster_hardware_config_local', '95.93 KiB']]
2025-10-21 10:39:32,597Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_vm_config' AND active = 1 GROUP BY table;
2025-10-21 10:39:33,314Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:33,315Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'cg_nx_metrics_vm_config_local' AND active = 1 GROUP BY table;
2025-10-21 10:39:34,258Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['cg_nx_metrics_vm_config_local', '80.40 KiB']]
[['cg_nx_metrics_vm_config_local', '80.40 KiB']]
2025-10-21 10:39:34,259Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history' AND active = 1 GROUP BY table;
2025-10-21 10:39:34,954Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:34,955Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history_cluster_consolidated' AND active = 1 GROUP BY table;
2025-10-21 10:39:35,714Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:35,715Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history_disk_consolidated' AND active = 1 GROUP BY table;
2025-10-21 10:39:36,490Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:36,490Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history_labels_consolidated' AND active = 1 GROUP BY table;
2025-10-21 10:39:37,213Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:37,214Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history_node_consolidated' AND active = 1 GROUP BY table;
2025-10-21 10:39:37,860Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:37,861Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history_node_zk_consolidated' AND active = 1 GROUP BY table;
2025-10-21 10:39:38,479Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:38,480Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history_raw' AND active = 1 GROUP BY table;
2025-10-21 10:39:39,098Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:39,099Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'config_history_vm_consolidated' AND active = 1 GROUP BY table;
2025-10-21 10:39:39,730Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:39,731Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_cpu_remaining_capacity_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:40,364Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:40,365Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_cpu_remaining_capacity_pct_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:40,985Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:40,986Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_cpu_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:41,615Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:41,615Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_cpu_threads_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:42,234Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:42,235Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_dead_vm_storage_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:42,862Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:42,862Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_hypervisor_cpu_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:43,523Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:43,524Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_inactive_vm_memory_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:44,172Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:44,173Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_inactive_vm_storage_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:44,809Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:44,810Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_inactive_vm_vcpu_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:45,439Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:45,440Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_memory_non_overcommited_vm_count_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:46,068Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:46,069Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_memory_overcommited_vm_count_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:46,692Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:46,693Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_memory_remaining_capacity_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:47,332Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:47,333Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_memory_remaining_capacity_pct_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:48,005Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:48,007Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_overprovisioned_vm_memory_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:48,663Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:48,664Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_overprovisioned_vm_storage_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:49,294Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:49,295Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_overprovisioned_vm_vcpu_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:49,933Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:49,934Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_powered_off_vm_duration_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:50,594Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:50,595Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_powered_on_vm_count_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:51,226Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:51,227Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_storage_remaining_capacity_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:51,873Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:51,874Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_storage_remaining_capacity_pct_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:54,549Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:54,550Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_disk_size_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:55,562Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:55,563Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_filtered_memory_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:56,868Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:56,869Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_filtered_vcpu_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:58,212Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:58,213Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_memory_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:58,927Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:58,928Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_memory_size_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:39:59,559Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:39:59,560Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_storage_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:40:00,250Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:00,251Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_vcpu_gain_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:40:00,918Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:00,919Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_vcpus_sum_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:40:01,590Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:01,591Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'derived_metrics_vm_vcpus_to_cpus_ratio_parameterized_view' AND active = 1 GROUP BY table;
2025-10-21 10:40:02,217Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:02,217Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'expired_budget' AND active = 1 GROUP BY table;
2025-10-21 10:40:02,923Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:02,924Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'expired_budget_local' AND active = 1 GROUP BY table;
2025-10-21 10:40:03,644Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:03,645Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infra_configuration_history_common_distributed' AND active = 1 GROUP BY table;
2025-10-21 10:40:04,288Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:04,289Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infra_configuration_history_common_local' AND active = 1 GROUP BY table;
2025-10-21 10:40:05,263Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['infra_configuration_history_common_local', '634.46 KiB']]
[['infra_configuration_history_common_local', '634.46 KiB']]
2025-10-21 10:40:05,264Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infra_configuration_history_vm_distributed' AND active = 1 GROUP BY table;
2025-10-21 10:40:06,082Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:06,083Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infra_configuration_history_vm_local' AND active = 1 GROUP BY table;
2025-10-21 10:40:08,559Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['infra_configuration_history_vm_local', '1.21 MiB']]
[['infra_configuration_history_vm_local', '1.21 MiB']]
2025-10-21 10:40:08,559Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure' AND active = 1 GROUP BY table;
2025-10-21 10:40:09,542Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:09,543Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_cdc_local' AND active = 1 GROUP BY table;
2025-10-21 10:40:10,524Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['infrastructure_cdc_local', '111.22 MiB']]
[['infrastructure_cdc_local', '111.22 MiB']]
2025-10-21 10:40:10,525Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_historical_rollup_1hr' AND active = 1 GROUP BY table;
2025-10-21 10:40:11,154Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:11,154Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_historical_rollup_1hr_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:11,786Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['infrastructure_historical_rollup_1hr_raw', '669.84 KiB']]
[['infrastructure_historical_rollup_1hr_raw', '669.84 KiB']]
2025-10-21 10:40:11,787Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_latest' AND active = 1 GROUP BY table;
2025-10-21 10:40:12,446Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:12,447Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_latest_mview' AND active = 1 GROUP BY table;
2025-10-21 10:40:13,078Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:13,079Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_latest_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:13,775Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['infrastructure_latest_raw', '401.26 KiB']]
[['infrastructure_latest_raw', '401.26 KiB']]
2025-10-21 10:40:13,775Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:14,443Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['infrastructure_raw', '179.44 MiB']]
[['infrastructure_raw', '179.44 MiB']]
2025-10-21 10:40:14,443Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_raw_to_cdc_mview' AND active = 1 GROUP BY table;
2025-10-21 10:40:15,080Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:15,081Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_rollup_1hr' AND active = 1 GROUP BY table;
2025-10-21 10:40:15,776Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:15,777Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'infrastructure_rollup_1hr_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:16,429Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['infrastructure_rollup_1hr_raw', '30.11 MiB']]
[['infrastructure_rollup_1hr_raw', '30.11 MiB']]
2025-10-21 10:40:16,431Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'labels_history_distributed' AND active = 1 GROUP BY table;
2025-10-21 10:40:17,119Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:17,120Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'labels_history_local' AND active = 1 GROUP BY table;
2025-10-21 10:40:17,835Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['labels_history_local', '1012.13 KiB']]
[['labels_history_local', '1012.13 KiB']]
2025-10-21 10:40:17,835Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'ml_forecast_multi_cloud' AND active = 1 GROUP BY table;
2025-10-21 10:40:18,496Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:18,496Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'ml_forecast_multi_cloud_local' AND active = 1 GROUP BY table;
2025-10-21 10:40:20,569Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['ml_forecast_multi_cloud_local', '4.64 KiB']]
[['ml_forecast_multi_cloud_local', '4.64 KiB']]
2025-10-21 10:40:20,570Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'schema_migrations' AND active = 1 GROUP BY table;
2025-10-21 10:40:21,583Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: [['schema_migrations', '707.00 B']]
[['schema_migrations', '707.00 B']]
2025-10-21 10:40:21,584Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver' AND active = 1 GROUP BY table;
2025-10-21 10:40:23,608Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:23,609Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_cdc_local' AND active = 1 GROUP BY table;
2025-10-21 10:40:24,710Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:24,711Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_historical_rollup_1hr' AND active = 1 GROUP BY table;
2025-10-21 10:40:25,790Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:25,790Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_historical_rollup_1hr_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:26,954Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:26,955Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_latest' AND active = 1 GROUP BY table;
2025-10-21 10:40:27,945Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:27,945Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_latest_mview' AND active = 1 GROUP BY table;
2025-10-21 10:40:29,042Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:29,043Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_latest_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:30,170Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:30,171Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:30,901Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:30,902Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_raw_to_cdc_mview' AND active = 1 GROUP BY table;
2025-10-21 10:40:31,668Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:31,669Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_rollup_1hr' AND active = 1 GROUP BY table;
2025-10-21 10:40:32,380Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
2025-10-21 10:40:32,380Z INFO  clickhouse_connection.py:183  Executing query: SELECT table, formatReadableSize(sum(bytes_on_disk)) AS size_on_disk FROM system.parts WHERE database = 'ncm' AND table = 'sqlserver_rollup_1hr_raw' AND active = 1 GROUP BY table;
2025-10-21 10:40:33,005Z INFO  clickhouse_connection.py:187  Query executed successfully. Result: []
[]
