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

7、修改配置文件。
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

安装Kubernetes组件
===

生成集群CA证书文件
---

一、配置CA证书。

1、使用root用户，登录K8S-PROD-MASTER-A1节点。

在家目录创建用于生成证书临时目录。
```
mkdir  $HOME/k8s-ssl  &&  cd  $HOME/k8s-ssl
```
2、配置ca证书信息， ST/L/expiry 字段可自行修改。
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cp ../etcd-ssl/ca-config.json .
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cat > ca-csr.json << EOF
{
  "CN": "kubernetes",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "ST": "HangZhou",
      "L": "ZheJiang",
      "O": "k8s",
      "OU": "System"
    }
  ],
  "ca": {
     "expiry": "87600h"
  }
}
EOF
```
3、执行gencert命令生成证书文件。
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cfssl gencert -initca ca-csr.json | cfssljson -bare ca

2019/03/12 17:38:18 [INFO] generating a new CA key and certificate from CSR
2019/03/12 17:38:19 [INFO] generate received request
2019/03/12 17:38:19 [INFO] received CSR
2019/03/12 17:38:19 [INFO] generating key: rsa-2048
2019/03/12 17:38:19 [INFO] encoded CSR
2019/03/12 17:38:19 [INFO] signed certificate with serial number 371293668666858827973511319667907765319628751223

[root@K8S-PROD-MASTER-A1 k8s-ssl]# ls -l ca*.pem
-rw------- 1 root root 1679 Mar 12 17:38 ca-key.pem
-rw-r--r-- 1 root root 1363 Mar 12 17:38 ca.pem
```

二、配置kube-apiserver证书

注意： 如需自定义集群域名， 请修改cluster | cluster.local 字段为自定义域名

1、配置kube-apiserver证书信息
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cat > kube-apiserver-csr.json << EOF
{
    "CN": "kube-apiserver",
    "hosts": [
      "127.0.0.1",
      "10.211.18.4",
      "10.211.18.5",
      "10.211.18.6",
      "10.211.18.10",
      "10.99.0.1",
      "kubernetes",
      "kubernetes.default",
      "kubernetes.default.svc",
      "kubernetes.default.svc.ziji",
      "kubernetes.default.svc.ziji.work"
    ],
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "ST": "HangZhou",
            "L": "ZheJiang",
            "O": "k8s",
            "OU": "System"
        }
    ]
}
EOF
```
2、执行cfssl生成kube-apiserver证书
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=/root/k8s-ssl/ca-config.json -profile=kubernetes kube-apiserver-csr.json | cfssljson -bare kube-apiserver

2019/03/12 22:01:33 [INFO] generate received request
2019/03/12 22:01:33 [INFO] received CSR
2019/03/12 22:01:33 [INFO] generating key: rsa-2048
2019/03/12 22:01:34 [INFO] encoded CSR
2019/03/12 22:01:34 [INFO] signed certificate with serial number 386694856404685594652175309996230208077296568138
2019/03/12 22:01:34 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").


[root@K8S-PROD-MASTER-A1 k8s-ssl]# ls -l kube-apiserver*.pem
-rw------- 1 root root 1675 Mar 12 22:01 kube-apiserver-key.pem
-rw-r--r-- 1 root root 1679 Mar 12 22:01 kube-apiserver.pem
```

三、配置kube-controller-manager证书

该集群包含 3 个节点，启动后将通过竞争选举机制产生一个 leader 节点，其它节点为阻塞状态。当 leader 节点不可用后，剩余节点将再次进行选举产生新的 leader 节点，从而保证服务的可用性。

1、创建证书和私钥

注意：hosts列表包含所有 kube-controller-manager 节点 IP
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cat > kube-controller-manager-csr.json << EOF
{
    "CN": "system:kube-controller-manager",
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
            "ST": "HangZhou",
            "L": "ZheJiang",
            "O": "system:kube-controller-manager",
            "OU": "System"
        }
    ]
} 
EOF
```

2、执行cfssl 生成kube-controller-manager证书
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes kube-controller-manager-csr.json | cfssljson -bare kube-controller-manager

[root@K8S-PROD-MASTER-A1 k8s-ssl]# ls -l kube-controller-manager*.pem
-rw------- 1 root root 1679 Mar 13 16:51 kube-controller-manager-key.pem
-rw-r--r-- 1 root root 1521 Mar 13 16:51 kube-controller-manager.pem
```

四、配置kube-scheduler证书

1、创建证书和私钥
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cat > kube-scheduler-csr.json << EOF
{
    "CN": "system:kube-scheduler",
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
            "ST": "HangZhou",
            "L": "ZheJiang",
            "O": "system:kube-scheduler",
            "OU": "System"
        }
    ]
}
EOF
```

2、执行cfssl生成kube-scheduler证书
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes kube-scheduler-csr.json | cfssljson -bare kube-scheduler

2019/03/13 18:34:17 [INFO] generate received request
2019/03/13 18:34:17 [INFO] received CSR
2019/03/13 18:34:17 [INFO] generating key: rsa-2048
2019/03/13 18:34:18 [INFO] encoded CSR
2019/03/13 18:34:18 [INFO] signed certificate with serial number 403553352625169635537829194764174077828018057798
2019/03/13 18:34:18 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

[root@K8S-PROD-MASTER-A1 k8s-ssl]# ls -l kube-scheduler*.pem
-rw------- 1 root root 1679 Mar 13 18:34 kube-scheduler-key.pem
-rw-r--r-- 1 root root 1497 Mar 13 18:34 kube-scheduler.pem
```

五、配置 kube-proxy 证书

kube-proxy 运行在所有 worker 节点上，，它监听 apiserver 中 service 和 Endpoint 的变化情况，创建路由规则来进行服务负载均衡。本文档kube-proxy使用ipvs模式。

1、创建 kube-proxy 证书

该证书只会被 kube-proxy 当做 client 证书使用，所以 hosts 字段为空。
```
cat > kube-proxy-csr.json << EOF
{
    "CN": "system:kube-proxy",
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "ST": "HangZhou",
            "L": "ZheJiang",
            "O": "system:kube-proxy",
            "OU": "System"
        }
    ]
}
EOF
```
2、生成 kube-proxy 证书
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes kube-proxy-csr.json | cfssljson -bare kube-proxy

2019/03/13 17:27:13 [INFO] generate received request
2019/03/13 17:27:13 [INFO] received CSR
……………

