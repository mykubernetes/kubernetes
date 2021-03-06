Pod对象
---
- apiVersion: api版本。
- kind: 编排对象，pod、Deployment、StatefulSet、DaemonSet、Service、Ingress等。
- metadata: 元数据，name、namespace、labels、annotations等。
  - labels: 一个API对象通过标签来选择另一个API对象
  - annotations: 是给Kubernetes看的，告诉Kubernetes开启某些功能
- spec: 用来描述这个API对象的期望状态。
- status: Pod的实际运行状态。

通过yaml创建nginx pod对象
```
# cat nginx_demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-demo
  namespace: default
  labels:
    k8s-app: nginx
    environment: dev
  annotations:
    name: nginx-demo
spec:
  containers:
  - name: nginx
    image: registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
    imagePullPolicy: IfNotPresent
    ports:
    - name: httpd
      containerPort: 80
      #除非绝对必要，否则不要为 Pod 指定 hostPort。 将 Pod 绑定到hostPort时，它会限制 Pod 可以调度的位置数
      #DaemonSet 中的 Pod 可以使用 hostPort，从而可以通过节点 IP 访问到 Pod；因为DaemonSet模式下Pod不会被调度到其他节点。
      #一般情况下 containerPort与hostPort值相同
      hostPort: 8090                    #可以通过宿主机+hostPort的方式访问该Pod。例如：pod在/调度到了k8s-node02【172.16.1.112】，那么该Pod可以通过172.16.1.112:8090方式进行访问。
      protocol: TCP
    volumeMounts:                       #定义容器挂载内容
    - name: nginx-site                  #使用的存储卷名称，跟下面volume字段的某个name值相同，这里表示使用volume的nginx-site这个存储卷
      mountPath: /usr/share/nginx/html  #挂载至容器中哪个目录
      readOnly: false                   #读写挂载方式，默认为读写模式false
    - name: nginx-log
      mountPath: /var/log/nginx/
      readOnly: false
  volumes:                              #volumes字段定义了paues容器关联的宿主机或分布式文件系统存储卷
  - name: nginx-site                    #存储卷名称
    hostPath:                           #路径，为宿主机存储路径
      path: /data/volumes/nginx/html/   #在宿主机上目录的路径
      type: DirectoryOrCreate           #定义类型，这表示如果宿主机没有此目录，则会自动创建
  - name: nginx-log
    hostPath:
      path: /data/volumes/nginx/log/
      type: DirectoryOrCreate
```

yaml格式的pod定义文件完整内容：  
---
```
apiVersion: v1                 #必选，版本号，例如v1
kind: Pod                      #必选，Pod
metadata:                      #必选，元数据
  name: string                 #必选，Pod名称
  namespace: string            #必选，Pod所属的命名空间
  labels:                      #自定义标签
    - name: string             #自定义标签名字
  annotations:                 #自定义注释列表
    - name: string
spec:                          #必选，Pod中容器的详细定义
  containers:                  #必选，Pod中容器列表
  - name: string               #必选，容器名称
    image: string              #必选，容器的镜像名称
    imagePullPolicy:           # Alawys下载镜像 IfnotPresent优先使用本地镜像，否则下载镜像，Nerver仅使用本地镜像
    command: [string]          #容器的启动命令列表，如不指定，使用打包时使用的启动命令
    args: [string]             #容器的启动命令参数列表
    workingDir: string         #容器的工作目录
    volumeMounts:              #挂载到容器内部的存储卷配置
    - name: string             #引用pod定义的共享存储卷的名称，需用volumes[]部分定义的的卷名
      mountPath: string        #存储卷在容器内mount的绝对路径，应少于512字符
      readOnly: boolean        #是否为只读模式
    ports:                     #需要暴露的端口库号列表
    - name: string             #端口号名称
      containerPort: int       #容器需要监听的端口号
      hostPort: int            #容器所在主机需要监听的端口号，默认与Container相同
      protocol: string         #端口协议，支持TCP和UDP，默认TCP
    env:                       #容器运行前需设置的环境变量列表
    - name: string             #环境变量名称
      value: string            #环境变量的值
    resources:                 #资源限制和请求的设置
      limits:                  #资源限制的设置
        cpu: string            #Cpu的限制，单位为core数，将用于docker run --cpu-shares参数
        memory: string         #内存限制，单位可以为Mib/Gib，将用于docker run --memory参数
      requests:                #资源请求的设置
        cpu: string            #Cpu请求，容器启动的初始可用数量
        memory: string         #内存清楚，容器启动的初始可用数量
    lifecycle                  #对pod内的容器进行启动后钩子和结束前钩子
      postStart                #启动后钩子
        exec
        httpGet
        tcpSocket
      preStop                  #结束前钩子
        exec
        httpGet
        tcpSocket
    readinessProbe：           #对pod内的容器就绪检查，当探测无响应几次后将自动重启该容器，检查方法有exec、httpGet和tcpSocket
    livenessProbe:             #对Pod内个容器健康检查，当探测无响应几次后将自动重启该容器，检查方法有exec、httpGet和tcpSocket
      exec:                    #对Pod容器内检查方式设置为exec方式
        command: [string]      #exec方式需要制定的命令或脚本
      httpGet:                 #对Pod内个容器健康检查方法设置为HttpGet，需要制定Path、port
        path: string
        port: number
        host: string
        scheme: string
        HttpHeaders:
        - name: string
          value: string
      tcpSocket:               #对Pod内个容器健康检查方式设置为tcpSocket方式
         port: number
      initialDelaySeconds: 0  #容器启动完成后首次探测的时间，单位为秒
      timeoutSeconds: 0       #对容器健康检查探测等待响应的超时时间，单位秒，默认1秒
      periodSeconds: 0        #对容器监控检查的定期探测时间设置，单位秒，默认10秒一次
      successThreshold: 0     ##对容器进行成功次数检查，默认1次
      failureThreshold: 0     #对容器进行失败次数检查，默认3次
      securityContext:
        privileged:false
  restartPolicy:            #Always不管以何种方式终止运行都将重启，OnFailure只有Pod以非0退出码退出才重启，Nerver不再重启该Pod
  nodeSelector: obeject     #设置NodeSelector表示将该Pod调度到包含这个label的node上，以key：value的格式指定
  imagePullSecrets:         #Pull镜像时使用的secret名称，以key：secretkey格式指定
  - name: string
  hostNetwork:false         #是否使用主机网络模式，默认为false，如果设置为true，表示使用宿主机网络
  volumes:                  #在该pod上定义共享存储卷列表
  - name: string            #共享存储卷名称 （volumes类型有很多种）
    emptyDir: {}            #类型为emtyDir的存储卷，与Pod同生命周期的一个临时目录。为空值
    hostPath: string        #类型为hostPath的存储卷，表示挂载Pod所在宿主机的目录
      path: string          #Pod所在宿主机的目录，将被用于同期中mount的目录
    secret:                 #类型为secret的存储卷，挂载集群与定义的secre对象到容器内部
      scretname: string  
      items:     
      - key: string
        path: string
    configMap:              #类型为configMap的存储卷，挂载预定义的configMap对象到容器内部
      name: string
      items:
      - key: string
        path: string
```  

