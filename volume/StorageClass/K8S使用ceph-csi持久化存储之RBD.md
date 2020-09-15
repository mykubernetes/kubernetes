一、集群和组件版本
---
K8S集群：1.17.3+  
Ceph集群：Nautilus（stables）  
Ceph-CSI：release-v3.1  
snapshotter-controller：release-2.1  
Linue kernel：3.10.0-1127.19.1.el7.x86_64 +  
镜像版本：
```
docker pull quay.io/k8scsi/csi-snapshotter:v2.1.1
docker pull quay.io/k8scsi/csi-snapshotter:v2.1.0
docker pull quay.io/k8scsi/csi-resizer:v0.5.0
docker pull quay.io/k8scsi/csi-provisioner:v1.6.0
docker pull quay.io/k8scsi/csi-node-driver-registrar:v1.3.0
docker pull quay.io/k8scsi/csi-attacher:v2.1.1
docker pull quay.io/cephcsi/cephcsi:v3.1-canary
docker pull quay.io/k8scsi/snapshot-controller:v2.0.1
```
二、部署
---
1）部署Ceph-CSI

1.1）克隆代码
```
# git clone https://github.com/ceph/ceph-csi.git
# cd ceph-csi/deploy/rbd/kubernetes
```

1.2）修改yaml文件  
1.2.1）修改csi-rbdplugin-provisioner.yaml和csi-rbdplugin.yaml文件，注释ceph-csi-encryption-kms-config配置：
```
# grep "#" csi-rbdplugin-provisioner.yaml
          # for stable functionality replace canary with latest release version
            #- name: ceph-csi-encryption-kms-config
            #  mountPath: /etc/ceph-csi-encryption-kms-config/
        #- name: ceph-csi-encryption-kms-config
        #  configMap:
        #    name: ceph-csi-encryption-kms-config
```

1.2.2）配置csi-config-map.yaml文件链接ceph集群的信息
```
# cat csi-config-map.yaml
---
apiVersion: v1
kind: ConfigMap
data:
  config.json: |-
    [
      {
        "clusterID": "c7b4xxf7-c61e-4668-9xx0-82c9xx5e3696",    // 通过ceph集群的ID
        "monitors": [
          "xxx.xxx.xxx.xxx:6789"
        ]
      }
    ]
metadata:
  name: ceph-csi-config
```

1.2.3）部署rbd相关的CSI
```
# kubectl apply -f ceph-csi/deploy/rbd/kubernetes/
# kubectl get pods
csi-rbdplugin-9f8kn                             3/3     Running   0          39h
csi-rbdplugin-pnjtn                             3/3     Running   0          39h
csi-rbdplugin-provisioner-7f469fb84-4qqbd       6/6     Running   0          41h
csi-rbdplugin-provisioner-7f469fb84-hkc9q       6/6     Running   5          41h
csi-rbdplugin-provisioner-7f469fb84-vm7qm       6/6     Running   0          40h
```

2)快照功能需要安装快照控制器支持：

2.1）克隆代码
```
# git clone https://github.com/kubernetes-csi/external-snapshotter
# cd external-snapshotter/deploy/kubernetes/snapshot-controller
```

2.2）部署
```
# kubectl external-snapshotter/deploy/kubernetes/snapshot-controller/
# kubectl get pods | grep snapshot-controller
snapshot-controller-0                           1/1     Running   0          20h
```

2.3）部署crd
```
# kubectl apply -f external-snapshotter/config/crd/
# kubectl api-versions | grep snapshot
snapshot.storage.k8s.io/v1beta1
```
至此，Ceph-CSI和snapshot-controller安装完成。下面进行功能测试。测试功能前需要在ceph集群中创建对应的存储池：


查看集群状态
```
# ceph -s
  cluster:
    id:     c7b43ef7-c61e-4668-9970-82c9775e3696
    health: HEALTH_OK
 
  services:
    mon: 1 daemons, quorum cka-node-01 (age 24h)
    mgr: cka-node-01(active, since 24h), standbys: cka-node-02, cka-node-03
    mds: cephfs:1 {0=cka-node-01=up:active} 2 up:standby
    osd: 3 osds: 3 up, 3 in
    rgw: 1 daemon active (cka-node-01)
 
  task status:
    scrub status:
        mds.cka-node-01: idle
 
  data:
    pools:   7 pools, 184 pgs
    objects: 827 objects, 1.7 GiB
    usage:   8.1 GiB used, 52 GiB / 60 GiB avail
    pgs:     184 active+clean
 
  io:
    client:   32 KiB/s rd, 0 B/s wr, 31 op/s rd, 21 op/s wr
```
 
创建存储池kubernetes
```
# ceph osd pool create kubernetes 8 8
# rbd pool init kubernetes
```

