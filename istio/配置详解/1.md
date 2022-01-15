在Kubernetes环境中，Kubernetes Ingress用于配置需要在集群外部公开的服务。但是在Istio服务网格中，更好的方法是使用新的配置模型，即Istio Gateway。Gateway允许将Istio流量管理的功能应用于进入集群的流量。

gateway 分为两种，分别是ingress-gateway和egress-gateway，分别用来处理入口流量和出口流量。gateway本质也是一个envoy pod。

# 资源详解

## selector

1.7.0/gateway/gateway-01.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
```


## servers.hosts

所有域名：

1.7.0/gateway/gateway-server-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
```

具体域名：

1.7.0/gateway/gateway-server-hosts-bookinfo-com.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "bookinfo.com"
```

多个域名：

1.7.0/gateway/gateway-server-hosts-multi.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "bookinfo.com"
    - "bookinfo.demo"
```

混合域名

1.7.0/gateway/gateway-server-hosts-mix.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*.com"
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "bookinfo.com"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

name

1.7.0/gateway/gateway-server-name.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
    name: bookinfo-gateway
```

## port

| Field | Type | Description | Required |
|-------|------|--------------|---------|
| number | uint32 | 一个有效的端口号 | 是 |
| protocol | string | 所使用的协议，支持HTTP|HTTPS|GRPC|HTTP2|MONGO|TCP|TLS. | 是 |
| name | string | 给端口分配一个名称 | 是 |

istio支持的协议：
- grpc
- grpc-web
- http
- http2
- https
- mongo
- mysql*
- redis*
- tcp
- tls
- udp

* These protocols are disabled by default to avoid accidentally enabling experimental features. To enable them, configure the corresponding Pilot environment variables.

## http

1、部署gateway

1.7.0/gateway/gateway-01.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
```

2、部署vs

1.7.0/virtaulservice/vs-bookinfo-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

3、访问浏览器

https

1、创建secret
```
kubectl create -n istio-system secret tls istio-ingressgateway-certs --key ./cert.key --cert=./cert.crt

kubectl exec deploy/istio-ingressgateway -n istio-system – ls /etc/istio/ingressgateway-certs
```

2、创建gateway

1.7.0/gateway/gateway-https.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "bookinfo.demo"
    - "ratings.demo"
    tls:
      mode: SIMPLE
      serverCertificate: /etc/istio/ingressgateway-certs/tls.crt
      privateKey: /etc/istio/ingressgateway-certs/tls.key
```

3、创建vs

1.7.0/virtaulservice/vs-bookinfo-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

4、访问浏览器

tcp

1、创建gateway

1.7.0/gateway/gateway-tcp.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: tcp-echo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 31400
      name: tcp
      protocol: TCP
    hosts:
    - "*"
```

2、创建vs dr

1.7.0/gateway/protocol/vs-dr-tcp-echo.yaml
```
kind: DestinationRule
metadata:
  name: tcp-echo-destination
spec:
  host: tcp-echo
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: tcp-echo
spec:
  hosts:
  - "*"
  gateways:
  - tcp-echo-gateway
  tcp:
  - match:
    - port: 31400
    route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
        subset: v1
```

3、添加端口
```
kubectl edit svc istio-ingressgateway -n istio-system
```

4、测试

telnet 10.68.12.164 31400

http2

1、创建gateway

1.7.0/gateway/gateway-http2.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 15444
      name: http2
      protocol: HTTP2
      targetPort: 15444
    hosts:
    - "*"
```

2、部署vs

1.7.0/virtaulservice/ vs-bookinfo-hosts-star.yaml
```
kubectl apply -f vs-bookinfo-hosts-star.yaml -n istio
```

```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

3、访问浏览器

mongo

1、部署gateway

1.7.0/gateway/gateway-mongo.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: mongo
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 27017
      name: mongo
      protocol: MONGO
    hosts:
    - "*"
```

2、部署vs

1.7.0/gateway/protocol/vs-mongodb.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: mongo
spec:
  hosts:
  - "*"
  gateways:
  - mongo
  tcp:
  - match:
    - port: 27017
    route:
    - destination:
        host: mongodb.istio.svc.cluster.local
        port:
          number: 27017
```

