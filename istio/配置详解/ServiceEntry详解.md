# 一、什么是ServiceEntry

使用服务条目资源（Service Entries）可以将条目添加到 Istio 内部维护的服务注册表中。添加服务条目后，Envoy 代理可以将流量发送到该服务，就好像该服务条目是网格中的服务一样。通过配置服务条目，可以管理在网格外部运行的服务的流量。

此外，可以配置虚拟服务和目标规则，以更精细的方式控制到服务条目的流量，就像为网格中的其他任何服务配置流量一样。

# 二、资源详解

| Field | Type | Description | Required |
|-------|------|------------|-----------|
| hosts | string[] | The hosts associated with the ServiceEntry. Could be a DNS name with wildcard prefix.The hosts field is used to select matching hosts in VirtualServices and DestinationRules.For HTTP traffic the HTTP Host/Authority header will be matched against the hosts field.For HTTPs or TLS traffic containing Server Name Indication (SNI), the SNI value will be matched against the hosts field.NOTE 1: When resolution is set to type DNS and no endpoints are specified, the host field will be used as the DNS name of the endpoint to route traffic to.NOTE 2: If the hostname matches with the name of a service from another service registry such as Kubernetes that also supplies its own set of endpoints, the ServiceEntry will be treated as a decorator of the existing Kubernetes service. Properties in the service entry will be added to the Kubernetes service if applicable. Currently, the only the following additional properties will be considered by istiod:subjectAltNames: In addition to verifying the SANs of the service accounts associated with the pods of the service, the SANs specified here will also be verified. | Yes |
| addresses | string[] | The virtual IP addresses associated with the service. Could be CIDR prefix. For HTTP traffic, generated route configurations will include http route domains for both the addresses and hosts field values and the destination will be identified based on the HTTP Host/Authority header. If one or more IP addresses are specified, the incoming traffic will be identified as belonging to this service if the destination IP matches the IP/CIDRs specified in the addresses field. If the Addresses field is empty, traffic will be identified solely based on the destination port. In such scenarios, the port on which the service is being accessed must not be shared by any other service in the mesh. In other words, the sidecar will behave as a simple TCP proxy, forwarding incoming traffic on a specified port to the specified destination endpoint IP/host. Unix domain socket addresses are not supported in this field. | No |
| ports | Port[] | The ports associated with the external service. If the Endpoints are Unix domain socket addresses, there must be exactly one port. | Yes |
| location | Location | Specify whether the service should be considered external to the mesh or part of the mesh. | No |
| resolution | Resolution | Service discovery mode for the hosts. Care must be taken when setting the resolution mode to NONE for a TCP port without accompanying IP addresses. In such cases, traffic to any IP on said port will be allowed (i.e. 0.0.0.0:). | Yes |
| endpoints | WorkloadEntry[] | One or more endpoints associated with the service. Only one of endpoints or workloadSelector can be specified. | No 
| workloadSelector | WorkloadSelector | Applicable only for MESH_INTERNAL services. Only one of endpoints or workloadSelector can be specified. Selects one or more Kubernetes pods or VM workloads (specified using WorkloadEntry) based on their labels. The WorkloadEntry object representing the VMs should be defined in the same namespace as the ServiceEntry. | No |
| exportTo | string[] | A list of namespaces to which this service is exported. Exporting a service allows it to be used by sidecars, gateways and virtual services defined in other namespaces. This feature provides a mechanism for service owners and mesh administrators to control the visibility of services across namespace boundaries.If no namespaces are specified then the service is exported to all namespaces by default.The value “.” is reserved and defines an export to the same namespace that the service is declared in. Similarly the value “*” is reserved and defines an export to all namespaces.For a Kubernetes Service, the equivalent effect can be achieved by setting the annotation “networking.istio.io/exportTo” to a comma-separated list of namespace names. |  No |
| subjectAltNames | string[] | If specified, the proxy will verify that the server certificate’s subject alternate name matches one of the specified values.NOTE: When using the workloadEntry with workloadSelectors, the service account specified in the workloadEntry will also be used to derive the additional subject alternate names that should be verified. | No |