创建用户kubernetes
```
# ceph auth get-or-create client.kubernetes mon 'profile rbd' osd 'profile rbd pool=kubernetes'
```

获取集群信息和查看用户key
```
# ceph mon dump
dumped monmap epoch 3
epoch 3
fsid c7b43ef7-c61e-4668-9970-82c9775e3696
last_changed 2020-09-11 11:05:25.529648
created 2020-09-10 16:22:52.967856
min_mon_release 14 (nautilus)
0: [v2:10.0.xxx.xxx0:3300/0,v1:10.0.xxx.xxx:6789/0] mon.cka-node-01
 
# ceph auth get client.kubernetes
exported keyring for client.kubernetes
[client.kubernetes]
    key = AQBt5xxxR0DBAAtjxxA+zlqxxxF3shYm8qLQmw==
    caps mon = "profile rbd"
    caps osd = "profile rbd pool=kubernetes"
```

三、验证
---
验证如下功能：

1）创建rbd类型pvc给pod使用；  
2）创建rbd类型pvc的快照，并验证基于快照恢复的可用性；  
3）扩容pvc大小；  
4）同一个pvc重复创建快照；  
1、创建rbd类型pvc给pod使用：  
1.1) 创建连接ceph集群的秘钥  
```
# cat secret.yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: csi-rbd-secret
  namespace: default
stringData:
  userID: kubernetes
  userKey: AQBt51lf9iR0DBAAtjA+zlqxxxYm8qLQmw==
  encryptionPassphrase: test_passphrase
 
# kubectl apply -f secret.yaml
```

1.2) 创建storeclass
```
# cat storageclass.yaml
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
   name: csi-rbd-sc
provisioner: rbd.csi.ceph.com
parameters:
   clusterID: c7b43xxf7-c61e-4668-9970-82c9e3696
   pool: kubernetes
   imageFeatures: layering
   csi.storage.k8s.io/provisioner-secret-name: csi-rbd-secret
   csi.storage.k8s.io/provisioner-secret-namespace: default
   csi.storage.k8s.io/controller-expand-secret-name: csi-rbd-secret
   csi.storage.k8s.io/controller-expand-secret-namespace: default
   csi.storage.k8s.io/node-stage-secret-name: csi-rbd-secret
   csi.storage.k8s.io/node-stage-secret-namespace: default
   csi.storage.k8s.io/fstype: ext4
reclaimPolicy: Delete
allowVolumeExpansion: true
mountOptions:
   - discard
 
# kubectl apply -f storageclass.yaml
```

1.3)基于storeclass创建pvc
```
# cat pvc.yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rbd-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: csi-rbd-sc
 
# kubectl apply -f pvc.yaml
# kubectl get pvc rbd-pvc
NAME      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
rbd-pvc   Bound    pvc-11b931b0-7cb5-40e1-815b-c15659310593   1Gi      RWO            csi-rbd-sc        17h
```

1.4）创建pod应用pvc
```
# cat pod.yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: csi-rbd-demo-pod
spec:
  containers:
    - name: web-server
      image: nginx
      volumeMounts:
        - name: mypvc
          mountPath: /var/lib/www/html
  volumes:
    - name: mypvc
      persistentVolumeClaim:
        claimName: rbd-pvc
        readOnly: false
 
# kubectl apply -f pod.yaml
# kubectl get pods csi-rbd-demo-pod
NAME               READY   STATUS    RESTARTS   AGE
csi-rbd-demo-pod   1/1     Running   0          40h

# kubectl exec -ti csi-rbd-demo-pod -- bash
root@csi-rbd-demo-pod:/# df -h
Filesystem               Size  Used Avail Use% Mounted on
overlay                  199G  7.4G  192G   4% /
tmpfs                     64M     0   64M   0% /dev
tmpfs                    7.8G     0  7.8G   0% /sys/fs/cgroup
/dev/mapper/centos-root  199G  7.4G  192G   4% /etc/hosts
shm                       64M     0   64M   0% /dev/shm
/dev/rbd0                976M  2.6M  958M   1% /var/lib/www/html
tmpfs                    7.8G   12K  7.8G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs                    7.8G     0  7.8G   0% /proc/acpi
tmpfs                    7.8G     0  7.8G   0% /proc/scsi
tmpfs                    7.8G     0  7.8G   0% /sys/firmware
```

写入文件，用于后续快照验证
```
root@csi-rbd-demo-pod:/# cd /var/lib/www/html;mkdir demo;cd demo;echo "snapshot test" > test.txt
root@csi-rbd-demo-pod:/var/lib/www/html# cat demo/test.txt
snapshot test
```

2）创建rbd类型pvc的快照，并验证基于快照恢复的可用性：