控制器
===
kubernetes中内建了很多controller（控制器），这些相当于一个状态机，用来控制pod的具体状态和行为。

部分控制器类型如下：
- ReplicationController 和 ReplicaSet
- Deployment
- DaemonSet
- StatefulSet
- Job/CronJob
- HorizontalPodAutoscaler

ReplicationController 和 ReplicaSet
- ReplicationController (RC)用来确保容器应用的副本数始终保持在用户定义的副本数，即如果有容器异常退出，会自动创建新的pod来替代；而异常多出来的容器也会自动回收。
- 在新版的Kubernetes中建议使用ReplicaSet (RS)来取代ReplicationController。ReplicaSet跟ReplicationController没有本质的不同，只是名字不一样，但ReplicaSet支持集合式selector。
- 虽然 ReplicaSets 可以独立使用，但如今它主要被Deployments 用作协调 Pod 的创建、删除和更新的机制。当使用 Deployment 时，你不必担心还要管理它们创建的 ReplicaSet，Deployment 会拥有并管理它们的 ReplicaSet。
- ReplicaSet 是下一代的 Replication Controller。 ReplicaSet 和 Replication Controller 的唯一区别是选择器的支持。ReplicaSet 支持新的基于集合的选择器需求，这在标签用户指南中有描述。而 Replication Controller 仅支持基于相等选择器的需求。




ReplicaSet控制器  
---

1、ReplicaSet示例
```
# cat ReplicaSet-01.yaml 
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      tier: frontend
  template:
    metadata:
      labels:
        tier: frontend
    spec:
      containers:
      - name: nginx
        image: registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
        imagePullPolicy: IfNotPresent
        ports:
        - name: httpd
          containerPort: 80
```

2、创建ReplicaSet，并查看rs状态与详情
```
# kubectl apply -f ReplicaSet-01.yaml 
replicaset.apps/frontend created

# kubectl get rs -o wide               # 查看状态
NAME       DESIRED   CURRENT   READY   AGE     CONTAINERS   IMAGES                                                        SELECTOR
frontend   3         3         3       2m12s   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17   tier=frontend

# kubectl describe rs frontend         # 查看详情
Name:         frontend
Namespace:    default
Selector:     tier=frontend
Labels:       <none>
Annotations:  kubectl.kubernetes.io/last-applied-configuration:
                {"apiVersion":"apps/v1","kind":"ReplicaSet","metadata":{"annotations":{},"name":"frontend","namespace":"default"},"spec":{"replicas":3,"se...
Replicas:     3 current / 3 desired
Pods Status:  3 Running / 0 Waiting / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  tier=frontend
  Containers:
   nginx:
    Image:        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
    Port:         80/TCP
    Host Port:    0/TCP
    Environment:  <none>
    Mounts:       <none>
  Volumes:        <none>
Events:
  Type    Reason            Age    From                   Message
  ----    ------            ----   ----                   -------
  Normal  SuccessfulCreate  10m    replicaset-controller  Created pod: frontend-kltwp
  Normal  SuccessfulCreate  10m    replicaset-controller  Created pod: frontend-76dbn
  Normal  SuccessfulCreate  10m    replicaset-controller  Created pod: frontend-jk8td
```

3、查看pod状态信息
```
# kubectl get pod -o wide --show-labels
NAME             READY   STATUS    RESTARTS   AGE     IP            NODE         NOMINATED NODE   READINESS GATES   LABELS
frontend-76dbn   1/1     Running   0          5m15s   10.244.4.31   k8s-node01   <none>           <none>            tier=frontend
frontend-jk8td   1/1     Running   0          5m15s   10.244.2.35   k8s-node02   <none>           <none>            tier=frontend
frontend-kltwp   1/1     Running   0          5m15s   10.244.2.34   k8s-node02   <none>           <none>            tier=frontend
```

4、删除一个pod，然后再次查看
```
# kubectl delete pod frontend-kltwp
pod "frontend-kltwp" deleted

# kubectl get pod -o wide --show-labels   # 可见重新创建了一个pod
NAME             READY   STATUS    RESTARTS   AGE     IP            NODE         NOMINATED NODE   READINESS GATES   LABELS
frontend-76dbn   1/1     Running   0          7m27s   10.244.4.31   k8s-node01   <none>           <none>            tier=frontend
frontend-jk8td   1/1     Running   0          7m27s   10.244.2.35   k8s-node02   <none>           <none>            tier=frontend
frontend-mf79k   1/1     Running   0          16s     10.244.4.32   k8s-node01   <none>           <none>            tier=frontend
```
由上可见，rs又新建了一个pod，保证了pod数总是为3.



Deployments控制器  
---
Deployment 控制器为 Pods和 ReplicaSets提供描述性的更新方式。用来替代以前的ReplicationController以方便管理应用。

典型的应用场景包括：
- 定义Deployment来创建Pod和ReplicaSet
- 滚动升级和回滚应用
- 扩容和缩容
- 暂停和继续Deployment

1、创建 Deployment
```
# cat nginx-deployment-1.17.1.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
# 重点关注该字段
  minReadySeconds: 10
  strategy:                              #定义更新策略      
    rollingUpdate:                       #滚动更新策略定义临时减少和增加的pod
      maxSurge: 1                        #最多允许多几个pod
      maxUnavailable: 1                  #最少有几个不可用
    type: RollingUpdate                  #更新策略  
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
        image: registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1
        ports:
        - containerPort: 80
```

2、启动deployment，并查看状态
```
# kubectl apply -f nginx-deployment-1.17.1.yaml --record               # --record 参数可以记录命令，通过 kubectl rollout history deployment/nginx-deployment 可查询
deployment.apps/nginx-deployment created

# kubectl get deployment -o wide
NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                          SELECTOR
nginx-deployment   2/3     3            2           10s   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx
```
参数说明：
-NAME：列出集群中 Deployments 的名称
-READY：已就绪副本数/期望副本数
-UP-TO-DATE：显示已更新和正在更新中的副本数
-AVAILABLE：显示应用程序可供用户使用的副本数
-AGE：显示运行的时间

3、查看ReplicaSet状态
```
# kubectl get rs -o wide
NAME                          DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                          SELECTOR
nginx-deployment-76b9d6bcf5   3         3         2       17s   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx,pod-template-hash=76b9d6bcf5
```
参数说明：
- NAME：列出集群中 ReplicaSet的名称
- DESIRED：期望副本数
- CURRENT：当前副本数
- READY：已就绪副本数
- AGE：运行时间

4、查看pod状态
```
# kubectl get pod -o wide
NAME                                READY   STATUS              RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
nginx-deployment-76b9d6bcf5-ngpg5   1/1     Running             0          26s   10.244.2.43   k8s-node02   <none>           <none>
nginx-deployment-76b9d6bcf5-rw827   1/1     Running             0          26s   10.244.2.44   k8s-node02   <none>           <none>
nginx-deployment-76b9d6bcf5-ttf4j   0/1     ContainerCreating   0          26s   <none>        k8s-node01   <none>           <none>
```

