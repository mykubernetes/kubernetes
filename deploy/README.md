kubeadm安装官方文档  
https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm/

kops安装官方文档  
https://kubernetes.io/docs/setup/production-environment/tools/kops/  
https://github.com/kubernetes/kops

kubespray安装官方文档  
https://kubernetes.io/docs/setup/production-environment/tools/kubespray/  
https://github.com/kubernetes-sigs/kubespray


查看证书时间  
```
openssl x509 -in apiserver.crt -text -noout
```  

必备工具
---
- kubectl：用于查看 Kubernetes 集群以及容器的状态，如 kubectl describe pod <pod-name>
- journalctl：用于查看 Kubernetes 组件日志，如 journalctl -u kubelet -l
- iptables和ebtables：用于排查 Service 是否工作，如 iptables -t nat -nL 查看 kube-proxy 配置的 iptables 规则是否正常
- tcpdump：用于排查容器网络问题，如 tcpdump -nn host 10.240.0.8
- perf：Linux 内核自带的性能分析工具，常用来排查性能问题，如 Container Isolation Gone Wrong 问题的排查

集群异常处理
---
按照不同的组件来说，具体的原因可能包括
- kube-apiserver 无法启动会导致
  - 集群不可访问
  - 已有的 Pod 和服务正常运行（依赖于 Kubernetes API 的除外）
- etcd 集群异常会导致
  - kube-apiserver 无法正常读写集群状态，进而导致 Kubernetes API 访问出错
  -	kubelet 无法周期性更新状态
-	kube-controller-manager/kube-scheduler 异常会导致
  -	复制控制器、节点控制器、云服务控制器等无法工作，从而导致 Deployment、Service 等无法工作，也无法注册新的 Node 到集群中来
  -	新创建的 Pod 无法调度（总是 Pending 状态）
- Node 本身宕机或者 Kubelet 无法启动会导致
  -	Node 上面的 Pod 无法正常运行
  -	已在运行的 Pod 无法正常终止
- 网络分区会导致 Kubelet 等与控制平面通信异常以及 Pod 之间通信异常

查看 Node 状态
---
一般来说，可以首先查看 Node 的状态，确认 Node 本身是不是 Ready 状态
```
kubectl get nodes
kubectl describe node <node-name>
```
如果是 NotReady 状态，则可以执行 kubectl describe node <node-name> 命令来查看当前 Node 的事件。这些事件通常都会有助于排查 Node 发生的问题。

查看日志
---
一般来说，Kubernetes 的主要组件有两种部署方法
- 直接使用 systemd 等启动控制节点的各个服务
- 使用 Static Pod 来管理和启动控制节点的各个服务
使用 systemd 等管理控制节点服务时，查看日志必须要首先 SSH 登录到机器上，然后查看具体的日志文件。如
```
journalctl -l -u kube-apiserver
journalctl -l -u kube-controller-manager
journalctl -l -u kube-scheduler
journalctl -l -u kubelet
journalctl -l -u kube-proxy
journalctl -l -u etcd
journalctl -l -u flanneld
```
或者直接查看日志文件


Pods异常处理
---
一般来说，无论 Pod 处于什么异常状态，都可以执行以下命令来查看 Pod 的状态
- kubectl get pod <pod-name> -o yaml 查看 Pod 的配置是否正确
-	kubectl describe pod <pod-name> 查看 Pod 的事件
-	kubectl logs <pod-name> [-c <container-name>] 查看容器日志
这些事件和日志通常都会有助于排查 Pod 发生的问题。

一、Pod 一直处于 Pending 状态

Pending 说明 Pod 还没有调度到某个 Node 上面。可以通过 kubectl describe pod <pod-name> 命令查看到当前 Pod 的事件，进而判断为什么没有调度。
```
$ kubectl describe pod mypod
...
Events:
  Type     Reason            Age                From               Message
  ----     ------            ----               ----               -------
  Warning  FailedScheduling  12s (x6 over 27s)  default-scheduler  0/4 nodes are available: 2 Insufficient cpu
```

可能的原因包括
- 资源不足，集群内所有的 Node 都不满足该 Pod 请求的 CPU、内存、GPU 或者临时存储空间等资源。解决方法是删除集群内不用的 Pod 或者增加新的 Node。
-	HostPort 端口已被占用，通常推荐使用 Service 对外开放服务端口


