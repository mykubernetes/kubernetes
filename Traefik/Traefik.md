ingress(边缘节点)
===

官方文档：https://docs.traefik.io/user-guide/kubernetes/  
项目地址：https://github.com/containous/traefik  

https://github.com/containous/traefik/tree/v1.7/examples/k8s  

边缘节点（Edge Node），所谓的边缘节点即集群内部用来向集群外暴露服务能力的节点，集群外部的服务通过该节点来调用集群内部的服务，边缘节点是集群内外交流的一个Endpoint。

边缘节点要考虑两个问题
-	边缘节点的高可用，不能有单点故障，否则整个kubernetes集群将不可用
-	对外的一致暴露端口，即只能有一个外网访问IP和端口

对边缘节点打污点， 防止其他Pod被调度到ingress节点。
```
# kubectl  taint node node01 node-role.kubernetes.io/LB=LB-A1:NoSchedule
node/node01 tainted

# kubectl  taint node node02 node-role.kubernetes.io/LB=LB-B1:NoSchedule
node/node02 tainted
```

设置边缘节点label, 后面pod调度将根据NodeSelector选择对应的Node节点
```
# kubectl  label  nodes node01 edgenode=true
node/node01 labeled
# kubectl  label  nodes node02 edgenode=true
node/node02 labeled
```

以 DaemonSet 的方式在边缘节点 node 上启动一个 traefik，并使用 hostPort 的方式在Node节点监听80 、443端口

```
#  mkdir $HOME/traefik ; cd $HOME/traefik
```


1、创建RBAC文件
```
# vim traefik-rbac.yaml
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: traefik-ingress-controller
rules:
  - apiGroups:
      - ""
    resources:
      - services
      - endpoints
      - secrets
    verbs:
      - get
      - list
      - watch
  - apiGroups:
      - extensions
    resources:
      - ingresses
    verbs:
      - get
      - list
      - watch
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: traefik-ingress-controller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: traefik-ingress-controller
subjects:
- kind: ServiceAccount
  name: traefik-ingress-controller
  namespace: kube-system

# kubectl  apply -f traefik-rbac.yaml 
clusterrole.rbac.authorization.k8s.io/traefik-ingress-controller created
clusterrolebinding.rbac.authorization.k8s.io/traefik-ingress-controller created
```

2、创建traefik.toml配置文件
```
# vim traefik-configmap.yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  namespace: kube-system
  name: traefik-conf
data:
  traefik.toml: |
    insecureSkipVerify = true
    defaultEntryPoints = ["http","https"]
    [entryPoints]
      [entryPoints.ping]
      address=":8888"
      [entryPoints.ping.auth]
        [entryPoints.ping.auth.basic]
          users = [
           "admin:$apr1$ehrsakXa$zr4qevnn4t.gOV7J8Ia/y1",
           "test:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/",
         ]
    [ping]
    entryPoint = "ping"

      [entryPoints.http]
      address = ":80"
        [entryPoints.http.redirect]
        #entryPoint = "https"
      [entryPoints.https]
      address = ":443"
        [entryPoints.https.tls]
        minVersion = "VersionTLS12"
        cipherSuites = [
          "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
          "TLS_RSA_WITH_AES_256_GCM_SHA384"
        ]

      [[entryPoints.https.tls.certificates]]
      CertFile = "/ssl/tls.crt"
      KeyFile = "/ssl/tls.key"


#以configmap方式创建traefik.toml
# kubectl  apply -f traefik-configmap.yaml 
configmap/traefik-conf created
```

3、创建 secret
```
# openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=*.ziji.work"
Generating a 2048 bit RSA private key
...........+++
.......................+++
writing new private key to 'tls.key'
-----


[root@K8S-PROD-MASTER-A1 traefik]# ls -l tls.*
-rw-r--r-- 1 root root 1099 May  5 10:50 tls.crt
-rw-r--r-- 1 root root 1704 May  5 10:50 tls.key

# kubectl -n kube-system create secret tls traefik-cert --key=tls.key --cert=tls.crt
secret/traefik-cert created
```

