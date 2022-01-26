# 一、什么是virtualService

`VirtualService`中文名称虚拟服务，是istio中一个重要的资源， 它定义了一系列针对指定服务的流量路由规则。每个路由规则都针对特定协议的匹配规则。如果流量符合这些特征，就会根据规则发送到服务注册表中的目标服务（或者目标服务的子集或版本）。

# 二、vs和k8s service的区别

如果没有 Istio virtual service，仅仅使用 k8s service 的话，那么只能实现最基本的流量负载均衡转发，但是就不能实现类似按百分比来分配流量等更加复杂、丰富、细粒度的流量控制了。

备注：虚拟服务相当于 K8s 服务的 sidecar，在原本 K8s 服务的功能之上，提供了更加丰富的路由控制。

例子：
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: test-virtual-svc
spec:
  hosts:
  - "web-svc"
  http:
  - route:
    - destination:
        host: web-svc
        subset: nginx
      weight: 25
    - destination:
        host: web-svc
        subset: tomcat
      weight: 75
```

# 三、配置详解

## exportTo

1、只在当前名称空间有效

virtaulservice/vs-bookinfo-dot.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - .
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

2、所有名称空间有效

virtaulservice/vs-bookinfo-star.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
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

3、特定名称空间有效

virtaulservice/vs-bookinfo-istio-system.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
 # - "default"
 # - "istio"
  - "istio-system"
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

## gateways

Gateway 名称列表，Sidecar 会据此使用路由。VirtualService 对象可以用于网格中的 Sidecar，也可以用于一个或多个 Gateway。这里公开的选择条件可以在协议相关的路由过滤条件中进行覆盖。保留字 mesh 用来指代网格中的所有 Sidecar。当这一字段被省略时，就会使用缺省值（mesh），也就是针对网格中的所有 Sidecar 生效。如果提供了 gateways 字段，这一规则就只会应用到声明的 Gateway 之中。要让规则同时对 Gateway 和网格内服务生效，需要显式的将 mesh 加入 gateways 列表。

1、单个gateway

virtaulservice/vs-bookinfo-gw-single.yaml
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

2、多个gateway

virtaulservice/vs-bookinfo-multi-gw.yaml
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
  - bookinfo-gateway-02
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

3、不同名称空间下的gateway

virtaulservice/vs-bookinfo-gw-namespace.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "*"
  gateways:
  - default/bookinfo-gateway
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

4、省略gateways默认为mesh

virtaulservice/vs-review-v2.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v2
```

5、gateways为mesh

virtaulservice/vs-review-mesh.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  gateways:
  - mesh
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v3
```

## hosts

必要字段：流量的目标主机。可以是带有通配符前缀的 DNS 名称，也可以是 IP 地址。根据所在平台情况，还可能使用短名称来代替 FQDN。这种场景下，短名称到 FQDN 的具体转换过程是要靠下层平台完成的。**一个主机名只能在一个 VirtualService 中定义。** 同一个`VirtualService`中可以用于控制多个 HTTP 和 TCP 端口的流量属性。 Kubernetes 用户注意：当使用服务的短名称时（例如使用 reviews，而不是 reviews.default.svc.cluster.local），Istio 会根据规则所在的命名空间来处理这一名称，而非服务所在的命名空间。假设 “default” 命名空间的一条规则中包含了一个 reviews 的 host引用，就会被视为 reviews.default.svc.cluster.local，而不会考虑 reviews 服务所在的命名空间。**为了避免可能的错误配置，建议使用 FQDN 来进行服务引用。** hosts 字段对 HTTP 和 TCP 服务都是有效的。网格中的服务也就是在服务注册表中注册的服务，必须使用他们的注册名进行引用；只有 Gateway 定义的服务才可以使用 IP 地址。

1、ip

virtaulservice/vs-bookinfo-hosts-ip.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "192.168.198.155"
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

2、多个hosts

virtaulservice/vs-bookinfo-hosts-multi.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "bookinfo.com"
  - "bookinfo.demo"
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

3、匹配所有域名

virtaulservice/vs-bookinfo-hosts-star.yaml
```
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

4、短fqdn

virtaulservice/vs-bookinfo-hosts-fqdn-short.yaml

在default名称空间创建vs
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "bookinfo"
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

