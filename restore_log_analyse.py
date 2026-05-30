import re
import requests
from collections import defaultdict 

d1 = """Total	1692.2	2113622
nucalm_task	187.062	871774
nucalm_variable	449.83	351115
nucalm_runbook	74.4639	347027
nucalm_action	587.623	326026
event	13.9245	64893
nucalm_run_log	76.6515	23347
nucalm_secret	26.1325	22013
nucalm_lifecycle	14.5889	11716
task	53.6613	11401
category_association	2.43266	11337
nucalm_config_spec	18.3902	9412
nucalm_credential	6.7243	5345
nucalm_back_filling_service_sync_status	6.968	4439
abac_entity_capability	10.5331	3751
nucalm_substrate_cfg	8.58414	3141
nucalm_service_cfg	4.36849	2870
nucalm_package_cfg	4.26828	2861
nucalm_app_blueprint	14.9882	2856
nucalm_application_cfg	6.54028	2844
nucalm_deployment_cfg	4.96746	2770
nucalm_substrate	9.92011	2443
nucalm_deployment_element	4.01913	2400
nucalm_service	3.99829	2374
nucalm_package	3.84512	2357
nucalm_substrate_element	8.71556	2355
nucalm_app_profile_instance	51.6389	2351
nucalm_app_protection_status	4.30753	2349
nucalm_application	6.28903	2336
nucalm_service_element	3.56796	2332
nucalm_deployment	4.72939	2324
nucalm_package_element	3.73071	2323
nucalm_app_beam_status	3.17323	2269
stig_report_details	0.136685	637
audit	0.129604	604
licensing_feature	0.7845	526
alert_check_schema	1.62764	525
intent_spec	3.76888	417
domain	0.47165	344
permission	0.661981	275
stig_rule	0.285311	122
ncc_error_codes	0.0868082	119
audit_event_schema	0.292492	113
nucalm_quota	0.0834389	92
nutanix_vulnerability_db	0.157911	78
category	0.0927401	56
abac_category	0.0797672	44
management_server_account	0.0982876	36
nucalm_provider	0.0814276	32
nucalm_resource_type	0.0931244	32
virtual_network	0.075531	32
nucalm_environment	0.183418	30
iamv2_backup_chunks	0.00600815	28
marketplace_item	1.12339	25
project_entity	0.330326	22
idempotency_entity	0.0358353	22
action_template	0.0567646	20
action_type	0.0387487	17
registry_db	0.0307741	15
virtual_disk	0.0627623	14
widget	0.0253267	13
nucalm_worker_state	0.0168619	13
alert	0.0027895	13
abac_category_key	0.0178328	12
report_config	0.0135708	6
pulse	0.00595665	5
msp_task	0.0385389	5
role	0.0976925	5
vulnerability_stats	0.0039978	4
certificates_entity	0.0186396	4
volume_group_config	0.0156231	4
report_template	0.00650787	4
volume_group_entity_capability	0.00393105	3
filter	0.00716591	3
panacea_follower	0.00473499	3
trigger_template	0.00579357	3
action_rule	0.0129881	3
panacea_leader	0.00523853	3
user_account_password_info	0.00364304	2
file_info	0.00176811	2
svcmgr_task	0.00441933	2
entity_snapshot	0.0514641	2
nc_service_version	0.00260544	2
virtual_switch	0.0132303	2
catalog_placement_policy_status_info	0.00259018	2
access_control_policy	0.00411892	2
virtual_nic	0.00879097	2
catalog_item_info	0.00564957	2
parcel_info	0.00205612	2
lcm_status_table	0.00268364	2
vm_recovery_point	0.000429153	2
license_cluster	0.00158596	2
mantle_secret	0.00181389	2
hardening_report_details	0.00208473	2
nucalm_service_version	0.00358009	2
storage_summary	0.0020113	1
xfit_policy	0.00188923	1
etcd_cluster_entity	0.0192862	1
nucalm_app_protection_rule	0.00148678	1
cluster_cpu_models	0.00124168	1
registry_entity	0.0282097	1
node	0.00836945	1
k8s_cluster_config	0.0152998	1
nucalm_consumption	0.0228415	1
svcmgr_history	0.00239182	1
vulcan_scheduled_entity	0.0016737	1
nucalm_app_protection_policy	0.00223351	1
msp_deployment_entity	0.00153065	1
image_info	0.00292492	1
vm_group	0.00122547	1
nucalm_license	0.00179863	1
recovery_point	0.000214577	1
replica_placement_policy	0.00121021	1
anduril_vm_info	0.00432301	1
infra_capabilities	0.00107384	1
cluster	0.0083065	1
nucalm_service_upgrade_history	0.00158501	1
pe_idf_sync_marker	0.00668907	1
post_paid_files_core	0.00285053	1
post_paid_aos_core	0.00684261	1
metrics_data_provider	0.00239086	1
scheduler_cluster_capabilities	0.00109673	1
vm	0.0113153	1
msp_config_entity	0.00631332	1
capabilities	0.00707817	1
cerebro_capabilities	0.00253868	1
license_details	0.00193405	1
password_manager_stats	0.000906944	1
license_metadata	0.00164795	1
k8s_cluster_task	0.00120354	1
domain_cloud_metadata	0.00108242	1
cluster_data_state	0.00147533	1
dashboard	0.00262737	1
entity_sync_stats_source	0.00131035	1
k8s_cluster_addon	0.0450172	1
trigger_type	0.00236034	1
entity_backup	0.00255585	1
k8s_cluster_worker	0.00134945	1
ipam	0.00220299	1
license_enforcement	0.00142479	1
cluster_resiliency_info	0.00347519	1
msp_entity_status	0.00160027	1
cluster_vulnerabilities	0.00108337	1
service_network_segmentation_info	0.00070858	1
nucalm_backup_restore_history	0.0011816	1
cluster_vm_capabilities	0.0016613	1
aos_networking_capabilities	0.00165176	1
pe_license_details	0.0014925	1
msp_entity	0.00785446	1"""