4、部署Traefik
```
# vim traefik-deamonset.yaml

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: traefik-ingress-controller
  namespace: kube-system
---
kind: DaemonSet
apiVersion: extensions/v1beta1
metadata:
  name: traefik-ingress-controller
  namespace: kube-system
  labels:
    k8s-app: traefik-ingress-lb
spec:
  template:
    metadata:
      labels:
        k8s-app: traefik-ingress-lb
        name: traefik-ingress-lb
    spec:
      serviceAccountName: traefik-ingress-controller
      terminationGracePeriodSeconds: 60
      hostNetwork: true
      restartPolicy: Always
      volumes:
       - name: ssl
         secret:
          secretName: traefik-cert
       - name: traefik-config
         configMap:
          name: traefik-conf
      containers:
      - image: traefik:v1.7
        imagePullPolicy: IfNotPresent
        name: traefik-ingress-lb
        ports:
        - name: http
          containerPort: 80
          hostPort: 80
        - name: https
          containerPort: 443
          hostPort: 443
        - name: admin
          containerPort: 8080
          hostPort: 8080
        volumeMounts:
        - mountPath: "/ssl"
          name: "ssl"
        - mountPath: "/etc/traefik"
          name: "traefik-config"
        securityContext:
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE
        args:
        - --configfile=/etc/traefik/traefik.toml
        - --api
        - --kubernetes
        - --logLevel=INFO
      tolerations:
      - key: "edgenode"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      nodeSelector:
        edgenode: "true"
---
kind: Service
apiVersion: v1
metadata:
  name: traefik-ingress-service
  namespace: kube-system
spec:
  selector:
    k8s-app: traefik-ingress-lb
  ports:
    - protocol: TCP
      port: 80
      name: web
    - protocol: TCP
      port: 443
      name: https
    - protocol: TCP
      port: 8080
      targetPort: 8080
      name: admin


[root@K8S-PROD-MASTER-A1 traefik]# kubectl  apply -f traefik-deamonset.yaml 
serviceaccount/traefik-ingress-controller created
daemonset.extensions/traefik-ingress-controller created
service/traefik-ingress-service created
```

查看部署情况
```
[root@K8S-PROD-MASTER-A1 traefik]# kubectl  get pod,svc -n kube-system 
NAME                                        READY   STATUS    RESTARTS   AGE
pod/coredns-756d6db49-s6x84                 1/1     Running   2          2d6h
pod/coredns-756d6db49-sf9wj                 1/1     Running   2          2d6h
pod/kubernetes-dashboard-5974995975-8tlgv   1/1     Running   2          2d6h
pod/nginx-test2-65c869854f-h8lxb            1/1     Running   1          2d4h
pod/traefik-ingress-controller-rkvk2        1/1     Running   0          25s

NAME                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                   AGE
service/coredns                   ClusterIP   10.99.110.110   <none>        53/UDP,53/TCP,9153/TCP    4d21h
service/kubernetes-dashboard      NodePort    10.99.255.171   <none>        443:32279/TCP             4d15h
service/nginx-test2               NodePort    10.99.201.93    <none>        80:31001/TCP              2d4h
service/traefik-ingress-service   ClusterIP   10.99.89.99     <none>        80/TCP,443/TCP,8181/TCP   27s
service/traefik-web-ui            ClusterIP   10.99.229.113   <none>        80/TCP                    2d5h
```

其中 traefik 监听 node 的 80 和 443 端口，80/443 提供http/https服务，8080 是其自带的 UI 界面。 由于traefik1.7.11已经丢弃了以下参数，生产环境建议对8080端口做限制。
```
--web     (Deprecated) Enable Web backend with default settings (default "false")
--web.address (Deprecated) Web administration port  (default ":8080")
```

5、部署UI

生成https证书
```
# openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout traefik-edge.ziji.work.key -out traefik-edge.ziji.work.crt -subj "/CN=traefik-edge.ziji.work"

# kubectl -n kube-system create secret tls traefik-cert --key=traefik-edge.ziji.work.key --cert=traefik-edge.ziji.work.crt
```

