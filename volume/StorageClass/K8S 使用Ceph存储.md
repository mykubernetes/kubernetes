# POD使用RBD做为持久数据卷
### 安装与配置
RBD支持ReadWriteOnce，ReadOnlyMany两种模式  
1、配置rbd-provisioner
```
cat >external-storage-rbd-provisioner.yaml<<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: rbd-provisioner
  namespace: kube-system
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: rbd-provisioner
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
  - apiGroups: [""]
    resources: ["endpoints"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["services"]
    resourceNames: ["kube-dns"]
    verbs: ["list", "get"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: rbd-provisioner
subjects:
  - kind: ServiceAccount
    name: rbd-provisioner
    namespace: kube-system
roleRef:
  kind: ClusterRole
  name: rbd-provisioner
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: rbd-provisioner
  namespace: kube-system
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: rbd-provisioner
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: rbd-provisioner
subjects:
- kind: ServiceAccount
  name: rbd-provisioner
  namespace: kube-system

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rbd-provisioner
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: rbd-provisioner
  replicas: 1
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: rbd-provisioner
    spec:
      containers:
      - name: rbd-provisioner
        image: "quay.io/external_storage/rbd-provisioner:v2.0.0-k8s1.11"
        env:
        - name: PROVISIONER_NAME
          value: ceph.com/rbd
      serviceAccount: rbd-provisioner
EOF
kubectl apply -f external-storage-rbd-provisioner.yaml
```
2、配置storageclass
```
1、创建pod时，kubelet需要使用rbd命令去检测和挂载pv对应的ceph image，所以要在所有的worker节点安装ceph客户端ceph-common。
将ceph的ceph.client.admin.keyring和ceph.conf文件拷贝到master的/etc/ceph目录下
yum -y install ceph-common

2、创建 osd pool 在ceph的mon或者admin节点
ceph osd pool create kube 128 128 
ceph osd pool ls

3、创建k8s访问ceph的用户 在ceph的mon或者admin节点
ceph auth get-or-create client.kube mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=kube' -o ceph.client.kube.keyring

4、查看key 在ceph的mon或者admin节点
ceph auth get-key client.admin
ceph auth get-key client.kube

5、创建 admin secret
kubectl create secret generic ceph-secret --type="kubernetes.io/rbd" \
--from-literal=key=AQCtovZdgFEhARAAoKhLtquAyM8ROvmBv55Jig== \
--namespace=kube-system

6、在 default 命名空间创建pvc用于访问ceph的 secret
kubectl create secret generic ceph-user-secret --type="kubernetes.io/rbd" \
--from-literal=key=AQAM9PxdEFi3AhAAzvvhuyk1AfN5twlY+4zNMA== \
--namespace=default

```
3、配置StorageClass
```
cat >storageclass-ceph-rdb.yaml<<EOF
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: dynamic-ceph-rdb
provisioner: ceph.com/rbd
parameters:
  monitors: 10.151.30.125:6789,10.151.30.126:6789,10.151.30.127:6789
  adminId: admin
  adminSecretName: ceph-secret
  adminSecretNamespace: kube-system
  pool: kube
  userId: kube
  userSecretName: ceph-user-secret
  fsType: ext4
  imageFormat: "2"
  imageFeatures: "layering"
EOF
```
4、创建yaml
```
kubectl apply -f storageclass-ceph-rdb.yaml
```
5、查看sc
```
kubectl get storageclasses 
```
### 测试使用
1、创建pvc测试
```
cat >ceph-rdb-pvc-test.yaml<<EOF
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: ceph-rdb-claim
spec:
  accessModes:     
    - ReadWriteOnce
  storageClassName: dynamic-ceph-rdb
  resources:
    requests:
      storage: 2Gi
EOF
kubectl apply -f ceph-rdb-pvc-test.yaml
```
2、查看
```
kubectl get pvc
kubectl get pv
```
3、创建 nginx pod 挂载测试
```
cat >nginx-pod.yaml<<EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod1
  labels:
    name: nginx-pod1
spec:
  containers:
  - name: nginx-pod1
    image: nginx:alpine
    ports:
    - name: web
      containerPort: 80
    volumeMounts:
    - name: ceph-rdb
      mountPath: /usr/share/nginx/html
  volumes:
  - name: ceph-rdb
    persistentVolumeClaim:
      claimName: ceph-rdb-claim
EOF
kubectl apply -f nginx-pod.yaml
```
4、查看
```
kubectl get pods -o wide
```
5、修改文件内容
```
kubectl exec -ti nginx-pod1 -- /bin/sh -c 'echo this is from Ceph RBD!!! > /usr/share/nginx/html/index.html'
```
6、访问测试
```
curl http://$podip
```
7、清理
```
kubectl delete -f nginx-pod.yaml
kubectl delete -f ceph-rdb-pvc-test.yaml
```
# POD使用CephFS做为持久数据卷
CephFS方式支持k8s的pv的3种访问模式ReadWriteOnce，ReadOnlyMany ，ReadWriteMany
## Ceph端创建CephFS pool
1、如下操作在ceph的mon或者admin节点
CephFS需要使用两个Pool来分别存储数据和元数据
```
ceph osd pool create fs_data 128
ceph osd pool create fs_metadata 128
ceph osd lspools
```
2、创建一个CephFS
```
ceph fs new cephfs fs_metadata fs_data
```
3、查看
```
ceph fs ls
```