[root@K8S-PROD-MASTER-A1 k8s-ssl]# ls -l kube-proxy*.pem
-rw------- 1 root root 1675 Mar 13 17:27 kube-proxy-key.pem
-rw-r--r-- 1 root root 1428 Mar 13 17:27 kube-proxy.pem
```

六、配置 admin 证书

为集群组件kubelet、kubectl配置admin TLS认证证书，具有访问kubernetes所有api的权限。

1、创建 admin证书文件
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cat > admin-csr.json << EOF
{
    "CN": "admin",
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "ST": "HangZhou",
            "L": "ZheJiang",
            "O": "system:masters",
            "OU": "System"
        }
    ]
}
EOF
```
2、生成 admin 证书
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes admin-csr.json | cfssljson -bare admin

2019/03/13 18:25:57 [INFO] generate received request
2019/03/13 18:25:57 [INFO] received CSR
2019/03/13 18:25:57 [INFO] generating key: rsa-2048
2019/03/13 18:25:57 [INFO] encoded CSR
2019/03/13 18:25:57 [INFO] signed certificate with serial number 125226606191023955519736334759407934858394250916
2019/03/13 18:25:57 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

[root@K8S-PROD-MASTER-A1 k8s-ssl]# ls -l admin*.pem
-rw------- 1 root root 1679 Mar 13 18:25 admin-key.pem
-rw-r--r-- 1 root root 1407 Mar 13 18:25 admin.pem
```

七、分发证书文件

提示：  node节点只需要ca、kube-proxy、kubelet证书，不需要拷贝kube-controller-manager、 kube-schedule、kube-apiserver证书

1、创建证书存放目录
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# mkdir -pv /data/apps/kubernetes/{pki,log,etc,certs}
mkdir: created directory ‘/data/apps/kubernetes’
mkdir: created directory ‘/data/apps/kubernetes/pki’
```
2、拷贝证书文件到apiserver、master节点
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cp ca*.pem admin*.pem kube-proxy*.pem kube-scheduler*.pem kube-controller-manager*.pem kube-apiserver*.pem /data/apps/kubernetes/pki/

[root@K8S-PROD-MASTER-A1 k8s-ssl]# rsync  -avzP /data/apps/kubernetes 10.211.18.4/data/apps/
[root@K8S-PROD-MASTER-A1 k8s-ssl]# rsync  -avzP /data/apps/kubernetes 10.211.18.5/data/apps/
[root@K8S-PROD-MASTER-A1 k8s-ssl]# rsync  -avzP /data/apps/kubernetes 10.211.18.6/data/apps/
```

部署Master节点
---
1、解压server包并拷贝文件到其他master节点
```
[root@K8S-PROD-MASTER-A1 k8s-ssl]# cd /opt/software/
[root@K8S-PROD-MASTER-A1 software]# ls -l
total 517804
drwxr-xr-x 3 1000 1000        96 Mar 12 16:11 etcd-v3.3.12-linux-amd64
-rw-r--r-- 1 root root  11350736 Mar 11 08:42 etcd-v3.3.12-linux-amd64.tar.gz
-rw-r--r-- 1 root root   9565743 Mar 11 08:44 flannel-v0.11.0-linux-amd64.tar.gz
-rw-r--r-- 1 root root  91418745 Mar 11 08:51 kubernetes-node-linux-amd64.tar.gz
-rw-r--r-- 1 root root 417885230 Mar 11 09:10 kubernetes-server-linux-amd64.tar.gz

[root@K8S-PROD-MASTER-A1 software]# tar zxf kubernetes-server-linux-amd64.tar.gz
[root@K8S-PROD-MASTER-A1 software]# rsync -avzP kubernetes/server   10.211.18.4:/data/apps/kubernetes/
[root@K8S-PROD-MASTER-A1 software]# rsync -avzP kubernetes/server   10.211.18.4:/data/apps/kubernetes/
[root@K8S-PROD-MASTER-A1 software]# rsync -avzP kubernetes/server   10.211.18.4:/data/apps/kubernetes/
```

2、配置环境变量，安装docker命令补全
```
[root@K8S-PROD-MASTER-A1 software]# yum install  bash-completion  -y
[root@K8S-PROD-MASTER-A1 software]# cat > /etc/profile.d/kubernetes.sh << EOF
K8S_HOME=/data/apps/kubernetes
export PATH=\$K8S_HOME/server/bin:\$PATH
source <(kubectl completion bash)
EOF

[root@K8S-PROD-MASTER-A1 software]# source /etc/profile.d/kubernetes.sh

[root@K8S-PROD-MASTER-A1 ~]# kubectl version
Client Version: version.Info{Major:"1", Minor:"13", GitVersion:"v1.13.6", GitCommit:"c27b913fddd1a6c480c229191a087698aa92f0b1", GitTreeState:"clean", BuildDate:"2019-02-28T13:37:52Z", GoVersion:"go1.11.5", Compiler:"gc", Platform:"linux/amd64"}
The connection to the server localhost:8080 was refused - did you specify the right host or port?
```

配置 TLS Bootstrapping
===
1、生成token
```
[root@K8S-PROD-MASTER-A1 software]# export BOOTSTRAP_TOKEN=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' ')
[root@K8S-PROD-MASTER-A1 software]# cat > /data/apps/kubernetes/token.csv << EOF
${BOOTSTRAP_TOKEN},kubelet-bootstrap,10001,"system:kubelet-bootstrap"
EOF
```

一、创建 kubelet bootstrapping kubeconfig

设置kube-apiserver访问地址， 后面需要对kube-apiserver配置高可用集群， 这里设置apiserver浮动IP。 KUBE_APISERVER=浮动IP
```
[root@K8S-PROD-MASTER-A1 software]# cd /data/apps/kubernetes/
# export KUBE_APISERVER="https://10.211.18.10:8443"

# kubectl config set-cluster kubernetes \
--certificate-authority=/data/apps/kubernetes/pki/ca.pem \
--embed-certs=true \
--server=${KUBE_APISERVER} \
--kubeconfig=kubelet-bootstrap.kubeconfig
Cluster "kubernetes" set.

# kubectl config set-credentials kubelet-bootstrap \
--token=${BOOTSTRAP_TOKEN} \
--kubeconfig=kubelet-bootstrap.kubeconfig
User "kubelet-bootstrap" set.

# kubectl config set-context default \
--cluster=kubernetes \
--user=kubelet-bootstrap \
--kubeconfig=kubelet-bootstrap.kubeconfig
Context "default" created.

# kubectl config use-context default --kubeconfig=kubelet-bootstrap.kubeconfig
Switched to context "default".
```

二、创建 kube-controller-manager kubeconfig
```
[root@K8S-PROD-MASTER-A1 kubernetes]# kubectl config set-cluster kubernetes \
--certificate-authority=/data/apps/kubernetes/pki/ca.pem \
--embed-certs=true \
--server=${KUBE_APISERVER} \
--kubeconfig=kube-controller-manager.kuconfig