同时要创建一个同名service
```
[root@master01 virtaulservice]# cat bookinfo-svc.yaml 
apiVersion: v1
kind: Service
metadata:
  name: bookinfo
  labels:
    app: productpage
    service: productpage
spec:
  ports:
  - port: 9080
    name: http
  selector:
    app: productpage
```

5、长fqdn

virtaulservice/vs-bookinfo-hosts-fqdn-long.yaml

在default名称空间创建vs
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  hosts:
  - "bookinfo.default.svc.cluster.local"
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


同时在default名称空间创建bookinfo svc

virtaulservice/bookinfo-svc.yaml
```
apiVersion: v1
kind: Service
metadata:
  name: bookinfo
  labels:
    app: productpage
    service: productpage
spec:
  ports:
  - port: 9080
    name: http
  selector:
    app: productpage
```

## http

HTTP 流量规则的有序列表。这个列表对名称前缀为 http-、http2-、grpc- 的服务端口，或者协议为 HTTP、HTTP2、GRPC 以及终结的 TLS，另外还有使用 HTTP、HTTP2 以及 GRPC 协议的 ServiceEntry 都是有效的。进入流量会使用匹配到的第一条规则。

### 1）corsPolicy

cors介绍 https://blog.csdn.net/java_green_hand0909/article/details/78740765

1、配置httpd服务
```
[root@master01 html]# cat index.html 
<html>
<head><title></title></head>
<body>
<script type="text/javascript" src="https://code.jquery.com/jquery-3.2.1.min.js"></script>  
<script>
$(function(){
        $("#cors").click(
                function(){
                        $.ajax({
                                type:"get",
                                dataType : "html",
                                url:"http://bookinfo.demo:27941/productpage",
                                success:function(data){
                                        alert(data);
                                }
                        })
                });

        $("#cors2").click(
                function(){
                        $.ajax({
                                type:"get",
                                dataType : "json",
                                url:"http://bookinfo.demo:27941/reviews/1",
                                contentType : 'application/json;charset=UTF-8',
                                success:function(data){
                                        var jsonStr = JSON.stringify(data);
                                        alert(jsonStr);
                                }
                        })
                });
          $("#cors3").click(
                function(){
                        $.ajax({
                                type:"delete",
                                contentType : 'application/json;charset=UTF-8',
                                dataType : "json",
                                url:"http://bookinfo.demo:27941/reviews/1",
                                success:function(data){
                                        var jsonStr = JSON.stringify(data);
                                        alert(jsonStr);
                                }
                        })
                });
           $("#cors4").click(
                function(){
                        $.ajax({
                                type:"get",
                                contentType : 'application/json;charset=UTF-8',
                                dataType : "json",
                                headers:{"X-Custom-Header":"value"},
                                url:"http://bookinfo.demo:27941/reviews/1",
                                success:function(data){
                                        var jsonStr = JSON.stringify(data);
                                        alert(jsonStr);
                                }
                        })
                });
         
});

</script>
<input type="button" id="cors" value="简单请求"/>
<input type="button" id="cors2" value="非简单请求"/>
<input type="button" id="cors3" value="非简单请求delete"/>
<input type="button" id="cors4" value="非简单请求headers"/>
</body>
</html>
```
注意替换端口 url:“http://bookinfo.demo:27941/productpage”,

2、启动nginx
```
systemctl start httpd
```

3、简单请求，配置cors

virtaulservice/corsPolicy/vs-productpage-cors.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    corsPolicy:
      allowOrigins:
      - exact: "http://mytest.com:8081"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

4、访问：

http://mytest.com:8081/

5、简单请求allowCredentials

virtaulservice/corsPolicy/vs-productpage-cors-allowCredentials.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    corsPolicy:
      allowCredentials: true
      allowOrigins:
      - exact: "http://mytest.com:8081"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

6、简单请求allowOrigins prefix

virtaulservice/corsPolicy/vs-productpage-cors-allowOrigins-prefix.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    corsPolicy:
      allowOrigins:
      - prefix: "http://mytest"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

7、简单请求allowOrigins regex

virtaulservice/corsPolicy/vs-productpage-cors-allowOrigins-regex.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    corsPolicy:
      allowOrigins:
      - regex: ".*"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

8、简单请求exposeHeaders

