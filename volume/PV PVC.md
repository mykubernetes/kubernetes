官方提供示例  
https://github.com/mykubernetes/examples/tree/master/staging/volumes  

PV PVC  
https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes  

https://github.com/kubernetes-incubator/external-storage
---

一、存储机制介绍
---
在 Kubernetes 中，存储资源和计算资源(CPU、Memory)同样重要，Kubernetes 为了能让管理员方便管理集群中的存储资源，同时也为了让使用者使用存储更加方便，所以屏蔽了底层存储的实现细节，将存储抽象出两个 API 资源 PersistentVolume 和 PersistentVolumeClaim 对象来对存储进行管理。

- PersistentVolume（持久化卷）： PersistentVolume 简称 PV， 是对底层共享存储的一种抽象，将共享存储定义为一种资源，它属于集群级别资源，不属于任何 Namespace，用户使用 PV 需要通过 PVC 申请。PV 是由管理员进行创建和配置，它和具体的底层的共享存储技术的实现方式有关，比如说 Ceph、GlusterFS、NFS 等，都是通过插件机制完成与共享存储的对接，且根据不同的存储 PV 可配置参数也是不相同。

- PersistentVolumeClaim（持久化卷声明）： PersistentVolumeClaim 简称 PVC，是用户存储的一种声明，类似于对存储资源的申请，它属于一个 Namespace 中的资源，可用于向 PV 申请存储资源。PVC 和 Pod 比较类似，Pod 消耗的是 Node 节点资源，而 PVC 消耗的是 PV 存储资源，Pod 可以请求 CPU 和 Memory，而 PVC 可以请求特定的存储空间和访问模式。

