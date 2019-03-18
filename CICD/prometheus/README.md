```
> kubectl apply -f prometheus-ns.yaml 
> kubectl apply -f node-exporter-daemonset.yaml
> kubectl apply -f node-exporter-service.yaml
> kubectl apply -f kube-state-metrics-ServiceAccount.yaml 
> kubectl apply -f kube-state-metrics-deploy.yaml
> kubectl apply -f kube-state-metrics-service.yaml
> kubectl apply -f monitor-node-disk-daemonset.yaml
> kubectl apply -f prometheus-config-configmap.yaml
> kubectl apply -f prometheus-k8s-ServiceAccount.yaml
> kubectl apply -f prometheus-rules-configmap.yaml 
> kubectl apply -f prometheus-secret.yaml
> kubectl apply -f prometheus-deploy.yaml
> kubectl apply -f prometheus-service.yaml
> kubectl apply -f grafana-net-2-dashboard-configmap.yaml
> kubectl apply -f grafana-deploy.yaml
> kubectl apply -f grafana-service.yaml
> kubectl apply -f grafana-net-2-dashboard-batch.yaml
> kubectl apply -f grafana-ingress.yaml
> kubectl apply -f alertmanager-config-configmap.yaml
> kubectl apply -f alertmanager-templates-configmap.yaml
> kubectl apply -f alertmanager-deploy.yaml
> kubectl apply -f alertmanager-service.yaml
```
