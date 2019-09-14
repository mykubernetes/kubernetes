官方提供示例  
https://github.com/mykubernetes/examples/tree/master/staging/volumes  

PV PVC  
https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes  


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
