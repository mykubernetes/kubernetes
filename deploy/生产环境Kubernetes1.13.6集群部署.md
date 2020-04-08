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


| 主机名(HostName)	| IP地址 | 角色(Role)	| 集群IP(Vip) |
| :------: | :--------: | :------: | :--------: |
| K8S-PROD-MASTER-A1 | 10.211.18.4 | Master	| 10.211.18.10 |
| K8S-PROD-MASTER-A2 | 10.211.18.5 | Master	|
| K8S-PROD-MASTER-A3 | 10.211.18.6 | Master | 
| K8S-PROD-NODE-A1 | 10.211.18.11	| Node | 不涉及 |
| K8S-PROD-NODE-A2 | 10.211.18.12	| Node | 不涉及 |
| K8S-PROD-NODE-A3 | 10.211.18.13	| Node | 不涉及 |
| K8S-PROD-NODE-A4 | 10.211.18.14	| Node | 不涉及 |
| K8S-PROD-LB-A1 | 10.211.18.50	| Ingress	| 10.211.18.100 |
| K8S-PROD-LB-B1 | 10.211.18.51	| Ingress |
| K8S-PROD-REGISTR-A1 | 10.211.18.61 | Registr |
| K8S-PROD-REGISTR-B1	| 10.211.18.62 | Registr |
| Ceph集群 | / | ceph |  |

前期准备工作
---
一、修改主机名/关闭selinux
操作步骤：  
步骤 1	以root用户登录所有节点。  
步骤 2	执行以下命令修改主机名、关闭selinux。  
```
#修改主机名
#  hostnamectl  --static set-hostname  K8S-PROD-NODE-A1
#关闭Selinux
#  sed -i 's/SELINUX=.*/SELINUX=disabled/g' /etc/selinux/config
```

二、升级系统内核/同步系统时间  
注意：Overlay需要内核版本在3.12+，所以在安装完centos7.6之后要进行内核升级

步骤 1	以root用户登录所有节点。
步骤 2	安装时间同步软件
```
# yum install chrony –y
```
步骤 3	修改/etc/chrony.conf配置文件， 增加如下内容。 
```
server time.aliyun.com iburst
```
步骤 4	安装必备软件
```
yum install wget vim gcc git lrzsz net-tools tcpdump telnet  rsync -y
```
启动chronyd
```
# systemctl  start chronyd
```

三、调整内核参数
```
cat >  /etc/sysctl.d/k8s.conf  << EOF
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 10
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
net.ipv4.neigh.default.gc_stale_time = 120
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.default.arp_announce = 2
net.ipv4.conf.lo.arp_announce = 2
net.ipv4.conf.all.arp_announce = 2
net.ipv4.ip_forward = 1
net.ipv4.tcp_max_tw_buckets = 5000
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.tcp_synack_retries = 2
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-arptables = 1
net.netfilter.nf_conntrack_max = 2310720
fs.inotify.max_user_watches=89100
fs.may_detach_mounts = 1
fs.file-max = 52706963
fs.nr_open = 52706963
EOF
```
执行以下命令使修改生效
```
sysctl --system
modprobe br_netfilter
```

四、加载ipvs模块
```
cat << EOF > /etc/sysconfig/modules/ipvs.modules 
#!/bin/bash
ipvs_modules_dir="/usr/lib/modules/\`uname -r\`/kernel/net/netfilter/ipvs"
for i in \`ls \$ipvs_modules_dir | sed -r 's#(.*).ko.xz#\1#'\`; do
/sbin/modinfo -F filename \$i &> /dev/null
if [ \$? -eq 0 ]; then
/sbin/modprobe \$i
fi
done
EOF

chmod +x /etc/sysconfig/modules/ipvs.modules 
bash /etc/sysconfig/modules/ipvs.modules
```


五、导入elrepo Key  
步骤 1	导入KEY  
```
# rpm -import https://www.elrepo.org/RPM-GPG-KEY-elrepo.org
```
步骤 2	安装elrepo的yum源
```
#  rpm -Uvh http://www.elrepo.org/elrepo-release-7.0-2.el7.elrepo.noarch.rpm

Retrieving http://www.elrepo.org/elrepo-release-7.0-2.el7.elrepo.noarch.rpm
Retrieving http://elrepo.org/elrepo-release-7.0-3.el7.elrepo.noarch.rpm
Preparing...                             ################################# [100%]
Updating / installing...
   1:elrepo-release-7.0-3.el7.elrepo ################################# [100%]
```

