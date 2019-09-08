LXCFS简介  
---
https://github.com/lxc/lxcfs  

社区中常见的做法是利用 lxcfs来提供容器中的资源可见性。lxcfs 是一个开源的FUSE（用户态文件系统）实现来支持LXC容器，它也可以支持Docker容器。  

LXCFS通过用户态文件系统，在容器中提供下列 procfs 的文件  
```
/proc/cpuinfo
/proc/diskstats
/proc/meminfo
/proc/stat
/proc/swaps
/proc/uptime
```  
比如，把宿主机的 /var/lib/lxcfs/proc/memoinfo 文件挂载到Docker容器的/proc/meminfo位置后。容器中进程读取相应文件内容时，LXCFS的FUSE实现会从容器对应的Cgroup中读取正确的内存限制。从而使得应用获得正确的资源约束设定。  

Docker环境下LXCFS使用
---
1、安装lxcfs的RPM包
```
wget https://copr-be.cloud.fedoraproject.org/results/ganto/lxd/epel-7-x86_64/00486278-lxcfs/lxcfs-2.0.5-3.el7.centos.x86_64.rpm
yum install lxcfs-2.0.5-3.el7.centos.x86_64.rpm
```  

2、启动 lxcfs  
```
lxcfs /var/lib/lxcfs &  
```  

3、测试  
```
$docker run -it -m 256m \
      -v /var/lib/lxcfs/proc/cpuinfo:/proc/cpuinfo:rw \
      -v /var/lib/lxcfs/proc/diskstats:/proc/diskstats:rw \
      -v /var/lib/lxcfs/proc/meminfo:/proc/meminfo:rw \
      -v /var/lib/lxcfs/proc/stat:/proc/stat:rw \
      -v /var/lib/lxcfs/proc/swaps:/proc/swaps:rw \
      -v /var/lib/lxcfs/proc/uptime:/proc/uptime:rw \
      ubuntu:16.04 /bin/bash

root@f4a2a01e61cd:/# free
              total        used        free      shared  buff/cache   available
Mem:         262144         708      261436        2364           0      261436
Swap:             0           0           0
```  
可以看到total的内存为256MB，配置已经生效  


lxcfs 的 Kubernetes实践  
---

首先要在集群节点上安装并启动lxcfs，用Kubernetes的方式，用利用容器和DaemonSet方式来运行lxcfs FUSE文件系统  
1、通过以下地址从Github上获得  
```
git clone https://github.com/denverdino/lxcfs-initializer
cd lxcfs-initializer
```  

2、其manifest文件如下  
```
apiVersion: apps/v1beta2
kind: DaemonSet
metadata:
  name: lxcfs
  labels:
    app: lxcfs
spec:
  selector:
    matchLabels:
      app: lxcfs
  template:
    metadata:
      labels:
        app: lxcfs
    spec:
      hostPID: true
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: lxcfs
        image: registry.cn-hangzhou.aliyuncs.com/denverdino/lxcfs:2.0.8
        imagePullPolicy: Always
        securityContext:
          privileged: true
        volumeMounts:
        - name: rootfs
          mountPath: /host
      volumes:
      - name: rootfs
        hostPath:
          path: /
```  
注： 由于lxcfs FUSE需要共享系统的PID名空间以及需要特权模式，所有我们配置了相应的容器启动参数。

3、在所有集群节点上自动安装、部署完成 lxcfs  
```
kubectl create -f lxcfs-daemonset.yaml
```  

4、manifest 文件如下  
```
# vim lxcfs-initializer.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: lxcfs-initializer-default
  namespace: default
rules:
- apiGroups: ["*"]
  resources: ["deployments"]
  verbs: ["initialize", "patch", "watch", "list"]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: lxcfs-initializer-service-account
  namespace: default
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: lxcfs-initializer-role-binding
subjects:
- kind: ServiceAccount
  name: lxcfs-initializer-service-account
  namespace: default
roleRef:
  kind: ClusterRole
  name: lxcfs-initializer-default
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  initializers:
    pending: []
  labels:
    app: lxcfs-initializer
  name: lxcfs-initializer
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: lxcfs-initializer
      name: lxcfs-initializer
    spec:
      serviceAccountName: lxcfs-initializer-service-account
      containers:
        - name: lxcfs-initializer
          image: registry.cn-hangzhou.aliyuncs.com/denverdino/lxcfs-initializer:0.0.2
          imagePullPolicy: Always
          args:
            - "-annotation=initializer.kubernetes.io/lxcfs"
            - "-require-annotation=true"
---
apiVersion: admissionregistration.k8s.io/v1alpha1
kind: InitializerConfiguration
metadata:
  name: lxcfs.initializer
initializers:
  - name: lxcfs.initializer.kubernetes.io
    rules:
      - apiGroups:
          - "*"
        apiVersions:
          - "*"
        resources:
          - deployments
```  
注： 这是一个典型的 Initializer 部署描述，首先我们创建了service account lxcfs-initializer-service-account，并对其授权了 "deployments" 资源的查找、更改等权限。然后我们部署了一个名为 "lxcfs-initializer"的Initializer，利用上述SA启动一个容器来处理对 “deployments” 资源的创建，如果deployment中包含 initializer.kubernetes.io/lxcfs为true的注释，就会对该应用中容器进行文件挂载

5、部署  
```
kubectl apply -f lxcfs-initializer.yaml
```  

6、部署一个简单的Apache应用，为其分配256MB内存，并且声明了如下注释"initializer.kubernetes.io/lxcfs": "true"
```
# vim  web.yaml
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  annotations:
    "initializer.kubernetes.io/lxcfs": "true"
  labels:
    app: web
  name: web
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: web
      name: web
    spec:
      containers:
        - name: web
          image: httpd:2
          imagePullPolicy: Always
          resources:
            requests:
              memory: "256Mi"
              cpu: "500m"
            limits:
              memory: "256Mi"
              cpu: "500m"
```  

7、部署和测试  
```
$ kubectl create -f web.yaml 
deployment "web" created

$ kubectl get pod
NAME                                 READY     STATUS    RESTARTS   AGE
web-7f6bc6797c-rb9sk                 1/1       Running   0          32s

$ kubectl exec web-7f6bc6797c-rb9sk free
             total       used       free     shared    buffers     cached      -/+ buffers/cache: 
Mem:        262144       2876     259268       2292          0        304      2572     259572
Swap:            0          0          0
```  
可以看到 free 命令返回的 total memory 就是我们设置的容器资源容量  

8、检查上述Pod的配置，果然相关的 procfs 文件都已经挂载正确  
```
$ kubectl describe pod web-7f6bc6797c-rb9sk
...
    Mounts:
      /proc/cpuinfo from lxcfs-proc-cpuinfo (rw)
      /proc/diskstats from lxcfs-proc-diskstats (rw)
      /proc/meminfo from lxcfs-proc-meminfo (rw)
      /proc/stat from lxcfs-proc-stat (rw)
...
```  















