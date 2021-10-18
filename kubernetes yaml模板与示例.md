

> Kubernetes资源的创建、更新、删除等操作时均可以使用json或yaml文件进行操作，更新和删除可以依赖之前的文件进行更改，但是创建资源清单文件就没那么容易了，k8s的配置项实在太多，稍微不注意就会犯错。要写好一个yaml文件，你需要了解yaml的语法，需要掌握k8s的各种配置，对于一个k8s的初学者而言，这将是一件很难的事情。本文按照k8s资源分类，详细列出各个资源的yaml字段与格式，供大家学习和使用。

# 一、pod

> 实际生产环境中很少直接创建pod资源，基本都是通过资源控制器对pod进行管理。

- yaml模板：
```
apiVersion: v1      #必填，版本号
kind: Pod     #必填，资源类型
metadata:       #必填，元数据
  name: <name>-Depolyment     #必填，资源名称
  namespace: <namespace>    #Pod所属的命名空间
  labels:      #自定义标签
  - key: <value>     #自定义标签名字<key: value>
  annotations:        #自定义注解列表  
  - name: <string>        #自定义注解名字  
spec:         #必填，部署的详细定义
  containers:      #必填，定义容器列表
  - name: <name>     #必填，容器名称
    image: <image-name>    #必填，容器的镜像名称
    imagePullPolicy: [Always | Never | IfNotPresent] #获取镜像的策略 Alawys表示下载镜像 IfnotPresent表示优先使用本地镜像，否则下载镜像，Nerver表示仅使用本地镜像
    command: [array]    #容器的启动命令列表，如不指定，使用打包时使用的启动命令
    args: [string]     #容器的启动命令参数列表
    workingDir: string     #选填，容器的工作目录
    env:       #容器运行前需设置的环境变量列表
    - name: string     #环境变量名称
      value: string    #环境变量的值
    ports:       #需要暴露的端口库号列表
    - name: string     #端口号名称
      containerPort: int   #容器需要监听的端口号
      hostPort: int    #容器所在主机需要监听的端口号，默认与Container相同
      protocol: string     #端口协议，支持TCP和UDP，默认TCP
    resources:       #建议填写，资源限制和请求的设置
      limits:      #资源限制的设置
        cpu: string    #Cpu的限制，单位为core数，将用于docker run --cpu-shares参数
        memory: string     #内存限制，单位可以为Mib/Gib，将用于docker run --memory参数
      requests:      #资源请求的设置
        cpu: string    #Cpu请求，容器启动的初始可用数量
        memory: string     #内存请求，容器启动的初始可用数量
    volumeMounts:    #挂载到容器内部的存储卷配置
    - name: string     #引用pod定义的共享存储卷的名称，需用volumes[]部分定义的的卷名
      mountPath: string    #存储卷在容器内mount的绝对路径，应少于512字符
      readOnly: boolean    #是否为只读模式
    livenessProbe:     #建议填写，对Pod内个容器健康检查的设置，当探测无响应几次后将自动重启该容器，检查方法有exec、httpGet和tcpSocket，对一个容器只需设置其中一种方法即可
      exec:      #对Pod容器内检查方式设置为exec方式
        command: [string]  #exec方式需要制定的命令或脚本
      httpGet:       #对Pod内个容器健康检查方法设置为HttpGet，需要制定Path、port
        path: string
        port: number
        host: string
        scheme: string
        HttpHeaders:
        - name: string
          value: string
      tcpSocket:     #对Pod内个容器健康检查方式设置为tcpSocket方式
        port: number
      initialDelaySeconds: 0  #容器启动完成后首次探测的时间，单位为秒
      timeoutSeconds: 0   #对容器健康检查探测等待响应的超时时间，单位秒，默认1秒
      periodSeconds: 0    #对容器监控检查的定期探测时间设置，单位秒，默认10秒一次
      successThreshold: 0 #处于失败状态时，探测操作至少连续多少次的成功才被认为是通过检测，显示为#success属性，默认值为1
      failureThreshold: 0 #处于成功状态时，探测操作至少连续多少次的失败才被视为是检测不通过，显示为#failure属性，默认值为3
    imagePullSecrets:    #Pull镜像时使用的secret名称，以key：secretkey格式指定
    - name: string
    hostNetwork: false      #是否使用主机网络模式，默认为false，如果设置为true，表示使用宿主机网络
  volumes:       #在该pod上定义共享存储卷列表
  - name: string     #共享存储卷名称 （volumes类型有很多种）
    emptyDir: {}     #类型为emtyDir的存储卷，与Pod同生命周期的一个临时目录。为空值
    hostPath: string     #类型为hostPath的存储卷，表示挂载Pod所在宿主机的目录
    path: string     #Pod所在宿主机的目录，将被用于同期中mount的目录
  - name: string     #共享存储卷名称
    secret:      #类型为secret的存储卷，挂载集群与定义的secre对象到容器内部
      scretname: string  
      items:     
      - key: string     #选择secrets定义的某个key
        path: string    #文件内容路径
  - name: string     #共享存储卷名称
    configMap:     #类型为configMap的存储卷，挂载预定义的configMap对象到容器内部
      name: string
      items:
      - key: string     #选择configmap定义的某个key
        path: string     #文件内容路径
  - name: string     #共享存储卷名称
    persistentVolumeClaim:
      claimName: string     #类型为PVC的持久化存储卷
  affinity: # 亲和调度
    nodeAffinity: # 节点亲和调度
      requiredDuringSchedulingIgnoredDuringExecution: #硬亲和调度 或preferredDuringSchedulingIgnoredDuringExecution 软亲和调度
        nodeSelectorTerms: # 选择条件
          - matchExpressions: # 匹配规则
              - key: key
                operator: In
                values:
                  - values
  nodeSelector:  #设置NodeSelector表示将该Pod调度到包含这个label的node上
    name: string     #自定义标签名字<key: value>
  restartPolicy: [Always | Never | OnFailure] #Pod的重启策略，Always表示一旦不管以何种方式终止运行，kubelet都将重启，OnFailure表示只有Pod以非0退出码退出才重启，Nerver表示不再重启该Pod
```