使用以下命令列出可用的内核相关包

步骤 3	执行如下命令查看可用内核
```
yum --disablerepo="*" --enablerepo="elrepo-kernel" list available
```
步骤 4	安装4.4.176内核
```
# yum --enablerepo=elrepo-kernel install kernel-lt kernel-lt-devel -y
```
步骤 5	更改内核默认启动顺序
```
# grub2-set-default 0
# reboot
```
步骤 6	验证内核是否升级成功
```
# uname -rp
4.4.176-1.el7.elrepo.x86_64 x86_64
```

六、上传软件包
参考表1将需上传的软件包或者脚本上传到Master和Node节点的指定目录下
| 待上传包/脚本 |说明 | 上传路径 |
| :------: | :--------: | :------: |
| kubernetes-server-linux-amd64.tar.gz | Kubernetes Master节点所需安装包。 | /opt/software |
| kubernetes-node-linux-amd64.tar.gz | Kubernetes Node节点所需安装包。 | /opt/software |
| etcd-v3.3.10-linux-amd64.tar.gz | Etcd键值存储数据库	| /opt/software |
| flannel-v0.11.0-linux-amd64.tar.gz | CNI网络插件 | /opt/software |


七、防火墙放行端口

Master Node Inbound
---
| Protocol | Port Range | Source | Purpose |
| :------: | :--------: | :------: | :------: |
| TCP	| 6443 8443	| Worker Node,API Requests	| Kubernetes API Server |
| UDP | 8285 | Master & Worker Nodes | Flannel overlay network – udp backend |
| UDP | 8472 | Master & Worker Nodes | Flannel overlay network – vxlan backend |

Worker Node Inbound
---
| Protocol | Port Range | Source | Purpose |
| :------: | :--------: | :------: | :------: |
| TCP	| 10250 | Master Nodes | Worker node Kubelet API for exec and logs. |
| TCP	| 10255 | Heapster | Worker node read-only Kubelet API. |
| TCP	| 30000-40000 | External Application Consumers | Default port range for external service ports. Typically, these ports would need to be exposed to external load-balancers, or other external consumers of the application itself. |
| UDP | 8285 | Master & Worker Nodes | flannel overlay network - udp backend. This is the default network configuration (only required if using flannel) |
|UDP | 8472 | Master & Worker Nodes | flannel overlay network - vxlan backend (only required if using flannel)
| TCP | 179 | Worket Nodes | Calico BGP network (only required if the BGP backend is used) |

Etcd Node Inbound
---
| Protocol | Port Range | Source | Purpose |
| :------: | :--------: | :------: | :------: |
| TCP	| 2379-2380 | Master Nodes | etcd server client API |
| TCP	| 2379-2380 | Worker Nodes | etcd server client API (only required if using flannel or Calico). |

Ingress
---
| Protocol | Port Range | Source | Purpose |
| :------: | :--------: | :------: | :------: |
| TCP | 80 | Ingress Nodes | http |
| TCP | 443 | Ingress Nodes | https |
| TCP | 8080 | Ingress Nodes | other |


安装Docker
===

1、安装存储驱动
```
yum install -y yum-utils \
device-mapper-persistent-data \
lvm2
```
2、添加YUM仓库
```
yum-config-manager --add-repo  https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
```
3、列出所有版本的Docker CE
```
#  yum list docker-ce --showduplicates | sort -r
docker-ce.x86_64            18.06.3.ce-3.el7
docker-ce.x86_64            18.06.2.ce-3.el7
```
4、安装特定版本
```
# yum install docker-ce-<VERSION_STRING> docker-ce-cli-<VERSION_STRING> containerd.io

# yum install docker-ce-18.06.2.ce-3.el7  containerd.io -y
```
5、修改docker服务配置文件
```
vim /usr/lib/systemd/system/docker.service   #增加如下参数

[Service]
# kill only the docker process, not all processes in the cgroup
KillMode=process
```
6、配置docker参数
```
# mkdir /etc/docker
# vi /etc/docker/daemon.json

{
    "log-level": "warn",
    "selinux-enabled": false,
    "insecure-registries": [
        "10.211.18.61:10500",
        "10.211.18.62:10500"
    ],
    "registry-mirrors": [
        "https://pqbap4ya.mirror.aliyuncs.com"
    ],
    "default-shm-size": "128M",
    "data-root": "/data/docker",
    "max-concurrent-downloads": 10,
    "max-concurrent-uploads": 5,
    "oom-score-adjust": -1000,
    "debug": false,
    "live-restore": true,
    "exec-opts": [
        "native.cgroupdriver=cgroupfs"
],
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "10"
},
    "oom-score-adjust": -1000,
    "registry-mirrors": ["$mirror"],
    "storage-driver": "overlay2",
    "storage-opts":["overlay2.override_kernel_check=true"]
}
```

