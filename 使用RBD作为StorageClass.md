官方介绍  
https://kubernetes.io/docs/concepts/storage/storage-classes/#ceph-rbd  
1、创建 ceph-secret-admin  
---
1)Ceph 存储集群默认是开启了 cephx 认证的  
```
$ ceph auth get-key client.admin |base64
QVFDUWFsMWFuUWlhRHhBQXpFMGpxMSsybEFjdHdSZ3J3M082YWc9PQ==
```  

2)获取并 base64 生成一下 k8s secret 认证 key  
```
$ vim ceph-secret-admin.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ceph-secret-admin
type: "kubernetes.io/rbd"  
data:
  key: QVFDUWFsMWFuUWlhRHhBQXpFMGpxMSsybEFjdHdSZ3J3M082YWc9PQ==
```  

3)创建名称为 ceph-secret-admin 的 Secret  
```
$ kubectl create -f ceph-secret-admin.yaml 
secret "ceph-secret-admin" created
$ kubectl get secret
NAME                  TYPE                                     DATA       AGE
ceph-secret-admin     kubernetes.io/rbd                         1         16s
default-token-630xt   kubernetes.io/service-account-token       3         15m
```  

2、创建 rbd-storage-class  
1)官方提供的存储类配置
```
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: fast
provisioner: kubernetes.io/rbd
parameters:
  monitors: 10.16.153.105:6789
  adminId: kube
  adminSecretName: ceph-secret
  adminSecretNamespace: kube-system
  pool: kube
  userId: kube
  userSecretName: ceph-secret-user
  fsType: ext4
  imageFormat: "2"
  imageFeatures: "layering"
```  
- provisioner 该字段指定使用存储卷类型为 kubernetes.io/rbd，注意 kubernetes.io/ 开头为 k8s 内部支持的存储提供者，不同的存储卷提供者类型这里要修改成对应的值。
- adminId | userId 这里需要指定两种 Ceph 角色 admin 和其他 user，admin 角色默认已经有了，其他 user 可以去 Ceph 集群创建一个并赋对应权限值，如果不创建，也可以都指定为 admin。
- adminSecretName 为上边创建的 Ceph 管理员 admin 使用的 ceph-secret-admin。
- adminSecretNamespace 管理员 secret 使用的命名空间，默认 default，如果修改为其他的话，需要修改 ceph-secret-admin.yaml 增加 namespace: other-namespace。


2)rbd-storage-class.yaml 文件  
```
$ vim rbd-storage-class.yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: rbd
provisioner: kubernetes.io/rbd
parameters:
  monitors: 10.222.78.12:6789
  adminId: admin
  adminSecretName: ceph-secret-admin
  adminSecretNamespace: default
  pool: rbd
  userId: admin
  userSecretName: ceph-secret-admin
```  

3)建一下名称为 rbd 类型为 rbd 的 storage-class  
```
$ kubectl create -f rbd-storage-class.yaml 
storageclass "rbd" created
$ kubectl get storageclass
NAME      TYPE
rbd       kubernetes.io/rbd
```  

4)创建一个 PVC 申请 1G 存储空间  
```
$ vim rbd-dyn-pv-claim.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ceph-rbd-dyn-pv-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: rbd
  resources:
    requests:
      storage: 1Gi
```  
- storageClassName: rbd 指明使用的 storageClass 为前面创建的 rbd  
- accessModes 指定模型为 ReadWriteOnce,rbd 只支持 ReadWriteOnce和ReadOnlyMany  

5)然后创建一个该 PVC  
```
$ kubectl create -f rbd-dyn-pv-claim.yaml 
persistentvolumeclaim "ceph-rbd-dyn-pv-claim" created
$ kubectl get pvc
NAME                     STATUS     VOLUME    CAPACITY   ACCESSMODES   STORAGECLASS   AGE
ceph-rbd-dyn-pv-claim   Pending                                           rbd        29s
```  

6)状态为 Pending 并没有创建成功  
```
$ kubectl describe pvc/ceph-rbd-dyn-pv-claim
Name:   ceph-rbd-dyn-pv-claim
Namespace:  default
StorageClass: rbd
Status:   Pending
Volume:   
Labels:   <none>
Annotations:  volume.beta.kubernetes.io/storage-provisioner=kubernetes.io/rbd
Capacity: 
Access Modes: 
Events:
  FirstSeen LastSeen  Count From        SubObjectPath Type    Reason  Message
  --------- --------  ----- ----        ------------- --------  ------  -------
  46s   6s    4 persistentvolume-controller     Warning   ProvisioningFailed  Failed to provision volume with StorageClass "rbd": failed to create rbd image: executable file not found in $PATH, command output: 
```  
从打印信息中可以看到如下出错信息 failed to create rbd image: executable file not found in $PATH，提示创建 rbd image 失败，因为在 $PATH 中没找到可执行文件  
需要安装 ceph-common工具插件来操作 Ceph,添加 ceph-common到hyperkube image 中  
具体就是构建一个新的安装了 ceph-common 的同名镜像 hyperkube-amd64 替换官方镜像即可  
```
$ cd /home/wanyang3/k8s
$ git clone https://github.com/kubernetes-incubator/external-storage.git
$ tree external-storage/ceph/rbd/deploy/
├── README.md
├── non-rbac
│   └── deployment.yaml
└── rbac
    ├── clusterrole.yaml
    ├── clusterrolebinding.yaml
    ├── deployment.yaml
    └── serviceaccount.yaml
```  
里提供rbac和no-rbac两种方式,我们搭建的 k8s 集群时开启了 rbac 认证  
ClusterRoleBinding 默认绑定 namespace: default，如果要修改为其他 namespace，对应的 storageClass 中的adminSecretNamespace 也需要对应修改下  
安装扩展存储卷插件
```
$ kubectl apply -f rbac/
clusterrole "rbd-provisioner" created
clusterrolebinding "rbd-provisioner" created
deployment "rbd-provisioner" created
serviceaccount "rbd-provisioner" create

$ kubectl get pods
NAME                              READY     STATUS    RESTARTS   AGE
rbd-provisioner-687025274-1l6h5   1/1       Running   0          9s
```  

修改上边 rbd-storage-class.yaml 文件将 provisioner: kubernetes.io/rbd 修改为 provisioner: ceph.com/rbd，意思就是不使用 k8s 内部提供的 rbd 存储类型，而是使用我们刚创建的扩展 rbd 存储。  
```
$ vim rbd-storage-class.yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: rbd
provisioner: ceph.com/rbd
parameters:
  monitors: 10.222.78.12:6789
  adminId: admin
  adminSecretName: ceph-secret-admin
  adminSecretNamespace: default
  pool: rbd
  userId: admin
  userSecretName: ceph-secret-admin
```  

重新创建一下名称为 rbd 类型为 ceph.com/rbd 的 storage-class  
```
$ kubectl apply -f rbd-storage-class.yaml

$ kubectl get sc
NAME      TYPE
rbd       ceph.com/rbd 
```  

创建rbd-dyn-pv-claim.yaml 文件不用做任何修改  
```
$ kubectl create -f rbd-dyn-pv-claim.yaml 
persistentvolumeclaim "ceph-rbd-dyn-pv-claim" created
$ kubectl get pvc
NAME                    STATUS    VOLUME                                     CAPACITY   ACCESSMODES   STORAGECLASS   AGE
ceph-rbd-dyn-pv-claim   Bound     pvc-cd63e53a-fa6f-11e7-a8e8-080027ee5979   1Gi        RWO           rbd            7s
```  


