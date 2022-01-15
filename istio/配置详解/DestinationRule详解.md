# 什么是DestinationRule

与VirtualService一样，DestinationRule也是 Istio 流量路由功能的关键部分。您可以将虚拟服务视为将流量如何路由到给定目标地址，然后使用目标规则来配置该目标的流量。在评估虚拟服务路由规则之后，目标规则将应用于流量的“真实”目标地址。

特别是，您可以使用目标规则来指定命名的服务子集，例如按版本为所有给定服务的实例分组。然后可以在虚拟服务的路由规则中使用这些服务子集来控制到服务不同实例的流量。

目标规则还允许您在调用整个目的地服务或特定服务子集时定制 Envoy 的流量策略，比如您喜欢的负载均衡模型、TLS 安全模式或熔断器设置。在目标规则参考中可以看到目标规则选项的完整列表。

# 资源详解

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| host | string | 必要字段。目标服务的名称。流量目标对应的服务，会在在平台的服务注册表（例如 Kubernetes 服务和 Consul 服务）以及 ServiceEntry 注册中进行查找，如果查找失败，则丢弃流量。Kubernetes 用户注意：当使用服务的短名称时（例如使用 reviews，而不是 reviews.default.svc.cluster.local），Istio 会根据规则所在的命名空间来处理这一名称，而非服务所在的命名空间。假设 default 命名空间的一条规则中包含了一个 reivews 的 host 引用，就会被视为 reviews.default.svc.cluster.local，而不会考虑 reviews 服务所在的命名空间。为了避免可能的错误配置，建议使用 FQDN 来进行服务引用。 | Yes |
| trafficPolicy | TrafficPolicy | 流量策略，包括负载均衡、连接池策略、异常点检查等 | No
| subsets | Subset[] | 是定义的一个服务的子集，经常用来定义一个服务版本，结合 VirtualService 使用 | No
| exportTo | string[] | 当前destination rule要导出的 namespace 列表。 应用于 service 的 destination rule 的解析发生在 namespace 层次结构的上下文中。 destination rule 的导出允许将其包含在其他 namespace 中的服务的解析层次结构中。 此功能为服务所有者和网格管理员提供了一种机制，用于控制跨 namespace 边界的 destination rule 的可见性 如果未指定任何 namespace，则默认情况下将 destination rule 导出到所有 namespace 值. 被保留，用于定义导出到 destination rule 被声明所在的相同 namespace 。类似的值*保留，用于定义导出到所有 namespaces NOTE：在当前版本中，exportTo值被限制为.或*（即， 当前namespace或所有namespace）| No |

## exportTo

1、名称空间

1.7.0/destinationrule/dr-productpage-exportto-namespace.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      exportTo:
      - 'istio-system'
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
```

2、当前名称空间

1.7.0/destinationrule/dr-productpage-exportto-dot.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      exportTo:
      - '.'
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
```

3、所有名称空间

1.7.0/destinationrule/dr-productpage-exportto-star.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      exportTo:
      - '*'
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
```

## host

- 短名称

1、部署vs

1.7.0/destinationrule/hosts/vs-details.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: VirtualService
    metadata:
      name: details
    spec:
      hosts:
      - details
      http:
      - route:
        - destination:
            host: details
```

2、部署dr

1.7.0/destinationrule/hosts/dr-details-hosts-short.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: details
    spec:
      host: details
```

- 长名称

1.7.0/destinationrule/hosts/dr-details-hosts-long.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: details
    spec:
      host: details.istio.svc.cluster.local
```

## trafficPolicy.connectionPool

连接池策略

tcp

tcp连接池设置

| Field | Type | Description | Required |
|-------|------|--------------|---------|
| maxConnections | int32 | Maximum number of HTTP1 /TCP connections to a destination host. Default 2^32-1. | No |
| connectTimeout | Duration | TCP connection timeout. | No |
| tcpKeepalive | TcpKeepalive | If set then set SO_KEEPALIVE on the socket to enable TCP Keepalives. | No |