- yaml示例：此处以最简单的busybox举例，添加容器启动命令参数
```
apiVersion: v1
kind: Pod
metadata:
  name: busybox-pod
  namespace: test
  labels:
    name: busybox-pod
spec:
  containers: 
  - name: busybox
    image: busybox:latest
    imagePullPolicy: IfNotPresent
    command: ["/bin/sh","-c","while true;do echo hello;sleep 1;done"]
  restartPolicy: Always
```

# 二、资源控制器

## 1. Deployment

- yaml模板
```
apiVersion: apps/v1      #必填，版本号
kind: Depolyment     #必填，资源类型
metadata:       #必填，元数据
  name: <name>-deploy     #必填，资源名称
  namespace: <namespace>    #Pod所属的命名空间
  labels:      #自定义标签
    - name: string     #自定义标签名字<key: value>
spec:         #必填，部署的详细定义
  selector: #必填，标签选择
    matchLabels: #必填，标签匹配
      name: <name> #必填，通过此标签匹配对应pod<key: value>
  replicas: <number> #必填，副本数量
  minReadySeconds: int #新创建的Pod状态为Ready持续的时间
  revisionHistoryLimit: int #保留的历史版本个数，默认是10
  minAvailable: int #Pod自愿中断的场景中，至少要保证可用的Pod对象数量或比例，要阻止任何Pod对象发生自愿中断，可将其设置为100%。
  maxUnavailable: int #Pod自愿中断的场景中，最多可转换为不可用状态的Pod对象数量或比例，0值意味着不允许Pod对象进行自愿中断；此字段与minAvailable互斥
  strategy: #版本更新控制
    type: RollingUpdate #更新策略，滚动更新（也可以是Recreate 重建更新）
    rollingUpdate: #滚动更新配置
      maxSurge: int #升级期间存在的总Pod对象数量最多不超过多少（百分比）
      maxUnavailable: int #升级期间正常可用的Pod副本数（包括新旧版本）不低于多少（百分比）
  template: #必填，应用容器模版定义
    metadata: 
      labels: 
        name: <name> #必填，与上面matchLabels的标签相同
    spec: 
      containers: #此处参考pod的containers
```

- yaml示例：以grafana alert举例。指定容器监听端口，配置存活就绪检测，设置资源限制，挂载宿主机本机目录存储，