# 三、exportTo

1、当前名称空间

1）部署sleep
```
kubectl apply -f samples/sleep/sleep.yaml -n istio
```

2)修改默认访问策略

mesh下面
```
outboundTrafficPolicy: 
  mode: REGISTRY_ONLY
```

重启pod istiod使之生效

3)应用serviceentry
```
# cat serviceentries/se-baidu-dot.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  exportTo: 
  - "."
  hosts:
  - "www.baidu.com"
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS
```

```
kubectl apply -f se-baidu-dot.yaml -n istio  
```

2、名称空间
```
# cat serviceentries/se-baidu-namespace.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  exportTo: 
  - "istio-system"
  hosts:
  - "www.baidu.com"
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS
```

```
kubectl apply -f se-baidu-namespace.yaml -n istio
```
- 修改名称空间为istio，再测试

3、所有名称空间
```
# cat serviceentries/se-baidu-star.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  exportTo: 
  - "*"
  hosts:
  - "www.baidu.com"
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS
```

# 四、hosts
```
# cat serviceentries/se-baidu-hosts.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  hosts:
  - "www.baidu.com"
  - "www.csdn.net"
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS
```

# 五、resolution

1、DNS
```
# cat serviceentries/se-baidu-resolution-dns.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  hosts:
  - "www.baidu.com"
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS
```

2、STATIC
```
# cat mongodb-se-resolution-static.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
```

```
# cat se-baidu-resolution-static.yaml

apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry
metadata:
  name: baidu
spec:
  hosts:
  - "www.baidu.com"
  ports: 
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 36.152.44.96
```

3、NONE

配置静态dns
```
kubectl edit cm coredns -n kube-system

hosts { 192.168.198.158 mymongodb.demo 36.152.44.96 www.baidu.com fallthrough }
```

```
# cat se-baidu-resolution-none.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  hosts:
  - www.baidu.com
  location: MESH_EXTERNAL
  ports:
  - number: 80
    name: http
    protocol: HTTP
  resolution: NONE
```

进入pod访问
```
kubectl exec -it client-bcd749854-dnkml -n istio -- /bin/sh

wget www.baidu.com
```

# 六、vs dr se联合使用

1)部署mongodb
```
yum install mongodb-org
```

配置mongodb远程访问
```
bind 0.0.0.0
```

启动mongod
```
systemctl start mongod
```

2)创建se
```
# cat mongodb-se-resolution-static-multi-ep.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
  - address: 192.168.198.155
```

3)创建vs
```
# cat vs-mongodb.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: vs-mongodb
spec:
  hosts:
  - "mymongodb.demo"
  tcp:
  - route:
    - destination:
        host: mymongodb.demo
```

4)创建dr
```
# cat dr-mongodb-random.yaml

apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: mymongodb
spec:
  host: mymongodb.demo
  trafficPolicy:
    loadBalancer:
      simple: RANDOM
```

5)设置coredns静态dns
```
kubectl get cm -n kube-system coredns -o yaml

hosts { 192.168.198.158 mymongodb.demo fallthrough }
```

6)进入mongodb pod
```
kubectl exec -it mongodb-v1-64d4666575-6n2dq -n istio -- /bin/bash
```

7)访问
```
mongo --host mymongodb.demo

或

mongo --host 192.168.198.158
```

# 七、location

| Name | Description |
|------|--------------|
| MESH_EXTERNAL|  Signifies that the service is external to the mesh. Typically used to indicate external services consumed through APIs. |
| MESH_INTERNAL | Signifies that the service is part of the mesh. Typically used to indicate services added explicitly as part of expanding the service mesh to include unmanaged infrastructure (e.g., VMs added to a Kubernetes based service mesh). |

1）MESH_EXTERNAL
```
# cat serviceentries/se-baidu-star.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  exportTo: 
  - "*"
  hosts:
  - "www.baidu.com"
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS
```