## 部署 cephfs-provisioner
1、使用社区提供的cephfs-provisioner
```
cat >external-storage-cephfs-provisioner.yaml<<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cephfs-provisioner
  namespace: kube-system
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: cephfs-provisioner
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
  - apiGroups: [""]
    resources: ["endpoints"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["create", "get", "delete"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: cephfs-provisioner
subjects:
  - kind: ServiceAccount
    name: cephfs-provisioner
    namespace: kube-system
roleRef:
  kind: ClusterRole
  name: cephfs-provisioner
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cephfs-provisioner
  namespace: kube-system
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["create", "get", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cephfs-provisioner
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: cephfs-provisioner
subjects:
- kind: ServiceAccount
  name: cephfs-provisioner
  namespace: kube-system

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cephfs-provisioner
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: cephfs-provisioner
  replicas: 1
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: cephfs-provisioner
    spec:
      containers:
      - name: cephfs-provisioner
        image: "quay.io/external_storage/cephfs-provisioner:latest"
        env:
        - name: PROVISIONER_NAME
          value: ceph.com/cephfs
        command:
        - "/usr/local/bin/cephfs-provisioner"
        args:
        - "-id=cephfs-provisioner-1"
      serviceAccount: cephfs-provisioner
EOF
kubectl apply -f external-storage-cephfs-provisioner.yaml
```

2、查看状态 等待running之后 再进行后续的操作
```
kubectl get pod -n kube-system
```

## 配置 storageclass
1、查看key 在ceph的mon或者admin节点
```
ceph auth get-key client.admin
```

2、创建 admin secret
```
kubectl create secret generic ceph-secret --type="kubernetes.io/rbd" \
--from-literal=key=AQCtovZdgFEhARAAoKhLtquAyM8ROvmBv55Jig== \
--namespace=kube-system
```

3、查看 secret
```
kubectl get secret ceph-secret -n kube-system -o yaml
```

4、配置 StorageClass
```
cat >storageclass-cephfs.yaml<<EOF
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: dynamic-cephfs
provisioner: ceph.com/cephfs
parameters:
    monitors: 10.151.30.125:6789,10.151.30.126:6789,10.151.30.127:6789
    adminId: admin
    adminSecretName: ceph-secret
    adminSecretNamespace: "kube-system"
    claimRoot: /volumes/kubernetes
EOF
```

5、创建
```
kubectl apply -f storageclass-cephfs.yaml
```

6、查看
```
kubectl get sc
```
## 测试使用
1、创建pvc测试
```
cat >cephfs-pvc-test.yaml<<EOF
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: cephfs-claim
spec:
  accessModes:     
    - ReadWriteMany
  storageClassName: dynamic-cephfs
  resources:
    requests:
      storage: 2Gi
EOF
kubectl apply -f cephfs-pvc-test.yaml
```

2、查看
```
kubectl get pvc
kubectl get pv
```

3、创建 nginx pod 挂载测试
```
cat >nginx-pod.yaml<<EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod2
  labels:
    name: nginx-pod2
spec:
  containers:
  - name: nginx-pod2
    image: nginx
    ports:
    - name: web
      containerPort: 80
    volumeMounts:
    - name: cephfs
      mountPath: /usr/share/nginx/html
  volumes:
  - name: cephfs
    persistentVolumeClaim:
      claimName: cephfs-claim
EOF
kubectl apply -f nginx-pod.yaml
```
 
4、查看
```
kubectl get pods -o wide
```

5、修改文件内容
```
kubectl exec -ti nginx-pod2 -- /bin/sh -c 'echo This is from CephFS!!! > /usr/share/nginx/html/index.html'
```

6、访问pod测试
```
curl http://$podip
```

7、清理
```
kubectl delete -f nginx-pod.yaml
kubectl delete -f cephfs-pvc-test.yaml
```
