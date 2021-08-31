一、kubernetes对GPU的支持版本
===
kubernetes提供对分布式节点上的AMD GPU和NVIDIA GPU管理的实验性的支持。在V1.6中已经添加了对NVIDIA GPU的支持，并且经历了多次向后不兼容的迭代。通过设备插件在v1.9中添加了对AMD GPU的支持。

从1.8版本开始，使用GPU的推荐方法是使用驱动插件。要是在1.10版本之前通过设备插件启用GPU支持，必须在整个系统中将DevicePlugins功能设置为true: --feature-gates="DevicePlugins=true 。1.10之后版本不需要这么做了。

然后，必须在节点上安装相应供应商GPU驱动程序，并从GPU供应商(AMD/NVIDIA)运行相应的设备插件。

二、kubernetes集群部署GPU
===
kubernetes集群版本: 1.13.5
docker版本: 18.06.1-ce
os系统是版本: centos7.5
内核版本: 4.20.13-1.el7.elrepo.x86_64
Nvidia GPU型号: P4000

# 1、安装nvidia驱动

#### 1)安装gcc
```
[root@k8s-01 ~]# yum install -y gcc
```

#### 2)安装nvidia驱动

下载链接: https://www.nvidia.cn/Download/driverResults.aspx/141795/cn

这里我们下载的是如下版本:
```
[root@k8s-01 ~]# ls NVIDIA-Linux-x86_64-410.93.run -alh
-rw-r--r-- 1 root root 103M Jul 25 17:22 NVIDIA-Linux-x86_64-410.93.run
```

#### 3)修改/etc/modprobe.d/blacklist.conf文件。阻止nouveau模块的加载
```
[root@k8s-01 ~]# echo -e "blacklist nouveau\noptions nouveau modeset=0" > /etc/modprobe.d/blacklist.conf
```

#### 4)重新简历initramfs image
```
[root@k8s-01 ~]# mv /boot/initramfs-$(uname -r).img /boot/initramfs-$(uname -r).img.bak
[root@k8s-01 ~]# dracut /boot/initramfs-$(uname -r).img $(uname -r)
```

#### 5)执行驱动安装
```
[root@k8s-01 ~]# sh NVIDIA-Linux-x86_64-410.93.run -a -q -s 
```

#### 6)安装工具包
只有驱动是不够的，我们需要一些工具包便于我们使用，其中cuda、cudnn是相关工具包。
```
[root@k8s-01 ~]# cat /etc/yum.repos.d/cuda.repo 
[cuda]
name=cuda
baseurl=http://developer.download.nvidia.com/compute/cuda/repos/rhel7/x86_64
enabled=1
gpgcheck=1
gpgkey=http://developer.download.nvidia.com/compute/cuda/repos/rhel7/x86_64/7fa2af80.pub
[root@k8s-01 ~]#
```

# 2安装nvidia-docker2
nvidia-docker是一个可以使用GPU的docker，在docker的基础上做了一层封装。目前基本被弃用。  
nvidia-docker2是一个runtime，能更好的和docker兼容。

#### 1)获取nvidia-docker2的yum源
```
[root@k8s-01 ~]# distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
[root@k8s-01 ~]# curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | sudo tee /etc/yum.repos.d/nvidia-docker.repo
```

#### 2)查看nvidia-docker2的列表
这里我们需要安装支持docker-18.06.1-ce版本的nvidia-docker2版本，否则会不支持。
```
[root@k8s-01 ~]# yum list nvidia-docker2 --showduplicate
Loaded plugins: fastestmirror
Loading mirror speeds from cached hostfile
 * base: mirrors.aliyun.com
 * epel: mirror01.idc.hinet.net
 * extras: mirrors.aliyun.com
 * updates: mirrors.163.com
Installed Packages
nvidia-docker2.noarch                                      2.0.3-1.docker18.06.1.ce                                      @nvidia-docker
Available Packages
nvidia-docker2.noarch                                      2.0.0-1.docker1.12.6                                          nvidia-docker 
nvidia-docker2.noarch                                      2.0.0-1.docker17.03.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.0-1.docker17.06.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.0-1.docker17.06.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.0-1.docker17.09.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.1-1.docker1.12.6                                          nvidia-docker 
nvidia-docker2.noarch                                      2.0.1-1.docker1.13.1                                          nvidia-docker 
nvidia-docker2.noarch                                      2.0.1-1.docker17.03.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.1-1.docker17.06.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.1-1.docker17.09.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.1-1.docker17.09.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.2-1.docker1.12.6                                          nvidia-docker 
nvidia-docker2.noarch                                      2.0.2-1.docker1.13.1                                          nvidia-docker 
nvidia-docker2.noarch                                      2.0.2-1.docker17.03.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.2-1.docker17.06.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.2-1.docker17.09.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.2-1.docker17.09.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.2-1.docker17.12.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker1.12.6                                          nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker1.13.1                                          nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker17.03.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker17.06.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker17.09.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker17.09.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker17.12.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker17.12.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.03.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.03.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.06.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.06.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.06.2                                         nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.09.0.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.09.1.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.09.2                                         nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.09.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.09.3.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-1.docker18.09.4.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-2.docker18.06.2.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-2.docker18.09.5.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-3.docker18.06.3.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-3.docker18.09.5.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-3.docker18.09.6.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.0.3-3.docker18.09.7.ce                                      nvidia-docker 
nvidia-docker2.noarch                                      2.1.0-1                                                       nvidia-docker 
nvidia-docker2.noarch                                      2.1.1-1                                                       nvidia-docker 
nvidia-docker2.noarch                                      2.2.0-1
```
这里我们安装2.0.3-1.docker18.06.1.ce版本即可。