d2= """Total	1653.97	2065185
nucalm_task	182.715	851514
nucalm_variable	439.095	342712
nucalm_runbook	72.9973	340192
nucalm_action	573.179	318029
event	13.5705	63243
nucalm_run_log	76.3853	23306
nucalm_secret	25.3107	21219
nucalm_lifecycle	14.3076	11491
category_association	2.41227	11242
task	52.4466	11185
nucalm_config_spec	17.9982	9219
nucalm_credential	6.48899	5158
nucalm_back_filling_service_sync_status	6.61276	4213
abac_entity_capability	10.0005	3571
nucalm_substrate_cfg	8.35828	3046
nucalm_deployment_cfg	5.06547	2825
nucalm_service_cfg	4.23038	2779
nucalm_package_cfg	4.14187	2777
nucalm_application_cfg	6.24964	2716
nucalm_app_blueprint	14.2333	2713
nucalm_service_element	3.62306	2368
nucalm_package_element	3.80146	2367
nucalm_app_protection_status	4.28769	2338
nucalm_app_beam_status	3.25019	2324
nucalm_app_profile_instance	50.6279	2305
nucalm_application	6.19211	2300
nucalm_substrate_element	8.50221	2298
nucalm_deployment	4.66225	2291
nucalm_service	3.84511	2283
nucalm_substrate	9.25329	2279
nucalm_deployment_element	3.77295	2253
nucalm_package	3.62928	2225
alert_check_schema	1.90914	616
stig_report_details	0.130248	607
licensing_feature	0.857755	574
audit	0.120163	560
intent_spec	4.32026	408
domain	0.434611	316
permission	0.582096	241
stig_rule	0.288554	127
ncc_error_codes	0.0792847	109
nutanix_vulnerability_db	0.175323	87
nucalm_quota	0.0752764	83
audit_event_schema	0.202622	78
category	0.0843287	51
abac_category	0.0801573	45
virtual_network	0.082612	35
nucalm_provider	0.0855083	34
nucalm_resource_type	0.0942211	31
project_entity	0.470862	31
iamv2_backup_chunks	0.00579357	27
marketplace_item	1.56067	24
idempotency_entity	0.039093	24
nucalm_environment	0.128399	21
alert	0.00450611	21
nucalm_worker_state	0.026	20
management_server_account	0.0527649	19
action_type	0.0371647	16
action_template	0.0429039	15
pulse	0.0130863	11
virtual_disk	0.0483761	11
registry_db	0.0207195	10
widget	0.017333	9
report_template	0.0151806	9
report_config	0.0160141	7
msp_task	0.0606556	6
abac_category_key	0.00877476	6
role	0.239928	5
iscsi_client_params	0.00809002	5
entity_sync_stats_source	0.00537872	4
panacea_follower	0.00631332	4
panacea_leader	0.00698471	4
stig_report	0.00597382	4
hardening_report_details	0.0031271	3
certificates_entity	0.011837	3
prism_notification_service_stats	0.00192261	3
prism_central_vm	0.00171661	3
iamv2_backups_metadata	0.00420284	3
virtual_nic	0.0148201	3
vulnerability_stats	0.00299835	3
nucalm_sync_status	0.00237656	2
replica_placement_policy	0.00242043	2
volume_group_entity_capability	0.0026207	2
host_nic	0.00455666	2
trigger_template	0.00391388	2
nucalm_service_version	0.00358009	2
action_rule	0.0101061	2
nucalm_service_upgrade_history	0.00317001	2
abac_user_capability	0.0288277	2
password_manager_stats	0.00181389	2
nucalm_backup_restore_history	0.0023632	2
container	0.0135212	2
trigger_type	0.00424957	2
msp_app	0.0235376	2
mercury_authn_cookie_info	0.00991058	2
nucalm_price_item_status	0.00271416	2
flow_migration_config	0.000807762	1
disk	0.00749969	1
security_dashboard_info	0.00103569	1
xi_tenant	0.00111198	1
image_info	0.00290966	1
xfit_policy	0.00193405	1
vm	0.0124865	1
memory_model	0.00174522	1
svcmgr_app	0.00220966	1
mantle_secret	0.000945091	1
entity_sync_rule	0.00112724	1
cluster	0.00659657	1
session_key	0.00219536	1
nc_service_version	0.00131035	1
file_info	0.000884056	1
pc_idf_sync_marker	0.00662136	1
anduril_vm_info	0.00471973	1
cluster_vulnerabilities	0.00200653	1
dashboard	0.00224113	1
license_info	0.000747681	1
recovery_point	0.000214577	1
node_entity	0.0295658	1
pc_licenses_sync	0.00135612	1
availability_zone_physical	0.00171375	1
nucalm_feature	0.00105953	1
distributed_virtual_switch	0.00248241	1
domain_resiliency_info	0.00241089	1
access_control_policy	0.00207806	1
metrics_data_provider	0.00258923	1
parcel_info	0.00102806	1
nic_team	0.00257015	1
nucalm_price_item	0.00133419	1
filter	0.00235844	1
pe_license_details	0.00147724	1
lcm_config	0.00309181	1
license_prism_central	0.00180435	1"""

