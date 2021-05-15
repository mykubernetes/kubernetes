Pod 三种探针简介
---
- LivenessProbe（存活探针） 存活探针主要进入容器检测容器中的应用是否正常运行，如果检测失败，则认为容器不健康，那么 Kubelet 将根据 Pod 中设置的 restartPolicy （重启策略）来判断，Pod 是否要进行重启操作，如果容器配置中没有配置 livenessProbe 存活探针，Kubelet 将认为存活探针探测一直为成功状态。
- ReadinessProbe（就绪探针） 用于判断容器中应用是否启动完成，当探测成功后才使 Pod 对外提供网络访问，设置容器 Ready 状态为 true，如果探测失败，则设置容器的 Ready 状态为 false。对于被 Service 管理的 Pod，Service 与 Pod、EndPoint 的关联关系也将基于 Pod 是否为 Ready 状态进行设置，如果 Pod 运行过程中 Ready 状态变为 false，则系统自动从 Service 关联的 EndPoint 列表中移除，如果 Pod 恢复为 Ready 状态。将再会被加回 Endpoint 列表。通过这种机制就能防止将流量转发到不可用的 Pod 上。
- StartupProbe（启动探针）指示容器中的应用是否已经启动。如果提供了启动探针(startup probe)，则禁用所有其他探针，直到它成功为止。如果启动探针失败，kubelet 将杀死容器，容器服从其重启策略进行重启。如果容器没有提供启动探针，则默认状态为成功Success。


三种探针的区别
---
- ReadinessProbe： 当检测失败后，将 Pod 的 IP:Port 从对应 Service 关联的 EndPoint 地址列表中删除。
- LivenessProbe： 当检测失败后将杀死容器，并根据 Pod 的重启策略来决定作出对应的措施。
- StartupProbe： 当检测失败后将杀死容器，并根据 Pod 的重启策略来决定作出对应的措施。

pod三种健康检查
---
- ExecAction： 在容器中执行指定的命令，如果能成功执行，则探测成功。
- HTTPGetAction： 通过容器的IP地址、端口号及路径调用 HTTP Get 方法，如果响应的状态码 200 ≤ status ≤ 400，则认为容器探测成功。
- TCPSocketAction： 通过容器的 IP 地址和端口号执行 TCP 检查，如果能够建立 TCP 连接，则探测成功。

探针探测结果有以下值：
---
- Success：表示通过检测。
- Failure：表示未通过检测。
- Unknown：表示检测没有正常进行。

Pod 探针的相关属性
---
- initialDelaySeconds： Pod 启动后首次进行检查的等待时间，单位“秒”。
- periodSeconds： 检查的间隔时间，默认为 10s，单位“秒”。
- timeoutSeconds： 探针执行检测请求后，等待响应的超时时间，默认为 1s，单位“秒”。
- successThreshold： 探针检测失败后认为成功的最小连接成功次数，默认为 1s，在 Liveness 探针中必须为 1s，最小值为 1s。
- failureThreshold： 探测失败的重试次数，重试一定次数后将认为失败，在 readiness 探针中，Pod会被标记为未就绪，默认为 3s，最小值为 1s。

一、通过 Exec 方式做健康探测
---
```
apiVersion: v1
kind: Pod
metadata:
  name: liveness-exec
  labels:
    app: liveness
spec:
  containers:
  - name: liveness
    image: busybox
    args:                       #创建测试探针探测的文件
    - /bin/sh
    - -c
    - touch /tmp/healthy; sleep 30; rm -rf /tmp/healthy; sleep 600
    livenessProbe:
      initialDelaySeconds: 10   #延迟检测时间
      periodSeconds: 5          #检测时间间隔
      failureThreshold: 2       #探测失败的重试次数
      successThreshold: 1       #探针检测失败后认为成功的最小连接成功次数
      timeoutSeconds: 5         #探针执行检测请求后，等待响应的超时时间
      exec:
        command:
        - cat
        - /tmp/healthy
```

二、通过 HTTP 方式做健康探测
---
```
apiVersion: v1
kind: Pod
metadata:
  name: liveness-http
  labels:
    test: liveness
spec:
  containers:
  - name: liveness
    image: mydlqclub/springboot-helloworld:0.0.1
    livenessProbe:
      initialDelaySeconds: 20   #延迟加载时间
      periodSeconds: 5          #重试时间间隔
      timeoutSeconds: 10        #超时时间设置
      httpGet:
        scheme: HTTP
        port: 8081
        path: /actuator/health
```
- scheme: 用于测试连接的协议，默认为 HTTP。
- host： 要连接的主机名，默认为 Pod IP。
- port： 容器上要访问端口号或名称。
- path： Http 服务器上的访问 URL。
- httpHeaders： 自定义 Http 请求 Headers，Http 允许重复 Headers。


