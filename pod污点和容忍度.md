Taints污点和Tolerations容忍概述
===
节点和Pod亲和力，是将Pod吸引到一组节点【根据拓扑域】（作为优选或硬性要求）。污点（Taints）则相反，它们允许一个节点排斥一组Pod。
- 容忍（Tolerations）应用于pod，允许（但不强制要求）pod调度到具有匹配污点的节点上。
- 污点（Taints）和容忍（Tolerations）共同作用，确保pods不会被调度到不适当的节点。一个或多个污点应用于节点；这标志着该节点不应该接受任何不容忍污点的Pod。

说明：我们在平常使用中发现pod不会调度到k8s的master节点，就是因为master节点存在污点。


Node的污点  
===
- NoSchedule:不能容忍此污点的新Pod对象不可调度至当前节点,属于强制型约束关系,节点上现存的 Pod 对象不受影响。

- PreferNoSchedule:NoSchedule的柔性约束版本,即不能容忍此污点的新 Pod 对象尽量不要调度至当前节点,不过无其他节点可供调度时也允许接受相应的Pod对象.节点上现存的Pod对象不受影响。

- NoExecute:不能容忍此污点的新Pod对象不可调度至当前节点,属于强制型约束关系,而且节点上现存的Pod对象因节点污点变动或Pod容忍度变动而不再满足匹配规则时,Pod对象将被驱逐。 

- 一个节点可以使用配置使用多个污点，一个pod对象也可以有多个容忍度

kubernetes内建使用的污点  
```
node.kubernetes.io/not-ready:    节点进入"NotReady"状态时被自动添加的污点
node.alpha.kubernetes.io/unreachable:   节点进入"NotReachable"状态时被自动添加的污点。 
node.kubernetes.io/out-of-disk:     节点进入"OutOfDisk"状态时被自动添加的污点
node.kubernetes.io/memory-pressure:    节点内存资源面临压力
node.kubernetes.io/ disk-pressure:   节点磁盘资源面临压力
node.kubernetes.io/network-unavailable:    节点网络不可用
node.kubernetes.io/unschedulable： 节点不可调度
node.cloudprovider.kubernetes.io/uninitialized:   kubelet由外部的云环境程序启动时,它将自动为节点添加此污点,待到云控制器管理器中的控制器初始化此节点时再将 其删除。 
```  

1、查看污点
```
$ kubectl get node
NAME            STATUS   ROLES    AGE    VERSION
k8s-master      Ready    master   102d   v1.16.6
k8s-node-2-12   Ready    <none>   102d   v1.16.6
k8s-node-2-13   Ready    <none>   102d   v1.16.6


$ kubectl describe nodes k8s-master
...
CreationTimestamp:  Sat, 23 Nov 2019 00:52:45 +0800
Taints:             node-role.kubernetes.io/master:PreferNoSchedule
Unschedulable:      false
...
```

2、为node设置taint
```
语法  
# kubectl taint nodes <node name> <key>=<value> : <effect>    #key和value可以根据自己需求任意定义  

## 设置污点并不允许 Pod 调度到该节点
# kubectl taint nodes node1 node-type=production:NoSchedule

## 设置污点尽量阻止污点调度到该节点
# kubectl taint nodes node2 node-role=admin:PreferNoSchedule

## 设置污点，不允许普通 Pod 调度到该节点，且将该节点上已经存在的 Pod 进行驱逐
# kubectl taint nodes node3 node-storage=ssd:NoExecute
```  

3、删除上面的taint  
```
语法：  
# kubectl taint nodes <node-name> <key>{:<effect>}-  

删除污点，可以不指定 value，指定 [effect] 值就可删除该 key:[effect] 的污点
# kubectl taint nodes node1 node-type:NoSchedule-
# kubectl taint nodes node2 node-role:PreferNoSchedule-
# kubectl taint nodes node3 node-storage:NoExecute-
```  

4、删除指定键名的所有污点  
```
## 也可以根据 key 直接将该 key 的所有 [effect] 都删除：
# kubectl taint nodes node1 node-type-
```  

5、删除节点上全部污点信息  
``` # kubectl patch nodes node1 -p '{"spec":{"taints":[]}}' ```  