d3="""Total	1694.62	2118353
nucalm_task	187.526	873934
nucalm_variable	449.939	351240
nucalm_runbook	74.8611	348878
nucalm_action	587.724	326097
event	13.9696	65103
nucalm_run_log	76.9932	23482
nucalm_secret	26.0963	21927
nucalm_lifecycle	14.7676	11859
task	54.6152	11655
category_association	2.47085	11515
nucalm_config_spec	18.3982	9413
nucalm_credential	6.69401	5321
nucalm_back_filling_service_sync_status	6.99991	4460
abac_entity_capability	10.3162	3700
nucalm_substrate_cfg	8.23737	3004
nucalm_application_cfg	6.61072	2871
nucalm_app_blueprint	15.0142	2862
nucalm_deployment_cfg	5.08438	2836
nucalm_package_cfg	4.16813	2794
nucalm_service_cfg	4.23313	2782
nucalm_package	3.96452	2431
nucalm_app_beam_status	3.38535	2420
nucalm_deployment	4.87993	2398
nucalm_application	6.39925	2377
nucalm_deployment_element	3.95213	2360
nucalm_substrate_element	8.73389	2360
nucalm_app_profile_instance	51.7595	2357
nucalm_service	3.96819	2356
nucalm_app_protection_status	4.26535	2326
nucalm_package_element	3.7308	2323
nucalm_service_element	3.5391	2313
nucalm_substrate	9.30193	2291
stig_report_details	0.135398	631
audit	0.122094	569
alert_check_schema	1.66528	540
licensing_feature	0.78894	528
intent_spec	4.77662	440
domain	0.392733	287
permission	0.635839	264
stig_rule	0.28684	126
ncc_error_codes	0.0894184	123
nutanix_vulnerability_db	0.189283	93
nucalm_quota	0.0671139	74
audit_event_schema	0.183197	70
category	0.0651674	39
idempotency_entity	0.0602684	37
abac_category	0.0614357	34
management_server_account	0.0931358	34
iamv2_backup_chunks	0.00708103	33
virtual_network	0.0778913	33
project_entity	0.470429	31
nucalm_resource_type	0.0818281	27
nucalm_environment	0.152874	25
nucalm_provider	0.0480356	19
marketplace_item	0.83707	16
action_type	0.036025	16
action_template	0.03936	14
registry_db	0.0266409	13
alert	0.00236034	11
widget	0.0192404	10
abac_user_capability	0.118442	9
nucalm_feature	0.00894928	8
nucalm_worker_state	0.0104179	8
pulse	0.00947571	8
virtual_disk	0.0361576	8
vulnerability_stats	0.0059967	6
nucalm_service_version	0.00918198	5
report_config	0.0112782	5
abac_category_key	0.00728321	5
panacea_follower	0.00789165	5
report_template	0.0073452	5
panacea_leader	0.00873089	5
role	0.0462046	4
mercury_authn_cookie_info	0.0198212	4
vm	0.0309067	3
nucalm_sync_status	0.00354958	3
filter	0.00750065	3
nucalm_service_upgrade_history	0.00475502	3
certificates_entity	0.0160036	3
platform_client_entity	0.0359049	3
volume_group_config	0.0133629	3
password_manager_stats	0.00272083	3
trigger_type	0.00659466	3
disk	0.015029	2
anduril_vm_info	0.00943947	2
mantle_secret	0.00184441	2
host_nic	0.00455666	2
svcmgr_app	0.00423717	2
svcmgr_task	0.00478363	2
volume_group_entity_capability	0.0026207	2
msp_app	0.0052433	2
node_entity	0.044529	2
stig_report	0.00298691	2
access_control_policy	0.0044384	2
nucalm_published_service	0.00176811	1
protection_domain	0.00547504	1
history	0.00165367	1
svcmgr_history	0.00239182	1
node_lazan_stats	0.003088	1
replica_placement_policy	0.0011797	1
nucalm_published_service_cfg	0.001647	1
msp	0.00396347	1
vm_management_cluster_config	0.000861168	1
scheduler_node_pool_record	0.00108147	1
trigger_template	0.00200176	1
storage_policy	0.00290298	1
node_pool_entity	0.00428963	1
nucalm_backup_restore_history	0.0011816	1
nucalm_account_data	0.00163841	1
pd_schedule	0.00247383	1
nucalm_license	0.00178337	1
hardening_report_details	0.00104237	1
scheduler_node_info	0.00111961	1
atlas_migration_config	0.000823021	1
metrics_data_provider	0.00257492	1
iscsi_client_params	0.0015831	1
protection_rule	0.00287437	1
docker_registry	0.00168419	1
license_metadata_mapping	0.00108242	1
parcel_info	0.00102806	1
dashboard	0.00204468	1
favorite	0.00115776	1
storage_pool	0.00289631	1
nucalm_price_item	0.00133419	1
entity_sync_stats_source	0.00131035	1
msp_dc_lb	0.0054636	1
license_enforcement	0.00142479	1
iamv2_backups_metadata	0.00140095	1
virtual_nic	0.00301552	1
lcm_config	0.00294781	1
container	0.00702	1"""