[root@K8S-PROD-MASTER-A1 kubernetes]# kubectl config set-credentials kube-controller-manager \
--client-certificate=/data/apps/kubernetes/pki/kube-controller-manager.pem \
--client-key=/data/apps/kubernetes/pki/kube-controller-manager-key.pem \
--embed-certs=true \
--kubeconfig=kube-controller-manager.kubeconfig

[root@K8S-PROD-MASTER-A1 kubernetes]# kubectl config set-context default \
--cluster=kubernetes \
--user=kube-controller-manager \
--kubeconfig=kube-controller-manager.kubeconfig

[root@K8S-PROD-MASTER-A1 kubernetes]# kubectl config use-context default --kubeconfig=kube-controller-manager.kubeconfig
```

三、创建 kube-scheduler kubeconfig
```
kubectl config set-cluster kubernetes \
--certificate-authority=/data/apps/kubernetes/pki/ca.pem \
--embed-certs=true \
--server=${KUBE_APISERVER} \
--kubeconfig=kube-scheduler.kubeconfig

kubectl config set-credentials kube-scheduler \
--client-certificate=/data/apps/kubernetes/pki/kube-scheduler.pem \
--client-key=/data/apps/kubernetes/pki/kube-scheduler-key.pem \
--embed-certs=true \
--kubeconfig=kube-scheduler.kubeconfig

kubectl config set-context default \
--cluster=kubernetes \
--user=kube-scheduler \
--kubeconfig=kube-scheduler.kubeconfig

kubectl config use-context default --kubeconfig=kube-scheduler.kubeconfig
```

四、创建 kube-proxy kubeconfig
```
kubectl config set-cluster kubernetes \
--certificate-authority=/data/apps/kubernetes/pki/ca.pem \
--embed-certs=true \
--server=${KUBE_APISERVER} \
--kubeconfig=kube-proxy.kubeconfig

kubectl config set-credentials kube-proxy \
--client-certificate=/data/apps/kubernetes/pki/kube-proxy.pem \
--client-key=/data/apps/kubernetes/pki/kube-proxy-key.pem \
--embed-certs=true \
--kubeconfig=kube-proxy.kubeconfig

kubectl config set-context default \
--cluster=kubernetes \
--user=kube-proxy \
--kubeconfig=kube-proxy.kubeconfig

kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig
```

五、创建 admin kubeconfig
```
kubectl config set-cluster kubernetes \
--certificate-authority=/data/apps/kubernetes/pki/ca.pem \
--embed-certs=true \
--server=${KUBE_APISERVER} \
--kubeconfig=admin.conf

kubectl config set-credentials admin \
--client-certificate=/data/apps/kubernetes/pki/admin.pem \
--client-key=/data/apps/kubernetes/pki/admin-key.pem \
--embed-certs=true \
--kubeconfig=admin.conf

kubectl config set-context default \
--cluster=kubernetes \
--user=admin \
--kubeconfig=admin.conf

kubectl config use-context default --kubeconfig=admin.conf
```

六、分发kubelet/kube-proxy配置文件

1、分发配置文件到node节点
```
[root@K8S-PROD-MASTER-A1 kubernetes]# rsync  -avz --exclude=kube-scheduler.kubeconfig --exclude=kube-controller-manager.kubeconfig --exclude=admin.conf --exclude=token.csv etc 10.211.18.11:/data/apps/kubernetes

sending incremental file list
etc/
etc/kube-proxy.kubeconfig
etc/kubelet-bootstrap.kubeconfig

sent 5,842 bytes  received 58 bytes  1,311.11 bytes/sec
total size is 8,482  speedup is 1.44
```

2、分发配置文件到其他master节点

配置kube-apiserver 
===
kube-apiserver 是 Kubernetes 最重要的核心组件之一，主要提供以下的功能
- 提供集群管理的 REST API 接口，包括认证授权、数据校验以及集群状态变更等
- 提供其他模块之间的数据交互和通信的枢纽（其他模块通过 API Server 查询或修改数据，只有 API Server 才直接操作 etcd）
```
[root@K8S-PROD-MASTER-A1 kubernetes]# cd /data/apps/kubernetes/pki/
[root@K8S-PROD-MASTER-A1 pki]# openssl genrsa -out /data/apps/kubernetes/pki/sa.key 2048
Generating RSA private key, 2048 bit long modulus
...............+++
......+++
e is 65537 (0x10001)
[root@K8S-PROD-MASTER-A1 pki]# openssl rsa -in /data/apps/kubernetes/pki/sa.key -pubout -out /data/apps/kubernetes/pki/sa.pub
writing RSA key
[root@K8S-PROD-MASTER-A1 pki]# ls -l sa.*
-rw-r--r-- 1 root root 1679 Mar 14 11:49 sa.key
-rw-r--r-- 1 root root  451 Mar 14 11:49 sa.pub
```
分发文件到其他apiserver节点
```
[root@K8S-PROD-MASTER-A1 pki]# scp -r /data/apps/kubernetes/pki/sa.* 10.211.18.5:/data/apps/kubernetes/pki/
[root@K8S-PROD-MASTER-A1 pki]# scp -r /data/apps/kubernetes/pki/sa.* 10.211.18.6:/data/apps/kubernetes/pki/

[root@K8S-PROD-MASTER-A1 kubernetes]# scp -r /data/apps/kubernetes/etc 10.211.18.5:/data/apps/kubernetes/
[root@K8S-PROD-MASTER-A1 kubernetes]# scp -r /data/apps/kubernetes/etc 10.211.18.6:/data/apps/kubernetes/
```

配置apiserver系统服务

1、分别在10.211.18.4、10.211.18.5、10.211.18.6三台主机执行如下命令。
```
cat > /usr/lib/systemd/system/kube-apiserver.service << EOF
[Unit]
Description=Kubernetes API Service
Documentation=https://github.com/kubernetes/kubernetes
After=network.target

[Service]
EnvironmentFile=-/data/apps/kubernetes/etc/kube-apiserver.conf
ExecStart=/data/apps/kubernetes/server/bin/kube-apiserver \\
\$KUBE_LOGTOSTDERR \\
\$KUBE_LOG_LEVEL \\
\$KUBE_ETCD_ARGS \\
\$KUBE_API_ADDRESS \\
\$KUBE_SERVICE_ADDRESSES \\
\$KUBE_ADMISSION_CONTROL \\
\$KUBE_APISERVER_ARGS
Restart=on-failure
Type=notify
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```


2、创建apiserver配置文件
```
···
[root@K8S-PROD-MASTER-A1 etc]# cat >/data/apps/kubernetes/etc/kube-apiserver.conf <<EOF
KUBE_API_ADDRESS="--advertise-address=10.211.18.4"