为traefik创建ingress代理
```
# vi  traefik-web-ui.yaml

apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.class: traefik
    #301 http to https
    ingress.kubernetes.io/ssl-redirect: "true"
    # Forces the frontend to redirect to SSL  but by sending a 302 instead of a 301.
#ingress.kubernetes.io/ssl-temporary-redirect: "true"
#优先级
    ingress.kubernetes.io/priority: "100"
    #限制IP
    ingress.kubernetes.io/whitelist-x-forwarded-for: "true"
    ingress.kubernetes.io/whitelist-source-range: "192.168.1.0/24, 10.211.18.0/24"
    #设置后端service权重值
    ingress.kubernetes.io/service-weights: |
      traefik-web-ui: 100%
    #设置认证
    ingress.kubernetes.io/auth-type: "basic"
    ingress.kubernetes.io/auth-secret: "ingress-auth"
  name: traefik-web-ui
  namespace: kube-system
spec:
  rules:
  - host: traefik-edge.ziji.work
    http:
      paths:
      - path: /
        backend:
          serviceName: traefik-ingress-service
          servicePort: 8080
  tls:
   - secretName: traefik-edge.ziji.work

# kubectl  apply -f traefik-web-ui.yaml 
ingress.extensions/traefik-web-ui created



# kubectl  get  ingress -n kube-system
NAME             HOSTS                    ADDRESS   PORTS     AGE
traefik-web-ui   traefik-edge.ziji.work             80, 443   50s
```
将traefik-edge.ziji.work域名解析到边缘节点浮动IP(VIP)， 访问域名测试是否正常

输入认证信息：  admin/admin



部署Traefik
---

1、部署rbac.yaml  
``` # kubectl apply -f https://raw.githubusercontent.com/containous/traefik/v1.7/examples/k8s/traefik-rbac.yaml ```  

2、部署traefik  
``` # kubectl apply -f https://raw.githubusercontent.com/containous/traefik/v1.7/examples/k8s/traefik-deployment.yaml ```  

3、查看运行的pod  
```
# kubectl get pod -n kube-system -o wide -l k8s-app=traefik-ingress-lb
NAME                                         READY   STATUS    RESTARTS   AGE     IP           NODE     NOMINATED NODE   READINESS GATES
traefik-ingress-controller-8c8b85bbc-6hsrv   1/1     Running   0          4m27s   10.244.1.3   node02   <none>           <none>
```  

4、查看service，暴露的nodeport为31494  
```
# kubectl get svc -n kube-system
NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                       AGE
kube-dns                  ClusterIP   10.96.0.10       <none>        53/UDP,53/TCP                 139m
tiller-deploy             ClusterIP   10.107.124.240   <none>        44134/TCP                     87m
traefik-ingress-service   NodePort    10.103.194.16    <none>        80:31155/TCP,8080:31494/TCP   5m5s
```  

5、访问traefik的dashboard  
http://192.168.101.68:31494  


6、Ingress方式访问taefik dashboard  
``` kubectl apply -f https://raw.githubusercontent.com/containous/traefik/v1.7/examples/k8s/ui.yaml ```  

7、查看yaml配置：  
包含了一个service和一个ingress规则  
```
---
apiVersion: v1
kind: Service
metadata:
  name: traefik-web-ui
  namespace: kube-system
spec:
  selector:
    k8s-app: traefik-ingress-lb
  ports:
  - name: web
    port: 80
    targetPort: 8080
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: traefik-web-ui
  namespace: kube-system
spec:
  rules:
  - host: traefik-ui.minikube
    http:
      paths:
      - path: /
        backend:
          serviceName: traefik-web-ui
          servicePort: web
```  

8、查看ingress  
```
# kubectl get ingress -n kube-system
NAME             HOSTS                 ADDRESS   PORTS   AGE
traefik-web-ui   traefik-ui.minikube             80      2m4s



# kubectl describe ingress traefik-web-ui -n kube-system
Name:             traefik-web-ui
Namespace:        kube-system
Address:          
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host                 Path  Backends
  ----                 ----  --------
  traefik-ui.minikube  
                       /   traefik-web-ui:web (10.244.1.3:8080)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"extensions/v1beta1","kind":"Ingress","metadata":{"annotations":{},"name":"traefik-web-ui","namespace":"kube-system"},"spec":{"rules":[{"host":"traefik-ui.minikube","http":{"paths":[{"backend":{"serviceName":"traefik-web-ui","servicePort":"web"},"path":"/"}]}}]}}

Events:  <none>



# kubectl get service -n kube-system 
NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                       AGE
kube-dns                  ClusterIP   10.96.0.10       <none>        53/UDP,53/TCP                 150m
tiller-deploy             ClusterIP   10.107.124.240   <none>        44134/TCP                     99m
traefik-ingress-service   NodePort    10.103.194.16    <none>        80:31155/TCP,8080:31494/TCP   16m
traefik-web-ui            ClusterIP   10.101.131.216   <none>        80/TCP                        6m
```  

