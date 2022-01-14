描述: 最近将部分业务通过Ingress进行发布管理, 从而实现应用灰蓝发布、金丝雀发布，更贴近当下自动化运维技术的发展，并为了进行实现七层自定义负载转发, 将不同应用程序配置到指定业务域名下不同的目录，并减少业务管理复杂化，同时节约域名资源，即多个业务可以通过一个域名出去提供服务。

但是在实际环境中却发现一个小问题，在通过ingress-nginx访问后端应用时，无法无法获取真实的客户端IP，经过一天的资料查找与实践，最终将该问题进行解决，下面将记一波解决思路流程和配置实践。

环境说明

访问流程: 客户端 -> 边界防火墙 -> A10（硬件）负载均衡 -> Ingrees-Nginx -> statefulsets.apps (应用配置、扩容及其生命管理) -> Pod (应用程序)

A10 负载均衡: 在硬件负载均衡上设置该业务域名的SSL，即实现外网访问https->转内网->http

ingress-nginx: 由helm部署的ingress，名称空间 kube-base

ingress-nginx-controller:
```
# （1）自定义ingress管理域名后端映射配置
$ kubectl get ingress -n app cq***-app
  # NAME        CLASS           HOSTS          ADDRESS       PORTS   AGE
  # cq***-app   ingress-nginx   app.cq***.cn   11.20.7.61   80      41d
# 关键配置
spec:
  ingressClassName: ingress-nginx
  rules:
  - host: app.cq***.cn
    http:
      paths:
      - backend:
          service:
            name: app-shangbao
            port:
              number: 80
        path: /shangbao/
        pathType: ImplementationSpecific

# （2）ingress-nginx-controller 控制器 services 服务查看
$ kubectl get svc -n kube-base ingress-nginx-controller
  # NAME                       TYPE       CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
  # ingress-nginx-controller   NodePort   11.20.7.61   <none>        80:30080/TCP,443:30443/TCP   332d
$ kubectl get svc -n kube-base ingress-nginx-controller
apiVersion: v1
kind: Service
metadata:
  annotations:
    k8s.kuboard.cn/workload: ingress-nginx-controller
    meta.helm.sh/release-name: ingress-nginx
    meta.helm.sh/release-namespace: kube-base
  creationTimestamp: "2021-02-15T04:57:22Z"
  labels:
    app.kubernetes.io/component: controller
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/name: ingress-nginx
  name: ingress-nginx-controller
  namespace: kube-base
  resourceVersion: "82785800"
  uid: 79ac32ad-82a6-4a77-b5ad-71d30ebb07c5
spec:
  clusterIP: 11.20.7.61
  clusterIPs:
  - 11.20.7.61
  externalTrafficPolicy: Cluster
  ports:
  - name: http
    nodePort: 30080
    port: 80
    protocol: TCP
    targetPort: 80
  - name: https
    nodePort: 30443
    port: 443
    protocol: TCP
    targetPort: 443
  selector:
    app.kubernetes.io/component: controller
    app.kubernetes.io/instance: ingress-nginx
    app.kubernetes.io/name: ingress-nginx
  sessionAffinity: None
  type: NodePort
status:
  loadBalancer: {}
```

- Step 01.通过业务后端日志发现获取的地址为K8S的master节点地址，而非真实的IP地址
```
# 日志
2022-01-13 09:59:19.365 [http-nio-80-exec-10] INFO  com.******.aop.AspectHandler-Access of com.******.controller.PageController.toPage?index  [IP]10.41.40.26,10.41.40.26,172.20.170.128,
2022-01-13 09:59:19.367 [http-nio-80-exec-10] INFO  com.******.aop.AspectHandler-Return of com.******.controller.PageController.toPage:shangbao/index  [IP]10.41.40.26,10.41.40.26,172.20.170.128,

# 程序中获取真实IP地址的请求头几种Header.
String ip0 = request.getHeader("X-Real-IP");
String ip1 = request.getHeader("X_FORWARDED_FOR");
String ip2 = request.getHeader("X-Forwarded-For");
String ip3 = request.getHeader("Proxy-Client-IP");
String ip4 = request.getHeader("WL-Proxy-Client-IP");
String ip5 = request.getHeader("HTTP_CLIENT_IP");
String ip6 = request.getHeader("HTTP_X_FORWARDED_FOR");
String ip7 = request.getRemoteAddr();
```

- step 02.通过抓取A10负载均衡流量及其A10访问ingress-nginx的流量，发现硬件负载均衡真实IP带入记录的Header字段是 X_FORWARDED_FOR.

