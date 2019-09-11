TLS 认证  
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
  
