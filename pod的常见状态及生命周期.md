pod的几种常见状态
- Pendding 未匹配到满足pod运行的节点，未调度
- containerCreating 调查成功，后创建容器状态，此状态持续时间不长
- Running 容器创建成功后处于运行中的状态
- Succeeded 成功运行，只有job和cronjob可出现此状态，容器运行结束正常退出，退出值为0
- Failed 失败运行，只有job和cronjob可出现此状态，容器运行结束退出，退出值为非0
- Ready 健康检查成功后的状态
- CrashLoopBackOff 未通过健康检查的状态
- Unkown 为api_server没有收到相关pod的汇报（kubelet和api的通信问题）
- Terminating 为pod终止时的状态

解决pod一直未被终止问题  
kubectl delete pod [pod name] --force --grace-period=0 -n [namespace]  

pod生命周期  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod_lifecycle.png)  

pod创建过程  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod.png)  

pod终止过程  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod_kill.png)  

Init Container容器
---
Pod可以包含多个容器，应用运行在这些容器里面，同时 Pod 也可以有一个或多个先于应用容器启动的 Init 容器。

如果为一个 Pod 指定了多个 Init 容器，这些Init容器会按顺序逐个运行。每个 Init 容器都必须运行成功，下一个才能够运行。当所有的 Init 容器运行完成时，Kubernetes 才会为 Pod 初始化应用容器并像平常一样运行。

Init容器与普通的容器非常像，除了以下两点：
- 1、Init容器总是运行到成功完成且正常退出为止
- 2、只有前一个Init容器成功完成并正常退出，才能运行下一个Init容器。

如果Pod的Init容器失败，Kubernetes会不断地重启Pod，直到Init容器成功为止。但如果Pod对应的restartPolicy为Never，则不会重新启动。

在所有的Init容器没有成功之前，Pod将不会变成Ready状态。Init容器的端口将不会在Service中进行聚集。正在初始化中的Pod处于Pending状态，但会将条件Initializing设置为true。

如果Pod重启，所有Init容器必须重新执行。

在 Pod 中的每个应用容器和 Init 容器的名称必须唯一；与任何其它容器共享同一个名称，会在校验时抛出错误。

Init 容器能做什么？

因为 Init 容器是与应用容器分离的单独镜像，其启动相关代码具有如下优势：
- 1、Init 容器可以包含一些安装过程中应用容器不存在的实用工具或个性化代码。例如，在安装过程中要使用类似 sed、 awk、 python 或 dig 这样的工具，那么放到Init容器去安装这些工具；再例如，应用容器需要一些必要的目录或者配置文件甚至涉及敏感信息，那么放到Init容器去执行。而不是在主容器执行。
- 2、Init 容器可以安全地运行这些工具，避免这些工具导致应用镜像的安全性降低。
- 3、应用镜像的创建者和部署者可以各自独立工作，而没有必要联合构建一个单独的应用镜像。

- 4、Init 容器能以不同于Pod内应用容器的文件系统视图运行。因此，Init容器可具有访问 Secrets 的权限，而应用容器不能够访问。
- 5、由于 Init 容器必须在应用容器启动之前运行完成，因此 Init 容器提供了一种机制来阻塞或延迟应用容器的启动，直到满足了一组先决条件。一旦前置条件满足，Pod内的所有的应用容器会并行启动。

- 等待其他服务进入就绪状态：这个可以用来解决服务之间的依赖问题，比如有一个Web服务，该服务又依赖于另外一个数据库服务，但是在启动这个Web服务的时候并不能保证依赖的这个数据库服务就已经启动起来，所以可能会出现一段时间内Web服务连接数据库异常。解决这个问题可以在Web服务的Pod中使用一个InitContainer，在这个初始化容器中去检查数据库是否已经准备好了，如果数据库服务准备好了，初始化容器就结束退出，然后主容器Web服务开始启动，这个时候去连接数据库就不会有问题。
- 做初始化配置：比如集群里检测所有已经存在的成员节点，为主容器准备好集群的配置信息，这样主容器起来后就能用这个配置信息加入集群

Init 容器示例

下面的例子定义了一个具有 2 个 Init 容器的简单 Pod。 第一个等待 myservice 启动，第二个等待 mydb 启动。 一旦这两个 Init容器都启动完成，Pod 将启动spec区域中的应用容器。