三、通过 TCP 方式做健康探测
---
```
apiVersion: v1
kind: Pod
metadata:
  name: liveness-tcp
  labels:
    app: liveness
spec:
  containers:
  - name: liveness
    image: nginx
    livenessProbe:
      initialDelaySeconds: 15
      periodSeconds: 20
      tcpSocket:
        port: 80
```

四、ReadinessProbe 探针使用示例
---
1、pod yaml脚本
```
# cat readinessProbe-httpget.yaml 
apiVersion: v1
kind: Pod
metadata:
  name: readiness-httpdget-pod
  namespace: default
  labels:
    test: readiness-httpdget
spec:
  containers:
  - name: readiness-httpget
    image: registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17
    imagePullPolicy: IfNotPresent
    readinessProbe:
      httpGet:
        path: /index1.html
        port: 80
      initialDelaySeconds: 5  #容器启动完成后，kubelet在执行第一次探测前应该等待 5 秒。默认是 0 秒，最小值是 0。
      periodSeconds: 3  #指定 kubelet 每隔 3 秒执行一次存活探测。默认是 10 秒。最小值是 1
```

2、创建 Pod，并查看pod状态
```
# kubectl apply -f readinessProbe-httpget.yaml 
pod/readiness-httpdget-pod created

# kubectl get pod -n default -o wide
NAME                     READY   STATUS    RESTARTS   AGE   IP            NODE         NOMINATED NODE   READINESS GATES
readiness-httpdget-pod   0/1     Running   0          5s    10.244.2.25   k8s-node02   <none>           <none>
```

3、查看pod详情
```
# kubectl describe pod readiness-httpdget-pod
Name:         readiness-httpdget-pod
Namespace:    default
Priority:     0
Node:         k8s-node02/172.16.1.112
Start Time:   Sat, 23 May 2020 16:10:04 +0800
Labels:       test=readiness-httpdget
Annotations:  kubectl.kubernetes.io/last-applied-configuration:
                {"apiVersion":"v1","kind":"Pod","metadata":{"annotations":{},"labels":{"test":"readiness-httpdget"},"name":"readiness-httpdget-pod","names...
Status:       Running
IP:           10.244.2.25
IPs:
  IP:  10.244.2.25
Containers:
  readiness-httpget:
    Container ID:   docker://066d66aaef191b1db08e1b3efba6a9be75378d2fe70e99400fc513b91242089c
………………
    Port:           <none>
    Host Port:      <none>
    State:          Running
      Started:      Sat, 23 May 2020 16:10:05 +0800
    Ready:          False                                       # 状态为False
    Restart Count:  0
    Readiness:      http-get http://:80/index1.html delay=5s timeout=1s period=3s #success=1 #failure=3
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-v48g4 (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             False                                       # 为False
  ContainersReady   False                                       # 为False
  PodScheduled      True 
Volumes:
  default-token-v48g4:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-v48g4
    Optional:    false
QoS Class:       BestEffort
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
Events:
  Type     Reason     Age                From                 Message
  ----     ------     ----               ----                 -------
  Normal   Scheduled  <unknown>          default-scheduler    Successfully assigned default/readiness-httpdget-pod to k8s-node02
  Normal   Pulled     49s                kubelet, k8s-node02  Container image "registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17" already present on machine
  Normal   Created    49s                kubelet, k8s-node02  Created container readiness-httpget
  Normal   Started    49s                kubelet, k8s-node02  Started container readiness-httpget
  Warning  Unhealthy  2s (x15 over 44s)  kubelet, k8s-node02  Readiness probe failed: HTTP probe failed with statuscode: 404
```
由上可见，容器未就绪。

4、我们进入pod的第一个容器，然后创建对应的文件
```
# kubectl exec -it readiness-httpdget-pod -c readiness-httpget bash

root@readiness-httpdget-pod:/# cd /usr/share/nginx/html
root@readiness-httpdget-pod:/usr/share/nginx/html# ls
50x.html  index.html
root@readiness-httpdget-pod:/usr/share/nginx/html# echo "readiness-httpdget info" > index1.html
root@readiness-httpdget-pod:/usr/share/nginx/html# ls
50x.html  index.html  index1.html
```

