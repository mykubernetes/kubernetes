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



prometheus的服务发现  
```
    - job_name: 'kubernetes-node'
      kubernetes_sd_configs:
      - role: node

添加服务器发现配置
kubectl apply -f prometheus.configmap.yaml
热更新刷新配置
curl -X POST http://10.101.143.162:9090/-/reload
```  