2)MESH_INTERNAL
```
# cat se-details-location-internal.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: details-se
spec:
  hosts:
  - details.bookinfo.com
  location: MESH_INTERNAL
  ports:
  - number: 9080
    name: http
    protocol: HTTP
  resolution: STATIC
  workloadSelector:
    labels:
      app: details
```

添加静态路由
```
hosts { 192.168.198.158 mymongodb.demo 36.152.44.96 www.baidu.com 10.68.190.94 details.bookinfo.com fallthrough }
```

删除client pod
```
kubectl delete pod client-bcd749854-dnkml -n istio
```

进入pod
```
kubectl exec -it client-bcd749854-hs2s7 -n istio -- /bin/sh

wget details.bookinfo.com:9080/details/0
```

# 八、addresses
```
# cat se-details-adresses.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: details-se
spec:
  hosts:
  - details.bookinfo.com
  addresses:
  - 192.168.198.177/32
  - 192.168.198.178/32
  location: MESH_INTERNAL
  ports:
  - number: 9080
    name: http
    protocol: HTTP
  resolution: STATIC
  workloadSelector:
    labels:
      app: details
```
- 两个address第一个不生效，最后一个生效，改为一个address再试

# 九、ports

1）http端口：
```
# cat serviceentries/se-baidu-star.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  exportTo: 
  - "*"
  hosts:
  - "www.baidu.com"
  ports:
  - number: 80
    name: http
    protocol: HTTP
  location: MESH_EXTERNAL
  resolution: DNS
```

2)443端口
```
# cat se-baidu-ports-https.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: baidu
spec:
  exportTo: 
  - "*"
  hosts:
  - "www.baidu.com"
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  location: MESH_EXTERNAL
  resolution: DNS
```

```
# cat se-jd-ports-https.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: jd-api
spec:
  hosts:
  - api.jd.com
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  resolution: DNS
```

```
kubectl exec -it sleep-557747455f-wqtls -n istio -- /bin/sh

curl 百度一下，你就知道

curl 多快好省，购物上京东！
```

# 十、使用egress
```
# cat se-cnn.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: cnn
spec:
  hosts:
  - edition.cnn.com
  ports:
  - number: 80
    name: http-port
    protocol: HTTP
  - number: 443
    name: https
    protocol: HTTPS
  resolution: DNS
```

```
# cat cnn-egressgateway.yaml

apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: cnn-egressgateway
spec:
  selector:
    istio: egressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - edition.cnn.com
```

```
# cat dr-egressgateway-cnn.yaml

apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: dr-egressgateway-cnn
spec:
  host: istio-egressgateway.istio-system.svc.cluster.local
  subsets:
  - name: cnn
```

```
# cat vs-cnn.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: direct-cnn-through-egress-gateway
spec:
  hosts:
  - edition.cnn.com
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
        subset: cnn
        port:
          number: 80
      weight: 100
  - match:
    - gateways:
      - istio-egressgateway
      port: 80
    route:
    - destination:
        host: edition.cnn.com
        port:
          number: 80
      weight: 100
```
curl http://edition.cnn.com/politics -I

查看egress日志
```
kubectl logs istio-egressgateway-bd6d77495-vmhvg -n istio-system -f
```

