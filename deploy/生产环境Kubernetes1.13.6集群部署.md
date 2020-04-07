系统架构概述
===
Kubernetes 主要由以下几个核心组件组成：
-	etcd 保存了整个集群的状态；
-	kube-apiserver 提供了资源操作的唯一入口，并提供认证、授权、访问控制、API 注册和发现等机制；
-	kube-controller-manager 负责维护集群的状态，比如故障检测、自动扩展、滚动更新等；
-	kube-scheduler 负责资源的调度，按照预定的调度策略将 Pod 调度到相应的机器上；
-	kubelet 负责维持容器的生命周期，同时也负责 Volume（CVI）和网络（CNI）的管理；
-	Container runtime 负责镜像管理以及 Pod 和容器的真正运行（CRI），默认的容器运行时为 Docker；
-	kube-proxy 负责为 Service 提供 cluster 内部的服务发现和负载均衡；

除了核心组件，还有一些推荐的 Add-ons：
-	kube-dns 负责为整个集群提供 DNS 服务
-	Ingress Controller 为服务提供外网入口
-	Heapster 提供资源监控
- Dashboard 提供 GUI
-	Federation 提供跨可用区的集群
-	Fluentd-elasticsearch 提供集群日志采集、存储与查询

安装前准备
===

| 软件包名称 | 说明 | 下载路径 |
| :------: | :--------: | :-------: |
| CentOS-7-x86_64-Minimal-1810.iso | Centos7 操作系统镜像 | https://mirrors.aliyun.com/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1810.iso  |
| kubernetes-server-linux-amd64.tar.gz | Kubernetes master节点的安装包，请获取所有包后解压。 | 访问https://github.com/kubernetes, 进入"kubernets > releases "。选择对应版本后，下载安装包。 |
| kubernetes-node-linux-amd64.tar.gz | Kubernetes Node节点的安装包。 | https://dl.k8s.io/v1.13.6/kubernetes-node-linux-amd64.tar.gz |
| etcd-v3.3.10-linux-amd64.tar.gz | etcd是一个开源的分布式键值存储，为Container Linux集群提供共享配置和服务发现。 | https://github.com/etcd-io/etcd/releases/download/v3.3.10/etcd-v3.3.10-linux-amd64.tar.gz |
| flannel-v0.11.0-linux-amd64.tar.gz | Container Network CNI plugin | https://github.com/coreos/flannel/releases/download/v0.11.0/flannel-v0.11.0-linux-amd64.tar.gz |

安装规划
===
| 名称 | 网段 |
| :------: | :--------: |
| Pod分配IP段 | 10.244.0.0/16 |
| ClusterIP 地址 | 10.99.0.0/16 |
| CoreDns 地址 | 10.99.110.110 |
| 统一安装路径 | /data/apps/ |