KUBE_ETCD_ARGS="--etcd-servers=https://10.211.18.4:2379,https://10.211.18.5:2379,https://10.211.18.6:2379 \
--etcd-cafile=/data/apps/etcd/ssl/etcd-ca.pem \
--etcd-certfile=/data/apps/etcd/ssl/etcd.pem \
--etcd-keyfile=/data/apps/etcd/ssl/etcd-key.pem"

KUBE_LOGTOSTDERR="--logtostderr=false"
KUBE_LOG_LEVEL=" --log-dir=/data/apps/kubernetes/log/  --v=2 \
--audit-log-maxage=7 \
--audit-log-maxbackup=10  \
--audit-log-maxsize=100 \
--audit-log-path=/data/apps/kubernetes/log/kubernetes.audit --event-ttl=12h"


KUBE_SERVICE_ADDRESSES="--service-cluster-ip-range=10.99.0.0/16"
KUBE_ADMISSION_CONTROL="--enable-admission-plugins=NamespaceLifecycle,LimitRanger,ServiceAccount,DefaultStorageClass,DefaultTolerationSeconds,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota,PersistentVolumeClaimResize,PodPreset"

KUBE_APISERVER_ARGS="--storage-backend=etcd3 \
--apiserver-count=3 \
--endpoint-reconciler-type=lease \
--runtime-config=api/all,settings.k8s.io/v1alpha1=true,admissionregistration.k8s.io/v1beta1 \
--enable-admission-plugins=Initializers \
--allow-privileged=true \
--authorization-mode=Node,RBAC \
--enable-bootstrap-token-auth=true \
--token-auth-file=/data/apps/kubernetes/etc/token.csv \
--service-node-port-range=30000-40000 \
--tls-cert-file=/data/apps/kubernetes/pki/kube-apiserver.pem \
--tls-private-key-file=/data/apps/kubernetes/pki/kube-apiserver-key.pem \
--client-ca-file=/data/apps/kubernetes/pki/ca.pem \
--service-account-key-file=/data/apps/kubernetes/pki/sa.pub \
--enable-swagger-ui=false \
--secure-port=6443 \
--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname \
--anonymous-auth=false \
--kubelet-client-certificate=/data/apps/kubernetes/pki/admin.pem \
--kubelet-client-key=/data/apps/kubernetes/pki/admin-key.pem "
EOF
```

3、分别启动三台apiserver
```
[root@K8S-PROD-MASTER-A1 etc]# mkdir –p /data/apps/kubernetes/log
[root@K8S-PROD-MASTER-A1 etc]# systemctl daemon-reload
[root@K8S-PROD-MASTER-A1 etc]# systemctl enable kube-apiserver
Created symlink from /etc/systemd/system/multi-user.target.wants/kube-apiserver.service to /usr/lib/systemd/system/kube-apiserver.service.

[root@K8S-PROD-MASTER-A1 etc]# systemctl start kube-apiserver
[root@K8S-PROD-MASTER-A1 etc]# systemctl status kube-apiserver
```


访问测试,出现一下内容说明搭建成功：
```
curl -k https://10.211.18.4:6443

{
"kind": "Status",
"apiVersion": "v1",
"metadata": {

},
"status": "Failure",
"message": "Unauthorized",
"reason": "Unauthorized",
"code": 401
}
```

配置apiserver高可用部署
===
 
![image](https://github.com/mykubernetes/kubernetes/blob/master/deploy/image/kuber1.png)

安装相关软件包
```
10.211.18.4   apiserver-0
10.211.18.5   apiserver-1
10.211.18.6   apiserver-2

分别在apiserver集群节点安装haproxy、keepalived
yum install haproxy keepalived -y
```


配置haproxy
1、在Master-A1执行如下命令
```
[root@K8S-PROD-MASTER-A1 ~]# cd /etc/haproxy/
[root@K8S-PROD-MASTER-A1 haproxy]# cp haproxy.cfg{,.bak} 
[root@K8S-PROD-MASTER-A1 haproxy]# > haproxy.cfg
···

依次在其他apiserver节点创建haproxy.cfg配置文件
···
[root@K8S-PROD-MASTER-A1 haproxy]# vi haproxy.cfg 

global
    log 127.0.0.1 local2
    chroot /var/lib/haproxy
    pidfile /var/run/haproxy.pid
    maxconn 4000
    user haproxy
    group haproxy
    daemon
    stats socket /var/lib/haproxy/stats

defaults
    mode tcp
    log global
    retries 3
    option tcplog
    option httpclose
    option dontlognull
    option abortonclose
    option redispatch
    maxconn 32000
    timeout connect 5000ms
    timeout client 2h
    timeout server 2h

listen stats
    mode http
    bind :10086
    stats enable
    stats uri /admin?stats
    stats auth admin:admin
    stats admin if TRUE

frontend k8s_apiserver 
    bind *:8443
    mode tcp
    default_backend https_sri

backend https_sri
    balance roundrobin
server apiserver1_10_211_18_4 10.211.18.4:6443 check inter 2000 fall 2 rise 2 weight 100
server apiserver2_10_211_18_5 10.211.18.5:6443 check inter 2000 fall 2 rise 2 weight 100
server apiserver3_10_211_18_6 10.211.18.6:6443 check inter 2000 fall 2 rise 2 weight 100
```

2、在Master-A2执行如下命令
```
[root@K8S-PROD-MASTER-A2 ~]# cd /etc/haproxy/
[root@K8S-PROD-MASTER-A2 haproxy]# cp haproxy.cfg{,.bak} 
[root@K8S-PROD-MASTER-A2 haproxy]# > haproxy.cfg

 [root@K8S-PROD-MASTER-A2 haproxy]# vi haproxy.cfg 
global
    log 127.0.0.1 local2
    chroot /var/lib/haproxy
    pidfile /var/run/haproxy.pid
    maxconn 4000
    user haproxy
    group haproxy
    daemon
    stats socket /var/lib/haproxy/stats

defaults
    mode tcp
    log global
    retries 3
    option tcplog
    option httpclose
    option dontlognull
    option abortonclose
    option redispatch
    maxconn 32000
    timeout connect 5000ms
    timeout client 2h
    timeout server 2h

listen stats
    mode http
    bind :10086
    stats enable
    stats uri /admin?stats
    stats auth admin:admin
    stats admin if TRUE

frontend k8s_apiserver 
    bind *:8443
    mode tcp
    default_backend https_sri

backend https_sri
    balance roundrobin
