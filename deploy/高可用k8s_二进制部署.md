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

