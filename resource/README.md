国际单位制：
- 十进制：E、P、T、G、M、K、m
- 二进制：Ei、Pi、Ti、Gi、Mi、Ki、MiB

比如：
- 1 KB = 1000 Bytes = 8000 Bits；
- 1 KiB = 1024 Bytes = 8192 Bits；

一、QoS 资源服务质量控制
---
1、QoS 等级分类
Kubernetes 中如果一个 Node 节点上的 Pod 占用资源过多并且不断飙升导致 Node 节点资源不足，可能会导致为了保证节点可用，将容器被杀掉。在遇见这种情况时候，我们希望先杀掉那些不太重要的容器，确保核心容器不会首先被杀掉。为了衡量先杀掉哪个程序，所以推出了优先级机制 QoS （Quality of Service）来做判断，Kubernetes 将容器划分为三种 QoS 等级

- Guaranteed： 完全可靠的
- Burstable： 较可靠的
- BestEffort： 不太可靠的


2、Kubernetes Pod QoS 特点  
在 Kubernetes 中资源不足时，根据 QoS 等级杀死 Pod 会有以下特点：

- BestEffort Pod： 优先级最低，在 Kubernetes 资源不足时候会将此 Pod 先杀掉。
- Burstable Pod： 优先级居中，如果整个系统内存资源不足，且已经杀完全部 BestEffort 等级的 Pod 时可能被杀掉。
- Guaranteed Pod： 优先级最高，一般情况下不会被杀掉，除非资源不足且系统 BestEffort 和 Burstable 的 Pod 都不存在的情

3、Pod 是如何分 QoS 等级
Kubernetes 中 Qos 等级是根据 Limits 和 Requests 这两个参数设置的值息息相关，Kubernetes 会根据这两个值的不同而给 Pod 设置不同的 QoS 等级

（1）、Guaranteed （等级-最高）  
 如果 Pod 中所有容器都定义了 Limits 和 Requests，并且全部容器的 Limits 值 = Requests 值（值不能为0），那么该 Pod 的 QoS 级别就是 Guaranteed。

注意：这种情况下容器可以只设置 Limits 值即可，引入在只设置 Limits 不设置 Requests 情况下，Requests 值默认等于 Limits 的值。

（2）、BestEffort（等级-最低）  
 如果 Pod 中所有容器都未定义 Requests 和 Limits 值，该 Pod 的 Qos 即为 BestEffort。

（3）、Burstable（等级-中等）  
  当一个 Pod 既不是 Guaranteed 级别，也不说 BestEffort 级别时候，该 Pod 的 QoS 级别就是 Burstable。例如，Pod 中全部或者部分容器 Requests 和 Limits 都定义，且 Requests 小于 Limits 值，或者 Pod 中一部分容器未定义 Requests 和 Limits 资源时

4、三种 Qos 的示例

（1）、Guaranteed

每个容器都设置 Limits 而不设置 Requests：
```
containers:
  - name: example-container1
    resources:
      limits:
        cpu: 10m
        memory: 512Mi
  - name: example-container2
    resources:
      limits:
        cpu: 100m
        memory: 100Mi
```
每个容器都设置 Limits 值和 Requests 值都相等：
```
containers:
  - name: example-container1
    resources:
      limits:
        cpu: 100m
        memory: 512Mi
      requests:
        cpu: 100
        memory: 512Mi
  - name: example-container2
    resources:
      limits:
        cpu: 200m
        memory: 256Mi
      requests:
        cpu: 200
        memory: 256Mi
```
（2）、BestEffort

Pod 中的所有容器都未定义 Requests 和 Limits：
```
containers:
  - name: example-container1
    resources:
  - name: example-container2
    resources:
```
（3）、Burstable

Pod 中只要有一个容器的 Requests 和 Limits 的设置的值不相同：
```
containers:
  - name: example-container1
    resources:
      limits:
        cpu: 100m
        memory: 512Mi
      requests:
        cpu: 100
        memory: 512Mi
  - name: example-container2
    resources:
      limits:
        cpu: 200m
        memory: 256Mi
      requests:
        cpu: 100
        memory: 128Mi
```
Pod 都存在 Limits，但是 Limits 中限制的类型不同：
```
containers:
  - name: example-container1
    resources:
      limits:
        memory: 512Mi
  - name: example-container2
    resources:
      limits:
        cpu: 200m
```
Pod 中两个容器只有一个 Limits ，另一个都没有设置：
```
containers:
  - name: example-container1
    resources:
      limits:
        cpu: 100m
        memory: 512Mi
      requests:
        cpu: 100
        memory: 512Mi
  - name: example-container2
    resources:
```