5、过一会儿状态说明
```
# kubectl get deployment -o wide --show-labels
NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                          SELECTOR    LABELS
nginx-deployment   3/3     3            3           23m   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx   app=nginx

# kubectl get rs -o wide --show-labels
NAME                          DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                          SELECTOR                                 LABELS
nginx-deployment-76b9d6bcf5   3         3         3       23m   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx,pod-template-hash=76b9d6bcf5   app=nginx,pod-template-hash=76b9d6bcf5

# kubectl get pod -o wide --show-labels
NAME                                READY   STATUS    RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES   LABELS
nginx-deployment-76b9d6bcf5-ngpg5   1/1     Running   0          23m   10.244.2.43   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=76b9d6bcf5
nginx-deployment-76b9d6bcf5-rw827   1/1     Running   0          23m   10.244.2.44   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=76b9d6bcf5
nginx-deployment-76b9d6bcf5-ttf4j   1/1     Running   0          23m   10.244.4.37   k8s-node01   <none>         
```
重点说明
- 1、ReplicaSet 的名称始终被格式化为[DEPLOYMENT-NAME]-[RANDOM-STRING]。随机字符串是随机生成，并使用 pod-template-hash 作为选择器和标签。
- 2、Deployment 控制器将 pod-template-hash 标签添加到 Deployment 创建或使用的每个 ReplicaSet 。此标签可确保 Deployment 的子 ReplicaSets 不重叠。因此不可修改。
- 3、注意Deployment、ReplicaSet和Pod三者的名称关系

6、更新 Deployment
- Deployment 可确保在更新时仅关闭一定数量的 Pods。默认情况下，它确保至少 75%所需 Pods 运行（25%最大不可用）。
- Deployment 更新过程中还确保仅创建一定数量的 Pods 且高于期望的 Pods 数。默认情况下，它可确保最多增加 25% 期望 Pods 数（25%最大增量）。

备注：实际操作中如果更新Deployment，那么最好通过yaml文件更新，这样回滚到任何版本都非常便捷，而且更容易追述；而不是通过命令行。


6.1、如下Deployment示例，由于只有3个副本。因此更新时不会先删除旧的pod，而是先新建一个pod。新pod运行时，才会删除对应老的pod。一切的前提都是为了满足上述的条件。

需求：更新 nginx Pods，从当前的1.17.1版本改为1.17.5版本。
```
# 方式一
kubectl edit deployment/nginx-deployment    # 然后修改 image 镜像信息 【不推荐】
# 上述方法不会记录命令，通过kubectl rollout history deployment/nginx-deployment 无法查询

# 方式二如下【可使用】：
kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5 --record 

# 方式三如下【推荐★★★★★】
kubectl apply -f nginx-deployment-1.17.5.yaml --record

# --record 参数可以记录命令，通过 kubectl rollout history deployment/nginx-deployment 可查询
```

6.2、要查看更新状态
```
# kubectl rollout status deployment/nginx-deployment
# 如没有更新完成，则显示更新过程直到更新成功
Waiting for deployment "nginx-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deployment" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deployment" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deployment" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deployment" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "nginx-deployment" rollout to finish: 1 old replicas are pending termination...
deployment "nginx-deployment" successfully rolled out

# 如已更新完毕，直接显示更新成功
deployment "nginx-deployment" successfully rolled out
```

6.3、更新中的Deployment、ReplicaSet、Pod信息
```
# kubectl get deployment -o wide --show-labels
NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                          SELECTOR    LABELS
nginx-deployment   3/3     1            3           12m   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx   app=nginx

# kubectl get rs -o wide --show-labels
NAME                          DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                          SELECTOR                                 LABELS
nginx-deployment-56d78686f5   1         1         0       23s   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx,pod-template-hash=56d78686f5   app=nginx,pod-template-hash=56d78686f5
nginx-deployment-76b9d6bcf5   3         3         3       12m   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx,pod-template-hash=76b9d6bcf5   app=nginx,pod-template-hash=76b9d6bcf5

# kubectl get pod -o wide --show-labels
NAME                                READY   STATUS              RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES   LABELS
nginx-deployment-56d78686f5-4kn4c   0/1     ContainerCreating   0          30s   <none>        k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-76b9d6bcf5-7lcr9   1/1     Running             0          12m   10.244.4.41   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=76b9d6bcf5
nginx-deployment-76b9d6bcf5-jbb5h   1/1     Running             0          12m   10.244.2.48   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=76b9d6bcf5
nginx-deployment-76b9d6bcf5-rt4m7   1/1     Running             0          12m   10.244.4.42   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=76b9d6bcf5
```

6.4、更新成功后的Deployment、ReplicaSet、Pod信息
```
# kubectl get deployment -o wide --show-labels
NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                          SELECTOR    LABELS
nginx-deployment   3/3     3            3           15m   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx   app=nginx

# kubectl get rs -o wide --show-labels
NAME                          DESIRED   CURRENT   READY   AGE     CONTAINERS   IMAGES                                                          SELECTOR                                 LABELS
nginx-deployment-56d78686f5   3         3         3       3m23s   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx,pod-template-hash=56d78686f5   app=nginx,pod-template-hash=56d78686f5
nginx-deployment-76b9d6bcf5   0         0         0       15m     nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx,pod-template-hash=76b9d6bcf5   app=nginx,pod-template-hash=76b9d6bcf5

# kubectl get pod -o wide --show-labels
NAME                                READY   STATUS    RESTARTS   AGE     IP            NODE         NOMINATED NODE   READINESS GATES   LABELS
nginx-deployment-56d78686f5-4kn4c   1/1     Running   0          3m25s   10.244.2.49   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-khsnm   1/1     Running   0          100s    10.244.2.50   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-t24qw   1/1     Running   0          2m44s   10.244.4.43   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
```

6.5、通过查询Deployment详情，知晓pod替换过程
```
# kubectl describe deploy nginx-deployment
Name:                   nginx-deployment
Namespace:              default
CreationTimestamp:      Thu, 28 May 2020 00:04:09 +0800
Labels:                 app=nginx
Annotations:            deployment.kubernetes.io/revision: 2
                        kubectl.kubernetes.io/last-applied-configuration:
                          {"apiVersion":"apps/v1","kind":"Deployment","metadata":{"annotations":{"kubernetes.io/change-cause":"kubectl apply --filename=nginx-deploy...
                        kubernetes.io/change-cause:
                          kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5 --record=true
Selector:               app=nginx
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=nginx
  Containers:
   nginx:
    Image:        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5
    Port:         80/TCP
    Host Port:    0/TCP
    Environment:  <none>
    Mounts:       <none>
  Volumes:        <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   nginx-deployment-56d78686f5 (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  93s   deployment-controller  Scaled up replica set nginx-deployment-76b9d6bcf5 to 3
  Normal  ScalingReplicaSet  38s   deployment-controller  Scaled up replica set nginx-deployment-56d78686f5 to 1
  Normal  ScalingReplicaSet  37s   deployment-controller  Scaled down replica set nginx-deployment-76b9d6bcf5 to 2
  Normal  ScalingReplicaSet  37s   deployment-controller  Scaled up replica set nginx-deployment-56d78686f5 to 2
  Normal  ScalingReplicaSet  35s   deployment-controller  Scaled down replica set nginx-deployment-76b9d6bcf5 to 1
  Normal  ScalingReplicaSet  35s   deployment-controller  Scaled up replica set nginx-deployment-56d78686f5 to 3
  Normal  ScalingReplicaSet  34s   deployment-controller  Scaled down replica set nginx-deployment-76b9d6bcf5 to 0
```

