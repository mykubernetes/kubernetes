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

Init容器
---
Init容器与普通的容器非常像，但是Init容器总是运行到成功完成为止。另外，每个Init容器都必须在下一个Init容器启动之前成功完成。

- 等待其他服务进入就绪状态：这个可以用来解决服务之间的依赖问题，比如有一个Web服务，该服务又依赖于另外一个数据库服务，但是在启动这个Web服务的时候并不能保证依赖的这个数据库服务就已经启动起来，所以可能会出现一段时间内Web服务连接数据库异常。解决这个问题可以在Web服务的Pod中使用一个InitContainer，在这个初始化容器中去检查数据库是否已经准备好了，如果数据库服务准备好了，初始化容器就结束退出，然后主容器Web服务开始启动，这个时候去连接数据库就不会有问题。
- 做初始化配置：比如集群里检测所有已经存在的成员节点，为主容器准备好集群的配置信息，这样主容器起来后就能用这个配置信息加入集群

```
apiVersion: v1
kind: Pod
metadata:
  name: example
  namespace: default
  labels:
    app: example
spec:
  containers:
  - name: nginx
    image: nginx:1.15.12
    imagePullPolicy: IfNotPresent
    volumeMounts:
    - name: workdir
      mountPath: /usr/share/nginx/html
  initContainers:
  - name: install
    image: busybox
    command:
    - wget
    - "-O"
    - "/work-dir/index.html"
    - http://kubernetes.io
    volumeMounts:
    - name: workdir
      mountPath: "/work-dir"
  volumes:
  - name: workdir
    emptyDir: {}
```

容器的创建，首先会执行initContainers，initContainers容器可以有多个，第一个成功退出后退出码为0，执行第二个initContainers容器
```
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
  labels:
    app: myapp
spec:
  containers:
  - name: myapp-container
    image: busybox
    command: ['sh', '-c', 'echo The app is running! && sleep 3600']
  initContainers:
  - name: init-myservice
    image: busybox
    command: ['sh', '-c', 'until nslookup myservice; do echo waiting for myservice; sleep 2;done;']
  - name: init-mydb
    image: busybox
    command: ['sh', '-c', 'until nslookup mydb; do echo waiting for mydb; sleep 2; done;']
```  

```
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
