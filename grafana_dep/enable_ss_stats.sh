sudo docker load -i micro-stats.tar
kubectl apply -f gene_stats_pod.yaml
kubectl apply -f gene_stats_role_binding.yaml
kubectl apply -f gene_stats_role.yaml
kubectl apply -f gene_stats_serviceMonitor.yaml
kubectl apply -f gene_stats_service.yaml
kubectl apply -f grafana-dashboardDatasources.yaml
kubectl apply -f grafana-dashboardDefinitions.yaml
kubectl apply -f grafana-dashboardSources.yaml
kubectl apply -f grafana-deployment.yaml
kubectl apply -f grafana-serviceAccount.yaml
kubectl apply -f grafana-serviceMonitor.yaml
kubectl apply -f grafana-service.yaml

kubectl patch svc grafana -n ntnx-system -p '{"spec": {"type": "NodePort"}}'

grafana_port=`kubectl get svc -A | grep grafana | awk {'print $6'} | awk -F'[:/]' '{print $2}'`
grafana_ip=`hostname -I | awk '{print $1}'`

echo $grafana_ip:$grafana_port
