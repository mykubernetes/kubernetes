# 一、实践环境准备
## 1. 服务器说明
我们这里使用的是五台centos 7.2实体机，具体信息如下表：

| 系统类型 | IP地址 | 节点角色 | CPU | Memory | Hostname |
| :------: | :--------: | :-------: | :-----: | :---------: | :-----: |
| centos-7.2 | 192.168.101.69 | master |   \>=2    | \>=2G | node01 |
| centos-7.2 | 192.168.101.70 | master |   \>=2    | \>=2G | node02 |
| centos-7.2 | 192.168.101.71 | master |   \>=2    | \>=2G | node03 |
| centos-7.2 | 192.168.101.72 | worker |   \>=2    | \>=2G | node04 |
| centos-7.2 | 192.168.101.73 | worker |   \>=2    | \>=2G | node05 |

## 2. 系统设置（所有节点）
#### 2.1 主机名
主机名必须每个节点都不一样，并且保证所有点之间可以通过hostname互相访问。
```bash
# 查看主机名
$ hostname

# 修改主机名
$ hostnamectl set-hostname <your_hostname>

# 配置host，使主节点之间可以通过hostname互相访问
$ vi /etc/hosts
# <node-ip> <node-hostname>
```
#### 2.2 安装依赖包
```bash
# 更新yum
$ yum update

# 安装依赖包
$ yum install -y conntrack ipvsadm ipset jq sysstat curl iptables libseccomp
```
#### 2.3 关闭防火墙、swap，重置iptables
```bash
# 关闭防火墙
$ systemctl stop firewalld && systemctl disable firewalld

# 重置iptables
$ iptables -F && iptables -X && iptables -F -t nat && iptables -X -t nat && iptables -P FORWARD ACCEPT

# 关闭swap
$ swapoff -a
$ sed -i '/swap/s/^\(.*\)$/#\1/g' /etc/fstab

# 关闭selinux
$ setenforce 0

# 关闭dnsmasq(否则可能导致docker容器无法解析域名)
$ service dnsmasq stop && systemctl disable dnsmasq
```
#### 2.4 系统参数设置

```bash
# 制作配置文件
$ cat > /etc/sysctl.d/kubernetes.conf <<EOF
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
net.ipv4.ip_forward=1
vm.swappiness=0
vm.overcommit_memory=1
vm.panic_on_oom=0
fs.inotify.max_user_watches=89100
EOF

# 生效文件
$ sysctl -p /etc/sysctl.d/kubernetes.conf
```
## 3. 安装docker（worker节点）
根据kubernetes对docker版本的兼容测试情况，我们选择17.03.1版本
由于近期docker官网速度极慢甚至无法访问，使用yum安装很难成功。我们直接使用rpm方式安装
```bash
# 手动下载rpm包
$ mkdir -p /opt/kubernetes/docker && cd /opt/kubernetes/docker
$ wget http://yum.dockerproject.org/repo/main/centos/7/Packages/docker-engine-selinux-17.03.1.ce-1.el7.centos.noarch.rpm
$ wget http://yum.dockerproject.org/repo/main/centos/7/Packages/docker-engine-17.03.1.ce-1.el7.centos.x86_64.rpm
$ wget http://yum.dockerproject.org/repo/main/centos/7/Packages/docker-engine-debuginfo-17.03.1.ce-1.el7.centos.x86_64.rpm

# 清理原有版本
$ yum remove -y docker* container-selinux

# 安装rpm包
$ yum localinstall -y *.rpm

# 开机启动
$ systemctl enable docker

# 设置参数
# 1.查看磁盘挂载
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G  2.8G   95G   3% /
devtmpfs         63G     0   63G   0% /dev
/dev/sda5      1015G  8.8G 1006G   1% /tol
/dev/sda1       197M  161M   37M  82% /boot

# 2.选择比较大的分区（我这里是/tol）
$ mkdir -p /tol/docker-data
$ cat <<EOF > /etc/docker/daemon.json
{
    "graph": "/tol/docker-data"
}
EOF

# 启动docker服务
service docker restart
```

