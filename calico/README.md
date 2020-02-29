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