![](https://mydlq-club.oss-cn-beijing.aliyuncs.com/images/kubernetes-storage-1002.jpg?x-oss-process=style/shuiyin)

上面两种资源 PV 和 PVC 的存在很好的解决了存储管理的问题，不过这些存储每次都需要管理员手动创建和管理，如果一个集群中有很多应用，并且每个应用都要挂载很多存储，那么就需要创建很多 PV 和 PVC 与应用关联。为了解决这个问题 Kubernetes 在 1.4 版本中引入了 StorageClass 对象。

当我们创建 PVC 时指定对应的 StorageClass 就能和 StorageClass 关联，StorageClass 会交由与他关联 Provisioner 存储插件来创建与管理存储，它能帮你创建对应的 PV 和在远程存储上创建对应的文件夹，并且还能根据设定的参数，删除与保留数据。所以管理员只要在 StorageClass 中配置好对应的参数就能方便的管理集群中的存储资源。

二、PersistentVolume 详解
---
1、PV 支持存储的类型

PersistentVolume 类型实现为插件,目前 Kubernetes 支持以下插件：

- RBD：Ceph 块存储。
- FC：光纤存储设备。
- NFS：网络问卷存储卷。
- iSCSI：iSCSI 存储设备。
- CephFS：开源共享存储系统。
- Flocker：一种开源共享存储系统。
- Glusterfs：一种开源共享存储系统。
- Flexvolume：一种插件式的存储机制。
- HostPath：宿主机目录，仅能用于单机。
- AzureFile：Azure 公有云提供的 File。
- AzureDisk：Azure 公有云提供的 Disk。
- ScaleIO Volumes：DellEMC 的存储设备。
- StorageOS：StorageOS 提供的存储服务。
- VsphereVolume：VMWare 提供的存储系统。
- Quobyte Volumes：Quobyte 提供的存储服务。
- Portworx Volumes：Portworx 提供的存储服务。
- GCEPersistentDisk：GCE 公有云提供的 PersistentDisk。
- AWSElasticBlockStore：AWS 公有云提供的 ElasticBlockStore。

2、PV 的生命周期

PV 生命周期总共四个阶段：
- Available： 可用状态，尚未被 PVC 绑定。
- Bound： 绑定状态，已经与某个 PVC 绑定。
- Failed： 当删除 PVC 清理资源，自动回收卷时失败，所以处于故障状态。
- Released： 与之绑定的 PVC 已经被删除，但资源尚未被集群回收。

3、基于 NFS 的 PV 示例
Kubernetes 支持多种存储，这里使用最广泛的 NFS 存储
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv1
  label:
    app: example
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  storageClassName: slow
  mountOptions:
    - hard
    - nfsvers=4.1
  nfs:
    path: /nfs/space
    server: 192.168.2.11
```

4、PV 的常用配置参数

（1）、存储能力 （capacity）

PV 可以通过配置 capacity 中的 storage 参数，对 PV 挂多大存储空间进行设置

目前 capacity 只有一个设置存储大小的选项，未来可能会增加。
```
capacity:
    storage: 5Gi
```
（2）、存储卷模式（volumeMode）

PV 可以通过配置 volumeMode 参数，对存储卷类型进行设置，可选项包括：

- Filesystem： 文件系统，默认是此选项。
- Block： 块设备

目前 Block 模式只有 AWSElasticBlockStore、AzureDisk、FC、GCEPersistentDisk、iSCSI、LocalVolume、RBD、VsphereVolume 等支持）。
```
volumeMode: Filesystem
```
（3）、访问模式（accessModes）

PV 可以通过配置 accessModes 参数，设置访问模式来限制应用对资源的访问权限，有以下机制访问模式：
- ReadWriteOnce（RWO）： 读写权限，只能被单个节点挂载。
- ReadOnlyMany（ROX）： 只读权限，允许被多个节点挂载读。
- ReadWriteMany（RWX）： 读写权限，允许被多个节点挂载。
```
accessModes:
  - ReadWriteOnce
```

不过不同的存储所支持的访问模式也不相同，具体如下：

| Volume Plugin |	ReadWriteOnce |	ReadOnlyMany |	ReadWriteMany |
| :------: | :--------: | :------: | :--------: |
| AWSElasticBlockStore | √ | - |	- |
| AzureFile |	√ |	√ |	√ |
| AzureDisk	√ |	-	| - |
| CephFS |	√ |	√ |	√ |
| Cinder |	√ |	- |	- |
| FC |	√ |	√ |	- |
| FlexVolume |	√ |	√ |	- |
| Flocker |	√ |	- |	- |
| GCEPersistentDisk |	√ |	√ |	- |
| GlusteFS |	√ |	√ |	√ |
| HostPath |	√ |	- |	- |
| iSCSI |	√ |	√ |	- |
| PhotonPersistentDisk |	√ |	- |	- |
| Quobyte |	√ |	√ |	√ |
| NFS |	√ |	√ |	√ |
| RBD |	√ |	√ |	- |
| VsphereVolume |	√ |	- |	- |
| PortworxVolume |	√ |	- |	√ |
| ScaleIO |	√ |	√ |	- |
| StorageOS |	√ |	- |	- |

（4）、挂载参数（mountOptions）

PV 可以根据不同的存储卷类型，设置不同的挂载参数，每种类型的存储卷可配置参数都不相同。如 NFS 存储，可以设置 NFS 挂载配置，如下：

下面例子只是 NFS 支持的部分参数，其它参数请自行查找 NFS 挂载参数。
```
mountOptions:
  - hard
  - nfsvers=4.1
```
（5）、存储类 （storageClassName）

PV 可以通过配置 storageClassName 参数指定一个存储类 StorageClass 资源，具有特定 StorageClass 的 PV 只能与指定相同 StorageClass 的 PVC 进行绑定，没有设置 StorageClass 的 PV 也是同样只能与没有指定 StorageClass 的 PVC 绑定。
```
storageClassName: slow
```
（6）、回收策略（persistentVolumeReclaimPolicy）

PV 可以通过配置 persistentVolumeReclaimPolicy 参数设置回收策略，可选项如下：

- Retain（保留）： 保留数据，需要由管理员手动清理。
- Recycle（回收）： 删除数据，即删除目录下的所有文件，比如说执行 rm -rf /thevolume/* 命令，目前只有 NFS 和 HostPath 支持。
- Delete（删除）： 删除存储资源，仅仅部分云存储系统支持，比如删除 AWS EBS 卷，目前只有 AWS EBS，GCE PD，Azure 磁盘和 Cinder 卷支持删除。
```
persistentVolumeReclaimPolicy: Recycle
```


三、PersistentVolumeClaim 详解
---
1、PVC 示例
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc1
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem
  resources:
    requests:
      storage: 8Gi
  storageClassName: slow
  selector:
    matchLabels:
      release: "stable"
    matchExpressions:
      - key: environment
        operator: In
        values: dev
```
2、PVC 的常用配置参数
（1）、筛选器（selector）

PVC 可以通过在 Selecter 中设置 Laberl 标签，筛选出带有指定 Label 的 PV 进行绑定。Selecter 中可以指定 matchLabels 或 matchExpressions，如果两个字段都设定了就需要同时满足才能匹配。
```
selector:
  matchLabels:
    release: "stable"
  matchExpressions:
    - key: environment
      operator: In
      values: dev
```
（2）、资源请求（resources）

PVC 设置目前只有 requests.storage 一个参数，用于指定申请存储空间的大小。
```
resources:
  requests:
    storage: 8Gi
```
（3）、存储类（storageClass）

PVC 要想绑定带有特定 StorageClass 的 PV 时，也必须设定 storageClassName 参数，且名称也必须要和 PV 中的 storageClassName 保持一致。如果要绑定的 PV 没有设置 storageClassName 则 PVC 中也不需要设置。

当 PVC 中如果未指定 storageClassName 参数或者指定为空值，则还需要考虑 Kubernetes 中是否设置了默认的 StorageClass：

- 未启用 DefaultStorageClass：等于 storageClassName 值为空。
-  启用 DefaultStorageClass：等于 storageClassName 值为默认的 StorageClass。

- 如果设置 storageClassName=""，则表示该 PVC 不指定 StorageClass。
```
storageClassName: slow
```
（4）、访问模式（accessModes）

PVC 中可设置的访问模式与 PV 种一样，用于限制应用对资源的访问权限。

（5）、存储卷模式（volumeMode）

PVC 中可设置的存储卷模式与 PV 种一样，分为 Filesystem 和 Block 两种。

四、StorageClass 详解
---
1、StorageClass 示例

这里使用 NFS 存储，创建 StorageClass 示例：
```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "true" #设置为默认的 StorageClass
provisioner: nfs-client
mountOptions: 
  - hard
  - nfsvers=4
parameters:
  archiveOnDelete: "true"
```
2、StorageClass 的常用配置参数

（1）、提供者（provisioner）

在创建 StorageClass 之前需要 Kubernetes 集群中存在 Provisioner（存储分配提供者）应用，如 NFS 存储需要有 NFS-Provisioner （NFS 存储分配提供者）应用，如果集群中没有该应用，那么创建的 StorageClass 只能作为标记,而不能提供创建 PV 的作用。

NFS 的存储 NFS Provisioner 可以参考：创建 NFS-Provisioner 博文
```
provisioner: nfs-client
```
（2）、参数（parameters）

后端存储提供的参数，不同的 Provisioner 可与配置的参数也是不相同。例如 NFS Provisioner 可与提供如下参数：
```
parameters:
  archiveOnDelete: "true" #删除 PV 后是否保留数据
```
（3）、挂载参数（mountOptions）

在 StorageClass 中，可以根据不同的存储来指定不同的挂载参数，此参数会与 StorageClass 绑定的 Provisioner 创建 PV 时，将此挂载参数与创建的 PV 关联。
```
mountOptions: 
  - hard
  - nfsvers=4
```
（4）、设置默认的 StorageClass

可与在 Kubernetes 集群中设置一个默认的 StorageClass，这样当创建 PVC 时如果未指定 StorageClass 则会使用默认的 StorageClass。
```
metadata:
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
```

五、PV 和 PVC 的生命周期
---
PV 是 Kubernetes 集群的存储资源，而 PVC 则是对存储资源的需求，创建 PVC 需要对 PV 发起使用申请，即和 PV 进行绑定。 PV 和 PVC 是一一对应的关系，它们二者的交互遵循如下生命周期：

![](https://mydlq-club.oss-cn-beijing.aliyuncs.com/images/kubernetes-storage-1003.png?x-oss-process=style/shuiyin)

1、存储供给

存储供给（Provisioning）是指为 PVC 准备可用的 PV 的一种机制。Kubernetes 支持 PV 供给方式有 静态供给 和 动态供给 两种：
- 静态供给： 指由集群管理员手动创建一定数量的 PV，创建 PV 时需要根据后端存储的不同，配置的参数也不同。
- 动态供给： 指不需要集群管理员手动创建 PV，将 PV 的创建工作交由 StorageClass 关联的 Provisioner 进行创建，会根据存储的不同自动配置相关的参数。创建完成 PV 后系统会自动将 PVC 与其绑定。

2、存储绑定

在静态模式下，在用户定义好 PVC 后，Kubernetes 将根据 PVC 提出的“申请空间的大小”、“访问模式”从集群中寻找已经存在且满足条件的 PV 进行绑定，如果集群中没有匹配的 PV 则 PVC 将处于 Pending 等待状态，知道系统创建了符合条件的 PV 再与其绑定。PV 与 PVC 绑定后就不能和别的 PVC 进行绑定。

在动态模式下，当创建 PVC 并且指定 StorageClass 后，与 StorageClass 关联的存储插件会自动创建对应的 PV 与该 PVC 进行绑定。

3、存储回收

完成存储卷的使用目标之后删除 PVC 对象，以便进行资源回收。不过，至于如何操作则取决于 PV 的回收策略 ，目前有三种策略：

- 保存策略（Retain）： 删除 PVC 之后，Kubernetes 系统不会自动删除 PV ，而仅是将它标识为 Released 状态，不过处于 Released 状态的 PV **不能被其他 PVC 申请所绑定，因为之前 PVC 绑定的应用数据仍然存在，需要由管理员手动清理数据，然后决定如何处理 PV 的使用。
- 回收策略： 当 PVC 删除后，此 PV 变成 Available 可用状态。不过此策略需要后端存储插件的支持。
- 删除策略： 当删除 PVC 后 PV 和存储中的数据会被立即删除，不过此策略也需要后端存储插件的支持。

六、PVC 使用示例
---
Deployment 中使用 PVC

一般 Deployment 中使用 PVC，大部分都是静态供给方式创建，即先创建 PV，再创建 PVC 与 PV 绑定，在设置应用于 PVC 关联。

下面是一个 NFS 存储创建 PV 的例子，如下：
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nginx-pv
  labels:
    app: nginx-pv
spec:
  accessModes:       
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  capacity:          
    storage: 1Gi
  mountOptions:
  - hard  
  - nfsvers=4.1  
  nfs:
    server: 192.168.2.11
    path: /nfs/data/nginx
```
创建 PVC 与 PV 进行关联绑定：
```
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: nginx-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  selector:
    matchLabels:
      app: nginx-pv
```
创建应用于 PVC 进行关联：
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      terminationGracePeriodSeconds: 1
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - name: server
          containerPort: 80
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: nginx-pvc
```
StatefulSet 中使用 PVC
---
在有状态的应用中，我们经常使用动态供给方式创建 PV 和 PVC，不过提前需要集群拥有:

- StorageClass：存储类
- Provisioner：与存储类关联的管理后端存储的插件

只有拥有上面两种资源同时存在时才能使用动态存储，本人这里使用的是 NFS 存储，关于如何创建 NFS Provisioner 可以查看 NFS Provisioner 一文，假如 Kubernetes 集群中使用 NFS 存储，且存在 Provisioner 的名称为 nfs-client 那就可以下面创建 StorageClass 示例：
```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: nfs-client
parameters:
  archiveOnDelete: "true"
mountOptions: 
  - hard
  - nfsvers=4
```
然后 StatefulSet 可以按下方式，在 volumeClaimTemplates 参数中指定使用的 StorageClass，然后与 StorageClass 关联的 NFS Provisioner 会执行创建 PVC 和 PV，然后两者进行绑定，下面是 StatefulSet 方式使用 volumeClaimTemplates挂载存储的示例：
```
apiVersion: v1
kind: Service
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None
  selector:
    app: nginx
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  selector:
    matchLabels:
      app: nginx
  serviceName: "nginx"
  replicas: 3
  template:
    metadata:
      labels:
        app: nginx
    spec:
      terminationGracePeriodSeconds: 1
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "nfs-storage"
      resources:
        requests:
          storage: 1Gi
```