## 4. 准备二进制文件（所有节点）
#### 4.1 配置免密登录
为了方便文件的copy我们选择一个中转节点（随便一个节点，可以是集群中的也可以是非集群中的），配置好跟其他所有节点的免密登录
```bash
# 看看是否已经存在rsa公钥
$ cat ~/.ssh/id_rsa.pub

# 如果不存在就创建一个新的
$ ssh-keygen -t rsa

# 把id_rsa.pub文件内容copy到其他机器的授权文件中
$ cat ~/.ssh/id_rsa.pub

# 在其他节点执行下面命令（包括worker节点）
$ echo "<file_content>" >> ~/.ssh/authorized_keys
```

#### 4.2 下载二进制文件
官方下载地址（在CHANGELOG链接里面）：
https://github.com/kubernetes/kubernetes/releases

网盘下载地址--推荐（我从官网下载整理好的文件）：
> 链接: https://pan.baidu.com/s/1_w9vyQaDGLKDOf_TU2Xu8Q  
  提取码: vca8

#### 4.3 分发文件并设置好PATH
```bash
# 把文件copy到每个节点上（注意替换自己的文件目录）
$ ssh <user>@<node-ip> "mkdir -p /opt/kubernetes/bin"
$ scp master/* <user>@<master-ip>:/opt/kubernetes/bin/
$ scp worker/* <user>@<worker-ip>:/opt/kubernetes/bin/

# 给每个节点设置PATH
$ ssh <user>@<node-ip> "echo 'PATH=/opt/kubernetes/bin:$PATH' >>~/.bashrc"

# 给自己设置path，后面会用到kubectl命令
$ vi ~/.bash_profile
```

## 5. 准备配置文件（中转节点）
上一步我们下载了kubernetes各个组件的二进制文件，这些可执行文件的运行也是需要添加很多参数的，包括有的还会依赖一些配置文件。现在我们就把运行它们需要的参数和配置文件都准备好。
#### 5.1 下载配置文件
我这准备了一个项目，专门为大家按照自己的环境生成配置的。它只是帮助大家尽量的减少了机械化的重复工作。它并不会帮你设置系统环境，不会给你安装软件。总之就是会减少你的部署工作量，但不会耽误你对整个系统的认识和把控。
```bash
$ cd ~
$ git clone https://gitee.com/pa/kubernetes-ha-binary.git

# 看看git内容
$ ls -l kubernetes-ha-binary
addons/
configs/
pki/
services/
init.sh
global-configs.properties
```
#### 5.2 文件说明
- **addons**
> kubernetes的插件目录，包括calico、coredns、dashboard等。

- **configs**
> 这个目录比较 - 凌乱，包含了部署集群过程中用到的杂七杂八的配置文件、脚本文件等。

- **pki**
> 各个组件的认证授权相关证书配置。

- **services**
> 所有的kubernetes服务(service)配置文件。

- **global-configs.properties**
> 全局配置，包含各种易变的配置内容。

- **init.sh**
> 初始化脚本，配置好global-config之后，会自动生成所有配置文件。

#### 5.3 生成配置
这里会根据大家各自的环境生成kubernetes部署过程需要的配置文件。
在每个节点上都生成一遍，把所有配置都生成好，后面会根据节点类型去使用相关的配置。
```bash
# cd到之前下载的git代码目录
$ cd kubernetes-ha-binary

# 编辑属性配置（根据文件注释中的说明填写好每个key-value）
$ vi global-config.properties

# 生成配置文件，确保执行过程没有异常信息
$ ./init.sh

# 查看生成的配置文件，确保脚本执行成功
$ find target/ -type f
```
> **执行init.sh常见问题：**
> 1. Syntax error: "(" unexpected
> - bash版本过低，运行：bash -version查看版本，如果小于4需要升级
> - 不要使用 sh init.sh的方式运行（sh和bash可能不一样哦）
> 2. config.properties文件填写错误，需要重新生成
> 再执行一次./init.sh即可，不需要手动删除target