3、添加端口
```
kubectl edit svc istio-ingressgateway -n istio-system
```

4、测试

tls

1、创建gateway

1.7.0/gateway/gateway-tls.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 15443
      name: tls
      protocol: TLS
    hosts:
    - "bookinfo.com"
    tls:
      mode: SIMPLE
      serverCertificate: /etc/istio/ingressgateway-certs/tls.crt
      privateKey: /etc/istio/ingressgateway-certs/tls.key
```

2、创建vs

1.7.0/gateway/protocol/vs-tls-protocol-echo.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: tcp-echo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  tcp:
  - match:
    - port: 15443
    route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
```

3、修改/etc/hosts

10.68.12.164 bookinfo.com

4、测试
```
openssl s_client -connect bookinfo.com:15443 -servername bookinfo.com
```

mysql

1、创建gateway

1.7.0/gateway/gateway-mysql.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: mysql
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 3306
      name: mysql
      protocol: MYSQL
    hosts:
    - "*"
~
```

2、创建vs

1.7.0/gateway/protocol/vs-mysql.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: mysql
spec:
  hosts:
  - "*"
  gateways:
  - mysql
  tcp:
  - match:
    - port: 3306
    route:
    - destination:
        host: mysqldb.istio.svc.cluster.local
        port:
          number: 3306
```

3、新增端口
```
kubectl edit svc istio-ingressgateway -nistio-system
```

4、istio启用mysql协议
```
kubectl set env deploy istiod -n istio-system PILOT_ENABLE_MYSQL_FILTER=true
```

5、测试
```
mysql -h 192.168.198.154 --port 37031 -uroot -p
```

redis

1、创建gateway

1.7.0/gateway/gateway-redis.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: redis
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 6379
      name: redis
      protocol: REDIS
    hosts:
    - "*"
~
```

2、部署redis

1.7.0/gateway/protocol/redis-deploy.yaml
```
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: bcia
    ms-name: redis
  name: bcia-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bcia
      ms-name: redis
  template:
    metadata:
      labels:
        app: bcia
        ms-name: redis
      name: bcia-redis
    spec:
     containers:
     - name: bcia-redis
       image: redis:5.0.8
       command:
         - "redis-server"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: bcia
    ms-name: redis
  ports:
  - port: 6379
    targetPort: 6379
```

3、创建vs

1.7.0/gateway/protocol/vs-redis.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: redis
spec:
  hosts:
  - "*"
  gateways:
  - redis
  tcp:
  - match:
    - port: 6379
    route:
    - destination:
        host: redis.istio.svc.cluster.local
        port:
          number: 6379
```

4、新增端口
```
kubectl edit svc istio-ingressgateway -nistio-system
```

5、istio启用redis协议
```
kubectl set env deploy istiod -n istio-system PILOT_ENABLE_REDIS_FILTER=true
```
6、测试
```
redis-cli -h 192.168.198.154 -p 29525
```

## tls

| Field | Type | Description | Required |
|-------|------|-------------|-----------|
| httpsRedirect | bool | 是否要做HTTP重定向 |否 |
| mode | TLSmode | 在配置的外部端口上使用 TLS 服务时，可以取 PASSTHROUGH、SIMPLE、MUTUAL、AUTO_PASSTHROUGH 这 4 种模式 | 否 |
| serverCertificate | string | 服务端证书的路径。当模式是 SIMPLE 和 MUTUAL 时必须指定 | 否 |
| privateKey | string | 服务端密钥的路径。当模式是 SIMPLE 和 MUTUAL 时必须指定 | 否 |
| caCertificates | string | CA 证书路径。当模式是 MUTUAL 时指定 | 否 |
| credentialName | string | 用于唯一标识服务端证书和秘钥。Gateway 使用 credentialName从远端的凭证存储中获取证书和秘钥，而不是使用 Mount 的文件 | 否 |
| subjectAltNames | string[] | SAN 列表，SubjectAltName 允许一个证书指定多个域名 | 否 |
| verifyCertificateSpki | string[] | 授权客户端证书的SKPI的base64编码的SHA-256哈希值的可选列表 | 否 |
| verifyCertificateHash | string[] | 授权客户端证书的十六进制编码SHA-256哈希值的可选列表 | 否 |
| minProtocolVersion | TLSProtocol | TLS 协议的最小版本 | 否 |
| maxProtocolVersion | TLSProtocol | TLS 协议的最大版本 | 否 |
| cipherSuites | string[] | 指定的加密套件，默认使用 Envoy 支持的加密套件 | 否 |