> 建议生产环境为资源添加limit和liveness
```
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: test
  name: grafana-alert-deploy
  labels:
    name: grafana-alert-deploy
spec:
  replicas: 2
  selector:
    matchLabels:
      name: grafanaAlert
  template:
    metadata:
      labels:
        name: grafanaAlert
    spec:
      containers:
      - name: grafana-alert
        image: grafana_alert:cm_v2
        imagePullPolicy: IfNotPresent
        command: ["python3.8","-u","-m","flask","run","-h","0.0.0.0","-p","9999"]
        ports:
        - containerPort: 9999
          protocol: TCP
        volumeMounts:
        - name: grafana-alert-log
          mountPath: /opt/grafanaAlert/log
        readinessProbe:
          tcpSocket: 
            port: 9999
        livenessProbe:
          tcpSocket: 
            port: 9999
        resources:    
          limits:   
            cpu: 1
            memory: 100Mi
          requests:     
            cpu: 100m
            memory: 10Mi
      volumes:
      - name: grafana-alert-log
        hostPath:
          path: /var/log/grafana-alert
          type: Directory
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: role
                    operator: In
                    values:
                      - removable
      dnsPolicy: ClusterFirst
      restartPolicy: Always
```

## 2. DaemonSet

> DaemonSet除了不用设置replicas，其他的与Deployment一致

- yaml模板
```
apiVersion: apps/v1      #必填，版本号
kind: DaemonSet     #必填，资源类型
metadata:       #必填，元数据
  name: <name>-ds     #必填，资源名称
  namespace: <namespace>    #Pod所属的命名空间
  labels:      #自定义标签
    - name: string     #自定义标签名字<key: value>
spec:         #必填，部署的详细定义
  selector: #必填，标签选择
    matchLabels: #必填，标签匹配
      name: <name> #必填，通过此标签匹配对应pod<key: value>
  template: #必填，应用容器模版定义
    metadata: 
      labels: 
        name: <name> #必填，与上面matchLabels的标签相同
    spec: 
      containers: #此处参考pod的containers
```

- yaml示例：监控组件node-exporter部署示例
```
apiVersion: apps/v1
kind: DaemonSet
metadata:
  labels:
    app: node-exporter-ds
  name: node-exporter-ds
  namespace: test
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      containers:
      - args:
        - --web.listen-address=127.0.0.1:9100
        - --path.procfs=/host/proc
        - --path.sysfs=/host/sys
        - --path.rootfs=/host/root
        - --collector.filesystem.ignored-mount-points=^/(dev|proc|sys|var/lib/docker/.+)($|/)
        - --collector.filesystem.ignored-fs-types=^(autofs|binfmt_misc|cgroup|configfs|debugfs|devpts|devtmpfs|fusectl|hugetlbfs|mqueue|overlay|proc|procfs|pstore|rpc_pipefs|securityfs|sysfs|tracefs)$
        image: prometheus/node-exporter:v0.18.1
        name: node-exporter
        resources:
          limits:
            cpu: 250m
            memory: 180Mi
          requests:
            cpu: 102m
            memory: 180Mi
        volumeMounts:
        - mountPath: /host/proc
          name: proc
          readOnly: false
        - mountPath: /host/sys
          name: sys
          readOnly: false
        - mountPath: /host/root
          mountPropagation: HostToContainer
          name: root
          readOnly: true
      - args:
        - --logtostderr
        - --secure-listen-address=$(IP):9100
        - --tls-cipher-suites=TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,TLS_RSA_WITH_AES_128_CBC_SHA256,TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256,TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256
        - --upstream=http://127.0.0.1:9100/
        env:
        - name: IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        image: 172.16.140.21/prometheus/kube-rbac-proxy:v0.4.1
        name: kube-rbac-proxy
        ports:
        - containerPort: 9100
          hostPort: 9100
          name: https
        resources:
          limits:
            cpu: 20m
            memory: 60Mi
          requests:
            cpu: 10m
            memory: 20Mi
      hostNetwork: true
      hostPID: true
      nodeSelector:
        kubernetes.io/os: linux
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
      serviceAccountName: node-exporter
      tolerations:
      - operator: Exists
      volumes:
      - hostPath:
          path: /proc
        name: proc
      - hostPath:
          path: /sys
        name: sys
      - hostPath:
          path: /
        name: root
```

## 3. Job

