Service的类型
---
- ClusterIp：默认类型，自动分配一个仅 Cluster 内部可以访问的虚拟 IP
- NodePort：在 ClusterIP 基础上为 Service 在每台机器上绑定一个端口，这样就可以通过 : NodePort 来访问该服务
- LoadBalancer：在 NodePort 的基础上，借助 cloud provider 创建一个外部负载均衡器，并将请求转发到: NodePort
- ExternalName：把集群外部的服务引入到集群内部来，在集群内部直接使用。没有任何类型代理被创建，这只有 kubernetes 1.7 或更高版本的 kube-dns 才支持

工作原理  
---
- apiserver 用户通过kubectl命令向apiserver发送创建service的命令，apiserver接收到请求后将数据存储到etcd中
- kube-proxy kubernetes的每个节点中都有一个叫做kube-porxy的进程，这个进程负责感知service，pod的变化，并将变化的信息写入本地的iptables规则中
- iptables 使用NAT等技术将virtualIP的流量转至endpoint中

代理模式分类  
---
1、userspace代理模式  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/service1.png)  

2、iptables代理模式  
查看规则  
```
# iptables -t nat -nvL
```  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/service2.png)  

3、ipvs代理模式  
查看规则  
```
# ipvsadm -Ln
```  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/service3.png)  

```
kind: Service
apiVersion: v1
metadata:
  name: myapp-svc-nodeport
spec:
  clusterIP: None                   #配置clusterIP为无头服务,tyep只能为clusterIP生效
  type: NodePort                    #配置svc类型默认为clusterIP
  sessionAffinity: ClientIP         #session绑定默认值为None(不启用)   ClientIP,None   效果不佳，不建议使用
  selector:
    app: myapp                      #对应pod的标签
  ports:
  - protocol: TCP                   #协议，默认tcp
    port: 80                        #server端口
    targetPort: 80                  #pod端口
    nodePort: 32223                 #集群接入，主机端口，范围30000-32767
```

服务解析
---
普通pod的地址解析
- svc_name.svc_ns_name.svc.cluster.local
```
dig -t A myapp-svc.default.svc.cluster.local @10.96.0.10
```

解析statefulset的pod IP 地址
- pod_name.svc_name.ns_name.svc.cluster.local
```
dig -t A myapp-0.myapp.default.svc.cluster.local @10.96.0.10
进入容器的解析方式
nslookup myapp-0.myapp.default.svc.cluster.local
```

解析过程svc_name.svc_ns.svc.cluster.local
```
# dig -t A external-www-svc.default.svc.cluster.local @10.96.0.10

; <<>> DiG 9.9.4-RedHat-9.9.4-73.el7_6 <<>> -t A external-www-svc.default.svc.cluster.local @10.96.0.10
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 48496
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 3, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;external-www-svc.default.svc.cluster.local. IN A

;; ANSWER SECTION:
external-www-svc.default.svc.cluster.local. 5 IN CNAME www.kubernetes.io.
www.kubernetes.io.	5	IN	CNAME	kubernetes.io.
kubernetes.io.		5	IN	A	45.54.44.102

;; Query time: 123 msec
;; SERVER: 10.96.0.10#53(10.96.0.10)
;; WHEN: Thu Mar 21 16:17:31 EDT 2019
;; MSG SIZE  rcvd: 206
```
实验  
---
1、创建myapp-deploy.yaml文件
```
# vim myapp-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deploy
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      release: stabel
  template:
    metadata:
      labels:
        app: myapp
        release: stabel
        env: test
    spec:
      containers:
      - name: myapp
        image: wangyanglinux/myapp:v2
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 80
```  

2、ClusterIP  
clusterIP 主要在每个 node 节点使用 iptables，将发向 clusterIP 对应端口的数据，转发到 kube-proxy 中。然后 kube-proxy 自己内部实现有负载均衡的方法，并可以查询到这个 service 下对应 pod 的地址和端口，进而把数据转发给对应的 pod 的地址和端口  
```
# vim myapp-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: myapp
    release: stabel
  ports:
  - name: http
    port: 80
    targetPort: 80
```  

3、Headless Service  
有时不需要或不想要负载均衡，以及单独的Service IP。遇到这种情况，可以通过指定Cluster IP(spec.clusterIP) 的值为 “None” 来创建 Headless Service 。这类 Service 并不会分配 Cluster IP， kube-proxy 不会处理它们，而且平台也不会为它们进行负载均衡和路由
```
# vim myapp-svc-headless.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-headless
  namespace: default
spec:
  selector:
    app: myapp
  clusterIP: "None"
  ports:
  - port: 80
    targetPort: 80
    
    
    
# dig -t A myapp-headless.default.svc.cluster.local. @10.96.0.10
```  



4、NodePort  
nodePort的原理在于在node上开了一个端口，将向该端口的流量导入到kube-proxy，然后由kube-proxy进一步到给对应的 pod
```
# vim myapp-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  type: LoadBalancer
  selector:
    app: myapp
    release: stabel
  ports:
  - name: http
    port: 80
    targetPort: 80
```  

5、LoadBalancer  
loadBalancer 和 nodePort 其实是同一种方式。区别在于 loadBalancer 比 nodePort 多了一步，就是可以调用cloud provider 去创建 LB 来向节点导流  
```
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  type: NodePort
  selector:
    app: myapp
    release: stabel
  ports:
  - name: http
    port: 80
    targetPort: 80
```  


6、ExternalName  
这种类型的 Service 通过返回 CNAME 和它的值，可以将服务映射到 externalName 字段的内容( 例如：www.baidu.com )。ExternalName Service 是Service 的特例，它没有 selector，也没有定义任何的端口和Endpoint。相反的，对于运行在集群外部的服务，它通过返回该外部服务的别名这种方式来提供服务
```
kind: Service
apiVersion: v1
metadata:
  name: my-service-1
  namespace: default
spec:
  type: ExternalName
  externalName: www.baidu.com
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
    nodePort: 0
  selector: {}
```  

7、定义Endpoints资源
```
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: default
spec:
  clusterIP: None
  ports:
  - port: 9093
    protocol: TCP
---
kind: Endpoints
apiVersion: v1
metadata:
  name: alertmanager
  namespace: default
subsets:
  - addresses:
      - ip: 10.211.18.5
    ports:
      - port:9093
        protocol: TCP
```




