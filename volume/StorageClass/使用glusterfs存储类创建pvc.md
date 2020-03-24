介绍
1、GlustrerFS 介绍

(1)、GlusterFS 简介

GlusterFS 是一个可扩展，分布式文件系统，集成来自多台服务器上的磁盘存储资源到单一全局命名空间，已提供共享文件存储。

(2)、Gluster 优势

- 可以扩展到几PB容量
- 支持处理数千个客户端
- 兼容POSIX接口
- 使用通用硬件，普通服务器即可构建
- 能够使用支持扩展属性的文件系统，例如ext4，XFS
- 支持工业标准的协议，例如NFS，SMB
- 提供很多高级功能，例如副本，配额，跨地域复制，快照以及bitrot检测
- 支持根据不同工作负载进行调优

2、Heketi 介绍

(1)、Heketi 简介

提供基于RESTful接口管理glusterfs的功能，可以方便的创建集群管理 GlusterFS 的 node，device，volume 与 Kubernetes 结合可以创建动态的 PV，扩展 GlusterFS 存储的动态管理功能。

- Heketi动态在集群内选择bricks构建指定的volumes，以确保副本会分散到集群不同的故障域内。
- Heketi还支持任意数量的ClusterFS集群，以保证接入的云服务器不局限于单个GlusterFS集群。

三、GlusterFS 安装环境设置
1、安装要求

在 Kubernetes 下安装 GlusterFS 必须满足以下要求，否则安装可能会报错。

(1)、三个节点

GlusterFS 安装至少需要三个节点来组成 GlusterFS 存储集群，所以 Kubernetes 集群至少要有三个节点。

(2)、开放端口

每个节点必须为 GlusterFS 通信打开以下端口：

- 2222 - GlusterFS pod的sshd
- 24007 - GlusterFS守护程序
- 24008 - GlusterFS管理

(3)、原始块设备

每个节点必须至少连接一个原始块设备（如空的本地磁盘）供 heketi 使用。这些设备上不得有任何数据，因为它们将由 heketi 格式化和分区。简单意思就是需要一个没有数据的空的本地硬盘。

(4)、安装 glusterfs-fuse 工具

每个节点都要求该mount.glusterfs命令可用。在所有基于Red Hat的操作系统下，该命令由 glusterfs-fuse 包提供，所以需要安装 glusterfs-fuse 工具。

(5)、加载内核

必须加载以下内核模块：

- dm_snapshot
- dm_mirror
- dm_thin_pool

(6)、kube-apiserver 开启 privileged

GlusterFS 在 Kubernetes 集群中需要以特权运行，需要在 kube-apiserver 中添加“–allow-privileged=true”参数以开启此功能。
2、配置要求的环境

将以下配置设置到各个要安装 GlusterFS 节点的机器上。

(1)、查看 Kubernetes 集群是否有三个节点
```
$ kubectl get nodes

NAME              STATUS   ROLES    AGE   VERSION
k8s-master-2-11   Ready    master   49d   v1.14.0
k8s-node-2-12     Ready    <none>   49d   v1.14.0
k8s-node-2-13     Ready    <none>   49d   v1.14.0
k8s-node-2-14     Ready    <none>   13h   v1.14.0
```
(2)、开放端口

首先查看端口列表来查找下该端口，查看是否被占用，无法找到不存在则没问题。
```
$ netstat -ntlp | grep -E '2222|24007|24008'
```
这里为了方便，将关闭防火墙(一般 kubernetes 集群防火墙已经关闭，检查一下如果关闭则跳过即可)。
```
$ systemctl stop firewalld
$ systemctl disable firewalld
```
(3)、原始块设备

这里是挂载了一块硬盘，且没有分区，检查一下磁盘情况。
```
$ lsblk

NAME            MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda               8:0    0   50G  0 disk 
├─sda1            8:1    0    1G  0 part /boot
└─sda2            8:2    0   49G  0 part 
  ├─centos-root 253:0    0 45.1G  0 lvm  /
  └─centos-swap 253:1    0  3.9G  0 lvm  
sdb
sr0              11:0    1  4.3G  0 rom  
```
显示的 /sdb 即是新挂载的硬盘设备，且没有进行分区。

记住此硬盘符，下面配置时候需要使用。

(4)、安装 glusterfs-fuse 工具
```
$ yum -y install glusterfs-fuse
```
(5)、加载内核

加载模块
```
$ modprobe dm_snapshot
$ modprobe dm_mirror
$ modprobe dm_thin_pool
```
查看是否加载模块
```
$ lsmod | grep dm_snapshot
$ lsmod | grep dm_mirror
$ lsmod | grep dm_thin_pool
```
（6)、kube-apiserver 开启 privileged