Pod对象的容忍度  
===

- 设置了污点的Node将根据taint的effect：NoSchedule、PreferNoSchedule、NoExecute和Pod之间产生互斥的关系，Pod将在一定程度上不会被调度到Node上。

1、概念
- 一个 Node 可以有多个污点。
- 一个 Pod 可以有多个容忍。
- Kuberentes 执行多个污点和容忍方法类似于过滤器。

2、注意
- 如果 Node 上带有污点 effect 为 NoSchedule，而 Node 上不带相应容忍，Kubernetes 就不会调度 Pod 到这台 Node 上。
- 如果 Node 上带有污点 effect 为 PreferNoShedule，这时候 Kubernetes 会努力不要调度这个 Pod 到这个 Node 上。
- 如果 Node 上带有污点 effect 为 NoExecute，这个已经在 Node 上运行的 Pod 会从 Node 上驱逐掉。没有运行在 Node 的 Pod 不能被调度到这个 Node 上。

```
## 容忍的 key、value 和对应 effect 也必须和污点 taints 保持一致
tolerations:                                        #spec字段下的容忍度配置              
- key: "node-type"                                  #可以容忍的自定义的key          
  operator: "Equal"                                 #污点信息完全匹配的等值
  value: "production"                               #可以容忍的自定义的value
  effect: "NoSchedule"                              #容忍的污点类型
  
## 容忍 tolerations 的 key 和要污点 taints 的 key 一致，且设置的 effect 也相同，不需要设置 value
tolerations:
- key: "node-role"
  operator: "Exists"                                ##Exists表示key存在就能容忍，value的值设置也不会不生效
  value: "admin"
  effect: "PreferNoSchedule"

##设置容忍时间
tolerations:
- key: "node.alpha.kubernetes.io/unreachable"
  operator: "Exists"                                #Exists表示key存在就能容忍，无需设置value
  effect: "NoExecute"
  tolerationSeconds: 6000                           #定义延迟驱逐当前Pod对象的时长，只能在NoExecute字段设置
```
- 其中key、value、effect要与Node上设置的taint保持一致
- operator的值为Exists时，将会忽略value；只要有key和effect就行
- tolerationSeconds：表示pod 能够容忍 effect 值为 NoExecute 的 taint；当指定了 tolerationSeconds【容忍时间】，则表示 pod 还能在这个节点上继续运行的时间长度。


3、当不指定key值时
- 当不指定key值和effect值时，且operator为Exists，表示容忍所有的污点【能匹配污点所有的keys，values和effects】
```
tolerations:
- operator: "Exists"
```  

4、当不指定effect值时
- 当不指定effect值时，则能匹配污点key对应的所有effects情况
```
tolerations:
- key: "key"
  operator: "Exists"
```  

5、当有多个Master存在时
- 当有多个Master存在时，为了防止资源浪费，可以进行如下设置：
```
kubectl taint nodes Node-name node-role.kubernetes.io/master=:PreferNoSchedule
```

多个Taints污点和多个Tolerations容忍怎么判断
---
可以在同一个node节点上设置多个污点（Taints），在同一个pod上设置多个容忍（Tolerations）。Kubernetes处理多个污点和容忍的方式就像一个过滤器：从节点的所有污点开始，然后忽略可以被Pod容忍匹配的污点；保留其余不可忽略的污点，污点的effect对Pod具有显示效果：特别是：
- 如果有至少一个不可忽略污点，effect为NoSchedule，那么Kubernetes将不调度Pod到该节点
- 如果没有effect为NoSchedule的不可忽视污点，但有至少一个不可忽视污点，effect为PreferNoSchedule，那么Kubernetes将尽量不调度Pod到该节点
- 如果有至少一个不可忽视污点，effect为NoExecute，那么Pod将被从该节点驱逐（如果Pod已经在该节点运行），并且不会被调度到该节点（如果Pod还未在该节点运行）


污点和容忍示例
===

一、Node污点为NoExecute的示例
--
1、实现如下污点
```
k8s-master 污点为：node-role.kubernetes.io/master:NoSchedule 【k8s自带污点，直接使用，不必另外操作添加】
k8s-node01 污点为：
k8s-node02 污点为：
```

