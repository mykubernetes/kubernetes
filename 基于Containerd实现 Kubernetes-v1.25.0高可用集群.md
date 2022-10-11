# 一、Kubernetes 高可用集群部署架构

本示例中的Kubernetes集群部署将基于以下环境进行。
- 每个主机2G内存以上,2核CPU以上
- OS: Ubuntu 20.04.4
- Kubernetes：v1.25,0
- CRI: v1.6.8 

网络环境：
```
节点网络：10.0.0.0.0/24
Pod网络：10.244.0.0/16
Service网络：10.96.0.0/12
```

| IP | 主机名 | 角色 |
|----|-------|------|
| 10.0.0.101 | master1.wang.org | K8s 集群主节点 1，Master和etcd |
| 10.0.0.102 | master2.wang.org | K8s 集群主节点 2，Master和etcd |
| 10.0.0.103 | master3.wang.org | K8s 集群主节点 3，Master和etcd |
| 10.0.0.104 | node1.wang.org | K8s 集群工作节点 1 |
| 10.0.0.105 | node2.wang.org | K8s 集群工作节点 2 |
| 10.0.0.106 | node3.wang.org | K8s 集群工作节点 3 |
| 10.0.0.107 | ha1.wang.org | K8s 主节点访问入口 1,提供高可用及负载均衡 |
| 10.0.0.108 | ha2.wang.org | K8s 主节点访问入口 2,提供高可用及负载均衡 |
| 10.0.0.100 | kubeapi.wang.org | VIP，在ha1和ha2主机实现 |

# 二、基于 Kubeadm 实现 Kubernetes v1.25.0和Containerd 集群部署流程说明

官方说明
```
https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/
https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
https://kubernetes.io/zh-cn/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm
```

使用 kubeadm ，能创建一个符合最佳实践的最小化 Kubernetes 集群。 事实上，你可以使用 kubeadm 配置一个通过 Kubernetes 一致性测试的集群。 kubeadm 还支持其他集群生命周期功能， 例如启动引导令牌和集群升级。
- Kubernetes集群API访问入口的高可用
- 每个节点主机的初始环境准备
- 在所有Master和Node节点都安装容器运行时,实际Kubernetes只使用其中的Containerd
- 在所有Master和Node节点安装kubeadm 、kubelet、kubectl
- 在所有节点安装和配置 cri-dockerd
- 在第一个 master 节点运行 kubeadm init 初始化命令 ,并验证 master 节点状态
- 在第一个 master 节点安装配置网络插件
- 在其它master节点运行kubeadm join 命令加入到控制平面集群中
- 在所有 node 节点使用 kubeadm join 命令加入集群
- 创建 pod 并启动容器测试访问 ，并测试网络通信

# 三、基于Kubeadm 部署 Kubernetes v1.25.0和Containerd 高可用集群

## 3.1 部署 Kubernetes 集群 API 访问入口的高可用

`在10.0.0.107和10.0.0.108上实现如下操作`

### 3.1.1 安装 HAProxy

利用 HAProxy 实现 Kubeapi 服务的负载均衡

```
#修改内核参数
[root@ha1 ~]#cat >> /etc/sysctl.conf <<EOF
net.ipv4.ip_nonlocal_bind = 1
EOF
[root@ha1 ~]#sysctl -p 
#安装配置haproxy
[root@ha1 ~]#apt update
[root@ha1 ~]#apt -y install haproxy
##添加下面行
[root@ha1 ~]#cat >> /etc/haproxy/haproxy.cfg <<EOF
listen stats
   mode http
   bind 0.0.0.0:8888
   stats enable
   log global
   stats uri /status
   stats auth admin:123456
    
listen kubernetes-api-6443
   bind 10.0.0.100:6443
   mode tcp 
   server master1 10.0.0.101:6443 check inter 3s fall 3 rise 3
   server master2 10.0.0.102:6443 check inter 3s fall 3 rise 3
   server master3 10.0.0.103:6443 check inter 3s fall 3 rise 3
EOF
[root@ha1 ~]#systemctl restart haproxy
```

### 3.1.2 安装 Keepalived

安装 keepalived 实现 HAProxy的高可用

```
[root@ha1 ~]#apt update
[root@ha1 ~]#apt -y install keepalived 
[root@ha1 ~]#vim /etc/keepalived/keepalived.conf
! Configuration File for keepalived
global_defs {
   router_id ha1.wang.org  #指定router_id,#在ha2上为ha2.wang.org
}
vrrp_script check_haproxy { #定义脚本
   script "/etc/keepalived/check_haproxy.sh"
   interval 1
   weight -30
   fall 3
   rise 2
   timeout 2
}

[root@ha1 ~]#apt update
[root@ha1 ~]#apt -y install keepalived 
[root@ha1 ~]#vim /etc/keepalived/keepalived.conf
! Configuration File for keepalived
global_defs {
   router_id ha1.wang.org  #指定router_id,#在ha2上为ha2.wang.org
}
vrrp_script check_haproxy { #定义脚本
   script "/etc/keepalived/check_haproxy.sh"
   interval 1
   weight -30
   fall 3
   rise 2
   timeout 2
}
```

### 3.1.3 测试访问

`浏览器访问验证,用户名密码: admin:123456`

```
http://kubeapi.wang.org:8888/status
```

## 3.2 所有主机初始化

### 3.2.1 配置 ssh key 验证

`配置 ssh key 验证,方便后续同步文件`

```
ssh-keygen
ssh-copy-id -i ~/.ssh/id_rsa.pub root@10.0.0.102
.....
```

### 3.2.2 设置主机名和解析

```
hostnamectl set-hostname master1.wang.org
cat > /etc/hosts <<EOF
10.0.0.100 kubeapi.wang.org kubeapi
10.0.0.101 master1.wang.org master1 
10.0.0.102 master2.wang.org master2
10.0.0.103 master2.wang.org master3
10.0.0.104 node1.wang.org node1
10.0.0.105 node2.wang.org node2
10.0.0.106 node3.wang.org node3
10.0.0.107 ha1.wang.org ha1
10.0.0.108 ha2.wang.org ha2
EOF
for i in {102..108};do scp /etc/hosts 10.0.0.$i:/etc/ ;done
```

### 3.2.3 禁用 swap

```
swapoff -a
sed -i '/swap/s/^/#/' /etc/fstab

#或者
systemctl disable --now swap.img.swap
systemctl mask swap.target
```

### 3.2.4 时间同步

```
#借助于chronyd服务（程序包名称chrony）设定各节点时间精确同步
apt -y install chrony
chronyc sources -v
```
### 3.2.5 禁用防火墙

```
#禁用默认配置的iptables防火墙服务
ufw disable
ufw status
```

### 3.2.6 内核参数调整

如果是安装 Docker 会自动配置以下的内核参数，而无需手动实现。但是如果安装Contanerd，还需手动配置允许 iptables 检查桥接流量,若要显式加载此模块，需运行 modprobe br_netfilter 为了让 Linux 节点的 iptables 能够正确查看桥接流量，还需要确认net.bridge.bridge-nf-call-iptables 设置为 1。

```
#加载模块
modprobe overlay
modprobe br_netfilter

#开机加载
cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

#设置所需的 sysctl 参数，参数在重新启动后保持不变
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

#应用 sysctl 参数而不重新启动
sysctl --system
```

## 3.3 所有主机安装 Containerd

### 3.3.1 包安装 Containerd

`在所有节点上安装Containerd`