TcpKeepalive

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| probes | uint32 | Maximum number of keepalive probes to send without response before deciding the connection is dead. Default is to use the OS level configuration (unless overridden, Linux defaults to 9.) | No |
| time | Duration | The time duration a connection needs to be idle before keep-alive probes start being sent. Default is to use the OS level configuration (unless overridden, Linux defaults to 7200s (ie 2 hours.) | No |
| interval | Duration | The time duration between keep-alive probes. Default is to use the OS level configuration (unless overridden, Linux defaults to 75s.) | No |

1.7.0/destinationrule/trafficPolicy/dr-productpage-connectionPool-tcp.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        connectionPool:
          tcp:
            maxConnections: 100
            connectTimeout: 30ms
            tcpKeepalive:
              time: 7200s
              interval: 75s
              probes: 10
```

## http

| Field | Type | Description | Required |
|-------|------|-------------|-----------|
| http1MaxPendingRequests | int32 | Maximum number of pending HTTP requests to a destination. Default 2^32-1. | No |
| http2MaxRequests | int32 | Maximum number of requests to a backend. Default 2^32-1. | No |
| maxRequestsPerConnection | int32 | Maximum number of requests per connection to a backend. Setting this parameter to 1 disables keep alive. Default 0, meaning “unlimited”, up to 2^29. | No |
| maxRetries | int32 | Maximum number of retries that can be outstanding to all hosts in a cluster at a given time. Defaults to 2^32-1. | No |
| idleTimeout | Duration | The idle timeout for upstream connection pool connections. The idle timeout is defined as the period in which there are no active requests. If not set, the default is 1 hour. When the idle timeout is reached the connection will be closed. Note that request based timeouts mean that HTTP/2 PINGs will not keep the connection alive. Applies to both HTTP1.1 and HTTP2 connections. | No |
| h2UpgradePolicy | H2UpgradePolicy | Specify if http1.1 connection should be upgraded to http2 for the associated destination. | No |

## h2UpgradePolicy

| Name | Description |
|------|--------------|
| DEFAULT | Use the global default. |
| DO_NOT_UPGRADE | Do not upgrade the connection to http2. This opt-out option overrides the default. |
| UPGRADE	Upgrade | the connection to http2. This opt-in option overrides the default. |

connectionPool-http.

1.7.0/destinationrule/trafficPolicy/dr-productpage-connectionPool-http.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        connectionPool:
          tcp:
            maxConnections: 10
            connectTimeout: 30ms
            tcpKeepalive:
              time: 7200s
              interval: 75s
              probes: 10
          http:
            http2MaxRequests: 10
            maxRequestsPerConnection: 1
            http1MaxPendingRequests: 1
            maxRetries: 1
            idleTimeout: 10s
            h2UpgradePolicy: DEFAULT
```

```
upstream connect error or disconnect/reset before headers. reset reason: overflow
```

destinationrule/trafficPolicy/dr-productpage-connectionPool-http-overflow.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        connectionPool:
          http:
            h2UpgradePolicy: DEFAULT
            http1MaxPendingRequests: 0
            http2MaxRequests: 1
            idleTimeout: 10s
            maxRequestsPerConnection: 1
            maxRetries: 1
          tcp:
            connectTimeout: 3ms
            maxConnections: 0
            tcpKeepalive:
              interval: 75s
              probes: 10
              time: 7200s
```

## h2UpgradePolicy

| Name | Description |
|------|-------------|
| DEFAULT | Use the global default. |
| DO_NOT_UPGRADE | Do not upgrade the connection to http2. This opt-out option overrides the default. |
| UPGRADE	Upgrade | the connection to http2. This opt-in option overrides the default. |

destinationrule/trafficPolicy/dr-productpage-h2UpgradePolicy-DEFAULT.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        connectionPool:
          http:
            h2UpgradePolicy: DEFAULT
```

```
kubectl logs --tail 10 -f -n istio productpage-v1-6b746f74dc-gvkpz -c istio-proxy
[2021-05-11T04:38:18.116Z] "GET /productpage HTTP/1.1" 200 - via_upstream - "-" 0 5183 149 148 "172.20.0.0" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36" "346116de-c68d-40a5-84fa-0fbe51635264" "192.168.198.154:31545" "127.0.0.1:9080" inbound|9080|| 127.0.0.1:36154 172.20.2.84:9080 172.20.0.0:0 outbound.9080._.productpage.istio.svc.cluster.local default
```

destinationrule/trafficPolicy/dr-productpage-h2UpgradePolicy-DO_NOT_UPGRADE.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        connectionPool:
          http:
            h2UpgradePolicy: DO_NOT_UPGRADE
```

```
[2021-05-11T04:39:15.100Z] "GET /productpage HTTP/1.1" 200 - via_upstream - "-" 0 5179 246 246 "172.20.0.0" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36" "5df1f8a7-ab0a-4b62-8505-e808130505d5" "192.168.198.154:31545" "127.0.0.1:9080" inbound|9080|| 127.0.0.1:36756 172.20.2.84:9080 172.20.0.0:0 outbound.9080._.productpage.istio.svc.cluster.local default
```

destinationrule/trafficPolicy/dr-productpage-h2UpgradePolicy-UPGRADE.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        connectionPool:
          http:
            h2UpgradePolicy: UPGRADE
```
```
[2021-05-11T04:36:08.846Z] "GET /productpage HTTP/2" 200 - via_upstream - "-" 0 5183 344 341 "172.20.0.0" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36" "2a53e429-0fee-4b49-9609-6ac24c886b96" "192.168.198.154:31545" "127.0.0.1:9080" inbound|9080|| 127.0.0.1:34824 172.20.2.84:9080 172.20.0.0:0 outbound.9080._.productpage.istio.svc.cluster.local default
```

## loadBalancer

负载均衡策略

consistentHash

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| httpHeaderName | string (oneof) | Hash based on a specific HTTP header. | Yes |
| httpCookie | HTTPCookie (oneof) | Hash based on HTTP cookie. | Yes |
| useSourceIp | bool (oneof) | Hash based on the source IP address. | Yes |
| minimumRingSize | uint64 | The minimum number of virtual nodes to use for the hash ring. Defaults to 1024. Larger ring sizes result in more granular load distributions. If the number of hosts in the load balancing pool is larger than the ring size, each host will be assigned a single virtual node. | No |

httpCookie

| Field | Type | Description | Required |
|-------|------|-------------|-----------|
| name | string | Name of the cookie. | Yes |
| path | string | Path to set for the cookie. | No |
| ttl | Duration | Lifetime of the cookie. | Yes |

1.7.0/destinationrule/trafficPolicy/loadBalancer/consistentHash/dr-productpage-loadBalancer-consistentHash-httpCookie.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          consistentHash:         
            httpCookie:
              name: user
              ttl: 0s
```

1、增加pod
```
kubectl scale deploy productpage-v1 --replicas=2 -n istio
```

2、打开日志
```
kubectl logs -f productpage-v1-6b746f74dc-988hj -n istio

kubectl logs --tail 1 -f productpage-v1-6b746f74dc-nb8sg -n istio
```

3、添加规则
```
kubectl apply -f dr-productpage-loadBalancer-consistentHash-httpCookie.yaml -n isito
```

4、访问浏览器

http://bookinfo.demo:nodeport/productpage

打开cookie console

5、查看日志

6、删除cookie，再次请求

7、查看日志

## httpHeaderName

1.7.0/destinationrule/trafficPolicy/loadBalancer/consistentHash/dr-details-httpHeaderName.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: details
    spec:
      host: details.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          consistentHash:
            httpHeaderName: end-user
```

1、增加pod
```
kubectl scale deploy details-v1 --replicas=2 -n istio
```

2、log 日志
```
kubectl logs details-v1-79f774bdb9-dmrnw -n istio -f

kubectl logs -f details-v1-79f774bdb9-wqz6j -n istio
```

3、浏览网页

登入productpage

4、查看日志

5、更改登入名称

6、查看日志

## useSourceIp

1.7.0/destinationrule/trafficPolicy/loadBalancer/consistentHash/dr-productpage-useSourceIp.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          consistentHash:
            useSourceIp: true
    ~
```

## httpQueryParameterName

1.7.0/destinationrule/trafficPolicy/loadBalancer/consistentHash/dr-productpage-httpQueryParameterName.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          consistentHash:
            httpQueryParameterName: test
```

## minimumRingSize

哈希环中最小虚拟节点数

1.7.0/destinationrule/trafficPolicy/loadBalancer/consistentHash/dr-productpage-minimumRingSize.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          consistentHash:
            minimumRingSize: 100
            httpQueryParameterName: test
```

localityLbSetting

| Field | Type | Description | Required |
| distribute | Distribute[] | Optional: only one of distribute or failover can be set. Explicitly specify loadbalancing weight across different zones and geographical locations. Refer to Locality weighted load balancing If empty, the locality weight is set according to the endpoints number within it. | No |
| failover | Failover[] | Optional: only failover or distribute can be set. Explicitly specify the region traffic will land on when endpoints in local region becomes unhealthy. Should be used together with OutlierDetection to detect unhealthy endpoints. Note: if no OutlierDetection specified, this will not take effect. | No |

## distribute

failure-domain.beta.kubernetes.io/region=us-east-1

failure-domain.beta.kubernetes.io/zone=us-east-1c

topology.kubernetes.io/region

topology.kubernetes.io/zone

topology.istio.io/subzone`

地域由如下三元组在网格中定义了地理位置：
- Region
- Zone
- Sub-zone

```
    distribute:
        - from: us-west/zone1/*
          to:
            "us-west/zone1/*": 80
            "us-west/zone2/*": 20
        - from: us-west/zone2/*
          to:
            "us-west/zone1/*": 20
            "us-west/zone2/*": 80
```

```
    [root@master01 localityLbSetting]# kubectl get node --show-labels
    NAME              STATUS   ROLES    AGE   VERSION   LABELS
    192.168.198.154   Ready    master   22d   v1.20.5   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=192.168.198.154,kubernetes.io/os=linux,kubernetes.io/role=master,topology.istio.io/subzone=sz01,topology.kubernetes.io/region=us-central1,topology.kubernetes.io/zone=z1
    192.168.198.155   Ready    master   22d   v1.20.5   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=192.168.198.155,kubernetes.io/os=linux,kubernetes.io/role=master,topology.istio.io/subzone=sz02,topology.kubernetes.io/region=us-central2,topology.kubernetes.io/zone=z2
    192.168.198.156   Ready    node     22d   v1.20.5   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=192.168.198.156,kubernetes.io/os=linux,kubernetes.io/role=node,topology.istio.io/subzone=sz03,topology.kubernetes.io/region=us-central3,topology.kubernetes.io/zone=z3
```

1.7.0/destinationrule/trafficPolicy/loadBalancer/localityLbSetting/dr-productpage-distribute.yaml
```
    apiVersion: networking.istio.io/v1alpha3
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          localityLbSetting:
            enabled: true
            distribute:
            - from: "us-central2/z2/*"
              to:
                "us-central3/z3/*": 100
                #"us-central2/z2/*": 100
                #"us-central1/z1/*": 100
        outlierDetection:
          consecutive5xxErrors: 1
          interval: 5m
          baseEjectionTime: 15m
```

```
kubectl scale deploy productpage-v1 --replicas=3 -n istio

kubectl logs -f productpage-v1-75bdc58c9c-7h4l4 -n istio -c istio-proxy

kubectl logs --tail 10 -f productpage-v1-75bdc58c9c-fgb2n -n istio -c istio-proxy

kubectl logs -f productpage-v1-75bdc58c9c-wcdgv -n istio -c istio-proxy
```

## enabled

是否启用

## failover

1.7.0/destinationrule/trafficPolicy/loadBalancer/localityLbSetting/dr-productpage-failover.yaml
```
    apiVersion: networking.istio.io/v1alpha3
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          localityLbSetting:
            enabled: true
            failover:
            - from: us-central1
              to: us-central2
            - from: us-central2
              to: us-central1
        outlierDetection:
          consecutive5xxErrors: 1
          interval: 5m
          baseEjectionTime: 15m
```

## simple

| Name | Description |
| ROUND_ROBIN | Round Robin policy. Default |
| LEAST_CONN | The least request load balancer uses an O(1) algorithm which selects two random healthy hosts and picks the host which has fewer active requests. |
| RANDOM | The random load balancer selects a random healthy host. The random load balancer generally performs better than round robin if no health checking policy is configured. |
| PASSTHROUGH | This option will forward the connection to the original IP address requested by the caller without doing any form of load balancing. This option must be used with care. It is meant for advanced use cases. Refer to Original Destination load balancer in Envoy for further details. |

## LEAST_CONN

1.7.0/destinationrule/trafficPolicy/loadBalancer/simple/dr-productpage-leastconn.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          simple: LEAST_CONN
```

## ROUND_ROBIN

1.7.0/destinationrule/trafficPolicy/loadBalancer/simple/dr-productpage-roundrobin.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          simple: ROUND_ROBIN
```

## RANDOM

1.7.0/destinationrule/trafficPolicy/loadBalancer/simple/dr-productpage-random.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          simple: RANDOM
```

## PASSTHROUGH

不使用负载均衡策略

no healthy upstream

1.7.0/destinationrule/trafficPolicy/loadBalancer/simple/dr-productpage-passthrough.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        loadBalancer:
          simple: PASSTHROUGH
```

使用方法，现在cluster配置中设置use_http_header为true，然后在请求中加入header。x-envoy-original-dst-host=10.195.16.237:8888 指向up stream

ef-passthrouth.yaml
```
    apiVersion: networking.istio.io/v1alpha3
    kind: EnvoyFilter
    metadata:
      name: lb-passthrough
      namespace: istio-system
    spec:
      workloadSelector:
        labels:
          istio: ingressgateway
      configPatches:
      - applyTo: CLUSTER
        match:
          cluster:
            name: outbound|9080||productpage.istio.svc.cluster.local
        patch:
            operation: MERGE
            value:
              original_dst_lb_config:
                use_http_header: true
```
```
curl -H "x-envoy-original-dst-host:172.20.0.38:9080" http://bookinfo.demo:30986/productpage

curl http://bookinfo.demo:30986/productpage -I
```

## outlierDetection

异常点检查

| Field | Type | Description | Required |
|-------|------|-------------|-----------|
| consecutiveErrors | int32 | Number of errors before a host is ejected from the connection pool. Defaults to 5. When the upstream host is accessed over HTTP, a 502, 503, or 504 return code qualifies as an error. When the upstream host is accessed over an opaque TCP connection, connect timeouts and connection error/failure events qualify as an error. | No |
| interval | Duration | Time interval between ejection sweep analysis. format: 1h/1m/1s/1ms. MUST BE >=1ms. Default is 10s. | No |
| baseEjectionTime | Duration | Minimum ejection duration. A host will remain ejected for a period equal to the product of minimum ejection duration and the number of times the host has been ejected. This technique allows the system to automatically increase the ejection period for unhealthy upstream servers. format: 1h/1m/1s/1ms. MUST BE >=1ms. Default is 30s. | No |
| maxEjectionPercent | int32 | Maximum % of hosts in the load balancing pool for the upstream service that can be ejected. Defaults to 10%. | No |
| minHealthPercent | int32 | Outlier detection will be enabled as long as the associated load balancing pool has at least minhealthpercent hosts in healthy mode. When the percentage of healthy hosts in the load balancing pool drops below this threshold, outlier detection will be disabled and the proxy will load balance across all hosts in the pool (healthy and unhealthy). The threshold can be disabled by setting it to 0%. The default is 0% as it’s not typically applicable in k8s environments with few pods per service. | No |

Warning: outlier detection consecutive errors is deprecated, use consecutiveGatewayErrors or consecutive5xxErrors instead

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| consecutiveGatewayErrors | UInt32Value | Number of gateway errors before a host is ejected from the connection pool. When the upstream host is accessed over HTTP, a 502, 503, or 504 return code qualifies as a gateway error. When the upstream host is accessed over an opaque TCP connection, connect timeouts and connection error/failure events qualify as a gateway error. This feature is disabled by default or when set to the value 0.Note that consecutivegatewayerrors and consecutive5xxerrors can be used separately or together. Because the errors counted by consecutivegatewayerrors are also included in consecutive5xxerrors, if the value of consecutivegatewayerrors is greater than or equal to the value of consecutive5xxerrors, consecutivegatewayerrors will have no effect. | No |
| consecutive5xxErrors | UInt32Value | Number of 5xx errors before a host is ejected from the connection pool. When the upstream host is accessed over an opaque TCP connection, connect timeouts, connection error/failure and request failure events qualify as a 5xx error. This feature defaults to 5 but can be disabled by setting the value to 0.Note that consecutivegatewayerrors and consecutive5xxerrors can be used separately or together. Because the errors counted by consecutivegatewayerrors are also included in consecutive5xxerrors, if the value of consecutivegatewayerrors is greater than or equal to the value of consecutive5xxerrors, consecutivegatewayerrors will have no effect.	 | |

1.7.0/destinationrule/trafficPolicy/outlierDetection/dr-productpage.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        connectionPool:
          tcp:
            maxConnections: 1
            connectTimeout: 30ms
          http:
            maxRequestsPerConnection: 1
            http1MaxPendingRequests: 1
        outlierDetection:
          #consecutiveErrors: 1
         # consecutiveGatewayErrors: 5
          consecutive5xxErrors: 1
          interval: 5s
          baseEjectionTime: 50s
          maxEjectionPercent: 100
          #minHealthPercent: 0
```
upstream connect error or disconnect/reset before headers. reset reason: overflow

no healthy upstream说明断路器生效

用jmeter做测试

## portLevelSettings

| Field | Type | Description | Required |
|-------|------|--------------|----------|
| port | PortSelector | Specifies the number of a port on the destination service on which this policy is being applied. | No |
| loadBalancer | LoadBalancerSettings	Settings controlling the load balancer algorithms. | No |
| connectionPool | ConnectionPoolSettings	Settings controlling the volume of connections to an upstream service | No |
| outlierDetection | OutlierDetection	Settings controlling eviction of unhealthy hosts from the load balancing pool | No |
| tls | TLSSettings | TLS related settings for connections to the upstream service. | No |

## connectionPool.http

1.7.0/destinationrule/trafficPolicy/portLevelSettings/connectionPool/dr-productpage-http.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          connectionPool:
            tcp:
              maxConnections: 10
              connectTimeout: 30ms
              tcpKeepalive:
                time: 7200s
                interval: 75s
                probes: 10
            http:
              http2MaxRequests: 10
              maxRequestsPerConnection: 1
              http1MaxPendingRequests: 1
              maxRetries: 1
              idleTimeout: 10s
              h2UpgradePolicy: DEFAULT
```

tcp

1.7.0/destinationrule/trafficPolicy/portLevelSettings/connectionPool/dr-productpage-tcp.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          connectionPool:
            tcp:
              maxConnections: 10
              connectTimeout: 30ms
              tcpKeepalive:
                time: 7200s
                interval: 75s
                probes: 10
```

## loadBalancer.consistentHash.httpCookie

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/dr-productpage-httpCookie.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            consistentHash:
              httpCookie:
                name: user
                ttl: 0s
```

httpHeaderName

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/dr-productpage-httpHeaderName.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            consistentHash:
              httpHeaderName: end-user
```

httpQueryParameterName

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/dr-productpage-httpQueryParameterName.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            consistentHash:
              httpQueryParameterName: test
```

minimumRingSize

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/dr-productpage-minimumRingSize.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            consistentHash:
              minimumRingSize: 100
              httpQueryParameterName: test
```

useSourceIp

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/dr-productpage-useSourceIp.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            consistentHash:
              useSourceIp: true
    ~
```

localityLbSetting.distribute

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/localityLbSetting/dr-productpage-distribute.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            localityLbSetting:
              enabled: true
              distribute:
              - from: "us-central1/*"
                to:
                  #"us-central1/*": 80
                  "us-central2/*": 100
```

failover

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/localityLbSetting/dr-productpage-failover.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            localityLbSetting:
              enabled: true
              failover:
              - from: us-central1
                to: us-central2
              - from: us-central1
                to: us-central2
          outlierDetection:
            consecutiveErrors: 7
            interval: 5m
            baseEjectionTime: 15m
```

simple.LEAST_CONN

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/simple/dr-productpage-leastconn.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: LEAST_CONN
```

ROUND_ROBIN

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/simple/dr-productpage-roundrobin.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: ROUND_ROBIN
```

RANDOM

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/simple/dr-productpage-random.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
```

PASSTHROUGH

1.7.0/destinationrule/trafficPolicy/portLevelSettings/loadBalancer/simple/dr-productpage-passthrough.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: PASSTHROUGH
```

outlierDetection

1.7.0/destinationrule/trafficPolicy/portLevelSettings/outlierDetection/dr-productpage.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          connectionPool:
            tcp:
              maxConnections: 10
              connectTimeout: 30ms
            http:
              http2MaxRequests: 50
              maxRequestsPerConnection: 5
          outlierDetection:
            consecutiveErrors: 7
            interval: 5s
            baseEjectionTime: 15s
            maxEjectionPercent: 30
            minHealthPercent: 10
```

tls

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| mode | TLSmode | Indicates whether connections to this port should be secured using TLS. The value of this field determines how TLS is enforced. | Yes |
| clientCertificate | string | REQUIRED if mode is MUTUAL. The path to the file holding the client-side TLS certificate to use. Should be empty if mode is ISTIO_MUTUAL. | No |
| privateKey | string | REQUIRED if mode is MUTUAL. The path to the file holding the client’s private key. Should be empty if mode is ISTIO_MUTUAL. | No |
| caCertificates | string | OPTIONAL: The path to the file containing certificate authority certificates to use in verifying a presented server certificate. If omitted, the proxy will not verify the server’s certificate. Should be empty if mode is ISTIO_MUTUAL. | No |
| subjectAltNames | string[] | A list of alternate names to verify the subject identity in the certificate. If specified, the proxy will verify that the server certificate’s subject alt name matches one of the specified values. If specified, this list overrides the value of subjectaltnames from the ServiceEntry. | No |
| sni	string	SNI | string | to present to the server during TLS handshake.	 | |

## caCertificates

1、创建证书
```
example.com2.key

example.com2.crt
```

上面两个证书和根证书的内容一致
```
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -subj '/O=example Inc./CN=example.com' -keyout example.com.key -out example.com.crt

openssl req -out productpage.csr -newkey rsa:2048 -nodes -keyout productpage.key -subj "/CN=productpage.istio.svc.cluster.local/O=some organization"

openssl x509 -req -days 365 -CA example.com2.crt -CAkey example.com.2key -set_serial 0 -in productpage.csr -out productpage.crt

openssl req -out client.example.com.csr -newkey rsa:2048 -nodes -keyout client.example.com.key -subj "/CN=sleep.istio.svc.cluster.local/O=client organization"

openssl x509 -req -in client.example.com.csr -CA example.com2.crt -CAkey example.com2.key -CAcreateserial -out client.example.com.crt -days 3650 -extensions v3_req -extfile ./workload.cfg
```
注意san

2、创建secret
```
kubectl create -n istio secret generic productpage-credential --from-file=tls.key=productpage.key --from-file=tls.crt=productpage.crt --from-file=ca.crt=example.com.crt
```

修改deployment
productpage-deploy.yaml
```
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      labels:
        app: productpage
        version: v1
      name: productpage-v1
    spec:
      progressDeadlineSeconds: 600
      replicas: 1
      revisionHistoryLimit: 10
      selector:
        matchLabels:
          app: productpage
          version: v1
      strategy:
        rollingUpdate:
          maxSurge: 25%
          maxUnavailable: 25%
        type: RollingUpdate
      template:
        metadata:
          annotations:                                                                                       
            sidecar.istio.io/userVolumeMount: '[{"name":"my-cert", "mountPath":"/etc/my-cert", "readonly":true}]'
            sidecar.istio.io/userVolume: '[{"name":"my-cert", "secret":{"secretName":"productpage-credential"}}]'
          labels:
            app: productpage
            version: v1
        spec:
          containers:
          - image: docker.io/istio/examples-bookinfo-productpage-v1:1.16.2
            imagePullPolicy: IfNotPresent
            name: productpage
            ports:
            - containerPort: 9080
              protocol: TCP
            resources: {}
            securityContext:
              runAsUser: 1000
            terminationMessagePath: /dev/termination-log
            terminationMessagePolicy: File
            volumeMounts:
            - mountPath: /tmp
              name: tmp
            - mountPath: /etc/my-cert
              name: secret-vol
          dnsPolicy: ClusterFirst
          restartPolicy: Always
          schedulerName: default-scheduler
          securityContext: {}
          serviceAccount: bookinfo-productpage
          serviceAccountName: bookinfo-productpage
          terminationGracePeriodSeconds: 30
          volumes:
          - emptyDir: {}
            name: tmp
          - name: secret-vol
            secret:
              defaultMode: 420
              secretName: productpage-credential
```

sleep-deploy.yaml
```
    piVersion: apps/v1
    kind: Deployment
    metadata:
      name: sleep
    spec:
      progressDeadlineSeconds: 600
      replicas: 1
      revisionHistoryLimit: 10
      selector:
        matchLabels:
          app: sleep
      strategy:
        rollingUpdate:
          maxSurge: 25%
          maxUnavailable: 25%
        type: RollingUpdate
      template:
        metadata:
          annotations:                                                                                       
            sidecar.istio.io/userVolumeMount: '[{"name":"my-cert", "mountPath":"/etc/my-cert", "readonly":true}]'
            sidecar.istio.io/userVolume: '[{"name":"my-cert", "secret":{"secretName":"productpage-credential"}}]'
          labels:
            app: sleep
        spec:
          containers:
          - command:
            - /bin/sleep
            - 3650d
            image: curlimages/curl
            imagePullPolicy: IfNotPresent
            name: sleep
            resources: {}
            terminationMessagePath: /dev/termination-log
            terminationMessagePolicy: File
            volumeMounts:
            - mountPath: /etc/sleep/tls
              name: secret-volume
          dnsPolicy: ClusterFirst
          restartPolicy: Always
          schedulerName: default-scheduler
          securityContext: {}
          serviceAccount: sleep
          serviceAccountName: sleep
          terminationGracePeriodSeconds: 0
          volumes:
          - name: secret-volume
            secret:
              defaultMode: 420
              optional: true
              secretName: sleep-secret
```

1.7.0/destinationrule/trafficPolicy/portLevelSettings/tls/dr-productpage-caCertificates.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
          tls:
            mode: MUTUAL
            caCertificates: /etc/my-cert/ca.crt
            clientCertificate: /etc/my-cert/tls.crt
            privateKey: /etc/my-cert/tls.key
            sni: productpage.istio.svc.cluster.local
```

```
kubectl exec -it -n istio sleep-789bfc5d9-2j7df -- /bin/sh

curl productpage.istio:9080/productpage
```

clientCertificate,privateKey

1.7.0/destinationrule/trafficPolicy/portLevelSettings/tls/dr-productpage-clientCertificate.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
          tls:
            mode: MUTUAL
            caCertificates: /etc/my-cert/ca.crt
            clientCertificate: /etc/my-cert/tls.crt
            privateKey: /etc/my-cert/tls.key
            sni: productpage.istio.svc.cluster.local
```

## mode

| Name | Description|
|------|------------|
| DISABLE | Do not setup a TLS connection to the upstream endpoint. |
| SIMPLE | Originate a TLS connection to the upstream endpoint. |
| MUTUAL | Secure connections to the upstream using mutual TLS by presenting client certificates for authentication. |
| ISTIO_MUTUAL | Secure connections to the upstream using mutual TLS by presenting client certificates for authentication. Compared to Mutual mode, this mode uses certificates generated automatically by Istio for mTLS authentication. When this mode is used, all other fields in TLSSettings should be empty. |

ISTIO_MUTUAL将配置在与host匹配的服务进行连接时使用Istio内部实现设置密钥和证书来进行双向TLS认证。 MUTUAL 将配置在与host匹配的服务进行连接时使用自定义的密钥和证书来进行双向TLS认证。 SIMPLE 将配置在与host匹配的服务进行连接时使用标准TLS语义

1.7.0/destinationrule/trafficPolicy/portLevelSettings/tls/dr-productpage-mode-disable.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
          tls:
            mode: DISABLE
```

1.7.0/destinationrule/trafficPolicy/portLevelSettings/tls/dr-productpage-mode-istio-mutual.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
          tls:
            mode: ISTIO_MUTUAL
```

credentialName

目前不支持

1.7.0/destinationrule/trafficPolicy/portLevelSettings/tls/dr-productpage-credentialName.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
          tls:
            mode: SIMPLE
            credentialName: bookinfo-credential
```
sni

1.7.0/destinationrule/trafficPolicy/portLevelSettings/tls/dr-productpage-sni.yaml

    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
          tls:
            mode: MUTUAL
            caCertificates: /etc/my-cert/ca.crt
            clientCertificate: /etc/my-cert/tls.crt
            privateKey: /etc/my-cert/tls.key
            sni: productpage.istio.svc.cluster.local
```

subjectAltNames

1.7.0/destinationrule/trafficPolicy/portLevelSettings/tls/dr-productpage-subjectAltNames.yaml
```
    apiVersion: networking.istio.io/v1beta1
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      subsets:
      - name: v1
        labels:
          version: v1
      trafficPolicy:
        portLevelSettings:
        - port:
            number: 9080
          loadBalancer:
            simple: RANDOM
          tls:
            mode: SIMPLE
            caCertificates: /etc/my-cert/ca.crt
            sni: productpage.istio.svc.cluster.local
            subjectAltNames: 
            - spiffe://cluster.local/ns/istio/sa/bookinfo-productpage
```

外部服务tls origination

Egress Gateways with TLS Origination (File Mount)

1、创建证书
```
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -subj '/O=example Inc./CN=example.com' -keyout example.com.key -out example.com.crt

openssl req -out my-nginx.mesh-external.svc.cluster.local.csr -newkey rsa:2048 -nodes -keyout my-nginx.mesh-external.svc.cluster.local.key -subj "/CN=my-nginx.mesh-external.svc.cluster.local/O=some organization" openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 0 -in my-nginx.mesh-external.svc.cluster.local.csr -out my-nginx.mesh-external.svc.cluster.local.crt

openssl req -out client.example.com.csr -newkey rsa:2048 -nodes -keyout client.example.com.key -subj "/CN=client.example.com/O=client organization" openssl x509 -req -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 1 -in client.example.com.csr -out client.example.com.crt
```

2、部署应用
```
kubectl create namespace mesh-external

kubectl create -n mesh-external secret tls nginx-server-certs --key my-nginx.mesh-external.svc.cluster.local.key --cert my-nginx.mesh-external.svc.cluster.local.crt kubectl create -n mesh-external secret generic nginx-ca-certs --from-file=example.com.crt
```

nginx.conf
```
    events {
    }
    ​
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

        server_name my-nginx.mesh-external.svc.cluster.local;
        ssl_certificate /etc/nginx-server-certs/tls.crt;
        ssl_certificate_key /etc/nginx-server-certs/tls.key;
        ssl_client_certificate /etc/nginx-ca-certs/example.com.crt;
        ssl_verify_client on;
      }
    }