二、资源范围管理对象 LimitRange
---
默认情况下如果创建一个 Pod 没有设置 Limits 和 Requests 对其加以限制，那么这个 Pod 可能能够使用 Kubernetes 集群中全部资源， 但是每创建 Pod 资源时都加上这个动作是繁琐的，考虑到这点 Kubernetes 提供了 LimitRange 对象，它能够对一个 Namespace 下的全部 Pod 使用资源设置默认值、并且设置上限大小和下限大小等操作。这里演示将使用 LimitRange 来限制某个 namespace 下的资源的测试用例。
  
1、创建测试用的 Namespace  
考虑到 LimitRange 是作用于 Namespace 的，所以这里提前创建一个用于测试的 Namespace
```
$ kubectl create namespace limit-namespace
```
2、创建 LimitRange 对 Namespace 资源限制

创建一个 LimitRange 对象限制 Namespace 下的资源使用，其中 limit 的类型有两种：
- 对 Container 使用资源进行限制，在 Pod 中的每一个容器都受此限制。
- 对 Pod 进行限制，即 Pod 中全部 Container 使用资源总和来进行限制。

资源对象 limit-range.yaml 内容如下：
```
apiVersion: v1
kind: LimitRange
metadata:
  name: limit-test
spec:
  limits:
    - type: Pod        #对Pod中所有容器资源总和进行限制
      max:
        cpu: 4000m
        memory: 2048Mi 
      min:
        cpu: 10m
        memory: 128Mi 
      maxLimitRequestRatio:
        cpu: 5
        memory: 5
    - type: Container  #对Pod中所有容器资源进行限制
      max:
        cpu: 2000m
        memory: 1024Mi
      min:
        cpu: 10m
        memory: 128Mi 
      maxLimitRequestRatio:
        cpu: 5
        memory: 5
      default:
        cpu: 1000m
        memory: 512Mi
      defaultRequest:
        cpu: 500m
        memory: 256Mi
```
注意：LimitRange 类型为 Pod 中，不能设置 Default。

执行 Kubectl 创建 LimitRange：
```
$ kubectl apply -f limit-range.yaml -n limit-namespace
```

3、查看创建后的 LimitRange
```
$ kubectl describe limitrange limit-test -n limit-namespace

Name:       limit-test
Namespace:  limit-namespace
Type        Resource  Min    Max  Default Request  Default Limit  Max Limit/Request Ratio
----        --------  ---    ---  ---------------  -------------  -----------------------
Pod         cpu       10m    4    -                -              5
Pod         memory    128Mi  2Gi  -                -              5
Container   cpu       10m    2    500m             1              5
Container   memory    128Mi  1Gi  256Mi            512Mi          5
```
可以看到上面 LimitRange 对象中的配置可以了解到，如果容器使用默认值，则容器的 Request 和 Limits 一致。

4、对 LimitRange 对象参数介绍

Container 参数：
- max： Pod 中所有容器的 Requests 值下限。
- min： Pod 中所有容器的 Limits 值上限。
- default： Pod 中容器未指定 Limits 时，将此值设置为默认值。
- defaultRequest： Pod 中容器未指定 Requests 是，将此值设置为默认值。
- maxLimitRequestRatio： Pod 中的容器设置 Limits 与 Requests 的比例的值不能超过 maxLimitRequestRatio 参数设置的值，即 Limits/Requests ≤ maxLimitRequestRatio。

Pod 参数：
- max： Pod 中所有容器资源总和值上限。
- min： Po 中所有容器资源总和值下限。
- maxLimitRequestRatio： Pod 中全部容器设置 Limits 总和与 Requests 总和的比例的值不能超过 maxLimitRequestRatio 参数设置的值，即 (All Container Limits)/(All Container Requests) ≤ maxLimitRequestRatio。

5、创建 Pod 来进行测试

（1）、Container 默认值测试

创建下面 Pod 对象，并观察创建后是否有默认的资源限制。
```
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
  - name: nginx1
    image: nginx:latest
```
查看 Pod 的描述信息，可以看到 Limits 和 Requests 的值和上面 LimitRange 中配置的默认值一致。
```
Containers:
  nginx1:
    Limits:
      cpu:     1000m
      memory:  512Mi
    Requests:
      cpu:     500m
      memory:  256Mi
```
（2）、Container Max 限制测试

上面设置 Max 中 CPU 和 Memory 的值分别为 2000m 与 1024Mi，下面创建一个 Pod 并设置其中某一个容器 limits 值超过 LimitRange 中设置的值，查看是否能起到限制作用。Pod 内容如下：
```
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
  - name: nginx1
    image: nginx:latest
  - name: nginx2
    image: nginx:latest
    resources:
      limits:
        cpu: "3000m"
        memory: "512Mi"
```
执行 Kubectl 命令创建 Pod 时并没有通过验证，并且已经提示 CPU 不能超过 2 个：
```
$ kubectl apply -f test.yaml -n limit-namespace

Error from server (Forbidden): error when creating "test.yaml": 
pods "test" is forbidden: maximum cpu usage per Container is 2, but limit is 3.
```
（3）、Container Min 限制测试