如果 Kubernetes 集群是 Kuberadm 安装则该参数默认开启，不需要配置。

编辑 kube-apiserver.yaml
```
$ vim /etc/kubernetes/manifests/kube-apiserver.yaml
```
在参数列添加下面参数：
```
    - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
    - --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
    - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
    - --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt
    - --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key
    - --requestheader-allowed-names=front-proxy-client
    - --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt
    - ......（略,添加下面参数）
    - --allow-privileged=true
```
四、设置 GlusterFS 安装配置

以下操作将在 Kubernetes Master 节点上进行操作
1、节点贴标签

需要安装 GlusterFS 的 Kubernetes 点击上设置 Label，因为 GlusterFS 是通过 Kubernetes 集群的 “DaemonSet” 方式安装的。

DaemonSet 安装方式默认会在每个节点上都进行安装，除非安装前设置筛选要安装节点 Label，带上此标签的节点才会安装。

安装脚本中设置 DaemonSet 中设置安装在贴有 “storagenode=glusterfs” 的节点，所以这是事先将节点贴上对应 Label。

(1)、Kubernetes 节点设置标签
```
$ kubectl label node k8s-node-2-12 storagenode=glusterfs 
$ kubectl label node k8s-node-2-13 storagenode=glusterfs
$ kubectl label node k8s-node-2-14 storagenode=glusterfs
```
(2)、查看节点标签是否设置成功
```
$ kubectl get nodes --show-labels

NAME           STATUS   ROLES    AGE   VERSION   LABELS
k8s-node-2-12  Ready    <none>   13d   v1.14.0   IngressProxy=true,beta.kubernetes.io/arch=amd64,storage=glusterfs
k8s-node-2-13  Ready    <none>   13d   v1.14.0   IngressProxy=true,beta.kubernetes.io/arch=amd64,storage=glusterfs
k8s-node-2-14  Ready    <none>   13d   v1.14.0   IngressProxy=true,beta.kubernetes.io/arch=amd64,storage=glusterfs
```
2、准备部署文件

在 Kubernetes 集群中部署 GlusterFS 可以借助 gluster-kubernetes，gluster-kubernetes 是一个为 Kubernetes 管理员提供一种机制，可以将 GlusterFS 作为本机存储服务轻松部署到现有 Kubernetes 集群上的工具，让 GlusterFS 像 Kubernetes 中的任何其他应用程序一样进行管理和编排。这是在 Kubernetes 中释放动态配置的持久性 GlusterFS 卷的强大功能的便捷方式，下面将下载对应部署文件，执行部署脚本进行安装。

(1)、GitHub 拉取源码
```
$ git clone https://github.com/gluster/gluster-kubernetes.git
```
(2)、进入源码部署文件夹
```
$ cd gluster-kubernetes/deploy
```
(3)、改变部署文件名称

安装文件中提供了一个 topology.json.sample 文件，里面可以设置安装节点信息，但是官方默认后缀为 .json.sample，需要将 sample 后缀去掉变为 json 以生效。
```
$ mv topology.json.sample topology.json
```
3、修改配置文件

打开拓扑文件 topology.json，修改其中的默认配置对应我们当前的 Kubernetes 集群配置。
```
$ vi topology.json
```
例如这里改成对应我的 kubernetes 集群，为：
```
{
  "clusters": [
    {
      "nodes": [
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-12"
              ],
              "storage": [
                "192.168.2.12"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-13"
              ],
              "storage": [
                "192.168.2.13"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-14"
              ],
              "storage": [
                "192.168.2.14"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        }
      ]
    }
  ]
}
```
修改参数说明：
- manage： Kubernetes 需要安装 GlusterFS 的各个节点名称。
- sotrage： Kubernetes 节点对应的 IP 地址。
- devices： 节点系统上相应的磁盘块设备，可以通过 “fdisk -l” 命令查看，例如这里就是上面挂在的硬盘符 “/dev/sdb”。

五、Kubernetes 安装 GlusterFS
---
1、Kubernetes 创建 Namespace