```
#Ubuntu20.04可以利用内置仓库安装containerd
[root@node1 ~]#apt update
[root@node1 ~]#apt -y install containerd

#确认服务启动
[root@node1 ~]#systemctl status containerd

#利用containerd的客户端工具ctr验证修改是否成功
[root@node1 ~]#containerd --version
containerd github.com/containerd/containerd 1.5.9-0ubuntu1~20.04.4 
ctr version 
[root@node1 ~]#ctr version 
Client:
 Version:  1.5.9-0ubuntu1~20.04.4
 Revision: 
 Go version: go1.13.8
Server:
 Version:  1.5.9-0ubuntu1~20.04.4
 Revision: 
 UUID: dedffba3-daac-4ad9-b596-14da3b7a1cf3
  
#修改containerd配置,将 sandbox_image 镜像源设置为阿里云google_containers镜像源（国内网络需要）
[root@node1 ~]#mkdir /etc/containerd/
[root@node1 ~]#containerd config default > /etc/containerd/config.toml
[root@node1 ~]#grep sandbox_image /etc/containerd/config.toml
[root@node1 ~]#sed -i "s#k8s.gcr.io/pause#registry.aliyuncs.com/google_containers/pause#g" /etc/containerd/config.toml

#镜像加速(可选)
[root@node1 ~]#vim /etc/containerd/config.toml

#在此行下面加两行
     [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
       [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
         endpoint = ["https://registry.aliyuncs.com"]

#配置containerd cgroup 驱动程序systemd（可选）
[root@node1 ~]#sed -i 's#SystemdCgroup = false#SystemdCgroup = true#g' /etc/containerd/config.toml
[root@node1 ~]#grep SystemdCgroup /etc/containerd/config.toml
           SystemdCgroup = true

[root@node1 ~]#systemctl restart containerd
```

### 3.3.2 二进制安装 Containerd

Containerd有两种二进制安装包:
- containerd-xxx ：不包含runC，需要单独安装runC
- cri-containerd-cni-xxx：包含runc和kubernetes里的所需要的相关文件

#### 3.3.2.1 下载 Containerd

官方下载链接
```
https://github.com/containerd/containerd
```

```
#查看内容
[root@node2 ~]#tar tf cri-containerd-cni-1.6.8-linux-amd64.tar.gz 
etc/
etc/crictl.yaml
etc/systemd/
etc/systemd/system/
etc/systemd/system/containerd.service
etc/cni/
etc/cni/net.d/
etc/cni/net.d/10-containerd-net.conflist
usr/
usr/local/
usr/local/sbin/
usr/local/sbin/runc
usr/local/bin/
usr/local/bin/containerd-stress
usr/local/bin/containerd-shim-runc-v2
usr/local/bin/containerd-shim
usr/local/bin/ctr
usr/local/bin/containerd
usr/local/bin/critest
usr/local/bin/ctd-decoder
usr/local/bin/crictl
usr/local/bin/containerd-shim-runc-v1
opt/
opt/containerd/
opt/containerd/cluster/
opt/containerd/cluster/gce/
opt/containerd/cluster/gce/env
opt/containerd/cluster/gce/cloud-init/
opt/containerd/cluster/gce/cloud-init/master.yaml
opt/containerd/cluster/gce/cloud-init/node.yaml
opt/containerd/cluster/gce/cni.template
opt/containerd/cluster/gce/configure.sh
opt/containerd/cluster/version
opt/cni/
opt/cni/bin/
opt/cni/bin/bandwidth
opt/cni/bin/loopback
opt/cni/bin/ipvlan
opt/cni/bin/host-local
opt/cni/bin/static
opt/cni/bin/vlan
opt/cni/bin/tuning
opt/cni/bin/host-device
opt/cni/bin/firewall
opt/cni/bin/portmap
opt/cni/bin/sbr
opt/cni/bin/macvlan
opt/cni/bin/bridge
opt/cni/bin/dhcp
opt/cni/bin/ptp
opt/cni/bin/vrf

#解压缩至根目录
[root@node2 ~]#tar xf cri-containerd-cni-1.6.8-linux-amd64.tar.gz -C /
```

#### 3.3.2.2 配置 Containerd
```
#修改containerd配置,将 sandbox_image 镜像源设置为阿里云google_containers镜像源（所有节点）
[root@node2 ~]#mkdir /etc/containerd/
[root@node2 ~]#containerd config default > /etc/containerd/config.toml
[root@node2 ~]#grep sandbox_image /etc/containerd/config.toml
[root@node2 ~]#sed -i "s#k8s.gcr.io/pause#registry.aliyuncs.com/google_containers/pause#g" /etc/containerd/config.toml

#镜像加速
[root@node1 ~]#vim /etc/containerd/config.toml
#在此行下面加两行
     [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
       [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
         endpoint = ["https://registry.aliyuncs.com"]
          
[root@node4 ~]#systemctl daemon-reload 
[root@node4 ~]#systemctl status containerd
● containerd.service - containerd container runtime
     Loaded: loaded (/etc/systemd/system/containerd.service; disabled; vendor preset: enabled)
     Active: inactive (dead)
       Docs: https://containerd.io
[root@node4 ~]#systemctl enable --now   containerd
Created symlink /etc/systemd/system/multi-user.target.wants/containerd.service → /etc/systemd/system/containerd.service.

[root@node3 ~]#systemctl is-active containerd
active
```

#### 3.3.2.3 安装 CNI 插件工具

虽然 cri-containerd-cni-1.6.8-linux-amd64.tar.gz 包含了cni，但是无法和kubernetes 兼容，在创建Pod时会出错下面错误日志

```
[root@node2 ~]#cat /var/log/syslog
Sep  4 20:04:57 node4 containerd[62104]: time="2022-09-04T20:04:57.394576089+08:00" level=info msg="RunPodSandbox for &PodSandboxMetadata{Name:demoapp-55c5f88dcb-kl7mf,Uid:5dfc305b-d641-4d2c-8199-7655b7a1ba32,Namespace:default,Attempt:0,}"
Sep  4 20:04:57 node4 containerd[62104]: time="2022-09-04T20:04:57.408282176+08:00" level=error msg="Failed to destroy network for sandbox \"2d21c280a65d6d40ae1a6aadab70b9e50e8430d6de17b5b41ed8ffecdb7d43f6\""error="plugin type=\"portmap\" failed (delete): incompatible CNI versions; config is \"1.0.0\", plugin supports [\"0.1.0\" \"0.2.0\" \"0.3.0\" \"0.3.1\" \"0.4.0\"]"
Sep  4 20:04:57 node4 systemd[1053]: run-netns-cni\x2df682c24c\x2db5d6\x2d9ba2\x2d2543\x2d78324d41d347.mount: Succeeded.
Sep  4 20:04:57 node4 systemd[1]: run-netns-cni\x2df682c24c\x2db5d6\x2d9ba2\x2d2543\x2d78324d41d347.mount: Succeeded.
Sep  4 20:04:57 node4 containerd[62104]: time="2022-09-04T20:04:57.411439230+08:00" level=error msg="RunPodSandbox for &PodSandboxMetadata{Name:demoapp-55c5f88dcb-kl7mf,Uid:5dfc305b-d641-4d2c-8199-7655b7a1ba32,Namespace:default,Attempt:0,} failed, error" error="failed to setup network for sandbox \"2d21c280a65d6d40ae1a6aadab70b9e50e8430d6de17b5b41ed8ffecdb7d43f6\": plugin type=\"bridge\" failed (add): incompatible CNI versions; config is \"1.0.0\", plugin supports [\"0.1.0\" \"0.2.0\" \"0.3.0\" \"0.3.1\" \"0.4.0\"]"
Sep  4 20:04:57 node4 kubelet[65352]: E0904 20:04:57.411790 65352 remote_runtime.go:222] "RunPodSandbox from runtime service failed" err="rpc error: code = Unknown desc = failed to setup network for sandbox \"2d21c280a65d6d40ae1a6aadab70b9e50e8430d6de17b5b41ed8ffecdb7d43f6\": plugin type=\"bridge\" failed (add): incompatible CNI versions; config is \"1.0.0\", plugin supports [\"0.1.0\" \"0.2.0\" \"0.3.0\" \"0.3.1\" \"0.4.0\"]"
Sep  4 20:04:57 node4 kubelet[65352]: E0904 20:04:57.411859 65352 kuberuntime_sandbox.go:71] "Failed to create sandbox for pod" err="rpc error: code = Unknown desc = failed to setup network for sandbox \"2d21c280a65d6d40ae1a6aadab70b9e50e8430d6de17b5b41ed8ffecdb7d43f6\": plugin type=\"bridge\" failed (add): incompatible CNI versions; config is \"1.0.0\", plugin supports [\"0.1.0\" \"0.2.0\" \"0.3.0\" \"0.3.1\" \"0.4.0\"]" pod="default/demoapp-55c5f88dcb-kl7mf"
Sep  4 20:04:57 node4 kubelet[65352]: E0904 20:04:57.411881 65352 kuberuntime_manager.go:772] "CreatePodSandbox for pod failed" err="rpc error: code = Unknown desc = failed to setup network for sandbox \"2d21c280a65d6d40ae1a6aadab70b9e50e8430d6de17b5b41ed8ffecdb7d43f6\": plugin type=\"bridge\" failed (add): incompatible CNI versions; config is \"1.0.0\", plugin supports [\"0.1.0\" \"0.2.0\" \"0.3.0\" \"0.3.1\" \"0.4.0\"]" pod="default/demoapp-55c5f88dcb-kl7mf"
Sep  4 20:04:57 node4 kubelet[65352]: E0904 20:04:57.411920 65352 pod_workers.go:965] "Error syncing pod, skipping" err="failed to \"CreatePodSandbox\" for \"demoapp-55c5f88dcb-kl7mf_default(5dfc305b-d641-4d2c8199-7655b7a1ba32)\" with CreatePodSandboxError: \"Failed to create sandbox for pod \\\"demoapp-55c5f88dcb-kl7mf_default(5dfc305b-d641-4d2c-8199-7655b7a1ba32)\\\": rpc error: code = Unknown desc = failed to setup network for sandbox \\\"2d21c280a65d6d40ae1a6aadab70b9e50e8430d6de17b5b41ed8ffecdb7d43f6\\\": plugin type=\\\"bridge\\\" failed (add): incompatible CNI versions; config is \\\"1.0.0\\\", plugin supports [\\\"0.1.0\\\" \\\"0.2.0\\\" \\\"0.3.0\\\" \\\"0.3.1\\\" \\\"0.4.0\\\"]\"" pod="default/demoapp-55c5f88dcb-kl7mf" podUID=5dfc305b-d641-4d2c-8199-7655b7a1ba32

```

