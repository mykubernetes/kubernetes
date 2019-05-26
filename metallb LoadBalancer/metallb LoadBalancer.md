部署metallb
============
官方部署metallb文档：  
https://metallb.universe.tf/tutorial/layer2/  
项目地址：  
https://github.com/google/metallb：  
部署metallb负载均衡器  

1、Metallb 支持 Helm 和 YAML 两种安装方法，这里我们使用第二种：  
```
# wget https://raw.githubusercontent.com/google/metallb/v0.7.3/manifests/metallb.yaml
# cat metallb.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: metallb-system
  labels:
    app: metallb
---

apiVersion: v1
kind: ServiceAccount
metadata:
  namespace: metallb-system
  name: controller
  labels:
    app: metallb
---
apiVersion: v1
kind: ServiceAccount
metadata:
  namespace: metallb-system
  name: speaker
  labels:
    app: metallb

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: metallb-system:controller
  labels:
    app: metallb
rules:
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list", "watch", "update"]
- apiGroups: [""]
  resources: ["services/status"]
  verbs: ["update"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: metallb-system:speaker
  labels:
    app: metallb
rules:
- apiGroups: [""]
  resources: ["services", "endpoints", "nodes"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: metallb-system
  name: config-watcher
  labels:
    app: metallb
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]
---

## Role bindings
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: metallb-system:controller
  labels:
    app: metallb
subjects:
- kind: ServiceAccount
  name: controller
  namespace: metallb-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: metallb-system:controller
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: metallb-system:speaker
  labels:
    app: metallb
subjects:
- kind: ServiceAccount
  name: speaker
  namespace: metallb-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: metallb-system:speaker
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: metallb-system
  name: config-watcher
  labels:
    app: metallb
subjects:
- kind: ServiceAccount
  name: controller
- kind: ServiceAccount
  name: speaker
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: config-watcher
---
apiVersion: apps/v1beta2
kind: DaemonSet
metadata:
  namespace: metallb-system
  name: speaker
  labels:
    app: metallb
    component: speaker
spec:
  selector:
    matchLabels:
      app: metallb
      component: speaker
  template:
    metadata:
      labels:
        app: metallb
        component: speaker
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "7472"
    spec:
      serviceAccountName: speaker
      terminationGracePeriodSeconds: 0
      hostNetwork: true
      containers:
      - name: speaker
        image: metallb/speaker:v0.7.3
        imagePullPolicy: IfNotPresent
        args:
        - --port=7472
        - --config=config
        env:
        - name: METALLB_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        ports:
        - name: monitoring
          containerPort: 7472
        resources:
          limits:
            cpu: 100m
            memory: 100Mi
          
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - all
            add:
            - net_raw

---
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  namespace: metallb-system
  name: controller
  labels:
    app: metallb
    component: controller
spec:
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: metallb
      component: controller
  template:
    metadata:
      labels:
        app: metallb
        component: controller
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "7472"
    spec:
      serviceAccountName: controller
      terminationGracePeriodSeconds: 0
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534 # nobody
      containers:
      - name: controller
        image: metallb/controller:v0.7.3
        imagePullPolicy: IfNotPresent
        args:
        - --port=7472
        - --config=config
        ports:
        - name: monitoring
          containerPort: 7472
        resources:
          limits:
            cpu: 100m
            memory: 100Mi
          
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - all
          readOnlyRootFilesystem: true

---




# kubectl apply -f metallb.yaml
```  

2、查看运行的pod  
metalLB包含两个部分： a cluster-wide controller, and a per-machine protocol speaker.  
```
# kubectl get pod -n metallb-system  -o wide
NAME                          READY   STATUS    RESTARTS   AGE    IP               NODE     NOMINATED NODE   READINESS GATES
controller-7cc9c87cfb-plqtm   1/1     Running   0          3m4s   10.244.2.2       node03   <none>           <none>
speaker-562p7                 1/1     Running   0          3m4s   192.168.101.67   node02   <none>           <none>
speaker-wvr46                 1/1     Running   0          3m4s   192.168.101.68   node03   <none>           <none>
```  

3、查看其它信息  
包含了 “controller” deployment,和 the “speaker” DaemonSet.  
```
# kubectl get daemonset -n metallb-system 
NAME      DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
speaker   2         2         2       2            2           <none>          3m57s

# kubectl get deployment -n metallb-system 
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
controller   1/1     1            1           4m23s
```  

4、目前还没有宣布任何内容，因为我们没有提供ConfigMap，也没有提供负载均衡地址的服务。  
接下来我们要生成一个 Configmap 文件，为 Metallb 设置网址范围以及协议相关的选择和配置，这里以一个简单的二层配置为例。  

创建config.yaml提供IP池  
```
# wget https://raw.githubusercontent.com/google/metallb/v0.7.3/manifests/example-layer2-config.yaml
```  
修改ip地址池和集群节点网段相同  
```
# vim example-layer2-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  namespace: metallb-system
  name: config
data:
  config: |
    address-pools:
    - name: my-ip-space
      protocol: layer2
      addresses:
      - 192.168.101.100-192.168.101.200
```  
注意：这里的 IP 地址范围需要跟集群实际情况相对应。  

执行yaml文件  
```
# kubectl apply -f example-layer2-config.yaml
```  

5、创建后端应用和服务测试  
```
# wget https://raw.githubusercontent.com/google/metallb/master/manifests/tutorial-2.yaml
# cat tutorial-2.yaml
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: nginx
spec:
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1
        ports:
        - name: http
          containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 80
  selector:
    app: nginx
  type: LoadBalancer


# kubectl apply -f tutorial-2.yaml
```  

查看yaml文件配置，包含了一个deployment和一个LoadBalancer类型的service，默认即可。  
```
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: nginx
spec:
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1
        ports:
        - name: http
          containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 80
  selector:
    app: nginx
  type: LoadBalancer
```  

查看service分配的EXTERNAL-IP  
```
# kubectl get service 
NAME         TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
kubernetes   ClusterIP      10.96.0.1       <none>          443/TCP        98m
nginx        LoadBalancer   10.98.204.137   192.168.101.100   80:30511/TCP   93s
```  

集群内访问该IP地址  
```
# curl 192.168.101.100
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>

<p><em>Thank you for using nginx.</em></p>
</body>
</html>
```  

ping该ip地址，发现从pod所在节点192.168.101.100发起的请求：  
```
# ping 192.168.101.100
PING 192.168.101.100 (192.168.101.100) 56(84) bytes of data.
64 bytes from 192.168.101.100: icmp_seq=1 ttl=64 time=107 ms
64 bytes from 192.168.101.100: icmp_seq=2 ttl=64 time=3.60 ms
64 bytes from 192.168.101.100: icmp_seq=3 ttl=64 time=3.85 ms
```  

浏览器访问  
http://192.168.101.100  
可以打开nginx  

此IP地址在集群外无法ping通，但可以访问80端口：  
命令行终端执行telnet 192.168.101.100 80测试成功。  

到这里metallb loadbalancer部署完成，你可以定义kubernetes dashboard，granafa dashboard等各种应用服务，以loadbalancer的方式直接访问，不是一般的方便。
