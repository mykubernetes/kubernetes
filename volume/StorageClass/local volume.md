local volume
===
kubernetes从1.10版本开始支持local volume（本地卷），workload（不仅是statefulsets类型）可以充分利用本地快速SSD，从而获取比remote volume（如cephfs、RBD）更好的性能。

在local volume出现之前，statefulsets也可以利用本地SSD，方法是配置hostPath，并通过nodeSelector或者nodeAffinity绑定到具体node上。但hostPath的问题是，管理员需要手动管理集群各个node的目录，不太方便。

下面两种类型应用适合使用local volume。

- 数据缓存，应用可以就近访问数据，快速处理。
- 分布式存储系统，如分布式数据库Cassandra ，分布式文件系统ceph/gluster

下面会先以手动方式创建PV、PVC、Pod的方式，介绍如何使用local volume，然后再介绍external storage提供的半自动方式

1、创建stoargeclass
```
# storageclass.yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: fast-disks
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

2、创建pv
```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv-example
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /mnt/disks/vol1
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - k8sdeploy-n102
          - k8sdeploy-n103
          - k8sdeploy-n104
```

3、用local volume PV
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: fast-disks
---
kind: Pod
apiVersion: v1
metadata:
  name: mypod
spec:
  containers:
    - name: myfrontend
      image: nginx
      volumeMounts:
      - mountPath: "/usr/share/nginx/html"
        name: mypd
  volumes:
    - name: mypd
      persistentVolumeClaim:
        claimName: local-pvc
```

4、进入到容器里，会看到挂载的目录，大小其实就是上面创建的PV所在磁盘的size。

在宿主机的 /mnt/disks/vol1目录下创建一个index.html文件：
```
echo "hello world" >  /mnt/disks/vol1/index.html
```

5、然后再去curl容器的IP地址，就可以得到刚写入的字符串了。
```
curl <pod-ip>
```
删除Pod/PVC，之后PV状态改为Released，该PV不会再被绑定PVC了。需要手动删除pv。

local-volume-provisioner动态创建pv
===
地址：https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner

1、clone项目
```
git clone https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner.gi4
git checkout tags/v2.3.4 -b v2.3.5
helm template ./helm/provisioner -f ./helm/provisioner/values.yaml > local-volume-provisioner.generated.yaml
kubectl create -f local-volume-provisioner.generated.yaml
```

2、创建storageclass
```
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: fast-disks
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

3、部署
```
kubectl apply -f local-fast-disks.yaml
```

4、挂载磁盘
其Provisioner本身其并不提供local volume，但它在各个节点上的provisioner会去动态的“发现”挂载点（discovery directory），当某node的provisioner在/mnt/fast-disks目录下发现有挂载点时，会创建PV，该PV的local.path就是挂载点，并设置nodeAffinity为该node。

挂载盘麻烦或者没有，可以参考mount bind方式
```
#!/bin/bash
for i in $(seq 1 5); do
  mkdir -p /mnt/fast-disks-bind/vol${i}
  mkdir -p /mnt/fast-disks/vol${i}
  mount --bind /mnt/fast-disks-bind/vol${i} /mnt/fast-disks/vol${i}
done
```

5、执行该脚本后，等待一会，执行查询pv命令，就可以发现自动创建了
```
kubectl get pv
```

6、测试pod是否可以运行
```
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: local-test
spec:
  serviceName: "local-service"
  replicas: 3
  selector:
    matchLabels:
      app: local-test
  template:
    metadata:
      labels:
        app: local-test
    spec:
      containers:
      - name: test-container
        image: busybox
        command:
        - "/bin/sh"
        args:
        - "-c"
        - "sleep 100000"
        volumeMounts:
        - name: local-vol
          mountPath: /tmp
  volumeClaimTemplates:
  - metadata:
      name: local-vol
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "fast-disks"
      resources:
        requests:
          storage: 2Gi
```