server apiserver1_10_211_18_4 10.211.18.4:6443 check inter 2000 fall 2 rise 2 weight 100
server apiserver2_10_211_18_5 10.211.18.5:6443 check inter 2000 fall 2 rise 2 weight 100
server apiserver3_10_211_18_6 10.211.18.6:6443 check inter 2000 fall 2 rise 2 weight 100
```

3、在Master-A3执行如下命令
```
[root@K8S-PROD-MASTER-A3 ~]# cd /etc/haproxy/
[root@K8S-PROD-MASTER-A3 haproxy]# cp haproxy.cfg{,.bak} 
[root@K8S-PROD-MASTER-A3 haproxy]# > haproxy.cfg

[root@K8S-PROD-MASTER-A3 haproxy]# vi haproxy.cfg 

global
    log 127.0.0.1 local2
    chroot /var/lib/haproxy
    pidfile /var/run/haproxy.pid
    maxconn 4000
    user haproxy
    group haproxy
    daemon
    stats socket /var/lib/haproxy/stats

defaults
    mode tcp
    log global
    retries 3
    option tcplog
    option httpclose
    option dontlognull
    option abortonclose
    option redispatch
    maxconn 32000
    timeout connect 5000ms
    timeout client 2h
    timeout server 2h

listen stats
    mode http
    bind :10086
    stats enable
    stats uri /admin?stats
    stats auth admin:admin
    stats admin if TRUE

frontend k8s_apiserver 
    bind *:8443
    mode tcp
    default_backend https_sri

backend https_sri
    balance roundrobin
server apiserver1_10_211_18_4 10.211.18.4:6443 check inter 2000 fall 2 rise 2 weight 100
server apiserver2_10_211_18_5 10.211.18.5:6443 check inter 2000 fall 2 rise 2 weight 100
server apiserver3_10_211_18_6 10.211.18.6:6443 check inter 2000 fall 2 rise 2 weight 100
```

配置keepalived
```
[root@K8S-PROD-MASTER-A1 haproxy]# cd /etc/keepalived/
[root@K8S-PROD-MASTER-A1 keepalived]# cp keepalived.conf{,.bak}  
[root@K8S-PROD-MASTER-A1 keepalived]#  > keepalived.conf
```
1、Master-A1节点
```
[root@K8S-PROD-MASTER-A1 keepalived]# vi keepalived.conf

! Configuration File for keepalived  
global_defs {  
    notification_email {   
        test@test.com   
    }   
    notification_email_from admin@test.com  
    smtp_server 127.0.0.1  
    smtp_connect_timeout 30  
    router_id LVS_MASTER_APISERVER
}  

vrrp_script check_haproxy {
    script "/etc/keepalived/check_haproxy.sh"
    interval 3
}  

vrrp_instance VI_1 {  
    state MASTER
    interface ens33
    virtual_router_id 60  
    priority 100
    advert_int 1  
    authentication {  
        auth_type PASS  
        auth_pass 1111  
}  
    unicast_peer {
    10.211.18.4
    10.211.18.5
    10.211.18.6
    }
    virtual_ipaddress {  
        10.211.18.10/24 label ens33:0
}

    track_script {   
        check_haproxy
    }
}
```
注意： 
其他两个节点state MASTER 字段需改为state BACKUP,  priority 100 需要分别设置90 80

```
[root@K8S-PROD-MASTER-A2 haproxy]# cd /etc/keepalived/
[root@K8S-PROD-MASTER-A2 keepalived]# cp keepalived.conf{,.bak}  
[root@K8S-PROD-MASTER-A2 keepalived]#  > keepalived.conf

[root@K8S-PROD-MASTER-A2 keepalived]# vi keepalived.conf

! Configuration File for keepalived  
global_defs {  
    notification_email {   
        test@test.com   
    }   
    notification_email_from admin@test.com  
    smtp_server 127.0.0.1  
    smtp_connect_timeout 30  
    router_id LVS_MASTER_APISERVER
}  

vrrp_script check_haproxy {
    script "/etc/keepalived/check_haproxy.sh"
    interval 3
}  

vrrp_instance VI_1 {  
    state BACKUP
    interface ens33
    virtual_router_id 60  
    priority 90
    advert_int 1  
    authentication {  
        auth_type PASS  
        auth_pass 1111  
}  
    unicast_peer {
    10.211.18.4
    10.211.18.5
    10.211.18.6
    }
    virtual_ipaddress {  
        10.211.18.10/24 label ens33:0
    }

    track_script {   
        check_haproxy
    }
}
```

创建keepalived配置文件
```
[root@K8S-PROD-MASTER-A3 haproxy]# cd /etc/keepalived/
[root@K8S-PROD-MASTER-A3 keepalived]# cp keepalived.conf{,.bak}  
[root@K8S-PROD-MASTER-A3 keepalived]#  > keepalived.conf


[root@K8S-PROD-MASTER-A3 keepalived]# vi keepalived.conf

! Configuration File for keepalived  
global_defs {  
    notification_email {   
        test@test.com   
    }   
    notification_email_from admin@test.com  
    smtp_server 127.0.0.1  
    smtp_connect_timeout 30  
    router_id LVS_MASTER_APISERVER
}  

vrrp_script check_haproxy {
    script "/etc/keepalived/check_haproxy.sh"
    interval 3
}  

vrrp_instance VI_1 {  
    state BACKUP
    interface ens33
    virtual_router_id 60  
    priority 80
    advert_int 1  
    authentication {  
        auth_type PASS  
        auth_pass 1111  
}  
    unicast_peer {
    10.211.18.4
    10.211.18.5
    10.211.18.6
    }
    virtual_ipaddress {  
        10.211.18.10/24 label ens33:0
    }

    track_script {   
        check_haproxy
    }
}
```


所有节点(Master1~Master3)需要配置检查脚本（check_haproxy.sh）, 当haproxy挂掉后自动停止keepalived
```
[root@K8S-PROD-MASTER-A1 keepalived]# vi /etc/keepalived/check_haproxy.sh

#!/bin/bash

flag=$(systemctl status haproxy &> /dev/null;echo $?)

if [[ $flag != 0 ]];then
echo "haproxy is down,close the keepalived"
systemctl stop keepalived
fi
```

2、修改系统服务
```
[root@K8S-PROD-MASTER-A1 keepalived]#  vi /usr/lib/systemd/system/keepalived.service

[Unit]
Description=LVS and VRRP High Availability Monitor
After=syslog.target network-online.target
Requires=haproxy.service    #增加该字段
[Service]
Type=forking
PIDFile=/var/run/keepalived.pid
KillMode=process
EnvironmentFile=-/etc/sysconfig/keepalived
ExecStart=/usr/sbin/keepalived $KEEPALIVED_OPTIONS
ExecReload=/bin/kill -HUP $MAINPID