# 二、高可用集群部署
## 1. CA证书（任意节点）
#### 1.1 安装cfssl
cfssl是非常好用的CA工具，我们用它来生成证书和秘钥文件
安装过程比较简单，如下：
```bash
# 下载
$ mkdir -p ~/bin
$ wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 -O ~/bin/cfssl
$ wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64 -O ~/bin/cfssljson

# 修改为可执行权限
$ chmod +x ~/bin/cfssl ~/bin/cfssljson

# 设置PATH
$ vim ~/.bash_profile
export PATH=$PATH:~/bin
$ source ~/.bash_profile

# 验证
$ cfssl version
```
#### 1.2 生成根证书
根证书是集群所有节点共享的，只需要创建一个 CA 证书，后续创建的所有证书都由它签名。
```bash
# 生成证书和私钥
$ cd target/pki
$ cfssl gencert -initca ca-csr.json | cfssljson -bare ca

# 生成完成后会有以下文件（我们最终想要的就是ca-key.pem和ca.pem，一个秘钥，一个证书）
$ ls
ca-config.json  ca.csr  ca-csr.json  ca-key.pem  ca.pem

# 创建目录
$ ssh <user>@<node-ip> "mkdir -p /etc/kubernetes/pki/"

# 分发到每个主节点
$ scp ca*.pem <user>@<node-ip>:/etc/kubernetes/pki/

```
## 2. 部署etcd集群（master节点）
#### 2.1 下载etcd
如果你是从网盘下载的二进制可以跳过这一步（网盘中已经包含了etcd，不需要另外下载）。
没有从网盘下载bin文件的话需要自己下载etcd
```bash
$ wget https://github.com/coreos/etcd/releases/download/v3.2.18/etcd-v3.2.18-linux-amd64.tar.gz
```
#### 2.2 生成证书和私钥
```bash
# 生成证书、私钥
$ cd target/pki/etcd
$ cfssl gencert -ca=../ca.pem \
    -ca-key=../ca-key.pem \
    -config=../ca-config.json \
    -profile=kubernetes etcd-csr.json | cfssljson -bare etcd

# 分发到每个etcd节点
$ scp etcd*.pem <user>@<node-ip>:/etc/kubernetes/pki/
```
#### 2.3 创建service文件
```bash
# scp配置文件到每个master节点
$ scp target/<node-ip>/services/etcd.service <node-ip>:/etc/systemd/system/

# 创建数据和工作目录
$ ssh <user>@<node-ip> "mkdir -p /var/lib/etcd"
```
#### 2.4 启动服务
etcd 进程首次启动时会等待其它节点的 etcd 加入集群，命令 systemctl start etcd 会卡住一段时间，为正常现象。
```bash
#启动服务
$ systemctl daemon-reload && systemctl enable etcd && systemctl restart etcd

#查看状态
$ service etcd status

#查看启动日志
$ journalctl -f -u etcd
```


## 3. 部署api-server（master节点）
#### 3.1 生成证书和私钥
```bash
# 生成证书、私钥
$ cd target/pki/apiserver
$ cfssl gencert -ca=../ca.pem \
  -ca-key=../ca-key.pem \
  -config=../ca-config.json \
  -profile=kubernetes kubernetes-csr.json | cfssljson -bare kubernetes

# 分发到每个master节点
$ scp kubernetes*.pem <user>@<node-ip>:/etc/kubernetes/pki/
```

#### 3.2 创建service文件
```bash
# scp配置文件到每个master节点
$ scp target/<node-ip>/services/kube-apiserver.service <user>@<node-ip>:/etc/systemd/system/

# 创建日志目录
$ ssh <user>@<node-ip> "mkdir -p /var/log/kubernetes"
```
#### 3.3 启动服务
```bash
#启动服务
$ systemctl daemon-reload && systemctl enable kube-apiserver && systemctl restart kube-apiserver

#查看运行状态
$ service kube-apiserver status

#查看日志
$ journalctl -f -u kube-apiserver

#检查监听端口
$ netstat -ntlp
```

## 4. 部署keepalived - apiserver高可用（master节点）
#### 4.1 安装keepalived
```bash
# 在两个主节点上安装keepalived（一主一备）
$ yum install -y keepalived
```
#### 4.2 创建keepalived配置文件
```bash
# 创建目录
$ ssh <user>@<master-ip> "mkdir -p /etc/keepalived"
$ ssh <user>@<backup-ip> "mkdir -p /etc/keepalived"

# 分发配置文件
$ scp target/configs/keepalived-master.conf <user>@<master-ip>:/etc/keepalived/keepalived.conf
$ scp target/configs/keepalived-backup.conf <user>@<backup-ip>:/etc/keepalived/keepalived.conf

# 分发监测脚本
$ scp target/configs/check-apiserver.sh <user>@<master-ip>:/etc/keepalived/
$ scp target/configs/check-apiserver.sh <user>@<backup-ip>:/etc/keepalived/
```

