Kubernetes管理GPU应用

官方说明
https://devblogs.nvidia.com/gpu-containers-runtime/

https://www.cnblogs.com/breezey/p/11801122.html  
https://www.jianshu.com/p/8b84c597ce03



https://github.com/NVIDIA/nvidia-docker

https://github.com/NVIDIA/nvidia-container-runtime

https://github.com/NVIDIA/k8s-device-plugin

在kubernetes中使用GPU资源

安装步骤

1.节点安装NVIDIA驱动
```
rpm --import https://www.elrepo.org/RPM-GPG-KEY-elrepo.org
rpm -Uvh http://www.elrepo.org/elrepo-release-7.0-3.el7.elrepo.noarch.rpm
yum install -y kmod-nvidia

验证
# nvidia-smi 
```


2.安装nvidia-docker2 # 注意不是nvidia-container-toolkit
```
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | sudo tee /etc/yum.repos.d/nvidia-docker.repo

yum install -y nvidia-docker2

pkill -SIGHUP dockerd
```

3.修改docker配置文件
```
# vim /etc/docker/daemon.json
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
}

# systemctl restart docker
```



3.安装Nvidia-device-plugin插件
```
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/1.0.0-beta4/nvidia-device-plugin.yml
# URL https://github.com/NVIDIA/k8s-device-plugin

验证安装
# kubectl get pod -n kube-system |grep nvidia
nvidia-device-plugin-daemonset-76gm6            1/1     Running   2          20d

```
4.验证node是否成功识别gpu资源
```
kubectl describe node nodeName
```
