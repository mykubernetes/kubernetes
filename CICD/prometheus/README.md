```
> kubectl apply -f prometheus-ns.yml 
> kubectl apply -f node-exporter-daemonset.yml
> kubectl apply -f node-exporter-service.yml
> kubectl apply -f kube-state-metrics-ServiceAccount.yml 
> kubectl apply -f kube-state-metrics-deploy.yml
> kubectl apply -f kube-state-metrics-service.yml
> kubectl apply -f monitor-node-disk-daemonset.yml
> kubectl apply -f prometheus-config-configmap.yml
> kubectl apply -f prometheus-k8s-ServiceAccount.yml
> kubectl apply -f prometheus-rules-configmap.yml 
> kubectl apply -f prometheus-secret.yml
> kubectl apply -f prometheus-deploy.yml
> kubectl apply -f prometheus-service.yml
> kubectl apply -f grafana-net-2-dashboard-configmap.yml
> kubectl apply -f grafana-deploy.yml
> kubectl apply -f grafana-service.yml
> kubectl apply -f grafana-net-2-dashboard-batch.yml
> kubectl apply -f grafana-ingress.yml
> kubectl apply -f alertmanager-config-configmap.yml
> kubectl apply -f alertmanager-templates-configmap.yml
> kubectl apply -f alertmanager-deploy.yml
> kubectl apply -f alertmanager-service.yml
```