5、之后看pod状态与详情
```
# kubectl get pod -n default -o wide
NAME                     READY   STATUS    RESTARTS   AGE     IP            NODE         NOMINATED NODE   READINESS GATES
readiness-httpdget-pod   1/1     Running   0          2m30s   10.244.2.25   k8s-node02   <none>           <none>

# kubectl describe pod readiness-httpdget-pod
Name:         readiness-httpdget-pod
Namespace:    default
Priority:     0
Node:         k8s-node02/172.16.1.112
Start Time:   Sat, 23 May 2020 16:10:04 +0800
Labels:       test=readiness-httpdget
Annotations:  kubectl.kubernetes.io/last-applied-configuration:
                {"apiVersion":"v1","kind":"Pod","metadata":{"annotations":{},"labels":{"test":"readiness-httpdget"},"name":"readiness-httpdget-pod","names...
Status:       Running
IP:           10.244.2.25
IPs:
  IP:  10.244.2.25
Containers:
  readiness-httpget:
    Container ID:   docker://066d66aaef191b1db08e1b3efba6a9be75378d2fe70e99400fc513b91242089c
………………
    Port:           <none>
    Host Port:      <none>
    State:          Running
      Started:      Sat, 23 May 2020 16:10:05 +0800
    Ready:          True                                             # 状态为True
    Restart Count:  0
    Readiness:      http-get http://:80/index1.html delay=5s timeout=1s period=3s #success=1 #failure=3
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-v48g4 (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             True                                             # 为True
  ContainersReady   True                                             # 为True
  PodScheduled      True 
Volumes:
  default-token-v48g4:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-v48g4
    Optional:    false
QoS Class:       BestEffort
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
Events:
  Type     Reason     Age                   From                 Message
  ----     ------     ----                  ----                 -------
  Normal   Scheduled  <unknown>             default-scheduler    Successfully assigned default/readiness-httpdget-pod to k8s-node02
  Normal   Pulled     2m33s                 kubelet, k8s-node02  Container image "registry.cn-beijing.aliyuncs.com/google_registry/nginx:1.17" already present on machine
  Normal   Created    2m33s                 kubelet, k8s-node02  Created container readiness-httpget
  Normal   Started    2m33s                 kubelet, k8s-node02  Started container readiness-httpget
  Warning  Unhealthy  85s (x22 over 2m28s)  kubelet, k8s-node02  Readiness probe failed: HTTP probe failed with statuscode: 404
```
由上可见，容器已就绪

五、ReadinessProbe + LivenessProbe 配合使用示例
---
```
apiVersion: v1
kind: Service
metadata:
  name: springboot
  labels:
    app: springboot
spec:
  type: NodePort
  ports:
  - name: server
    port: 8080
    targetPort: 8080
    nodePort: 31180
  - name: management
    port: 8081
    targetPort: 8081
    nodePort: 31181
  selector:
    app: springboot
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: springboot
  labels:
    app: springboot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: springboot
  template:
    metadata:
      name: springboot
      labels:
        app: springboot
    spec:
      containers:
      - name: readiness
        image: mydlqclub/springboot-helloworld:0.0.1
        ports:
        - name: server 
          containerPort: 8080
        - name: management
          containerPort: 8081
        readinessProbe:
          initialDelaySeconds: 20 
          periodSeconds: 5      
          timeoutSeconds: 10        
          httpGet:
            scheme: HTTP
            port: 8081
            path: /actuator/health
        livenessProbe:
          initialDelaySeconds: 30 
          periodSeconds: 10 
          timeoutSeconds: 5 
          httpGet:
            scheme: HTTP
            port: 8081
            path: /actuator/health
```

六、启动检测
---
有时候，会有一些现有的应用程序在启动时需要较多的初始化时间【如：Tomcat服务】。这种情况下，在不影响对触发这种探测的死锁的快速响应的情况下，设置存活探测参数是要有技巧的。

技巧就是使用一个命令来设置启动探测。针对HTTP 或者 TCP 检测，可以通过设置 failureThreshold * periodSeconds 参数来保证有足够长的时间应对糟糕情况下的启动时间。

1、pod yaml文件
```
# cat startupProbe-httpget.yaml
apiVersion: v1
kind: Pod
metadata:
  name: startup-pod
  labels:
    test: startup
spec:
  containers:
  - name: startup
    image: registry.cn-beijing.aliyuncs.com/google_registry/tomcat:7.0.94-jdk8-openjdk
    imagePullPolicy: IfNotPresent
    ports:
    - name: web-port
      containerPort: 8080
      hostPort: 8080
    livenessProbe:
      httpGet:
        path: /index.jsp
        port: web-port
      initialDelaySeconds: 5
      periodSeconds: 10
      failureThreshold: 1
    startupProbe:
      httpGet:
        path: /index.jsp
        port: web-port
      periodSeconds: 10      #指定 kubelet 每隔 10 秒执行一次存活探测。默认是 10 秒。最小值是 1
      failureThreshold: 30   #最大的失败次数
```

2、启动pod，并查看状态
```
# kubectl apply -f startupProbe-httpget.yaml 
pod/startup-pod created

# kubectl get pod -o wide
NAME          READY   STATUS    RESTARTS   AGE     IP            NODE         NOMINATED NODE   READINESS GATES
startup-pod   1/1     Running   0          8m46s   10.244.4.26   k8s-node01   <none>           <none>
```

3、查看pod详情
```
# kubectl describe pod startup-pod
```

有启动探测，应用程序将会有最多 5 分钟(30 * 10 = 300s) 的时间来完成它的启动。一旦启动探测成功一次，存活探测任务就会接管对容器的探测，对容器死锁可以快速响应。 如果启动探测一直没有成功，容器会在 300 秒后被杀死，并且根据 restartPolicy 来设置 Pod 状态。