Kubenetes 创建一个名称为 storage 的 Namespace，供 GlusterFS 使用 (当然，放在 kube-system 空间下亦可)
```
$ kubectl create namespace storage
```
2、部署 GlusterFS
- -n 是指定安装到 Kubernetes 集群下的 Namespace
- -g 是指创建新的集群
``
$ ./gk-deploy -g -n storage
``
安装日志信息：
```
$ ./gk-deploy -g -n storage

Welcome to the deployment tool for GlusterFS on Kubernetes and OpenShift.
Before getting started, this script has some requirements of the execution
environment and of the container platform that you should verify.
The client machine that will run this script must have:
 * Administrative access to an existing Kubernetes or OpenShift cluster
 * Access to a python interpreter 'python'
Each of the nodes that will host GlusterFS must also have appropriate firewall
rules for the required GlusterFS ports:
 * 2222  - sshd (if running GlusterFS in a pod)
 * 24007 - GlusterFS Management
 * 24008 - GlusterFS RDMA
 * 49152 to 49251 - Each brick for every volume on the host requires its own
   port. For every new brick, one new port will be used starting at 49152. We
   recommend a default range of 49152-49251 on each host, though you can adjust
   this to fit your needs.
The following kernel modules must be loaded:
 * dm_snapshot
 * dm_mirror
 * dm_thin_pool
For systems with SELinux, the following settings need to be considered:
 * virt_sandbox_use_fusefs should be enabled on each node to allow writing to
   remote GlusterFS volumes
In addition, for an OpenShift deployment you must:
 * Have 'cluster_admin' role on the administrative account doing the deployment
 * Add the 'default' and 'router' Service Accounts to the 'privileged' SCC
 * Have a router deployed that is configured to allow apps to access services
   running in the cluster
Do you wish to proceed with deployment?

[Y]es, [N]o? [Default: Y]: y
Using Kubernetes CLI.
Using namespace "storage".
Checking for pre-existing resources...
  GlusterFS pods ... found.
  deploy-heketi pod ... not found.
  heketi pod ... not found.
  gluster-s3 pod ... not found.
Creating initial resources ... Error from server (AlreadyExists): error when creating "/usr/local/glusterfs/deploy/kube-templates/heketi-service-account.yaml": serviceaccounts "heketi-service-account" already exists
Error from server (AlreadyExists): clusterrolebindings.rbac.authorization.k8s.io "heketi-sa-view" already exists
clusterrolebinding.rbac.authorization.k8s.io/heketi-sa-view not labeled
OK
secret/heketi-config-secret created
secret/heketi-config-secret labeled
service/deploy-heketi created
deployment.extensions/deploy-heketi created
Waiting for deploy-heketi pod to start ... OK
Creating cluster ... ID: da2f4e8619698c655de0c28312fb7ec8
Allowing file volumes on cluster.
Allowing block volumes on cluster.
Creating node k8s-node-2-12 ... ID: a11d14623a516c8798a82a81e331e16e
Adding device /dev/sdb ... OK
Creating node k8s-node-2-13 ... ID: 2c55d2da091bcb7c40b6400557e41ba6
Adding device /dev/sdb ... OK
Creating node k8s-node-2-14 ... ID: fd29f688d5b6cfc1a8b8a56f7a362e64
Adding device /dev/sdb ... OK
heketi topology loaded.
Saving /tmp/heketi-storage.json
secret/heketi-storage-secret created
endpoints/heketi-storage-endpoints created
service/heketi-storage-endpoints created
job.batch/heketi-storage-copy-job created
service/heketi-storage-endpoints labeled
pod "deploy-heketi-865f55765-m8wg4" deleted
service "deploy-heketi" deleted
deployment.apps "deploy-heketi" deleted
replicaset.apps "deploy-heketi-865f55765" deleted
job.batch "heketi-storage-copy-job" deleted
secret "heketi-storage-secret" deleted
service/heketi created
deployment.extensions/heketi created
Waiting for heketi pod to start ... OK
......到这里已经完成安装
```
3、部署失败清除

部署失败使用下面命令清除对应 Kubernetes 资源，再将节点的目录/var/lib/glusterd清空，删除磁盘的 vg 和 pv

-n 是指定安装到 Kubernetes 集群下的 Namespace
```
$ ./gk-deploy -g --abort -n storage
```
4、部署中遇到的问题

遇到的问题1：

如果遇到如下问题，请确认是否挂载了新硬盘且未分区格式化等。
```
initialized or contains data?):   WARNING: Device /dev/centos/root not initialized in udev database even after waiting 10000000 microseconds.
```
遇到的问题2：

如果卡在heketi topology loaded.不动，请查看是否给 Kubernetes 节点设置 Label，或 GlusterFS 要求最少三个节点，请查看是否满足需求。
```
Creating node k8s-node-2-13 ... ID: 2c55d2da091bcb7c40b6400557e41ba6
Adding device /dev/sdb ... OK
Creating node k8s-node-2-14 ... ID: fd29f688d5b6cfc1a8b8a56f7a362e64
Adding device /dev/sdb ... OK
heketi topology loaded.
```
5、查看资源

