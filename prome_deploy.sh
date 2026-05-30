mkdir prome_stats
cd prome_stats
scp mohan.as@10.41.26.208:/home/mohan.as/kube_stats/* .

/usr/bin/kubectl apply -f grafana-dashboardDatasources.yaml
/usr/bin/kubectl apply -f grafana-dashboardDefinitions.yaml
/usr/bin/kubectl apply -f grafana-dashboardSources.yaml
/usr/bin/kubectl apply -f grafana-deployment.yaml
/usr/bin/kubectl apply -f grafana-serviceAccount.yaml
/usr/bin/kubectl apply -f grafana-serviceMonitor.yaml
/usr/bin/kubectl apply -f grafana-service.yaml
/usr/bin/kubectl apply -f calm_role.yaml
/usr/bin/kubectl apply -f calm_role_binding.yaml 
/usr/bin/kubectl apply -f calm_service_monitor.yaml
/usr/bin/kubectl apply -f epsilon_role.yaml
/usr/bin/kubectl apply -f epsilon_role_binding.yaml 
/usr/bin/kubectl apply -f epsilon_service_monitor.yaml 

kubectl patch svc grafana -n ntnx-system -p '{"spec": {"type": "NodePort"}}'

grafana_port=`kubectl get svc -A | grep grafana | awk {'print $6'} | awk -F'[:/]' '{print $2}'`
grafana_ip=`hostname -I | awk '{print $1}'`
echo http://$grafana_ip:$grafana_port

/usr/bin/kubectl expose service ncm-calm -n ntnx-ncm-self-service --name=ncm-calm-nodeport --type=NodePort
/usr/bin/kubectl expose service ncm-epsilon -n ntnx-ncm-common --name=ncm-epsilon-nodeport --type=NodePort

kubectl patch svc ncm-calm-nodeport -n ntnx-ncm-self-service -p '{"metadata": {"labels": {"app.kubernetes.io/name": "ncm-calm-nodeport"}}}'
kubectl patch svc ncm-epsilon-nodeport -n ntnx-ncm-common -p '{"metadata": {"labels": {"app.kubernetes.io/name": "ncm-epsilon-nodeport"}}}'

kubectl patch svc ncm-calm-nodeport -n ntnx-ncm-self-service --type='json' -p='[{"op": "add", "path": "/spec/ports/-", "value": {"name": "calmstats", "nodePort": 32527, "port": 8001, "protocol": "TCP", "targetPort": 8001}}]'
kubectl patch svc ncm-epsilon-nodeport -n ntnx-ncm-common --type='json' -p='[{"op": "add", "path": "/spec/ports/-", "value": {"name": "epsilonstats", "nodePort": 32552, "port": 8002, "protocol": "TCP", "targetPort": 8002}}]'

calm_idf_ip=`kubectl get svc -n ntnx-ncm-self-service | grep idf  | awk '{print $3}'`
sed -i "s/calm_idf_ip/$calm_idf_ip/g" expose_calm_metrics.py

common_idf_ip=`kubectl get svc -n ntnx-ncm-common | grep idf  | awk '{print $3}'`
sed -i "s/common_idf_ip/$common_idf_ip/g" expose_calm_metrics.py

epsilon_pod_name=`kubectl get pods -n ntnx-ncm-common | grep epsilon`
calm_pod_name=`kubectl get pods -n ntnx-ncm-self-service | grep calm`

# login to pod and run python3 files indviduall in calm/epsilon pod
epsilon_processes=$(kubectl exec -i $epsilon_pod_name -n ntnx-ncm-common -c 'source /home/epsilon/venv/bin/activate;supervisorctl -c /home/epsilon/conf/supervisor/supervisord.conf status'| head -n50 | awk '{print}')
for process_name in `echo "$epsilon_processes" | awk '/RUNNING/ {print $1}'`;
do
  process_id=`echo "$epsilon_processes" | grep $process_name | awk '{print $4}'`
  process_id=${process_id/,/}
done

nucalm_processes=$(kubectl exec -i $calm_pod_name -n ntnx-ncm-common bash -c 'source /home/calm/venv/bin/activate;supervisorctl -c /home/calm/conf/supervisor/supervisord.conf status' | head -n50 | awk '{print}')
for process_name in `echo "$nucalm_processes" | awk '/RUNNING/ {print $1}'`;
do
  process_id=`echo "$nucalm_processes" | grep $process_name | awk '{print $4}'`
  process_id=${process_id/,/}
done