二、Pod 一直处于 Waiting 或 ContainerCreating 状态

通过 kubectl describe pod <pod-name> 命令查看到当前 Pod 的事件

可能的原因有以下几种

- 镜像拉取失败，比如
  - 配置了错误的镜像
  - Kubelet 无法访问镜像（国内环境访问 gcr.io 需要特殊处理）
  - 私有镜像的密钥配置错误
  - 镜像太大，拉取超时（可以适当调整 kubelet 的 --image-pull-progress-deadline 和 --runtime-request-timeout 选项）
- CNI 网络错误，一般需要检查 CNI 网络插件的配置，比如
  -	无法配置 Pod 网络
  -	无法分配 IP 地址
-	容器无法启动，需要检查是否打包了正确的镜像或者是否配置了正确的容器参数

三、Pod 处于 ImagePullBackOff 状态

这通常是镜像名称配置错误或者私有镜像的密钥配置错误导致。这种情况可以使用 docker pull <image> 来验证镜像是否可以正常拉取。

如果是私有镜像，需要首先创建一个 docker-registry 类型的 Secret
```
kubectl create secret docker-registry my-secret --docker-server=DOCKER_REGISTRY_SERVER --docker-username=DOCKER_USER --docker-password=DOCKER_PASSWORD --docker-email=DOCKER_EMAIL
```
然后在容器中引用这个 Secret
```
spec:
  containers:
  - name: private-reg-container
    image: <your-private-image>
  imagePullSecrets:
  - name: my-secret
```

四、Pod 一直处于 CrashLoopBackOff 状态

CrashLoopBackOff 状态说明容器曾经启动了，但又异常退出了。此时 Pod 的 RestartCounts 通常是大于 0 的，可以先查看一下容器的日志
```
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl logs --previous <pod-name>
```
这里可以发现一些容器退出的原因，比如
-	容器进程退出
-	健康检查失败退出
-	OOMKilled
```
$ kubectl describe pod mypod
...
Containers:
  sh:
    Container ID:  docker://3f7a2ee0e7e0e16c22090a25f9b6e42b5c06ec049405bc34d3aa183060eb4906
    Image:         alpine
    Image ID:      docker-pullable://alpine@sha256:7b848083f93822dd21b0a2f14a110bd99f6efb4b838d499df6d04a49d0debf8b
    Port:          <none>
    Host Port:     <none>
    State:          Terminated
      Reason:       OOMKilled
      Exit Code:    2
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    2
    Ready:          False
    Restart Count:  3
    Limits:
      cpu:     1
      memory:  1G
    Requests:
      cpu:        100m
      memory:     500M
...
```
如果此时如果还未发现线索，还可以到容器内执行命令来进一步查看退出原因
```
kubectl exec cassandra -- cat /var/log/cassandra/system.log
```
如果还是没有线索，那就需要 SSH 登录该 Pod 所在的 Node 上，查看 Kubelet 或者 Docker 的日志进一步排查了
```
# Query Node
kubectl get pod <pod-name> -o wide

# SSH to Node
ssh <username>@<node-name>
```

五、Pod 处于 Error 状态

通常处于 Error 状态说明 Pod 启动过程中发生了错误。常见的原因包括
- 依赖的 ConfigMap、Secret 或者 PV 等不存在
-	请求的资源超过了管理员设置的限制，比如超过了 LimitRange 等
-	违反集群的安全策略，比如违反了 PodSecurityPolicy 等
-	容器无权操作集群内的资源，比如开启 RBAC 后，需要为 ServiceAccount 配置角色绑定

六、Pod 处于 Terminating 或 Unknown 状态
- 从集群中删除该 Node。使用公有云时，kube-controller-manager 会在 VM 删除后自动删除对应的 Node。而在物理机部署的集群中，需要管理员手动删除 Node（如 kubectl delete node <node-name>。
- Node 恢复正常。Kubelet 会重新跟 kube-apiserver 通信确认这些 Pod 的期待状态，进而再决定删除或者继续运行这些 Pod。
- 用户强制删除。用户可以执行 kubectl delete pods <pod> --grace-period=0 --force 强制删除 Pod。除非明确知道 Pod 的确处于停止状态（比如 Node 所在 VM 或物理机已经关机），否则不建议使用该方法。特别是 StatefulSet 管理的 Pod，强制删除容易导致脑裂或者数据丢失等问题。