# node_entities_data = [["nucalm_action	800.011	443602","nucalm_runbook	101.578	473388","nucalm_run_log	107.51	33705","nucalm_task	254.545	1186267","nucalm_variable	615.765	480786"],
#                       ["nucalm_task	1018.01	4744255","nucalm_variable	2445.07	1909412","nucalm_runbook	406.124	1892677","nucalm_action	3195.74	1772386","nucalm_run_log	418.582	127680"],
#                       ["nucalm_action	588.218	326249		nucalm_action	573.64	318164		nucalm_action	588.1	326168","nucalm_runbook	74.8911	349018		nucalm_runbook	73.0271	340331		nucalm_runbook	74.5008	347199","nucalm_run_log	77.0505	23500		nucalm_run_log	76.4456	23325		nucalm_run_log	76.7014	23360","nucalm_task	187.615	874349		nucalm_task	182.803	851922		nucalm_task	187.151	872185","nucalm_variable	450.047	351325		nucalm_variable	439.197	342793		nucalm_variable	449.95	351210"],
#   ["nucalm_action	2232.04	1237200		nucalm_action	2180.81	1208712		nucalm_action	2232	1237163","nucalm_runbook	282.924	1318520		nucalm_runbook	276.701	1289520		nucalm_runbook	282.737	1317651","nucalm_run_log	275.349	83933		nucalm_run_log	270.807	82564		nucalm_run_log	274.923	83878","nucalm_task	708.342	3301114		nucalm_task	692.429	3226953		nucalm_task	708.498	3301840","nucalm_variable	1730.89	1354157		nucalm_variable	1694.08	1325482		nucalm_variable	1734.36	1356799"]]
# urls = ['http://10.46.1.165/Bugs/NBV/CALM_380/incremental_backup_restore/1NS/final_run_restore/restore_3000.log','http://10.46.1.165/Bugs/NBV/CALM_380/incremental_backup_restore/1NL/restore/restore12_5k.log','http://10.46.1.165/Bugs/NBV/CALM_380/incremental_backup_restore/3NS/restore/restore_7000Apps.log','http://10.46.1.165/Bugs/NBV/CALM_380/incremental_backup_restore/3NL/restore/restore_25000Apps.log']
urls = ['http://10.46.1.165/Bugs/NBV/CALM_380/incremental_backup_restore/3NL/restore/restore_25000Apps.log']
d1 = [{i.split()[0]:i.split()[1:]} for i in d1.split('\n')]
d2 = [{i.split()[0]:i.split()[1:]} for i in d2.split('\n')]
d3 = [{i.split()[0]:i.split()[1:]} for i in d3.split('\n')]
dFinal = {}
for item in d1:
    for key, value in item.items():
        dFinal[key] = [eval(value[0]),eval(value[1])]