## httpsRedirect

1.7.0/gateway/tls/gw-httpsRedirect.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
    tls:
      httpsRedirect: true
  - port:
      number: 443
      name: https-443
      protocol: HTTPS
    hosts:
    - "*"
    tls:
      mode: SIMPLE
      serverCertificate: /etc/istio/ingressgateway-certs/tls.crt
      privateKey: /etc/istio/ingressgateway-certs/tls.key
```

```
wget http://bookinfo.com:80/productpage --no-check-certificate
```

测试访问浏览器

## mode

| Name | Description |
|------|-------------|
| PASSTHROUGH | 客户端提供的SNI字符串将用作VirtualService TLS路由中的匹配条件，以根据服务注册表确定目标服务 |
| SIMPLE | 使用标准TLS语义的安全连接 |
| MUTUAL | 通过提供服务器证书进行身份验证，使用双边TLS来保护与下游的连接 |
| AUTO_PASSTHROUGH | 与直通模式相似，不同之处在于具有此TLS模式的服务器不需要关联的VirtualService即可从SNI值映射到注册表中的服务。目标详细信息（例如服务/子集/端口）被编码在SNI值中。代理将转发到SNI值指定的上游（Envoy）群集（一组端点）。 |
| ISTIO_MUTUAL | 通过提供用于身份验证的服务器证书，使用相互TLS使用来自下游的安全连接 |

## PASSTHROUGH

1、创建证书
```
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -subj ‘/O=example Inc./CN=example.com’ -keyout example.com.key -out example.com.crt

openssl req -out nginx.example.com.csr -newkey rsa:2048 -nodes -keyout nginx.example.com.key -subj “/CN=nginx.example.com/O=some organization”

openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 0 -in nginx.example.com.csr -out nginx.example.com.crt
```

2、创建secret
```
kubectl create secret tls nginx-server-certs --key nginx.example.com.key --cert nginx.example.com.crt -n istio
```

3、创建nginx配置文件
```
events {
}

http {
  log_format main '$remote_addr - $remote_user [$time_local]  $status '
  '"$request" $body_bytes_sent "$http_referer" '
  '"$http_user_agent" "$http_x_forwarded_for"';
  access_log /var/log/nginx/access.log main;
  error_log  /var/log/nginx/error.log;

  server {
    listen 443 ssl;

    root /usr/share/nginx/html;
    index index.html;

    server_name nginx.example.com;
    ssl_certificate /etc/nginx-server-certs/tls.crt;
    ssl_certificate_key /etc/nginx-server-certs/tls.key;
  }
}
```

```
kubectl create configmap nginx-configmap --from-file=nginx.conf=./nginx.conf -nistio
```

4、创建deploy
```
apiVersion: v1
kind: Service
metadata:
  name: my-nginx
  labels:
    run: my-nginx
spec:
  ports:
  - port: 443
    protocol: TCP
  selector:
    run: my-nginx
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nginx
spec:
  selector:
    matchLabels:
      run: my-nginx
  replicas: 1
  template:
    metadata:
      labels:
        run: my-nginx
    spec:
      containers:
      - name: my-nginx
        image: nginx
        ports:
        - containerPort: 443
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx
          readOnly: true
        - name: nginx-server-certs
          mountPath: /etc/nginx-server-certs
          readOnly: true
      volumes:
      - name: nginx-config
        configMap:
          name: nginx-configmap
      - name: nginx-server-certs
        secret:
          secretName: nginx-server-certs
```

5、创建gateway
```
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https-443
      protocol: HTTPS
    hosts:
    - "nginx.example.com"
    tls:
      mode: PASSTHROUGH
```

6、创建vs
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: nginx
spec:
  hosts:
  - nginx.example.com
  gateways:
  - bookinfo-gateway
  tls:
  - match:
    - port: 443
      sniHosts:
      - nginx.example.com
    route:
    - destination:
        host: my-nginx
        port:
          number: 443
```

