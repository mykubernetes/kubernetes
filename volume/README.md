官方提供示例  
https://github.com/mykubernetes/examples/tree/master/staging/volumes  

PV PVC  
https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes  


1、访问模式
accessModes 指定访问模式为 ReadWriteOnce，支持的访问模式有：
- ReadWriteOnce – PV 能以 read-write 模式 mount 到单个节点。
- ReadOnlyMany – PV 能以 read-only 模式 mount 到多个节点。
- ReadWriteMany – PV 能以 read-write 模式 mount 到多个节点。

2、回收策略
- persistentVolumeReclaimPolicy 指定当 PV 的回收策略为 Recycle，支持的策略有：
- Retain – 需要管理员手工回收。
- Recycle – 清除 PV 中的数据，效果相当于执行 rm -rf /thevolume/*。
- Delete – 删除 Storage Provider 上的对应存储资源，例如 AWS EBS、GCE PD、Azure Disk、OpenStack Cinder Volume 等。

3、pv状态
- Available：空闲状态。
- Bound：已经绑定到某个PVC上。
- Released：对应的PVC已经被删除，但资源还没有被集群收回。
- Failed：PV自动回收失败。


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