for item in d2:
    for key, value in item.items():
      if key not in dFinal:
        dFinal[key] = [0,0]
      dFinal[key][0] += eval(value[0])
      dFinal[key][1] += eval(value[1])
for item in d3:
    for key, value in item.items():
      if key not in dFinal:
        dFinal[key] = [0,0]
      dFinal[key][0] += eval(value[0])
      dFinal[key][1] += eval(value[1])
import json
for i in dFinal:
  print(i, dFinal[i][1], dFinal[i][0])
# import json
# # print(json.dumps(dFinal))
# for url,entities_data in zip(urls, [dFinal]):
#   # Defining a dict 
#   data = defaultdict(list) 

#   res = requests.get(url)
#   text_lines = res.text.splitlines()
#   data['Total'] = [text_lines[0].split('Z')[0], text_lines[-1].split('Z')[0]]


#   for i in text_lines:
#     s = i.split()
#     if 'restore started for' in i:
#       entity = s[11].split(',')[0]
#       data[entity] = [' '.join(s[:2])[:-1]]
#     if 'restore done for' in i:
#       entity = s[11].split(',')[0]
#       data[entity].append(' '.join(s[:2])[:-1])
#   # for i in ['IDF backup process' 'elastic search data restore process', 'zookeper data restore process']:
#   #   for j in ['started', 'completed']:
#   #     process = f".*{i} {j}"
#   #     print(process)
#   #     process_data = re.findall(process, res.text, re.MULTILINE)
#   #     if len(process_data) != 1:
#   #       print(process_data, process)
#   #       print(process_data[100000000])
#   #     data[i].append(process_data[0].split('Z')[0])

#   # for i in dFinal:
#   #   if i == 'Total':
#   #     continue
#   #   for j in ['restore started for', 'restore done for']:
#   #     process = f".*{j} {i}$"
#   #     print(process)
#   #     process_data = re.findall(process, res.text, re.MULTILINE)
#   #     if len(process_data) != 1:
#   #       print(process_data, process)
#   #       print(process_data[100000000])
#   #     data[i].append(process_data[0].split('Z')[0])

#   lines = res.split('\n')
#   for i in lines:
#     if 'restore started for' in i:
#       for j in dFinal:
#         if j in i:
          

#   # from datetime import datetime
#   # entites = []
#   # values = []
#   # total = ((datetime.strptime(data['Total'][1], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(data['Total'][0], '%Y-%m-%d %H:%M:%S.%f')).total_seconds())/60
#   # for d in data:
#   #   if d == 'Total':continue
#   #   dt1 = datetime.strptime(data[d][0], '%Y-%m-%d %H:%M:%S.%f')
#   #   dt2 = datetime.strptime(data[d][1], '%Y-%m-%d %H:%M:%S.%f')
#   #   diff_seconds = (dt2 - dt1).total_seconds()
#   #   diff_min = diff_seconds / 60
#   #   if diff_min > total/100:
#   #     values.append(str(round(diff_min, 2)))
#   #     entites.append(d)
#   # tVales = []
#   # order = ["nucalm_action","nucalm_runbook", "nucalm_run_log", "nucalm_task", "nucalm_variable"]
#   # print(','.join(order))
#   # for i in order:
#   #   for j in range(len(entites)):
#   #     if i == entites[j]:
#   #       print(values[j], end=',')
#   # print()

#   # entities_data = [i.split() for i in entities_data]
#   # for j in ["nucalm_action","nucalm_runbook", "nucalm_run_log", "nucalm_task", "nucalm_variable"]:
#   #   for i in range(len(entities_data)):
#   #     if entities_data[i][0] == j:
#   #       eCount = 0
#   #       mVal = 0
#   #       for k in range(0,len(entities_data[i]),3):
#   #         eCount += int(entities_data[i][k+2])
#   #         mVal += float(entities_data[i][k+1])
#   #       print(''.join(['# ', str(eCount),'<br>', str(round((mVal),2)), ' MB']), end=',')
#   # print()