Pod yaml文件
```
[root@k8s-master lifecycle]# pwd
/root/k8s_practice/lifecycle
[root@k8s-master lifecycle]# cat init_C_pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-busybox-pod
  labels:
    app: myapp
spec:
  containers:
  - name: myapp-container
    image: registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']
  initContainers:
  - name: init-myservice
    image: registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24
    command: ['sh', '-c', "until nslookup myservice; do echo waiting for myservice; sleep 60; done"]
  - name: init-mydb
    image: registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24
    command: ['sh', '-c', "until nslookup mydb; do echo waiting for mydb; sleep 60; done"]
```

启动这个 Pod，并检查其状态，可以执行如下命令：
```
[root@k8s-master lifecycle]# kubectl apply -f init_C_pod.yaml 
pod/myapp-busybox-pod created 
[root@k8s-master lifecycle]# kubectl get -f init_C_pod.yaml -o wide  # 或者kubectl get pod myapp-busybox-pod -o wide
NAME                READY   STATUS     RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
myapp-busybox-pod   0/1     Init:0/2   0          55s   10.244.4.16   k8s-node01   <none>           <none>
```

如需更详细的信息：
```
[root@k8s-master lifecycle]# kubectl describe pod myapp-busybox-pod 
Name:         myapp-busybox-pod
Namespace:    default
Priority:     0
…………
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
Events:
  Type    Reason     Age    From                 Message
  ----    ------     ----   ----                 -------
  Normal  Scheduled  2m18s  default-scheduler    Successfully assigned default/myapp-busybox-pod to k8s-node01
  Normal  Pulled     2m17s  kubelet, k8s-node01  Container image "registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24" already present on machine
  Normal  Created    2m17s  kubelet, k8s-node01  Created container init-myservice
  Normal  Started    2m17s  kubelet, k8s-node01  Started container init-myservice
```

如需查看Pod内 Init 容器的日志，请执行：
```
[root@k8s-master lifecycle]# kubectl logs -f --tail 500 myapp-busybox-pod -c init-myservice   # 第一个 init container 详情
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

waiting for myservice
nslookup: can't resolve 'myservice'
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
………………
[root@k8s-master lifecycle]# kubectl logs myapp-busybox-pod -c init-mydb   # 第二个 init container 详情
Error from server (BadRequest): container "init-mydb" in pod "myapp-busybox-pod" is waiting to start: PodInitializing
```
此时Init 容器将会等待直至发现名称为mydb和myservice的 Service。

Service yaml文件
```
[root@k8s-master lifecycle]# pwd
/root/k8s_practice/lifecycle
[root@k8s-master lifecycle]# cat init_C_service.yaml 
---
kind: Service
apiVersion: v1
metadata:
  name: myservice
spec:
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9376
---
kind: Service
apiVersion: v1
metadata:
  name: mydb
spec:
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9377
```

创建mydb和myservice的 service 命令：
```
[root@k8s-master lifecycle]# kubectl create -f init_C_service.yaml 
service/myservice created
service/mydb created
```

之后查看pod状态和service状态，能看到这些 Init容器执行完毕后，随后myapp-busybox-pod的Pod转移进入 Running 状态：
```
[root@k8s-master lifecycle]# kubectl get svc -o wide mydb myservice
NAME        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE   SELECTOR
mydb        ClusterIP   10.108.24.84     <none>        80/TCP    72s   <none>
myservice   ClusterIP   10.105.252.196   <none>        80/TCP    72s   <none>
[root@k8s-master lifecycle]# 
[root@k8s-master lifecycle]# kubectl get pod myapp-busybox-pod -o wide 
NAME                READY   STATUS    RESTARTS   AGE     IP            NODE         NOMINATED NODE   READINESS GATES
myapp-busybox-pod   1/1     Running   0          7m33s   10.244.4.17   k8s-node01   <none>           <none>
```
由上可知：一旦我们启动了 mydb 和 myservice 这两个 Service，我们就能够看到 Init 容器完成，并且 myapp-busybox-pod 被创建。