6.6、多 Deployment 动态更新
- 当 Deployment 正在展开进行更新时，Deployment 会为每个更新创建一个新的 ReplicaSet 并开始向上扩展，之前的 ReplicaSet 会被添加到旧 ReplicaSets 队列并开始向下扩展。


7、回滚 Deployment

7.1、命令行方式

问题产生
- 假设在更新 Deployment 时犯了一个拼写错误，将镜像名称命名为了 nginx:1.1710 而不是 nginx:1.17.10
```
# kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.1710 --record
deployment.apps/nginx-deployment image updated
```

7.2、查看Deployment、ReplicaSet、Pod信息
```
# kubectl get deploy -o wide --show-labels
NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                          SELECTOR    LABELS
nginx-deployment   3/3     1            3           14m   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.1710   app=nginx   app=nginx

# kubectl get rs -o wide --show-labels
NAME                          DESIRED   CURRENT   READY   AGE     CONTAINERS   IMAGES                                                          SELECTOR                                 LABELS
nginx-deployment-55c7bdfb86   3         3         3       9m19s   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17     app=nginx,pod-template-hash=55c7bdfb86   app=nginx,pod-template-hash=55c7bdfb86
nginx-deployment-56d78686f5   0         0         0       12m     nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx,pod-template-hash=56d78686f5   app=nginx,pod-template-hash=56d78686f5
nginx-deployment-76b9d6bcf5   0         0         0       13m     nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx,pod-template-hash=76b9d6bcf5   app=nginx,pod-template-hash=76b9d6bcf5
nginx-deployment-844d7bbb7f   1         1         0       64s     nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.1710   app=nginx,pod-template-hash=844d7bbb7f   app=nginx,pod-template-hash=844d7bbb7f

# kubectl get pod -o wide --show-labels
NAME                                READY   STATUS             RESTARTS   AGE    IP            NODE         NOMINATED NODE   READINESS GATES   LABELS
nginx-deployment-55c7bdfb86-bwzk9   1/1     Running            0          10m    10.244.4.49   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=55c7bdfb86
nginx-deployment-55c7bdfb86-cmvzg   1/1     Running            0          10m    10.244.2.55   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=55c7bdfb86
nginx-deployment-55c7bdfb86-kjrrw   1/1     Running            0          10m    10.244.2.56   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=55c7bdfb86
nginx-deployment-844d7bbb7f-pctwr   0/1     ImagePullBackOff   0          2m3s   10.244.4.51   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=844d7bbb7f
```

7.3、需求：回滚到以前稳定的 Deployment 版本。

7.4、检查 Deployment 修改历史
```
# kubectl rollout history deployment/nginx-deployment
deployment.apps/nginx-deployment 
REVISION  CHANGE-CAUSE
1         kubectl apply --filename=nginx-deployment.yaml --record=true
2         kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5 --record=true
3         kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17 --record=true
4         kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.1710 --record=true
```

7.5、查看修改历史的详细信息，运行
```
# kubectl rollout history deployment/nginx-deployment --revision=3
deployment.apps/nginx-deployment with revision #3
Pod Template:
  Labels:	app=nginx
	pod-template-hash=55c7bdfb86
  Annotations:	kubernetes.io/change-cause:
	  kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17 --record=true
  Containers:
   nginx:
    Image:	registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
    Port:	80/TCP
    Host Port:	0/TCP
    Environment:	<none>
    Mounts:	<none>
  Volumes:	<none>
```

7.6、回滚到上一次修改（即版本 3）或指定版本

现在已决定撤消当前更新并回滚到以前的版本
```
# 回滚到上一版本
# kubectl rollout undo deployment/nginx-deployment
deployment.apps/nginx-deployment rolled back

# 回滚到指定历史版本
# kubectl rollout undo deployment/nginx-deployment --to-revision=2
deployment.apps/nginx-deployment rolled back
```

7.7、检查回滚是否成功、 Deployment 是否正在运行
```
# kubectl get deploy -o wide --show-labels
NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                          SELECTOR    LABELS
nginx-deployment   3/3     3            3           17h   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx   app=nginx
```

7.8、获取 Deployment 描述信息
```
# kubectl describe deployment
Name:                   nginx-deployment
Namespace:              default
CreationTimestamp:      Thu, 28 May 2020 00:04:09 +0800
Labels:                 app=nginx
Annotations:            deployment.kubernetes.io/revision: 7
                        kubectl.kubernetes.io/last-applied-configuration:
                          {"apiVersion":"apps/v1","kind":"Deployment","metadata":{"annotations":{"kubernetes.io/change-cause":"kubectl apply --filename=nginx-deploy...
                        kubernetes.io/change-cause:
                          kubectl set image deployment/nginx-deployment nginx=registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5 --record=true
Selector:               app=nginx
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=nginx
  Containers:
   nginx:
    Image:        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5
    Port:         80/TCP
    Host Port:    0/TCP
    Environment:  <none>
    Mounts:       <none>
  Volumes:        <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   nginx-deployment-56d78686f5 (3/3 replicas created)
Events:
  Type    Reason             Age                 From                   Message
  ----    ------             ----                ----                   -------
………………
  Normal  ScalingReplicaSet  107s                deployment-controller  Scaled up replica set nginx-deployment-56d78686f5 to 1
  Normal  ScalingReplicaSet  104s                deployment-controller  Scaled down replica set nginx-deployment-55c7bdfb86 to 2
  Normal  ScalingReplicaSet  104s                deployment-controller  Scaled up replica set nginx-deployment-56d78686f5 to 2
  Normal  ScalingReplicaSet  103s                deployment-controller  Scaled down replica set nginx-deployment-55c7bdfb86 to 1
  Normal  ScalingReplicaSet  103s                deployment-controller  Scaled up replica set nginx-deployment-56d78686f5 to 3
  Normal  ScalingReplicaSet  102s                deployment-controller  Scaled down replica set nginx-deployment-55c7bdfb86 to 0
```