安装完成后 Kubernetes 集群 安装的 Namespace 下应该存下面这些 Pod、Service
```
$ kubectl get pods,service -n storage

[root@k8s-master-2-11 ~]# 
NAME                     READY   STATUS    RESTARTS   AGE
glusterfs-lkjwq          1/1     Running   0          16h
glusterfs-mtlq4          1/1     Running   0          16h
glusterfs-tb867          1/1     Running   0          16h
heketi-85dbbbb55-cndgz   1/1     Running   0          15h

NAME                                                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/glusterfs-dynamic-41db5f46-7344-11e9-8b45-000c29d98 ClusterIP   10.10.126.0     <none>        1/TCP      15h
service/heketi                                              ClusterIP   10.10.249.63    <none>        8080/TCP   16h
service/heketi-storage-endpoints                            ClusterIP   10.10.211.195   <none>        1/TCP      16h
```
六、测试 GlusterFS

这里将进行创建一个 StorageClass，然后创建 PVC 进行测试，看其是否能自动生成 PV。之后再创建一个 Nnginx Pod，在其中容器挂载目录创建一个 index.html 文件，然后进入 GlusterFS 容器内查看能否找到对应资源。
1、创建 StorageClass

(1)、gluserfs-sc.yaml
```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: glusterfs-sc                    #---SorageClass 名称
provisioner: kubernetes.io/glusterfs
parameters:
  resturl: "http://10.10.249.63:8080"   #---heketi service的cluster ip 和端口
  restuser: "admin"                     #---任意填写，因为没有启用鉴权模式
  restuserkey: "My Secret Life"         #---任意填写，因为没有启用鉴权模式
  gidMin: "40000"
  gidMax: "50000"
  volumetype: "replicate:3"             #---申请的副本数，默认为3副本模式
```
(2)、创建 StorageClass
```
$ kubectl apply -f gluserfs-sc.yaml
```
(3)、查看 StorageClass
```
$ kubectl get storageclass

NAME           PROVISIONER               AGE
glusterfs-sc   kubernetes.io/glusterfs   15h
```
2、创建 PVC

(1)、gluserfs-pvc.yaml
```
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: myclaim
  annotations:
    volume.beta.kubernetes.io/storage-class: "glusterfs-sc"   #---需要与storageclass的名称一致
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi       #---设置请求大小为1G
```
(2)、创建 pvc

-n 设置创建的 namespace，这里替换成自己想创建 PVC 资源的 namespace
```
$ kubectl apply -f gluserfs-pvc.yaml -n mydlqcloud
```
(3)、查看PVC
```
$ kubectl get pvc -n mydlqcloud

NAME      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
myclaim   Bound    pvc-41db5f46-7344-11e9-8b45-000c29d98697   1Gi        RWO            glusterfs-sc   15h
```
3、查看是否创建 PV
```
$ kubectl get pv | grep myclaim

pvc-41db5f46-7344-11e9-8b45-000c29697  1Gi  RW  delete   Bound   storage/myclaim   glusterfs-sc  15h
```
4、创建一个使用 PVC 的 Nginx Pod

(1)、nginx-pod.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    name: nginx-pod
spec:
  containers:
  - name: nginx-pod
    image: nginx:1.16.0-alpine
    ports:
    - name: web
      containerPort: 80
    volumeMounts:
    - name: gluster-test
      mountPath: /usr/share/nginx/html
  volumes:
  - name: gluster-test
    persistentVolumeClaim:
      claimName: myclaim
```
(2)、创建 Nginx Pod
```
$ kubectl create -f nginx-pod.yaml -n mydlqcloud
```
(3)、查看创建的 Nginx Pod
```
$ kubectl get pod -n mydlqcloud | grep nginx-pod

nginx-pod                1/1     Running   0          92s
```
5、在 Nginx Pod 创建 HTML

(1)、进入 Nginx Pod
```
$ kubectl exec -it nginx-pod /bin/sh -n mydlqcloud
```
(2)、创建 HTML
```
$ cd /usr/share/nginx/html
$ echo 'Hello World from GlusterFS!!!' > index.html
```
(3)、退出Nginx Pod
```
$ exit
```
6、检查创建的HTML 文件是否写入 GlusterFS 存储中

(1)、查看 GlusterFS Pod 名称
```
$ kubectl get pods -n storage

