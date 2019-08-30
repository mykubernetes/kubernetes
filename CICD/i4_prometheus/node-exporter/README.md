1、部署node-export  
```
cat prometheus-node-exporter.yaml
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: kube-system
  labels:
    name: node-exporter
spec:
  template:
    metadata:
      labels:
        name: node-exporter
    spec:
      hostPID: true
      hostIPC: true
      hostNetwork: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:v0.16.0
        ports:
        - containerPort: 9100
        resources:
          requests:
            cpu: 0.15
        securityContext:
          privileged: true
        args:
        - --path.procfs
        - /host/proc
        - --path.sysfs
        - /host/sys
        - --collector.filesystem.ignored-mount-points
        - '"^/(sys|proc|dev|host|etc)($|/)"'
        volumeMounts:
        - name: dev
          mountPath: /host/dev
        - name: proc
          mountPath: /host/proc
        - name: sys
          mountPath: /host/sys
        - name: rootfs
          mountPath: /rootfs
      tolerations:
      - key: "node-role.kubernetes.io/master"
        operator: "Exists"
        effect: "NoSchedule"
      volumes:
        - name: proc
          hostPath:
            path: /proc
        - name: dev
          hostPath:
            path: /dev
        - name: sys
          hostPath:
            path: /sys
        - name: rootfs
          hostPath:
            path: /
```  
由于获取主机的监控指标数据，node-exporter是运行在容器中的，所以在Pod中需要配置一些Pod的安全策略  
- hostPID:true 
- hostIPC:true
- hostNetwork:true

将主机/dev、/proc、/sys这些目录挂在到容器中，因为采集的很多节点数据都是通过这些文件来获取系统信息  
比如top命令可以查看当前cpu使用情况，数据就来源于/proc/stat，使用free命令可以查看当前内存使用情况，其数据来源是/proc/meminfo文件  
- path: /proc
- path: /dev
- path: /sys

使用kubeadm搭建的，同时需要监控master节点的，则需要添加下方的相应容忍  
```
- key: "node-role.kubernetes.io/master"
        operator: "Exists"
        effect: "NoSchedule
```  

node-exporter容器相关启动参数  
```
        args:
        - --path.procfs     #配置挂载宿主机（node节点）的路径
        - /host/proc
        - --path.sysfs      #配置挂载宿主机（node节点）的路径
        - /host/sys
        - --collector.filesystem.ignored-mount-points
        - '"^/(sys|proc|dev|host|etc)($|/)"'
```  



```
# kubectl create -f prometheus-node-exporter.yaml
daemonset.extensions/node-exporter created


# kubectl get pod -n kube-system -o wide|grep node
node-exporter-rtkbh                     1/1     Running            0          25s     10.4.82.139   abcdocker82-139.opi.com              
node-exporter-snvl4                     1/1     Running            0          25s     10.4.82.140   abcdocker82-140.opi.com              
node-exporter-wz4z4                     1/1     Running            0          25s     10.4.82.138   abcdocker82-138.opi.com              
node-exporter-x8lv4                     1/1     Running            0          25s     10.4.82.142   abcdockerl82-142.opi.com              

在任意集群节点curl 9100/metrics
# curl 127.0.0.1:9100/metrics
```  



prometheus的服务发现配置
```
关于服务发现
    - job_name: 'kubernetes-node'
      kubernetes_sd_configs:
      - role: node

metrics监听的端口是10250而并不是我们设置的9100，这里使用__address__标签替换10250端口为9100
    - job_name: 'kubernetes-node'
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        replacement: '${1}:9100'
        target_label: __address__
        action: replace
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

cAdvisor是一个容器资源监控工具，包括容器的内存，CPU，网络IO，资源IO等资源，同时提供了一个Web页面用于查看容器的实时运行状态。 
cAvisor已经内置在了kubelet组件之中，所以我们不需要单独去安装，cAdvisor的数据路径为/api/v1/nodes//proxy/metrics

    - job_name: 'kubernetes-cadvisor'
      kubernetes_sd_configs:
      - role: node
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics/cadvisor

Api-Service 监控
apiserver作为Kubernetes最核心的组件，它的监控也是非常有必要的，对于apiserver的监控，我们可以直接通过kubernetes的service来获取

   - job_name: 'kubernetes-apiserver'
     kubernetes_sd_configs:
     - role: endpoints

这里我们使用keep动作，将符合配置的保留下来，例如我们过滤default命名空间下服务名称为kubernetes的元数据，这里可以根据__meta_kubernetes_namespace和__mate_kubertnetes_service_name2个元数据进行relabel
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https
 
Service 监控
这里我们对service进行过滤，只有在service配置了prometheus.io/scrape: "true"过滤出来
    - job_name: 'kubernetes-service-endpoints'
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scheme]
        action: replace
        target_label: __scheme__
        regex: (https?)
      - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_service_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_service_name]
        action: replace
        target_label: kubernetes_name

只有如下配置的才会被发现
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: redis
  namespace: abcdocker
  annotations:
    prometheus.io/scrape: "true"      #添加标签
    prometheus.io/port: "9121"        #添加标签端口
spec:
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:4
        resources:
          requests:
            cpu: 100m
            memory: 100Mi
        ports:
        - containerPort: 6379
      - name: redis-exporter
        image: oliver006/redis_exporter:latest
        resources:
          requests:
            cpu: 100m
            memory: 100Mi
        ports:
        - containerPort: 9121
---
kind: Service
apiVersion: v1
metadata:
  name: redis
  namespace: abcdocker
spec:
  selector:
    app: redis
  ports:
  - name: redis
    port: 6379
    targetPort: 6379
  - name: prom
    port: 9121
    targetPort: 9121

添加服务器发现配置
kubectl apply -f prometheus.configmap.yaml
热更新刷新配置
curl -X POST http://10.101.143.162:9090/-/reload
```  