virtaulservice/corsPolicy/vs-productpage-cors-exposeHeaders.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    corsPolicy:
      allowOrigins:
      - exact: "http://mytest.com:8081"
      exposeHeaders: 
      - test
      - test2
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

9、非简单请求

virtaulservice/corsPolicy/vs-reviews-cors.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookreviews
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        prefix: /reviews
    corsPolicy:
      allowOrigins:
      - exact: "http://mytest.com:8081"
      allowMethods:
      - GET
      - OPTIONS
      maxAge: "1m"
    route:
    - destination:
        host: reviews
        port:
          number: 9080
```

10、非简单请求allowMethods

virtaulservice/corsPolicy/vs-reviews-cors-allowMethods.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookreviews
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        prefix: /reviews
    corsPolicy:
      allowOrigins:
      - exact: "http://mytest.com:8081"
      allowMethods:
      - POST
      - OPTIONS
      maxAge: "1m"
    route:
    - destination:
        host: reviews
        port:
          number: 9080
```

11、非简单请求allowHeaders

virtaulservice/corsPolicy/vs-reviews-cors-allowHeaders.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookreviews
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        prefix: /reviews
    corsPolicy:
      allowOrigins:
      - exact: "http://mytest.com:8081"
      allowMethods:
      - GET
      - OPTIONS
      maxAge: "1m"
      allowHeaders:
      - X-Custom-Header
      - content-type
    route:
    - destination:
        host: reviews
        port:
          number: 9080
```

12、非简单请求maxAge

virtaulservice/corsPolicy/vs-reviews-cors-maxAge.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookreviews
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        prefix: /reviews
    corsPolicy:
      allowOrigins:
      - exact: "http://mytest.com:8081"
      allowMethods:
      - GET
      - OPTIONS
      maxAge: "10s"
      #maxAge: "1m"
      #maxAge: "1h"
    route:
    - destination:
        host: reviews
        port:
          number: 9080
```

### 2）delegate

1、向istiod容器设置环境变量
```
PILOT_ENABLE_VIRTUAL_SERVICE_DELEGATE=true
kubectl set env deploy istiod -n istio-system --list
kubectl set env deploy istiod -n istio-system PILOT_ENABLE_VIRTUAL_SERVICE_DELEGATE=true
```

2、配置文件

virtaulservice/delegate/vs-delegate.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    delegate:
      name: productpage
      namespace: istio
  - match:
    - uri:
        prefix: /reviews
    delegate:
      name: reviews
      namespace: istio
```

vs productpage

virtaulservice/delegate/vs-productpage.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: productpage
spec:
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

访问url

http://bookinfo.com:30986/productpage

http://bookinfo.com:30986/reviews/1

### 3）fault 故障注入

1、abort 错误注入
```
# cat virtaulservice/fault/vs-productpage-fault-abort.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
  namespace: istio
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - fault:
      abort:
        httpStatus: 500
        percentage:
          value: 100
    match:
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
        host: productpage
        subset: v1
```

2、http2 abort
```
# cat virtaulservice/fault/vs-productpage-fault-abort-http2Error.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
  namespace: istio
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - fault:
      abort:
        #grpcStatus: "test"
        http2Error: "test"
        #httpStatus: 500
        percentage:
          value: 100
    match:
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
        host: productpage
        subset: v1
```
- HTTP/2 abort fault injection not supported yet 目前不支持http2

3、delay 延时注入
```
# cat virtaulservice/fault/vs-productpage-fault-delay.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
  namespace: istio
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - fault:
      delay:
        percentage:
          value: 100.0
        fixedDelay: 7s
    match:
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
        host: productpage
        subset: v1
```

exponentialDelay
```
# cat virtaulservice/fault/vs-productpage-fault-delay-exponentialDelay.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
  namespace: istio
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - fault:
      delay:
        percentage:
          value: 100.0
        exponentialDelay: 7s
    match:
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
        host: productpage
        subset: v1
