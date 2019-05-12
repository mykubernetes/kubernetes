Prometheus Operator 部署
=====================
1、获取地址  
```
$ git clone https://github.com/camilb/prometheus-kubernetes.git
$ cd prometheus-kubernetes
```  

2、执行脚本  
```
$ ./deploy
Check for uncommitted changes


Creating 'monitoring' namespace.
Error from server (AlreadyExists): namespaces "monitoring" already exists

1) AWS
2) GCP
3) Azure
4) Custom
Please select your cloud provider:4                    #输入要部署的环境，本地选择4
Deploying on custom providers without persistence
Setting components version
Enter Prometheus Operator version [v0.19.0]:

Enter Prometheus version [v2.2.1]:

Enter Prometheus storage retention period in hours [168h]:

Enter Prometheus storage volume size [40Gi]: 20Gi

Enter Prometheus memory request in Gi or Mi [1Gi]:

Enter Grafana version [5.1.1]:

Enter Alert Manager version [v0.15.0-rc.1]:

Enter Node Exporter version [v0.16.0-rc.3]:

Enter Kube State Metrics version [v1.3.1]:

Enter Prometheus external Url [http://127.0.0.1:9090]:

Enter Alertmanager external Url [http://127.0.0.1:9093]:

Do you want to use NodeSelector  to assign monitoring components on dedicated nodes?
Y/N [N]:

Do you want to set up an SMTP relay?
Y/N [N]:

Do you want to set up slack alerts?
Y/N [N]:

Removing all the sed generated files

Deploying Prometheus Operator
serviceaccount/prometheus-operator created
clusterrole.rbac.authorization.k8s.io/prometheus-operator created
clusterrolebinding.rbac.authorization.k8s.io/prometheus-operator created
service/prometheus-operator created
deployment.apps/prometheus-operator created
Waiting for Operator to register custom resource definitions.....done!

Deploying Alertmanager
secret/alertmanager-main created
service/alertmanager-main created
alertmanager.monitoring.coreos.com/main created

Deploying node-exporter
daemonset.extensions/node-exporter created
service/node-exporter created

Deploying Kube State Metrics exporter
serviceaccount/kube-state-metrics created
clusterrole.rbac.authorization.k8s.io/kube-state-metrics created
clusterrolebinding.rbac.authorization.k8s.io/kube-state-metrics created
role.rbac.authorization.k8s.io/kube-state-metrics-resizer created
rolebinding.rbac.authorization.k8s.io/kube-state-metrics created
deployment.apps/kube-state-metrics created
service/kube-state-metrics created

Deploying Grafana
Enter Grafana administrator username [admin]: admin                #grafana账号
Enter Grafana administrator password: **************               #grafana密码
secret/grafana-credentials created
configmap/grafana-dashboards created
deployment.apps/grafana created
service/grafana created

Deploying Prometheus
serviceaccount/prometheus-k8s created
role.rbac.authorization.k8s.io/prometheus-k8s created
role.rbac.authorization.k8s.io/prometheus-k8s created
role.rbac.authorization.k8s.io/prometheus-k8s created
clusterrole.rbac.authorization.k8s.io/prometheus-k8s created
rolebinding.rbac.authorization.k8s.io/prometheus-k8s created
rolebinding.rbac.authorization.k8s.io/prometheus-k8s created
rolebinding.rbac.authorization.k8s.io/prometheus-k8s created
clusterrolebinding.rbac.authorization.k8s.io/prometheus-k8s created
configmap/prometheus-k8s-rules created
servicemonitor.monitoring.coreos.com/alertmanager created
servicemonitor.monitoring.coreos.com/kube-dns created
servicemonitor.monitoring.coreos.com/kube-state-metrics created
servicemonitor.monitoring.coreos.com/kubelet created
servicemonitor.monitoring.coreos.com/node-exporter created
servicemonitor.monitoring.coreos.com/prometheus-operator created
servicemonitor.monitoring.coreos.com/prometheus created
service/prometheus-k8s created
prometheus.monitoring.coreos.com/k8s created
servicemonitor.monitoring.coreos.com/kube-apiserver created
servicemonitor.monitoring.coreos.com/kube-controller-manager created
servicemonitor.monitoring.coreos.com/kube-scheduler created

Self hosted
service/kube-controller-manager-prometheus-discovery created
service/kube-dns-prometheus-discovery created
service/kube-scheduler-prometheus-discovery created
servicemonitor.monitoring.coreos.com/kube-apiserver created
servicemonitor.monitoring.coreos.com/kube-controller-manager created
servicemonitor.monitoring.coreos.com/kube-scheduler created

Removing local changes

Done
```  

3、可以查看下 Prometheus Operator 所创建的 CRD 资源都有哪些。  
```
$ kubectl get crd
NAME                                    CREATED AT
alertmanagers.monitoring.coreos.com     2018-08-09T02:55:16Z
prometheuses.monitoring.coreos.com      2018-08-09T02:55:16Z
servicemonitors.monitoring.coreos.com   2018-08-09T02:55:16Z

$ kubectl get ServiceMonitor -n monitoring
NAME                      CREATED AT
alertmanager              1h
kube-apiserver            1h
kube-controller-manager   1h
kube-dns                  1h
kube-scheduler            1h
kube-state-metrics        1h
kubelet                   1h
node-exporter             1h
prometheus                1h
prometheus-operator       1h
```  

4、各个服务部署启动完毕之后，通过 Kubectl 命令查看下 monitoring 命名空间下的 Pod 和 Service。  
```
$ kubectl get pods -n monitoring
NAMESPACE     NAME                                  READY     STATUS    RESTARTS   AGE
monitoring    alertmanager-main-0                   2/2       Running   0          52m
monitoring    alertmanager-main-1                   2/2       Running   0          51m
monitoring    alertmanager-main-2                   2/2       Running   0          51m
monitoring    grafana-568b569696-wxlxz              2/2       Running   0          51m
monitoring    kube-state-metrics-9977d88d8-p99wt    2/2       Running   0          45m
monitoring    node-exporter-kckr5                   1/1       Running   0          52m
monitoring    prometheus-k8s-0                      2/2       Running   0          51m
monitoring    prometheus-k8s-1                      2/2       Running   0          51m
monitoring    prometheus-operator-f596c68cf-8xblq   1/1       Running   0          52m

$ kubectl get svc -n monitoring
NAME                    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
alertmanager-main       ClusterIP   10.109.10.5      <none>        9093/TCP            52m
alertmanager-operated   ClusterIP   None             <none>        9093/TCP,6783/TCP   52m
grafana                 ClusterIP   10.106.93.254    <none>        3000/TCP            52m
kube-state-metrics      ClusterIP   10.107.82.174    <none>        8080/TCP            52m
node-exporter           ClusterIP   None             <none>        9100/TCP            52m
prometheus-k8s          ClusterIP   10.107.161.100   <none>        9090/TCP            52m
prometheus-operated     ClusterIP   None             <none>        9090/TCP            52m
prometheus-operator     ClusterIP   10.106.114.242   <none>        8080/TCP            52m
```  

5、配置外网访问  
```
$ kubectl edit svc grafana -n monitoring
......
spec:
  clusterIP: 10.106.93.254
  externalTrafficPolicy: Cluster
  ports:
  - nodePort: 30077
    port: 3000
    protocol: TCP
    targetPort: web
  selector:
    app: grafana
  sessionAffinity: None
  type: NodePort         # 这里将 ClusterIP 修改为 NodePort
status:
  loadBalancer: {}
```  

