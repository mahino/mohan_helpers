import requests
import json
import sys
import time

payload = {}
files={}
headers = {
  'Authorization': 'Basic YWRtaW46TnV0YW5peC4xMjM='
}
final = {}
query_range = f"http://{sys.argv[1]}:{sys.argv[2]}/api/datasources/proxy/1/api/v1/query_range?query="
all_pods = {
    # "default": [
    #     "micro-stats"
    # ],
    "kube-system": [
        "cloud-controller-manager-rlk2q",
        "coredns-79b94b7c88-5p666",
        "kube-apiserver-ncm-e76921-default-0",
        "kube-flannel-ds-9gc4m",
        "kube-proxy-ds-ztzwh",
        "lb-controller-deployment-0",
        "mspdns-b8xbg",
        "mspserviceregistry-54dbdf4bbd-ffbrn"
    ],
    "ntnx-ikat": [
        "ikat-9sqlv"
    ],
    "ntnx-ncm-aiops": [
        "neuron-0",
        "reports-7c69596d97-7wcz5",
        "sizer-56f544894c-4rv45",
        "uda-665bd94dc5-c4dxx",
        "vulcan-797fd9fc7f-2r9tk"
    ],
    "ntnx-ncm-common": [
        "aiops-ui-66f48dcf98-482t8",
        "cfs-0",
        "cluster-mgmt-764b67895c-bdw4c",
        "dcis-7755cfb8d5-fwdh8",
        "dmis-5747ddfb64-l7kts",
        "dpm-d5fbdfdc9-59gzr",
        "ergon-fd597869d-g8q2v",
        "external-notifications-service-56bccbfc49-s69qz",
        "filestore-chakr-cm-0",
        "filestore-chakr-db-instance-0",
        "insights-collector-0",
        "mercury-6b5864865-wqxhz",
        "msp-prometheus-collector-5446f794f9-k6fgj",
        "ncm-adonis-service-qj2p4",
        "ncm-backup-5b7f4997c5-qx67k",
        "ncm-data-processor-57dc64c777-6q4wl",
        "ncm-dbal-dedupe-56fc68d9f-z458b",
        "ncm-epsilon-0",
        "ncm-migration-5c745db96-x9n2n",
        "ncm-post-processor-6d69c4c6c-8r87c",
        "nutanix-infra-data-receiver-8547c6b895-q8hp7",
        "onboarding-svc-7dd76b4677-jhx6w",
        "otel-collector-799b4c5796-xh6dx",
        "search-c65bbd6d9-7xrrr",
        "signals-manager-b5599cdff-pkz7b",
        "statsgw-59c4567bd6-lnxq8",
        "zeus-collector-0"
    ],
    "ntnx-ncm-datastore": [
        "altinity-clickhouse-operator-8657c457f-mcchn",
        "ch-keeper-pull-image-hkgj5",
        "ch-server-pull-image-4txhx",
        "chakr-cm-0",
        "chakr-db-instance-0",
        "chi-clickhouse-chcluster1-0-0-0",
        "chk-clickhouse-keeper-chkeeper-chkeeper-0-0-0",
        "clickhouse-keeper-chkeeper-0",
        "clickhouse-schema-job-1740036290-7tg2g",
        "cpaas-nats-0",
        "cpaas-nats-box-6cdc959f6c-p74xd",
        "idf-statefulset-0",
        "ncm-postgres-0",
        "ss-chakr-cm-0",
        "ss-chakr-db-instance-0",
        "ss-idf-statefulset-0",
        "ss-zk-0",
        "zk-0"
    ],
    "ntnx-ncm-self-service": [
        "insights-collector-0",
        "ncm-calm-0",
        "ncm-policy-6d4b6ff4d6-q7nr7",
        "ncm-tunnel-server-688485dc8-b2rmr"
    ],
    "ntnx-system": [
        "alertmanager-main-0",
        "alerts-broker-7747fc4d6c-shqqm",
        "csi-node-ntnx-plugin-zdjpv",
        "csi-provisioner-ntnx-plugin-0",
        "fluent-bit-dszjq",
        "fluentd-aggregator-0",
        "grafana-5bbffb8b4-7frmb",
        "kube-state-metrics-69685668f6-w7k4s",
        "mutator-webhook-dep-54869fd5bc-n5nrz",
        "node-exporter-c6tm7",
        "ntnx-cluster-maintainer-5c7bbbfd77-hls9t",
        "ntnx-k8s-cluster-maintainer-operator-75c549c444-fbwl4",
        "prometheus-k8s-0",
        "prometheus-operator-6f4ffb8dc9-gkz5c"
    ]
}

# app crud 6h 1741717325220&to=1741739988752
# 6k apps 1741621603565&to=1741638871142
# 7k apps 1741621603565&to=1741638871142
# 9k apps 1746605823864 1746628893023