NAME                     READY   STATUS    RESTARTS   AGE
glusterfs-lkjwq          1/1     Running   0          16h
glusterfs-mtlq4          1/1     Running   0          16h
glusterfs-tb867          1/1     Running   0          16h
heketi-85dbbbb55-cndgz   1/1     Running   0          15h
```
(2)、进入任意一个 Pod 容器中

勿忘 -n 来指定 GlusterFS 的 namespace
```
$ kubectl exec -ti glusterfs-lkjwq /bin/sh -n storage
```
(3)、查询 heketi 的挂载
```
$ mount | grep heketi
sh-4.2# mount | grep heketi
/dev/mapper/centos-root on /var/lib/heketi type xfs (rw,relatime,attr2,inode64,noquota)
/dev/mapper/vg_d62e08192968971ac7f7edc6eb2f3ae5-brick_61bd5976b4d2880dcd5889b174d5b3c7 on /var/lib/heketi/mounts/vg_d62e08192968971ac7f7edc6eb2f3ae5/brick_61bd5976b4d2880dcd5889b174d5b3c7 type xfs (rw,noatime,nouuid,attr2,inode64,logbsize=256k,sunit=512,swidth=512,noquota)
/dev/mapper/vg_d62e08192968971ac7f7edc6eb2f3ae5-brick_78eb1c74ff7ab78969e116e5389444fd on /var/lib/heketi/mounts/vg_d62e08192968971ac7f7edc6eb2f3ae5/brick_78eb1c74ff7ab78969e116e5389444fd type xfs (rw,noatime,nouuid,attr2,inode64,logbsize=256k,sunit=512,swidth=512,noquota)
```
(4)、查看文件列表
```
$ cd /var/lib/heketi/mounts/vg_d62e08192968971ac7f7edc6eb2f3ae5/brick_78eb1c74ff7ab78969e116e5389444fd/brick
$ ls

index.html
```
(5)、查看 index.html 内容
```
$ cat index.html

Hello World from GlusterFS!!!
```
七、配置 Heketi Client
---
在 Kubernetes 集群任意节点安装 Heketi Client 客户端，用于操作 Kubernetes 集群中的 Heketi。

例如这里选择用 k8s-node-2-12 节点进行操作。
1、下载 Heketi Client
```
$ wget https://github.com/heketi/heketi/releases/download/v9.0.0/heketi-client-v9.0.0.linux.amd64.tar.gz
```
2、解压Heketi Client 安装包
```
$ tar -xvf heketi-client-v9.0.0.linux.amd64.tar.gz
```
3、将可 heketi-cli 移动到 bin 文件夹下
```
$ mv heketi-client/bin/heketi-cli /usr/local/bin/heketi-cli
```
4、查看 Kubernetes 集群的 Heketi Service

查看 Heketi Service，记住其集群 IP 和 Port
```
$ kubectl get service -n storage

NAME                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
heketi                     ClusterIP   10.10.249.63    <none>        8080/TCP   15m
heketi-storage-endpoints   ClusterIP   10.10.211.195   <none>        1/TCP      15m
```
访问该 Service 地址，查看是否互通
```
$ curl http://10.10.249.63:8080/hello

Hello from Heketi
```
5、测试 heketi-cli 命令

测试 heketi-cli 命令， 其中 “-s” 指的是 Heketi Service 地址，即上面步骤查找到的Heketi Service 的 IP:PORT
```
$ heketi-cli -s http://10.10.249.63:8080 cluster list

Clusters:
Id:b4cdf0d91b77d872238d5674c86e82df [file][block]
```
6、设置 Heketi Service 环境变量

每次都要输入 -s http://ip:port 比较麻烦，这里设置它的一个变量，指定这个 Hiketi Service 地址，这样不必每次都输入 -s 命令了。
```
$ export HEKETI_CLI_SERVER=http://10.10.249.63:8080
```
7、再次测试 heketi-cli 命令

输入 heteti-cli 命令测试，这次不用指定 -s 到 hekari service 地址，直接执行。
```
$ heketi-cli cluster list

Clusters:
Id:b4cdf0d91b77d872238d5674c86e82df [file][block]
```
八、GluserFS 集群扩容
---
在 Kubernetes 环境中通过 Heketi 操作 GlusterFS 集群的管理工作，用其增加、减少存储工作。

1、GlusterFS 集群节点增加设备

GlusterFS 节点新增硬盘设备，可以按以下方式执行。

Kubernetes 的 k8s-node-2-14 节点新增 /dev/sdc 设备，将其加入 GlusterFS 节点

(1)、查看新挂载设备

查看新挂载的设备符，可以看到为 “/dev/sdc”
```
$ lsblk

