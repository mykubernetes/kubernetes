官方提供示例  
https://github.com/mykubernetes/examples/tree/master/staging/volumes  

PV PVC  
https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes  

https://github.com/kubernetes-incubator/external-storage
---

一、存储机制介绍  
在 Kubernetes 中，存储资源和计算资源(CPU、Memory)同样重要，Kubernetes 为了能让管理员方便管理集群中的存储资源，同时也为了让使用者使用存储更加方便，所以屏蔽了底层存储的实现细节，将存储抽象出两个 API 资源 PersistentVolume 和 PersistentVolumeClaim 对象来对存储进行管理。

- PersistentVolume（持久化卷）： PersistentVolume 简称 PV， 是对底层共享存储的一种抽象，将共享存储定义为一种资源，它属于集群级别资源，不属于任何 Namespace，用户使用 PV 需要通过 PVC 申请。PV 是由管理员进行创建和配置，它和具体的底层的共享存储技术的实现方式有关，比如说 Ceph、GlusterFS、NFS 等，都是通过插件机制完成与共享存储的对接，且根据不同的存储 PV 可配置参数也是不相同。

- PersistentVolumeClaim（持久化卷声明）： PersistentVolumeClaim 简称 PVC，是用户存储的一种声明，类似于对存储资源的申请，它属于一个 Namespace 中的资源，可用于向 PV 申请存储资源。PVC 和 Pod 比较类似，Pod 消耗的是 Node 节点资源，而 PVC 消耗的是 PV 存储资源，Pod 可以请求 CPU 和 Memory，而 PVC 可以请求特定的存储空间和访问模式。

![](https://mydlq-club.oss-cn-beijing.aliyuncs.com/images/kubernetes-storage-1002.jpg?x-oss-process=style/shuiyin)


1、访问模式
accessModes支持的访问模式有：
- ReadWriteOnce 缩写RWO read-write 单路读写
- ReadOnlyMany 缩写ROX read-only 多路只读
- ReadWriteMany 缩写RWX read-write 多路读写

2、回收策略
persistentVolumeReclaimPolicy支持的策略有：
- Retain (保留) 需要管理员手工回收。
- Recycle (回收) PV 中的数据，效果相当于执行 rm -rf /thevolume/*。
- Delete (清除) 关联的存储资产（例如 AWS EBS、GCE PD、Azure Disk 和 OpenStack Cinder 卷）将被删除
当前，只有 NFS 和 HostPath 支持回收策略。AWS EBS、GCE PD、Azure Disk 和 Cinder 卷支持删除策略  

3、pv状态
- Available （可用）空闲状态。
- Bound （已绑定）已经绑定到某个PVC上。
- Released （已释放）对应的PVC已经被删除，但资源还没有被集群收回。
- Failed （失败）PV自动回收失败。


4、hostPath卷指定type类型有多种  

| 值  | 行为 |
| :------: | :--------: |
|   | 空字符串（默认）用于向后兼容，这意味着在挂载 hostPath 卷之前不会执行任何检查 |
| DirectoryOrCreate | 如果在给定的路径上没有任何东西存在，那么将根据需要在那里创建一个空目录，权限设置为 0755，与 Kubelet 具有相同的组和所有权 |
| Directory | 给定的路径下必须存在目录 |
| FileOrCreate | 如果在给定的路径上没有任何东西存在，那么会根据需要创建一个空文件，权限设置为 0644，与 Kubelet 具有相同的组和所有权 |
| File | 给定的路径下必须存在文件 |
| Socket | 给定的路径下必须存在 UNIX 套接字 |
| CharDevice | 给定的路径下必须存在字符设备 |
| BlockDevice | 给定的路径下必须存在块设备 |

hostPath示例
```
apiVersion: v1
kind: Pod
metadata:
  name: test-pd
spec:
  containers:
  - image: k8s.gcr.io/test-webserver
    name: test-container
    volumeMounts:
    - mountPath: /test-pd
      name: test-volume
  volumes:
  - name: test-volume
    hostPath:
      # directory location on host
      path: /data
      # this field is optional
      type: Directory
```  
