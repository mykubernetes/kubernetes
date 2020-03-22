Pod 两种探针简介
---
- LivenessProbe（存活探针） 存活探针主要作用是，用指定的方式进入容器检测容器中的应用是否正常运行，如果检测失败，则认为容器不健康，那么 Kubelet 将根据 Pod 中设置的 restartPolicy （重启策略）来判断，Pod 是否要进行重启操作，如果容器配置中没有配置 livenessProbe 存活探针，Kubelet 将认为存活探针探测一直为成功状态。
- ReadinessProbe（就绪探针） 用于判断容器中应用是否启动完成，当探测成功后才使 Pod 对外提供网络访问，设置容器 Ready 状态为 true，如果探测失败，则设置容器的 Ready 状态为 false。对于被 Service 管理的 Pod，Service 与 Pod、EndPoint 的关联关系也将基于 Pod 是否为 Ready 状态进行设置，如果 Pod 运行过程中 Ready 状态变为 false，则系统自动从 Service 关联的 EndPoint 列表中移除，如果 Pod 恢复为 Ready 状态。将再会被加回 Endpoint 列表。通过这种机制就能防止将流量转发到不可用的 Pod 上。

pod三种健康检查
---
- ExecAction： 在容器中执行指定的命令，如果能成功执行，则探测成功。
- HTTPGetAction： 通过容器的IP地址、端口号及路径调用 HTTP Get 方法，如果响应的状态码 200 ≤ status ≤ 400，则认为容器探测成功。
- TCPSocketAction： 通过容器的 IP 地址和端口号执行 TCP 检查，如果能够建立 TCP 连接，则探测成功。

探针探测结果有以下值：
---
- Success：表示通过检测。
- Failure：表示未通过检测。
- Unknown：表示检测没有正常进行。