上面设置 Min 中 CPU 和 Memory 的值分别为 10m 与 128Mi，下面创建一个 Pod 并设置其中某一个容器 Requests 值小于 LimitRange 中设置的值，是否能起到限制作用。Pod 内容如下：
```
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
  - name: nginx1
    image: nginx:latest
  - name: nginx2
    image: nginx:latest
    resources:
      requests:
        cpu: "100m"
        memory: "64Mi"
```
执行 Kubectl 命令创建 Pod 时并没有通过验证，并且已经提示 Memory 不能低于 128Mi 大小：
```
$ kubectl apply -f test.yaml -n limit-namespace

Error from server (Forbidden): error when creating "test.yaml": pods "test" is forbidden: 
[minimum memory usage per Container is 128Mi, but request is 64Mi.
, cpu max limit to request ratio per Container is 5, but provided ratio is 10.000000.
, memory max limit to request ratio per Container is 5, but provided ratio is 8.000000.]
```
（4）、Container MaxLimitRequestRatio 限制测试

上面 LimitRange 中设置 maxLimitRequestRatio 值为 5，就是限制 Pod 中容器 CPU 和 Memory 的 limit/request 的值小于 5,这里测试一下设置内存 limit/request 中值超过 5 创建 Pod 是否会报错。Pod 内容如下：
```
apiVersion: v1
kind: Pod
metadata:
  name: test
spec:
  containers:
  - name: nginx1
    image: nginx:latest
  - name: nginx2
    image: nginx:latest
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "200m"
        memory: "1024Mi"
```
执行 Kubectl 命令创建 Pod 时并没有通过验证，并且已经提示 limit/request ratio 为 8，超过了限制的值 5：
```
$ kubectl apply -f test.yaml -n limit-namespace

Error from server (Forbidden): error when creating "test.yaml": 
pods "test" is forbidden: memory max limit to request ratio per Container is 5, but provided ratio is 8.000000.
```

三、资源配额管理对象 ResourcesQuota
---
Kubernetes 是一个多租户平台，更是一个镜像集群管理工具。一个 Kubernetes 集群中的资源一般是由多个团队共享的，这时候经常要考虑的是如何对这个整体资源进行分配。在 kubernetes 中提供了 Namespace 来讲应用隔离，那么是不是也能将资源的大小跟 Namespace 挂钩进行一起隔离呢？这当然是可以的，Kubernetes 提供了 Resources Quotas 工具，让集群管理员可以创建 ResourcesQuota 对象管理这个集群整体资源的配额，它可以限制某个 Namespace 下计算资源的使用量，也可以设置某个 Namespace 下某种类型对象的上限等。

上面说白了就是，通过设置不同的 Namespace 与对应的 RBAC 权限将各个团队隔离，然后通过 ResourcesQuota 对象来现在该 Namespace 能够拥有的资源的多少。

1、开启资源配额 ResourceQuota

ResourceQuota 对象一般在 Kubernetes 中是默认开启的，如果未开启且不能创建该对象，那么可以进入 Master 的 Kubernetes 配置目录修改 Apiserver 配置文件 kube-apiserver.yaml，在添加参数 --admission-control=ResourceQuota 来开启。
```
spec:
  containers:
  - command:
    - kube-apiserver
    - --advertise-address=192.168.2.11
    - --allow-privileged=true
    - --authorization-mode=Node,RBAC
    - --admission-control=ResourceQuota    #开启ResourceQuota
    - ......
```
注意：一个 Namespace 中可以拥有多个 ResourceQuota 对象。

2、配额资源类型
- 计算资源配额： 限制一个 Namespace 中所有 Pod 的计算资源（CPU、Memory）的总和。
- 存储资源配额： 限制一个 Namespace 中所有存储资源的总量。
- 对象数量配额： 限制一个 Namespace 中指定类型对象的数量。

（1）、ResourcesQuota 支持的计算资源：
- cpu： 所有非终止状态的Pod中，其CPU需求总量不能超过该值。
- limits.cpu： 所有非终止状态的Pod中，其CPU限额总量不能超过该值。
- limits.memory： 所有非终止状态的Pod中，其内存限额总量不能超过该值。
- memory： 所有非终止状态的Pod中，其内存需求总量不能超过该值。
- requests.cpu： 所有非终止状态的Pod中，其CPU需求总量不能超过该值。
- requests.memory： 所有非终止状态的Pod中，其内存需求总量不能超过该值。