NAME                                                                              MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda                                                                                 8:0    0   50G  0 disk 
├─sda1                                                                              8:1    0    1G  0 part /boot
└─sda2                                                                              8:2    0   49G  0 part 
  ├─centos-root                                                                   253:0    0 45.1G  0 lvm  /
  └─centos-swap                                                                   253:1    0  3.9G  0 lvm  
sdb                                                                                 8:16   0   30G  0 disk 
├─vg_48e1705a862bccec97ca25de0a5afbc2-tp_66de677e1d6e065dbe6bffd658e84f4e_tmeta   253:2    0   12M  0 lvm  
│ └─vg_48e1705a862bccec97ca25de0a5afbc2-tp_66de677e1d6e065dbe6bffd658e84f4e-tpool 253:4    0    2G  0 lvm  
│   ├─vg_48e1705a862bccec97ca25de0a5afbc2-tp_66de677e1d6e065dbe6bffd658e84f4e     253:5    0    2G  0 lvm  
│   └─vg_48e1705a862bccec97ca25de0a5afbc2-brick_5ef2856630417cdf261e348e9e5b692b  253:6    0    2G  0 lvm  
└─vg_48e1705a862bccec97ca25de0a5afbc2-tp_66de677e1d6e065dbe6bffd658e84f4e_tdata   253:3    0    2G  0 lvm  
  └─vg_48e1705a862bccec97ca25de0a5afbc2-tp_66de677e1d6e065dbe6bffd658e84f4e-tpool 253:4    0    2G  0 lvm  
    ├─vg_48e1705a862bccec97ca25de0a5afbc2-tp_66de677e1d6e065dbe6bffd658e84f4e     253:5    0    2G  0 lvm  
    └─vg_48e1705a862bccec97ca25de0a5afbc2-brick_5ef2856630417cdf261e348e9e5b692b  253:6    0    2G  0 lvm  
sdc                                                                                 8:32   0   20G  0 disk 
sr0  
```
(2)、修改拓扑文件

修改 Heketi 的拓扑文件 topology.json
```
{
  "clusters": [
    {
      "nodes": [
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-12"
              ],
              "storage": [
                "192.168.2.12"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-13"
              ],
              "storage": [
                "192.168.2.13"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-14"
              ],
              "storage": [
                "192.168.2.14"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb",
            "/dev/sdc"      #------------新增的硬盘------------
          ]
        }
      ]
    }
  ]
}
```
(3)、Heketi 重新加载拓扑文件

Heketi 重新载入 topology.json 文件，以执行扩容操作，将新设备加入 GlusterFS 节点中。
```
$ heketi-cli topology load --json=./topology.json

    Found node k8s-node-2-12 on cluster b4cdf0d91b77d872238d5674c86e82df
        Found device /dev/sdb
    Found node k8s-node-2-13 on cluster b4cdf0d91b77d872238d5674c86e82df
        Found device /dev/sdb
    Found node k8s-node-2-14 on cluster b4cdf0d91b77d872238d5674c86e82df
        Found device /dev/sdb
        Adding device /dev/sdc ... OK
```
(4)、查看节点列表

查看 Heketi 管理的 GlusterFS 集群节点列表
```
$ heketi-cli node list

Id:5109827180c19506a60cb50303cfdff6 Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:7a5717ae22ed4b579dec6f0ad70587ff Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:b5aef310f1ff6a1815ecb008265b5a56 Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:e30756768d89302c25f93b58efc1c232 Cluster:b4cdf0d91b77d872238d5674c86e82df
```
(5)、查看节点信息

查看 Heketi 管理的 GlusterFS 集群某个节点信息，可以看到已经将 /dev/sdc 设备加入到 GlusterFS 节点
```
$ heketi-cli node info e30756768d89302c25f93b58efc1c232

Node Id: e30756768d89302c25f93b58efc1c232
State: online
Cluster Id: b4cdf0d91b77d872238d5674c86e82df
Zone: 1
Management Hostname: k8s-node-2-14
Storage Hostname: 192.168.2.14
Devices:
Id:48e1705a862bccec97ca25de0a5afbc2  Name:/dev/sdb State:online  Size (GiB):29  Used (GiB):2  Free (GiB):27  Bricks:1    
Id:c7a22cf667a50cd57edf2b06f36afa2e  Name:/dev/sdc State:online  Size (GiB):19  Used (GiB):0  Free (GiB):19  Bricks:0
```
2、GlusterFS 集群新增节点

GlusterFS 集群新增存储节点，可以按以下方式执行。

比如 Kubernetes 新增 k8s-node-2-15 节点，将其加入 GlusterFS 集群

(1)、Kubernetes 新节点添加 GlusterFS 标签

新增加节点为 “k8s-node-2-15”，节点设置 GlusterFS 标签 storagenode=glusterfs ，这样会自动在该 Kubernetes 节点上启动一个 GlusterFS Pod。
```
$ kubectl label node k8s-node-2-15 storagenode=glusterfs