- yaml模板
```
apiVersion: batch/v1  #必填，版本号
kind: Job # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-job # 必填，资源名称
  namespace: test # pod所属的命名空间
  labels: # 自定义标签
    name: string #自定义标签名字<key: value>
spec: # 必填，部署的详细定义
  completions: int # 资源重复作业数，默认值: 1	
  parallelism: int # 资源并行作业数，默认值: 1
  backoffLimit: int # 资源失败重试次数，默认值：6
  activeDeadlineSecond: int # 资源作业超时时间，默认0 永不超时
  ttlSecondsAfterFinished: int # 任务执行完，多少秒自动删除，默认300
  template: # 必填，应用容器模板定义
    spec:
      containers: #此处参考pod的containers
      - name: busybox
        image: busybox:latest
        imagePullPolicy: IfNotPresent
        command: ["echo", "hello world"]
      restartPolicy: Never # job类型资源重启策略必须为Never或者OnFailure
```

- yaml示例：以busybox镜像启动，输出hello world举例。记得将重启策略设置为Never或者OnFailure
```
apiVersion: batch/v1
kind: Job
metadata:
  name: hello-job
  namespace: test
  labels:
    name: hello-job
spec:
  template:
    spec:
      containers: 
      - name: busybox
        image: busybox:latest
        imagePullPolicy: IfNotPresent
        command: ["echo", "hello world"]
      restartPolicy: Never
```

## 4. CronJob

- yaml模板
```
apiVersion: batch/v1  #必填，版本号
kind: Job # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-cj # 必填，资源名称
  namespace: test # pod所属的命名空间
  labels: # 自定义标签
    name: string #自定义标签名字<key: value>
spec: # 必填，部署的详细定义
  schedule: "* * * * *" # 必填，运行时间点
  concurrencyPolicy: [Allow 允许|Forbid 禁止|Replace 替换] # 并发执行策略，默认允许
  failedJobHistoryLimit: int # 为失败的任务执行保留的历史记录数，默认为1
  successfulJobsHistoryLimit: int # 为成功的任务执行保留的历史记录数，默认为3。
  startingDeadlineSeconds: int # 因各种原因缺乏执行作业的时间点所导致的启动作业错误的超时时长，会被记入错误历史记录。
  suspend: boolean # 是否挂起后续的任务执行，默认为false，对运行中的作业不会产生影响。
  jobTemplate: # 控制器模板，与template类似
    metedata:
      labels: # 自定义标签
        name: string #自定义标签名字<key: value>
    spec:
      template: # 必填，应用容器模板定义
        spec:
          containers: #此处参考pod的containers
          - name: busybox
            image: busybox:latest
            imagePullPolicy: IfNotPresent
            command: ["echo", "hello world"]
          restartPolicy: Never # job类型资源重启策略必须为Never或者OnFailure
```

- yaml示例：以busybox镜像启动，输出hello world举例。记得将重启策略设置为Never或者OnFailure
```
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: hello-cj
  namespace: test
  labels:
    app: hello-cronjob
spec:
  schedule: "*/2 * * * *"
  jobTemplate:
    metadata:
      labels:
        app: hello-cronjob
    spec:
      template:
        spec:
          containers: 
          - name: busybox
            image: busybox:latest
            imagePullPolicy: IfNotPresent
            command: ["echo", "hello world"]
          restartPolicy: Never
```

## 5. StatefulSet

> 创建StatefulSet资源之前，先要保证集群中存在StorageClass，并使用headless service暴露服务
> StatefulSet相较于Deployment，多了volumeClaimTemplates字段，即pvc存储的配置信息

- yaml模板
```
apiVersion: apps/v1      #必填，版本号
kind: StatefulSet     #必填，资源类型
metadata:       #必填，元数据
  name: <name>-sts     #必填，资源名称
  namespace: <namespace>    #Pod所属的命名空间
spec:         #必填，部署的详细定义
  selector: #必填，标签选择
    matchLabels: #必填，标签匹配
      key: <value> #必填，通过此标签匹配对应pod<key: value>
  serviceName: string # Headless Service资源名称
  replicas: int # 副本数量
  template: #必填，应用容器模版定义
    metadata: #必填，元数据
      labels:  # 标签
        key: <value> #必填，与上面matchLabels的标签相同
    spec: 
      containers: #此处参考pod的containers
  volumeClaimTemplates: #必填，+pvc模板
    - metadata:       #必填，元数据
        name: <name>-depolyment     #必填，资源名称
      spec:
        accessModes: [ "ReadWriteOnce | ReadOnlyMany | ReadWriteMany" ] #必填，访问模式
        storageClassName: strint  #存储类名，改为集群中已存在的
        resources: # 存储卷需要占用的资源量最小值
          requests: # 请求空间大小
            storage: 1Gi # 空间大小值
```