2、污点查看操作如下：
```
kubectl describe node k8s-master | grep 'Taints' -A 5
kubectl describe node k8s-node01 | grep 'Taints' -A 5
kubectl describe node k8s-node02 | grep 'Taints' -A 5
```
除了k8s-master默认的污点，在k8s-node01、k8s-node02无污点。

3、污点为NoExecute示例
```
# cat noexecute_tolerations.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: noexec-tolerations-deploy
  labels:
    app: noexectolerations-deploy
spec:
  replicas: 6
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-pod
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
        imagePullPolicy: IfNotPresent
        ports:
          - containerPort: 80
       # 有容忍并有 tolerationSeconds 时的格式
#      tolerations:
#      - key: "check-mem"
#        operator: "Equal"
#        value: "memdb"
#        effect: "NoExecute"
#        # 当Pod将被驱逐时，Pod还可以在Node节点上继续保留运行的时间
#        tolerationSeconds: 30
```

4、运行yaml文件
```
# kubectl apply -f noexecute_tolerations.yaml 
deployment.apps/noexec-tolerations-deploy created

# kubectl get deploy -o wide
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
noexec-tolerations-deploy   6/6     6            6           10s   myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get pod -o wide
NAME                                         READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
noexec-tolerations-deploy-85587896f9-2j848   1/1     Running   0          15s   10.244.4.101   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-jgqkn   1/1     Running   0          15s   10.244.2.141   k8s-node02   <none>           <none>
noexec-tolerations-deploy-85587896f9-jmw5w   1/1     Running   0          15s   10.244.2.142   k8s-node02   <none>           <none>
noexec-tolerations-deploy-85587896f9-s8x95   1/1     Running   0          15s   10.244.4.102   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-t82fj   1/1     Running   0          15s   10.244.4.103   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-wx9pz   1/1     Running   0          15s   10.244.2.143   k8s-node02   <none>           <none>
```
由上可见，pod是在k8s-node01、k8s-node02平均分布的。

5、添加effect为NoExecute的污点
```
kubectl taint nodes k8s-node02 check-mem=memdb:NoExecute
```

6、此时所有节点污点为
```
k8s-master 污点为：node-role.kubernetes.io/master:NoSchedule 【k8s自带污点，直接使用，不必另外操作添加】
k8s-node01 污点为：
k8s-node02 污点为：check-mem=memdb:NoExecute
```

7、再次查看pod信息
```
# kubectl get pod -o wide
NAME                                         READY   STATUS    RESTARTS   AGE    IP             NODE         NOMINATED NODE   READINESS GATES
noexec-tolerations-deploy-85587896f9-2j848   1/1     Running   0          2m2s   10.244.4.101   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-ch96j   1/1     Running   0          8s     10.244.4.106   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-cjrkb   1/1     Running   0          8s     10.244.4.105   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-qbq6d   1/1     Running   0          7s     10.244.4.104   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-s8x95   1/1     Running   0          2m2s   10.244.4.102   k8s-node01   <none>           <none>
noexec-tolerations-deploy-85587896f9-t82fj   1/1     Running   0          2m2s   10.244.4.103   k8s-node01   <none>           <none>
```
由上可见，在k8s-node02节点上的pod已被驱逐，驱逐的pod被调度到了k8s-node01节点。

二、Pod没有容忍时（Tolerations）
--

1、节点上的污点设置（Taints）
```
k8s-master 污点为：node-role.kubernetes.io/master:NoSchedule 【k8s自带污点，直接使用，不必另外操作添加】
k8s-node01 污点为：check-nginx=web:PreferNoSchedule
k8s-node02 污点为：check-nginx=web:NoSchedule
```

2、污点添加操作如下：
```
kubectl taint nodes k8s-node01 check-nginx=web:PreferNoSchedule
kubectl taint nodes k8s-node02 check-nginx=web:NoSchedule
```

3、污点查看操作如下：
```
kubectl describe node k8s-master | grep 'Taints' -A 5
kubectl describe node k8s-node01 | grep 'Taints' -A 5
kubectl describe node k8s-node02 | grep 'Taints' -A 5
```