```

```
kubectl create configmap nginx-configmap -n mesh-external --from-file=nginx.conf=./nginx.conf
```

nginx-deploy.yaml
```
    apiVersion: v1
    kind: Service
    metadata:
      name: my-nginx
      namespace: mesh-external
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
      namespace: mesh-external
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
            - name: nginx-ca-certs
              mountPath: /etc/nginx-ca-certs
              readOnly: true
          volumes:
          - name: nginx-config
            configMap:
              name: nginx-configmap
          - name: nginx-server-certs
            secret:
              secretName: nginx-server-certs
          - name: nginx-ca-certs
            secret:
              secretName: nginx-ca-certs
```

3、egress gateway
```
kubectl create -n istio-system secret tls nginx-client-certs --key client.example.com.key --cert client.example.com.crt kubectl create -n istio-system secret generic nginx-ca-certs --from-file=example.com.crt
```

gateway-patch.json
```
    [{
      "op": "add",
      "path": "/spec/template/spec/containers/0/volumeMounts/0",
      "value": {
        "mountPath": "/etc/istio/nginx-client-certs",
        "name": "nginx-client-certs",
        "readOnly": true
      }
    },
    {
      "op": "add",
      "path": "/spec/template/spec/volumes/0",
      "value": {
      "name": "nginx-client-certs",
        "secret": {
          "secretName": "nginx-client-certs",
          "optional": true
        }
      }
    },
    {
      "op": "add",
      "path": "/spec/template/spec/containers/0/volumeMounts/1",
      "value": {
        "mountPath": "/etc/istio/nginx-ca-certs",
        "name": "nginx-ca-certs",
        "readOnly": true
      }
    },
    {
      "op": "add",
      "path": "/spec/template/spec/volumes/1",
      "value": {
      "name": "nginx-ca-certs",
        "secret": {
          "secretName": "nginx-ca-certs",
          "optional": true
        }
      }
    }]