进入myapp-busybox-pod容器，并通过nslookup查看这两个Service的DNS记录。
```
[root@k8s-master lifecycle]# kubectl exec -it myapp-busybox-pod sh
/ # nslookup mydb 
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      mydb
Address 1: 10.108.24.84 mydb.default.svc.cluster.local
/ # 
/ # 
/ # 
/ # nslookup myservice
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      myservice
Address 1: 10.105.252.196 myservice.default.svc.cluster.local
```


Lifecycle钩子
---

1、Pause容器说明

每个Pod里运行着一个特殊的被称之为Pause的容器，其他容器则为业务容器，这些业务容器共享Pause容器的网络栈和Volume挂载卷，因此他们之间通信和数据交换更为高效。在设计时可以充分利用这一特性，将一组密切相关的服务进程放入同一个Pod中；同一个Pod里的容器之间仅需通过localhost就能互相通信。

2、kubernetes中的pause容器主要为每个业务容器提供以下功能：
- PID命名空间：Pod中的不同应用程序可以看到其他应用程序的进程ID。
- 网络命名空间：Pod中的多个容器能够访问同一个IP和端口范围。
- IPC命名空间：Pod中的多个容器能够使用SystemV IPC或POSIX消息队列进行通信。
- UTS命名空间：Pod中的多个容器共享一个主机名；Volumes（共享存储卷）。
- Pod中的各个容器可以访问在Pod级别定义的Volumes。

3、主容器生命周期事件的处理函数
Kubernetes 支持 postStart 和 preStop 事件。当一个主容器启动后，Kubernetes 将立即发送 postStart 事件；在主容器被终结之前，Kubernetes 将发送一个 preStop 事件。
- postStart 指的是在容器启动后立刻执行一个指定的操作
- preStop 容器被杀死之前。

4、postStart 和 preStop 处理函数
```
cat lifecycle-events.yaml 
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-demo-pod
  namespace: default
  labels:
    test: lifecycle
spec:
  containers:
  - name: lifecycle-demo
    image: registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
    imagePullPolicy: IfNotPresent
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "echo 'Hello from the postStart handler' >> /var/log/nginx/message"]
      preStop:
        exec:
          command: ["/bin/sh", "-c", "echo 'Hello from the preStop handler'   >> /var/log/nginx/message"]
    volumeMounts:                          #定义容器挂载内容
    - name: message-log                    #使用的存储卷名称，如果跟下面volume字段name值相同，则表示使用volume的nginx-site这个存储卷
      mountPath: /var/log/nginx/           #挂载至容器中哪个目录
      readOnly: false                      #读写挂载方式，默认为读写模式false
  initContainers:
  - name: init-myservice
    image: registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24
    command: ["/bin/sh", "-c", "echo 'Hello initContainers'   >> /var/log/nginx/message"]
    volumeMounts:                          #定义容器挂载内容
    - name: message-log                    #使用的存储卷名称，如果跟下面volume字段name值相同，则表示使用volume的nginx-site这个存储卷
      mountPath: /var/log/nginx/           #挂载至容器中哪个目录
      readOnly: false                      #读写挂载方式，默认为读写模式false
  volumes:                                 #volumes字段定义了paues容器关联的宿主机或分布式文件系统存储卷
  - name: message-log                      #存储卷名称
    hostPath:                              #路径，为宿主机存储路径
      path: /data/volumes/nginx/log/       #在宿主机上目录的路径
      type: DirectoryOrCreate              #定义类型，这表示如果宿主机没有此目录则会自动创建
```

5、启动pod，查看pod状
```
# kubectl apply -f lifecycle-events.yaml 
pod/lifecycle-demo-pod created

# kubectl get pod -o wide
NAME                 READY   STATUS    RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
lifecycle-demo-pod   1/1     Running   0          5s    10.244.2.30   k8s-node02   <none>           <none>
```