处于 Terminating 状态的 Pod 在 Kubelet 恢复正常运行后一般会自动删除。但有时也会出现无法删除的情况，并且通过 kubectl delete pods <pod> --grace-period=0 --force 也无法强制删除。此时一般是由于 finalizers 导致的，通过 kubectl edit 将 finalizers 删除即可解决。
```
"finalizers": [
  "foregroundDeletion"
]
```
  
七、Pod 行为异常

这里所说的行为异常是指 Pod 没有按预期的行为执行，比如没有运行 podSpec 里面设置的命令行参数。这一般是 podSpec yaml 文件内容有误，可以尝试使用 --validate 参数重建容器，比如
```
kubectl delete pod mypod
kubectl create --validate -f mypod.yaml
```
也可以查看创建后的 podSpec 是否是对的，比如
```
kubectl get pod mypod -o yaml
```

网络排错
---
介绍各种常见的网络问题以及排错方法，包括 Pod 访问异常、Service 访问异常以及网络安全策略异常等。
- Pod 访问容器外部网络
- 从容器外部访问 Pod 网络
- Pod 之间相互访问

当然，以上每种情况还都分别包括本地访问和跨主机访问两种场景，并且一般情况下都是通过 Service 间接访问 Pod。

网络异常可能的原因比较多，常见的有
- CNI 网络插件配置错误，导致多主机网络不通，比如
  - IP 网段与现有网络冲突
  - 插件使用了底层网络不支持的协议
  - 忘记开启 IP 转发等
    - sysctl net.ipv4.ip_forward
    - sysctl net.bridge.bridge-nf-call-iptables
- Pod 网络路由丢失，比如
  - kubenet 要求网络中有 podCIDR 到主机 IP 地址的路由，这些路由如果没有正确配置会导致 Pod 网络通信等问题
  - 在公有云平台上，kube-controller-manager 会自动为所有 Node 配置路由，但如果配置不当（如认证授权失败、超出配额等），也有可能导致无法配置路由
- 主机内或者云平台的安全组、防火墙或者安全策略等阻止了 Pod 网络，比如
  - 非 Kubernetes 管理的 iptables 规则禁止了 Pod 网络
  - 公有云平台的安全组禁止了 Pod 网络（注意 Pod 网络有可能与 Node 网络不在同一个网段）
  - 交换机或者路由器的 ACL 禁止了 Pod 网络

Service 无法访问
---
访问 Service ClusterIP 失败时，可以首先确认是否有对应的 Endpoints
```
kubectl get endpoints <service-name>
```
如果该列表为空，则有可能是该 Service 的 LabelSelector 配置错误，可以用下面的方法确认一下

#查询 Service 的 LabelSelector
```
kubectl get svc <service-name> -o jsonpath='{.spec.selector}'
```

#查询匹配 LabelSelector 的 Pod
```
kubectl get pods -l key1=value1,key2=value2
```
如果 Endpoints 正常，可以进一步检查
-	Pod 的 containerPort 与 Service 的 containerPort 是否对应
-	直接访问 podIP:containerPort 是否正常
再进一步，即使上述配置都正确无误，还有其他的原因会导致 Service 无法访问，比如
-	Pod 内的容器有可能未正常运行或者没有监听在指定的 containerPort 上
-	CNI 网络或主机路由异常也会导致类似的问题
-	kube-proxy 服务有可能未启动或者未正确配置相应的 iptables 规则，比如正常情况下名为 hostnames 的服务会配置以下 iptables 规则

Volume异常处理
---
持久化存储异常（PV、PVC、StorageClass等）的排错方法。
 
一般来说，无论 PV 处于什么异常状态，都可以执行 kubectl describe pv/pvc <pod-name> 命令来查看当前 PV 的事件。这些事件通常都会有助于排查 PV 或 PVC 发生的问题。
```
kubectl get pv
kubectl get pvc
kubectl get sc

kubectl describe pv <pv-name>
kubectl describe pvc <pvc-name>
kubectl describe sc <storage-class-name>
```



