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
