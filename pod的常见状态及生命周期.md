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

Lifecycle钩子
---

- postStart 指的是在容器启动后立刻执行一个指定的操作
- preStop 容器被杀死之前。
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
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "echo Hello from the postStart handler > /usr/share/message"]
      preStop:
        exec:
          command: ["/usr/sbin/nginx","-s","quit"]
```
