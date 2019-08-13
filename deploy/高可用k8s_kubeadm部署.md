# 一、实践环境准备
## 1. 服务器说明
我们这里使用的是五台centos-7.6的虚拟机，具体信息如下表：

| 系统类型 | IP地址 | 节点角色 | CPU | Memory | Hostname |
| :------: | :--------: | :-------: | :-----: | :---------: | :-----: |
| centos-7.6 | 192.168.101.69 | master |   \>=2    | \>=2G | node01 |
| centos-7.6 | 192.168.101.70 | master |   \>=2    | \>=2G | node02 |
| centos-7.6 | 192.168.101.71 | master |   \>=2    | \>=2G | node03 |
| centos-7.6 | 192.168.101.72 | worker |   \>=2    | \>=2G | node04 |
| centos-7.6 | 192.168.101.73 | worker |   \>=2    | \>=2G | node05 |

## 2. 系统设置（所有节点）
#### 2.1 主机名
主机名必须每个节点都不一样，并且保证所有点之间可以通过hostname互相访问。
```bash
# 查看主机名
$ hostname
# 修改主机名
$ hostnamectl set-hostname <your_hostname>
# 配置host，使所有节点之间可以通过hostname互相访问
$ vi /etc/hosts
<node-ip> <node-hostname>
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
## 3. 安装docker（所有节点）
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
# 2.设置docker启动参数
# - 设置docker数据目录：选择比较大的分区（默认为/var/lib/docker）
# - 设置cgroup driver（默认是cgroupfs，主要目的是与kubelet配置统一，这里也可以不设置后面在kubelet中指定cgroupfs）
$ cat <<EOF > /etc/docker/daemon.json
{
    "graph": "/docker/data/path",                  #配置修改docker数据目录
    "exec-opts": ["native.cgroupdriver=systemd"]   #配置cgroup
}
EOF
# 启动docker服务
service docker restart
```

## 4. 安装必要工具（所有节点）
#### 4.1 工具说明
- **kubeadm:**  部署集群用的命令
- **kubelet:** 在集群中每台机器上都要运行的组件，负责管理pod、容器的生命周期
- **kubectl:** 集群管理工具（可选，只要在控制集群的节点上安装即可）

#### 4.2 安装方法

```bash
# 配置yum源（科学上网的同学可以把"mirrors.aliyun.com"替换为"packages.cloud.google.com"）
$ cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=http://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=0
repo_gpgcheck=0
gpgkey=http://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg
       http://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF

# 安装工具
# 找到要安装的版本号
$ yum list kubeadm --showduplicates | sort -r

# 安装指定版本（这里用的是1.14.0）
$ yum install -y kubeadm-1.14.0-0 kubelet-1.14.0-0 kubectl-1.14.0-0 --disableexcludes=kubernetes

# 设置kubelet的cgroupdriver（kubelet的cgroupdriver默认为systemd，如果上面没有设置docker的exec-opts为systemd，这里就需要将kubelet的设置为cgroupfs）
$ sed -i "s/cgroup-driver=systemd/cgroup-driver=cgroupfs/g" /etc/systemd/system/kubelet.service.d/10-kubeadm.conf

# 启动kubelet
$ systemctl enable kubelet && systemctl start kubelet

```


## 5. 准备配置文件（任意节点）
#### 5.1 下载配置文件
我这准备了一个项目，专门为大家按照自己的环境生成配置的。它只是帮助大家尽量的减少了机械化的重复工作。它并不会帮你设置系统环境，不会给你安装软件。总之就是会减少你的部署工作量，但不会耽误你对整个系统的认识和把控。
```bash
$ cd ~ && git clone https://gitee.com/pa/kubernetes-ha-kubeadm.git
# 看看git内容
$ ls -l kubernetes-ha-kubeadm
addons/
configs/
scripts/
init.sh
global-configs.properties
```
#### 5.2 文件说明
- **addons**
> kubernetes的插件，比如calico和dashboard。

- **configs**
> 包含了部署集群过程中用到的各种配置文件。

- **scripts**
> 包含部署集群过程中用到的脚本，如keepalive检查脚本。

- **global-configs.properties**
> 全局配置，包含各种易变的配置内容。

- **init.sh**
> 初始化脚本，配置好global-config之后，会自动生成所有配置文件。

