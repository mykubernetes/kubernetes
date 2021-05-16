场景需求
===
Kubernetes的两个Service（ServiceA、ServiceB）和对应的Pod（PodA、PodB）分别属于不同的namespace名称空间，现需要PodA和PodB跨namespace名称空间并通过Service实现互访。

说明：这里是指通过Service的Name进行通信访问，而不是通过Service的IP【因因为每次重启Service，NAME不会改变，而IP是会改变的】。

1、创建Service和Pod
```
# cat deply_service_myns.yaml 
apiVersion: v1
kind: Namespace
metadata:
  name: myns
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deploy1
  namespace: myns
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
      release: v1
  template:
    metadata:
      labels:
        app: myapp
        release: v1
    spec:
      containers:
      - name: myapp
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-clusterip1
  namespace: myns
spec:
  type: ClusterIP  # 默认类型
  selector:
    app: myapp
    release: v1
  ports:
  - name: http
    port: 80
    targetPort: 80


# cat deply_service_mytest.yaml 
apiVersion: v1
kind: Namespace
metadata:
  name: mytest
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deploy2
  namespace: mytest
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
      release: v2
  template:
    metadata:
      labels:
        app: myapp
        release: v2
    spec:
      containers:
      - name: myapp
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v2
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-clusterip2
  namespace: mytest
spec:
  type: ClusterIP  # 默认类型
  selector:
    app: myapp
    release: v2
  ports:
  - name: http
    port: 80
    targetPort: 80
```

2、运行yaml文件
```
kubectl apply -f deply_service_myns.yaml 
kubectl apply -f deply_service_mytest.yaml
```

3、查看myns名称空间信息
```
# kubectl get svc -n myns -o wide
NAME               TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE   SELECTOR
myapp-clusterip1   ClusterIP   10.100.61.11   <none>        80/TCP    3m    app=myapp,release=v1

# kubectl get deploy -n myns -o wide
NAME            READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS   IMAGES                                                      SELECTOR
myapp-deploy1   2/2     2            2           3m7s   myapp        registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp,release=v1

# kubectl get rs -n myns -o wide
NAME                       DESIRED   CURRENT   READY   AGE     CONTAINERS   IMAGES                                                      SELECTOR
myapp-deploy1-5b9d78576c   2         2         2       3m15s   myapp        registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp,pod-template-hash=5b9d78576c,release=v1

# kubectl get pod -n myns -o wide
NAME                             READY   STATUS    RESTARTS   AGE     IP             NODE         NOMINATED NODE   READINESS GATES
myapp-deploy1-5b9d78576c-wfw4n   1/1     Running   0          3m20s   10.244.2.136   k8s-node02   <none>           <none>
myapp-deploy1-5b9d78576c-zsfjl   1/1     Running   0          3m20s   10.244.3.193   k8s-node01   <none>           <none>
```

4、查看mytest名称空间信息
```
# kubectl get svc -n mytest -o wide
NAME               TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE    SELECTOR
myapp-clusterip2   ClusterIP   10.100.201.103   <none>        80/TCP    4m9s   app=myapp,release=v2

# kubectl get deploy -n mytest -o wide
NAME            READY   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS   IMAGES                                                      SELECTOR
myapp-deploy2   2/2     2            2           4m15s   myapp        registry.cn-beijing.aliyuncs.com/google_registry/myapp:v2   app=myapp,release=v2

# kubectl get rs -n mytest -o wide
NAME                      DESIRED   CURRENT   READY   AGE     CONTAINERS   IMAGES                                                      SELECTOR
myapp-deploy2-dc8f96497   2         2         2       4m22s   myapp        registry.cn-beijing.aliyuncs.com/google_registry/myapp:v2   app=myapp,pod-template-hash=dc8f96497,release=v2

# kubectl get pod -n mytest -o wide
NAME                            READY   STATUS    RESTARTS   AGE     IP             NODE         NOMINATED NODE   READINESS GATES
myapp-deploy2-dc8f96497-nnkqn   1/1     Running   0          4m27s   10.244.3.194   k8s-node01   <none>           <none>
myapp-deploy2-dc8f96497-w47dt   1/1     Running   0          4m27s   10.244.2.137   k8s-node02   <none>           <none>
```