范例：解决CNI问题
```
#下载链接：https://github.com/containernetworking/plugins/releases
[root@node2 ~]#wget https://github.com/containernetworking/plugins/releases/download/v1.1.1/cni-plugins-linux-amd64-v1.1.1.tgz

#覆盖原有的文件
[root@node2 ~]#tar xf cni-plugins-linux-amd64-v1.1.1.tgz -C /opt/cni/bin/
```

## 3.4 所有主机安装 kubeadm、kubelet 和 kubectl

通过国内镜像站点阿里云安装的参考链接：
```
https://developer.aliyun.com/mirror/kubernetes
```

范例: Ubuntu 安装
```
# apt-get update && apt-get install -y apt-transport-https
# curl https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add -

# cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main
EOF

# for i in {102..106};do scp /etc/apt/sources.list.d/kubernetes.list 10.0.0.$i:/etc/apt/sources.list.d/;done

# apt-get update
#查看版本
apt-cache madison kubeadm|head
   kubeadm |  1.25.0-00 | https://mirrors.aliyun.com/kubernetes/apt kubernetes-xenial/main amd64 Packages
   kubeadm |  1.24.2-00 | https://mirrors.aliyun.com/kubernetes/apt kubernetes-xenial/main amd64 Packages
   kubeadm |  1.24.1-00 | https://mirrors.aliyun.com/kubernetes/apt kubernetes-xenial/main amd64 Packages
   kubeadm |  1.24.0-00 | https://mirrors.aliyun.com/kubernetes/apt kubernetes-xenial/main amd64 Packages

#安装指定版本
# apt install -y  kubeadm=1.25.0-00 kubelet=1.25.0-00 kubectl=1.25.0-00

#安装最新版本
# apt-get install -y kubelet kubeadm kubectl
```

## 3.5 提前准备 Kubernetes 初始化所需镜像(可选)

```
##Kubernetes-v1.24.X查看需要下载的镜像,发现k8s.gcr.io无法从国内直接访问
[root@master1 ~]#kubeadm config images list 
k8s.gcr.io/kube-apiserver:v1.25.0
k8s.gcr.io/kube-controller-manager:v1.25.0
k8s.gcr.io/kube-scheduler:v1.25.0
k8s.gcr.io/kube-proxy:v1.25.0
k8s.gcr.io/pause:3.7
k8s.gcr.io/etcd:3.5.3-0
k8s.gcr.io/coredns/coredns:v1.8.6

#Kubernetes-v1.25.0下载镜像地址调整为 registry.k8s.io,但仍然无法从国内直接访问
[root@master1 ~]#kubeadm config images list 
registry.k8s.io/kube-apiserver:v1.25.0
registry.k8s.io/kube-controller-manager:v1.25.0
registry.k8s.io/kube-scheduler:v1.25.0
registry.k8s.io/kube-proxy:v1.25.0
registry.k8s.io/pause:3.8
registry.k8s.io/etcd:3.5.4-0
registry.k8s.io/coredns/coredns:v1.9.3

#查看国内镜像
[root@master1 ~]#kubeadm config images list --image-repository 
registry.aliyuncs.com/google_containers  
registry.aliyuncs.com/google_containers/kube-apiserver:v1.24.4
registry.aliyuncs.com/google_containers/kube-controller-manager:v1.24.4
registry.aliyuncs.com/google_containers/kube-scheduler:v1.24.4
registry.aliyuncs.com/google_containers/kube-proxy:v1.24.4
registry.aliyuncs.com/google_containers/pause:3.7
registry.aliyuncs.com/google_containers/etcd:3.5.3-0
registry.aliyuncs.com/google_containers/coredns:v1.8.6

#从国内镜像站拉取镜像
[root@master1 ~]#kubeadm config images pull --kubernetes-version=v1.25.0 --image-repository registry.aliyuncs.com/google_containers   

#查看拉取的镜像
[root@master1 ~]#docker images
REPOSITORY                                                       TAG       IMAGE ID       CREATED         SIZE
registry.aliyuncs.com/google_containers/kube-apiserver           v1.25.0   d521dd763e2e   4 weeks ago     130MB
registry.aliyuncs.com/google_containers/kube-scheduler           v1.25.0   3a5aa3a515f5   4 weeks ago     51MB
registry.aliyuncs.com/google_containers/kube-proxy               v1.25.0   2ae1ba6417cb   4 weeks ago     110MB
registry.aliyuncs.com/google_containers/kube-controller-manager  v1.25.0   586c112956df   4 weeks ago     119MB
registry.aliyuncs.com/google_containers/etcd                     3.5.3-0   aebe758cef4c   4 months ago   299MB
registry.aliyuncs.com/google_containers/pause                    3.7       221177c6082a   5 months ago   711kB
registry.aliyuncs.com/google_containers/coredns                  v1.8.6    a4ca41631cc7   10 months ago   46.8MB

#导出镜像
[root@master1 ~]#docker image save `docker image ls --format "{{.Repository}}:{{.Tag}}"` -o k8s-images-v1.25.0.tar
[root@master1 ~]#gzip k8s-images-v1.25.0.tar
```

## 3.6 在第一个 master 节点初始化 Kubernetes 集群