#### 4.3 启动keepalived
```bash
# 分别在master和backup上启动服务
$ systemctl enable keepalived && service keepalived start

# 检查状态
$ service keepalived status

# 查看日志
$ journalctl -f -u keepalived

# 访问测试
$ curl --insecure https://<master-vip>:6443/
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {
    
  },
  "status": "Failure",
  "message": "Unauthorized",
  "reason": "Unauthorized",
  "code": 401
```

## 5. 部署kubectl（任意节点）
kubectl 是 kubernetes 集群的命令行管理工具，它默认从 ~/.kube/config 文件读取 kube-apiserver 地址、证书、用户名等信息。
#### 5.1 创建 admin 证书和私钥
kubectl 与 apiserver https 安全端口通信，apiserver 对提供的证书进行认证和授权。
kubectl 作为集群的管理工具，需要被授予最高权限。这里创建具有最高权限的 admin 证书。
```bash
# 创建证书、私钥
$ cd target/pki/admin
$ cfssl gencert -ca=../ca.pem \
  -ca-key=../ca-key.pem \
  -config=../ca-config.json \
  -profile=kubernetes admin-csr.json | cfssljson -bare admin
```
#### 5.2 创建kubeconfig配置文件
kubeconfig 为 kubectl 的配置文件，包含访问 apiserver 的所有信息，如 apiserver 地址、CA 证书和自身使用的证书
```bash
# 设置集群参数
$ kubectl config set-cluster kubernetes \
  --certificate-authority=../ca.pem \
  --embed-certs=true \
  --server=https://<MASTER_VIP>:6443 \
  --kubeconfig=kube.config

# 设置客户端认证参数
$ kubectl config set-credentials admin \
  --client-certificate=admin.pem \
  --client-key=admin-key.pem \
  --embed-certs=true \
  --kubeconfig=kube.config

# 设置上下文参数
$ kubectl config set-context kubernetes \
  --cluster=kubernetes \
  --user=admin \
  --kubeconfig=kube.config
  
# 设置默认上下文
$ kubectl config use-context kubernetes --kubeconfig=kube.config

# 分发到目标节点
$ scp kube.config <user>@<node-ip>:~/.kube/config
```
#### 5.3 授予 kubernetes 证书访问 kubelet API 的权限
在执行 kubectl exec、run、logs 等命令时，apiserver 会转发到 kubelet。这里定义 RBAC 规则，授权 apiserver 调用 kubelet API。
```bash
$ kubectl create clusterrolebinding kube-apiserver:kubelet-apis --clusterrole=system:kubelet-api-admin --user kubernetes
```

#### 5.4 小测试
```bash
# 查看集群信息
$ kubectl cluster-info
$ kubectl get all --all-namespaces
$ kubectl get componentstatuses
```

## 6. 部署controller-manager（master节点）
controller-manager启动后将通过竞争选举机制产生一个 leader 节点，其它节点为阻塞状态。当 leader 节点不可用后，剩余节点将再次进行选举产生新的 leader 节点，从而保证服务的可用性。
#### 6.1 创建证书和私钥
```bash
# 生成证书、私钥
$ cd target/pki/controller-manager
$ cfssl gencert -ca=../ca.pem \
  -ca-key=../ca-key.pem \
  -config=../ca-config.json \
  -profile=kubernetes controller-manager-csr.json | cfssljson -bare controller-manager
# 分发到每个master节点
$ scp controller-manager*.pem <user>@<node-ip>:/etc/kubernetes/pki/
```

