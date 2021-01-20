Kubernetes Pod调度失败问题(Insufficient pods)


Kubernetes的node默认最大pod数量为110个，所有node都达到110个时无法再调度，出现如下报错信息
```
0/3 nodes are available: 1 node(s) had taints that the pod didn't tolerate, 2 Insufficient pods
```

解决办法：

修改/etc/sysconfig/kubelet配置文件，添加--max-pods配置，然后重启kubelet服务，修改后文件内容如下
```
# vim /etc/sysconfig/kubelet
KUBELET_EXTRA_ARGS="--fail-swap-on=false --max-pods=300"
```
