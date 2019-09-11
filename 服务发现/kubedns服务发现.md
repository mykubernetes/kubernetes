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

DNS Pod具有静态IP并作为Kubernetes服务暴露出来。该静态IP被分配后,kubelet会将使用 --cluster-dns = <dns-service-ip>参数配置的DNS传递给每个容器。DNS名称也需要域名，本地域可以使用参数--cluster-domain = <default-local-domain>在kubelet中配置  

dnsmasq容器通过监听ConfigMap来动态生成配置,可以自定义存根域和上下游域名服务器  

例如，下面的 ConfigMap 建立了一个 DNS 配置，它具有一个单独的存根域和两个上游域名服务器  
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-dns
  namespace: kube-system
data:
  stubDomains: |
    {"acme.local": ["1.2.3.4"]}
  upstreamNameservers: |
    ["8.8.8.8", "8.8.4.4"]
```  
按如上说明，具有.acme.local后缀的DNS请求被转发到 DNS 1.2.3.4。Google 公共 DNS 服务器 为上游查询提供服务,下表描述了具有特定域名的查询如何映射到它们的目标 DNS 服务器  

| 域名                                 | 响应查询的服务器                      |
| ------------------------------------ | ------------------------------------- |
| kubernetes.default.svc.cluster.local | kube-dns                              |
| foo.acme.local                       | 自定义 DNS (1.2.3.4)                  |
| widget.com                           | 上游 DNS (8.8.8.8, 8.8.4.4，其中之一) |

另外我们还可以为每个 Pod 设置 DNS 策略。 当前 Kubernetes 支持两种 Pod 特定的 DNS 策略：“Default” 和 “ClusterFirst”。 可以通过 dnsPolicy 标志来指定这些策略。

> 注意：**Default** 不是默认的 DNS 策略。如果没有显式地指定**dnsPolicy**，将会使用 **ClusterFirst**

* 如果 dnsPolicy 被设置为 “Default”，则名字解析配置会继承自 Pod 运行所在的节点。自定义上游域名服务器和存根域不能够与这个策略一起使用
* 如果 dnsPolicy 被设置为 “ClusterFirst”，这就要依赖于是否配置了存根域和上游 DNS 服务器
    * 未进行自定义配置：没有匹配上配置的集群域名后缀的任何请求，例如 “www.kubernetes.io”，将会被转发到继承自节点的上游域名服务器。
    * 进行自定义配置：如果配置了存根域和上游 DNS 服务器（类似于 前面示例 配置的内容），DNS 查询将基于下面的流程对请求进行路由：
        * 查询首先被发送到 kube-dns 中的 DNS 缓存层。
        * 从缓存层，检查请求的后缀，并根据下面的情况转发到对应的 DNS 上：
            * 具有集群后缀的名字（例如 “.cluster.local”）：请求被发送到 kubedns。
            * 具有存根域后缀的名字（例如 “.acme.local”）：请求被发送到配置的自定义 DNS 解析器（例如：监听在 1.2.3.4）。
            * 未能匹配上后缀的名字（例如 “widget.com”）：请求被转发到上游 DNS（例如：Google 公共 DNS 服务器，8.8.8.8 和 8.8.4.4）。

![image](https://raw.githubusercontent.com/cnych/kubernetes-learning/master/docs/images/dns.png)

### 域名格式
我们前面说了如果我们建立的 Service 如果支持域名形式进行解析，就可以解决我们的服务发现的功能，那么利用 kubedns 可以将 Service 生成怎样的 DNS 记录呢？

* 普通的 Service：会生成 servicename.namespace.svc.cluster.local 的域名，会解析到 Service 对应的 ClusterIP 上，在 Pod 之间的调用可以简写成 servicename.namespace，如果处于同一个命名空间下面，甚至可以只写成 servicename 即可访问
* Headless Service：无头服务，就是把 clusterIP 设置为 None 的，会被解析为指定 Pod 的 IP 列表，同样还可以通过 podname.servicename.namespace.svc.cluster.local 访问到具体的某一个 Pod。

> CoreDNS 实现的功能和 KubeDNS 是一致的，不过 CoreDNS 的所有功能都集成在了同一个容器中，在最新版的1.11.0版本中官方已经推荐使用 CoreDNS了，大家也可以安装 CoreDNS 来代替 KubeDNS，其他使用方法都是一致的：https://coredns.io/


## 测试

创建nginx-service.yaml  
```
# cat nginx-service.yaml
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: nginx-deploy
  labels:
    k8s-app: nginx-demo
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.7.9
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  labels:
    name: nginx-service
spec:
  ports:
  - port: 5000
    targetPort: 80
  selector:
    app: nginx
```  

应用该服务  
```
# kubectl apply -f nginx-service.yaml
```  

现在我们来使用一个简单 Pod 来测试下 Service 的域名访问：
```shell
$ kubectl run --rm -i --tty test-dns --image=busybox /bin/sh
If you don't see a command prompt, try pressing enter.
/ # cat /etc/resolv.conf
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
/ #
```

进入到Pod中，查看**/etc/resolv.conf**中的内容，可以看到 nameserver 的地址**10.96.0.10**，该IP地址即是在安装kubedns插件的时候集群分配的一个固定的静态IP地址，我们可以通过下面的命令进行查看  
```shell
$ kubectl get svc kube-dns -n kube-system
NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)         AGE
kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP   62d
```  

也就是说这个Pod现在默认的nameserver就是kubedns的地址，现在来访问创建的nginx-service服务  
```shell
/ # wget -q -O- nginx-service.default.svc.cluster.local

```

可以使用wget命令去访问nginx-service服务的域名的时候被hang住了，这是因为上面我们建立Service的时候暴露的端口是5000  
```shell
/ # wget -q -O- nginx-service.default.svc.cluster.local:5000
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>

<p><em>Thank you for using nginx.</em></p>
</body>
</html>
```

加上5000端口，就正常访问到服务，再试一试访问：nginx-service.default.svc、nginx-service.default、nginx-service，在同namespace下可以直接访问  