2.1)创建上一步pvc的快照
```
# cat snapshot.yaml
---
apiVersion: snapshot.storage.k8s.io/v1beta1
kind: VolumeSnapshot
metadata:
  name: rbd-pvc-snapshot
spec:
  volumeSnapshotClassName: csi-rbdplugin-snapclass
  source:
    persistentVolumeClaimName: rbd-pvc
 
# kubectl apply -f snapshot.yaml
# kubectl get VolumeSnapshot rbd-pvc-snapshot
NAME               READYTOUSE   SOURCEPVC   SOURCESNAPSHOTCONTENT   RESTORESIZE   SNAPSHOTCLASS             SNAPSHOTCONTENT                                    CREATIONTIME   AGE
rbd-pvc-snapshot   true         rbd-pvc                             1Gi           csi-rbdplugin-snapclass   snapcontent-48f3e563-d21a-40bb-8e15-ddbf27886c88   19h            19h
```

2.2)创建基于快照恢复的pvc
```
# cat pvc-restore.yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rbd-pvc-restore
spec:
  storageClassName: csi-rbd-sc
  dataSource:
    name: rbd-pvc-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
 
# kubectl apply -f pvc-restore.yaml
```

2.3)创建pod应用快照恢复的pvc
```
# cat pod-restore.yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: csi-rbd-restore-demo-pod
spec:
  containers:
    - name: web-server
      image: nginx
      volumeMounts:
        - name: mypvc
          mountPath: /var/lib/www/html
  volumes:
    - name: mypvc
      persistentVolumeClaim:
        claimName: rbd-pvc-restore
        readOnly: false
 
# kubectl apply -f pod-restore.yaml
# kubectl get pods csi-rbd-restore-demo-pod
NAME                       READY   STATUS    RESTARTS   AGE
csi-rbd-restore-demo-pod   1/1     Running   0          18h
# kubectl exec -ti csi-rbd-restore-demo-pod -- bash
root@csi-rbd-restore-demo-pod:/# df -h
Filesystem               Size  Used Avail Use% Mounted on
overlay                  199G  7.4G  192G   4% /
tmpfs                     64M     0   64M   0% /dev
tmpfs                    7.8G     0  7.8G   0% /sys/fs/cgroup
/dev/mapper/centos-root  199G  7.4G  192G   4% /etc/hosts
shm                       64M     0   64M   0% /dev/shm
/dev/rbd3                976M  2.6M  958M   1% /var/lib/www/html
tmpfs                    7.8G   12K  7.8G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs                    7.8G     0  7.8G   0% /proc/acpi
tmpfs                    7.8G     0  7.8G   0% /proc/scsi
tmpfs                    7.8G     0  7.8G   0% /sys/firmware

root@csi-rbd-restore-demo-pod:/# cd /var/lib/www/html
root@csi-rbd-restore-demo-pod:/var/lib/www/html# ls
demo  lost+found
root@csi-rbd-restore-demo-pod:/var/lib/www/html# cat demo/test.txt
snapshot test
```
基于快照恢复数据功能正常

3）扩容pvc大小：

3.1)修改rbd-pvc的容量大小
```
# cat pvc.yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rbd-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi    // 由1G改为100G
  storageClassName: csi-rbd-sc
 
# kubectl apply -f pvc.yaml
# kubectl get pvc rbd-pvc
NAME      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
rbd-pvc   Bound    pvc-11b931b0-7cb5-40e1-815b-c15659310593   100Gi      RWO            csi-rbd-sc     40h
# kubectl exec -ti csi-rbd-demo-pod -- bash
root@csi-rbd-demo-pod:/# df -h
Filesystem               Size  Used Avail Use% Mounted on
overlay                  199G  7.4G  192G   4% /
tmpfs                     64M     0   64M   0% /dev
tmpfs                    7.8G     0  7.8G   0% /sys/fs/cgroup
/dev/mapper/centos-root  199G  7.4G  192G   4% /etc/hosts
shm                       64M     0   64M   0% /dev/shm
/dev/rbd0                 99G  6.8M   99G   1% /var/lib/www/html    // 扩容正常
tmpfs                    7.8G   12K  7.8G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs                    7.8G     0  7.8G   0% /proc/acpi
tmpfs                    7.8G     0  7.8G   0% /proc/scsi
tmpfs                    7.8G     0  7.8G   0% /sys/firmware
```

再次写入数据用于后续第二次创建快照
```
root@csi-rbd-demo-pod:# cd /var/lib/www/html;mkdir test;echo "abc" > test/demo.txt;echo "abc" >> /var/lib/www/html/demo/test.txt
root@csi-rbd-demo-pod:/var/lib/www/html# cat test/demo.txt
abc
root@csi-rbd-demo-pod:/var/lib/www/html# cat demo/test.txt
snapshot test
abc
```
4）同一个pvc重复创建快照：