#### 6.2 创建controller-manager的kubeconfig
```bash
# 创建kubeconfig
$ kubectl config set-cluster kubernetes \
  --certificate-authority=../ca.pem \
  --embed-certs=true \
  --server=https://<MASTER_VIP>:6443 \
  --kubeconfig=controller-manager.kubeconfig

$ kubectl config set-credentials system:kube-controller-manager \
  --client-certificate=controller-manager.pem \
  --client-key=controller-manager-key.pem \
  --embed-certs=true \
  --kubeconfig=controller-manager.kubeconfig

$ kubectl config set-context system:kube-controller-manager \
  --cluster=kubernetes \
  --user=system:kube-controller-manager \
  --kubeconfig=controller-manager.kubeconfig

$ kubectl config use-context system:kube-controller-manager --kubeconfig=controller-manager.kubeconfig

# 分发controller-manager.kubeconfig
$ scp controller-manager.kubeconfig <user>@<node-ip>:/etc/kubernetes/

```
#### 6.3 创建service文件
```bash
# scp配置文件到每个master节点
$ scp target/services/kube-controller-manager.service <user>@<node-ip>:/etc/systemd/system/
```
#### 6.4 启动服务
```bash
# 启动服务
$ systemctl daemon-reload && systemctl enable kube-controller-manager && systemctl restart kube-controller-manager

# 检查状态
$ service kube-controller-manager status

# 查看日志
$ journalctl -f -u kube-controller-manager

# 查看leader
$ kubectl get endpoints kube-controller-manager --namespace=kube-system -o yaml
```

## 7. 部署scheduler（master节点）
scheduler启动后将通过竞争选举机制产生一个 leader 节点，其它节点为阻塞状态。当 leader 节点不可用后，剩余节点将再次进行选举产生新的 leader 节点，从而保证服务的可用性。
#### 7.1 创建证书和私钥
```bash
# 生成证书、私钥
$ cd target/pki/scheduler
$ cfssl gencert -ca=../ca.pem \
  -ca-key=../ca-key.pem \
  -config=../ca-config.json \
  -profile=kubernetes scheduler-csr.json | cfssljson -bare kube-scheduler
```

#### 7.2 创建scheduler的kubeconfig
```bash
# 创建kubeconfig
$ kubectl config set-cluster kubernetes \
  --certificate-authority=../ca.pem \
  --embed-certs=true \
  --server=https://<MASTER_VIP>:6443 \
  --kubeconfig=kube-scheduler.kubeconfig

$ kubectl config set-credentials system:kube-scheduler \
  --client-certificate=kube-scheduler.pem \
  --client-key=kube-scheduler-key.pem \
  --embed-certs=true \
  --kubeconfig=kube-scheduler.kubeconfig

$ kubectl config set-context system:kube-scheduler \
  --cluster=kubernetes \
  --user=system:kube-scheduler \
  --kubeconfig=kube-scheduler.kubeconfig

$ kubectl config use-context system:kube-scheduler --kubeconfig=kube-scheduler.kubeconfig

# 分发kubeconfig
$ scp kube-scheduler.kubeconfig <user>@<node-ip>:/etc/kubernetes/
```
#### 7.3 创建service文件
```bash
# scp配置文件到每个master节点
$ scp target/services/kube-scheduler.service <user>@<node-ip>:/etc/systemd/system/
```
#### 7.4 启动服务
```bash
# 启动服务
$ systemctl daemon-reload && systemctl enable kube-scheduler && systemctl restart kube-scheduler

# 检查状态
$ service kube-scheduler status

# 查看日志
$ journalctl -f -u kube-scheduler

# 查看leader
$ kubectl get endpoints kube-scheduler --namespace=kube-system -o yaml
```

