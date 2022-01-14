# Kubernetes 映射外部服务到集群内部的场景

## 场景 1.集群外的数据库映射到集群内部(IP地址)

描述: 如果您在 Kubernetes 内部和外部分别运行一些服务应用，此时应用如果分别依赖集群内部和外部应用时，通过采用将集群外部服务映射到K8s集群内部。

希望未来某个时候您可以将所有服务都移入集群内，但在此之前将是“内外混用”的状态。幸运的是您可以使用静态 Kubernetes 服务来缓解上述痛点。

在本例中，假如有一个集群外的 MySQL 服务器, 由于此服务器在与 Kubernetes 集群相同的网络（或 VPC）中创建，因此可以使用高性能的内部 IP 地址映射到集群内部以供Pod访问。

- 第一步,我们创建一个将从此服务接收流量的 Endpoints 对象并将该对象与Service进行绑定。
```
# 非常注意: service和endpoint名字要相同属于同一个名称空间.
tee mapping-svc-ep.yaml << 'EOF'
kind: Endpoints
apiVersion: v1
metadata:
  name: mysqldb
  namespace: test
subsets:
  - addresses:
    - ip: 192.168.12.50
    ports:
    - port: 3306
      protocol: TCP
---

kind: Service
apiVersion: v1
metadata:
  name: mysqldb
  namespace: test
spec:
  type: ClusterIP  
  ports:
  - port: 13306
    protocol: TCP
    targetPort: 3306
EOF
```

- 第二步,创建Service和Endpoints,然后您可以看到 Endpoints 手动定义了数据库的 IP 地址，并且使用的名称与服务名称相同。
```
$ kubectl apply -f mapping-svc-ep.yaml
  # endpoints/mysqldb created
  # service/mysqldb created
$ kubectl describe svc/mysql -n test
  # Name:              mysqldb
  # Namespace:         test
  # Labels:            <none>
  # Annotations:       <none>
  # Selector:          <none>
  # Type:              ClusterIP
  # IP:                10.102.172.40
  # Port:              <unset>  13306/TCP  # 集群内部访问的映射端口
  # TargetPort:        3306/TCP            # 目标服务端口
  # Endpoints:         192.168.12.50:3306  # 目标服务IP及端口
  # Session Affinity:  None
  # Events:            <none>

$ kubectl get svc -n test mysqldb
  NAME    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
  mysql   ClusterIP   10.102.172.40   <none>        13306/TCP   23s
```

- 第三步,集群内部Pod访问映射的MySQL服务。
```
# Telnet cluster_ip mapping_port
$ telnet 10.102.172.40 13306
  # Trying 10.102.172.40...
  # Connected to 10.102.172.40.
  # Escape character is '^]'.

  # 5.5.5-10.4.18-MariaDB-1:10.4.18+maria~bionic-log&

# 创建测试Pod
~$ kubectl run busybox-demo -n test --image=busybox:latest --command -- sleep 3600
~$ kubectl get pod -n test
  # NAME                         READY   STATUS             RESTARTS   AGE
  # busybox-demo                 1/1     Running            0          11s

# 进入Pod的终端
$ kubectl exec -it -n test busybox-demo -- sh
ping mysql.test.svc -c 1
  # PING mysql.test.svc (10.102.172.40): 56 data bytes
  # 64 bytes from 10.102.172.40: seq=0 ttl=64 time=0.062 ms
telnet mysql.test.svc 13306  # 连接方式1
  # Connected to mysql.test.svc
  # t
  # 5.5.5-10.4.18-MariaDB-1:10.4.18+maria~bionic-log(AxY7G<8C▒'8&SPv&TU0/8mysql_native_passwordxterm-256color
  # !#08S01Got packets out of orderConnection closed by foreign host
telnet mysql 13306          # 连接方式2
  Connected to mysql
  ....
  5.5.5-10.4.18-MariaDB-1:10.4.18+maria~bionic-log
  ...
```
Kubernetes 将 Endpoints 中定义的所有 IP 地址视为与常规 Kubernetes Pod 一样。现在您可以用一个简单的连接字符串访问数据库：mysql://mysql.test.svc 或者 mysql://mysql

根本不需要在代码中使用 IP 地址！如果以后 IP 地址发生变化，您可以为端点更新 IP 地址，而应用无需进行任何更改。

## 场景 2.具有 URI 的远程服务映射到集群内部

描述: 如果您使用的是来自第三方的托管网站，它们可能会为您提供可用于连接的统一资源标识符 (URI)。

如果它们为您提供 IP 地址，则可以使用场景 1 中的方法。

在本例中，我在 集群外部创建了一个网站，而我想在集群内部进行重定向访问。

- 第一步，编写部署的资源清单。
```
cat > mapping-svc-ExternalName.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: myweb
  namespace: test
spec:
  type: ExternalName
  externalName: www.weiyigeek.top
EOF
```

- 第二步，部署ExternalName类型的services, 我们创建一个 “ExternalName” Kubernetes 服务，此服务为您提供将流量重定向到外部服务的静态 Kubernetes 服务。此服务在内核级别执行简单的 CNAME 重定向，因此对性能的影响非常小。
```
~$ kubectl apply -f mapping-svc-ExternalName.yaml
~$ kubectl describe svc/myweb -n test
  # Name:              myweb
  # Namespace:         test
  # Labels:            <none>
  # Annotations:       <none>
  # Selector:          <none>
  # Type:              ExternalName
  # IP:
  # External Name:     www.weiyigeek.top  # 外部域名
  # Session Affinity:  None
  # Events:            <none>

~$ kubectl get svc -n test myweb
  NAME    TYPE           CLUSTER-IP   EXTERNAL-IP       PORT(S)   AGE
  myweb   ExternalName   <none>       www.weiyigeek.top   <none>    48s
```