4.1)再次对rbd-pvc创建快照
```
# cat snapshot-1.yaml
---
apiVersion: snapshot.storage.k8s.io/v1beta1
kind: VolumeSnapshot
metadata:
  name: rbd-pvc-snapshot-1
spec:
  volumeSnapshotClassName: csi-rbdplugin-snapclass
  source:
    persistentVolumeClaimName: rbd-pvc
 
# kubectl apply -f snapshot-1.yaml
# kubectl get VolumeSnapshot rbd-pvc-snapshot-1
NAME                 READYTOUSE   SOURCEPVC   SOURCESNAPSHOTCONTENT   RESTORESIZE   SNAPSHOTCLASS             SNAPSHOTCONTENT                                    CREATIONTIME   AGE
rbd-pvc-snapshot-1   true         rbd-pvc                             100Gi         csi-rbdplugin-snapclass   snapcontent-b82dceb0-7ba6-4a3e-88ab-2220b729d85f   18h            18h
```

4.2)基于rbd-pvc-snapshot-1快照恢复pvc
```
# cat pvc-restore-1.yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rbd-pvc-restore-1
spec:
  storageClassName: csi-rbd-sc
  dataSource:
    name: rbd-pvc-snapshot-1
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
 
# kubectl apply -f pvc-restore-1.yaml
```

4.3)创建pod引用rbd-pvc-restore-1恢复的pvc
```
# cat pod-restore-1.yaml
---
apiVersion: v1
kind: Pod
metadata:
  name: csi-rbd-restore-demo-pod-1
spec:
  containers:
    - name: web-server
      image: nginx
      volumeMounts:
        - name: mypvc
          mountPath: /var/lib/www/html
  volumes:
    - name: mypvc
      persistentVolumeClaim:
        claimName: rbd-pvc-restore-1
        readOnly: false
 
# kubectl apply -f pod-restore-1.yaml
NAME                         READY   STATUS    RESTARTS   AGE
csi-rbd-restore-demo-pod-1   1/1     Running   0          18h
# kubectl exec -ti csi-rbd-restore-demo-pod-1 -- bash
root@csi-rbd-restore-demo-pod-1:/# df -h
Filesystem               Size  Used Avail Use% Mounted on
overlay                  199G  7.4G  192G   4% /
tmpfs                     64M     0   64M   0% /dev
tmpfs                    7.8G     0  7.8G   0% /sys/fs/cgroup
/dev/mapper/centos-root  199G  7.4G  192G   4% /etc/hosts
shm                       64M     0   64M   0% /dev/shm
/dev/rbd4                 99G  6.8M   99G   1% /var/lib/www/html
tmpfs                    7.8G   12K  7.8G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs                    7.8G     0  7.8G   0% /proc/acpi
tmpfs                    7.8G     0  7.8G   0% /proc/scsi
tmpfs                    7.8G     0  7.8G   0% /sys/firmware
root@csi-rbd-restore-demo-pod-1:/# cd /var/lib/www/html
root@csi-rbd-restore-demo-pod-1:/var/lib/www/html# cat demo/test.txt
snapshot test
abc
root@csi-rbd-restore-demo-pod-1:/var/lib/www/html# cat test/demo.txt
abc
```
至此验证扩容后的pvc，二次创建的快照恢复数据功能正常
 
查看第一个创建的快照中是否有后续添加的文件数据,如下数据还是第一个快照创建时数据
```
[root@cka-node-01 rbd]# kubectl exec -ti csi-rbd-restore-demo-pod -- bash
root@csi-rbd-restore-demo-pod:/# df -h
Filesystem               Size  Used Avail Use% Mounted on
overlay                  199G  7.4G  192G   4% /
tmpfs                     64M     0   64M   0% /dev
tmpfs                    7.8G     0  7.8G   0% /sys/fs/cgroup
/dev/mapper/centos-root  199G  7.4G  192G   4% /etc/hosts
shm                       64M     0   64M   0% /dev/shm
/dev/rbd3                976M  2.6M  958M   1% /var/lib/www/html
tmpfs                    7.8G   12K  7.8G   1% /run/secrets/kubernetes.io/serviceaccount
tmpfs                    7.8G     0  7.8G   0% /proc/acpi
tmpfs                    7.8G     0  7.8G   0% /proc/scsi
tmpfs                    7.8G     0  7.8G   0% /sys/firmware
root@csi-rbd-restore-demo-pod:/# cd /var/lib/www/html
root@csi-rbd-restore-demo-pod:/var/lib/www/html# cat demo/test.txt
snapshot test
root@csi-rbd-restore-demo-pod:/var/lib/www/html# ls
demo  lost+found
```