（2）、ResourcesQuota 支持限制的存储资源：
- requests.storage：所有 PVC 请求的存储大小总量不能超过此值。
- Persistentvolumeclaims： PVC 对象存在的最大数目。
- .storageclass.storage.k8s.io/requests.storage： 和 StorageClass 关联的 PVC 的请求存储的量大小不能超过此设置的值。
- .storageclass.storage.k8s.io/persistentvolumeclaims： 和 StorageClass 关联的 PVC 的总量。

（3）、ResourcesQuota 支持限制的对象资源：
- Configmaps： 允许存在的 ConfigMap 的数量。
- Pods： 允许存在的非终止状态的 Pod 数量，如果 Pod 的 status.phase 为 Failed 或 Succeeded ， 那么其处于终止状态。
- Replicationcontrollers： 允许存在的 Replication Controllers 的数量。
- Resourcequotas： 允许存在的 Resource Quotas 的数量。
- Services： 允许存在的 Service 的数量。
- services.loadbalancers： 允许存在的 LoadBalancer 类型的 Service 的数量。
- services.nodeports： 允许存在的 NodePort 类型的 Service 的数量。
- Secrets： 允许存在的 Secret 的数量。

3、配额作用域
每个配额都有一组相关的作用域（scope），配额只会对作用域内的资源生效。当一个作用域被添加到配额中后，它会对作用域相关的资源数量作限制，如配额中指定了允许（作用域）集合之外的资源，会导致验证错误。
- Terminating： 匹配 spec.activeDeadlineSeconds ≥ 0 的 Pod。
- NotTerminating： 匹配 spec.activeDeadlineSeconds 是 nil（空） 的 Pod。
- BestEffort： 匹配所有 QoS 等级是 BestEffort 级别的 Pod。
- NotBestEffort： 匹配所有 QoS 等级不是 BestEffort 级别的 Pod。

BestEffort 作用域限制配额跟踪以下资源：
- pods

Terminating、 NotTerminating 和 NotBestEffort 限制配额跟踪以下资源：
- cpu
- limits.cpu
- limits.memory
- memory
- pods
- requests.cpu
- requests.memory

4、ResourceQuota 使用示例

（1）、设置某 Namespace 计算资源的配额

创建 resources-test1.yaml 用于设置计算资源的配额：
```
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
spec:
  hard:
    pods: "4"
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
```
创建该配额对象：

-n：指定限制配额的 namespace
```
$ kubectl apply -f resources-test1.yaml -n limit-namespace
```
查看创建后的 ResourcesQuota 配额的详细信息:
```
$ kubectl describe quota compute-resources -n limit-namespace

Name:            compute-resources
Namespace:       limit-namespace
Resource         Used   Hard
--------         ----   ----
limits.cpu       2      2
limits.memory    1Gi    2Gi
pods             2      4
requests.cpu     2      1
requests.memory  512Mi  1Gi
```
（2）、设置某 Namespace 对象数量的配额

创建 resources-test2.yaml 用于设置对象数量的配额：
```
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
spec:
  hard:
    configmaps: "10"
    persistentvolumeclaims: "4"
    replicationcontrollers: "20"
    secrets: "10"
    services: "10"
    services.loadbalancers: "2"
```
创建该配额对象：
```
$ kubectl apply -f resources-test2.yaml -n limit-namespace
```
查看创建后的 ResourcesQuota 配额的详细信息:
```
$ kubectl describe quota object-counts -n limit-namespace

Name:                   object-counts
Namespace:              limit-namespace
Resource                Used  Hard
--------                ----  ----
configmaps              0     10
persistentvolumeclaims  0     4
replicationcontrollers  0     20
secrets                 1     10
services                0     10
services.loadbalancers  0     2
```
（3）、限制 Namespace 下 Pod 数量并只作用域 BestEffort

创建 resources-test3.yaml 用于设置 Pod 对象数量的配额，并设置作用域 BestEffort：
```
apiVersion: v1
kind: ResourceQuota
metadata:
  name: besteffort
spec:
  hard:
    pods: "5"
  scopes:
  - BestEffort
```
创建该配额对象：
```
$ kubectl apply -f resources-test3.yaml -n limit-namespace
```
查看创建后的 ResourcesQuota 配额的详细信息:
```
$ kubectl describe quota besteffort -n limit-namespace

Name:       besteffort
Namespace:  limit-namespace
Scopes:     BestEffort
 * Matches all pods that do not have resource requirements set. These pods have a best effort quality of service.
Resource  Used  Hard
--------  ----  ----
pods      0     5
```
上面配额对象创建完成后，可以创建几个 Pod 对其配额规则进行验证。

在实际使用过程中应当统计集群资源总量，然后按需分配给各个 Namespace 一定配额，如果想限制 Pod 使用资源的大小，就可以创建 LimitRange 来完成这个限制规则。最后说一句，创建 Pod 时候最好考虑好 Pod 的 QoS 优先级。
