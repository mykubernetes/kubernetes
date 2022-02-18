# Docker背后的内核知识

当谈论docker时，常常会聊到docker的实现方式。很多开发者都知道，docker容器本质上是宿主机的进程，Docker通过namespace实现了资源隔离，通过cgroups实现了资源限制，通过写时复制机制（copy-on-write）实现了高效的文件操作。当进一步深入namespace和cgroups等技术细节时，大部分开发者都会感到茫然无措。尤其是接下来解释libcontainer的工作原理时，我们会接触大量容器核心知识。所以在这里，希望先带领大家走进linux内核，了解namespa和cgroups的技术细节。

# 一： Namespace资源隔离

namespace是Linux系统的底层概念，在内核层实现，即有一些不同类型的命名空间被部署在核内，各个docker容器运行在同一个docker主进程并且共用同一个宿主机系统内核，各docker容器运行在宿主机的用户空间，每个容器都要有类似于虚拟机一样的相互隔离的运行空间，但是容器技术是在一个进程内实现运行指定服务的运行环境，并且还可以保护宿主机内核不受其他进程的干扰和影响，如文件系统空间、网络空间、进程空间等，目前主要通过以下技术实现容器运行空间的相互隔离：

linux内核提拱了6种namespace隔离的系统调用，如下图所示，但是真正的容器还需要处理许多其他工作。

| namespace | 系统调用参数 | 隔离内容 | 功能 | 内核版本 |
| UTS Namespace (UNIX Timesharing System) | CLONE_NEWUTS | 主机名或域名 | 提供主机名隔离能力 | Linux 2.6.19 |
| IPC Namespace (Inter-Process Communication) | CLONE_NEWIPC | 信号量、消息队列和共享内存 | 提供进程间通信的隔离能力 | Linux 2.6.19 |
| PID Namespace (Process Identification) | CLONE_NEWPID | 进程编号 | 提供进程隔离能力 | Linux 2.6.24 |
| Net Namespace (network) | CLONE_NEWNET | 网络设备、网络战、端口等 | 提供网络隔离能力 | Linux 2.6.29 |
| MNT Namespace (mount) | CLONE_NEWNS | 挂载点（文件系统） | 提供磁盘挂载点和文件系统的隔离能力 | Linux 2.4.19 |
| User Namespace (user) | CLONE_NEWUSER | 用户组和用户组 | 提供用户隔离能力 | Linux 3.8 |

实际上，linux内核实现namespace的主要目的，就是为了实现轻量级虚拟化技术服务。在同一个namespace下的进程合一感知彼此的变化，而对外界的进程一无所知。这样就可以让容器中的进程产生错觉，仿佛自己置身一个独立的系统环境中，以达到隔离的目的

## 1.1 UTS Namespace

UTS(UNIX Time-sharing System)Namespace提供了主机名与域名的隔离，用于系统标识，其中包含了主机名hostname 和域名domainname ，它使得一个容器拥有属于自己hostname标识，这个主机名标识独立于宿主机系统和其上的其他容器。这样每个docke容器就可以拥有独立的主机名和域名了，在网络上可以被视为一个独立的节点，而非宿主机上的一个进程。docker中，每个镜像基本都以自身所提供的服务名称来命名镜像的hostname，且不会对宿主机产生任何影响，其原理就是使用了UTS namespace。
```
root@test:~# docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
59b7f2d18847        centos              "/bin/bash"         2 seconds ago       Up 1 second                             gallant_proskuriakova
ed76b09b0780        centos              "/bin/bash"         3 seconds ago       Up 3 seconds                            frosty_dubinsky
root@test:~# docker exec -it 59b7f2d18847 bash
[root@59b7f2d18847 /]# hostname
59b7f2d18847
[root@59b7f2d18847 /]# cat /etc/hosts
127.0.0.1    localhost
::1    localhost ip6-localhost ip6-loopback
fe00::0    ip6-localnet
ff00::0    ip6-mcastprefix
ff02::1    ip6-allnodes
ff02::2    ip6-allrouters
172.17.0.3    59b7f2d18847 
[root@59b7f2d18847 /]# ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
11: eth0@if12: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 02:42:ac:11:00:03 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.3/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever
```