- Step 03.想要Ingress-Nginx传递自定义的X_FORWARDED_FOR字段,我们需要在 ingress-nginx 配置字典中加入如下配置.
```
# 配置 ingress-nginx 字典更改后会自动更新进ingress-nginx的POD中/etc/nginx/nginx.conf的文件里。
$ kubectl get cm -n kube-base ingress-nginx-controller -o yaml

$ kubectl edit cm -n kube-base ingress-nginx-controller
apiVersion: v1
  data:
    enable-underscores-in-headers: "true"
    use-forwarded-headers: "true"
    forwarded-for-header: X_FORWARDED_FOR
    compute-full-forwarded-for: "true"
    proxy-real-ip-cidr: 192.168.4.11,192.168.10.11
```
参数解析:
- enable-underscores-in-headers: 是否在标题名称中启用下划线, 缺省默认为off，表示如果请求中header name 中包含下划线，则忽略掉不会传递到后端代理或者应用程序，即获取不到该Header，所以此处为了不丢弃A10传递过来的 X_FORWARDED_FOR Header 需要将该参数设置为True。
- use-forwarded-headers: 如果设置为True时，则将设定的X-Forwarded-* Header传递给后端, 当Ingress在L7 代理/负载均衡器之后使用此选项。如果设置为 false 时，则会忽略传入的X-Forwarded-*Header, 当 Ingress 直接暴露在互联网或者 L3/数据包的负载均衡器后面,并且不会更改数据包中的源 IP请使用此选项。
- forwarded-for-header: 设置用于标识客户端的原始 IP 地址的 Header 字段。默认值X-Forwarded-For，此处由于A10带入的是自定义记录IP的Header,所以此处填入是X_FORWARDED_FOR.
- compute-full-forwarded-for: 将 remote address 附加到 X-Forwarded-For Header而不是替换它。当启用此选项后端应用程序负责根据自己的受信任代理列表排除并提取客户端 IP。
- proxy-real-ip-cidr: 如果启用 use-forwarded-headers 或 use-proxy-protocol，则可以使用该参数其定义了外部负载衡器 、网络代理、CDN等地址，多个地址可以以逗号分隔的 CIDR 。默认值: "0.0.0.0/0"

***Tips: 为了统一可移植性，在程序设置或者硬件负载转发中，转发、设置的 header 里不建议采用"_"下划线,可以用驼峰命名或者其他的符号(如减号-)进行代替上述的X_FORWARDED_FOR字段把我是坑得，欲哭无泪。***

管理配置负载均衡的那位小哥也是位人才，这样设置是为了防止X-Forwarded-For伪造来源IP，效果还是很Nice的，但是还是建议不要用下划线连接。

上述参数配置后在ingress-nginx-control中的/etc/nginx/nginx.conf结果如下:
```
# use-forwarded-headers 参数设置后
real_ip_header      X_FORWARDED_FOR;
real_ip_recursive   on;
set_real_ip_from    192.168.10.11;
set_real_ip_from    192.168.4.11;

# We can't use $proxy_add_x_forwarded_for because the realip module replaces the remote_addr too soon
# 我们不能使用 `$proxy_add_x_forwarded_for`, 因为 realip 模块过早地替换了远程 remote_addr。
map $http_x_forwarded_for $full_x_forwarded_for {
  default          "$http_x_forwarded_for, $realip_remote_addr";
  ''               "$realip_remote_addr";
}
```

- Step 04.为了在后端演示ingress-nginx传递过来的参数, 创建一个nginx应用在log_format参数设置如下"$http_X_FORWARDED_FOR" - "$http_X_Real_IP"'
```
# /etc/nginx/nginx.conf
log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
  '$status $body_bytes_sent "$http_referer" '
  '"$http_user_agent" "$http_x_forwarded_for" - "$http_X_FORWARDED_FOR" - "$http_X_Real_IP"';
# 输出结果 "10.41.40.22" -- "10.41.40.22" --  "10.20.172.103"  

proxy_set_header X-Real-IP              $remote_addr;   # realip 模块 已经将 X_FORWARDED_FOR 字段赋值给 $remote_addr, 所以该字段也记录了真实IP.
proxy_set_header X-Forwarded-For        $full_x_forwarded_for;
```

- Step 05.在应 Pod 中进行利用tcpdump抓包，日志记录真实IP和效果如下所示:
```
$ kubectl exec -it -n app shangbao-text sh
# tcpdump -nnX port 80 -vv -w test.pcap 

# 日志效果:
2022-01-13 22:31:00.178  INFO 1 --- [p-nio-80-exec-4] com.******.aop.AspectHandler: Access of com.******.controller.PageController.toPage?index  [IP]183.222.192.169,183.222.192.169,10.41.40.21,172.20.35.192,
2022-01-13 22:31:00.180  INFO 1 --- [p-nio-80-exec-4] com.******.aop.AspectHandler: Return of com.******.controller.PageController.toPage:shangbao/index  [IP]183.222.192.169,183.222.192.169,10.41.40.21,172.20.35.192,
```

官方文档地址: https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#proxy-real-ip-cidr

至此完毕！