- yaml示例：以nginx服务使用nfs共享存储为例
```
#先定义了一个名为myapp-svc的Headless Service资源，用于为关联到的每个Pod资源创建DNS资源记录。
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
  clusterIP: None
  selector:
    app: myapp-pod

---
# 定义多个使用NFS存储后端的PV，空间大小为2GB，仅支持单路的读写操作。
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  storageClassName: nfs
  nfs:
    path: /nfs/data1
    server: 172.17.0.2
---
# 定义了一个名为myapp的StatefulSet资源，它通过Pod模板创建了两个Pod资源副本，并基于volumeClaimTemplates（存储卷申请模板）向nfs存储类请求动态供给PV，从而为每个Pod资源提供大小为1GB的专用存储卷。
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: myapp-sts
spec:
  selector:
    matchLabels:
      app: myapp-pod
  serviceName: myapp-svc
  replicas: 2
  template:
    metadata:
      labels:
        app: myapp-pod
    spec:
      containers:
      - name: nginx
        image: k8s.gcr.io/nginx-slim:0.8
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: myapp-data
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: myapp-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "nfs"
      resources:
        requests:
          storage: 1Gi
```
# 三、服务与暴露

## 1. Service-ClusterIP

- yaml模板
```
apiVersion: v1 # 必填，版本号
kind: Service # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-svc # 必填，资源名称
  namespace: test # 资源命名空间
spec: # 必填，资源详细定义
  type: ClusterIP # 资源类型，默认ClusterIP
  selector: # 必填，标签选择
    key: <value> # 必填，通过此标签匹配对应的资源
  ports: # 必填，服务暴露端端口列表
  - name: string # 服务暴露名称
    port: int # 必填，服务监听端口号
    targetPort: int # 必填，服务转发后端Pod端口号
    protocol: [TCP | UDP] # 端口协议
  sessionAffinity: [None | ClientIP] # 要使用的粘性会话的类型,默认none不使用。ClientIP：基于客户端IP地址识别客户端身份，把来自同一个源IP地址的请求始终调度至同一个Pod对象。
  sessionAffinityConfig: int # 会话保持的时长
```

- yaml示例：使用ClusterIP方式，将myapp的80端口暴露出去
```
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
  namespace: test
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - name: http
    port: 80
    targetPort: 80
```

## 2. Service-NodePort

- yaml模板
```
apiVersion: v1 # 必填，版本号
kind: Service # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-svc # 必填，资源名称
  namespace: test # 资源命名空间
spec: # 必填，资源详细定义
  type: NodePort # 必填，资源类型
  selector: # 必填，标签选择
    key: <value> # 必填，通过此标签匹配对应的资源
  ports: # 必填，服务暴露端端口列表
  - name: string # 服务暴露名称
    port: int # 必填，服务监听端口号
    targetPort: int # 必填，服务转发后端Pod端口号
    nodePort: int 必填，指定映射物理机端口号
    protocol: [TCP | UDP] # 端口协议
  sessionAffinity: [None | ClientIP] # 要使用的粘性会话的类型,默认none不使用。ClientIP：基于客户端IP地址识别客户端身份，把来自同一个源IP地址的请求始终调度至同一个Pod对象。
  sessionAffinityConfig: int # 会话保持的时长
```

- yaml示例：使用NodePort方式，将myapp的80端口映射到物理机30001端口
```
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
  namespace: test
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
  - name: http
    port: 80
    targetPort: 80
    nodePort: 30001
```

## 3. Service-headless

- yaml模板
```
apiVersion: v1 # 必填，版本号
kind: Service # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-svc # 必填，资源名称
  namespace: test # 资源命名空间
spec: # 必填，资源详细定义
  clusterIP: None # 必填，指定clusterIp为none，使用headless
  selector: # 必填，标签选择
    key: <value> # 必填，通过此标签匹配对应的资源
  ports: # 必填，服务暴露端端口列表
  - name: string # 服务暴露名称
    port: int # 必填，服务监听端口号
    targetPort: int # 必填，服务转发后端Pod端口号
    protocol: [TCP | UDP] # 端口协议
  sessionAffinity: [None | ClientIP] # 要使用的粘性会话的类型,默认none不使用。ClientIP：基于客户端IP地址识别客户端身份，把来自同一个源IP地址的请求始终调度至同一个Pod对象。
  sessionAffinityConfig: int # 会话保持的时长
```