[Install]
WantedBy=multi-user.target
```


firewalld放行VRRP协议
```
firewall-cmd --direct --permanent --add-rule ipv4 filter INPUT 0 --in-interface ens33 --destination 224.0.0.18 --protocol vrrp -j ACCEPT
firewall-cmd --reload
```
注意：--in-interface ens33请修改为实际网卡名称


登录apiserver节点启动以下服务
```
[root@K8S-PROD-MASTER-A1 haproxy]# systemctl enable haproxy 
Created symlink from /etc/systemd/system/multi-user.target.wants/haproxy.service to /usr/lib/systemd/system/haproxy.service.


[root@K8S-PROD-MASTER-A1 haproxy]# systemctl  start haproxy
[root@K8S-PROD-MASTER-A1 haproxy]# systemctl  status haproxy
● haproxy.service - HAProxy Load Balancer
   Loaded: loaded (/usr/lib/systemd/system/haproxy.service; enabled; vendor preset: disabled)
   Active: active (running) since Mon 2019-04-29 10:19:21 CST; 6h ago
 Main PID: 5304 (haproxy-systemd)
   CGroup: /system.slice/haproxy.service
           ├─5304 /usr/sbin/haproxy-systemd-wrapper -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid
           ├─5308 /usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid -Ds
           └─5344 /usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid -Ds

Apr 29 10:19:21 K8S-PROD-MASTER-A1 systemd[1]: Started HAProxy Load Balancer.
Apr 29 10:19:21 K8S-PROD-MASTER-A1 haproxy-systemd-wrapper[5304]: haproxy-systemd-wrapper: executing /usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid –Ds



[root@K8S-PROD-MASTER-A1 keepalived]# systemctl enable keepalived
Created symlink from /etc/systemd/system/multi-user.target.wants/keepalived.service to /usr/lib/systemd/system/keepalived.service.

[root@K8S-PROD-MASTER-A1 keepalived]# systemctl  start keepalived 
[root@K8S-PROD-MASTER-A1 keepalived]# systemctl  status keepalived
● keepalived.service - LVS and VRRP High Availability Monitor
   Loaded: loaded (/usr/lib/systemd/system/keepalived.service; enabled; vendor preset: disabled)
   Active: active (running) since Mon 2019-04-29 10:19:28 CST; 4h 2min ago
 Main PID: 5355 (keepalived)
   CGroup: /system.slice/keepalived.service
           ├─5355 /usr/sbin/keepalived -D
           ├─5356 /usr/sbin/keepalived -D
           └─5357 /usr/sbin/keepalived -D

Apr 29 10:21:32 K8S-PROD-MASTER-A1 Keepalived_vrrp[5357]: Sending gratuitous ARP on ens33 for 10.211.18.10
Apr 29 10:21:32 K8S-PROD-MASTER-A1 Keepalived_vrrp[5357]: Sending gratuitous ARP on ens33 for 10.211.18.10
Apr 29 10:21:32 K8S-PROD-MASTER-A1 Keepalived_vrrp[5357]: Sending gratuitous ARP on ens33 for 10.211.18.10
Apr 29 10:21:32 K8S-PROD-MASTER-A1 Keepalived_vrrp[5357]: Sending gratuitous ARP on ens33 for 10.211.18.10
Apr 29 10:21:37 K8S-PROD-MASTER-A1 Keepalived_vrrp[5357]: Sending gratuitous ARP on ens33 for 10.211.18.10
Apr 29 10:21:37 K8S-PROD-MASTER-A1 Keepalived_vrrp[5357]: VRRP_Instance(VI_1) Sending/queueing gratuitous ARPs on ens33 for 10.211.18.10
```

执行ip a命令， 查看浮动IP

![image](https://github.com/mykubernetes/kubernetes/blob/master/deploy/image/kuber2.png) 


http://10.211.18.10:10086/admin?stats 登录haproxy，查看服务是否正常

![image](https://github.com/mykubernetes/kubernetes/blob/master/deploy/image/kuber3.png) 


配置启动kube-controller-manager
---
kube-controller-manager 负责维护集群的状态，比如故障检测、自动扩展、滚动更新等

在启动时设置 --leader-elect=true 后，controller manager 会使用多节点选主的方式选择主节点。只有主节点才会调用 StartControllers() 启动所有控制器，而其他从节点则仅执行选主算法。
 
1、执行如下创建系统服务文件
```
[root@K8S-PROD-MASTER-A1 software]#  cat > /usr/lib/systemd/system/kube-controller-manager.service << EOF
Description=Kubernetes Controller Manager
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/data/apps/kubernetes/etc/kube-controller-manager.conf
ExecStart=/data/apps/kubernetes/server/bin/kube-controller-manager \
$KUBE_LOGTOSTDERR \
$KUBE_LOG_LEVEL \
$KUBECONFIG \
$KUBE_CONTROLLER_MANAGER_ARGS

Restart=always
RestartSec=10s

#Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

2、创建kube-controller-manager.conf配置文件
```
[root@K8S-PROD-MASTER-A2 etc]# cat > /data/apps/kubernetes/etc/kube-controller-manager.conf <<EOF
KUBE_LOGTOSTDERR="--logtostderr=false"
KUBE_LOG_LEVEL="--v=2 --log-dir=/data/apps/kubernetes/log/"


KUBECONFIG="--kubeconfig=/data/apps/kubernetes/etc/kube-controller-manager.kubeconfig"

KUBE_CONTROLLER_MANAGER_ARGS="--bind-address=127.0.0.1 \
--cluster-cidr=10.99.0.0/16 \
--cluster-name=kubernetes \
--cluster-signing-cert-file=/data/apps/kubernetes/pki/ca.pem \
--cluster-signing-key-file=/data/apps/kubernetes/pki/ca-key.pem \
--service-account-private-key-file=/data/apps/kubernetes/pki/sa.key \
--root-ca-file=/data/apps/kubernetes/pki/ca.pem \
--leader-elect=true \
--use-service-account-credentials=true \
--node-monitor-grace-period=10s \
--pod-eviction-timeout=10s \
--allocate-node-cidrs=true \
--controllers=*,bootstrapsigner,tokencleaner \
--horizontal-pod-autoscaler-use-rest-clients=true \
--experimental-cluster-signing-duration=87600h0m0s \
--feature-gates=RotateKubeletServerCertificate=true""
EOF
```
3、启动kube-controller-manager
```
systemctl daemon-reload
systemctl enable kube-controller-manager
systemctl start kube-controller-manager

systemctl status kube-controller-manager
```