## 1.2 IPC Namespace

一个容器内的进程间通信，允许一个容器内的不同进程的(内存、缓存等)数据访问，但是不能跨容器直接访问其他容器的数据，申请IPC资源就申请了一个全局唯一的32位ID，所以IPC namespace中实际上包含了系统IPC标识符以及实现POSIX消息队列的文件系统。在同一个IPC namespace下的进程彼此可见，不同IPC namespace下的进程则互相不可见。
目前使用IPC namespace机制的系统不多，其中比较有名的有PostgreSQL。Docker当前也使用IPC namespace实现了容器与宿主机、容器与容器之间的IPC隔离。

## 1.3 PID Namespace

Linux系统中，有一个PID为1的进程(init/systemd)是其他所有进程的父进程，那么在每个容器内也要有一个父进程来管理其下属的子进程，那么多个容器的进程通PID namespace进程隔离(比如PID编号重复、器内的主进程生成与回收子进程等)。
- 每个容器有独立的PID名空间
- 容器的生命周期和其PID1进程一致
- 利用docker exec可以进入到容器的命名空间中启动进程
- 容器的PID1进程需要能够正确的处理SIGTERM信号来支持优雅退出。
- 如果容器中包含多个进程，需要PID1进程能够正确的传播SIGTERM信号来结束所有的子进程之后再退出。
- 确保PID1进程是期望的进程。缺省sh/bash进程没有提供SIGTERM的处理，需要通过shell脚本来设置正确的PID1进程，或捕获SIGTERM信号。

## 1.4 Net Namespace

每一个容器都类似于虚拟机一样有自己的网卡、监听端口、TCP/IP协议栈等，Docker使用network namespace启动一个vethX接口，这样你的容器将拥有它自己的桥接ip地址，通常是docker0，而docker0实质就是Linux的虚拟网桥,网桥是在OSI七层模型的数据链路层的网络设备，通过mac地址对网络进行划分，并且在不同网络直接传递数据。

## 1.5 MNT Namespace

每个容器都要有独立的根文件系统有独立的用户空间，以实现在容器里面启动服务并且使用容器的运行环境，即一个宿主机是ubuntu的服务器，可以在里面启动一个centos运行环境的容器并且在容器里面启动一个Nginx服务，此Nginx运行时使用的运行环境就是centos系统目录的运行环境，但是在容器里面是不能访问宿主机的资源，宿主机是使用了chroot技术把容器锁定到一个指定的运行目录里面。

例如：/var/lib/containerd/io.containerd.runtime.v1.linux/moby/容器ID

根目录：/var/lib/docker/overlay2/ID
```
root@test:~# docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
59b7f2d18847        centos              "/bin/bash"         About an hour ago   Up About an hour                        gallant_proskuriakova
ed76b09b0780        centos              "/bin/bash"         About an hour ago   Up About an hour                        frosty_dubinsky
root@test:~# ls /var/lib/containerd/io.containerd.runtime.v1.linux/moby/
59b7f2d18847e6d02f5dd1967f75ebdc4ccd8cef7391f77599a56ee288d140e1  ed76b09b0780c4e437e7ddb41698b356af1709aa1a644ad5e607e0c293e24d81
root@test:~# ls /var/lib/docker/overlay2/b08f94804312404c22ea1488c0ae94e60cc3d53f56d2218179e56a439b3ee24b/merged/
bin  dev  etc  home  lib  lib64  lost+found  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
```