8、扩容/缩容Deployment
```
# kubectl scale deployment/nginx-deployment --replicas=10
deployment.apps/nginx-deployment scaled

# kubectl get deploy -o wide --show-labels
NAME               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                                                          SELECTOR    LABELS
nginx-deployment   10/10   10           10          17h   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx   app=nginx

# kubectl get rs -o wide --show-labels
NAME                          DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES                                                          SELECTOR                                 LABELS
nginx-deployment-55c7bdfb86   0         0         0       17h   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17     app=nginx,pod-template-hash=55c7bdfb86   app=nginx,pod-template-hash=55c7bdfb86
nginx-deployment-56d78686f5   10        10        10      17h   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.5   app=nginx,pod-template-hash=56d78686f5   app=nginx,pod-template-hash=56d78686f5
nginx-deployment-76b9d6bcf5   0         0         0       17h   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17.1   app=nginx,pod-template-hash=76b9d6bcf5   app=nginx,pod-template-hash=76b9d6bcf5
nginx-deployment-844d7bbb7f   0         0         0       17h   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.1710   app=nginx,pod-template-hash=844d7bbb7f   app=nginx,pod-template-hash=844d7bbb7f

# kubectl get pod -o wide --show-labels
NAME                                READY   STATUS    RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES   LABELS
nginx-deployment-56d78686f5-4v5mj   1/1     Running   0          44s   10.244.2.64   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-8m7mx   1/1     Running   0          44s   10.244.4.60   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-c7wlb   1/1     Running   0          44s   10.244.4.59   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-jg5lt   1/1     Running   0          44s   10.244.2.63   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-jj58d   1/1     Running   0          11m   10.244.4.56   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-k2kts   1/1     Running   0          11m   10.244.4.57   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-qltkv   1/1     Running   0          44s   10.244.2.61   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-r7vmm   1/1     Running   0          11m   10.244.2.60   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-rxlpm   1/1     Running   0          44s   10.244.2.62   k8s-node02   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
nginx-deployment-56d78686f5-vlzrf   1/1     Running   0          44s   10.244.4.58   k8s-node01   <none>           <none>            app=nginx,pod-template-hash=56d78686f5
```

9、清理策略Policy
- 可以在 Deployment 中设置 .spec.revisionHistoryLimit，以指定保留多少该 Deployment 的 ReplicaSets数量。其余的将在后台进行垃圾回收。默认情况下，是10。

注意：此字段设置为 0 将导致清理 Deployment 的所有历史记录，因此 Deployment 将无法通过命令行回滚。



DaemonSet控制器  
---
- DaemonSet 确保全部（或者某些）节点上运行一个 Pod 的副本。当有节点加入集群时，会为他们新增一个 Pod。当有节点从集群移除时，这些 Pod 也会被回收。删除 DaemonSet 将会删除它创建的所有 Pod。

DaemonSet 的一些典型用法：
- 在每个节点上运行集群存储 DaemonSet，例如 glusterd、ceph。
- 在每个节点上运行日志收集 DaemonSet，例如 fluentd、logstash。
- 在每个节点上运行监控 DaemonSet，例如 Prometheus Node Exporter、Flowmill、Sysdig 代理、collectd、Dynatrace OneAgent、AppDynamics 代理、Datadog 代理、New Relic 代理、Ganglia gmond 或者 Instana 代理。


备注：DaemonSet 中的 Pod 可以使用 hostPort，从而可以通过节点 IP 访问到 Pod；因为DaemonSet模式下Pod不会被调度到其他节点。使用示例如下：
```
ports:
- name: httpd
  containerPort: 80
  #除非绝对必要，否则不要为 Pod 指定 hostPort。 将 Pod 绑定到hostPort时，它会限制 Pod 可以调度的位置数；DaemonSet除外
  #一般情况下 containerPort与hostPort值相同
  hostPort: 8090     #可以通过宿主机+hostPort的方式访问该Pod。例如：pod在/调度到了k8s-node02【172.16.1.112】，那么该Pod可以通过172.16.1.112:8090方式进行访问。
  protocol: TCP
```

1、DaemonSet示例
```
# cat daemonset.yaml 
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-elasticsearch
  namespace: default
  labels:
    k8s-app: fluentd-logging
spec:
  selector:
    matchLabels:
      name: fluentd-elasticsearch
  template:
    metadata:
      labels:
        name: fluentd-elasticsearch
    spec:
      tolerations:
      # 允许在master节点运行
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      containers:
      - name: fluentd-elasticsearch
        image: registry.cn-beijing.aliyuncs.com/google_registry/fluentd:v2.5.2
        resources:
          limits:
            cpu: 1
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 200Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      # 优雅关闭应用，时间设置。超过该时间会强制关闭【可选项】，默认30秒
      terminationGracePeriodSeconds: 30
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

2、运行daemonset，并查看状态
```
# kubectl apply -f daemonset.yaml 
daemonset.apps/fluentd-elasticsearch created

# kubectl get daemonset -o wide
NAME                    DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE   CONTAINERS              IMAGES                                                            SELECTOR
fluentd-elasticsearch   3         3         3       3            3           <none>          92s   fluentd-elasticsearch   registry.cn-beijing.aliyuncs.com/google_registry/fluentd:v2.5.2   name=fluentd-elasticsearch

# kubectl get pod -o wide
NAME                          READY   STATUS    RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
fluentd-elasticsearch-52b8z   1/1     Running   0          95s   10.244.2.92   k8s-node02   <none>           <none>
fluentd-elasticsearch-fps95   1/1     Running   0          95s   10.244.0.46   k8s-master   <none>           <none>
fluentd-elasticsearch-pz8j7   1/1     Running   0          95s   10.244.4.83   k8s-node01   <none>           <none>
```
由上可见，在k8s集群所有节点包括master节点都运行了daemonset的pod。



job控制器
---

- Job创建一个或多个Pod，并确保指定数量的Pod成功终止。Pod成功完成后，Job将跟踪成功完成的情况。当达到指定的成功完成次数时，任务（即Job）就完成了。删除Job将清除其创建的Pod。
- 一个简单的情况是创建一个Job对象，以便可靠地运行一个Pod来完成。如果第一个Pod发生故障或被删除（例如，由于节点硬件故障或节点重启），则Job对象将启动一个新的Pod。
- 当然还可以使用Job并行运行多个Pod。

Job终止和清理
- Job完成后，不会再创建其他Pod，但是Pod也不会被删除。这样使我们仍然可以查看已完成容器的日志，以检查是否有错误、警告或其他诊断输出。Job对象在完成后也将保留下来，以便您查看其状态。
- 当我们删除Job对象时，对应的pod也会被删除。

特殊说明
- 单个Pod时，默认Pod成功运行后Job即结束
- restartPolicy 仅支持Never和OnFailure
- .spec.completions 标识Job结束所需要成功运行的Pod个数，默认为1
- .spec.parallelism 标识并行运行的Pod个数，默认为1
- .spec.activeDeadlineSeconds 为Job的持续时间，不管有多少Pod创建。一旦工作到指定时间，所有的运行pod都会终止且工作状态将成为type: Failed与reason: DeadlineExceeded。

```
apiVersion: batch/v1
kind: Job
metadata:
  name: job-multi
spec:
  activeDeadlineSeconds: 100           #最大活动时间长度，超出此时长的作业将被终止
  backoffLimit: 5                      #将作业标记为失败状态之前的重试次数，默认值为6
  completions: 5                       #总共运行次数
  parallelism： 2                      #并行执行数量
  template:
    metadata:
      labels:
        app: myjob
    spec:
      containers:
      - name: myjob
        image: alpine
        command: ["/bin/sh",  "-c", "sleep 30"]
      restartPolicy: Never           #仅支持Never和OnFailure两种，不支持Always
```  

1、Job示例
```
# cat job.yaml 
apiVersion: batch/v1
kind: Job
metadata:
  name: pi
spec:
  #completions: 3  # 标识Job结束所需要成功运行的Pod个数，默认为1
  template:
    spec:
      containers:
      - name: pi
        image: registry.cn-beijing.aliyuncs.com/google_registry/perl:5.26
        command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never
  backoffLimit: 4
```

2、创建job，与状态查看
```
# kubectl apply -f job.yaml 
job.batch/pi created