## 8. 部署kubelet（worker节点）
#### 8.1 预先下载需要的镜像
```bash
# 预先下载镜像到所有节点（由于镜像下载的速度过慢，我给大家提供了阿里云仓库的镜像）
$ scp target/configs/download-images.sh <user>@<node-ip>:~

# 在目标节点上执行脚本下载镜像
$ sh ~/download-images.sh
```
#### 8.2 创建bootstrap配置文件
```bash
# 创建 token
$ cd target/pki/admin
$ export BOOTSTRAP_TOKEN=$(kubeadm token create \
      --description kubelet-bootstrap-token \
      --groups system:bootstrappers:worker \
      --kubeconfig kube.config)
      
# 设置集群参数
$ kubectl config set-cluster kubernetes \
      --certificate-authority=../ca.pem \
      --embed-certs=true \
      --server=https://<MASTER_VIP>:6443 \
      --kubeconfig=kubelet-bootstrap.kubeconfig

# 设置客户端认证参数
$ kubectl config set-credentials kubelet-bootstrap \
      --token=${BOOTSTRAP_TOKEN} \
      --kubeconfig=kubelet-bootstrap.kubeconfig

# 设置上下文参数
$ kubectl config set-context default \
      --cluster=kubernetes \
      --user=kubelet-bootstrap \
      --kubeconfig=kubelet-bootstrap.kubeconfig

# 设置默认上下文
$ kubectl config use-context default --kubeconfig=kubelet-bootstrap.kubeconfig

# 把生成的配置copy到每个worker节点上
$ scp kubelet-bootstrap.kubeconfig <user>@<node-ip>:/etc/kubernetes/kubelet-bootstrap.kubeconfig

# 先在worker节点上创建目录
$ mkdir -p /etc/kubernetes/pki

# 把ca分发到每个worker节点
$ scp target/pki/ca.pem <user>@<node-ip>:/etc/kubernetes/pki/
```
#### 8.3 kubelet配置文件
把kubelet配置文件分发到每个worker节点上
```bash
$ scp target/worker-<node-ip>/kubelet.config.json <user>@<node-ip>:/etc/kubernetes/
```
#### 8.4 kubelet服务文件
把kubelet服务文件分发到每个worker节点上
```bash
$ scp target/worker-<node-ip>/kubelet.service <user>@<node-ip>:/etc/systemd/system/
```
#### 8.5 启动服务
kublet 启动时查找配置的 --kubeletconfig 文件是否存在，如果不存在则使用 --bootstrap-kubeconfig 向 kube-apiserver 发送证书签名请求 (CSR)。
kube-apiserver 收到 CSR 请求后，对其中的 Token 进行认证（事先使用 kubeadm 创建的 token），认证通过后将请求的 user 设置为 system:bootstrap:，group 设置为 system:bootstrappers，这就是Bootstrap Token Auth。

```bash
# bootstrap附权
$ kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --group=system:bootstrappers

# 启动服务
$ mkdir -p /var/lib/kubelet
$ systemctl daemon-reload && systemctl enable kubelet && systemctl restart kubelet

# 在master上Approve bootstrap请求
$ kubectl get csr
$ kubectl certificate approve <name> 

# 查看服务状态
$ service kubelet status

# 查看日志
$ journalctl -f -u kubelet
```

## 9. 部署kube-proxy（worker节点）
#### 9.1 创建证书和私钥
```bash
$ cd target/pki/proxy
$ cfssl gencert -ca=../ca.pem \
  -ca-key=../ca-key.pem \
  -config=../ca-config.json \
  -profile=kubernetes  kube-proxy-csr.json | cfssljson -bare kube-proxy
```
#### 9.2 创建和分发 kubeconfig 文件
```bash
# 创建kube-proxy.kubeconfig
$ kubectl config set-cluster kubernetes \
  --certificate-authority=../ca.pem \
  --embed-certs=true \
  --server=https://<master-vip>:6443 \
  --kubeconfig=kube-proxy.kubeconfig
$ kubectl config set-credentials kube-proxy \
  --client-certificate=kube-proxy.pem \
  --client-key=kube-proxy-key.pem \
  --embed-certs=true \
  --kubeconfig=kube-proxy.kubeconfig
$ kubectl config set-context default \
  --cluster=kubernetes \
  --user=kube-proxy \
  --kubeconfig=kube-proxy.kubeconfig
$ kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig

# 分发kube-proxy.kubeconfig
$ scp kube-proxy.kubeconfig <user>@<node-ip>:/etc/kubernetes/
```
#### 9.3 分发kube-proxy.config
```bash
$ scp target/worker-<node-ip>/kube-proxy.config.yaml <user>@<node-ip>:/etc/kubernetes/
```

#### 9.4 分发kube-proxy服务文件
```bash
$ scp target/services/kube-proxy.service <user>@<node-ip>:/etc/systemd/system/
```

#### 9.5 启动服务
```bash
# 创建依赖目录
$ mkdir -p /var/lib/kube-proxy && mkdir -p /var/log/kubernetes

# 启动服务
$ systemctl daemon-reload && systemctl enable kube-proxy && systemctl restart kube-proxy

# 查看状态
$ service kube-proxy status

# 查看日志
$ journalctl -f -u kube-proxy
```

## 10. 部署CNI插件 - calico
我们使用calico官方的安装方式来部署。
```bash
# 创建目录（在配置了kubectl的节点上执行）
$ mkdir -p /etc/kubernetes/addons

# 上传calico配置到配置好kubectl的节点（一个节点即可）
$ scp target/addons/calico* <user>@<node-ip>:/etc/kubernetes/addons/

# 部署calico
$ kubectl create -f /etc/kubernetes/addons/calico-rbac-kdd.yaml
$ kubectl create -f /etc/kubernetes/addons/calico.yaml

# 查看状态
$ kubectl get pods -n kube-system
```