参数说明
| 参数名称 | 描述 |
| :------: | :--------: |
| log-level | 日志级别[error|warn|info|debug]。 |
| insecure-registries | 配置私有镜像仓库，多个地址以“,”隔开。 |
| registry-mirrors | 默认拉取镜像仓库地址 |
| max-concurrent-downloads | 最大下载镜像数量 |
| max-concurrent-uploads | 最大上传镜像数量 |
| live-restore	Docker | 停止时保持容器继续运行，取值[true|false] |
| native.cgroupdriver | Docker存储驱动 |
| data-root | 设置docker存储路径， 默认为/var/lib/docker |

详细参数请参考官方文档： https://docs.docker.com/engine/reference/commandline/dockerd/#/linux-configuration-file

7、启动docker
```
# systemctl  enable docker
# systemctl  start  docker
```


安装Cfssl 
===
1、在K8S-PROD-MASTER-A1节点操作
```
wget -O /bin/cfssl https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
wget -O /bin/cfssljson https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
wget -O /bin/cfssl-certinfo https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
for cfssl in `ls /bin/cfssl*`;do chmod +x $cfssl;done;
```

安装Etcd集群
===
etcd 是基于 Raft 的分布式 key-value 存储系统，由 CoreOS 开发，常用于服务发现、共享配置以及并发控制（如 leader 选举、分布式锁等）。kubernetes 使用 etcd 存储所有运行数据。

步骤 1	在K8S-PROD-MASTER-A1节点制作证书文件
```
# mkdir -pv $HOME/etcd-ssl && cd $HOME/etcd-ssl
```
1.	生成CA证书，expiry为证书过期时间(10年)
```
cat > ca-config.json << EOF
{
  "signing": {
    "default": {
      "expiry": "87600h"
    },
    "profiles": {
      "kubernetes": {
        "usages": [
            "signing",
            "key encipherment",
            "server auth",
            "client auth"
        ],
        "expiry": "87600h"
      }
    }
  }
}
EOF
```
2.	生成CA证书请求文件， ST/L/字段可自行修改
```
cat > etcd-ca-csr.json << EOF
{
  "CN": "etcd",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "ST": "ZheJiang",
      "L": "HangZhou",
      "O": "etcd",
      "OU": "Etcd Security"
    }
  ]
}
EOF
```
3.	生成证书请求文件，ST/L/字段可自行修改
```
cat > etcd-csr.json << EOF
{
    "CN": "etcd",
    "hosts": [
      "127.0.0.1",
      "10.211.18.4",
      "10.211.18.5",
      "10.211.18.6",
      "10.211.18.10"
    ],
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "ST": "ZheJiang",
            "L": "HangZhou",
            "O": "etcd",
            "OU": "Etcd Security"
        }
    ]
}
EOF
```
注意：  hosts字段内为etcd主机ip， 请根据业务ip自行修改。