kubeadm init 命令参考说明
```
--kubernetes-version：#kubernetes程序组件的版本号，它必须要与安装的kubelet程序包的版本号相同
--control-plane-endpoint：#多主节点必选项,用于指定控制平面的固定访问地址，可是IP地址或DNS名称，会被用于集群管理员及集群组件的kubeconfig配置文件的API Server的访问地址,如果是单主节点的控制平面部署时不使用该选项,注意:kubeadm 不支持将没有 --control-plane-endpoint 参数的单个控制平面集群转换为高可用性集群。
--pod-network-cidr：#Pod网络的地址范围，其值为CIDR格式的网络地址，通常情况下Flannel网络插件的默认为10.244.0.0/16，Calico网络插件的默认值为192.168.0.0/16
--service-cidr：#Service的网络地址范围，其值为CIDR格式的网络地址，默认为10.96.0.0/12；通常，仅Flannel一类的网络插件需要手动指定该地址
--service-dns-domain string #指定k8s集群域名，默认为cluster.local，会自动通过相应的DNS服务实现解析
--apiserver-advertise-address：#API 服务器所公布的其正在监听的 IP 地址。如果未设置，则使用默认网络接口。apiserver通告给其他组件的IP地址，一般应该为Master节点的用于集群内部通信的IP地址，0.0.0.0表示此节点上所有可用地址,非必选项
--image-repository string #设置镜像仓库地址，默认为 k8s.gcr.io,此地址国内可能无法访问,可以指向国内的镜像地址
--token-ttl #共享令牌（token）的过期时长，默认为24小时，0表示永不过期；为防止不安全存储等原因导致的令牌泄露危及集群安全，建议为其设定过期时长。未设定该选项时，在token过期后，若期望再向集群中加入其它节点，可以使用如下命令重新创建token，并生成节点加入命令。kubeadm token create --print-join-command
--ignore-preflight-errors=Swap” #若各节点未禁用Swap设备，还需附加选项“从而让kubeadm忽略该错误
--upload-certs #将控制平面证书上传到 kubeadm-certs Secret
--cri-socket  #v1.24版之后指定连接cri的socket文件路径,注意;不同的CRI连接文件不同

#如果是cRI是containerd，则使用--cri-socket unix:///run/containerd/containerd.sock
#如果是cRI是docker，则使用--cri-socket unix:///var/run/cri-dockerd.sock
#如果是CRI是CRI-o，则使用--cri-socket unix:///var/run/crio/crio.sock
#注意:CRI-o与containerd的容器管理机制不一样，所以镜像文件不能通用。
```

范例: 初始化集群
```
[root@master1 ~]#kubeadm init --control-plane-endpoint="kubeapi.wang.org" --kubernetes-version=v1.25.0 --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12 --token-ttl=0 --image-repository registry.aliyuncs.com/google_containers --upload-certs

[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy

Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
 https://kubernetes.io/docs/concepts/cluster-administration/addons/

You can now join any number of the control-plane node running the following command on each as root:

 kubeadm join kubeapi.wang.org:6443 --token ihbe5g.6jxdfwym49epsirr \
 --discovery-token-ca-cert-hash sha256:b7a7abccfc394fe431b8733e05d0934106c0e81abeb0a2bab4d1b7cfd82104c0 \
 --control-plane --certificate-key ae34c01f75e9971253a39543a289cdc651f23222c0e074a6b7ecb2dba667c059

Please note that the certificate-key gives access to cluster sensitive data, keep it secret!
As a safeguard, uploaded-certs will be deleted in two hours; If necessary, you can use
"kubeadm init phase upload-certs --upload-certs" to reload certs afterward.

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join kubeapi.wang.org:6443 --token ihbe5g.6jxdfwym49epsirr \
 --discovery-token-ca-cert-hash sha256:b7a7abccfc394fe431b8733e05d0934106c0e81abeb0a2bab4d1b7cfd82104c0 
```

如果想重新初始化,可以执行下面
```
#如果有工作节点,先在工作节点执行,再在control节点执行下面操作
kubeadm reset -f --cri-socket unix:///run/cri-dockerd.sock
rm -rf /etc/cni/net.d/  $HOME/.kube/config
reboot
```

## 3.7 在第一个 master 节点生成 kubectl 命令的授权文件

kubectl是kube-apiserver的命令行客户端程序，实现了除系统部署之外的几乎全部的管理操作，是kubernetes管理员使用最多的命令之一。kubectl需经由API server认证及授权后方能执行相应的管理操作，kubeadm部署的集群为其生成了一个具有管理员权限的认证配置文件/etc/kubernetes/admin.conf，它可由kubectl通过默认的“$HOME/.kube/config”的路径进行加载。当然，用户也可在kubectl命令上使用--kubeconfig选项指定一个别的位置。

下面复制认证为Kubernetes系统管理员的配置文件至目标用户（例如当前用户root）的家目录下：
```
#可复制3.6的结果执行下面命令
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

## 3.8 实现 kubectl 命令补全

kubectl 命令功能丰富,默认不支持命令补会,可以用下面方式实现
```
kubectl completion bash > /etc/profile.d/kubectl_completion.sh
. /etc/profile.d/kubectl_completion.sh
exit
```

## 3.9 在第一个 master 节点配置网络组件

Kubernetes系统上Pod网络的实现依赖于第三方插件进行，这类插件有近数十种之多，较为著名的有flannel、calico、canal和kube-router等，简单易用的实现是为CoreOS提供的flannel项目。下面的命令用于在线部署flannel至Kubernetes系统之上：首先，下载适配系统及硬件平台环境的flanneld至每个节点，并放置于/opt/bin/目录下。我们这里选用flanneld-amd64，目前最新的版本为v0.19.1，因而，我们需要在集群的每个节点上执行如下命令：

提示：下载flanneld的地址为 https://github.com/flannel-io/flannel/releases

随后，在初始化的第一个master节点k8s-master01上运行如下命令，向Kubernetes部署kube-flannel

```
#默认没有网络插件,所以显示如下状态
[root@master1 ~]#kubectl get nodes 
NAME               STATUS     ROLES           AGE   VERSION
master1.wang.org   NotReady   control-plane   17m   v1.25.0

[root@master1 ~]#kubectl apply -f https://raw.githubusercontent.com/flannelio/flannel/master/Documentation/kube-flannel.yml

#稍等一会儿,可以看到下面状态
[root@master1 ~]#kubectl get nodes 
NAME               STATUS   ROLES           AGE   VERSION
master1.wang.org   Ready   control-plane   23m   v1.25.0
```

## 3.10 将所有 worker 节点加入 Kubernetes 集群

在所有worker节点执行下面操作,加上集群
```
#复制上面第4.8步的执行结果,额外添加--cri-socket选项修改为下面执行
[root@node1 ~]#kubeadm join kubeapi.wang.org:6443 --token ihbe5g.6jxdfwym49epsirr \
 --discovery-token-ca-cert-hash sha256:b7a7abccfc394fe431b8733e05d0934106c0e81abeb0a2bab4d1b7cfd82104c0  --cri-socket unix:///run/cri-dockerd.sock

[preflight] Running pre-flight checks
[preflight] Reading configuration from the cluster...
[preflight] FYI: You can look at this config file with 'kubectl -n kube-system get cm kubeadm-config -o yaml'
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Starting the kubelet
[kubelet-start] Waiting for the kubelet to perform the TLS Bootstrap...

This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.

Run 'kubectl get nodes' on the control-plane to see this node join the cluster.

[root@node1 ~]#docker images
REPOSITORY                                           TAG       IMAGE ID       CREATED         SIZE
rancher/mirrored-flannelcni-flannel                  v0.19.1   252b2c3ee6c8   12days ago      62.3MB
registry.aliyuncs.com/google_containers/kube-proxy   v1.25.0   2ae1ba6417cb   5weeks ago      110MB
rancher/mirrored-flannelcni-flannel-cni-plugin       v1.1.0    fcecffc7ad4a   2months ago     8.09MB
registry.aliyuncs.com/google_containers/pause        3.7       221177c6082a   5months ago     711kB
registry.aliyuncs.com/google_containers/coredns      v1.8.6    a4ca41631cc7   10months ago    46.8MB

