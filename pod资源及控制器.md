Pod对象
---
- apiVersion: api版本。
- kind: 编排对象，pod、Deployment、StatefulSet、DaemonSet、Service、Ingress等。
- metadata: 元数据，name、namespace、labels、annotations等。
  - labels: 一个API对象通过标签来选择另一个API对象
  - annotations: 是给Kubernetes看的，告诉Kubernetes开启某些功能
- spec: 用来描述这个API对象的期望状态。
- status: Pod的实际运行状态。


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

DaemonSet控制器  
---
```
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: filebeat-ds
  labels:
    app: filebeat
spec:
  selector:
    matchLabels:
      app: filebeat
  updateStrategy:
    rollingUpdate:
      maxUnavailable: 1
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: filebeat
      name: filebeat
    spec:
      containers:
      - name: filebeat
        image: ikubernetes/filebeat:5.6.5-alpine
        env:
        - name: REDIS_HOST
          value: db.ikubernetes.io:6379
        - name: LOG_LEVEL
          value: info
```  

job控制器  
---
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


CronJob控制器  
---
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

statefulset
---
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