#### 3)安装nvidia-docker2
```
[root@k8s-01 ~]# yum install -y nvidia-docker2-2.0.3-1.docker18.06.1.ce
```

#### 4)配置默认的docker runtime为nvidia
```
[root@k8s-01 ~]# cat /etc/docker/daemon.json 
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```

#### 5)重启docker
```
[root@k8s-01 ~]# systemctl restart docker 
```

#### 6)查看docker信息
```
[root@k8s-01 wf-deploy]# docker info
Containers: 63
 Running: 0
 Paused: 0
 Stopped: 63
Images: 51
Server Version: 18.06.1-ce
Storage Driver: overlay2
 Backing Filesystem: xfs
 Supports d_type: true
 Native Overlay Diff: true
Logging Driver: json-file
Cgroup Driver: cgroupfs
Plugins:
 Volume: local
 Network: bridge host macvlan null overlay
 Log: awslogs fluentd gcplogs gelf journald json-file logentries splunk syslog
Swarm: inactive
Runtimes: runc nvidia
Default Runtime: nvidia
Init Binary: docker-init
containerd version: 468a545b9edcd5932818eb9de8e72413e616e86e
runc version: 69663f0bd4b60df09991c08812a60108003fa340-dirty (expected: 69663f0bd4b60df09991c08812a60108003fa340)
init version: fec3683
Security Options:
 seccomp
  Profile: default
Kernel Version: 4.20.13-1.el7.elrepo.x86_64
Operating System: CentOS Linux 7 (Core)
OSType: linux
Architecture: x86_64
CPUs: 2
Total Memory: 7.79GiB
Name: k8s-01
ID: DWPY:P2I4:NWL4:3U3O:UTGC:PLJC:IGTO:7ZXJ:A7CD:SJGT:7WT5:WNGX
Docker Root Dir: /var/lib/docker
Debug Mode (client): false
Debug Mode (server): false
Registry: https://index.docker.io/v1/
Labels:
Experimental: false
Insecure Registries:
 192.168.50.2
 127.0.0.0/8
Live Restore Enabled: false
```
可以看出docker的默认runtime为nvidia

# 3安装驱动插件
获取插件的最新yaml文件
```
[root@k8s-01 ~]# kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v1.11/nvidia-device-plugin.yml
```

# 查看有GPU的节点
```
[root@wf-229 ~]# kubectl get node 192.18.1.26 -ojson | jq '.status.allocatable'
{
  "cpu": "48",
  "ephemeral-storage": "258961942919",
  "hugepages-1Gi": "0",
  "hugepages-2Mi": "0",
  "memory": "131471388Ki",
  "nvidia.com/gpu": "1",
  "pods": "200"
}
```

# 创建包含GPU资源的POD
```
[root@wf-229 gpu]# cat test.yaml 
apiVersion: v1
kind: Pod
metadata:
  labels:
    k8s-app: nginx-pod
  name: nginx-pod
spec:
  containers:
  - image: nginx:latest
    imagePullPolicy: Always
    name: nginx
    ports:
    - containerPort: 80
      name: nginx
      protocol: TCP
    resources:
      limits:
        nvidia.com/gpu: "1"
```

# 查看pod中分配的GPU资源
```
[root@wf-229 gpu]# kubectl exec -it nginx-pod bash
root@nginx-pod:/# nvidia-smi 
Mon Aug 12 11:39:05 2019       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 410.93       Driver Version: 410.93       CUDA Version: N/A      |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  Quadro P4000        Off  | 00000000:3B:00.0 Off |                  N/A |
| 46%   34C    P8     5W / 105W |      0MiB /  8119MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                       GPU Memory |
|  GPU       PID   Type   Process name                             Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```

三、CLI介绍
===
- nvidia-container-cli

nvidia-container-cli 是一个命令行工具，用于配置Linux容器对GPU 硬件的使用。支持:
- 1）list: 打印nvidia驱动库及路径
- 2）info: 打印所有Nvidia GPU设备
- 3）configure: 进入给定进程的命名空间，执行必要操作保证容器内可以使用被指定的GPU以及对应能力（指定 Nvidia 驱动库）。 configure是我们使用到的主要命令，它将Nvidia 驱动库的so文件 和 GPU设备信息， 通过文件挂载的方式映射到容器中。

查看NODE节点GPU
```
kubectl get node 192.18.1.26 -ojson | jq '.status.allocatable'
```


https://github.com/mykubernetes/kubernetes-handbook/blob/master/setup/addon-list/gpu.md

https://github.com/feiskyer/kubernetes-handbook/blob/master/practice/gpu.md