#可以将镜像导出到其它worker节点实现加速
[root@node1 ~]#docker image save `docker image ls --format "{{.Repository}}:{{.Tag}}"` -o k8s-images-v1.25.0.tar
[root@node1 ~]#gzip k8s-images-v1.25.0.tar
[root@node1 ~]#scp k8s-images-v1.25.0.tar.gz node2:
[root@node1 ~]#scp k8s-images-v1.25.0.tar.gz node3:
[root@node2 ~]#docker load -i k8s-images-v1.25.0.tar.gz
[root@master1 ~]#kubectl get nodes
NAME               STATUS   ROLES           AGE   VERSION
master1.wang.org   Ready   control-plane   58m   v1.25.0
node1.wang.org     Ready   <none>         44m   v1.25.0
node2.wang.org     Ready   <none>         18m   v1.25.0
node3.wang.org     Ready   <none>         65s   v1.25.0
```

## 3.11 测试应用编排及服务访问

至此一个master附带有三个worker的kubernetes集群基础设施已经部署完成，用户随后即可测试其核心功能。

demoapp是一个web应用,可将demoapp以Pod的形式编排运行于集群之上，并通过在集群外部进行访问：
```
[root@master1 ~]#kubectl create deployment demoapp --image=ikubernetes/demoapp:v1.0 --replicas=3
[root@master1 ~]#kubectl get pod -o wide
NAME                       READY   STATUS   RESTARTS   AGE     IP           NODE             NOMINATED NODE   READINESS GATES
demoapp-78b49597cf-7pdww   1/1     Running   0         2m39s   10.244.2.2   node2.wang.org   <none>           <none>
demoapp-78b49597cf-wcjkp   1/1     Running   0         2m39s   10.244.2.3   node2.wang.org   <none>           <none>
demoapp-78b49597cf-zmlmv   1/1     Running   0         2m39s   10.244.1.4   node3.wang.org   <none>           <none>

[root@master1 ~]#curl 10.244.2.2
iKubernetes demoapp v1.0 !! ClientIP: 10.244.0.0, ServerName: demoapp-78b49597cf-7pdww, ServerIP: 10.244.2.2!

[root@master1 ~]#curl 10.244.2.3
iKubernetes demoapp v1.0 !! ClientIP: 10.244.0.0, ServerName: demoapp-78b49597cf-wcjkp, ServerIP: 10.244.2.3!

[root@master1 ~]#curl 10.244.1.4
iKubernetes demoapp v1.0 !! ClientIP: 10.244.0.0, ServerName: demoapp-78b49597cf-zmlmv, ServerIP: 10.244.1.4!

#使用如下命令了解Service对象demoapp使用的NodePort，格式:<集群端口>:<POd端口>,以便于在集群外部进行访问
[root@master1 ~]#kubectl create service nodeport demoapp --tcp=80:80
[root@master1 ~]#kubectl get svc
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)       AGE
demoapp      NodePort    10.110.101.190   <none>        80:30037/TCP  102s
kubernetes   ClusterIP   10.96.0.1        <none>        443/TCP       67m

[root@master1 ~]#curl 10.110.101.190
iKubernetes demoapp v1.0 !! ClientIP: 10.244.0.0, ServerName: demoapp-78b49597cf-wcjkp, ServerIP: 10.244.2.3!

[root@master1 ~]#curl 10.110.101.190
iKubernetes demoapp v1.0 !! ClientIP: 10.244.0.0, ServerName: demoapp-78b49597cf-zmlmv, ServerIP: 10.244.1.4!

[root@master1 ~]#curl 10.110.101.190
iKubernetes demoapp v1.0 !! ClientIP: 10.244.0.0, ServerName: demoapp-78b49597cf-7pdww, ServerIP: 10.244.2.2!

#用户可以于集群外部通过“http://NodeIP:30037”这个URL访问demoapp上的应用，例如于集群外通过浏览器访问“http://<kubernetes-node>:30037”。
[root@rocky8 ~]#curl 10.0.0.100:30037
iKubernetes demoapp v1.0 !! ClientIP: 10.244.0.0, ServerName: demoapp-78b49597cf-wcjkp, ServerIP: 10.244.2.3!

[root@rocky8 ~]#curl 10.0.0.101:30037
iKubernetes demoapp v1.0 !! ClientIP: 10.244.1.0, ServerName: demoapp-78b49597cf-7pdww, ServerIP: 10.244.2.2!

[root@rocky8 ~]#curl 10.0.0.102:30037
iKubernetes demoapp v1.0 !! ClientIP: 10.244.2.0, ServerName: demoapp-78b49597cf-zmlmv, ServerIP: 10.244.1.4!

#扩容
[root@master1 ~]#kubectl scale deployment demoapp --replicas 5
deployment.apps/demoapp scaled

[root@master1 ~]#kubectl get pod 
NAME                       READY   STATUS   RESTARTS   AGE
demoapp-78b49597cf-44hqj   1/1     Running   0         41m
demoapp-78b49597cf-45jd8   1/1     Running   0         9s
demoapp-78b49597cf-49js5   1/1     Running   0         41m
demoapp-78b49597cf-9lw2z   1/1     Running   0         9s
demoapp-78b49597cf-jtwkt   1/1     Running   0         41m

#缩容
[root@master1 ~]#kubectl scale deployment demoapp --replicas 2
deployment.apps/demoapp scaled

#可以看到销毁pod的过程
[root@master1 ~]#kubectl get pod 
NAME                       READY   STATUS       RESTARTS   AGE
demoapp-78b49597cf-44hqj   1/1     Terminating   0         41m
demoapp-78b49597cf-45jd8   1/1     Terminating   0         53s
demoapp-78b49597cf-49js5   1/1     Running       0         41m
demoapp-78b49597cf-9lw2z   1/1     Terminating   0         53s
demoapp-78b49597cf-jtwkt   1/1     Running       0         41m

#再次查看,最终缩容成功
[root@master1 ~]#kubectl get pod
NAME                       READY   STATUS   RESTARTS   AGE
demoapp-78b49597cf-49js5   1/1     Running   0         42m
demoapp-78b49597cf-jtwkt   1/1     Running   0         42m
```

问题：如果出现创建的Pod在10.88.0.0/网段，导致无法访问Pod
```
[root@master1 ~]#kubectl get pod -o wide
NAME                       READY   STATUS   RESTARTS   AGE     IP           NODE             NOMINATED NODE   READINESS GATES
demoapp-55c5f88dcb-8jqfv   1/1     Running   0         5m25s   10.88.0.2    node4.wang.org   <none>           <none>

[root@node4 ~]#rm -f /etc/cni/net.d/10-containerd-net.conflis
[root@node4 ~]#reboot
```

## 3.12 扩展 Kubernetes 集群为多主模式

```
https://kubernetes.io/zh-cn/docs/setup/production-environment/tools/kubeadm/highavailability/#manual-certs
```

在 master2 和 master3 重复上面的 4.2-4.5 步后,再执行下面操作加入集群
```
[root@master2 ~]#kubeadm join kubeapi.wang.org:6443 --token ihbe5g.6jxdfwym49epsirr \
--discovery-token-ca-cert-hash sha256:b7a7abccfc394fe431b8733e05d0934106c0e81abeb0a2bab4d1b7cfd82104c0 --control-plane \
--certificate-key ae34c01f75e9971253a39543a289cdc651f23222c0e074a6b7ecb2dba667c059 \
--cri-socket unix:///run/cri-dockerd.sock

This node has joined the cluster and a new control plane instance was created:

* Certificate signing request was sent to apiserver and approval was received.
* The Kubelet was informed of the new secure connection details.
* Control plane label and taint were applied to the new node.
* The Kubernetes control plane instances scaled up.
* A new etcd member was added to the local/stacked etcd cluster.

To start administering your cluster from this node, you need to run the 
following as a regular user:

 mkdir -p $HOME/.kube
 sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
 sudo chown $(id -u):$(id -g) $HOME/.kube/config

Run 'kubectl get nodes' to see this node join the cluster.