node/k8s-node-2-15 labeled
```
(2)、修改拓扑文件

修改 Heketi 的拓扑文件 topology.json，将新节点信息加入其中
```
{
  "clusters": [
    {
      "nodes": [
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-12"
              ],
              "storage": [
                "192.168.2.12"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-13"
              ],
              "storage": [
                "192.168.2.13"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-14"
              ],
              "storage": [
                "192.168.2.14"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb",
            "/dev/sdc"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "k8s-node-2-15"         #新kubernetes节点名称
              ],
              "storage": [
                "192.168.2.15"          #新kubernetes节点IP
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb"                  #挂载的设备
          ]
        }
      ]
    }
  ]
}
```
(3)、Heketi 重新加载拓扑文件

Heketi 重新载入 topology.json 文件，以执行扩容操作，将新节点加入 GlusterFS 集群。
```
$ heketi-cli topology load --json=./topology.json
    
    Found node k8s-node-2-12 on cluster b4cdf0d91b77d872238d5674c86e82df
        Found device /dev/sdb
    Found node k8s-node-2-13 on cluster b4cdf0d91b77d872238d5674c86e82df
        Found device /dev/sdb
    Found node k8s-node-2-14 on cluster b4cdf0d91b77d872238d5674c86e82df
        Found device /dev/sdb
        Found device /dev/sdc
    Creating node k8s-node-2-15 ... ID: 7a5717ae22ed4b579dec6f0ad70587ff
        Adding device /dev/sdb ... OK
```
(4)、查看 GlusterFS 节点
```
$ heketi-cli node list

Id:5109827180c19506a60cb50303cfdff6 Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:7a5717ae22ed4b579dec6f0ad70587ff Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:b5aef310f1ff6a1815ecb008265b5a56 Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:e30756768d89302c25f93b58efc1c232 Cluster:b4cdf0d91b77d872238d5674c86e82df
```
3、GlusterFS 集群节点删除设备
(1)、查看删除前的节点信息
```
$ heketi-cli node info e30756768d89302c25f93b58efc1c232

Node Id: e30756768d89302c25f93b58efc1c232
State: online
Cluster Id: b4cdf0d91b77d872238d5674c86e82df
Zone: 1
Management Hostname: k8s-node-2-14
Storage Hostname: 192.168.2.14
Devices:
Id:48e1705a862bccec97ca25de0a5afbc2   Name:/dev/sdb            State:online    Size (GiB):29      Used (GiB):2       Free (GiB):27      Bricks:1       
Id:7cf2a1d44bb287e2c864880b82a25bd6   Name:/dev/sdc            State:online    Size (GiB):19      Used (GiB):0       Free (GiB):19      Bricks:0 
```
(2)、使设备脱机
```
$ heketi-cli device disable c7a22cf667a50cd57edf2b06f36afa2e

Device c7a22cf667a50cd57edf2b06f36afa2e is now offline
```
(3)、将设备从集群移除
```
$ heketi-cli device remove c7a22cf667a50cd57edf2b06f36afa2e

Device c7a22cf667a50cd57edf2b06f36afa2e is now removed
```
(4)、将设备删除
```
$ heketi-cli device delete c7a22cf667a50cd57edf2b06f36afa2e

Device c7a22cf667a50cd57edf2b06f36afa2e deleted
```
(5)、查看删除后的节点信息
```
$ heketi-cli node info e30756768d89302c25f93b58efc1c232

Node Id: e30756768d89302c25f93b58efc1c232
State: online
Cluster Id: b4cdf0d91b77d872238d5674c86e82df
Zone: 1
Management Hostname: k8s-node-2-14
Storage Hostname: 192.168.2.14
Devices:
Id:48e1705a862bccec97ca25de0a5afbc2 Name:/dev/sdb  State:online  Size (GiB):29  Used (GiB):2  Free (GiB):27  Bricks:1
```
4、GlusterFS 集群删除节点

GlusterFS 集群删除存储节点，可以按以下方式执行。

(1)、查看删除前的节点列表
```
$ heketi-cli -s http://10.10.249.63:8080 node list

Id:5109827180c19506a60cb50303cfdff6 Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:7a5717ae22ed4b579dec6f0ad70587ff Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:b5aef310f1ff6a1815ecb008265b5a56 Cluster:b4cdf0d91b77d872238d5674c86e82df
Id:e30756768d89302c25f93b58efc1c232 Cluster:b4cdf0d91b77d872238d5674c86e82df
```
(2)、查看节点信息
```
$ heketi-cli -s http://10.10.249.63:8080 node info 7a5717ae22ed4b579dec6f0ad70587ff