## 11. 部署DNS插件 - coredns
```bash
# 上传配置文件
$ scp target/addons/coredns.yaml <user>@<node-ip>:/etc/kubernetes/addons/

# 部署coredns
$ kubectl create -f /etc/kubernetes/addons/coredns.yaml
```

# 三、集群可用性测试
## 1. 创建nginx ds

```bash
 # 写入配置
$ cat > nginx-ds.yml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: nginx-ds
  labels:
    app: nginx-ds
spec:
  type: NodePort
  selector:
    app: nginx-ds
  ports:
  - name: http
    port: 80
    targetPort: 80
---
apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: nginx-ds
  labels:
    addonmanager.kubernetes.io/mode: Reconcile
spec:
  template:
    metadata:
      labels:
        app: nginx-ds
    spec:
      containers:
      - name: my-nginx
        image: nginx:1.7.9
        ports:
        - containerPort: 80
EOF

# 创建ds
$ kubectl create -f nginx-ds.yml


```

## 2. 检查各种ip连通性
```bash
# 检查各 Node 上的 Pod IP 连通性（主节点没有calico所以不能访问podip）
$ kubectl get pods  -o wide

# 在每个worker节点上ping pod ip
$ ping <pod-ip>

# 检查service可达性
$ kubectl get svc

# 在每个worker节点上访问服务（主节点没有proxy所以不能访问service-ip）
$ curl <service-ip>:<port>

# 在每个节点检查node-port可用性
$ curl <node-ip>:<port>
```

## 3. 检查dns可用性
```bash
# 创建一个nginx pod
$ cat > pod-nginx.yaml <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.7.9
    ports:
    - containerPort: 80
EOF

# 创建pod
$ kubectl create -f pod-nginx.yaml

# 进入pod，查看dns
$ kubectl exec  nginx -i -t -- /bin/bash

# 查看dns配置
root@nginx:/# cat /etc/resolv.conf

# 查看名字是否可以正确解析
root@nginx:/# ping nginx-ds
root@nginx:/# ping kubernetes
```

# 四. 部署dashboard
## 1. 部署dashboard
```bash
# 上传dashboard配置
$ scp target/addons/dashboard-all.yaml <user>@<node-ip>:/etc/kubernetes/addons/

# 创建服务
$ kubectl apply -f /etc/kubernetes/addons/dashboard-all.yaml

# 查看服务运行情况
$ kubectl get deployment kubernetes-dashboard -n kube-system
$ kubectl --namespace kube-system get pods -o wide
$ kubectl get services kubernetes-dashboard -n kube-system
$ netstat -ntlp|grep 8401
```

## 2. 访问dashboard

为了集群安全，从 1.7 开始，dashboard 只允许通过 https 访问，我们使用nodeport的方式暴露服务，可以使用 https://NodeIP:NodePort 地址访问 
关于自定义证书 
默认dashboard的证书是自动生成的，肯定是非安全的证书，如果大家有域名和对应的安全证书可以自己替换掉。使用安全的域名方式访问dashboard。 
在dashboard-all.yaml中增加dashboard启动参数，可以指定证书文件，其中证书文件是通过secret注进来的。
  
> \- –tls-cert-file  
  \- dashboard.cer  
  \- –tls-key-file  
  \- dashboard.key

## 3. 登录dashboard
Dashboard 默认只支持 token 认证，所以如果使用 KubeConfig 文件，需要在该文件中指定 token，我们这里使用token的方式登录
```bash
# 创建service account
$ kubectl create sa dashboard-admin -n kube-system

# 创建角色绑定关系
$ kubectl create clusterrolebinding dashboard-admin --clusterrole=cluster-admin --serviceaccount=kube-system:dashboard-admin

# 查看dashboard-admin的secret名字
$ ADMIN_SECRET=$(kubectl get secrets -n kube-system | grep dashboard-admin | awk '{print $1}')

# 打印secret的token
$ kubectl describe secret -n kube-system ${ADMIN_SECRET} | grep -E '^token' | awk '{print $2}'
```

