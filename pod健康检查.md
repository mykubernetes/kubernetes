Pod 两种探针简介
---
- LivenessProbe（存活探针） 存活探针主要作用是，用指定的方式进入容器检测容器中的应用是否正常运行，如果检测失败，则认为容器不健康，那么 Kubelet 将根据 Pod 中设置的 restartPolicy （重启策略）来判断，Pod 是否要进行重启操作，如果容器配置中没有配置 livenessProbe 存活探针，Kubelet 将认为存活探针探测一直为成功状态。
- ReadinessProbe（就绪探针） 用于判断容器中应用是否启动完成，当探测成功后才使 Pod 对外提供网络访问，设置容器 Ready 状态为 true，如果探测失败，则设置容器的 Ready 状态为 false。对于被 Service 管理的 Pod，Service 与 Pod、EndPoint 的关联关系也将基于 Pod 是否为 Ready 状态进行设置，如果 Pod 运行过程中 Ready 状态变为 false，则系统自动从 Service 关联的 EndPoint 列表中移除，如果 Pod 恢复为 Ready 状态。将再会被加回 Endpoint 列表。通过这种机制就能防止将流量转发到不可用的 Pod 上。


两种探针的区别
---
- ReadinessProbe： 当检测失败后，将 Pod 的 IP:Port 从对应 Service 关联的 EndPoint 地址列表中删除。
- LivenessProbe： 当检测失败后将杀死容器，并根据 Pod 的重启策略来决定作出对应的措施。

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
apiVersion: v1
kind: Pod
metadata:
  name: springboot
  labels:
    app: springboot
spec:
  containers:
  - name: springboot
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
```

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
