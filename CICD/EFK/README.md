部署EFK  
=======
1、下载yaml文件  
```
# mkdir efk && cd efk 
wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/fluentd-elasticsearch/es-statefulset.yaml 
wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/fluentd-elasticsearch/es-service.yaml 
wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/fluentd-elasticsearch/fluentd-es-configmap.yaml 
wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/fluentd-elasticsearch/fluentd-es-ds.yaml 
wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/fluentd-elasticsearch/kibana-service.yaml 
wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/fluentd-elasticsearch/kibana-deployment.yaml
```  

2、查看下载的yml文件：  
```
ll 
total 36 
-rw-rw-r-- 1 centos centos 382 Dec 26 14:50 es-service.yaml 
-rw-rw-r-- 1 centos centos 2871 Dec 26 14:55 es-statefulset.yaml 
-rw-rw-r-- 1 centos centos 15528 Dec 26 18:12 fluentd-es-configmap.yaml 
-rw-rw-r-- 1 centos centos 2833 Dec 26 18:40 fluentd-es-ds.yaml 
-rw-rw-r-- 1 centos centos 1052 Dec 26 14:50 kibana-deployment.yaml 
-rw-rw-r-- 1 centos centos 354 Dec 26 14:50 kibana-service.yaml
```  

3、更换容器拉取路径  
使用vim打开以下3个yaml文件，输入/image回车，定位到3个容器镜像的拉取路径：  
```
# es-statefulset.yaml
k8s.gcr.io/elasticsearch:v6.3.0

# fluentd-es-ds.yaml
k8s.gcr.io/fluentd-elasticsearch:v2.2.0

# kibana-deployment.yaml	
docker.elastic.co/kibana/kibana-oss:6.3.2
```  
这里将elasticsearch镜像替换为其官方仓库镜像  
```
#es-statefulset.yaml
docker.elastic.co/elasticsearch/elasticsearch-oss:6.5.4

#fluentd-es-ds.yaml
willdockerhub/fluentd-elasticsearch:v2.3.2

#kibana-deployment.yaml
docker.elastic.co/kibana/kibana-oss:6.5.4
```  

4、Node节点打标签  
Fluentd是以DaemonSet的形式运行在Kubernetes集群中，这样就可以保证集群中每个Node上都会启动一个Fluentd 

发现NODE-SELECTOR选项beta.kubernetes.io/fluentd-ds-ready=true 只会调度到标签beta.kubernetes.io/fluentd-ds-ready=true 的节点,否则无法正常启动  

发现没有这个标签，为需要收集日志的Node 打上这个标签：  
```
$ kubectl label node k8s-node1 beta.kubernetes.io/fluentd-ds-ready=true
node/k8s-node1 labeled
$ kubectl label node k8s-node2 beta.kubernetes.io/fluentd-ds-ready=true
node/k8s-node2 labeled
```  

5、所有准备工作完成后，通过kubectl apply -f .直接进行部署：  
```
$ kubectl apply -f .
service/elasticsearch-logging created serviceaccount/elasticsearch-logging created
clusterrole.rbac.authorization.k8s.io/elasticsearch-logging created
clusterrolebinding.rbac.authorization.k8s.io/elasticsearch-logging created
statefulset.apps/elasticsearch-logging created
configmap/fluentd-es-config-v0.1.6 created
serviceaccount/fluentd-es created
clusterrole.rbac.authorization.k8s.io/fluentd-es created
clusterrolebinding.rbac.authorization.k8s.io/fluentd-es created
daemonset.apps/fluentd-es-v2.2.1 created
deployment.apps/kibana-logging created
service/kibana-logging created
```  

6、查看pod状态：
```
$ kubectl get pod -n kube-system -o wide
NAME                                    READY STATUS   RESTARTS   AGE   IP           NODE       NOMINATED NODE READINESS GATES 
coredns-78d4cf999f-7hv9m                1/1  Running   6        15d   10.244.0.15    k8s-master   <none>        <none>
coredns-78d4cf999f-lj5rg                1/1  Running   6        15d   10.244.0.14    k8s-master   <none>        <none>
elasticsearch-logging-0                 1/1  Running   0        97m   10.244.1.105   k8s-node1    <none>        <none>
elasticsearch-logging-1                 1/1  Running   0        96m   10.244.2.95    k8s-node2    <none>        <none>
etcd-k8s-master                         1/1  Running   6        15d   192.168.92.56  k8s-master   <none>        <none>
fluentd-es-v2.3.2-jkkgp                 1/1  Running   0        97m   10.244.1.104   k8s-node1    <none>        <none>
fluentd-es-v2.3.2-kj4f7                 1/1  Running   0        97m   10.244.2.93    k8s-node2    <none>        <none>
kibana-logging-7b59799486-wg97l         1/1  Running   0        97m   10.244.2.94    k8s-node2    <none>        <none>
kube-apiserver-k8s-master               1/1  Running   6        15d   192.168.92.56  k8s-master   <none>        <none>
kube-controller-manager-k8s-master      1/1  Running   7        15d   192.168.92.56  k8s-master   <none>        <none>
kube-flannel-ds-amd64-ccjrp             1/1  Running   6        15d   192.168.92.56  k8s-master   <none>        <none>
kube-flannel-ds-amd64-lzx5v             1/1  Running   9        15d   192.168.92.58  k8s-node2    <none>        <none>
kube-flannel-ds-amd64-qtnx6             1/1  Running   7        15d   192.168.92.57  k8s-node1    <none>        <none>
kube-proxy-89d96                        1/1  Running   0        7h32m 192.168.92.57  k8s-node1    <none>        <none>
kube-proxy-t2vfx                        1/1  Running   0        7h32m 192.168.92.56  k8s-master   <none>        <none>
kube-proxy-w6pl4                        1/1  Running   0        7h32m 192.168.92.58  k8s-node2    <none>        <none>
kube-scheduler-k8s-master               1/1  Running   7        15d   192.168.92.56  k8s-master   <none>        <none>
kubernetes-dashboard-847f8cb7b8-wrm4l   1/1  Running   8        15d   10.244.2.80   k8s-node2     <none>        <none>
tiller-deploy-7bf99c9559-8p7w4          1/1  Running   5        6d21h 10.244.1.90
```
