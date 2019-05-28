
1.创建storageclass  
```
# vim two-replica-glusterfs-sc.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: two-replica-glusterfs-sc
provisioner: kubernetes.io/glusterfs      #提供了存储资源的存储系统，存储类依赖此字段来判断存储插件适用的目标存储系统
reclaimPolicy: Retain                     #为当前存储类动态创建pv指定的回收策略，可用值为Delete(默认)和Retain
parameters:                               #存储类使用的参数描述要关联到的存储卷
  gidMax: "50000"
  gidMin: "40000"
  resturl: http://10.142.21.23:30088      #指定gluster存储系统的RESTful风格的访问接口
  volumetype: replicate:2
  restauthenabled: "true"                 #只有此字段设置成true时restuser和restuserkey才会启用
  restuser: "admin"
  restuserkey: "123456"
#  secretNamespace: "default"
#  secretName: "heketi-secret"
```  

2.创建pvc  
```
# vim kafka-pvc.yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: kafka-pvc
  namespace: kube-system
spec:
  storageClassName: two-replica-glusterfs-sc         #对应上边存储类名
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 20Gi
```  

3、应用  
```
# kubectl create -f kafka-pvc.yaml 

创建后会自动产生pvc
kubectl get pvc -n kube-system
NAME        STATUS    VOLUME                                     CAPACITY   ACCESSMODES   STORAGECLASS               AGE
kafka-pvc   Bound     pvc-9749a71a-c943-11e7-8ccf-00505694b7e8   20Gi       RWX           two-replica-glusterfs-sc   3m

# 自动产生了一个pv
kubectl get pv
NAME                                       CAPACITY   ACCESSMODES   RECLAIMPOLICY   STATUS      CLAIM                  STORAGECLASS   REASON    AGE
pvc-1c45d9a2-c76e-11e7-892e-00505694eb6a   1Gi        RWX           Delete          Bound       default/gluster-pvc1   gfs                      17m


4.创建应用  
```
# vim nginx-use-glusterfs.yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: nginx-use-pvc
  namespace: kube-system
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - image: nginx:1.11.4-alpine
        imagePullPolicy: IfNotPresent
        name: nginx-use-pvc
        volumeMounts:
        - mountPath: /test
          name: my-pvc
      volumes:
      - name: my-pvc
        persistentVolumeClaim:
          claimName: kafka-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-use-pvc
  namespace: kube-system
spec:
  type: NodePort
  ports:
  - name: nginx-use-pvc
    port: 80
    targetPort: 80
    nodePort: 30080
  selector:
    app: nginx
```  
