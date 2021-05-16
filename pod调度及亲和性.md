一、nodeName调度
===

nodeName是节点选择约束的最简单形式，但是由于其限制，通常很少使用它。nodeName是PodSpec的领域。

pod.spec.nodeName将Pod直接调度到指定的Node节点上，会【跳过Scheduler的调度策略】，该匹配规则是【强制】匹配。可以越过Taints污点进行调度。

nodeName用于选择节点的一些限制是：
- 如果指定的节点不存在，则容器将不会运行，并且在某些情况下可能会自动删除。
- 如果指定的节点没有足够的资源来容纳该Pod，则该Pod将会失败，并且其原因将被指出，例如OutOfmemory或OutOfcpu。
- 云环境中的节点名称并非总是可预测或稳定的。

nodeName示例

1、获取当前的节点信息
```
# kubectl get nodes -o wide
NAME         STATUS   ROLES    AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                KERNEL-VERSION           CONTAINER-RUNTIME
k8s-master   Ready    master   42d   v1.17.4   172.16.1.110   <none>        CentOS Linux 7 (Core)   3.10.0-1062.el7.x86_64   docker://19.3.8
k8s-node01   Ready    <none>   42d   v1.17.4   172.16.1.111   <none>        CentOS Linux 7 (Core)   3.10.0-1062.el7.x86_64   docker://19.3.8
k8s-node02   Ready    <none>   42d   v1.17.4   172.16.1.112   <none>        CentOS Linux 7 (Core)   3.10.0-1062.el7.x86_64   docker://19.3.8
```

2、当nodeName指定节点存在
```
# cat scheduler_nodeName.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler-nodename-deploy
  labels:
    app: nodename-deploy
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
      # 指定节点运行
      nodeName: k8s-master
```

3、运行yaml文件并查看信息
```
# kubectl apply -f scheduler_nodeName.yaml 
deployment.apps/scheduler-nodename-deploy created

# kubectl get deploy -o wide
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodename-deploy   0/5     5            0           6s    myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get rs -o wide
NAME                                  DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodename-deploy-d5c9574bd   5         5         5       15s   myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp,pod-template-hash=d5c9574bd

# kubectl get pod -o wide
NAME                                        READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
scheduler-nodename-deploy-d5c9574bd-6l9d8   1/1     Running   0          23s   10.244.0.123   k8s-master   <none>           <none>
scheduler-nodename-deploy-d5c9574bd-c82cc   1/1     Running   0          23s   10.244.0.119   k8s-master   <none>           <none>
scheduler-nodename-deploy-d5c9574bd-dkkjg   1/1     Running   0          23s   10.244.0.122   k8s-master   <none>           <none>
scheduler-nodename-deploy-d5c9574bd-hcn77   1/1     Running   0          23s   10.244.0.121   k8s-master   <none>           <none>
scheduler-nodename-deploy-d5c9574bd-zstjx   1/1     Running   0          23s   10.244.0.120   k8s-master   <none>           <none>
```
由上可见，yaml文件中nodeName: k8s-master生效，所有pod被调度到了k8s-master节点。如果这里是nodeName: k8s-node02，那么就会直接调度到k8s-node02节点。

4、当nodeName指定节点不存在
```
# cat scheduler_nodeName_02.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler-nodename-deploy
  labels:
    app: nodename-deploy
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
      # 指定节点运行，该节点不存在
      nodeName: k8s-node08
```

5、运行yaml文件并查看信息
```
# kubectl apply -f scheduler_nodeName_02.yaml 
deployment.apps/scheduler-nodename-deploy created

# kubectl get deploy -o wide
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodename-deploy   0/5     5            0           4s    myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get rs -o wide
NAME                                   DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodename-deploy-75944bdc5d   5         5         0       9s    myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp,pod-template-hash=75944bdc5d

# kubectl get pod -o wide
NAME                                         READY   STATUS    RESTARTS   AGE   IP       NODE         NOMINATED NODE   READINESS GATES
scheduler-nodename-deploy-75944bdc5d-c8f5d   0/1     Pending   0          13s   <none>   k8s-node08   <none>           <none>
scheduler-nodename-deploy-75944bdc5d-hfdlv   0/1     Pending   0          13s   <none>   k8s-node08   <none>           <none>
scheduler-nodename-deploy-75944bdc5d-q9qgt   0/1     Pending   0          13s   <none>   k8s-node08   <none>           <none>
scheduler-nodename-deploy-75944bdc5d-q9zl7   0/1     Pending   0          13s   <none>   k8s-node08   <none>           <none>
scheduler-nodename-deploy-75944bdc5d-wxsnv   0/1     Pending   0          13s   <none>   k8s-node08   <none>           <none>
```
由上可见，如果指定的节点不存在，则容器将不会运行，一直处于Pending 状态。