```

```
kubectl -n istio-system patch --type=json deploy istio-egressgateway -p "$(cat gateway-patch.json)"

kubectl exec -n istio-system "$(kubectl -n istio-system get pods -l istio=egressgateway -o jsonpath='{.items[0].metadata.name}')" -- ls -al /etc/istio/nginx-client-certs /etc/istio/nginx-ca-certs
```

4、Configure mutual TLS origination

se-nginx.yaml
```
    apiVersion: networking.istio.io/v1alpha3
    kind: ServiceEntry
    metadata:
      name: my-nginx
    spec:
      hosts:
      - "my-nginx.mesh-external.svc.cluster.local"
      addresses:
      - 192.168.198.159
      ports:
      - number: 443
        name: https
        protocol: HTTPS
      location: MESH_INTERNAL
      resolution: STATIC
      workloadSelector:
        labels:
          run: my-nginx
```

gw-dr.yaml
```
    apiVersion: networking.istio.io/v1alpha3
    kind: Gateway
    metadata:
      name: istio-egressgateway
    spec:
      selector:
        istio: egressgateway
      servers:
      - port:
          number: 443
          name: https
          protocol: HTTPS
        hosts:
        - my-nginx.mesh-external.svc.cluster.local
        tls:
          mode: ISTIO_MUTUAL
    ---
    apiVersion: networking.istio.io/v1alpha3
    kind: DestinationRule
    metadata:
      name: egressgateway-for-nginx
    spec:
      host: istio-egressgateway.istio-system.svc.cluster.local
      subsets:
      - name: nginx
        trafficPolicy:
          loadBalancer:
            simple: ROUND_ROBIN
          portLevelSettings:
          - port:
              number: 443
            tls:
              mode: ISTIO_MUTUAL
              #mode: MUTUAL
              #clientCertificate: /etc/istio/nginx-client-certs/tls.crt
              #privateKey: /etc/istio/nginx-client-certs/tls.key
              #caCertificates: /etc/istio/nginx-ca-certs/example.com.crt
              sni: my-nginx.mesh-external.svc.cluster.local