```
- exponentialDelay not supported yet 目前不支持

### 4）headers

#### request

1、add

virtaulservice/headers/vs-headers-request-add.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    headers:
      request:
        add:
          TEST_REQUEST_HEADER: XX
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、remove

virtaulservice/headers/vs-headers-request-remove.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    headers:
      request:
        remove:
        - TEST_REQUEST_HEADER
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

3、set

virtaulservice/headers/vs-headers-request-set.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    headers:
      request:
        set:
          TEST_REQUEST_HEADER: XX
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

#### response

1、add

virtaulservice/headers/vs-headers-response-add.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    headers:
      response:
        add:
          TEST_REQUEST_HEADER: XX
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、remove

virtaulservice/headers/vs-headers-response-remove.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    headers:
      response:
        remove:
        - x-envoy-upstream-service-time
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```


3、set

virtaulservice/headers/vs-headers-response-set.yaml

没有就添加，有就修改
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
    headers:
      response:
        set:
          content-type: "text/html"
          Test: "test"
          x-envoy-upstream-service-time: "1111111111"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

## 5)match 匹配规则

### authority

1、exact
```
# cat virtaulservice/match/vs-match-authority-exact.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - authority:
        exact: "bookinfo.demo:27941"                          # 匹配域名加端口
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、prefix
```
# cat virtaulservice/match/vs-match-authority-prefix.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - authority:
        prefix: "bookinfo"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

3、regex
```
# cat virtaulservice/match/vs-match-authority-regex.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - authority:
        regex: "bookinfo.de.*"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### gateways
```
# cat virtaulservice/match/vs-match-gateways.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  - bookinfo-gateway-02
  hosts:
  - '*'
  http:
  - match:
    - uri:
        exact: /productpage
      gateways:
      - bookinfo-gateway-02
    - uri:
        prefix: /static
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### headers

1、exact
```
# cat virtaulservice/match/vs-match-header-exact.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          exact: mark
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v3
```

2、prefix

virtaulservice/match/vs-match-headers-prefix.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          prefix: ma
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v3
```

3、regex

virtaulservice/match/vs-match-headers-regex.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          regex: "m.*k"
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v3
```

4、cookie
```
# cat virtaulservice/match/vs-match-header-cookie-bookinfo.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - headers:
        cookie:
          regex: "^(.*?;)?(session=.*)(;.*)?$"
  - route:
    - destination:
        host: productpage
        port:
          number: 9080
```

5、user-agent

header user-agent例子

safari 5.1 - MAC
- User-Agent:Mozilla/5.0 (Macintosh; U；Intel Mac OS X 10_6_8;en-us) AppleWebKit/534.50(KHTML, like Gecko) Version/5.1 Safari/534.50

safari 5.1 - Windows
- User-Agent:Mozilla/5.0 (Windows; U；Windows NT 6.1;en-us) AppleWebKit/534.50(KHTML, like Gecko) Version/5.1 Safari/534.50

IE 9.0
- User-Agent:Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)

IE 8.0
- User-Agent:Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident4.0)

IE 7.0
- User-Agent:Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)

IE 7.0
- User-Agent:Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)

```
# cat virtaulservice/match/vs-match-headers-user-agent.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - headers:
        user-agent:
          regex: ".*chrome"
  - route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### ignoreUriCase 忽略URI大小写

virtaulservice/match/vs-match-ignoreUriCase.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        exact: "/PRODUCTPAGE"
      ignoreUriCase: true
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### method

1、exact
```
# cat virtaulservice/match/vs-match-method-exact.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - method:
        exact: "GET"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、prefix
```
# cat virtaulservice/match/vs-match-method-prefix.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - method:
        prefix: "G"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

3、regex
```
# cat virtaulservice/match/vs-match-method-regex.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - method:
        regex: "G.*T"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### name 名称标识，具体不起作用
```
# cat virtaulservice/match/vs-match-name.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        exact: /productpage
      name: book
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### port
```
# cat virtaulservice/match/vs-match-port.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - port: 80
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### queryParams 查询参数

1、exact
```
# cat virtaulservice/match/vs-match-queryParams-exact.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - queryParams:
        test:
          exact: test
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、prefix
```
# cat virtaulservice/match/vs-match-queryParams-prefix.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - queryParams:
        test:
          prefix: test
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```
不起作用，只要有queryParams为test就能访问

3、regex
```
# cat virtaulservice/match/vs-match-queryParams-regex.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - queryParams:
        test:
          regex: "\\d+$"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```
test值必须是数字

### scheme

1、exact
```
cat vs-match-scheme-exact.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - scheme:
        exact: "http"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、prefix
