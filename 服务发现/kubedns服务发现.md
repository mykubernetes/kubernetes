1、Kubernetes DNS pod中包括3个容器，可以通过kubectl⼯具查看  
```
# kubectl get pod -n kube-system |grep kube-dns
kube-dns-6bd5696b8c-rwdb5              3/3     Running            0          4m16s
```  

2、READY ⼀栏可以看到是 3/3，⽤如下命令可以很清楚的看到 kube-dns 包含的3个容器  
```
# kubectl describe pod kube-dns-6bd5696b8c-rwdb5 -n kube-system
```  
kube-dns、dnsmasq-nanny、sidecar 这3个容器

- kubedns: kubedns 基于 SkyDNS 库，通过 apiserver 监听 Service 和 Endpoints 的变更事件同时也同步到本地 Cache，实现了⼀个实时的 Kubernetes 集群内 Service 和 Pod 的 DNS服务发现
- dnsmasq: dsnmasq 容器则实现了 DNS 的缓存功能(在内存中预留⼀块默认⼤⼩为 1G 的地⽅，保存当前最常⽤的 DNS 查询记录，如果缓存中没有要查找的记录，它会到 kubedns 中查询，并把结果缓存起来)，通过监听 ConfigMap 来动态⽣成配置
- sider: sidecar 容器实现了可配置的 DNS 探测，并采集对应的监控指标暴露出来供 prometheus 使⽤
![image](https://raw.githubusercontent.com/cnych/kubernetes-learning/master/docs/images/kubedns.jpg)
