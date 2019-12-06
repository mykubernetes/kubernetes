
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
  name: kubelet                    #定义的名称
  namespace: monitoring
spec:
  endpoints:
  - bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    honorLabels: true
    interval: 30s
    port: http-metrics              #去掉https-metrics的s    #这里定义的就是在svc上的端口名称
    scheme: http                    #去掉https的s
#    tlsConfig:                     #注释证书
#      insecureSkipVerify: true     #
  - bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    honorLabels: true
    interval: 30s
    path: /metrics/cadvisor
    port: http-metrics              #去掉https-metrics的s    #这里定义的就是在svc上的端口名称
    scheme: http                    #去掉https的s
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
alertmanagers.monitoring.coreos.com     48m
prometheuses.monitoring.coreos.com      48m
prometheusrules.monitoring.coreos.com   48m
servicemonitors.monitoring.coreos.com   48m
```

4、查看prometheus是否部署成功
```
# kubectl get pod -n monitoring
NAME                                   READY   STATUS    RESTARTS   AGE
alertmanager-main-0                    2/2     Running   0          49m
alertmanager-main-1                    2/2     Running   0          48m
alertmanager-main-2                    2/2     Running   0          48m
grafana-545d8c5576-8lgvg               1/1     Running   0          51m
kube-state-metrics-c86f5648c-4ffdb     4/4     Running   0          25s
node-exporter-7hthp                    2/2     Running   0          51m
node-exporter-r7np2                    2/2     Running   0          51m
node-exporter-ssbdr                    2/2     Running   0          51m
node-exporter-wd7jm                    2/2     Running   0          51m
prometheus-adapter-66fc7797fd-bd7gx    1/1     Running   0          51m
prometheus-k8s-0                       3/3     Running   1          49m
prometheus-k8s-1                       3/3     Running   1          49m
prometheus-operator-7cfc488cdd-wtm8w   1/1     Running   0          51m
```

5、prometheus和alertmanager采用的StatefulSet创建,其他的Pod则采用deployment创建
```
# kubectl get statefulsets -n monitoring
NAME                READY   AGE
alertmanager-main   3/3     52m
prometheus-k8s      2/2     52m

# kubectl get deployments -n monitoring
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
grafana               1/1     1            1           53m
kube-state-metrics    1/1     1            1           53m
prometheus-adapter    1/1     1            1           53m
prometheus-operator   1/1     1            1           53m
```  

6、查看service
```
# kubectl get svc -n monitoring |egrep  "prometheus|grafana|alertmanage"
alertmanager-main       ClusterIP   10.106.59.84            9093/TCP            59m
alertmanager-operated   ClusterIP   None                    9093/TCP,6783/TCP   57m
grafana                 ClusterIP   10.110.58.16            3000/TCP            59m
prometheus-adapter      ClusterIP   10.105.34.241           443/TCP             59m
prometheus-k8s          ClusterIP   10.102.246.32           9090/TCP            59m
prometheus-operated     ClusterIP   None                    9090/TCP            57m
prometheus-operator     ClusterIP   None                    8080/TCP            59m
```  

7、集群外访问prometheus
```
kubectl edit svc -n monitoring prometheus-k8s
kubectl edit svc -n monitoring grafana
kubectl edit svc -n monitoring alertmanager-main

修改 type: NodePort
```  