5、只看Service和Pod
```
# kubectl get pod -A -o wide | grep -E '(my)|(NAME)'
NAMESPACE              NAME                                         READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
myns                   myapp-deploy1-5b9d78576c-wfw4n               1/1     Running   0          41m   10.244.2.136   k8s-node02   <none>           <none>
myns                   myapp-deploy1-5b9d78576c-zsfjl               1/1     Running   0          41m   10.244.3.193   k8s-node01   <none>           <none>
mytest                 myapp-deploy2-dc8f96497-nnkqn                1/1     Running   0          41m   10.244.3.194   k8s-node01   <none>           <none>
mytest                 myapp-deploy2-dc8f96497-w47dt                1/1     Running   0          41m   10.244.2.137   k8s-node02   <none>           <none>

# kubectl get svc -A -o wide | grep -E '(my)|(NAME)'
NAMESPACE              NAME                        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                  AGE   SELECTOR
myns                   myapp-clusterip1            ClusterIP   10.100.61.11     <none>        80/TCP                   41m   app=myapp,release=v1
mytest                 myapp-clusterip2            ClusterIP   10.100.201.103   <none>        80/TCP                   41m   app=myapp,release=v2
```

6、pod跨名称空间namespace与Service通信

说明：是通过Service的NAME进行通信，而不是Service的IP【因为每次重启Service，NAME不会改变，而IP是会改变的】。
```
# 进入ns名称空间下的一个Pod容器
# kubectl exec -it -n myns myapp-deploy1-5b9d78576c-wfw4n sh
/ # cd /root/

### 如下说明在同一名称空间下，通信无问题
~ # ping myapp-clusterip1 
PING myapp-clusterip1 (10.100.61.11): 56 data bytes
64 bytes from 10.100.61.11: seq=0 ttl=64 time=0.046 ms
64 bytes from 10.100.61.11: seq=1 ttl=64 time=0.081 ms


~ # wget myapp-clusterip1 -O myns.html
Connecting to myapp-clusterip1 (10.100.61.11:80)
myns.html            100%


~ # cat myns.html 
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>

### 如下说明在不同的名称空间下，通过Service的NAME进行通信存在问题
~ # ping myapp-clusterip2
ping: bad address 'myapp-clusterip2'


~ # wget myapp-clusterip2 -O mytest.html
wget: bad address 'myapp-clusterip2'
```

7、实现跨namespace与Service通信

通过Service的ExternalName类型即可实现跨namespace名称空间与Service通信。

Service域名格式：$(service name).$(namespace).svc.cluster.local，其中 cluster.local 为指定的集群的域名
```
# cat svc_ExternalName_visit.yaml 
# 实现 myns 名称空间的pod，访问 mytest 名称空间的Service：myapp-clusterip2
apiVersion: v1
kind: Service
metadata:
  name: myapp-clusterip1-externalname
  namespace: myns
spec:
  type: ExternalName
  externalName: myapp-clusterip2.mytest.svc.cluster.local
  ports:
  - name: http
    port: 80
    targetPort: 80
---
# 实现 mytest 名称空间的Pod，访问 myns 名称空间的Service：myapp-clusterip1
apiVersion: v1
kind: Service
metadata:
  name: myapp-clusterip2-externalname
  namespace: mytest
spec:
  type: ExternalName
  externalName: myapp-clusterip1.myns.svc.cluster.local
  ports:
  - name: http
    port: 80
    targetPort: 80
```

8、运行yaml文件
```
[root@k8s-master cross_ns]# kubectl apply -f svc_ExternalName_visit.yaml
[root@k8s-master cross_ns]# 
[root@k8s-master cross_ns]# kubectl get svc -A -o wide | grep -E '(ExternalName)|(NAME)' 
NAMESPACE              NAME                            TYPE           CLUSTER-IP       EXTERNAL-IP                                 PORT(S)                  AGE   SELECTOR
myns                   myapp-clusterip1-externalname   ExternalName   <none>           myapp-clusterip2.mytest.svc.cluster.local   80/TCP                   28s   <none>
mytest                 myapp-clusterip2-externalname   ExternalName   <none>           myapp-clusterip1.myns.svc.cluster.local     80/TCP                   28s   <none>
```

9、pod跨名称空间namespace与Service通信