[root@master2 ~]#mkdir -p $HOME/.kube
[root@master2 ~]#sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
[root@master2 ~]#sudo chown $(id -u):$(id -g) $HOME/.kube/config
[root@master1 ~]#kubectl get nodes
NAME               STATUS    ROLES           AGE     VERSION
master1.wang.org   Ready     control-plane   29m     v1.25.0
master2.wang.org   Ready     control-plane   26m     v1.25.0
master3.wang.org   Ready     control-plane   3m48s   v1.25.0
node1.wang.org     Ready     <none>          19m     v1.25.0
node2.wang.org     Ready     <none>          18m     v1.25.0
node3.wang.org     Ready     <none>          18m     v1.25.0
```

浏览器访问验证,用户名密码: admin:123456
```
http://kubeapi.wang.org:8888/status
```

# 四、Containerd 客户端工具

containerd 的客户端工具有ctr,crictl和 nerdctl

## 4.1 ctr和crictl

`ctr` 是由 containerd 提供的一个客户端工具。

`crictl` 是 CRI 兼容的容器运行时命令行接口，和containerd无关，由Kubernetes提供，可以使用它来检查和调试 k8s 节点上的容器运行时和应用程序。

| **命令** | **docker** | **ctr（containerd）** | **crictl（kubernetes）** |
|----------|------------|-----------------------|--------------------------|
| 查看镜像 | docker images | ctr image ls | crictl images |
| 拉取镜像 | docker pull | ctr image pull | ctictl pull |
| 推送镜像 | docker push c| tr image push | 无 |
| 删除镜像 | docker rmi | ctr image rm | crictl rmi |
| 导入镜像 | docker load | ctr image import | 无 |
| 导出镜像 | docker save | ctr image export | 无 |
| 修改镜像标签 | docker tag | ctr image tag | 无 |
| 创建一个新的容器 | docker create | ctr container create | crictl create |
| 运行一个新的容器 | docker run c| tr run | 无（最小单元为Pod） |
| 删除容器 | docker rm | ctr container rm | crictl rm |
| 查看运行的容器 | docker ps | ctr task ls/ctr container ls | crictl ps |
| 启动已有的容器 | docker start | ctr task start | crictl start |
| 关闭已有的容器 | docker stop | ctr task kill | crictl stop |
| 在容器内部执行命令 | docker exec | 无 | crictl exec |
| 查看容器数信息 | docker inspect | ctr container info | crictl inspect |
| 查看容器日志 | docker logs | 无 | crictl logs |
| 查看容器资源 | docker stats | 无 | crictl stats |

## 4.2 nerdctl

### 4.2.1 nerdctl 介绍

nerdctl 是 与 Docker 兼容的CLI for Containerd，其支持Compose

nerdctl 和 docker命令行语法很相似，学习比较容易

项目地址：https://github.com/containerd/nerdctl

nerdctl 官方发布包包含两个安装版本:
- Minimal: 仅包含 nerdctl 二进制文件以及 rootless 模式下的辅助安装脚本
- Full: 看名字就能知道是个全量包，其包含了 Containerd、CNI、runc、BuildKit 等完整组件

## 4.2.2 nerdctl 安装和使用

### 4.2.2.1 在单机使用 nerdctl 代替 Docker

```
#https://github.com/containerd/nerdctl/releases
#在新主机使用nerdctl/代替docker
[root@ubuntu2004 ~]#wget 
https://github.com/containerd/nerdctl/releases/download/v0.22.2/nerdctl-full0.22.2-linux-amd64.tar.gz
#查看文件内容
[root@ubuntu2004 ~]#tar tf nerdctl-full-0.22.2-linux-amd64.tar.gz 
bin/
bin/buildctl
bin/buildg
bin/buildg.sh
bin/buildkitd
bin/bypass4netns
bin/bypass4netnsd
bin/containerd
bin/containerd-fuse-overlayfs-grpc
bin/containerd-rootless-setuptool.sh
bin/containerd-rootless.sh
bin/containerd-shim-runc-v2
bin/containerd-stargz-grpc
bin/ctd-decoder
bin/ctr
bin/ctr-enc
bin/ctr-remote
bin/fuse-overlayfs
bin/ipfs
bin/nerdctl
bin/rootlessctl
bin/rootlesskit
bin/runc
bin/slirp4netns
bin/tini
lib/
lib/systemd/
lib/systemd/system/
lib/systemd/system/buildkit.service
lib/systemd/system/containerd.service
lib/systemd/system/stargz-snapshotter.service
libexec/
libexec/cni/
libexec/cni/bandwidth
libexec/cni/bridge
libexec/cni/dhcp
libexec/cni/firewall
libexec/cni/host-device
libexec/cni/host-local
libexec/cni/ipvlan
libexec/cni/loopback
libexec/cni/macvlan
libexec/cni/portmap
libexec/cni/ptp
libexec/cni/sbr
libexec/cni/static
libexec/cni/tuning
libexec/cni/vlan
libexec/cni/vrf
share/
share/doc/
share/doc/nerdctl/
share/doc/nerdctl/README.md
share/doc/nerdctl/docs/
share/doc/nerdctl/docs/build.md
share/doc/nerdctl/docs/builder-debug.md
share/doc/nerdctl/docs/cni.md
share/doc/nerdctl/docs/compose.md
share/doc/nerdctl/docs/config.md
share/doc/nerdctl/docs/cosign.md
share/doc/nerdctl/docs/dir.md
share/doc/nerdctl/docs/experimental.md
share/doc/nerdctl/docs/faq.md
share/doc/nerdctl/docs/freebsd.md
share/doc/nerdctl/docs/gpu.md
share/doc/nerdctl/docs/ipfs.md
share/doc/nerdctl/docs/multi-platform.md
share/doc/nerdctl/docs/nydus.md
share/doc/nerdctl/docs/ocicrypt.md
share/doc/nerdctl/docs/overlaybd.md
share/doc/nerdctl/docs/registry.md
share/doc/nerdctl/docs/rootless.md
share/doc/nerdctl/docs/stargz.md
share/doc/nerdctl-full/
share/doc/nerdctl-full/README.md
share/doc/nerdctl-full/SHA256SUMS

[root@ubuntu2004 ~]#tar Cxvf /usr/local nerdctl-full-0.22.2-linux-amd64.tar.gz
[root@ubuntu2004 ~]#systemctl enable --now containerd

#查看用法
[root@ubuntu2004 ~]#nerdctl --help
nerdctl is a command line interface for containerd

Config file ($NERDCTL_TOML): /etc/nerdctl/nerdctl.toml

Usage:
 nerdctl [flags]
 nerdctl [command]
Management  commands:
 apparmor   Manage AppArmor profiles
 builder    Manage builds
 container  Manage containers
 image      Manage images
 ipfs       Distributing images on IPFS
 namespace  Manage containerd namespaces
 network    Manage networks
 system     Manage containerd
 volume     Manage volumes
Commands:
 build      Build an image from a Dockerfile. Needs buildkitd to be running.
 commit     Create a new image from a container's changes
 completion Generate the autocompletion script for the specified shell
 compose    Compose
 cp         Copy files/folders between a running container and the local filesystem.
 create     Create a new container. Optionally specify "ipfs://" or "ipns://"scheme to pull image from IPFS.
 events     Get real time events from the server
 exec       Run a command in a running container
 help       Help about any command
 history    Show the history of an image
 images     List images
 info       Display system-wide information
 inspect    Return low-level information on objects.
 kill       Kill one or more running containers
 load       Load an image from a tar archive or STDIN
 login      Log in to a Docker registry
 logout     Log out from a Docker registry
 logs       Fetch the logs of a container. Currently, only containers created with `nerdctl run -d` are supported.
 pause      Pause all processes within one or more containers
 port       List port mappings or a specific mapping for the container
 ps         List containers
 pull       Pull an image from a registry. Optionally specify "ipfs://" or "ipns://" scheme to pull image from IPFS.
 push       Push an image or a repository to a registry. Optionally specify "ipfs://" or "ipns://" scheme to push image to IPFS.
 rename     rename a container
 restart    Restart one or more running containers
 rm         Remove one or more containers
 rmi        Remove one or more images
 run        Run a command in a new container. Optionally specify "ipfs://" or "ipns://" scheme to pull image from IPFS.
 save       Save one or more images to a tar archive (streamed to STDOUT by default)
 start      Start one or more running containers
 stats      Display a live stream of container(s) resource usage statistics.
 stop       Stop one or more running containers
 tag        Create a tag TARGET_IMAGE that refers to SOURCE_IMAGE
 top        Display the running processes of a container
 unpause    Unpause all processes within one or more containers
 update     Update one or more running containers
 version    Show the nerdctl version information
 wait       Block until one or more containers stop, then print their exit codes.