启动三个容器用于以下验证过程：
```
root@test:~# docker version
Client: Docker Engine - Community
 Version:           19.03.15
 API version:       1.40
 Go version:        go1.13.15
 Git commit:        99e3ed8919
 Built:             Sat Jan 30 03:17:01 2021
 OS/Arch:           linux/amd64
 Experimental:      false

Server: Docker Engine - Community
 Engine:
  Version:          19.03.15
  API version:      1.40 (minimum version 1.12)
  Go version:       go1.13.15
  Git commit:       99e3ed8919
  Built:            Sat Jan 30 03:15:30 2021
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          1.4.9
  GitCommit:        e25210fe30a0a703442421b0f60afac609f950a3
 runc:
  Version:          1.0.1
  GitCommit:        v1.0.1-0-g4144b63
 docker-init:
  Version:          0.18.0
  GitCommit:        fec3683
root@test:~# docker run  -d --name nginx-1 -p 80:80 nginx
root@test:~# docker run  -d --name nginx-2 -p 81:80 nginx
root@test:~# docker run  -d --name nginx-3 -p 82:80 nginx
root@test:~# docker exec nginx-1 cat /etc/issue
Debian GNU/Linux 10 \n \l

root@test:~# docker exec nginx-1 ls /
bin
boot
dev
docker-entrypoint.d
docker-entrypoint.sh
etc
home
lib
lib64
media
mnt
opt
proc
root
run
sbin
srv
sys
tmp
usr
var
```

## 1.6 User Namespace

User Namespace允许在各个宿主机的各个容器空间内创建相同的用户名以及相同的用户UID和GID，只是会把用户的作用范围限制在每个容器内，即A容器和B容器可以有相同的用户名称和ID的账户，但是此用户的有效范围仅是当前容器内，不能访问另外一个容器内的文件系统，即相互隔离、互补影响、永不相见。

# 二：Linux Cgroups

在一个容器，如果不对其做任何资源限制，则宿主机会允许其占用无限大的内存空间，有时候会因为代码bug程序会一直申请内存，直到把宿主机内存占完，为了避免此类的问题出现，宿主机有必要对容器进行资源分配限制，比如CPU、内存等，Linux Cgroups的全称是Linux Control Groups，它最主要的作用，就是限制一个进程组能够使用的资源上限，包括CPU、内存、磁盘、网络带宽等等。此外，还能够对进程进行优先级设置，以及将进程挂起和恢复等操作。

## 2.1 功能和定位

Cgroups全称Control Groups，是Linux内核提供的物理资源隔离机制，通过这种机制，可以实现对Linux进程或者进程组的资源限制、隔离和统计功能。

## 2.2 相关概念介绍
- 任务(task): 在cgroup中，任务就是一个进程。
- 控制组(control group): cgroup的资源控制是以控制组的方式实现，控制组指明了资源的配额限制。进程可以加入到某个控制组，也可以迁移到另一个控制组。
- 层级(hierarchy): 控制组有层级关系，类似树的结构，子节点的控制组继承父控制组的属性(资源配额、限制等)。
- 子系统(subsystem): 一个子系统其实就是一种资源的控制器，比如memory子系统可以控制进程内存的使用。子系统需要加入到某个层级，然后该层级的所有控制组，均受到这个子系统的控制。

概念间的关系：
- 子系统可以依附多个层级，当且仅当这些层级没有其他的子系统，比如两个层级同时只有一个cpu子系统，是可以的。
- 一个层级可以附加多个子系统。
- 一个任务可以是多个cgroup的成员，但这些cgroup必须位于不同的层级。
- 子进程自动成为父进程cgroup的成员，可按需求将子进程移到不同的cgroup中。

两个任务组成了一个 Task Group，并使用了 CPU 和 Memory 两个子系统的 cgroup，用于控制 CPU 和 MEM 的资源隔离。

## 2.3 子系统

- cpu: 限制进程的 cpu 使用率。
- cpuacct 子系统，可以统计 cgroups 中的进程的 cpu 使用报告。
- cpuset: 为cgroups中的进程分配单独的cpu节点或者内存节点。
- memory: 限制进程的memory使用量。
- blkio: 限制进程的块设备io。
- devices: 控制进程能够访问某些设备。
- net_cls: 标记cgroups中进程的网络数据包，然后可以使用tc模块（traffic control）对数据包进行控制。
- net_prio: 限制进程网络流量的优先级。
- huge_tlb: 限制HugeTLB的使用。
- freezer:挂起或者恢复cgroups中的进程。
- ns: 控制cgroups中的进程使用不同的namespace。

