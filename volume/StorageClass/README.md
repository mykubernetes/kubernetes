一、NFS Provisioner 简介

NFS Provisioner 是一个自动配置卷程序，它使用现有的和已配置的 NFS 服务器来支持通过持久卷声明动态配置 Kubernetes 持久卷。

- 持久卷被配置为：${namespace}-${pvcName}-${pvName}。

二、创建 NFS Server 端

部署 NFS 动态卷分配应用 “NFS Provisioner”，所以部署前请确认已经存在 NFS Server 端

这里 NFS Server 环境为：
- IP地址：192.168.2.11
- 存储目录：/nfs/data

三、创建 ServiceAccount

现在的 Kubernetes 集群大部分是基于 RBAC 的权限控制，所以创建一个一定权限的 ServiceAccount 与后面要创建的 “NFS Provisioner” 绑定，赋予一定的权限。

提前修改里面的 Namespace 值设置为要部署 “NFS Provisioner” 的 Namespace 名
```
vim nfs-rbac.yaml

kind: ServiceAccount
apiVersion: v1
metadata:
  name: nfs-client-provisioner
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: nfs-client-provisioner-runner
rules:
  - apiGroups: [""]
    resources: ["persistentvolumes"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: [""]
    resources: ["persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "update"]
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "update", "patch"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: run-nfs-client-provisioner
subjects:
  - kind: ServiceAccount
    name: nfs-client-provisioner
    namespace: kube-system      #替换成你要部署NFS Provisioner的 Namespace
roleRef:
  kind: ClusterRole
  name: nfs-client-provisioner-runner
  apiGroup: rbac.authorization.k8s.io
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: leader-locking-nfs-client-provisioner
rules:
  - apiGroups: [""]
    resources: ["endpoints"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: leader-locking-nfs-client-provisioner
subjects:
  - kind: ServiceAccount
    name: nfs-client-provisioner
    namespace: kube-system      #替换成你要部署NFS Provisioner的 Namespace
roleRef:
  kind: Role
  name: leader-locking-nfs-client-provisioner
  apiGroup: rbac.authorization.k8s.io
```
创建 RBAC
- -n: 指定应用部署的 Namespace
```
$ kubectl apply -f nfs-rbac.yaml -n kube-system
```
四、部署 NFS Provisioner

设置 NFS Provisioner 部署文件，这里将其部署到 “kube-system” Namespace 中。
```
# vim nfs-provisioner-deploy.yaml

kind: Deployment
apiVersion: apps/v1
metadata:
  name: nfs-client-provisioner
  labels:
    app: nfs-client-provisioner
spec:
  replicas: 1
  strategy:
    type: Recreate      #---设置升级策略为删除再创建(默认为滚动更新)
  selector:
    matchLabels:
      app: nfs-client-provisioner
  template:
    metadata:
      labels:
        app: nfs-client-provisioner
    spec:
      serviceAccountName: nfs-client-provisioner
      containers:
        - name: nfs-client-provisioner
          #---由于quay.io仓库国内被墙，所以替换为Azure仓库
          image: quay.azk8s.cn/external_storage/nfs-client-provisioner:latest 
          volumeMounts:
            - name: nfs-client-root
              mountPath: /persistentvolumes
          env:
            - name: PROVISIONER_NAME
              value: nfs-client     #--- nfs-provisioner的名称，以后设置的storageclass要和这个保持一致
            - name: NFS_SERVER
              value: 192.168.2.11   #---NFS服务器地址，和 valumes 保持一致
            - name: NFS_PATH
              value: /nfs/data      #---NFS服务器目录，和 valumes 保持一致
      volumes:
        - name: nfs-client-root
          nfs:
            server: 192.168.2.11    #---NFS服务器地址
            path: /nfs/data         #---NFS服务器目录
```
创建 NFS Provisioner
- -n: 指定应用部署的 Namespace
```
$ kubectl apply -f nfs-provisioner-deploy.yaml -n kube-system
```
五、创建 NFS SotageClass

创建一个 StoageClass，声明 NFS 动态卷提供者名称为 “nfs-storage”。
```
# vim nfs-storage.yaml

apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "true" #---设置为默认的storageclass
provisioner: nfs-client    #---动态卷分配者名称，必须和上面创建的"provisioner"变量中设置的Name一致
parameters:
  archiveOnDelete: "true"  #---设置为"false"时删除PVC不会保留数据,"true"则保留数据
mountOptions: 
  - hard        #指定为硬挂载方式
  - nfsvers=4   #指定NFS版本，这个需要根据 NFS Server 版本号设置
```
创建 StorageClass
```
$ kubectl apply -f nfs-storage.yaml
```
六、创建 PVC 和 Pod 进行测试
1、创建测试 PVC

在 “kube-public” Namespace 下创建一个测试用的 PVC 并观察是否自动创建是 PV 与其绑定。
```
# vim test-pvc.yaml

kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: test-pvc
spec:
  storageClassName: nfs-storage #---需要与上面创建的storageclass的名称一致
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Mi
```
创建 PVC
- -n：指定创建 PVC 的 Namespace
```
$ kubectl apply -f test-pvc.yaml -n kube-public
```
查看 PVC 状态是否与 PV 绑定

利用 Kubectl 命令获取 pvc 资源，查看 STATUS 状态是否为 “Bound”。
```
$ kubectl get pvc test-pvc -n kube-public

NAME       STATUS   VOLUME                 CAPACITY   ACCESS MODES   STORAGECLASS
test-pvc   Bound    pvc-be0808c2-9957-11e9 1Mi        RWO            nfs-storage
```
2、创建测试 Pod 并绑定 PVC

创建一个测试用的 Pod，指定存储为上面创建的 PVC，然后创建一个文件在挂载的 PVC 目录中，然后进入 NFS 服务器下查看该文件是否存入其中。
```
# vim test-pod.yaml

kind: Pod
apiVersion: v1
metadata:
  name: test-pod
spec:
  containers:
  - name: test-pod
    image: busybox:latest
    command:
      - "/bin/sh"
    args:
      - "-c"
      - "touch /mnt/SUCCESS && exit 0 || exit 1"  #创建一个名称为"SUCCESS"的文件
    volumeMounts:
      - name: nfs-pvc
        mountPath: "/mnt"
  restartPolicy: "Never"
  volumes:
    - name: nfs-pvc
      persistentVolumeClaim:
        claimName: test-pvc
```
创建 Pod
- -n：指定创建 Pod 的 Namespace
```
$ kubectl apply -f test-pod.yaml -n kube-public
```
3、进入 NFS Server 服务器验证是否创建对应文件

进入 NFS Server 服务器的 NFS 挂载目录，查看是否存在 Pod 中创建的文件：
```
$ cd /nfs/data
$ ls -l

-rw-r--r-- kube-public-test-pvc-pvc-3dc54156-b81d-11e9-a8b8-000c29d98697

$ cd /kube-public-test-pvc-pvc-3dc54156-b81d-11e9-a8b8-000c29d98697
$ ls -l

-rw-r--r-- 1 root root 0 Jun 28 12:44 SUCCESS
```
可以看到已经生成 SUCCESS 该文件，并且可知通过 NFS Provisioner 创建的目录命名方式为 “namespace名称-pvc名称-pv名称”，pv 名称是随机字符串，所以每次只要不删除 PVC，那么 Kubernetes 中的与存储绑定将不会丢失，要是删除 PVC 也就意味着删除了绑定的文件夹，下次就算重新创建相同名称的 PVC，生成的文件夹名称也不会一致，因为 PV 名是随机生成的字符串，而文件夹命名又跟 PV 有关,所以删除 PVC 需谨慎。