- yaml示例：使用headless方式，将myapp的80端口服务暴露出去
```
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
  namespace: test
spec:
  clusterIP: None
  selector:
    app: myapp
  ports:
  - name: http
    port: 80
    targetPort: 80
```

## 4. Ingress（nginx）

- yaml模板
```
aVersion: networking.k8s.io/v1 # 必填，版本号
kind: Ingress # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-ingress # 必填，资源名称
  labels: # 自定义标签
    name: string #自定义标签名字<key: value>
spec: # 必填，资源详细定义
  tls: # tls配置
  - hosts:
    - myapp.test.com #访问地址
    secretName: string # tls证书名称
  rules: # 定义当前Infress资源转发规则列表
  - host: myapp.test.com
    http:
      paths:
      - pathType: Prefix # 指定应如何匹配Ingress路径
        path: "/" # 转发路径
        backend: # 转发后端
          service:
            name: string # 转发后端名称
            port: 
              number: int # 转发后端端口
```

- yaml示例：将myapp-svc服务配置为域名myapp.test.com，并添加tls配置
```
aVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  labels:
    name: myapp-ingress
spec:
  tls:
  - hosts:
    - myapp.test.com
    secretName: myapp-tls-secret
  rules:
  - host: myapp.test.com
    http:
      paths:
      - pathType: Prefix
        path: "/"
        backend:
          service:
            name: myapp-svc
            port: 
              number: 80
```

## 5. IngressRouter（traefik）

> 在traefik v1版本中，默认使用的都是ingress，在v2版本中，引入了Ingress route的概念，他们实际的作用都是一样的，写法上略有不同，实际上，ingress并不是traefik或者nginx定义的一个概念，是k8s定义的，但是traefik也用的是ingress这个概念，所以可以看到网上的大部分文档，在v1版本的时候使用ingress指定规则的话，需要在metadata字段指定注释即表明此ingress使用的是traefik控制器，在v2版本中，也可以使用ingress，但是需要在配置文件中的provider字段添加kubernetesIngress: “”
> 此处以traefik v2 IngressRouter为例

- yaml模板
```
apiVersion: traefik.containo.us/v1alpha1 # 必填，版本号
kind: IngressRoute # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-ingress-tls # 必填，资源名称
  namespace: string # 资源命名空间
spec: # 必填，资源详细定义
  routes: # 定义当前Ingress资源的转发规则列表
  - kind: Rule # 必填，规则类型
    match: string # 必填，规则匹配表达式
    services: # 必填，转发配置
    - name: string # 必填，转发后端目标
      port: int # 必填，转发后端端口
    middlewares: # 中间件配置（如BasicAuth）
  tls: # tls证书配置
    options: # 配置选项
      name: string # 配置选项名称
      namespace: string # 配置选项命名空间
    secretName: string # tls证书名称
```

- yaml示例：将grafana-svc服务配置为域名grafana.test.com，并添加tls配置
```
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: grafana-ingress-tls
  namespace: grafana
spec:
  routes:
  - kind: Rule
    match: Host(`grafana.test.com`)
    services:
    - name: grafana-svc
      port: 3000
  tls:
    options:
      name: https-tlsoption
      namespace: default
    secretName: grafana-ingress-tls
```

# 四、存储

## 1. PersistentVolume

- yaml模板
```
apiVersion: v1 # 必填，版本号
kind: PersistentVolume # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-pv # 必填，资源名称
  labels: # 资源标签
    key: value #资源标签键值对 
spec: # 必填，资源详细定义
  capacity: # 必填，当前PV的容量
    storage: <int>Gi # 必填，pv容量大小值，单位Ki，Mi，Gi
  accessModes: # 必填，访问模式
    - ReadWriteMany # ReadWriteOnce 仅可被单个节点读写挂载，ReadOnlyMany 可被多个节点同时只读挂载，ReadWriteMany 可被多个节点同时读写挂载
  persistentVolumeReclaimPolicy: Recycle # 必填，PV空间被释放时的处理机制。Retain：保持不动，由管理员随后手动回收。Recycle：空间回收，即删除存储卷目录下的所有文件（包括子目录和隐藏文件）。Delete：删除存储卷，仅部分云端存储系统支持
  storageClassName: string # 当前PV所属的StorageClass的名称；默认为空值，即不属于任何StorageClass。
  mountOptions: # 挂载选项组成的列表
    - hard
    - nfsvers=4.1
  nfs:
    path: path # nfs共享目录
    server: XXX.XXX.XXX.XXX # nfs服务器地址
  volumeMode: Filesystem # 卷模型，用于指定此卷可被用作文件系统还是裸格式的块设备；默认为Filesystem。
```