二、nodeSelector调度
===

nodeSelector是节点选择约束的最简单推荐形式。nodeSelector是PodSpec的领域。它指定键值对的映射。

Pod.spec.nodeSelector是通过Kubernetes的label-selector机制选择节点，由调度器调度策略匹配label，而后调度Pod到目标节点，该匹配规则属于【强制】约束。由于是调度器调度，因此不能越过Taints污点进行调度。

nodeSelector示例

1、获取当前的节点信息
```
# kubectl get node -o wide --show-labels
NAME         STATUS   ROLES    AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                KERNEL-VERSION           CONTAINER-RUNTIME   LABELS
k8s-master   Ready    master   42d   v1.17.4   172.16.1.110   <none>        CentOS Linux 7 (Core)   3.10.0-1062.el7.x86_64   docker://19.3.8     beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=k8s-master,kubernetes.io/os=linux,node-role.kubernetes.io/master=
k8s-node01   Ready    <none>   42d   v1.17.4   172.16.1.111   <none>        CentOS Linux 7 (Core)   3.10.0-1062.el7.x86_64   docker://19.3.8     beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=k8s-node01,kubernetes.io/os=linux
k8s-node02   Ready    <none>   42d   v1.17.4   172.16.1.112   <none>        CentOS Linux 7 (Core)   3.10.0-1062.el7.x86_64   docker://19.3.8     beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=k8s-node02,kubernetes.io/os=linux
```

2、添加label标签

运行kubectl get nodes以获取群集节点的名称。然后可以对指定节点添加标签。比如：k8s-node01的磁盘为SSD，那么添加disk-type=ssd；k8s-node02的CPU核数高，那么添加cpu-type=hight；如果为Web机器，那么添加service-type=web。怎么添加标签可以根据实际规划情况而定。
```
### 给k8s-node01 添加指定标签
# kubectl label nodes k8s-node01 disk-type=ssd
node/k8s-node01 labeled

#### 删除标签命令 kubectl label nodes k8s-node01 disk-type-
# kubectl get node --show-labels
NAME         STATUS   ROLES    AGE   VERSION   LABELS
k8s-master   Ready    master   42d   v1.17.4   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=k8s-master,kubernetes.io/os=linux,node-role.kubernetes.io/master=
k8s-node01   Ready    <none>   42d   v1.17.4   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,disk-type=ssd,kubernetes.io/arch=amd64,kubernetes.io/hostname=k8s-node01,kubernetes.io/os=linux
k8s-node02   Ready    <none>   42d   v1.17.4   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=k8s-node02,kubernetes.io/os=linux
```
由上可见，已经为k8s-node01节点添加了disk-type=ssd 标签。

3、当nodeSelector标签存在
```
# cat scheduler_nodeSelector.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler-nodeselector-deploy
  labels:
    app: nodeselector-deploy
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
      # 指定节点标签选择，且标签存在
      nodeSelector:
        disk-type: ssd
```

4、运行yaml文件并查看信息
```
# kubectl apply -f scheduler_nodeSelector.yaml 
deployment.apps/scheduler-nodeselector-deploy created

# kubectl get deploy -o wide
NAME                            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodeselector-deploy   5/5     5            5           10s   myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get rs -o wide
NAME                                       DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodeselector-deploy-79455db454   5         5         5       14s   myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp,pod-template-hash=79455db454

# kubectl get pod -o wide
NAME                                             READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
scheduler-nodeselector-deploy-79455db454-745ph   1/1     Running   0          19s   10.244.4.154   k8s-node01   <none>           <none>
scheduler-nodeselector-deploy-79455db454-bmjvd   1/1     Running   0          19s   10.244.4.151   k8s-node01   <none>           <none>
scheduler-nodeselector-deploy-79455db454-g5cg2   1/1     Running   0          19s   10.244.4.153   k8s-node01   <none>           <none>
scheduler-nodeselector-deploy-79455db454-hw8jv   1/1     Running   0          19s   10.244.4.152   k8s-node01   <none>           <none>
scheduler-nodeselector-deploy-79455db454-zrt8d   1/1     Running   0          19s   10.244.4.155   k8s-node01   <none>           <none>
```
由上可见，所有pod都被调度到了k8s-node01节点。当然如果其他节点也有disk-type=ssd 标签，那么pod也会调度到这些节点上。

