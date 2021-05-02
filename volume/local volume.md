kubernetes使用local volume
===

local volume是指挂载的某个本地存储设备，例如磁盘、分区或者目录。local volume只能用作静态创建的持久卷。尚不支持动态配置。

相比hostPath volumes，local volumes可以以持久和可移植的方式使用，而无需手动将 Pod 调度到节点，因为系统通过查看 PersistentVolume 所属节点的亲和性配置，就能了解卷的节点约束。

1、创建storage class
```
$ cat local_sc.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

2、创建PV，使用local volume和nodeAffinity的持久卷
```
$ cat local_pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: example-pv
spec:
  capacity:
    storage: 10Gi
  # volumeMode field requires BlockVolume Alpha feature gate to be enabled.
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node01
```



3、创建pod和pvc绑定到pv
```
$ cat local_pod.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: local-test
spec:
  serviceName: "local-service"
  replicas: 1
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
          mountPath: /usr/test-pod
  volumeClaimTemplates:
  - metadata:
      name: local-vol
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "local-storage"
      resources:
        requests:
          storage: 2Gi
```
