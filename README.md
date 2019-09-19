官网https://kubernetes.io/zh/docs/concepts/  
https://www.kubernetes.org.cn/k8s  
https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.15/#-strong-api-overview-strong-  
实用中文文档http://docs.kubernetes.org.cn/  
https://v1-14.docs.kubernetes.io/zh/docs/concepts/services-networking/ingress/  
阿里云使用kubernetes  
https://help.aliyun.com/document_detail/86420.html?spm=a2c4g.11186623.6.586.5c791be1iCa4aC  

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

pod生命周期  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod_lifecycle.png)  

pod创建过程  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod.png)  

pod终止过程  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod_kill.png)  

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



ReplicaSet控制器  
---
```
apiVersion: apps/v1
kind: ReplicaSet
metadata:                          #元数据
  name: rs-example                 #副本控制器名字
spec:                              #期望状态
  replicas: 2                      #副本数
  selector:                        #标签选择器
     matchLabels:               
       app: rs-demo                #标签
  template:                        #定义pod
    metadata: 
      labels:
        app: rs-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.12-alpine
        ports:
        - name: http
          containerPort: 80
```


Deployment控制器  
---
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deploy-nginx
spec:
  replicas: 3                            #副本数
  minReadySeconds: 10
  strategy:                              #定义更新策略      
    rollingUpdate:                       #滚动更新策略定义临时减少和增加的pod
      maxSurge: 1                        #最多允许多几个pod
      maxUnavailable: 1                  #最少有几个不可用
    type: RollingUpdate                  #更新策略
  selector:                              #标签选择器
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.10-alpine
        ports:
        - containerPort: 80
          name: http
        readinessProbe:
          periodSeconds: 1
          httpGet:
            path: /
            port: http
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

service
---
```
kind: Service
apiVersion: v1
metadata:
  name: myapp-svc-nodeport
spec:
  clusterIP: None                   #配置clusterIP为无头服务,tyep只能为clusterIP生效
  type: NodePort                    #配置svc类型默认为clusterIP
  sessionAffinity: ClientIP         #session绑定默认值为None(不启用)   ClientIP,None   效果不佳，不建议使用
  selector:
    app: myapp                      #对应pod的标签
  ports:
  - protocol: TCP                   #协议，默认tcp
    port: 80                        #server端口
    targetPort: 80                  #pod端口
    nodePort: 32223                 #集群接入，主机端口，范围30000-32767
```
创建service资源会自动创建对应的Endpoints资源对象  
```
获取service信息
# kubectl get svc myapp-svc-nodeport
获取service
# kubectl get endpoints myapp-svc-nodeport
```  
服务解析  
dig -t A myapp-svc.default.svc.cluster.local @10.96.0.10  
svc_name.svc_ns_name.svc.cluster.local

ExternalName资源类型  
通过DNS引入集群外部资源
```
kind: Service
apiVersion: v1
metadata:
  name: external-www-svc
spec:
  type: ExternalName
  externalName: www.kubernetes.io
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
    nodePort: 0
  selector: {}
```  

解析过程svc_name.svc_ns.svc.cluster.local  
```
# dig -t A external-www-svc.default.svc.cluster.local @10.96.0.10

; <<>> DiG 9.9.4-RedHat-9.9.4-73.el7_6 <<>> -t A external-www-svc.default.svc.cluster.local @10.96.0.10
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 48496
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 3, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;external-www-svc.default.svc.cluster.local. IN A

;; ANSWER SECTION:
external-www-svc.default.svc.cluster.local. 5 IN CNAME www.kubernetes.io.
www.kubernetes.io.	5	IN	CNAME	kubernetes.io.
kubernetes.io.		5	IN	A	45.54.44.102

;; Query time: 123 msec
;; SERVER: 10.96.0.10#53(10.96.0.10)
;; WHEN: Thu Mar 21 16:17:31 EDT 2019
;; MSG SIZE  rcvd: 206
```  

statefulset
---
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

解析statefulset的pod IP 地址    
nslookup myapp-0.myapp.default.svc.cluster.local  
pod_name.svc_name.ns_name.svc.cluster.local  


定义Endpoints资源
```
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: default
spec:
  clusterIP: None
  ports:
  - port: 9093
    protocol: TCP
---
kind: Endpoints
apiVersion: v1
metadata:
  name: alertmanager
  namespace: default
subsets:
  - addresses:
      - ip: 10.211.18.5
    ports:
      - port:9093
        protocol: TCP


```  