5、当nodeSelector标签不存在
```
# cat scheduler_nodeSelector_02.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler-nodeselector-deploy
  labels:
    app: nodeselector-deploy
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
      # 指定节点标签选择，且标签不存在
      nodeSelector:
        service-type: web
```

6、运行yaml文件并查看信息
```
# kubectl apply -f scheduler_nodeSelector_02.yaml 
deployment.apps/scheduler-nodeselector-deploy created

# kubectl get deploy -o wide
NAME                            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodeselector-deploy   0/5     5            0           26s   myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp

# kubectl get rs -o wide
NAME                                       DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                      SELECTOR
scheduler-nodeselector-deploy-799d748db6   5         5         0       30s   myapp-pod    registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1   app=myapp,pod-template-hash=799d748db6

# kubectl get pod -o wide
NAME                                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES
scheduler-nodeselector-deploy-799d748db6-92mqj   0/1     Pending   0          40s   <none>   <none>   <none>           <none>
scheduler-nodeselector-deploy-799d748db6-c2w25   0/1     Pending   0          40s   <none>   <none>   <none>           <none>
scheduler-nodeselector-deploy-799d748db6-c8tlx   0/1     Pending   0          40s   <none>   <none>   <none>           <none>
scheduler-nodeselector-deploy-799d748db6-tc5n7   0/1     Pending   0          40s   <none>   <none>   <none>           <none>
scheduler-nodeselector-deploy-799d748db6-z8c57   0/1     Pending   0          40s   <none>   <none>   <none>           <none>
```
由上可见，如果nodeSelector匹配的标签不存在，则容器将不会运行，一直处于Pending 状态。

三、亲和性 Affinity
---

| 调度策略 | 匹配标签 | 操作符 | 拓扑域支持 | 调度目标 |
| :------: | :--------: | :-------: | :-----: | :---------: |
| nodeAffinity | 主机 | In, NotIn, Exists,DoesNotExist, Gt, Lt | 否 | 指定主机 |
| podAffinity | POD | In, NotIn, Exists,DoesNotExist | 是 | POD与指定POD同一拓扑域 |
| podAnitAffinity | POD | In, NotIn, Exists,DoesNotExist | 是 | POD与指定POD不在同一拓扑域 |

1、Affinity 介绍
由于上面 NodeName 和 NodeSelector 两种调度方式过于生硬，不能够灵活配置应用能启动在什么节点、不启动在什么节点与配置两个相同的实例启动在不同的节点等等规则。所以 Kubernetes 中还有另一种调度方式，那就是 Affinity 亲和性，这种方式可以非常灵活的配置应用的调度规则。

(1)、Affinity 可以分为三种类
- NodeAffinity: Node 亲和性
- PodAffinity： Pod 亲和性
- PodAntiAffinity： Pod 反亲和性

(2)、亲和性调度可以分成软策略和硬策略两种方式
- preferredDuringSchedulingIgnoredDuringExecution（软策略）： 如果没有满足调度要求的节点，Pod 就会忽略这条规则，继续完成调度过程，即是满足条件最好，没有满足也无所谓的一种策略。
- requiredDuringSchedulingIgnoredDuringExecution（硬策略）： 比较强硬，如果没有满足条件的节点的话，就不断重试直到满足条件为止，即是必须满足该要求，不然不调度的策略。

2、相关参数介绍

(1)、调度条件参数：

- nodeSelectorTerms：下面有多个选项的话，满足任何一个条件就可以了；
- matchExpressions：有多个选项的话，则必须同时满足这些条件才能正常调度 POD。

(2)、权重 weight 参数：

- 权重范围为 1-100，权重的值涉及调度器的优选打分过程，每个节点的评分都会加上这个 weight，最后绑定最高的节点。

(3)、拓扑域 topologyKey 参数及可配置选项：

topologykey 的值表示指作用于 topology 范围内的 node 上运行的 pod，其值可配置为：

- kubernetes.io/hostname（Node）
- failure-domain.beta.kubernetes.io/zone（Zone）
- failure-domain.beta.kubernetes.io/region（Region）

(4)、匹配选项 operator 可用的选项：
- In： label 的值在某个列表中
- NotIn： label 的值不在某个列表中
- Gt： label 的值大于某个值
- Lt： label 的值小于某个值
- Exists： 某个 label 存在
- DoesNotExist： 某个 label 不存在