## 2.4 验证系统cgroups
```
root@test:~# cat /etc/issue
Ubuntu 20.04.2 LTS \n \l
root@test:~# uname -r
5.4.0-81-generic
root@test:~# cat /boot/config-5.4.0-81-generic |grep CGROUP
CONFIG_CGROUPS=y
CONFIG_BLK_CGROUP=y
CONFIG_CGROUP_WRITEBACK=y
CONFIG_CGROUP_SCHED=y
CONFIG_CGROUP_PIDS=y
CONFIG_CGROUP_RDMA=y
CONFIG_CGROUP_FREEZER=y
CONFIG_CGROUP_HUGETLB=y
CONFIG_CGROUP_DEVICE=y
CONFIG_CGROUP_CPUACCT=y
CONFIG_CGROUP_PERF=y
CONFIG_CGROUP_BPF=y
# CONFIG_CGROUP_DEBUG is not set
CONFIG_SOCK_CGROUP_DATA=y
# CONFIG_BLK_CGROUP_IOLATENCY is not set
CONFIG_BLK_CGROUP_IOCOST=y
# CONFIG_BFQ_CGROUP_DEBUG is not set
CONFIG_NETFILTER_XT_MATCH_CGROUP=m
CONFIG_NET_CLS_CGROUP=m
CONFIG_CGROUP_NET_PRIO=y
CONFIG_CGROUP_NET_CLASSID=y
```

## 2.5 cgroups中内存模块
```
root@test:~# cat /boot/config-5.4.0-81-generic |grep MEM|grep CG
CONFIG_MEMCG=y
CONFIG_MEMCG_SWAP=y
# CONFIG_MEMCG_SWAP_ENABLED is not set
CONFIG_MEMCG_KMEM=y
CONFIG_SLUB_MEMCG_SYSFS_ON=y
```

## 2.6 查看系统cgroups
```
root@test:~# ll /sys/fs/cgroup/
total 0
drwxr-xr-x 15 root root 380 Sep  7 14:51 ./
drwxr-xr-x 10 root root   0 Sep  7 14:51 ../
dr-xr-xr-x  5 root root   0 Sep  7 14:51 blkio/
lrwxrwxrwx  1 root root  11 Sep  7 14:51 cpu -> cpu,cpuacct/
lrwxrwxrwx  1 root root  11 Sep  7 14:51 cpuacct -> cpu,cpuacct/
dr-xr-xr-x  5 root root   0 Sep  7 14:51 cpu,cpuacct/
dr-xr-xr-x  3 root root   0 Sep  7 14:51 cpuset/
dr-xr-xr-x  5 root root   0 Sep  7 14:51 devices/
dr-xr-xr-x  4 root root   0 Sep  7 14:51 freezer/
dr-xr-xr-x  3 root root   0 Sep  7 14:51 hugetlb/
dr-xr-xr-x  5 root root   0 Sep  7 14:51 memory/
lrwxrwxrwx  1 root root  16 Sep  7 14:51 net_cls -> net_cls,net_prio/
dr-xr-xr-x  3 root root   0 Sep  7 14:51 net_cls,net_prio/
lrwxrwxrwx  1 root root  16 Sep  7 14:51 net_prio -> net_cls,net_prio/
dr-xr-xr-x  3 root root   0 Sep  7 14:51 perf_event/
dr-xr-xr-x  5 root root   0 Sep  7 14:51 pids/
dr-xr-xr-x  2 root root   0 Sep  7 14:51 rdma/
dr-xr-xr-x  6 root root   0 Sep  7 14:51 systemd/
dr-xr-xr-x  5 root root   0 Sep  7 14:51 unified/

root@test:~# cat /sys/fs/cgroup/cpu/docker/4317158e38bdbc3f52f95cb4bff2a0a95f00d9014dafebbbb29919b9baeffa31/cpuacct.usage
71341241
root@test:~# cat /sys/fs/cgroup/memory/docker/4317158e38bdbc3f52f95cb4bff2a0a95f00d9014dafebbbb29919b9baeffa31/memory.limit_in_bytes 
9223372036854771712
root@test:~# cat /sys/fs/cgroup/memory/docker/4317158e38bdbc3f52f95cb4bff2a0a95f00d9014dafebbbb29919b9baeffa31/memory.max_usage_in_bytes 
5152768
```