Flags:
  -H, --H string                 Alias of --address (default "/run/containerd/containerd.sock")
  -a, --a string                 Alias of --address (default "/run/containerd/containerd.sock")
      --address string           containerd address, optionally with "unix://"prefix [$CONTAINERD_ADDRESS] (default "/run/containerd/containerd.sock")
      --cgroup-manager string   Cgroup manager to use ("cgroupfs"|"systemd") (default "cgroupfs")
      --cni-netconfpath string   cni config directory [$NETCONFPATH] (default "/etc/cni/net.d")
      --cni-path string         cni plugins binary directory [$CNI_PATH] (default "/opt/cni/bin")
      --data-root string         Root directory of persistent nerdctl state (managed by nerdctl, not by containerd) (default "/var/lib/nerdctl")
      --debug                   debug mode
      --debug-full               debug mode (with full output)
  -h, --help                     help for nerdctl
      --host string             Alias of --address (default "/run/containerd/containerd.sock")
      --hosts-dir strings       A directory that contains <HOST:PORT>/hosts.toml (containerd style) or <HOST:PORT>/{ca.cert, cert.pem, key.pem} (docker style) (default [/etc/containerd/certs.d,/etc/docker/certs.d])
      --insecure-registry       skips verifying HTTPS certs, and allows falling back to plain HTTP
  -n, --n string                 Alias of --namespace (default "default")
      --namespace string         containerd namespace, such as "moby" forDocker, "k8s.io" for Kubernetes [$CONTAINERD_NAMESPACE] (default "default")
      --snapshotter string       containerd snapshotter [$CONTAINERD_SNAPSHOTTER] (default "overlayfs")
      --storage-driver string   Alias of --snapshotter (default "overlayfs")
  -v, --version                 version for nerdctl

Use "nerdctl [command] --help" for more information about a command.

[root@ubuntu2004 ~]#nerdctl run -d --name nginx -p 80:80 nginx:alpine
[root@ubuntu2004 ~]#nerdctl ps
CONTAINER ID   IMAGE                             COMMAND                   CREATED         STATUS   PORTS                 NAMES
4dc4a4e4d872   docker.io/library/nginx:alpine    "/docker-entrypoint.…"    5seconds ago   Up        0.0.0.0:80->80/tcp    nginx
[root@ubuntu2004 ~]#curl 127.0.0.1
```

#### 4.2.2.2 在 Kubernetes 集群中使用 nerdctl
```
#在使用containerd的kubernetes环境中安装nerdctl
[root@node2 ~]#wget https://github.com/containerd/nerdctl/releases/download/v0.22.2/nerdctl-0.22.2-linux-amd64.tar.gz

#查看文件内容
[root@node2 ~]#tar tf nerdctl-0.22.2-linux-amd64.tar.gz
nerdctl
containerd-rootless-setuptool.sh
containerd-rootless.sh

#安装至指定目录
[root@node2 ~]#tar xf nerdctl-0.22.2-linux-amd64.tar.gz -C /usr/local/bin/
[root@node2 ~]#ls /usr/local/bin/
containerd-rootless-setuptool.sh containerd-rootless.sh nerdctl

#注意：加-n k8s.io 选项才能查看到k8s的名称空间的镜像和容器
#查看k8s名称空间的镜像
[root@node2 ~]#nerdctl -n k8s.io images

#查看k8s名称空间的容器
[root@node2 ~]#nerdctl -n k8s.io ps

#查看默认名称空间default的镜像
[root@node2 ~]#nerdctl images

#查看默认名称空间default的容器
[root@node2 ~]#nerdctl ps

#如果是使用apt安装的cni插件创建容器时会出下面错误
[root@node2 ~]#nerdctl run -d --name nginx -p 80:80 nginx:alpine
            
FATA[0010] failed to create shim: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error running hook #0: error running hook: exit status 1, stdout: , stderr: time="2022-09-10T12:56:43Z" level=fatal msg="failed to call cni.Setup: plugin type=\"bridge\" 
failed (add): incompatible CNI versions; config is \"1.0.0\", plugin supports [\"0.1.0\" \"0.2.0\" \"0.3.0\" \"0.3.1\" \"0.4.0\"]"
Failed to write to log, write
/var/lib/nerdctl/1935db59/containers/default/206d99263af985df7dce896e29451d8ee31234fd0a55b19eb3bde39d2b1bfdd9/oci-hook.createRuntime.log: file already closed: unknown 

[root@node2 ~]#mv /opt/cni/bin/* /srv

#下载cni插件
[root@node2 ~]#wget https://github.com/containernetworking/plugins/releases/download/v1.1.1/cni-plugins-linux-amd64-v1.1.1.tgz
[root@node2 ~]#tar xf cni-plugins-linux-amd64-v1.1.1.tgz -C /opt/cni/bin/

#启动成功
[root@node2 ~]#nerdctl start nginx

#或者删除再启动成功
[root@node2 ~]#nerdctl run -d --name nginx -p 80:80 nginx:alpine
FATA[0000] name "nginx" is already used by ID "206d99263af985df7dce896e29451d8ee31234fd0a55b19eb3bde39d2b1bfdd9"

[root@node2 ~]#nerdctl rm -f nginx
nginx

[root@node2 ~]#nerdctl run -d --name nginx -p 80:80 nginx:alpine
6b7ea18022d3e1293a5149f316742af093e061f3a968eb80762d5fd976dec595

[root@node2 ~]#nerdctl ps 
CONTAINER ID   IMAGE                             COMMAND                   CREATED        STATUS   PORTS                 NAMES
94bdff6354c0   docker.io/library/nginx:alpine    "/docker-entrypoint.…"    4seconds ago   Up        0.0.0.0:80->80/tcp   nginx
```

# install_kubernetes_containerd.sh
```
#!/bin/bash
#说明:安装Kubernetes服务器内存建议至少2G

KUBE_VERSION="1.25.0"
#KUBE_VERSION="1.24.4"
#KUBE_VERSION="1.24.3"
#KUBE_VERSION="1.24.0"

KUBE_VERSION2=$(echo $KUBE_VERSION |awk -F. '{print $2}')

KUBEAPI_IP=10.0.0.100
MASTER1_IP=10.0.0.101
MASTER2_IP=10.0.0.102
MASTER3_IP=10.0.0.103
NODE1_IP=10.0.0.104
NODE2_IP=10.0.0.105
NODE3_IP=10.0.0.106
HARBOR_IP=10.0.0.200

DOMAIN=wang.org

MASTER1=master1.$DOMAIN
MASTER2=master2.$DOMAIN
MASTER3=master3.$DOMAIN
NODE1=node1.$DOMAIN
NODE2=node2.$DOMAIN
NODE3=node3.$DOMAIN
HARBOR=harbor.$DOMAIN

POD_NETWORK="10.244.0.0/16"
SERVICE_NETWORK="10.96.0.0/12"

IMAGES_URL="registry.aliyuncs.com/google_containers"


LOCAL_IP=`hostname -I|awk '{print $1}'`

. /etc/os-release

COLOR_SUCCESS="echo -e \\033[1;32m"
COLOR_FAILURE="echo -e \\033[1;31m"
END="\033[m"


color () {
    RES_COL=60
    MOVE_TO_COL="echo -en \\033[${RES_COL}G"
    SETCOLOR_SUCCESS="echo -en \\033[1;32m"
    SETCOLOR_FAILURE="echo -en \\033[1;31m"
    SETCOLOR_WARNING="echo -en \\033[1;33m"
    SETCOLOR_NORMAL="echo -en \E[0m"
    echo -n "$1" && $MOVE_TO_COL
    echo -n "["
    if [ $2 = "success" -o $2 = "0" ] ;then
        ${SETCOLOR_SUCCESS}
        echo -n $"  OK  "    
    elif [ $2 = "failure" -o $2 = "1"  ] ;then 
        ${SETCOLOR_FAILURE}
        echo -n $"FAILED"
    else
        ${SETCOLOR_WARNING}
        echo -n $"WARNING"
    fi
    ${SETCOLOR_NORMAL}
    echo -n "]"
    echo 
}

check () {
    if [ $ID = 'ubuntu' -a ${VERSION_ID} = "20.04"  ];then
        true
    else
        color "不支持此操作系统，退出!" 1
        exit
    fi
    if [ $KUBE_VERSION2 -lt 24 ] ;then 
        color "当前kubernetes版本过低，Containerd要求不能低于v1.24.0版，退出!" 1
        exit
    fi
}