修改集群外主机hosts:  
```
192.168.101.66 traefik-ui.minikube
192.168.101.67 traefik-ui.minikube
192.168.101.68 traefik-ui.minikube
```  

http://traefik-ui.minikube:31494/dashboard/

9、部署自定义 Ingress
```
$ vim dashboard-ela-k8s-traefik.yaml

apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: dashboard-ela-k8s-traefik
  namespace: kube-system
  annotations:
    kubernetes.io/ingress.class: traefik
spec:
  rules:
  - host: dashboard.k8s.traefik
    http:
      paths:
      - path: /  
        backend:
          serviceName: kubernetes-dashboard
          servicePort: 80
  - host: ela.k8s.traefik
    http:
      paths:
      - path: /  
        backend:
          serviceName: elasticsearch-logging
          servicePort: 9200

$ kubectl create -f dashboard-ela-k8s-traefik.yaml
ingress "dashboard-ela-k8s-traefik" created

$ kubectl get ingress --all-namespaces
NAMESPACE     NAME                        HOSTS                                   ADDRESS   PORTS     AGE
kube-system   dashboard-ela-k8s-traefik   dashboard.k8s.traefik,ela.k8s.traefik             80        25s
kube-system   traefik-web-ui              traefik-ui.k8s                                    80        31m
```  

10、通过域名下不同的路径转发到不同的服务上去的 Ingress 配置  
```
$ vim my-k8s-traefik.yaml

apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: my-k8s-traefik
  namespace: kube-system
  annotations:
    kubernetes.io/ingress.class: traefik
    traefik.frontend.rule.type: PathPrefixStrip          #根据不同路径做转发需要配置此项
spec:
  rules:
  - host: my.k8s.traefik
    http:
      paths:
      - path: /dashboard
        backend:
          serviceName: kubernetes-dashboard
          servicePort: 80
      - path: /kibana
        backend:
          serviceName: kibana-logging
          servicePort: 5601

$ kubectl create -f my-k8s-traefik.yaml
ingress "my-k8s-traefik" created

$ kubectl get ingress --all-namespaces
NAMESPACE     NAME                        HOSTS                                   ADDRESS   PORTS     AGE
kube-system   dashboard-ela-k8s-traefik   dashboard.k8s.traefik,ela.k8s.traefik             80        12m
kube-system   my-k8s-traefik              my.k8s.traefik                                    80        4s
kube-system   traefik-web-ui              traefik-ui.k8s                                    80        43m
```  
- 注意：这里我们根据路径来转发，需要指明 rule 为 PathPrefixStrip，配置为 traefik.frontend.rule.type: PathPrefixStrip  


TLS 认证
---
1、创建ca证书  
```
# openssl req -newkey rsa:2048 -nodes -keyout tls.key -x509 -days 365 -out tls.crt
```  

2、创建一个secret对象来存储上面的证书  
```
# kubectl create secret generic traefik-cert --from-file=tls.crt --from-file=tls.key -n kube-system
```  

3、创建configmap
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: traefik-conf
  namespace: kube-system 
data:
traefik.toml: |
  defaultEntryPoints = ["http", "https"]

  [entryPoints]
    [entryPoints.http]
    address = ":80"
      [entryPoints.http.redirect]
        entryPoint = "https"
    [entryPoints.https]
    address = ":443"
      [entryPoints.https.tls]
        [[entryPoints.https.tls.certificates]]
        CertFile = "/ssl/tls.crt"
        KeyFile = "/ssl/tls.key"
```  
- [entryPoints.http] http接入
- [entryPoints.http.redirect] 强行跳转到https
- [entryPoints.https] https接入
- [entryPoints.https.tls] 指定证书文件路径


```
kind: Deployment
apiVersion: extensions/v1beta1
metadata:
  name: traefik-ingress-controller
  namespace: kube-system
  labels:
    k8s-app: traefik-ingress-lb