```
# cat vs-match-scheme-prefix.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - scheme:
        prefix: "http"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

3、regex
```
# cat vs-match-scheme-regex.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - scheme:
        regex: ".*"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### sourceLabels
```
# cat virtaulservice/match/vs-match-sourceLabels.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - sourceLabels:
        app: productpage
        version: v1
    route:
    - destination:
        host: reviews
        subset: v2
```

### sourceNamespace

virtaulservice/match/vs-match-sourceNamespace.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - sourceNamespace: istio-system
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### uri

1、exact
```
# cat virtaulservice/match/vs-match-uri-exact.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        exact: /productpage
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、prefix
```
# cat virtaulservice/match/vs-match-uri-prefix.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        prefix: /product
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

3、regex
```
# cat virtaulservice/match/vs-match-uri-regex.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        regex: "/p.*e"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

### withoutHeaders 无头匹配


1、exact
```
# cat vs-match-withoutHeaders-exact.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - withoutHeaders:
        end-user:
          exact: mark
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v3
```

```
curl http://bookinfo.demo:30986/productpage -H "end-user: mark" -I
curl http://bookinfo.demo:30986/productpage -H "end-user: hxp"
```
- 如果header不存在也是不匹配

2、prefix
```
# cat vs-match-withoutHeaders-prefix.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - withoutHeaders:
        end-user:
          prefix: ma
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v3
```

```
curl http://bookinfo.demo:30986/productpage -H "end-user: mark" -I
curl http://bookinfo.demo:30986/productpage -H "end-user: hxp"
```
- 如果header不存在也是不匹配

3、regex
```
# cat vs-match-withoutHeaders-regex.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - withoutHeaders:
        end-user:
          regex: "m.*k"
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v3
```

```
curl http://bookinfo.demo:30986/productpage -H "end-user: mark" -I
curl http://bookinfo.demo:30986/productpage -H "end-user: hxp"
```
- 如果header不存在也是不匹配

## mirror 流量镜像
```
# cat virtaulservice/mirror/vs-http-mirror.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
        host: productpage
        port:
          number: 9080
    mirror:
      host: productpage.istio-2.svc.cluster.local
      port: 
        number: 9080
    mirrorPercentage:
      value: 100
```

1、创建namespace
```
kubectl create ns istio-2
```

2、打标签
```
kubectl label ns istio-2 istio-injection=enabled
```

3、部署deployment
```
kubectl apply -f productpage-deploy.yaml -n istio-2
```

4、打开日志
```
kubectl logs -f productpage-v1-64794f5db4-ng9sn -n istio-2
```

5、创建资源
```
kubectl apply -f vs-http-mirror.yaml -n istio
```

6、访问url

http://192.168.198.154:27941/productpage

### subset

1、创建dr
```
kubectl apply -f dr-productpage.yaml -n istio-2
```

2、创建mirror资源
```
kubectl apply -f vs-http-mirror-subset.yaml -n istio
```

3、访问

http://192.168.198.154:27941/productpage

4、观察日志

## name 标识名称，不起作用

virtaulservice/vs-bookinfo-name.yaml
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
    name: bookinfo
    route:
    - destination:
        host: productpage.istio.svc.cluster.local
        port:
          number: 9080
```

## redirect 重定向

virtaulservice/redirect/vs-productpage-redirect.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        exact: /mypage
    redirect:
      uri: /productpage
      authority: 192.168.198.154:27941
      redirectCode: 308
  - match:
    - uri:
        prefix: /productpage
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
        host: productpage
        port:
```

访问：

http://192.168.198.154:27941/mypage

## retries 重试

- attempts：必选字段，定义重试的次数
- perTryTimeout：每次重试超时的时间，单位可以是ms、s、m和h
- retryOn：进行重试的条件，可以是多个条件，以逗号分隔

其中重试条件retryOn的取值可以包括以下几种。
- 5xx：在上游服务返回5xx应答码，或者在没有返回时重试
- gateway-error：类似于5xx异常，只对502、503和504应答码进行重试。
- connect-failure：在链接上游服务失败时重试 retriable-4xx：在上游服务返回可重试的4xx应答码时执行重试。
- refused-stream：在上游服务使用REFUSED_STREAM错误码重置时执行重试。
- cancelled：gRPC应答的Header中状态码是cancelled时执行重试。
- deadline-exceeded：在gRPC应答的Header中状态码是deadline-exceeded时执行重试
- internal：在gRPC应答的Header中状态码是internal时执行重试
- resource-exhausted：在gRPC应答的Header中状态码是resource-exhausted时执行重试
- unavailable：在gRPC应答的Header中状态码是unavailable时执行重试。

1、设置延迟错误
```
# cat virtaulservice/retry/vs-reviews.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v3
    fault:
      delay:
        percentage:
          value: 100.0
        fixedDelay: 7s