4、无容忍示例
```
# cat no_tolerations.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: no-tolerations-deploy
  labels:
    app: notolerations-deploy
spec:
  replicas: 5
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-pod
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
        imagePullPolicy: IfNotPresent
        ports:
          - containerPort: 80
```

5、运行yaml文件
```
# kubectl apply -f no_tolerations.yaml 
deployment.apps/no-tolerations-deploy created

# kubectl get deploy -o wide
NAME                    READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
no-tolerations-deploy   5/5     5            5           9s    myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get pod -o wide
NAME                                     READY   STATUS    RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
no-tolerations-deploy-85587896f9-6bjv8   1/1     Running   0          16s   10.244.4.54   k8s-node01   <none>           <none>
no-tolerations-deploy-85587896f9-hbbjb   1/1     Running   0          16s   10.244.4.58   k8s-node01   <none>           <none>
no-tolerations-deploy-85587896f9-jlmzw   1/1     Running   0          16s   10.244.4.56   k8s-node01   <none>           <none>
no-tolerations-deploy-85587896f9-kfh2c   1/1     Running   0          16s   10.244.4.55   k8s-node01   <none>           <none>
no-tolerations-deploy-85587896f9-wmp8b   1/1     Running   0          16s   10.244.4.57   k8s-node01   <none>           <none>
```
由上可见，因为k8s-node02节点的污点check-nginx 的effect为NoSchedule，说明pod不能被调度到该节点。此时k8s-node01节点的污点check-nginx 的effect为PreferNoSchedule【尽量不调度到该节点】；但只有该节点满足调度条件，因此都调度到了k8s-node01节点。

三、Pod单个容忍时（Tolerations）
--

1、节点上的污点设置（Taints）
```
k8s-master 污点为：node-role.kubernetes.io/master:NoSchedule 【k8s自带污点，直接使用，不必另外操作添加】
k8s-node01 污点为：check-nginx=web:PreferNoSchedule
k8s-node02 污点为：check-nginx=web:NoSchedule
```

2、污点添加操作如下：
```
kubectl taint nodes k8s-node01 check-nginx=web:PreferNoSchedule
kubectl taint nodes k8s-node02 check-nginx=web:NoSchedule
```

3、污点查看操作如下：
```
kubectl describe node k8s-master | grep 'Taints' -A 5
kubectl describe node k8s-node01 | grep 'Taints' -A 5
kubectl describe node k8s-node02 | grep 'Taints' -A 5
```

4、单个容忍示例
```
# cat one_tolerations.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: one-tolerations-deploy
  labels:
    app: onetolerations-deploy
spec:
  replicas: 6
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-pod
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
        imagePullPolicy: IfNotPresent
        ports:
          - containerPort: 80
      tolerations:
      - key: "check-nginx"
        operator: "Equal"
        value: "web"
        effect: "NoSchedule"
```

5、运行yaml文件
```
# kubectl apply -f one_tolerations.yaml 
deployment.apps/one-tolerations-deploy created

# kubectl get deploy -o wide
NAME                     READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
one-tolerations-deploy   6/6     6            6           3s    myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get pod -o wide
NAME                                      READY   STATUS    RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
one-tolerations-deploy-5757d6b559-gbj49   1/1     Running   0          7s    10.244.2.73   k8s-node02   <none>           <none>
one-tolerations-deploy-5757d6b559-j9p6r   1/1     Running   0          7s    10.244.2.71   k8s-node02   <none>           <none>
one-tolerations-deploy-5757d6b559-kpk9q   1/1     Running   0          7s    10.244.2.72   k8s-node02   <none>           <none>
one-tolerations-deploy-5757d6b559-lsppn   1/1     Running   0          7s    10.244.4.65   k8s-node01   <none>           <none>
one-tolerations-deploy-5757d6b559-rx72g   1/1     Running   0          7s    10.244.4.66   k8s-node01   <none>           <none>
one-tolerations-deploy-5757d6b559-s8qr9   1/1     Running   0          7s    10.244.2.74   k8s-node02   <none>           <none>
```
由上可见，此时pod会尽量【优先】调度到k8s-node02节点，尽量不调度到k8s-node01节点。如果我们只有一个pod，那么会一直调度到k8s-node02节点。