三、Node 亲和性 NodeAffinity
--
NodeAffinity 是用于调度应用时候，会根据 NodeAffinity 参数去跟 Node 上的 Label 进行匹配，如果有符合条件的 Node 则该应用就可与调度到该节点，其功能跟 NodeSelector 类似，不过设置的条件比其更灵活。例如，下面是设置应用必须运行在 amd64 的节点中，并且设置尽可能启动到 k8s-node-2-12 节点上，可以按如下配置：

(1)、设置 Deployment 对象配置 nodeAffinity 参数
```
# vim deploy.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
  labels:
    app: hello
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
      - name: hello
        image: tutum/hello-world:latest
        ports:
        - containerPort: 80
      affinity:  
        nodeAffinity:    #Pod亲和性
          requiredDuringSchedulingIgnoredDuringExecution:  #硬策略
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/arch
                operator: In
                values:
                - amd64
          preferredDuringSchedulingIgnoredDuringExecution:  #软策略
          - weight: 100  #权重，取值范围为 1-100
            preference:
              matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                - k8s-node-2-12            
```
(2)、执行部署应用
```
$ kubectl create -f deploy.yaml
```
(3)、查看启动的应用所在节点
```
$ kubectl get pods -o wide

NAME                    READY   STATUS    RESTARTS   AGE   IP               NODE         
hello-bc58f99c8-fpd5t   1/1     Running   0          17s   10.244.134.232   k8s-node-2-12
```

NodeAffinity 规则设置的注意事项如下：
- 如果 nodeAffinity 指定了多个 nodeSelectorTerms，那么其中任意一个能够匹配成功即可。
- 如果同时定义了 nodeSelector 和 nodeAffinity，那么必须两个条件都得到满足，Pod 才能最终运行在指定的 Node 上。
- 如果在 nodeSelectorTerms 中有多个 matchExpressions，则一个节点必须满足所有 matchExpressions 才能运行该 Pod。


节点硬亲和性  
```
apiVersion: v1
kind: Pod
metadata:
  name: with-required-nodeaffinity-2
spec:
  affinity:
    nodeAffinity:                                                    #节点亲和性
      requiredDuringSchedulingIgnoredDuringExecution:                #硬亲和性
        nodeSelectorTerms:                                           #标签选择器
        - matchExpressions:                                          #匹配的标签
          - {key: zone, operator: In, values: ["foo", "bar"]}        #根据values匹配，值不能为空 operator选项有In、NotIn
          - {key: ssd, operator: Exists, values: []}                 #存在性匹配，值必选为空  operator选项Exists、DoesNotExist
  containers:
  - name: myapp
    image: ikubernetes/myapp:v1
    resources:
      requests:
        cpu: 6
        memory: 20Gi
```  

同上不同写法
```
apiVersion: v1
kind: Pod
metadata:
  name: affinity
  labels:
    app: node-affinity-pod
spec:
  containers:
  - name: with-node-affinity
    image: ikubernetes/myapp:v1
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/hostname
            operator: NotIn
            values:
            - k8s-node02
```  


节点软亲和性  
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deploy-with-node-affinity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      name: myapp-pod
      labels:
        app: myapp
    spec:
      affinity:
        nodeAffinity:                                              #节点亲和性
          preferredDuringSchedulingIgnoredDuringExecution:         #软亲和性
          - weight: 60                                             #权重1-100数值越高优先级越高
            preference:
              matchExpressions:                                    #匹配方式
              - {key: zone, operator: In, values: ["foo"]}
          - weight: 30                                             #如果有多个模式匹配合适，权重高的优先
            preference:
              matchExpressions:
              - {key: ssd, operator: Exists, values: []}
      containers:
      - name: myapp
        image: ikubernetes/myapp:v1
```  

同上不同写法
```
apiVersion: v1
kind: Pod
metadata:
  name: affinity
  labels:
    app: node-affinity-pod
spec:
  containers:
  - name: with-node-affinity
    image: ikubernetes/myapp:v1
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: kubernetes.io/hostname
            operator: In
            values:
            - k8s-node02
```  

硬策略和软策略同时使用，先满足硬策略再满足软策略
```
apiVersion: v1
kind: Pod
metadata:
  name: affinity
  labels:
    app: node-affinity-pod
spec:
  containers:
  - name: with-node-affinity
    image: ikubernetes/myapp:v1
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/hostname
            operator: NotIn
            values:
            - k8s-node02
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: source
            operator: In
            values:
            - qikqiak