6、查看pod详情
```
# kubectl describe pod lifecycle-demo-pod
Name:         lifecycle-demo-pod
Namespace:    default
Priority:     0
Node:         k8s-node02/172.16.1.112
Start Time:   Sat, 23 May 2020 22:08:04 +0800
Labels:       test=lifecycle
………………
Init Containers:
  init-myservice:
    Container ID:  docker://1cfabcb60b817efd5c7283ad9552dafada95dbe932f92822b814aaa9c38f8ba5
    Image:         registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24
    Image ID:      docker-pullable://registry.cn-beijing.aliyuncs.com/ducafe/busybox@sha256:f73ae051fae52945d92ee20d62c315306c593c59a429ccbbdcba4a488ee12269
    Port:          <none>
    Host Port:     <none>
    Command:
      /bin/sh
      -c
      echo 'Hello initContainers'   >> /var/log/nginx/message
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Sat, 23 May 2020 22:08:06 +0800
      Finished:     Sat, 23 May 2020 22:08:06 +0800
    Ready:          True
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/log/nginx/ from message-log (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-v48g4 (ro)
Containers:
  lifecycle-demo:
    Container ID:   docker://c07f7f3d838206878ad0bfeaec9b4222ac7d6b13fb758cc1b340ac43e7212a3a
    Image:          registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
    Image ID:       docker-pullable://registry.cn-beijing.aliyuncs.com/google_registry/nginx@sha256:7ac7819e1523911399b798309025935a9968b277d86d50e5255465d6592c0266
    Port:           <none>
    Host Port:      <none>
    State:          Running
      Started:      Sat, 23 May 2020 22:08:07 +0800
    Ready:          True
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/log/nginx/ from message-log (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-v48g4 (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
Volumes:
  message-log:
    Type:          HostPath (bare host directory volume)
    Path:          /data/volumes/nginx/log/
    HostPathType:  DirectoryOrCreate
  default-token-v48g4:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-v48g4
    Optional:    false
QoS Class:       BestEffort
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
Events:
  Type    Reason     Age        From                 Message
  ----    ------     ----       ----                 -------
  Normal  Scheduled  <unknown>  default-scheduler    Successfully assigned default/lifecycle-demo-pod to k8s-node02
  Normal  Pulled     87s        kubelet, k8s-node02  Container image "registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24" already present on machine
  Normal  Created    87s        kubelet, k8s-node02  Created container init-myservice
  Normal  Started    87s        kubelet, k8s-node02  Started container init-myservice
  Normal  Pulled     86s        kubelet, k8s-node02  Container image "registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17" already present on machine
  Normal  Created    86s        kubelet, k8s-node02  Created container lifecycle-demo
  Normal  Started    86s        kubelet, k8s-node02  Started container lifecycle-demo
```

7、查看输出信息
```
# pwd
/data/volumes/nginx/log

# cat message 
Hello initContainers
Hello from the postStart handler
```
由上可知，init Container先执行，然后当一个主容器启动后，Kubernetes 将立即发送 postStart 事件。

8、停止该pod,查看日志
```
# kubectl delete pod lifecycle-demo-pod
pod "lifecycle-demo-pod" deleted

# pwd
/data/volumes/nginx/log

# cat message 
Hello initContainers
Hello from the postStart handler
Hello from the preStop handler
```
由上可知，当在容器被终结之前， Kubernetes 将发送一个 preStop 事件。

共享宿主机的Network、IPC 和 PIDNamespace
---
```
apiVersion: v1
kind: Pod
metadata:
  name: example
  namespace: default
  labels:
    app: example
spec:
  hostNetwork: true
  hostIPC: true
  hostPID: true
  containers:
  - name: busybox
    image: busybox
    args:
    - sleep
    - "600"
```

PodPreset
---

有时候需要重复为Pod定义某些自动，可以统一定义某些Pod自动注入。

比如想给web服务统一添加一个缓存目录，如果有很多web服务，每个添加比较麻烦，可以定义PodPreset，自动为Pod注入某些配置。


1、定义一个PodPreset对象
```
    apiVersion: settings.k8s.io/v1alpha1
    kind: PodPreset
    metadata:
      name: cache-pod-perset
    spec:
      selector:
        matchLabels:
          role: web
      volumeMounts:
      - mountPath: /cache
        name: cache-volume
      volumes:
      - name: cache-volume
        emptyDir: {}
```

2、定义一个Pod，在Pod创建时使用上面定义perSet
```
    apiVersion: v1
    kind: Pod
    metadata:
      name: example-pod-perset
      namespace: default
      labels:
        app: example
        role: web
    spec:
      containers:
      - name: nginx
        image: nginx:latest
```
在PodPreset的定义中，首先是一个selector，这就意味着后面这些追加的字段只会作用于selector所选中的Pod对象。