```

2、设置重试
```
# cat virtaulservice/retry/vs-bookinfo.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
        host: productpage
        subset: v1
    retries:
      attempts: 5
      perTryTimeout: 3s
      retryOn: 5xx,connect-failure
```

查看重试日志
```
kubectl logs -f productpage-v1-6b746f74dc-nb8sg -n istio
```

是否重试其他机子
```
# cat virtaulservice/retry/vs-bookinfo-retryRemoteLocalities.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
        host: productpage
        subset: v1
    retries:
      attempts: 5
      perTryTimeout: 3s
      retryOn: 5xx,connect-failure
      retryRemoteLocalities: true
```

## rewrite 重写

1、uri
```
# cat virtaulservice/rewrite/vs-http-rewrite.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        regex: "/m.*k"
    rewrite:
      uri: "/productpage"
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

2、authority
```
# cat virtaulservice/rewrite/vs-http-rewrite-authority.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
  http:
  - match:
    - uri:
        regex: "/m.*k"
    rewrite:
      uri: "/productpage"
      authority: bookinfo.com:27941
    route:
    - destination:
        host: productpage
        port:
          number: 9080
```

## route 路由

### destination

1、host
```
# cat virtaulservice/route/vs-reviews-host.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
  - route:
    - destination:
        host: reviews
```

2、port
```
# cat virtaulservice/route/vs-reviews-port.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
  - route:
    - destination:
        host: reviews
        port:
          number: 9080
```

3、subset
```
# cat virtaulservice/route/vs-reviews-subset.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
```

### headers

#### request

1、add
```
# cat virtaulservice/route/vs-reviews-headers-request-add.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      headers:
        request:
          add:
            test: test
```

2、remove
```
# cat virtaulservice/route/vs-reviews-headers-request-remove.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      headers:
        request:
          remove:
          - test
```

3、set
```
# cat virtaulservice/route/vs-reviews-headers-request-set.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      headers:
        request:
          set:
            test: test
```

#### response

1、add
```
# cat virtaulservice/route/vs-bookinfo-headers-response-add.yaml

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
      headers:
        response:
          add:
            test: test
```

2、remove
```
# cat virtaulservice/route/vs-bookinfo-headers-response-remove.yaml

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
      headers:
        response:
          remove:
          - x-envoy-upstream-service-time
```

3、set
```
# cat virtaulservice/route/vs-bookinfo-headers-response-set.yaml

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
      headers:
        response:
          set:
            content-type: "text/html"
            test: test
            x-envoy-upstream-service-time: "1111"
~
```

### weight 权重

virtaulservice/route/vs-reviews-weight.yaml
```
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
    - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 50
    - destination:
        host: reviews
        subset: v3
      weight: 50
```

## timeout 超时

virtaulservice/timeout/vs-http-timeout.yaml
```
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: bookinfo
spec:
  exportTo:
  - '*'
  gateways:
  - bookinfo-gateway
  hosts:
  - '*'
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
        host: productpage
        port:
          number: 9080
    timeout: 0.01s
```

## tls

一个有序列表，对应的是透传 TLS 和 HTTPS 流量。路由过程通常利用 ClientHello 消息中的 SNI 来完成。TLS 路由通常应用在 https-、tls- 前缀的平台服务端口，或者经 Gateway 透传的 HTTPS、TLS 协议端口，以及使用 HTTPS 或者 TLS 协议的 ServiceEntry 端口上。注意：没有关联 VirtualService 的 https- 或者 tls- 端口流量会被视为透传 TCP 流量。

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
# cat nginx-deploy.yaml

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
# cat virtaulservice/tls/gw-mode-passthrough.yaml

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