install_prepare () {
    cat >> /etc/hosts <<EOF

$KUBEAPI_IP kubeapi.$DOMAIN
$MASTER1_IP $MASTER1
$MASTER2_IP $MASTER2
$MASTER3_IP $MASTER3
$NODE1_IP $NODE1
$NODE2_IP $NODE2
$NODE3_IP $NODE3
$HARBOR_IP $HARBOR
EOF
    hostnamectl set-hostname $(awk -v ip=$LOCAL_IP '{if($1==ip && $2 !~ "kubeapi")print $2}' /etc/hosts)
    swapoff -a
    sed -i '/swap/s/^/#/' /etc/fstab
    color "安装前准备完成!" 0
    sleep 1
}

config_kernel () {
    cat <<EOF | tee /etc/modules-load.d/k8s.conf
    overlay
    br_netfilter
EOF

    modprobe overlay
    modprobe br_netfilter

    cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
    sysctl --system
}

install_containerd () {
    apt update
    apt -y install containerd || { color "安装Containerd失败!" 1; exit 1; }
    mkdir /etc/containerd/
    containerd config default > /etc/containerd/config.toml
    sed -i "s#k8s.gcr.io#${IMAGES_URL}#g"  /etc/containerd/config.toml
    #sed -i 's#SystemdCgroup = false#SystemdCgroup = true#g' /etc/containerd/config.toml
    systemctl restart containerd.service
    [ $? -eq 0 ] && { color "安装Containerd成功!" 0; sleep 1; } || { color "安装Containerd失败!" 1 ; exit 2; }
}

install_kubeadm () {
    apt-get update && apt-get install -y apt-transport-https
    curl https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add - 
    cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main
EOF
    apt-get update
    apt-cache madison kubeadm |head
    ${COLOR_FAILURE}"5秒后即将安装: kubeadm-"${KUBE_VERSION}" 版本....."${END}
    ${COLOR_FAILURE}"如果想安装其它版本，请按ctrl+c键退出，修改版本再执行"${END}
    sleep 6

    #安装指定版本
    apt install -y  kubeadm=${KUBE_VERSION}-00 kubelet=${KUBE_VERSION}-00 kubectl=${KUBE_VERSION}-00
    [ $? -eq 0 ] && { color "安装kubeadm成功!" 0;sleep 1; } || { color "安装kubeadm失败!" 1 ; exit 2; }
    
    #实现kubectl命令自动补全功能    
    kubectl completion bash > /etc/profile.d/kubectl_completion.sh
}

#只有Kubernetes集群的第一个master节点需要执行下面初始化函数
kubernetes_init () {
    kubeadm init --control-plane-endpoint="kubeapi.$DOMAIN" \
                 --kubernetes-version=v${KUBE_VERSION}  \
                 --pod-network-cidr=${POD_NETWORK} \
                 --service-cidr=${SERVICE_NETWORK} \
                 --token-ttl=0  \
                 --upload-certs \
                 --image-repository=${IMAGES_URL} 
    [ $? -eq 0 ] && color "Kubernetes集群初始化成功!" 0 || { color "Kubernetes集群初始化失败!" 1 ; exit 3; }
    mkdir -p $HOME/.kube
    cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    chown $(id -u):$(id -g) $HOME/.kube/config
}

reset_kubernetes() {
    kubeadm reset -f --cri-socket unix:///run/cri-dockerd.sock
    rm -rf  /etc/cni/net.d/  $HOME/.kube/config
}

config_crictl () {
    cat > /etc/crictl.yaml <<EOF
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
EOF

}

check 

PS3="请选择编号(1-4): "
ACTIONS="
初始化新的Kubernetes集群
加入已有的Kubernetes集群
退出Kubernetes集群
退出本程序
"
select action in $ACTIONS;do
    case $REPLY in 
    1)
        install_prepare
        config_kernel
        install_containerd
        install_kubeadm
        kubernetes_init
        config_crictl
        break
        ;;
    2)
        install_prepare
        config_kernel
        install_containerd
        install_kubeadm
        $COLOR_SUCCESS"加入已有的Kubernetes集群已准备完毕,还需要执行最后一步加入集群的命令 kubeadm join ... "${END}
        break
        ;;
    3)
        reset_kubernetes
        break
        ;;
    4)
        exit
        ;;
    esac
done
exec bash
```

# kube-flannel-v0.19.1.yml
```
---
kind: Namespace
apiVersion: v1
metadata:
  name: kube-flannel
  labels:
    pod-security.kubernetes.io/enforce: privileged
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: flannel
rules:
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
- apiGroups:
  - ""
  resources:
  - nodes
  verbs:
  - list
  - watch
- apiGroups:
  - ""
  resources:
  - nodes/status
  verbs:
  - patch
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: flannel
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flannel
subjects:
- kind: ServiceAccount
  name: flannel
  namespace: kube-flannel
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flannel
  namespace: kube-flannel
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: kube-flannel-cfg
  namespace: kube-flannel
  labels:
    tier: node
    app: flannel
data:
  cni-conf.json: |
    {
      "name": "cbr0",
      "cniVersion": "0.3.1",
      "plugins": [
        {
          "type": "flannel",
          "delegate": {
            "hairpinMode": true,
            "isDefaultGateway": true
          }
        },
        {
          "type": "portmap",
          "capabilities": {
            "portMappings": true
          }
        }
      ]
    }
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "Backend": {
        "Type": "vxlan"
      }
    }
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: kube-flannel-ds
  namespace: kube-flannel
  labels:
    tier: node
    app: flannel
spec:
  selector:
    matchLabels:
      app: flannel
  template:
    metadata:
      labels:
        tier: node
        app: flannel
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: kubernetes.io/os
                operator: In
                values:
                - linux
      hostNetwork: true
      priorityClassName: system-node-critical
      tolerations:
      - operator: Exists
        effect: NoSchedule
      serviceAccountName: flannel
      initContainers:
      - name: install-cni-plugin
       #image: flannelcni/flannel-cni-plugin:v1.1.0 for ppc64le and mips64le (dockerhub limitations may apply)
        image: docker.io/rancher/mirrored-flannelcni-flannel-cni-plugin:v1.1.0
        command:
        - cp
        args:
        - -f
        - /flannel
        - /opt/cni/bin/flannel
        volumeMounts:
        - name: cni-plugin
          mountPath: /opt/cni/bin
      - name: install-cni
       #image: flannelcni/flannel:v0.19.1 for ppc64le and mips64le (dockerhub limitations may apply)
        image: docker.io/rancher/mirrored-flannelcni-flannel:v0.19.1
        command:
        - cp
        args:
        - -f
        - /etc/kube-flannel/cni-conf.json
        - /etc/cni/net.d/10-flannel.conflist
        volumeMounts:
        - name: cni
          mountPath: /etc/cni/net.d
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
      containers:
      - name: kube-flannel
       #image: flannelcni/flannel:v0.19.1 for ppc64le and mips64le (dockerhub limitations may apply)
        image: docker.io/rancher/mirrored-flannelcni-flannel:v0.19.1
        command:
        - /opt/bin/flanneld
        args:
        - --ip-masq
        - --kube-subnet-mgr
        resources:
          requests:
            cpu: "100m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "50Mi"
        securityContext:
          privileged: false
          capabilities:
            add: ["NET_ADMIN", "NET_RAW"]
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: EVENT_QUEUE_DEPTH
          value: "5000"
        volumeMounts:
        - name: run
          mountPath: /run/flannel
        - name: flannel-cfg
          mountPath: /etc/kube-flannel/
        - name: xtables-lock
          mountPath: /run/xtables.lock
      volumes:
      - name: run
        hostPath:
          path: /run/flannel
      - name: cni-plugin
        hostPath:
          path: /opt/cni/bin
      - name: cni
        hostPath:
          path: /etc/cni/net.d
      - name: flannel-cfg
        configMap:
          name: kube-flannel-cfg
      - name: xtables-lock
        hostPath:
          path: /run/xtables.lock
          type: FileOrCreate
```