到目前所有service和pod信息查看
```
# kubectl get svc -A -o wide | grep -E '(my)|(NAME)'
NAMESPACE              NAME                            TYPE           CLUSTER-IP       EXTERNAL-IP                                 PORT(S)                  AGE   SELECTOR
myns                   myapp-clusterip1                ClusterIP      10.100.61.11     <none>                                      80/TCP                   62m   app=myapp,release=v1
myns                   myapp-clusterip1-externalname   ExternalName   <none>           myapp-clusterip2.mytest.svc.cluster.local   80/TCP                   84s   <none>
mytest                 myapp-clusterip2                ClusterIP      10.100.201.103   <none>                                      80/TCP                   62m   app=myapp,release=v2
mytest                 myapp-clusterip2-externalname   ExternalName   <none>           myapp-clusterip1.myns.svc.cluster.local     80/TCP                   84s   <none>

# kubectl get pod -A -o wide | grep -E '(my)|(NAME)'
NAMESPACE              NAME                                         READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
myns                   myapp-deploy1-5b9d78576c-wfw4n               1/1     Running   0          62m   10.244.2.136   k8s-node02   <none>           <none>
myns                   myapp-deploy1-5b9d78576c-zsfjl               1/1     Running   0          62m   10.244.3.193   k8s-node01   <none>           <none>
mytest                 myapp-deploy2-dc8f96497-nnkqn                1/1     Running   0          62m   10.244.3.194   k8s-node01   <none>           <none>
mytest                 myapp-deploy2-dc8f96497-w47dt                1/1     Running   0          62m   10.244.2.137   k8s-node02   <none>           <none>
```

10、myns 名称空间的pod，访问 mytest 名称空间的Service：myapp-clusterip2
```
# kubectl exec -it -n myns myapp-deploy1-5b9d78576c-wfw4n sh
/ # cd /root/
### 如下说明在同一名称空间下，通信无问题
~ # ping myapp-clusterip1 
PING myapp-clusterip1 (10.100.61.11): 56 data bytes
64 bytes from 10.100.61.11: seq=0 ttl=64 time=0.057 ms
64 bytes from 10.100.61.11: seq=1 ttl=64 time=0.071 ms
………………
~ # 
~ # wget myapp-clusterip1 -O myns.html
Connecting to myapp-clusterip1 (10.100.61.11:80)
myns.html            100%
~ # 
~ # cat myns.html 
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>

### 如下说明通过Service externalname类型，实现了Pod跨namespace名称空间与Service访问
~ # ping myapp-clusterip1-externalname
PING myapp-clusterip1-externalname (10.100.201.103): 56 data bytes
64 bytes from 10.100.201.103: seq=0 ttl=64 time=0.050 ms
64 bytes from 10.100.201.103: seq=1 ttl=64 time=0.311 ms
………………
~ # 
~ # wget myapp-clusterip1-externalname -O mytest.html
Connecting to myapp-clusterip1-externalname (10.100.201.103:80)
mytest.html          100%
~ # 
~ # cat mytest.html 
Hello MyApp | Version: v2 | <a href="hostname.html">Pod Name</a>
```

11、mytest 名称空间的Pod，访问 myns 名称空间的Service：myapp-clusterip1
```
# kubectl exec -it -n mytest myapp-deploy2-dc8f96497-w47dt sh
/ # cd /root/
### 如下说明在同一名称空间下，通信无问题
~ # ping myapp-clusterip2 
PING myapp-clusterip2 (10.100.201.103): 56 data bytes
64 bytes from 10.100.201.103: seq=0 ttl=64 time=0.087 ms
64 bytes from 10.100.201.103: seq=1 ttl=64 time=0.073 ms
………………
~ # 
~ # wget myapp-clusterip2 -O mytest.html
Connecting to myapp-clusterip2 (10.100.201.103:80)
mytest.html          100%
~ # 
~ # cat mytest.html 
Hello MyApp | Version: v2 | <a href="hostname.html">Pod Name</a>

### 如下说明通过Service externalname类型，实现了Pod跨namespace名称空间与Service访问
~ # ping myapp-clusterip2-externalname
PING myapp-clusterip2-externalname (10.100.61.11): 56 data bytes
64 bytes from 10.100.61.11: seq=0 ttl=64 time=0.089 ms
64 bytes from 10.100.61.11: seq=1 ttl=64 time=0.071 ms
………………
~ # 
~ # wget myapp-clusterip2-externalname -O myns.html
Connecting to myapp-clusterip2-externalname (10.100.61.11:80)
myns.html            100%
~ # 
~ # cat myns.html 
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
```
由上可见，实现了Pod跨namespace名称空间与Service访问。