四、Pod多个容忍时（Tolerations）
--

1、节点上的污点设置（Taints）
```
k8s-master 污点为：node-role.kubernetes.io/master:NoSchedule 【k8s自带污点，直接使用，不必另外操作添加】
k8s-node01 污点为：check-nginx=web:PreferNoSchedule, check-redis=memdb:NoSchedule
k8s-node02 污点为：check-nginx=web:NoSchedule, check-redis=database:NoSchedule
```

2、污点添加操作如下：
```
kubectl taint nodes k8s-node01 check-nginx=web:PreferNoSchedule
kubectl taint nodes k8s-node01 check-redis=memdb:NoSchedule
kubectl taint nodes k8s-node02 check-nginx=web:NoSchedule
kubectl taint nodes k8s-node02 check-redis=database:NoSchedule
```

3、污点查看操作如下：
```
kubectl describe node k8s-master | grep 'Taints' -A 5
kubectl describe node k8s-node01 | grep 'Taints' -A 5
kubectl describe node k8s-node02 | grep 'Taints' -A 5
```

4、多个容忍示例
```
# cat multi_tolerations.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-tolerations-deploy
  labels:
    app: multitolerations-deploy
spec:
  replicas: 6
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-pod
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
        imagePullPolicy: IfNotPresent
        ports:
          - containerPort: 80
      tolerations:
      - key: "check-nginx"
        operator: "Equal"
        value: "web"
        effect: "NoSchedule"
      - key: "check-redis"
        operator: "Exists"
        effect: "NoSchedule"
```

5、运行yaml文件
```
# kubectl apply -f multi_tolerations.yaml 
deployment.apps/multi-tolerations-deploy created

# kubectl get deploy -o wide
NAME                       READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
multi-tolerations-deploy   6/6     6            6           5s    myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get pod -o wide
NAME                                        READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
multi-tolerations-deploy-776ff4449c-2csnk   1/1     Running   0          10s   10.244.2.171   k8s-node02   <none>           <none>
multi-tolerations-deploy-776ff4449c-4d9fh   1/1     Running   0          10s   10.244.4.116   k8s-node01   <none>           <none>
multi-tolerations-deploy-776ff4449c-c8fz5   1/1     Running   0          10s   10.244.2.173   k8s-node02   <none>           <none>
multi-tolerations-deploy-776ff4449c-nj29f   1/1     Running   0          10s   10.244.4.115   k8s-node01   <none>           <none>
multi-tolerations-deploy-776ff4449c-r7gsm   1/1     Running   0          10s   10.244.2.172   k8s-node02   <none>           <none>
multi-tolerations-deploy-776ff4449c-s8t2n   1/1     Running   0          10s   10.244.2.174   k8s-node02   <none>           <none>
```
由上可见，示例中的pod容忍为：check-nginx=web:NoSchedule；check-redis=:NoSchedule。因此pod会尽量调度到k8s-node02节点，尽量不调度到k8s-node01节点。

五、Pod容忍指定污点key的所有effects情况
---

1、节点上的污点设置（Taints）
```
k8s-master 污点为：node-role.kubernetes.io/master:NoSchedule 【k8s自带污点，直接使用，不必另外操作添加】
k8s-node01 污点为：check-redis=memdb:NoSchedule
k8s-node02 污点为：check-redis=database:NoSchedule
```

2、污点添加操作如下：
```
kubectl taint nodes k8s-node01 check-redis=memdb:NoSchedule
kubectl taint nodes k8s-node02 check-redis=database:NoSchedule
```

3、污点查看操作如下：
```
kubectl describe node k8s-master | grep 'Taints' -A 5
kubectl describe node k8s-node01 | grep 'Taints' -A 5
kubectl describe node k8s-node02 | grep 'Taints' -A 5
```

4、多个容忍示例
```
# cat key_tolerations.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: key-tolerations-deploy
  labels:
    app: keytolerations-deploy
spec:
  replicas: 6
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-pod
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
        imagePullPolicy: IfNotPresent
        ports:
          - containerPort: 80
      tolerations:
      - key: "check-redis"
        operator: "Exists"
```