```

vs-nginx.yaml
```
    apiVersion: networking.istio.io/v1alpha3
    kind: VirtualService
    metadata:
      name: direct-nginx-through-egress-gateway
    spec:
      hosts:
      - my-nginx.mesh-external.svc.cluster.local
      gateways:
      - istio-egressgateway
      - mesh
      http:
      - match:
        - gateways:
          - mesh
          port: 80
        route:
        - destination:
            host: istio-egressgateway.istio-system.svc.cluster.local
            subset: nginx
            port:
              number: 443
          weight: 100
      - match:
        - gateways:
          - istio-egressgateway
          port: 443
        route:
        - destination:
            host: my-nginx.mesh-external.svc.cluster.local
            port:
              number: 443
          weight: 100
```

dr-nginx.yaml
```
kubectl apply -f dr-nginx.yaml -n istio-system
```
```
    apiVersion: networking.istio.io/v1alpha3
    kind: DestinationRule
    metadata:
      name: originate-mtls-for-nginx
    spec:
      host: my-nginx.mesh-external.svc.cluster.local
      trafficPolicy:
        loadBalancer:
          simple: ROUND_ROBIN
        portLevelSettings:
        - port:
            number: 443
          tls:
            mode: MUTUAL
            #mode: SIMPLE
            clientCertificate: /etc/istio/nginx-client-certs/tls.crt
            privateKey: /etc/istio/nginx-client-certs/tls.key
            caCertificates: /etc/istio/nginx-ca-certs/example.com.crt
            sni: my-nginx.mesh-external.svc.cluster.local
```
```
kubectl exec "$(kubectl get pod -l app=sleep -o jsonpath={.items..metadata.name} -nistio)" -c sleep -nistio -- curl -sS http://my-nginx.mesh-external.svc.cluster.local
```

## tls

subsets

1.7.0/destinationrule/subsets/dr-productpage-subsets.yaml
```
    apiVersion: networking.istio.io/v1alpha3
    kind: DestinationRule
    metadata:
      name: productpage
    spec:
      host: productpage.istio.svc.cluster.local
      trafficPolicy:
        loadBalancer:
          simple: LEAST_CONN
      subsets:
      - name: v1
        labels:
          version: v1
        trafficPolicy:
          loadBalancer:
            simple: ROUND_ROBIN
```