2、拷贝证书文件到etcd节点（在K8S-PROD-MASTER-A1节点操作）
```
[root@K8S-PROD-MASTER-A1 etcd-ssl]# cfssl gencert -initca etcd-ca-csr.json | cfssljson -bare etcd-ca

2019/03/12 13:25:46 [INFO] generating a new CA key and certificate from CSR
2019/03/12 13:25:46 [INFO] generate received request
2019/03/12 13:25:46 [INFO] received CSR
2019/03/12 13:25:46 [INFO] generating key: rsa-2048
2019/03/12 13:25:47 [INFO] encoded CSR
2019/03/12 13:25:47 [INFO] signed certificate with serial number 77730668163919124554579164782550661290070653555

[root@K8S-PROD-MASTER-A1 etcd-ssl]# cfssl gencert -ca=etcd-ca.pem -ca-key=etcd-ca-key.pem -config=ca-config.json -profile=kubernetes etcd-csr.json | cfssljson -bare etcd
2019/03/12 13:25:57 [INFO] generate received request
2019/03/12 13:25:57 [INFO] received CSR
2019/03/12 13:25:57 [INFO] generating key: rsa-2048
2019/03/12 13:25:57 [INFO] encoded CSR
2019/03/12 13:25:57 [INFO] signed certificate with serial number 147067344941643695772357706461558238128357623444
2019/03/12 13:25:57 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
```
3、分别在etcd节点创建以下目录
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# mkdir -pv /data/apps/etcd/{ssl,bin,etc,data}
```
4、分发证书文件
```
[root@K8S-PROD-MASTER-A1]# cd /root/etcd-ssl
[root@K8S-PROD-MASTER-A1]# mkdir -pv /data/apps/etcd/ssl
[root@K8S-PROD-MASTER-A1]# cp etcd*.pem /data/apps/etcd/ssl
[root@K8S-PROD-MASTER-A1]# scp -r /data/apps/etcd 10.211.18.5:/data/apps/etcd
[root@K8S-PROD-MASTER-A1]# scp -r /data/apps/etcd 10.211.18.6:/data/apps/etcd
```
5、解压etcd-v3.3.12-linux-amd64.tar.gz
```
[root@K8S-PROD-MASTER-A1 software]# tar zxf etcd-v3.3.12-linux-amd64.tar.gz
[root@K8S-PROD-MASTER-A1 software]# mv etcd-v3.3.12-linux-amd64/etcd* /data/apps/etcd/bin/
[root@K8S-PROD-MASTER-A1 software]# cd /data/apps/etcd/
```
6、配置系统服务
```
[root@K8S-PROD-MASTER-A1 etcd]# vi /usr/lib/systemd/system/etcd.service
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
WorkingDirectory=/data/apps/etcd/
EnvironmentFile=-/data/apps/etcd/etc/etcd.conf
User=etcd
# set GOMAXPROCS to number of processors
ExecStart=/bin/bash -c "GOMAXPROCS=$(nproc) /data/apps/etcd/bin/etcd --name=\"${ETCD_NAME}\" --data-dir=\"${ETCD_DATA_DIR}\" --listen-client-urls=\"${ETCD_LISTEN_CLIENT_URLS}\""
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