5、运行yaml文件
```
# kubectl apply -f key_tolerations.yaml 
deployment.apps/key-tolerations-deploy created

# kubectl get deploy -o wide
NAME                     READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
key-tolerations-deploy   6/6     6            6           21s   myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get pod -o wide
NAME                                     READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
key-tolerations-deploy-db5c4c4db-2zqr8   1/1     Running   0          26s   10.244.2.170   k8s-node02   <none>           <none>
key-tolerations-deploy-db5c4c4db-5qb5p   1/1     Running   0          26s   10.244.4.113   k8s-node01   <none>           <none>
key-tolerations-deploy-db5c4c4db-7xmt6   1/1     Running   0          26s   10.244.2.169   k8s-node02   <none>           <none>
key-tolerations-deploy-db5c4c4db-84rkj   1/1     Running   0          26s   10.244.4.114   k8s-node01   <none>           <none>
key-tolerations-deploy-db5c4c4db-gszxg   1/1     Running   0          26s   10.244.2.168   k8s-node02   <none>           <none>
key-tolerations-deploy-db5c4c4db-vlgh8   1/1     Running   0          26s   10.244.4.112   k8s-node01   <none>           <none>
```
由上可见，示例中的pod容忍为：check-nginx=:；仅需匹配node污点的key即可，污点的value和effect不需要关心。因此可以匹配k8s-node01、k8s-node02节点。

六、Pod容忍所有污点
---

1、节点上的污点设置（Taints）
```
k8s-master 污点为：node-role.kubernetes.io/master:NoSchedule 【k8s自带污点，直接使用，不必另外操作添加】
k8s-node01 污点为：check-nginx=web:PreferNoSchedule, check-redis=memdb:NoSchedule
k8s-node02 污点为：check-nginx=web:NoSchedule, check-redis=database:NoSchedule
```

2、污点添加操作如下：
```
kubectl taint nodes k8s-node01 check-nginx=web:PreferNoSchedule
kubectl taint nodes k8s-node01 check-redis=memdb:NoSchedule
kubectl taint nodes k8s-node02 check-nginx=web:NoSchedule
kubectl taint nodes k8s-node02 check-redis=database:NoSchedule
```

3、污点查看操作如下：
```
kubectl describe node k8s-master | grep 'Taints' -A 5
kubectl describe node k8s-node01 | grep 'Taints' -A 5
kubectl describe node k8s-node02 | grep 'Taints' -A 5
```

4、所有容忍示例
```
# cat all_tolerations.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: all-tolerations-deploy
  labels:
    app: alltolerations-deploy
spec:
  replicas: 6
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp-pod
        image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
        imagePullPolicy: IfNotPresent
        ports:
          - containerPort: 80
      tolerations:
      - operator: "Exists"
```

5、运行yaml文件
```
# kubectl apply -f all_tolerations.yaml 
deployment.apps/all-tolerations-deploy created

# kubectl get deploy -o wide
NAME                     READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
all-tolerations-deploy   6/6     6            6           8s    myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get pod -o wide
NAME                                      READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
all-tolerations-deploy-566cdccbcd-4klc2   1/1     Running   0          12s   10.244.0.116   k8s-master   <none>           <none>
all-tolerations-deploy-566cdccbcd-59vvc   1/1     Running   0          12s   10.244.0.115   k8s-master   <none>           <none>
all-tolerations-deploy-566cdccbcd-cvw4s   1/1     Running   0          12s   10.244.2.175   k8s-node02   <none>           <none>
all-tolerations-deploy-566cdccbcd-k8fzl   1/1     Running   0          12s   10.244.2.176   k8s-node02   <none>           <none>
all-tolerations-deploy-566cdccbcd-s2pw7   1/1     Running   0          12s   10.244.4.118   k8s-node01   <none>           <none>
all-tolerations-deploy-566cdccbcd-xzngt   1/1     Running   0          13s   10.244.4.117   k8s-node01   <none>           <none>
```
后上可见，示例中的pod容忍所有的污点，因此pod可被调度到所有k8s节点。
