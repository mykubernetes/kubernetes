kubernetes网络方案值Calico
===
Calico是一个纯三层的数据中心网络方案，Calico支持广泛的平台，包括kubernetes、OpenStack等。

Calico在每一个计算节点利用Linux Kernel 实现了一个高效的虚拟路由器（vRouter）来负责数据转发，而每个vRouter通过BGP协议负责把自己上运行的workload的路由信息向整个Calico 网络内传输。

此外，Calico项目还实现了Kubernetes网络策略，提供ACL功能

1、BGP概念
---
实际上，Calico项目提供的网络解决方案，与Flannel的host-gw模式几乎一样。也就是说，Calico也是基于路由表实现容器的数据包转发，但不同于Flannel使用flanneld进程来维护路由信息的做法，而Calico项目使用BGP协议来自动维护整个集群的路由信息。

BGP英文全称是Border Gateway Protocol,即边界网关协议，它是一种自治系统间的动态路由发现协议，与其他BGP系统交换网络可达信息。
![image](https://github.com/mykubernetes/kubernetes/blob/master/calico/image/BGP1.png)

在这个图中，有两个自治系统（autonomous system,简称为AS）: AS1 和 AS2。

在互联网中，一个自治系统（AS）是一个有权自主地决定在本系统中应采用何种路由协议的小型单位。这个网络单位可以是一个简单的网络也可以是一个由一个或多个普通的网络管理员来控制的网络群体，它是一个单独的可管理的网络单元（例如一所大学，一个企业或者一个公司个体）。一个自治系统有时也被称为是一个路由选择域（routing domain）。一个自治系统将会分配一个全局的唯一的16位号码，有时我们把这个号码叫做自治系统号（ASN）

在正常情况下，自治系统之间不会有任何来往。如果两个自治系统里的主机，要通过IP地址直接进行通信，我们就必须使用路由器把这两个自治系统连起来。BGP协议就是让他们互联的一种方式。

2、Calico BGP实现
---
![image](https://github.com/mykubernetes/kubernetes/blob/master/calico/image/calico%20BGP%E5%AE%9E%E7%8E%B0.png)

Calico主要由三个部分组成：

- Felix: 以DaemonSet方式部署，运行在每一个Node节点上，主要负责维护宿主机上路由规则以及ACL规则。
- BGP Client (BIRD): 主要负责把Felix写入kernel的路由信息分发到集群Calico网络。
- Etcd: 分布式键值存储，保存Calico的策略和网络配置状态。
- calicoctl: 允许您从简单的命令行界面实现高级策略和网络。

3、Calico 部署
---
```
crul https://docs.projectcalico.org/v3.9/manifests/calico-etcd.yaml -o calico.yaml
```
下载完成后还需要修改里面配置项：
具体步骤如下：
- 配置连接etcd地址，如果使用https,还需要配置证书。
- 根据实际网络规划修改Pod CIDR(CALICO_IPV4POOL_CIDR)。
- 选择工作模式(CALICO_IPV4POOL_CIDR)，支持BGP,IPIP。
修改完成应用清单：
```
# kubectl apply -f calico.yaml
# kubectl get pods -n kube-system
```

4、Calico管理工具
---
下载工具：https://github.com/projectcalico/calicoctl/releases
```
# wget -o /usr/local/bin/calicoctl https://github.com/projectcalico/calicoctl/releases/download/v3.9.1/calicoctl
# chmod +x /usr/local/bin/calicoctl
```

```
# mkdir /etc/calico
# vim /etc/calico/calicoctl.cfg
apiVersion: projectcalico.org/v3
kind: CalicoAPIConfig
metadata:
spec:
  datastoreType: "etcdv3"
  etcdEndpoints: "https://192.168.31.61:2379,https://192.168.31.62:2379,https://192.168.31.63:2379"
  etcdKeyFile: "/opt/etcd/ssl/server-key.pem"
  etcdCertFile: "/opt/etcd/ssl/server.pem"
  etcdCACertFile: "/opt/etcd/ssl/ca.pem"
```
使用calicoctl查看服务状态
```
# calicoctl node status
Calico process is running.

IPv4 BGP status
+---------------+-------------------+-------+----------+-------------+
| PEER ADDRESS  |     PEER TYPE     | STATE |  SINCE   |    INFO     |
+---------------+-------------------+-------+----------+-------------+
| 192.168.31.63 | node-to-node mesh | up    | 09:03:56 | Established |
| 192.168.31.62 | node-to-node mesh | up    | 09:04:08 | Established |
+---------------+-------------------+-------+----------+-------------+

IPv6 BGP status
No IPv6 peers found.

# calicoctl get nodes
NAME
k8s-master1
k8s-node1
k8s-node2

查看IPAM的IP地址池：
# calicoctl get ippool
NAME                     CIDR                  SELECTOR
default-ipv4-ippool      10.244.0.0/16         all() 
```

5、Calico BGP 原理剖析
---

![image](https://github.com/mykubernetes/kubernetes/blob/master/calico/image/calico2.png)

Pod 1 访问 Pod 2大致流程如下：  
  1.数据包从容器1出到达Veth Pair另一端（宿主机上，以cali前缀开头）；  
  2.宿主机根据路由规则，将数据包转发给下一条（网关）；  
  3.到达Node2,根据路由规则将数据包转发给cali设备，从而到达容器2。  

路由表：
```
# node1
10.244.36.65 dev cali4f18ce2c9a1 scope link
10.244.169.128/26 via 192.168.31.63 dev ens33 proto bird
10.244.235.192/26 via 192.168.31.61 dev ens33 proto bird
# node2
10.244.169.129 dev calia4d5b2258bb scope link
10.244.36.64/26 via 192.168.31.63 dev ens33 proto bird
10.244.235.192/26 via 192.168.31.61 dev ens33 proto bird
```
其中，这里最核心的“下一跳”路由规则，就是由Calico的Felix进程负责维护的。这些路由规则信息，则是通过BGP Client也是就是BIRD组件，使用BGP协议传世而来的。

6、Route Reflector 模式（RR）
---
https://docs.projectcalico.org/master/networking/bgp

Calico 维护的网络在默认是（Node-to-Node Mesh）全互联模式，Calico集群中的节点之间都会相互建立连接，用于路由交换。但是随着集群规模的扩大，mesh模式将形成一个巨大服务网络，连接数成倍增加。

这时就需要使用Route Reflector（路由器反射）模式解决这个问题。

确定一个或多个Calico节点充当路由反射器，让其他节点从这个RR节点获取路由信息。

具体步骤如下：

1、关闭node-to-node BGP网络
---
添加default BGP配置，调整nodeToNodeMeshEnabled和asNumber:
```
cat << EOF | calicoctl create -f -
apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
  name: default
spec:
  logServerityScreen: Info
  nodeToNodeMeshEnabled: false
  asNumber: 63400
EOF
```
ASN号可以通过获取# calicoctl get nodes --output=wide

2、配置指点节点充当路由反射器
---
为方便让BGPPeer轻松选择节点，通过标签选择器匹配。

给路由器反射节点打标签：
```
kubectl label node my-node route-reflector=true
```
然后配置路由器反射器节点routeReflectorClusterID:
```
# calicoctl get node k8s-node2 -o yaml > node.yaml

apiVersion: projectcalico.org/v3
kind: Node
metadata:
  annotation:
    projectcalico.org/kube-labels: '{"beta.kubernetes.io/arch": "amd64","beta.kubernetes.io/os": "linux","kubernetes.io/arch": "amd64","kubernetes.io/hostname": "k8s-node2","kubernetes.io/os": "linux"}'
  creationTimestamp: null
  labels:
    beta.kubernetes.io/arch: amd64
    beta.kubernetes.io/os: linux
    kubernetes.io/arch: amd64
    kubernetes.io/hostname: k8s-node2
    kubernetes.io/os: linux
  name: k8s-node2
spec:
  bgp:
    ipv4Address: 192.168.31.63/24
    routeReflectorClusterID: 244.0.0.1   #集群ID
  orchRefs:
  - nodeName: k8s-node2
    orchestrator: k8s
```
现在，很容易使用标签选择器将路由反射器节点与其他非路由反射器节点配置为对等：
```
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: peer-with-route-reflectors
spec:
  nodeSelector: all()
  peerSelector: route-reflector == 'true'
```
查看节点的BGP连接状态：
```
calicoctl node status
```

7、IPIP模式
---
在前面提到过，Flannel host-gw模式最主要的限制，就是要求集群宿主机之间是二层连通的。而这个限制于Calico来说，也同样存在。
修改为IPIP模式：
```
# calicoctl get ipPool -o yaml > ipip.yaml
# vim ipip.yaml
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: default-ipv4-ippool
spec:
  blockSize: 26
  cidr: 10.244.0.0/16
  ipipMode: Always
  natOutgoing: true

# calicoctl apply -f ipip.yaml
# calicoctl get ippool -o wide
```
![image](https://github.com/mykubernetes/kubernetes/blob/master/calico/image/calico3.png)  
Pod1 访问 Pod2 大致流程如下：  
  1.数据包从容器1出到达Veth Pair 另一端（宿主机上，以cali前缀开头）；  
  2.进入IP隧道设备（tunl0）,由Linux内核IPIP驱动封装在宿主机网络的IP包中（新的IP包目的地址源IP的下一跳地址，即192.168.31.63），这样就成了Node1到Node2的数据包；  
  3.数据包经过路由器三层转发到Node2;  
  4.Node2收到数据包后，网络协议栈会使用IPIP驱动进行解包，从中拿到原始IP包；  
  5.然后根据路由规则，根据路由规则将数据包转发给cali设备，从而到达容器2。  
路由表
```
#node1
10.244.36.65 dev cali4f18ce2c9a1 scope link
10.244.169.128/26 via 192.168.31.63 dev tunl0 proto bird onlink
#node2
10.244.169.129 dev calia4df18ce2c9a1 scope link
10.244.36.64/26 via 192.168.31.62 dev tunl0 proto bird onlink
```
不难看到，当Calico使用IPIP模式的时候，集群的网络性能可能会因为额外的封包和解包工作而下降所以建议你将所有宿主机节点放在一个子网里，避免使用IPIP。

1、为什么需要网络隔离？
---
CNI插件解决了不同Node节点pod互通问题，从而形成一个扁平化网络，默认情况下kubernetes网络允许所有Pod到Pod的流量，在一些场景中，我们不希望Pod直接默认相互访问，例如：
- 应用程序间的访问控制。例如微服务A允许访问微服务B,微服务C不能访问微服务A
- 开发环境命令空间不能访问测试环境命名空间Pod
- 当Pod暴露到外部时，需要做Pod白名单
- 多租户网络环境隔离
所以，我们需要使用network policy对pod网络进行隔离。支持对Pod级别和Namespace级别网络访问控制。

Pod网络入口方向隔离
- 基于Pod级网络隔离：只允许特点对象访问Pod（使用标签定义），允许白名单上的IP地址或者IP段访问Pod
- 基于Namespace级网络隔离： 多个命名空间，A和B命名空间Pod完全隔离。

Pod网络出口方向隔离
- 拒绝某个Namespace上所有Pod访问外部
- 基于目的IP的网络隔离： 只允许Pod访问白名单上的IP地址或者IP段
- 基于目标端口的网络隔离： 只允许Pod访问白名单上的端口

2、网络策略概述
---