# kubectl get job -o wide
NAME   COMPLETIONS   DURATION   AGE   CONTAINERS   IMAGES                                                       SELECTOR
pi     0/1           16s        16s   pi           registry.cn-beijing.aliyuncs.com/google_registry/perl:5.26   controller-uid=77004357-fd5e-4395-9bbb-cd0698e19cb9

# kubectl get pod -o wide
NAME       READY   STATUS              RESTARTS   AGE   IP       NODE         NOMINATED NODE   READINESS GATES
pi-6zvm5   0/1     ContainerCreating   0          85s   <none>   k8s-node01   <none>           <none>
```

3、再次查看
```
# kubectl get job -o wide
NAME   COMPLETIONS   DURATION   AGE   CONTAINERS   IMAGES                                                       SELECTOR
pi     1/1           14m        44m   pi           registry.cn-beijing.aliyuncs.com/google_registry/perl:5.26   controller-uid=77004357-fd5e-4395-9bbb-cd0698e19cb9

# kubectl get pod -o wide
NAME       READY   STATUS      RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
pi-6zvm5   0/1     Completed   0          44m   10.244.4.63   k8s-node01   <none>           <none>

# kubectl describe job pi
Name:           pi
Namespace:      default
Selector:       controller-uid=76680f6f-442c-4a09-91dc-c3d4c18465b0
Labels:         controller-uid=76680f6f-442c-4a09-91dc-c3d4c18465b0
                job-name=pi
