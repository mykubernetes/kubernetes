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
          hostPort: 80
        - name: https
          containerPort: 443
          hostPort: 443
        - name: admin
          containerPort: 8080
        args:
        - --configfile=/config/traefik.toml       #在启动参数添加文件
        - --api
        - --kubernetes
        - --logLevel=INFO
```  
