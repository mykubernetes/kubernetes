```
deploy prometheus namespase
> $ kubectl apply -f prometheus-ns.yaml

deploy export
> $ kubectl apply -f node-exporter-daemonset.yaml
> $ kubectl apply -f node-exporter-service.yaml

deploy kube-state-metrics
> $ kubectl apply -f kube-state-metrics-ServiceAccount.yaml 
> $ kubectl apply -f kube-state-metrics-deploy.yaml
> $ kubectl apply -f kube-state-metrics-service.yaml

deploy disk monitor
> $ kubectl apply -f monitor-node-disk-daemonset.yaml

deploy prometheus
> $ kubectl apply -f prometheus-config-configmap.yaml
> $ kubectl apply -f prometheus-k8s-ServiceAccount.yaml
> $ kubectl apply -f prometheus-rules-configmap.yaml 
> $ kubectl apply -f prometheus-secret.yaml
> $ kubectl apply -f prometheus-deploy.yaml
> $ kubectl apply -f prometheus-service.yaml

deploy grafana 
> $ kubectl apply -f grafana-net-2-dashboard-configmap.yaml
> $ kubectl apply -f grafana-deploy.yaml
> $ kubectl apply -f grafana-service.yaml
> $ kubectl apply -f grafana-net-2-dashboard-batch.yaml
> $ kubectl apply -f grafana-ingress.yaml

deploy alertmanager
> $ kubectl apply -f alertmanager-config-configmap.yaml
> $ kubectl apply -f alertmanager-templates-configmap.yaml
> $ kubectl apply -f alertmanager-deploy.yaml
> $ kubectl apply -f alertmanager-service.yaml
```