Annotations:    kubectl.kubernetes.io/last-applied-configuration:
                  {"apiVersion":"batch/v1","kind":"Job","metadata":{"annotations":{},"name":"pi","namespace":"default"},"spec":{"backoffLimit":4,"
Parallelism:    1
Completions:    1
Start Time:     Tue, 11 Aug 2020 23:34:44 +0800
Completed At:   Tue, 11 Aug 2020 23:35:02 +0800
Duration:       18s
Pods Statuses:  0 Running / 1 Succeeded / 0 Failed
Pod Template:
  Labels:  controller-uid=76680f6f-442c-4a09-91dc-c3d4c18465b0
           job-name=pi
  Containers:
   pi:
    Image:      registry.cn-beijing.aliyuncs.com/google_registry/perl:5.26
    Port:       <none>
    Host Port:  <none>
    Command:
      perl
      -Mbignum=bpi
      -wle
      print bpi(2000)
    Environment:  <none>
    Mounts:       <none>
  Volumes:        <none>
Events:
  Type    Reason            Age    From            Message
  ----    ------            ----   ----            -------
  Normal  SuccessfulCreate  2m33s  job-controller  Created pod: pi-6zvm5
```

4、并查看 Pod 的标准输出
```
[root@k8s-master controller]# kubectl logs --tail 500 pi-6zvm5
3.141592653589793238462643383279502884197169399375105820974944592307816406………………
```

CronJob控制器
---

Cron Job 创建是基于时间调度的 Jobs

一个 CronJob 对象就像 crontab (cron table) 文件中的一行。它用 Cron 格式进行编写，并周期性地在给定的调度时间执行 Job。
CronJob 限制

CronJob 创建 Job 对象，每个 Job 的执行次数大约为一次。 之所以说 “大约” ，是因为在某些情况下，可能会创建两个 Job，或者不会创建任何 Job。虽然试图使这些情况尽量少发生，但不能完全杜绝。因此，Job 应该是幂等的。

CronJob 仅负责创建与其调度时间相匹配的 Job，而 Job 又负责管理其代表的 Pod。

使用案例：
- 1、在给定时间点调度Job
- 2、创建周期性运行的Job。如：数据备份、数仓导数、执行任务、邮件发送、数据拉取、数据推送

特殊说明
- .spec.schedule 必选，任务被创建和执行的调度时间。同Cron格式串，例如 0 * * * *。
- .spec.jobTemplate 必选，任务模版。它和 Job的语法完全一样
- .spec.startingDeadlineSeconds 可选的。默认未设置。它表示任务如果由于某种原因错过了调度时间，开始该任务的截止时间的秒数。过了截止时间，CronJob 就不会开始任务。不满足这种最后期限的任务会被统计为失败任务。如果没有该声明，那任务就没有最后期限。
- .spec.concurrencyPolicy 可选的。它声明了 CronJob 创建的任务执行时发生重叠如何处理。spec 仅能声明下列规则中的一种：
  - Allow (默认)：CronJob 允许并发任务执行。
  - Forbid：CronJob 不允许并发任务执行；如果新任务的执行时间到了而老任务没有执行完，CronJob 会忽略新任务的执行。
  - Replace：如果新任务的执行时间到了而老任务没有执行完，CronJob 会用新任务替换当前正在运行的任务。

请注意，并发性规则仅适用于相同 CronJob 创建的任务。如果有多个 CronJob，它们相应的任务总是允许并发执行的。

- .spec.suspend 可选的。如果设置为 true ，后续发生的执行都会挂起。这个设置对已经开始执行的Job不起作用。默认是关闭的false。备注：在调度时间内挂起的执行都会被统计为错过的任务。当 .spec.suspend 从 true 改为 false 时，且没有开始的最后期限，错过的任务会被立即调度。
- .spec.successfulJobsHistoryLimit 和 .spec.failedJobsHistoryLimit 可选的。 这两个声明了有多少执行完成和失败的任务会被保留。默认设置为3和1。限制设置为0代表相应类型的任务完成后不会保留。

说明：如果 startingDeadlineSeconds 设置为很大的数值或未设置（默认），并且 concurrencyPolicy 设置为 Allow，则作业将始终至少运行一次。


```
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: cronjob-example
  labels:
    app: mycronjob
spec:
  schedule: "*/2 * * * *"         #Cron格式的作业调度运行时间点；必选字段
  successfulJobsHistoryLimit: 3   #为成功的任务执行保留历史记录数，默认为3
  failedJobHistoryLimit: 1        #为失败的任务执行保留的历史记录数，默认为1
  startingDeadlineSeconds： 3     #因各种原因缺乏执行作业的时间点所导致的启动作业错误的超时时长，会被记入错误历史记录
  concurrencyPolicy: Allow        #并发执行策略，Allow(允许)、Forbid（禁止）、Replace（替换）定义前一次作业尚未完成时是否运行后一次的作业
  suspend：false                  #如果设置为true，后续所有执行都会被挂起。它对已经开始执行的Job不起作用
  jobTemplate:                    #Job控制器模板,用于为CronJob控制器生成Job对象；必选字段
    metadata:
      labels:
        app: mycronjob-jobs
    spec:
      parallelism: 2
      template:
        spec:
          containers:
          - name: myjob
            image: alpine
            command:
            - /bin/sh
            - -c
            - date; echo Hello from the Kubernetes cluster; sleep 10
          restartPolicy: OnFailure           #仅支持Never和OnFailure两种，不支持Always
```

1、CronJob示例
```
# cat cronjob.yaml 
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: hello
spec:
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: hello
            image: registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24
            args:
            - /bin/sh
            - -c
            - date; echo Hello from the Kubernetes cluster
          restartPolicy: OnFailure
```

2、启动cronjob并查看状态
```
# kubectl apply -f cronjob.yaml 
cronjob.batch/hello created

# kubectl get cronjob -o wide
NAME    SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE   CONTAINERS   IMAGES                                                          SELECTOR
hello   */1 * * * *   False     1        8s              27s   hello        registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24   <none>

# kubectl get job -o wide
NAME               COMPLETIONS   DURATION   AGE   CONTAINERS   IMAGES                                                          SELECTOR
hello-1590721020   1/1           2s         21s   hello        registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24   controller-uid=9e0180e8-8362-4a58-8b93-089b92774b5e

# kubectl get pod -o wide
NAME                     READY   STATUS      RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
hello-1590721020-m4fr8   0/1     Completed   0          36s   10.244.4.66   k8s-node01   <none>           <none>
```

3、几分钟之后的状态信息
```
# kubectl get cronjob -o wide
NAME    SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE     CONTAINERS   IMAGES                                                          SELECTOR
hello   */1 * * * *   False     0        55s             7m14s   hello        registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24   <none>

# kubectl get job -o wide
NAME               COMPLETIONS   DURATION   AGE    CONTAINERS   IMAGES                                                          SELECTOR
hello-1590721260   1/1           1s         3m1s   hello        registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24   controller-uid=0676bd6d-861b-440b-945b-4b2704872728
hello-1590721320   1/1           2s         2m1s   hello        registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24   controller-uid=09c1902e-76ef-4731-b3b4-3188961c13e9
hello-1590721380   1/1           2s         61s    hello        registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24   controller-uid=f30dc159-8905-4cfc-b06b-f950c8dcfc28

# kubectl get pod -o wide
NAME                     READY   STATUS      RESTARTS   AGE    IP            NODE         NOMINATED NODE   READINESS GATES
hello-1590721320-m4pxf   0/1     Completed   0          2m6s   10.244.4.70   k8s-node01   <none>           <none>
hello-1590721380-wk7jh   0/1     Completed   0          66s    10.244.2.77   k8s-node02   <none>           <none>
hello-1590721440-rcx7v   0/1     Completed   0          6s     10.244.4.72   k8s-node01   <none>           <none>

# kubectl describe cronjob hello
Name:                          hello
Namespace:                     default
Labels:                        <none>
Annotations:                   kubectl.kubernetes.io/last-applied-configuration:
                                 {"apiVersion":"batch/v1beta1","kind":"CronJob","metadata":{"annotations":{},"name":"hello","namespace":"default"},"spec":{"jobTemplate":{"...
Schedule:                      */1 * * * *
Concurrency Policy:            Allow
Suspend:                       False
Successful Job History Limit:  3
Failed Job History Limit:      1
Starting Deadline Seconds:     <unset>
Selector:                      <unset>
Parallelism:                   <unset>
Completions:                   <unset>
Pod Template:
  Labels:  <none>
  Containers:
   hello:
    Image:      registry.cn-beijing.aliyuncs.com/google_registry/busybox:1.24
    Port:       <none>
    Host Port:  <none>
    Args:
      /bin/sh
      -c
      date; echo Hello from the Kubernetes cluster
    Environment:     <none>
    Mounts:          <none>
  Volumes:           <none>
Last Schedule Time:  Wed, 12 Aug 2020 00:01:00 +0800
Active Jobs:         <none>
Events:
  Type    Reason            Age                  From                Message
  ----    ------            ----                 ----                -------
  Normal  SuccessfulCreate  19m                  cronjob-controller  Created job hello-1597160520
  Normal  SawCompletedJob   19m                  cronjob-controller  Saw completed job: hello-1597160520, status: Complete
  Normal  SuccessfulCreate  18m                  cronjob-controller  Created job hello-1597160580
  Normal  SawCompletedJob   18m                  cronjob-controller  Saw completed job: hello-1597160580, status: Complete
  Normal  SuccessfulCreate  17m                  cronjob-controller  Created job hello-1597160640
  Normal  SawCompletedJob   17m                  cronjob-controller  Saw completed job: hello-1597160640, status: Complete
  Normal  SuccessfulCreate  16m                  cronjob-controller  Created job hello-1597160700
  Normal  SuccessfulDelete  16m                  cronjob-controller  Deleted job hello-1597160520
  Normal  SawCompletedJob   16m                  cronjob-controller  Saw completed job: hello-1597160700, status: Complete
  Normal  SuccessfulCreate  15m                  cronjob-controller  Created job hello-1597160760
  Normal  SawCompletedJob   15m                  cronjob-controller  Saw completed job: hello-1597160760, status: Complete
  Normal  SuccessfulDelete  15m                  cronjob-controller  Deleted job hello-1597160580
  Normal  SuccessfulCreate  14m                  cronjob-controller  Created job hello-1597160820
  Normal  SuccessfulDelete  14m                  cronjob-controller  Deleted job hello-1597160640
  Normal  SawCompletedJob   14m                  cronjob-controller  Saw completed job: hello-1597160820, status: Complete
  Normal  SuccessfulCreate  13m                  cronjob-controller  Created job hello-1597160880
  Normal  SawCompletedJob   13m                  cronjob-controller  Saw completed job: hello-1597160880, status: Complete
………………
  Normal  SawCompletedJob   11m                  cronjob-controller  Saw completed job: hello-1597161000, status: Complete
  Normal  SuccessfulDelete  11m                  cronjob-controller  Deleted job hello-1597160820
  Normal  SawCompletedJob   10m                  cronjob-controller  (combined from similar events): Saw completed job: hello-1597161060, status: Complete
  Normal  SuccessfulCreate  4m13s (x7 over 10m)  cronjob-controller  (combined from similar events): Created job hello-1597161420
```

4、找到最后一次调度任务创建的 Pod， 并查看 Pod 的标准输出。请注意任务名称和 Pod 名称是不同的。
```
#  kubectl logs pod/hello-1590721740-rcx7v      # 或者 kubectl logs hello-1590721740-rcx7v
Fri May 29 03:09:04 UTC 2020
Hello from the Kubernetes cluster
```

5、删除 CronJob
```
# kubectl get cronjob
NAME    SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
hello   */1 * * * *   False     0        32s             19m

# kubectl delete cronjob hello  # 或者 kubectl delete -f cronjob.yaml
cronjob.batch "hello" deleted

# kubectl get cronjob                 # 可见已删除
No resources found in default namespace.
```

statefulset
---

StatefulSet 中的 Pod 拥有一个具有黏性的、独一无二的身份标识。这个标识基于 StatefulSet 控制器分配给每个 Pod 的唯一顺序索引。Pod 的名称的形式为<statefulset name>-<ordinal index> 。例如：web的StatefulSet 拥有两个副本，所以它创建了两个 Pod：web-0和web-1。

和 Deployment 相同的是，StatefulSet 管理了基于相同容器定义的一组 Pod。但和 Deployment 不同的是，StatefulSet 为它们的每个 Pod 维护了一个固定的 ID。这些 Pod 是基于相同的声明来创建的，但是不能相互替换：无论怎么调度，每个 Pod 都有一个永久不变的 ID。

【使用场景】StatefulSets 对于需要满足以下一个或多个需求的应用程序很有价值：
- 稳定的、唯一的网络标识符，即Pod重新调度后其PodName和HostName不变【当然IP是会变的】
- 稳定的、持久的存储，即Pod重新调度后还是能访问到相同的持久化数据，基于PVC实现
- 有序的、优雅的部署和缩放
- 有序的、自动的滚动更新

限制
- 给定 Pod 的存储必须由 PersistentVolume 驱动 基于所请求的 storage class 来提供，或者由管理员预先提供。
- 删除或者收缩 StatefulSet 并不会删除它关联的存储卷。这样做是为了保证数据安全，它通常比自动清除 StatefulSet 所有相关的资源更有价值。
- StatefulSet 当前需要 headless 服务 来负责 Pod 的网络标识。你需要负责创建此服务。
- 当删除 StatefulSets 时，StatefulSet 不提供任何终止 Pod 的保证。为了实现 StatefulSet 中的 Pod 可以有序和优雅的终止，可以在删除之前将 StatefulSet 缩放为 0。
- 在默认 Pod 管理策略(OrderedReady) 时使用滚动更新，可能进入需要人工干预才能修复的损坏状态。

| Cluster Domain | Service(ns/name) | Statefulset(ns/name) | StatefulSet Domain | Pod DNS | Pod Hostname |
|----------------|------------------|---------------------|--------------------|----------|--------------|
| cluster.local | default/nginx | default/web | nginx.default.svc.cluster.local | web-{0..N-1}.nginx.default.svc.cluster.local | web-{0..N-1} |
| cluster.local | foo/nginx | foo/web | nginx.foo.svc.cluster.local | web-{0..N-1}.nginx.foo.svc.cluster.local | web-{0..N-1} |
| kube.local | foo/nginx | foo/web | nginx.foo.svc.kube.local | web-{0..N-1}.nginx.foo.svc.kube.local | web-{0..N-1} |

```
nslookup web-0.nginx.default.svc.cluster.local
```

```
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
  labels:
    app: myapp-svc
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None                #配置statefulset需要配置成None
  selector:
    app: myapp-pod
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: myapp
spec:
  serviceName: myapp-svc
  replicas: 2                    #副本模式
  selector:
    matchLabels:
      app: myapp-pod
  template:
    metadata:
      labels:
        app: myapp-pod
    spec:
      containers:
      - name: myapp
        image: ikubernetes/myapp:v5
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: myappdata
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:                          #动态获取pvc
  - metadata:
      name: myappdata
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "gluster-dynamic"
      resources:
        requests:
          storage: 2Gi
```  

1、tatefulSet示例
```
# cat statefulset.yaml 
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: http
  clusterIP: None
  selector:
    app: nginx
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  selector:
    matchLabels:
      app: nginx # has to match .spec.template.metadata.labels
  serviceName: "nginx"
  replicas: 3 # by default is 1
  template:
    metadata:
      labels:
        app: nginx # has to match .spec.selector.matchLabels
    spec:
      terminationGracePeriodSeconds: 10   # 默认30秒
      containers:
      - name: nginx
        image: registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
        ports:
        - containerPort: 80
          name: http
```

2、启动StatefulSet和Service，并查看状态
```
# kubectl apply -f statefulset.yaml 
service/nginx created
statefulset.apps/web created

# kubectl get service -o wide
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE   SELECTOR
kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   17d   <none>
nginx        ClusterIP   None         <none>        80/TCP    87s   app=nginx

# kubectl get statefulset -o wide
NAME   READY   AGE   CONTAINERS   IMAGES
web    3/3     15m   nginx        registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17

# kubectl get pod -o wide
NAME    READY   STATUS    RESTARTS   AGE   IP             NODE         NOMINATED NODE   READINESS GATES
web-0   1/1     Running   0          16m   10.244.2.95    k8s-node02   <none>           <none>
web-1   1/1     Running   0          16m   10.244.3.103   k8s-node01   <none>           <none>
web-2   1/1     Running   0          16m   10.244.3.104   k8s-node01   <none>           <none>
```
由上可见，StatefulSet 中的pod是有序的。有N个副本，那么序列号为0~(N-1)。

3、查看StatefulSet相关的域名信息
```
# cat myapp_demo.yaml 
apiVersion: v1
kind: Pod
metadata:
  name: myapp-demo
  namespace: default
  labels:
    k8s-app: myapp
spec:
  containers:
  - name: myapp
    image: registry.cn-beijing.aliyuncs.com/google_registry/myapp:v1
    imagePullPolicy: IfNotPresent
    ports:
    - name: httpd
      containerPort: 80
      protocol: TCP

# kubectl apply -f myapp_demo.yaml
pod/myapp-demo created

# kubectl get pod -o wide | grep 'myapp'
myapp-demo   1/1     Running   0          3m24s   10.244.2.101   k8s-node02   <none>           <none>
```

4、进入pod并查看StatefulSet域名信息
```
# 进入一个k8s管理的myapp镜像容器。
# kubectl exec -it myapp-demo sh

/ # nslookup 10.244.2.95
nslookup: can't resolve '(null)': Name does not resolve

Name:      10.244.2.95
Address 1: 10.244.2.95 web-0.nginx.default.svc.cluster.local


/ # nslookup 10.244.3.103
nslookup: can't resolve '(null)': Name does not resolve

Name:      10.244.3.103
Address 1: 10.244.3.103 web-1.nginx.default.svc.cluster.local


/ # nslookup 10.244.3.104
nslookup: can't resolve '(null)': Name does not resolve

Name:      10.244.3.104
Address 1: 10.244.3.104 web-2.nginx.default.svc.cluster.local


##### nginx.default.svc.cluster.local   为service的域名信息
/ # nslookup nginx.default.svc.cluster.local
nslookup: can't resolve '(null)': Name does not resolve

Name:      nginx.default.svc.cluster.local
Address 1: 10.244.3.104 web-2.nginx.default.svc.cluster.local
Address 2: 10.244.3.103 web-1.nginx.default.svc.cluster.local
Address 3: 10.244.2.95 web-0.nginx.default.svc.cluster.local
```

StatefulSet网络标识与PVC

有上文可得如下信息：
- 1、匹配StatefulSet的Pod name(网络标识)的模式为：$(statefulset名称)-$(序号)，比如StatefulSet名称为web，副本数为3。则为：web-0、web-1、web-2
- 2、StatefulSet为每个Pod副本创建了一个DNS域名，这个域名的格式为：$(podname).(headless service name)，也就意味着服务之间是通过Pod域名来通信而非Pod IP。当Pod所在Node发生故障时，Pod会被漂移到其他Node上，Pod IP会发生改变，但Pod域名不会变化
- 3、StatefulSet使用Headless服务来控制Pod的域名，这个Headless服务域名的为：$(service name).$(namespace).svc.cluster.local，其中 cluster.local 指定的集群的域名
- 4、根据volumeClaimTemplates，为每个Pod创建一个PVC，PVC的命令规则为：$(volumeClaimTemplates name)-$(pod name)，比如volumeClaimTemplates为www，pod name为web-0、web-1、web-2；那么创建出来的PVC为：www-web-0、www-web-1、www-web-2
- 5、删除Pod不会删除对应的PVC，手动删除PVC将自动释放PV。