#### 5.3 生成配置
这里会根据大家各自的环境生成kubernetes部署过程需要的配置文件。
在每个节点上都生成一遍，把所有配置都生成好，后面会根据节点类型去使用相关的配置。
```bash
# cd到之前下载的git代码目录
$ cd kubernetes-ha-kubeadm

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
> 2. global-config.properties文件填写错误，需要重新生成  
> 再执行一次./init.sh即可，不需要手动删除target

#### 5.4 配置好免密登录
为了方便文件的copy我们选择一个中转节点，配置好跟其他所有节点的免密登录
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

#### 5.5 预先下载安装所需要的镜像
```
$ cat <<EOF > pull_k8s_images.sh
images=(
    kube-apiserver:v1.14.0
    kube-controller-manager:v1.14.0
    kube-scheduler:v1.14.0
    kube-proxy:v1.14.0
    pause:3.1
    etcd:3.2.24
    coredns:1.2.2
)

for imageName in ${images[@]} ; do
    docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/$imageName
    docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/$imageName k8s.gcr.io/$imageName
done
EOF

$ sh pull_k8s_images.sh
```

# 二. 搭建高可用集群
## 1. 部署keepalived - apiserver高可用（任选两个master节点）
#### 1.1 安装keepalived
```bash
# 在两个主节点上安装keepalived（一主一备）
$ yum install -y keepalived
```
#### 1.2 创建keepalived配置文件
```bash
# 创建目录
$ ssh <user>@<master-ip> "mkdir -p /etc/keepalived"
$ ssh <user>@<backup-ip> "mkdir -p /etc/keepalived"

# 分发配置文件(在git仓库内的target目录)
$ scp target/configs/keepalived-master.conf <user>@<master-ip>:/etc/keepalived/keepalived.conf
$ scp target/configs/keepalived-backup.conf <user>@<backup-ip>:/etc/keepalived/keepalived.conf

# 分发监测脚本(在git仓库内的target目录)
$ scp target/scripts/check-apiserver.sh <user>@<master-ip>:/etc/keepalived/
$ scp target/scripts/check-apiserver.sh <user>@<backup-ip>:/etc/keepalived/
```

#### 1.3 启动keepalived
```bash
# 分别在master和backup上启动服务
$ systemctl enable keepalived && service keepalived start

# 检查状态
$ service keepalived status

# 查看日志
$ journalctl -f -u keepalived

# 查看虚拟ip
$ ip a
```

## 2. 部署第一个主节点
```bash
# 准备配置文件(在git仓库内的target目录)
$ scp target/configs/kubeadm-config.yaml <user>@<node-ip>:~
# ssh到第一个主节点，执行kubeadm初始化系统（注意保存最后打印的加入集群的命令）
$ kubeadm init --config=kubeadm-config.yaml --experimental-upload-certs

# copy kubectl配置（上一步会有提示）
$ mkdir -p ~/.kube
$ cp -i /etc/kubernetes/admin.conf ~/.kube/config

# 测试一下kubectl
$ kubectl get pods --all-namespaces

# **备份init打印的join命令**

```

## 3. 部署网络插件 - calico
我们使用calico官方的安装方式来部署。
```bash
# 创建目录（在配置了kubectl的节点上执行）
$ mkdir -p /etc/kubernetes/addons

# 上传calico配置到配置好kubectl的节点（一个节点即可）
$ scp target/addons/calico* <user>@<node-ip>:/etc/kubernetes/addons/

# 部署calico
$ kubectl apply -f /etc/kubernetes/addons/calico-rbac-kdd.yaml
$ kubectl apply -f /etc/kubernetes/addons/calico.yaml

# 查看状态
$ kubectl get pods -n kube-system
```
## 4. 加入其它master节点
```bash
# 使用之前保存的join命令加入集群
$ kubeadm join ...

# 耐心等待一会，并观察日志
$ journalctl -f

# 查看集群状态
# 1.查看节点
$ kubectl get nodes
# 2.查看pods
$ kubectl get pods --all-namespaces
```

## 5. 加入worker节点
```bash
# 使用之前保存的join命令加入集群
$ kubeadm join ...

# 耐心等待一会，并观察日志
$ journalctl -f

# 查看节点
$ kubectl get nodes
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
# 检查各 Node 上的 Pod IP 连通性
$ kubectl get pods  -o wide

# 在每个节点上ping pod ip
$ ping <pod-ip>

# 检查service可达性
$ kubectl get svc

# 在每个节点上访问服务
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
$ netstat -ntlp|grep 30005
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