Node Id: 7a5717ae22ed4b579dec6f0ad70587ff
State: online
Cluster Id: b4cdf0d91b77d872238d5674c86e82df
Zone: 1
Management Hostname: k8s-node-2-15
Storage Hostname: 192.168.2.15
Devices:
Id:d8d252c60c10763d8797f4dcb16c4f25   Name:/dev/sdb            State:online    Size (GiB):29      Used (GiB):0       Free (GiB):29      Bricks:0  
```
(3)、使节点脱机
```
$ heketi-cli -s http://10.10.249.63:8080 node disable 7a5717ae22ed4b579dec6f0ad70587ff

Node 7a5717ae22ed4b579dec6f0ad70587ff is now offline
```
(4)、将节点从集群移除
```
$ heketi-cli -s http://10.10.249.63:8080 node remove 7a5717ae22ed4b579dec6f0ad70587ff

Node 7a5717ae22ed4b579dec6f0ad70587ff is now removed
```
(5)、删除节点的设备
```
$ heketi-cli -s http://10.10.249.63:8080 device delete d8d252c60c10763d8797f4dcb16c4f25

Device d8d252c60c10763d8797f4dcb16c4f25 deleted
```
(6)、删除节点
```
$ heketi-cli -s http://10.10.249.63:8080 node delete 7a5717ae22ed4b579dec6f0ad70587ff

Node 7a5717ae22ed4b579dec6f0ad70587ff deleted
```
(7)、查看 GlusterFS Pod 数量
```
$ kubectl get daemonset -n storage

NAME       DESIRED  CURRENT  READY  UP-TO-DATE  AVAILABLE  NODE SELECTOR           AGE
glusterfs  4        4        4      46库，           4          storagenode=glusterfs   11h
```
(8)、将标签 storagenode=glusterfs 从 Kubernetes 节点移除

标签 storagenode=glusterfs 从 k8s-node-2-15 节点移除
```
$ kubectl label node k8s-node-2-15 storagenode-

node/k8s-node-2-15 labeled
```
查看 GlusterFS Pod 数量已经减少1
```
$ kubectl get daemonset -n storage

NAME       DESIRED  CURRENT  READY  UP-TO-DATE  AVAILABLE  NODE SELECTOR           AGE
glusterfs  3        3        3      3           3          storagenode=glusterfs   11h
```
九、Heketi 命令简介
---
```
#----------------------Cluster命令----------------------
## (1)、查看GlusterFS集群列表
$ heketi-cli cluster list

## (2)、查看GlusterFS集群信息
$ heketi-cli cluster info da2f4e8619698c655de0c28312fb7ec8

## (3)、查看GlusterFS节点信息
$ heketi-cli node info 2c55d2da091bcb7c40b6400557e41ba6

#----------------------Volume命令----------------------
## (1)、创建一个 volume(大小1GB，默认3副本)
$ heketi-cli volume create --size=1

## (2)、查看卷信息列表
$ heketi-cli volume list

#----------------------Heketi-cli 其它命令----------------------
#heketi支持如下命令
heketi-cli -h
  blockvolume                    Heketi Volume Management
  cluster                        Heketi cluster management
  db                             Heketi Database Management
  device                         Heketi device management
  help                           Help about any command
  loglevel                       Heketi Log Level
  node                           Heketi Node Management
  setup-openshift-heketi-storage Setup OpenShift/Kubernetes persistent storage for Heketi
  topology                       Heketi Topology Management
  volume                         Heketi Volume Management
#集群相关命令
heketi-clicluster -h
  create      Create a cluster
  delete      Delete the cluster
  info        Retrieves information about cluster
  list        Lists the clusters managed by Heketi
  setflags    Set flags on a cluster
#节点相关命令
heketi-cli node -h
  add         Add new node to be managed by Heketi
  delete      Deletes a node from Heketi management
  disable     Disallow usage of a node by placing it offline
  enable      Allows node to go online
  info        Retrieves information about the node
  list        List all nodes in cluster
  remove      Removes a node and all its associated devices from Heketi
  rmtags      Removes tags from a node
  settags     Sets tags on a node
#卷相关命令
heketi-cli volume -h
  clone       Creates a clone
  create      Create a GlusterFS volume
  delete      Deletes the volume
  expand      Expand a volume
  info        Retrieves information about the volume
  list        Lists the volumes managed by Heketi
其他的命令可以通过<-h>查看详细使用方式
```
