
1、安装  
```
git clone https://github.com/coreos/kube-prometheus.git
cd kube-prometheus
kubectl create -f manifests/setup
kubectl create -f manifests/
```

2、修改kubelet服务发现配置
```
# cd manifests/
# cat prometheus-serviceMonitorKubelet.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    k8s-app: kubelet
  name: kubelet
  namespace: monitoring
spec:
  endpoints:
  - bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    honorLabels: true
    interval: 30s
    port: http-metrics              #去掉https-metrics的s
    scheme: https
#    tlsConfig:                     #注释证书
#      insecureSkipVerify: true     #
  - bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    honorLabels: true
    interval: 30s
    path: /metrics/cadvisor
    port: http-metrics              #去掉https-metrics的s
    scheme: https
#    tlsConfig:                     #注释证书
#      insecureSkipVerify: true     #
  jobLabel: k8s-app
  namespaceSelector:                #匹配命名空间，代表去匹配kube-system命名空间下匹配，具有k8s-app=kubelet的标签，会将匹配的标签纳入我们prometheus监控中
    matchNames:
    - kube-system
  selector:                         #匹配kube-system命名空间下具有k8s-app=kube-scheduler标签的svc
    matchLabels:
      k8s-app: kubelet
```

3、查看crd是否部署成功
```
# kubectl get crd |grep coreos
alertmanagers.monitoring.coreos.com     3d
prometheuses.monitoring.coreos.com      3d
prometheusrules.monitoring.coreos.com   3d
servicemonitors.monitoring.coreos.com   3d
```