配置kubectl
---
```
[root@K8S-PROD-MASTER-A1 pki]# rm -rf $HOME/.kube
[root@K8S-PROD-MASTER-A1 pki]# mkdir -p $HOME/.kube
[root@K8S-PROD-MASTER-A1 pki]# cp  /data/apps/kubernetes/etc/admin.conf  $HOME/.kube/config
[root@K8S-PROD-MASTER-A1 pki]# sudo chown $(id -u):$(id -g) $HOME/.kube/config
[root@K8S-PROD-MASTER-A1 pki]# kubectl get node
```

查看各个组件的状态
```
kubectl get componentstatuses


[root@K8S-PROD-MASTER-A1 pki]# kubectl get componentstatuses
NAME               STATUS    MESSAGE   ERROR
controller-manager Healthy   ok
scheduler          Healthy   ok
etcd-1             Healthy {"health": "true"}
etcd-0             Healthy {"health": "true"}
etcd-2             Healthy {"health": "true"}
```

配置kubelet使用bootstrap
```
[root@K8S-PROD-MASTER-A1 pki]#  kubectl create clusterrolebinding kubelet-bootstrap \
--clusterrole=system:node-bootstrapper \
--user=kubelet-bootstrap
```

配置启动kube-scheduler
---
kube-scheduler 负责分配调度 Pod 到集群内的节点上，它监听 kube-apiserver，查询还未分配 Node 的 Pod，然后根据调度策略为这些 Pod 分配节点。按照预定的调度策略将 Pod 调度到相应的机器上（更新 Pod 的 NodeName 字段）。 
 
1、执行如下创建系统服务文件
```
[root@K8S-PROD-MASTER-A2 etc]# cat > /usr/lib/systemd/system/kube-scheduler.service << EOF
[Unit]
Description=Kubernetes Scheduler Plugin
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/data/apps/kubernetes/etc/kube-scheduler.conf
ExecStart=/data/apps/kubernetes/server/bin/kube-scheduler \
$KUBE_LOGTOSTDERR \
$KUBE_LOG_LEVEL \
$KUBECONFIG \
$KUBE_SCHEDULER_ARGS
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

2、创建kube-scheduler.conf配置文件
```
[root@K8S-PROD-MASTER-A2 etc]#  cat > /data/apps/kubernetes/etc/kube-scheduler.conf << EOF
KUBE_LOGTOSTDERR="--logtostderr=false"
KUBE_LOG_LEVEL="--v=2 --log-dir=/data/apps/kubernetes/log/"

KUBECONFIG="--kubeconfig=/data/apps/kubernetes/etc/kube-scheduler.kubeconfig"
KUBE_SCHEDULER_ARGS="--leader-elect=true --address=127.0.0.1" 
EOF
```

3、启动kube-scheduler， 并设置服务开机自启动
```
systemctl daemon-reload
systemctl enable kube-scheduler
systemctl start kube-scheduler
systemctl  status kube-scheduler
```


部署Node节点
===
配置kubelet
---
kubelet 负责维持容器的生命周期，同时也负责 Volume（CVI）和网络（CNI）的管理；

每个节点上都运行一个 kubelet 服务进程，默认监听 10250 端口，接收并执行 master 发来的指令，管理 Pod 及 Pod 中的容器。每个 kubelet 进程会在 API Server 上注册节点自身信息，定期向 master 节点汇报节点的资源使用情况，并通过 cAdvisor/metric-server 监控节点和容器的资源。
 
配置并启动kubelet， flanneld (master与node节点都需要安装)

在Master节点配置kubelet
```
[root@K8S-PROD-MASTER-A1 pki]# cat > /usr/lib/systemd/system/kubelet.service << EOF
[Unit]
Description=Kubernetes Kubelet Server
Documentation=https://github.com/kubernetes/kubernetes
After=docker.service
Requires=docker.service

[Service]
EnvironmentFile=-/data/apps/kubernetes/etc/kubelet.conf
ExecStart=/data/apps/kubernetes/node/bin/kubelet \\
\$KUBE_LOGTOSTDERR \\
\$KUBE_LOG_LEVEL \\
\$KUBELET_CONFIG \\
\$KUBELET_HOSTNAME \\
\$KUBELET_POD_INFRA_CONTAINER \\
\$KUBELET_ARGS
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```
创建kubelet配置文件
```
[root@K8S-PROD-MASTER-A1 pki]# cat > /data/apps/kubernetes/etc/kubelet.conf << EOF
KUBE_LOGTOSTDERR="--logtostderr=false"
KUBE_LOG_LEVEL="--v=2 --log-dir=/data/apps/kubernetes/log/"

KUBELET_HOSTNAME="--hostname-override=10.211.18.4"
KUBELET_POD_INFRA_CONTAINER="--pod-infra-container-image=registry.cn-hangzhou.aliyuncs.com/google_containers/pause-amd64:3.1"
KUBELET_CONFIG="--config=/data/apps/kubernetes/etc/kubelet-config.yml"
KUBELET_ARGS="--bootstrap-kubeconfig=/data/apps/kubernetes/etc/kubelet-bootstrap.kubeconfig \
--kubeconfig=/data/apps/kubernetes/etc/kubelet.kubeconfig \
--cert-dir=/data/apps/kubernetes/pki \
--feature-gates=RotateKubeletClientCertificate=true \
--system-reserved=memory=300Mi \
--kube-reserved=memory=400Mi \
--eviction-hard=imagefs.available<15%,memory.available<300Mi,nodefs.available<10%,nodefs.inodesFree<5%"
EOF
```
```
[root@K8S-PROD-MASTER-A1 pki]# cat > /data/apps/kubernetes/etc/kubelet-config.yml << EOF
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
address: 10.211.18.4
port: 10250
cgroupDriver: cgroupfs
clusterDNS:
  - 10.99.110.110
clusterDomain: ziji.work.
hairpinMode: promiscuous-bridge
maxPods: 200
failSwapOn: false
imageGCHighThresholdPercent: 90
imageGCLowThresholdPercent: 80
imageMinimumGCAge: 5m0s
serializeImagePulls: false
authentication:
  x509:
    clientCAFile: /data/apps/kubernetes/pki/ca.pem
  anonymous:
    enbaled: false
  webhook:
    enbaled: false
EOF
```
启动kubelet
```
[root@K8S-PROD-MASTER-A1 pki]# systemctl daemon-reload
[root@K8S-PROD-MASTER-A1 pki]# systemctl enable kubelet
[root@K8S-PROD-MASTER-A1 pki]# systemctl restart kubelet
[root@K8S-PROD-MASTER-A1 pki]# systemctl  status kubelet 
● kubelet.service - Kubernetes Kubelet Server
   Loaded: loaded (/usr/lib/systemd/system/kubelet.service; enabled; vendor preset: disabled)
   Active: active (running) since Mon 2019-04-29 18:35:33 CST; 13s ago
     Docs: https://github.com/kubernetes/kubernetes
 Main PID: 29401 (kubelet)
    Tasks: 8
   Memory: 13.0M
   CGroup: /system.slice/kubelet.service
           └─29401 /data/apps/kubernetes/server/bin/kubelet --logtostderr=true --v=0 --config=/data/apps/kubernetes/etc/kubelet-config.yml --hostname-override=10.211.18.4 --pod-infra-container-i...