## match

1、sinHosts
```
# cat virtaulservice/tls/vs-nginx-sniHosts.yaml

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

访问url https://nginx.example.com:39329/

2、port
```
# cat virtaulservice/tls/vs-nginx-port.yaml

apiVersion: networking.istio.io/v1beta1
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
        subset: v1
```

访问url https://nginx.example.com:39329


3、gateways
```
# cat 1.7.0/virtaulservice/tls/vs-nginx-gateways.yaml

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
      gateways:
      - bookinfo-gateway
    route:
    - destination:
        host: my-nginx
        port:
          number: 443
        subset: v1
```

4、destinationSubnets 目标子集

只对mesh traffic有效， destinationSubnets为svc ip
```
openssh req -out nginx.example.com.csr -newkey rsa:2048 -nodes -keyout nginx.example.com.key -subj "/CN=my-nginx/O=some organization"

opensshl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 0 -in nginx.example.com.csr -out  nginx.example.com.crt
```

创建secret
```
kubectl create secret tls nginx-server-certs --key  nginx.example.com.key --cert  nginx.example.com.crt -n istio
```

部署v2
```
kubectl apply -f nginx-deploy-v2.yaml -n istio
kubectl exec -it -n istio my-nginx-57fb7765cb-nfxb7 -- /bin/bash
echo "nginx-01" > /usr/share/nginx/html/index.html

kubectl exec -it -n istio my-nginx-v2-78bdfbf89f-slcmx -- /bin/bash
echo "nginx-02" > /usr/share/nginx/html/index.html

kubectl cp certs/example.com.crt -n istio sleep-557747455f-p23hz:/tmp/
```

创建规则
```
dr-my-nginx-v1-v2.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-gninx
spec:
  hosts: my-nginx
  subsets:
  - name: v1
    labels:
      run: my-nginx
      version: v1
   - name: v12
    labels:
      run: my-nginx
      version: v2 
```

```
# cat 1.7.0/virtaulservice/tls/vs-nginx-destinationSubnets.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-nginx
spec:
  hosts:
  - my-nginx
  tls:
  - match:
    - port: 443
      sniHosts:
      - my-nginx
      destinationSubnets: 
      - 10.0.0.0/8
    route:
    - destination:
        host: my-nginx
        subset: v2
```

```
kubectl cp certs/example.com.crt -n istio sleep-557747455f-p24hz:/tmp/
kubectl exec -it -n istio sleep-557747455f-p24hz --/bin/sh

curl -v --cacert /tmp/example.com.crt "https://my-nginx"
```

5、sourceLabels
- 只对mesh traffic有效
```
# cat 1.7.0/virtaulservice/tls/vs-nginx-sourceLabels.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: nginx
spec:
  hosts:
  - my-nginx
  tls:
  - match:
    - port: 443
      sniHosts:
      - my-nginx
      sourceLabels:
        app: sleep
    route:
    - destination:
        host: my-nginx
        port:
          number: 443
        subset: v2
```

```
kubectl exec -it -n istio sleep-55747455f-p24hz --/bin/sh
curl -v --cacert /tmp/example.com.crt "https://my-nginx"
```

6、sourceNamespace
- 只对mesh traffic有效
```
1.7.0/virtaulservice/tls/vs-nginx-sourceNamespace.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: nginx
spec:
  hosts:
  - my-nginx
  tls:
  - match:
    - port: 443
      sniHosts:
      - my-nginx
      sourceNamespace: istio
    route:
    - destination:
        host: my-nginx
        port:
          number: 443
        subset: v1
```
```
kubectl exec -it -n istio sleep-55747455f-p24hz --/bin/sh
curl -v --cacert /tmp/example.com.crt "https://my-nginx"
```

## route
- 和http鸡巴一样

## tcp

一个针对透传 TCP 流量的有序路由列表。TCP 路由对所有 HTTP 和 TLS 之外的端口生效。进入流量会使用匹配到的第一条规则。

## match.port

1、部署deploy
```
kubectl apply -f tcp-echo-services.yaml -n istio
```

tcp-echo-services.yaml
```
apiVersion: v1
kind: Service
metadata:
  name: tcp-echo
  labels:
    app: tcp-echo