- 第三步,进入Pod中进行访问测试
```
~$ kubectl exec -it -n test busybox-demo -- sh
ping myweb
  # PING myweb (192.168.12.18): 56 data bytes
  # 64 bytes from 192.168.12.18: seq=0 ttl=63 time=0.344 ms

wget myweb/api.json # 由于Busybox 中不带curl 此处简单采用wget进行演示
  # Connecting to myweb (192.168.12.18:80)
  # saving to 'api.json'
  # api.json             100%  15  0:00:00 ETA
  # 'api.json' saved

cat api.json
  # {"status":"ok"}

wget --spider myweb.test.svc/api.json # 
  # Connecting to myweb.test.svc (192.168.12.18:80)
  # remote file exists
```
Tips: 非常注意,由于 “ExternalName” 使用 CNAME 重定向，因此无法执行端口重映射我们无法使用port指定集群内部访问端口字段。


## 场景 3.具有 URI 和端口重映射功能的远程托管数据库

描述: CNAME 重定向对于每个环境均使用相同端口的服务非常有效，但如果每个环境的不同端点使用不同的端口，CNAME 重定向就略显不足，此时我们可以

幸运的是我们可以使用一些基本工具来解决这个问题，手动创建无头服务及endpoint，引入外部数据库，然后通过k8s集群中的域名解析服务访问，访问的主机名格式为[svc_name].[namespace_name].svc.cluster.local。

在本例中，我在其它K8S集群外部创建了一个appspring的应用，而我想在当前集群通过集群services进行访问调用。

- 第一步，资源清单的创建，此处使用无头服务，对应的svc及endpoint配置文件应该如下。
```
tee svc-ep-clusterIP.yaml << 'EOF'
kind: Endpoints
apiVersion: v1
metadata:
  name: appspring
  namespace: test
  labels:
    app: appspring
subsets:
  - addresses:
    - ip: 10.41.40.21
    - ip: 10.41.40.22
    - ip: 10.41.40.23
    ports:
    - name: http
      port: 32179
      protocol: TCP
---
kind: Service
apiVersion: v1
metadata:
  name: appspring
  namespace: test
  labels:
    app: appspring
spec:
  clusterIP: None
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 32179
  type: ClusterIP
EOF
```

- 第二步,创建service及endpoint
```
$ kubectl apply -f svc-ep-clusterIP.yaml
  # endpoints/appspring created
  # service/appspring created

$ kubectl describe svc/appspring -n test
  # Name:              appspring
  # Namespace:         test
  # Labels:            app=appspring
  # Annotations:       <none>
  # Selector:          <none>
  # Type:              ClusterIP
  # IP:                None
  # Port:              http  80/TCP  # 映射到集群内部端口
  # TargetPort:        32179/TCP
  # Endpoints:         10.41.40.21:32179,10.41.40.22:32179,10.41.40.23:32179    # 目标负载IP以及应用端口
  # Session Affinity:  None
  # Events:            <none>

$ kubectl get svc -n test
  # NAME   TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
  # appspring   ClusterIP   None         <none>        80/TCP    4m45s
```

- 第三步,在k8s集群中启动一个alpine:latest容器进行验证：
```
kubectl run alpine-demo -n test --image=alpine:latest --command -- sleep 3600
kubectl exec -it -n test  alpine-demo -- sh
/ # ping appspring -c 1  # 可以看出是轮询请求的
PING appspring (10.41.40.22): 56 data bytes
64 bytes from 10.41.40.22: seq=0 ttl=60 time=1.196 ms

/ # ping appspring -c 1
PING appspring (10.41.40.21): 56 data bytes
64 bytes from 10.41.40.21: seq=0 ttl=60 time=1.273 ms

/ # ping appspring -c 1
PING appspring (10.41.40.23): 56 data bytes
64 bytes from 10.41.40.23: seq=0 ttl=60 time=1.304 ms

/ # wget appspring:32179
Connecting to appspring:32179 (10.41.40.22:32179)
Connecting to appspring:32179 (10.41.40.21:32179)
saving to 'index.html'
index.html           100% |*************************************************************************|  5275  0:00:00 ETA
'index.html' saved
/ # cat index.html

/ # ls -alh index.html
-rw-r--r--    1 root     root        5.2K Dec  6 14:58 index.htm
```
注：URI 可以使用 DNS 在多个 IP 地址之间进行负载平衡，因此，如果 IP 地址发生变化，这个方法可能会有风险！如果您通过上述命令获取多个 IP 地址，则可以将所有这些地址都包含在 Endpoints YAML 中，并且 Kubernetes 会在所有 IP 地址之间进行流量的负载平衡。


## 映射总结:

将外部服务映射到内部服务可让您未来灵活地将这些服务纳入集群，同时最大限度地减少重构工作。即使您今天不打算将服务加入集群，以后可能也会这样做！而且，这样一来，您可以更轻松地管理和了解组织所使用的外部服务。

如果外部服务具有有效域名，并且您不需要重新映射端口，那么使用 “ExternalName” 服务类型将外部服务映射到内部服务十分简便、快捷。如果您没有域名或需要执行端口重映射，只需将 IP 地址添加到端点并使用即可。

至此从K8s集群中引入外部服务实践完成。