7、访问url

https://nginx.example.com:39329/

## SIMPLE

1、创建gateway

1.7.0/gateway/tls/simple/gateway-simple.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "bookinfo.demo"
    - "ratings.demo"
    - "nginx.example.com"
    tls:
      mode: SIMPLE
      serverCertificate: /etc/istio/ingressgateway-certs/tls.crt
      privateKey: /etc/istio/ingressgateway-certs/tls.key
```

2、创建vs

1.7.0/virtaulservice/vs-bookinfo-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

3、访问 https://bookinfo.demo:39329/productpage

## MUTUAL

1、创建证书
```
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -subj ‘/O=example Inc./CN=example.com’ -keyout example.com.key -out example.com.crt

openssl req -out bookinfo.example.com.csr -newkey rsa:2048 -nodes -keyout bookinfo.example.com.key -subj “/CN=bookinfo.example.com/O=some organization”

openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 0 -in bookinfo.example.com.csr -out bookinfo.example.com.crt
```

2、创建secret
```
kubectl create -n istio-system secret generic bookinfo-credential --from-file=tls.key=bookinfo.example.com.key --from-file=tls.crt=bookinfo.example.com.crt --from-file=ca.crt=example.com.crt
```

3、创建gateway

1.7.0/gateway/tls/mutual/gateway-mutual.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
 name: bookinfo-gateway
spec:
 selector:
   istio: ingressgateway 
 servers:
 - port:
     number: 443
     name: https
     protocol: HTTPS
   tls:
     mode: MUTUAL
     credentialName: bookinfo-credential 
   hosts:
   - bookinfo.example.com
```

4、创建vs

1.7.0/virtaulservice/vs-bookinfo-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

5、生成客户端证书
```
openssl req -out client.example.com.csr -newkey rsa:2048 -nodes -keyout client.example.com.key -subj “/CN=client.example.com/O=client organization”

openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 1 -in client.example.com.csr -out client.example.com.crt
```

6、访问
```
curl -v -HHost:bookinfo.example.com --resolve “bookinfo.example.com:39329:192.168.198.154” --cacert example.com.crt --cert client.example.com.crt --key client.example.com.key “https://bookinfo.example.com:39329/productpage”
```

## AUTO_PASSTHROUGH

http://www.finbit.org/docs/examples/multicluster/split-horizon-eds//eAEFwUEKwCAMBMAX2b37m6IBF2IjboTS13dmZC5VgErGxUCPJth7z-UmzOPJ5kdpG1rOLCM2v3iKdeEH6-4X5Q,

主要用于多k8s集群，单istio控制面
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: tls
      protocol: TLS
    tls:
      mode: AUTO_PASSTHROUGH
    hosts:
    - "*.local"
```

## ISTIO_MUTUAL

1、创建证书
```
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -subj ‘/O=example Inc./CN=example.com’ -keyout example.com.key -out example.com.crt

openssl req -out bookinfo.example.com.csr -newkey rsa:2048 -nodes -keyout bookinfo.example.com.key -subj “/CN=bookinfo.example.com/O=some organization”

openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 0 -in bookinfo.example.com.csr -out bookinfo.example.com.crt
```

2、创建secret
```
kubectl create -n istio-system secret generic bookinfo-credential --from-file=tls.key=bookinfo.example.com.key --from-file=tls.crt=bookinfo.example.com.crt --from-file=ca.crt=example.com.crt
```

3、创建gateway

1.7.0/gateway/tls/istio-mutual/gateway-istio-mutual.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: ISTIO_MUTUAL
      credentialName: "bookinfo-credential"
    hosts:
    - "*"
```

4、创建vs

1.7.0/virtaulservice/vs-bookinfo-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

5、访问
```
curl -v -HHost:bookinfo.example.com --resolve “bookinfo.example.com:39329:192.168.198.154” --cacert example.com.crt “https://bookinfo.example.com:39329/productpage”
```

## credentialName

1、创建secret
```
cd 1.7.0/gateway/certs

kubectl create -n istio-system secret tls bookinfo-secret --key ./cert.key --cert=./cert.crt
```

2、创建gateway
```
kubectl apply -f gateway-credentialName.yaml -n istio
```