pod_mem_cpu = {}
start_time = sys.argv[3]
end_time   = sys.argv[4]

# for e in ['container_memory_working_set_bytes', 'node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate']:
#   for i in all_pods:
#     for j in all_pods[i]:
#       values = []
#       app = ''
#       if e == 'container_memory_working_set_bytes':
#         app = ", image!=\"\""
#       url = query_range + "sum(" + e + "{namespace=\"" + i + "\", pod=\"" + j + "\", cluster=\"\"" + app + "}) by (container)&start=" + start_time + "&end=" + end_time + "&step=15"
#       response = requests.request("GET", url, headers=headers, data=payload, files=files)
#       if response.status_code != 200:
#         print(response.status_code)
        
#       response = json.loads(response.content)
#       try:
#         for n in response['data']['result'][1]['values']:
#           values.append(eval(n[1]))
#         values.sort()
#         pod_mem_cpu[e+'_'+i+'_'+j] = f"{values[-1]}, {values[int(len(values)*0.5)]}, {values[int(len(values)*0.75)]}, {values[int(len(values)*0.9)]}, {values[int(len(values)*0.95)]}, {values[int(len(values)*0.99)]}"
#       except IndexError as err:
#         print(f"ERROR: No data found for [{i}]-[{j}]")
#       except KeyError as err:
#         print(f"ERROR: Key error [{err}]")
#         print(response)
# # print(json.dumps(pod_mem_cpu))

# micro = {}
# for i in ['cpu_perc', 'mem_rss']:
#   for j in ['ncm_calm', 'ncm_epsilon']:
#     url = query_range + 'sum(micro_services_stats{type="%s", container_name="%s"}) by (process, pid)&start=%s&end=%s&step=15' % (i, j, start_time, end_time)
#     response = requests.request("GET", url, headers=headers, data=payload, files=files)
#     response = json.loads(response.content)
#     print(response)
#     for m in response['data']['result']:
#       try:
#         print(m['metric']['process'] )
#         values = []
#         for n in m['values']:
#           if eval(n[1]):
#             values.append(eval(n[1]))
#         values.sort()
#         micro[i+'_'+j+'_'+m['metric']['process']+'_'+m['metric']['pid']] = f"{values[-1]}, {values[int(len(values)*0.5)]}, {values[int(len(values)*0.75)]}, {values[int(len(values)*0.9)]}, {values[int(len(values)*0.95)]}, {values[int(len(values)*0.99)]}"
#       except IndexError:
#         print(f"ERROR: No data found for [{i}]-[{j}]-[{m['metric']['process']}]-[{m['metric']['pid']}]")

# trans_bytes = {}
# for e in ['container_network_receive_bytes_total', 'container_network_transmit_bytes_total']:
#   for i in all_pods:
#     for j in all_pods[i]:
#       values = []
#       url = query_range + "sum(irate(" + e + "{cluster=\"\",namespace=~\"" + i + "\", pod=~\"" + j + "\"}[4h:5m])) by (pod)&start=" + start_time + "&end=" + end_time + "&step=5"
#       response = requests.request("GET", url, headers=headers, data=payload, files=files)
#       response = json.loads(response.content)
#       try:
#         for n in response['data']['result'][0]['values']:
#           values.append(eval(n[1]))
#         values.sort()
#         trans_bytes[e+'_'+i+'_'+j] = f"{values[-1]}, {values[int(len(values)*0.5)]}, {values[int(len(values)*0.75)]}, {values[int(len(values)*0.9)]}, {values[int(len(values)*0.95)]}, {values[int(len(values)*0.99)]}"
#       except IndexError:
#         print(f"ERROR: No data found for [{i}]-[{j}]")