```

四、Pod 亲和性 PodAffinity
---
Pod 亲和性 主要解决 Pod 可以和哪些 Pod部署在同一个拓扑域中的问题。一般用于一个应用存在多个实例，或者设置应用与另一个应用间建立关联的时候才会用到，比如，A 应用要启动两个实例，但是要求这两个实例启动在同一个节点上。再比如，有 A 和 B 两个应用，要求这两个引用起动在同一节点上。下面介绍下，如何设置同一应用实例启动在相同节点上，可以按如下配置：

(1)、设置 Deployment 对象配置 podAffinity 参数
```
# vim deploy.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
  labels:
    app: hello
spec:
  replicas: 2  #两个示例
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
      - name: hello
        image: tutum/hello-world:latest
        ports:
        - containerPort: 80
      affinity:  
        podAffinity:    #Pod亲和性
          requiredDuringSchedulingIgnoredDuringExecution:  #硬策略
          - topologyKey: kubernetes.io/hostname
            labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - hello
```
(2)、执行部署应用
```
$ kubectl create -f deploy.yaml
```
(3)、查看启动的应用所在节点
```
$ kubectl get pods -o wide

NAME                     READY   STATUS    RESTARTS   AGE   IP              NODE
hello-57db96b746-7xk89   1/1     Running   0          20s   10.244.39.254   k8s-node-2-13
hello-57db96b746-q55xk   1/1     Running   0          20s   10.244.39.252   k8s-node-2-13
```
pod硬亲和性
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-with-pod-affinity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      name: myapp
      labels:
        app: myapp
    spec:
      affinity:
        podAffinity:                                            #pod亲和性
          requiredDuringSchedulingIgnoredDuringExecution:       #硬亲和性
          - labelSelector:                                      #标签选择器
              matchExpressions:                                 #匹配方法
              - {key: app, operator: In, values: ["db"]}
            topologyKey: zone                                   #以节点标签的key为标准，作为拓扑域，在同一域内进行匹配
      containers:
      - name: myapp
        image: ikubernetes/myapp:v1
```  


pod软亲和性
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-with-preferred-pod-affinity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      name: myapp
      labels:
        app: myapp
    spec:
      affinity:
        podAffinity:                                             #pod亲和性
          preferredDuringSchedulingIgnoredDuringExecution:       #软亲和性
          - weight: 80
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - {key: app, operator: In, values: ["db"]}
              topologyKey: rack
          - weight: 20
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - {key: app, operator: In, values: ["db"]}
              topologyKey: zone
      containers:
      - name: myapp
        image: ikubernetes/myapp:v1
```  

5、Pod 反亲和性 PodAntiAffinity

Pod 反亲和性 主要是解决 Pod 不能和哪些 Pod 部署在同一个拓扑域中的问题，是用于处理的 Pod 之间的关系。比如一个 Pod 被调度到某一个节点上，新起的 Pod 不想和这个 Pod 调度到一起，就可以使用 Pod 的反亲和性 podAntiAffinity。例如，设置应用启动在不同节点上，可以按如下配置：

(1)、设置 Deployment 对象配置 podAntiAffinity 参数
```
# vim deploy.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
  labels:
    app: hello
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
      - name: hello
        image: tutum/hello-world:latest
        ports:
        - containerPort: 80
      affinity:  
        podAntiAffinity:    #Pod反亲和性
          requiredDuringSchedulingIgnoredDuringExecution:  #硬策略
          - topologyKey: kubernetes.io/hostname
            labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - hello
```         

(2)、执行部署应用
```
$ kubectl create -f deploy.yaml
```
(3)、查看启动的应用所在节点
```
$ kubectl get pods -o wide

NAME                     READY   STATUS    RESTARTS   AGE   IP               NODE
hello-67c8bbb758-qhhvg   1/1     Running   0          14s   10.244.134.238   k8s-node-2-12
hello-67c8bbb758-x6lrd   1/1     Running   0          14s   10.244.39.251    k8s-node-2-13
```

pod反亲和性  
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-with-pod-anti-affinity
spec:
  replicas: 4
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      name: myapp
      labels:
        app: myapp
    spec:
      affinity:
        podAntiAffinity:                                       #反亲和性
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - {key: app, operator: In, values: ["myapp"]}
            topologyKey: kubernetes.io/hostname
      containers:
      - name: myapp
        image: ikubernetes/myapp:v1
```