1.7.0/gateway/tls/gateway-credentialName.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "*"
    tls:
      credentialName: bookinfo-secret
      mode: SIMPLE
```

3、·创建vs

1.7.0/virtaulservice/vs-bookinfo-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

4、访问 https://bookinfo.demo:39329/productpage

## caCertificates

1生成证书
```
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -subj ‘/O=example Inc./CN=example.com’ -keyout example.com.key -out example.com.crt

openssl req -out bookinfo.example.com.csr -newkey rsa:2048 -nodes -keyout bookinfo.example.com.key -subj “/CN=bookinfo.example.com/O=some organization”

openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 0 -in bookinfo.example.com.csr -out bookinfo.example.com.crt
```

2、创建secret
```
kubectl create -n istio-system secret generic istio-ingressgateway-certs --from-file=tls.key=bookinfo.example.com.key --from-file=tls.crt=bookinfo.example.com.crt --from-file=ca.crt=example.com.crt
```

检查配置是否生效：
```
kubectl exec deploy/istio-ingressgateway -n istio-system – ls /etc/istio/ingressgateway-certs
```

3、创建gateway

1.7.0/gateway/tls/gateway-caCertificates.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "*"
    tls:
      mode: MUTUAL
      caCertificates: /etc/istio/ingressgateway-certs/ca.crt
      serverCertificate: /etc/istio/ingressgateway-certs/tls.crt
      privateKey: /etc/istio/ingressgateway-certs/tls.key
```

4、创建vs

1.7.0/virtaulservice/vs-bookinfo-hosts-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - bookinfo-gateway
  http:
  - match:
    - uri:
        exact: /productpage
    - uri:
        prefix: /static
    - uri:
        exact: /login
    - uri:
        exact: /logout
    - uri:
        prefix: /api/v1/products
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

5、生成客户端证书
```
openssl req -out client.example.com.csr -newkey rsa:2048 -nodes -keyout client.example.com.key -subj “/CN=client.example.com/O=client organization”

openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 1 -in client.example.com.csr -out client.example.com.crt
```

6、访问
```
curl -v -HHost:bookinfo.example.com --resolve “bookinfo.example.com:39329:192.168.198.154” --cacert example.com.crt --cert client.example.com.crt --key client.example.com.key “https://bookinfo.example.com:39329/productpage”
```

## cipherSuites

部署gateway

1.7.0/gateway/tls/gateway-cipherSuites.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "bookinfo.demo"
    - "ratings.demo"
    - "nginx.example.com"
    tls:
      mode: SIMPLE
      cipherSuites: 
      - ECDHE-RSA-AES256-GCM-SHA384
      - ECDHE-RSA-AES128-GCM-SHA256
      credentialName: bookinfo-secret
```

## minProtocolVersion maxProtocolVersion

| Name | Description |
|-------|-------------|
| TLS_AUTO | 自动选择DLS版本 |
| TLSV1_0 | TLS 1.0 |
| TLSV1_1 | TLS 1.1 |
| TLSV1_2 | TLS 1.2 |
| TLSV1_3 | TLS 1.3 |

## TLS_AUTO

1.7.0/gateway/tls/protocolVersion/gateway-tls-version-tls_auto.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "*"
    tls:
      credentialName: bookinfo-secret
      mode: SIMPLE
      minProtocolVersion: TLS_AUTO
      maxProtocolVersion: TLS_AUTO
```

## TLSV1_0

1.7.0/gateway/tls/protocolVersion/gateway-tls-version-tlsv1_0.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "*"
    tls:
      credentialName: bookinfo-secret
      mode: SIMPLE
      minProtocolVersion: TLSV1_0
      maxProtocolVersion: TLSV1_0
```

## TLSV1_0 - TLSV1_3
```
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: bookinfo-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    hosts:
    - "*"
    tls:
      credentialName: bookinfo-secret
      mode: SIMPLE
      minProtocolVersion: TLSV1_0
      maxProtocolVersion: TLSV1_3
```

## subjectAltNames

gRPC config for type.googleapis.com/envoy.config.listener.v3.Listener rejected: Error adding/updating listener(s) 0.0.0.0_8443: SAN-based verification of peer certificates without trusted CA is insecure and not allowed