Apr 29 18:35:33 K8S-PROD-MASTER-A1 systemd[1]: kubelet.service holdoff time over, scheduling restart.
Apr 29 18:35:33 K8S-PROD-MASTER-A1 systemd[1]: Stopped Kubernetes Kubelet Server.
Apr 29 18:35:33 K8S-PROD-MASTER-A1 systemd[1]: Started Kubernetes Kubelet Server.
Apr 29 18:35:33 K8S-PROD-MASTER-A1 kubelet[29401]: I0429 18:35:33.694991   29401 server.go:407] Version: v1.13.4
Apr 29 18:35:33 K8S-PROD-MASTER-A1 kubelet[29401]: I0429 18:35:33.695245   29401 plugins.go:103] No cloud provider specified.
Apr 29 18:35:33 K8S-PROD-MASTER-A1 kubelet[29401]: E0429 18:35:33.699058   29401 bootstrap.go:184] Unable to read existing bootstrap client config: invalid configuration: [unable to read client-...
```

在Node节点配置kubelet
```
[root@K8S-PROD-NODE-A1 etc]#  cd software/
[root@K8S-PROD-NODE-A1 etc]#  tar zxf kubernetes-node-linux-amd64.tar.gz
[root@K8S-PROD-NODE-A1 etc]#  mv kubernetes/node  /data/apps/kubernetes/
```
```
[root@K8S-PROD-NODE-A1 etc]#  cat > /etc/systemd/system/kubelet.service << EOF
[Unit]
Description=Kubernetes Kubelet Server
Documentation=https://github.com/kubernetes/kubernetes
After=docker.service
Requires=docker.service

[Service]
EnvironmentFile=-/data/apps/kubernetes/etc/kubelet.conf
ExecStart=/data/apps/kubernetes/node/bin/kubelet \\
\$KUBE_LOGTOSTDERR \\
\$KUBE_LOG_LEVEL \\
\$KUBELET_CONFIG \\
\$KUBELET_HOSTNAME \\
\$KUBELET_POD_INFRA_CONTAINER \\
\$KUBELET_ARGS
Restart=on-failure

[Install]
WantedBy=multi-user.target 
EOF
```

```
[root@K8S-PROD-NODE-A1 etc]# cat > /data/apps/kubernetes/etc/kubelet << EOF
KUBE_LOGTOSTDERR="--logtostderr=false"
KUBE_LOG_LEVEL="--v=2 --log-dir=/data/apps/kubernetes/log/"

KUBELET_HOSTNAME="--hostname-override=10.211.18.11"
KUBELET_POD_INFRA_CONTAINER="--pod-infra-container-image=registry.cn-hangzhou.aliyuncs.com/google_containers/pause-amd64:3.1"
KUBELET_CONFIG="--config=/data/apps/kubernetes/etc/kubelet-config.yml"
KUBELET_ARGS="--bootstrap-kubeconfig=/data/apps/kubernetes/etc/kubelet-bootstrap.kubeconfig \
--kubeconfig=/data/apps/kubernetes/etc/kubelet.kubeconfig \
--cert-dir=/data/apps/kubernetes/pki \
--system-reserved=memory=300Mi \
--kube-reserved=memory=400Mi \
--eviction-hard=imagefs.available<15%,memory.available<300Mi,nodefs.available<10%,nodefs.inodesFree<5%"
EOF
```

```
[root@K8S-PROD-NODE-A1 etc]# cat > /data/apps/kubernetes/etc/kubelet-config.yml << EOF
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
address: 10.211.18.11
port: 10250
cgroupDriver: cgroupfs
clusterDNS:
  - 10.99.110.110
clusterDomain: ziji.work.
hairpinMode: promiscuous-bridge
maxPods: 200
failSwapOn: false
imageGCHighThresholdPercent: 90
imageGCLowThresholdPercent: 80
imageMinimumGCAge: 5m0s
serializeImagePulls: false
authentication:
  x509:
    clientCAFile: /data/apps/kubernetes/pki/ca.pem
  anonymous:
    enbaled: false
  webhook:
    enbaled: false
EOF
```
node1启动kubelet
```
[root@K8S-PROD-NODE-A1 etc]# systemctl daemon-reload
[root@K8S-PROD-NODE-A1 etc]# systemctl enable kubelet
[root@K8S-PROD-NODE-A1 etc]# systemctl restart kubelet
[root@K8S-PROD-NODE-A1 etc]# systemctl status kubelet
● kubelet.service - Kubernetes Kubelet Server
   Loaded: loaded (/usr/lib/systemd/system/kubelet.service; enabled; vendor preset: disabled)
   Active: active (running) since Fri 2019-03-22 11:55:33 CST; 14s ago
     Docs: https://github.com/kubernetes/kubernetes
 Main PID: 11124 (kubelet)
    Tasks: 8
   Memory: 13.1M
   CGroup: /system.slice/kubelet.service
           └─11124 /data/apps/kubernetes/node/bin/kubelet --logtostderr=true --v=0 --config=/data/apps/kubernetes/etc/kubelet-config.yml --hostname-override=10.211.18.11 --pod-infra-container-im...

Mar 22 11:55:33 K8S-PROD-NODE-A1 systemd[1]: kubelet.service holdoff time over, scheduling restart.
Mar 22 11:55:33 K8S-PROD-NODE-A1 systemd[1]: Stopped Kubernetes Kubelet Server.
Mar 22 11:55:33 K8S-PROD-NODE-A1 systemd[1]: Started Kubernetes Kubelet Server.
Mar 22 11:55:33 K8S-PROD-NODE-A1 kubelet[11124]: I0322 11:55:33.941658   11124 server.go:407] Version: v1.13.4
Mar 22 11:55:33 K8S-PROD-NODE-A1 kubelet[11124]: I0322 11:55:33.942154   11124 plugins.go:103] No cloud provider specified.
Mar 22 11:55:33 K8S-PROD-NODE-A1 kubelet[11124]: E0322 11:55:33.965594   11124 bootstrap.go:184] Unable to read existing bootstrap client config:
```







在node上操作
重复以上步骤， 修改kubelet-config.yml  address:地址为node节点ip, --hostname-override= 为node ip地址


