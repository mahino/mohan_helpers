scp mohan.as@10.41.26.208:/home/mohan.as/kube_stats/* .
/usr/bin/kubectl apply -f grafana-dashboardDatasources.yaml
/usr/bin/kubectl apply -f grafana-dashboardDefinitions.yaml
/usr/bin/kubectl apply -f grafana-dashboardSources.yaml
/usr/bin/kubectl apply -f grafana-deployment.yaml
/usr/bin/kubectl apply -f grafana-serviceAccount.yaml
/usr/bin/kubectl apply -f grafana-serviceMonitor.yaml 
/usr/bin/kubectl apply -f grafana-service.yaml
/usr/bin/kubectl get po -A |grep grafana