- yaml示例：一个使用NFS存储后端的PV，空间大小为5GB，支持多路的读写操作。
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
  labels:
    release: stable
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Recycle
  storageClassName: nfs
  mountOptions:
    - hard
    - nfsvers=4.1
  nfs:
    path: /nfs
    server: 172.17.0.2
```

## 2. PersistentVolumeClaim

- yaml模板
```
apiVersion: v1 # 必填，版本号
kind: PersistentVolumeClaim # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-pvc # 必填，资源名称
  namespace: test # 资源命名空间
spec: # 必填，资源详细定义
  accessModes: # 必填，访问模式
    - ReadWriteMany # ReadWriteOnce 仅可被单个节点读写挂载，ReadOnlyMany 可被多个节点同时只读挂载，ReadWriteMany 可被多个节点同时读写挂载
  storageClassName: string # 必填，所依赖的存储类的名称。
  volumeMode: Filesystem # 卷模型，用于指定此卷可被用作文件系统还是裸格式的块设备；默认为Filesystem。
  resources: # 必填，当前PVC存储卷需要占用的资源量最小值 
    requests: # 必填，pvc请求空间大小
      storage: 5Gi # 必填，空间大小值如1Gi
  selector: # 绑定时对PV应用的标签选择器，用于挑选要绑定的PV
    matchLabels: # 标签选择器
      release: stable # key-value标签
```

 - yaml示例：一个使用NFS存储后端的PVC，绑定release为stable且storageClassName为nfs的pv
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
  namespace: test
spec:
  resources:
    requests:
      storage: 5Gi
  storageClassName: nfs
  accessModes:
    - ReadWriteOnce
  selector:
    matchLabels:
      release: stable
```

## 3. StorageClass

> 创建StorageClass之前，先要在集群创建ClusterRole、RoleBinding和ClusterRoleBinding

- yaml模板
```
apiVersion: storage.k8s.io/v1 # 必填，版本号
kind: StorageClass # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-sc # 必填，资源名称
provisioner: string # 必填，这里的名称要和provisioner配置文件中的环境变量PROVISIONER_NAME保持一致
parameters: # 存储类参数
```

- yaml示例：以nfs共享存储为例
```
apiVersion: storage.k8s.io/v1 
kind: StorageClass
metadata:
  name: nfs-sc
provisioner: nfs-storage
parameters:
  archiveOnDelete: "false"
```

# 五、配置信息

## 1. ConfigMap

- yaml模板
```
apiVersion: v1 # 必填，版本号
kind: ConfigMap # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-cm # 必填，资源名称
  namespace: string # 资源命名空间
data: # 必填，保存的数据信息
  key: value # 数据信息
```

- yaml示例：创建configmap，保存两组信息：log_level为INFO，log_file为/var/log/test.log
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-cm
  namespace: test
data:
  log_level: INFO
  log_file: /var/log/test.log
```

## 2. Secret

- yaml模板
```
apiVersion: v1 # 必填，版本号
kind: Secret # 必填，资源类型
metadata: # 必填，元数据
  name: <name>-cm # 必填，资源名称
  namespace: string # 资源命名空间
type: Opaque # 必填，secret数据类型标识。Opaque：base64 编码格式的 Secret，用来存储密码、密钥等。kubernetes.io/dockerconfigjson：用来存储私有docker registry的认证信息。kubernetes.io/service-account-token：用于被serviceaccount引用，serviceaccout 创建时Kubernetes会默认创建对应的secret
data: # 必填，保存的数据信息
  key: value # 数据信息
```

- yaml示例：创建configmap，保存两组信息：log_level为INFO，log_file为/var/log/test.log
```
apiVersion: v1
kind: Secret
metadata:
  name: password-secret
type: Opaque
data:
  password: MTIzLmNvbQ==
```