# PVCs = {}
# PCVs_pods = {
#     "ntnx-ncm-common": [
#         "data-ncm-epsilon-0",
#         "datadir-cfs-0",
#         "ergon-fd597869d-qj4jj-ergon-data",
#         "filestore-chakr-cm-data-dir-filestore-chakr-cm-0",
#         "filestore-chakr-db-instance-data-dir-0-filestore-chakr-db-instance-0",
#         "otel-collector-pvc"
#     ],
#     "ntnx-ncm-datastore": [
#         "chakr-cm-data-dir-chakr-cm-0",
#         "chakr-db-instance-data-dir-0-chakr-db-instance-0",
#         "chakr-db-instance-data-dir-1-chakr-db-instance-0",
#         "chakr-db-instance-data-dir-2-chakr-db-instance-0",
#         "chakr-db-instance-data-dir-3-chakr-db-instance-0",
#         "chakr-db-instance-data-dir-4-chakr-db-instance-0",
#         "chakr-db-instance-data-dir-5-chakr-db-instance-0",
#         "chakr-db-instance-data-dir-6-chakr-db-instance-0",
#         "chakr-db-instance-data-dir-7-chakr-db-instance-0",
#         "clickhouse-data-volume-chi-clickhouse-chcluster1-0-0-0",
#         "clickhouse-keeper-datadir-volume-chk-clickhouse-keeper-chkeeper-chkeeper-0-0-0",
#         "cpaas-nats-js-pvc-cpaas-nats-0",
#         "datadir-ss-zk-0",
#         "datadir-zk-0",
#         "keeper-volume-clickhouse-keeper-chkeeper-0",
#         "nats-jwt-pvc-cpaas-nats-0",
#         "postgresdata-ncm-postgres-0",
#         "ss-chakr-cm-data-dir-ss-chakr-cm-0",
#         "ss-chakr-db-instance-data-dir-0-ss-chakr-db-instance-0",
#         "ss-chakr-db-instance-data-dir-1-ss-chakr-db-instance-0",
#         "ss-chakr-db-instance-data-dir-2-ss-chakr-db-instance-0",
#         "ss-chakr-db-instance-data-dir-3-ss-chakr-db-instance-0",
#         "ss-chakr-db-instance-data-dir-4-ss-chakr-db-instance-0",
#         "ss-chakr-db-instance-data-dir-5-ss-chakr-db-instance-0",
#         "ss-chakr-db-instance-data-dir-6-ss-chakr-db-instance-0",
#         "ss-chakr-db-instance-data-dir-7-ss-chakr-db-instance-0"
#     ],
#     "ntnx-ncm-self-service": [
#         "data-ncm-calm-0",
#         "ncm-policy-pvc",
#         "ncm-tunnel-server-pvc"
#     ],
#     "ntnx-system": [
#         "fluentd-logs-fluentd-aggregator-0",
#         "prometheus-k8s-db-prometheus-k8s-0"
#     ]
# }

# for i in PCVs_pods:
#   for j in PCVs_pods[i]:
#     values = []
#     # (sum without(instance, node) (topk(1, (kubelet_volume_stats_capacity_bytes{cluster="", job="kubelet", metrics_path="/metrics", namespace="ntnx-ncm-datastore", persistentvolumeclaim="chakr-cm-data-dir-chakr-cm-0"}))) - sum without(instance, node) (topk(1, (kubelet_volume_stats_available_bytes{cluster="", job="kubelet", metrics_path="/metrics", namespace="ntnx-ncm-datastore", persistentvolumeclaim="chakr-cm-data-dir-chakr-cm-0"}))))
#     url = query_range + "(sum without(instance, node) (topk(1, (kubelet_volume_stats_capacity_bytes{cluster=\"\", job=\"kubelet\", metrics_path=\"/metrics\", namespace=~\"" + i + "\", persistentvolumeclaim=\"" + j + "\"}))) - sum without(instance, node) (topk(1, (kubelet_volume_stats_available_bytes{cluster=\"\", job=\"kubelet\", metrics_path=\"/metrics\", namespace=~\"" + i + "\", persistentvolumeclaim=\"" + j + "\"}))))&start=" + start_time + "&end=" + end_time + "&step=5"
#     response = requests.request("GET", url, headers=headers, data=payload, files=files)
#     response = json.loads(response.content)
#     try:
#       for n in response['data']['result'][0]['values']:
#         values.append(eval(n[1]))
#       values.sort()
#       PVCs[i+'_'+j] = f"{values[-1]}, {values[int(len(values)*0.5)]}, {values[int(len(values)*0.75)]}, {values[int(len(values)*0.9)]}, {values[int(len(values)*0.95)]}, {values[int(len(values)*0.99)]}"
#     except IndexError:
#       print(f"ERROR: No data found for [{i}]-[{j}]")

idf_ent = {}
for i in ['mem', 'entities']:
    values = []
    url = query_range + "sum(entity_stats{metric=\"" + i + "\"}) by (entity_type)&start=" + start_time + "&end=" + end_time + "&step=5"
    response = requests.request("GET", url, headers=headers)
    response = json.loads(response.content)
    for m in response['data']['result']:
      try:
        print(m['metric']['entity_type'] )
        values = []
        for n in m['values']:
          if eval(n[1]):
            values.append(eval(n[1]))
        values.sort()
        idf_ent[i+'_'+m['metric']['entity_type']] = f"{values[-1]}, {values[int(len(values)*0.5)]}, {values[int(len(values)*0.75)]}, {values[int(len(values)*0.9)]}, {values[int(len(values)*0.95)]}, {values[int(len(values)*0.99)]}"
      except IndexError:
        print(f"ERROR: No data found for [{i}]-[{m['metric']['entity_type']}]")

# final['PVC'] = PVCs
# final['micro'] = micro
# final['trans_bytes'] = trans_bytes
# final['pod_mem_cpu'] = pod_mem_cpu
final['idf_ent'] = idf_ent

print(json.dumps(final))