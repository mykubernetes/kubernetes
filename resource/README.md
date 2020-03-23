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