spec:
  ports:
  - name: tcp
    port: 9000
  - name: tcp-other
    port: 9001
  # Port 9002 is omitted intentionally for testing the pass through filter chain.
  selector:
    app: tcp-echo
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tcp-echo-v1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tcp-echo
      version: v1
  template:
    metadata:
      labels:
        app: tcp-echo
        version: v1
    spec:
      containers:
      - name: tcp-echo
        image: docker.io/istio/tcp-echo-server:1.2
        imagePullPolicy: IfNotPresent
        args: [ "9000,9001,9002", "one" ]
        ports:
        - containerPort: 9000
        - containerPort: 9001
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tcp-echo-v2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tcp-echo
      version: v2
  template:
    metadata:
      labels:
        app: tcp-echo
        version: v2
    spec:
      containers:
      - name: tcp-echo
        image: docker.io/istio/tcp-echo-server:1.2
        imagePullPolicy: IfNotPresent
        args: [ "9000,9001,9002", "two" ]
        ports:
        - containerPort: 9000
        - containerPort: 9001
```

2、添加service 端口
```
kubectl edit svc istio-ingressgateway -n istio-system

  - name: tcp
    port: 31400
    protocol: TCP
    targetPort: 31400
```


3、创建资源
```
kubectl apply -f tcp-echo-all-v1.yaml -n istio
```

tcp-echo-all-v1.yaml
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
---
apiVersion: networking.istio.io/v1alpha3
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

4、访问

telnet 192.168.198.154 37048

## destinationSubnets

virtaulservice/tcp/vs-destinationSubnets.yaml
```
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
    - destinationSubnets:
      - 172.20.2.0/24
    route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
        subset: v2
```

## sourceSubnet

virtaulservice/tcp/vs-sourceSubnet.yaml
```
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
    - sourceSubnet: 172.20.1.24
    route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
        subset: v2
```

## sourceLabels

virtaulservice/tcp/vs-sourceLabels.yaml
```
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
    - sourceLabels:
        app: istio-ingressgateway
    route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
        subset: v2
```

## sourceNamespace

virtaulservice/tcp/vs-sourceNamespace.yaml
```
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
    - sourceNamespace: istio-system
    route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
        subset: v2
```

## gateways

virtaulservice/tcp/vs-gateways.yaml
```
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
    - gateways:
      - tcp-echo-gateway
    route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
        subset: v2
```

## route.destination.host

virtaulservice/tcp/vs-route-host.yaml
```
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
  - route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
```

## port

virtaulservice/tcp/vs-route-port.yaml
```
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
  - route:
    - destination:
        host: tcp-echo
        port:
          number: 9000
```

## subset

virtaulservice/tcp/vs-route-subset.yaml
```
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
  - route:
    - destination:
        host: tcp-echo
        subset: v2
        port:
          number: 9000
```

## weight

virtaulservice/tcp/tcp-echo-20-v2.yaml
```
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
      weight: 80
    - destination:
        host: tcp-echo
        port:
          number: 9000
        subset: v2
      weight: 20
```

三种协议路由规则对比

VirtualService 在http、tls、tcp这三个字段上分别定义了应用于HTTP、TLS和TCP三种协议的路由规则。从规则构成上都是先定义一组匹配条件，然后对满足条件的的流量执行对应的操作。因为协议的内容不同，路由匹配条件不同，所以执行的操作也不同。如下表所示对比了三种路由规则。从各个维度来看，HTTP路由规则的内容最丰富，TCP路由规则的内容最少，这也符合协议分层的设计。

| 比较内容 | HTTP | TLS | TCP |
|-------- |------|-----|-----|
| 路由规则 | HTTPRoute | TLSRoute | TCPRoute |
| 流量匹配条件 | HTTPMatchRequest | TLSMatchAttributes | L4MatchAttribues |
| 条件属性 | uri、scheme、method、authority、port、sourceLabels、gateway | sniHosts、destinationSubnets、port、sourceLabels、gateway | destinationSubnets、port、sourceLabels、gateway |
| 流量操作 | route、redirect、rewirite、retry、timeout、faultlnjection、corsPolicy | Route | Route |
| 目标路由定义 | HTTPRouteDestination | RouteDestination | RouteDestination |
| 目标路由属性 | destination、weight、headers | destination、weight | destination、weight |