7、修改配置文件，红色字段内容请根据业务规划自行修改。
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cat << EOF > /data/apps/etcd/etc/etcd.conf
[Member]
#ETCD_CORS=""
ETCD_NAME="K8S-PROD-ETCD-A1"
ETCD_DATA_DIR="/data/apps/etcd/data/default.etcd"
#ETCD_WAL_DIR=""
ETCD_LISTEN_PEER_URLS="https://10.211.18.4:2380"
ETCD_LISTEN_CLIENT_URLS="https://127.0.0.1:2379,https://10.211.18.4:2379"
#ETCD_MAX_SNAPSHOTS="5"
#ETCD_MAX_WALS="5"
#ETCD_SNAPSHOT_COUNT="100000"
#ETCD_HEARTBEAT_INTERVAL="100"
#ETCD_ELECTION_TIMEOUT="1000"
#ETCD_QUOTA_BACKEND_BYTES="0"
#ETCD_MAX_REQUEST_BYTES="1572864"
#ETCD_GRPC_KEEPALIVE_MIN_TIME="5s"
#ETCD_GRPC_KEEPALIVE_INTERVAL="2h0m0s"
#ETCD_GRPC_KEEPALIVE_TIMEOUT="20s"
#
#[Clustering]
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://10.211.18.4:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://127.0.0.1:2379,https://10.211.18.4:2379"
#ETCD_DISCOVERY=""
#ETCD_DISCOVERY_FALLBACK="proxy"
#ETCD_DISCOVERY_PROXY=""
#ETCD_DISCOVERY_SRV=""
ETCD_INITIAL_CLUSTER="K8S-PROD-ETCD-A1=https://10.211.18.4:2380,K8S-PROD-ETCD-A2=https://10.211.18.5:2380,K8S-PROD-ETCD-A3=https://10.211.18.6:2380"
ETCD_INITIAL_CLUSTER_TOKEN="BigBoss"
#ETCD_INITIAL_CLUSTER_STATE="new"
#ETCD_STRICT_RECONFIG_CHECK="true"
#ETCD_ENABLE_V2="true"
#
#[Proxy]
#ETCD_PROXY="off"
#ETCD_PROXY_FAILURE_WAIT="5000"
#ETCD_PROXY_REFRESH_INTERVAL="30000"
#ETCD_PROXY_DIAL_TIMEOUT="1000"
#ETCD_PROXY_WRITE_TIMEOUT="5000"
#ETCD_PROXY_READ_TIMEOUT="0"
#
#[Security]
ETCD_CERT_FILE="/data/apps/etcd/ssl/etcd.pem"
ETCD_KEY_FILE="/data/apps/etcd/ssl/etcd-key.pem"
#ETCD_CLIENT_CERT_AUTH="false"
ETCD_TRUSTED_CA_FILE="/data/apps/etcd/ssl/etcd-ca.pem"
#ETCD_AUTO_TLS="false"
ETCD_PEER_CERT_FILE="/data/apps/etcd/ssl/etcd.pem"
ETCD_PEER_KEY_FILE="/data/apps/etcd/ssl/etcd-key.pem"
#ETCD_PEER_CLIENT_CERT_AUTH="false"
ETCD_PEER_TRUSTED_CA_FILE="/data/apps/etcd/ssl/etcd-ca.pem"
#ETCD_PEER_AUTO_TLS="false"
#
[Logging]
ETCD_DEBUG="false"
#ETCD_LOG_PACKAGE_LEVELS=""
ETCD_LOG_OUTPUT="default"
#
#[Unsafe]
#ETCD_FORCE_NEW_CLUSTER="false"
#
#[Version]
#ETCD_VERSION="false"
#ETCD_AUTO_COMPACTION_RETENTION="0"
#
#[Profiling]
#ETCD_ENABLE_PPROF="false"
#ETCD_METRICS="basic"
#
#[Auth]
#ETCD_AUTH_TOKEN="simple"
EOF
```

8、启动服务
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# useradd -r etcd && chown etcd.etcd -R /data/apps/etcd
[root@K8S-PROD-MASTER-A1 k8s-ssl]# systemctl enable etcd
[root@K8S-PROD-MASTER-A1 k8s-ssl]# systemctl start etcd
[root@K8S-PROD-MASTER-A1 k8s-ssl]# systemctl status etcd

● etcd.service - Etcd Server
   Loaded: loaded (/usr/lib/systemd/system/etcd.service; enabled; vendor preset: disabled)
   Active: active (running) since Tue 2019-03-12 17:11:30 CST; 49ms ago
```
将etcd配置文件、系统服务拷贝到其他etcd节点，根据实际情况修改对应字段信息。

9、设置环境变量
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# echo "PATH=$PATH:/data/apps/etcd/bin/" >> /etc/profile.d/etcd.sh
[root@K8S-PROD-MASTER-A1 k8s-ssl]# chmod +x /etc/profile.d/etcd.sh
[root@K8S-PROD-MASTER-A1 k8s-ssl]# source  /etc/profile.d/etcd.sh
[root@K8S-PROD-MASTER-A1 k8s-ssl]# etcdctl --endpoints "https://10.211.18.4:2379,https://10.211.18.4:2379,https://10.211.18.4:2379"   --ca-file=/data/apps/etcd/ssl/etcd-ca.pem  --cert-file=/data/apps/etcd/ssl/etcd.pem   --key-file=/data/apps/etcd/ssl/etcd-key.pem  member list

46b51f26084e3e7e: name=K8S-PROD-ETCD-A2 peerURLs=https://10.211.18.5:2380 clientURLs=https://10.211.18.5:2379,https://127.0.0.1:2379 isLeader=true
74974148d0145708: name=K8S-PROD-ETCD-A1 peerURLs=https://10.211.18.4:2380 clientURLs=https://10.211.18.4:2379,https://127.0.0.1:2379 isLeader=false
b69515ada606e488: name=K8S-PROD-ETCD-A3 peerURLs=https://10.211.18.6:2380 clientURLs=https://10.211.18.6:2379,https://127.0.0.1:2379 isLeader=false
```