# 十一、endpoints

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| address | string | Address associated with the network endpoint without the port. Domain names can be used if and only if the resolution is set to DNS, and must be fully-qualified without wildcards. Use the form unix:///absolute/path/to/socket for Unix domain socket endpoints. | Yes |
| ports | map | Set of ports associated with the endpoint. If the port map is specified, it must be a map of servicePortName to this endpoint’s port, such that traffic to the service port will be forwarded to the endpoint port that maps to the service’s portName. If omitted, and the targetPort is specified as part of the service’s port specification, traffic to the service port will be forwarded to one of the endpoints on the specified targetPort. If both the targetPort and endpoint’s port map are not specified, traffic to a service port will be forwarded to one of the endpoints on the same port.NOTE 1: Do not use for unix:// addresses.NOTE 2: endpoint port map takes precedence over targetPort. | No |
| labels | map | One or more labels associated with the endpoint. | No |
| network | string | Network enables Istio to group endpoints resident in the same L3 domain/network. All endpoints in the same network are assumed to be directly reachable from one another. When endpoints in different networks cannot reach each other directly, an Istio Gateway can be used to establish connectivity (usually using the AUTO_PASSTHROUGH mode in a Gateway Server). This is an advanced configuration used typically for spanning an Istio mesh over multiple clusters. | No |
| locality | string | The locality associated with the endpoint. A locality corresponds to a failure domain (e.g., country/region/zone). Arbitrary failure domain hierarchies can be represented by separating each encapsulating failure domain by /. For example, the locality of an an endpoint in US, in US-East-1 region, within availability zone az-1, in data center rack r11 can be represented as us/us-east-1/az-1/r11. Istio will configure the sidecar to route to endpoints within the same locality as the sidecar. If none of the endpoints in the locality are available, endpoints parent locality (but within the same network ID) will be chosen. For example, if there are two endpoints in same network (networkID “n1”), say e1 with locality us/us-east-1/az-1/r11 and e2 with locality us/us-east-1/az-2/r12, a sidecar from us/us-east-1/az-1/r11 locality will prefer e1 from the same locality over e2 from a different locality. Endpoint e2 could be the IP associated with a gateway (that bridges networks n1 and n2), or the IP associated with a standard service endpoint. | No |
| weight | uint32 | The load balancing weight associated with the endpoint. Endpoints with higher weights will receive proportionally higher traffic. | No |
| serviceAccount | string | The service account associated with the workload if a sidecar is present in the workload. The service account must be present in the same namespace as the configuration ( WorkloadEntry or a ServiceEntry)	 | |

- https://istio.io/latest/docs/reference/config/networking/workload-entry/#WorkloadEntry

1) address
```
# cat mongodb-se-resolution-static-multi-ep.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
  - address: 192.168.198.155
```

2)labels

1创建se
```
endpoints/se-mongodb-labels.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
    labels:
      version: v1
  - address: 192.168.198.155
    labels:
      version: v2
```

2创建vs
```
# cat endpoints/vs-mongodb-v1.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: vs-mongodb
spec:
  hosts:
  - "mymongodb.demo"
  tcp:
  - route:
    - destination:
        host: mymongodb.demo
        subset: v1
```

3创建dr
```
# cat endpoints/dr-mongodb.yaml

apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: mymongodb
spec:
  host: mymongodb.demo
  trafficPolicy:
    loadBalancer:
      simple: RANDOM
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

4访问
```
kubectl exec -it mongodb-v1-64d4666575-6n2dq -n istio -- /bin/bash

mongo --host mymongodb.demo
```
- 结果都路由到v1版本

3）locality

region/zone/subzone

distribute
```
[root@master01 kube]# kubectl get node --show-labels
NAME              STATUS   ROLES    AGE   VERSION   LABELS
192.168.198.154   Ready    master   22d   v1.20.5   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=192.168.198.154,kubernetes.io/os=linux,kubernetes.io/role=master,topology.istio.io/subzone=sz01,topology.kubernetes.io/region=us-central1,topology.kubernetes.io/zone=z1
192.168.198.155   Ready    master   22d   v1.20.5   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=192.168.198.155,kubernetes.io/os=linux,kubernetes.io/role=master,topology.istio.io/subzone=sz02,topology.kubernetes.io/region=us-central2,topology.kubernetes.io/zone=z2
192.168.198.156   Ready    node     22d   v1.20.5   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=192.168.198.156,kubernetes.io/os=linux,kubernetes.io/role=node,topology.istio.io/subzone=sz03,topology.kubernetes.io/region=us-central3,topology.kubernetes.io/zone=z3
```

```
# cat endpoints/se-mongodb-locality.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
    locality: "us-central1/z1/sz01"
    labels:
      version: v1
  - address: 192.168.198.155
    labels:
      version: v2
    locality: "us-central2/z2/sz02"
```

topology.kubernetes.io/region=us-central1

topology.kubernetes.io/zone=z1

topology.istio.io/subzone=sz01

```
# cat endpoints/dr-mongodb-locality.yaml

apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: dr-mongodb
spec:
  host: mymongodb.demo
  trafficPolicy:
    loadBalancer:
      localityLbSetting:
        enabled: true
        distribute:
        - from: "us-central1/z1/*"
          to:
            #"us-central3/z3/*": 100
            "us-central2/z2/*": 100
            #"us-central1/z1/*": 100
    outlierDetection:
      consecutive5xxErrors: 1
      interval: 5m
      baseEjectionTime: 15m
```

```
# cat endpoints/vs-mongodb-locality.yaml

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: vs-mongodb
spec:
  hosts:
  - "mymongodb.demo"
  tcp:
  - route:
    - destination:
        host: mymongodb.demo
```

```
kubectl exec -it mongodb-v1-64d4666575-hl6br -n istio -- /bin/bash

mongo --host 192.168.198.158
```

4)failover
```
# cat endpoints/dr-mongodb-locality-failover.yaml

apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: dr-mongodb
spec:
  host: mymongodb.demo
  trafficPolicy:
    loadBalancer:
      localityLbSetting:
        enabled: true
        failover:
        - from: us-central1/z1/sz01
          to: us-central2/z2/sz02
        - from: us-central2/z2/sz02
          to: us-central1/z1/sz01
    outlierDetection:
      consecutive5xxErrors: 1
      interval: 1s
      baseEjectionTime: 15m
```

5) network
```
# cat endpoints/se-mongodb-network.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
    network: n1
  - address: 192.168.198.155
```

6) weight
```
# cat endpoints/se-mongodb-weight.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
    weight: 10
  - address: 192.168.198.155
    weight: 90
```

7)serviceAccount
```
# cat endpoints/se-mongodb-serviceaccount.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27017
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
    serviceAccount: mongov1
  - address: 192.168.198.155
    serviceAccount: mongov2
```

8) ports
```
# cat endpoints/se-mongodb-endpoint-ports.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: mongodb-se
spec:
  hosts:
  - mymongodb.demo 
  addresses:
  - "192.168.198.158/32"
  ports:
  - number: 27019
    name: mongodb
    protocol: MONGO
  location: MESH_EXTERNAL
  resolution: STATIC
  endpoints:
  - address: 192.168.198.154
    ports:
      mongodb: 27017
  - address: 192.168.198.155
    ports:
      mongodb: 27017
```
```
mongo --host mymongodb.demo --port 27019
```

# 十二、subjectAltNames

在default部署details2
```
details2-deploy.yaml
```

```
se-details-subject-alt-names.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: details-se
spec:
  hosts:
  - details.default.com
  addresses:
  - 192.168.198.159
  location: MESH_INTERNAL
  ports:
  - number: 9080
    name: http
    protocol: HTTP
  resolution: STATIC
  subjectAltNames:
  - "aa"
  workloadSelector:
    labels:
      app: default-details
```

# 十三、workloadSelector

在default部署details2
```
details2-deploy.yaml

apiVersion: v1
kind: Service
metadata:
  name: details
  labels:
    app: details
    service: details
spec:
  ports:
  - port: 9080
    name: http
  selector:
    app: details
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: bookinfo-details
  labels:
    account: details
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: details-v1
  labels:
    app: default-details
    version: v1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: default-details
      version: v1
  template:
    metadata:
      labels:
        app: default-details
        version: v1
    spec:
      serviceAccountName: bookinfo-details
      containers:
      - name: details
        image: docker.io/istio/examples-bookinfo-details-v1:1.16.2
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 9080
        securityContext:
          runAsUser: 1000
```

```
se-details-workloadSelector.yaml

apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: details-se
spec:
  hosts:
  - details.default.com
  addresses:
  - 192.168.198.159
  location: MESH_INTERNAL
  ports:
  - number: 9080
    name: http
    protocol: HTTP
  resolution: STATIC
  workloadSelector:
    labels:
      app: default-details
```

```
kubectl apply -f se-details-workloadSelector.yaml
```