spec:
  replicas: 1
  selector:
    matchLabels:
      k8s-app: traefik-ingress-lb
  template:
    metadata:
      labels:
        k8s-app: traefik-ingress-lb
        name: traefik-ingress-lb
    spec:
      serviceAccountName: traefik-ingress-controller
      terminationGracePeriodSeconds: 60
      volumes:                         #将文件挂载到容器
      - name: ssl
        secret:
          secretName: traefik-cert
      - name: config
        configMap:
          name: traefik-conf
      tolerations:
      - operator: "Exists"
      nodeSelector:
        kubernetes.io/hostname: master
      containers:
      - image: traefik
        name: traefik-ingress-lb
        volumeMounts:
        - mountPath: "/ssl"
          name: "ssl"                     #挂载证书文件
        - mountPath: "/config"
          name: "config"                  #挂载配置文件
        ports:
        - name: http
          containerPort: 80
          hostPort: 80                    #暴露主机端口80
        - name: https
          containerPort: 443              #添加https暴露端口
          hostPort: 443                   #暴露主机端口443
        - name: admin
          containerPort: 8080
        args:
        - --configfile=/config/traefik.toml       #在启动参数添加文件
        - --api
        - --kubernetes
        - --logLevel=INFO
```  

应用配置查看日志  
```
$ kubectl apply -f traefik.yaml
$ kubectl logs -f traefik-ingress-controller-7dcfd9c6df-v58k7 -n kube-system
time="2018-08-26T11:26:44Z" level=info msg="Server configuration reloaded on :80"
time="2018-08-26T11:26:44Z" level=info msg="Server configuration reloaded on :443"
time="2018-08-26T11:26:44Z" level=info msg="Server configuration reloaded on :8080"
```  

测试
部署三个web服务
```
# cat backend.yaml
kind: Deployment
apiVersion: extensions/v1beta1
metadata:
  name: svc1
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: svc1
    spec:
      containers:
      - name: svc1
        image: cnych/example-web-service
        env:
        - name: APP_SVC
          value: svc1
        ports:
        - containerPort: 8080
          protocol: TCP

---
kind: Deployment
apiVersion: extensions/v1beta1
metadata:
  name: svc2
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: svc2
    spec:
      containers:
      - name: svc2
        image: cnych/example-web-service
        env:
        - name: APP_SVC
          value: svc2
        ports:
        - containerPort: 8080
          protocol: TCP

---
kind: Deployment
apiVersion: extensions/v1beta1
metadata:
  name: svc3
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: svc3
    spec:
      containers:
      - name: svc3
        image: cnych/example-web-service
        env:
        - name: APP_SVC
          value: svc3
        ports:
        - containerPort: 8080
          protocol: TCP

---
kind: Service
apiVersion: v1
metadata:
  labels:
    app: svc1
  name: svc1
spec:
  type: ClusterIP
  ports:
  - port: 8080
    name: http
  selector:
    app: svc1

---
kind: Service
apiVersion: v1
metadata:
  labels:
    app: svc2
  name: svc2
spec:
  type: ClusterIP
  ports:
  - port: 8080
    name: http
  selector:
    app: svc2

---
kind: Service
apiVersion: v1
metadata:
  labels:
    app: svc3
  name: svc3
spec:
  type: ClusterIP
  ports:
  - port: 8080
    name: http
  selector:
    app: svc3
```  

应用配置
```
# kubectl create -f backend.yaml
deployment.extensions "svc1" created
deployment.extensions "svc2" created
deployment.extensions "svc3" created
service "svc1" created
service "svc2" created
service "svc3" created
```  

配置ingress对象  
```
# example-ingress.yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: example-web-app
  annotations:
    kubernetes.io/ingress.class: "traefik"
spec:
  rules:
  - host: example.haimaxy.com
    http:
      paths:
      - path: /s1
        backend:
          serviceName: svc1
          servicePort: 8080
      - path: /s2
        backend:
          serviceName: svc2
          servicePort: 8080
      - path: /
        backend:
          serviceName: svc3
          servicePort: 8080
```  

应用配置
```
$ kubectl create -f example-ingress.yaml
ingress.extensions "example-web-app" created
$ kubectl get ingress
NAME              HOSTS                 ADDRESS   PORTS     AGE
example-web-app   example.haimaxy.com             80        1m
$ kubectl describe ingress example-web-app
Name:             example-web-app
Namespace:        default
Address:
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host                 Path  Backends
  ----                 ----  --------
  example.haimaxy.com
                       /s1   svc1:8080 (<none>)
                       /s2   svc2:8080 (<none>)
                       /     svc3:8080 (<none>)
Annotations:
  kubernetes.io/ingress.class:  traefik
Events:                         <none>
```  

不同的服务配置不同的证书方式
```
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: example-web-app
  annotations:
    kubernetes.io/ingress.class: "traefik"
spec:
  tls:
    - secretName: traefik-cert
  rules:
  - host:
```
  

