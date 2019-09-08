
Kubernetes 安装Jenkins
---

这里使用k8s的pv进行存储数据，当然也可以使用storage class对象来自动创建  
1、创建pv需要使用nfs，我这里直接创建一台nfs服务器  
```
我们在k8s集群的任意一个节点配置一台nfs集群，其他节点主要是挂载
for i in k8s-01 k8s-02 k8s-03 k8s-04;do ssh root@$i "yum install nfs-utils rpcbind -y";done

#我这里使用单独的NFS服务器，IP为192.168.0.100
#NFS服务节点操作如下
mkdir -p /data1/k8s-vloume
echo "/data1/k8s-vloume  *(rw,no_root_squash,sync)" >/etc/exports
systemctl start rpcbind
systemctl enable rpcbind
systemctl enable nfs
systemctl restart nfs
#IP改成网段

其他k8s节点直接启动rpcbind并且挂载目录就可以

#挂载
systemctl start rpcbind
systemctl enable rpcbind
mkdir /data1/k8s-vloume -p
mount -t nfs 192.168.0.100:/data1/k8s-vloume /data1/k8s-vloume


#创建完成你们自己测一下就可以了
```  

2、这里需要创建一个命名空间  
```
kubectl create namespace jenkins

#在创建一下jenkins存储yaml的目录
mkdir -p /opt/jenkins 
```  

3、创建Jenkins Deployment  
```
# vim /opt/jenkins/jenkins_deployment.yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: jenkins         #deployment名称
  namespace: jenkins      #命名空间
spec:
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      terminationGracePeriodSeconds: 10     #优雅停止pod
      serviceAccount: jenkins               #后面还需要创建服务账户
      containers:
      - name: jenkins
        image: jenkins/jenkins:lts               #镜像版本
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080                #外部访问端口
          name: web
          protocol: TCP
        - containerPort: 50000              #jenkins save发现端口
          name: agent
          protocol: TCP
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /login
            port: 8080
          initialDelaySeconds: 60          #容器初始化完成后，等待60秒进行探针检查
          timeoutSeconds: 5
          failureThreshold: 12          #当Pod成功启动且检查失败时，Kubernetes将在放弃之前尝试failureThreshold次。放弃生存检查意味着重新启动Pod。而放弃就绪检查，Pod将被标记为未就绪。默认为3.最小值为1
        readinessProbe:
          httpGet:
            path: /login
            port: 8080
          initialDelaySeconds: 60
          timeoutSeconds: 5
          failureThreshold: 12
        volumeMounts:                       #需要将jenkins_home目录挂载出来
        - name: jenkinshome
          subPath: jenkins
          mountPath: /var/jenkins_home
        env:
        - name: LIMITS_MEMORY
          valueFrom:
            resourceFieldRef:
              resource: limits.memory
              divisor: 1Mi
        - name: JAVA_OPTS
          value: -Xmx$(LIMITS_MEMORY)m -XshowSettings:vm -Dhudson.slaves.NodeProvisioner.initialDelay=0 -Dhudson.slaves.NodeProvisioner.MARGIN=50 -Dhudson.slaves.NodeProvisioner.MARGIN0=0.85 -Duser.timezone=Asia/Shanghai
      securityContext:
        fsGroup: 1000
      volumes:
      - name: jenkinshome
        persistentVolumeClaim:
          claimName: opspvc             #这里将上面创建的pv关联到pvc上

#这里不进行创建
```  

4、因为要保证Jenkins持久化缓存数据，我们创建了一个PV  
```
cat >/opt/jenkins/jenkins_pv.yaml <<EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: opspv
spec:
  capacity:
    storage: 20Gi
  accessModes:
  - ReadWriteMany
  persistentVolumeReclaimPolicy: Delete
  nfs:
    server: 192.168.0.100
    path: /data1/k8s-vloume

---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: opspvc
  namespace: jenkins
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 20Gi
EOF

#注意修改NFS挂载目录以及NFS Server
```  


5、创建rbac  
```
cat >/opt/jenkins/jenkins_rbac.yaml <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins
  namespace: jenkins

---

kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: jenkins
rules:
  - apiGroups: ["extensions", "apps"]
    resources: ["deployments"]
    verbs: ["create", "delete", "get", "list", "watch", "patch", "update"]
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["create", "delete", "get", "list", "watch", "patch", "update"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["create","delete","get","list","patch","update","watch"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create","delete","get","list","patch","update","watch"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get","list","watch"]
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: jenkins
  namespace: jenkins
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: jenkins
subjects:
  - kind: ServiceAccount
    name: jenkins
    namespace: jenkins
EOF
```  

6、创建svc  
```
cat >/opt/jenkins/jenkins_svc.yaml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: jenkins
  namespace: jenkins
  labels:
    app: jenkins
spec:
  selector:
    app: jenkins
  type: NodePort
  ports:
  - name: web
    port: 8080
    targetPort: web
    nodePort: 30002
  - name: agent
    port: 50000
    targetPort: agent
EOF
```


7、直接使用kubectl apple -f .，我为了排查错误，进行一个顺序执行  
```
#这里我先执行pv然后在执行rbac，依次deployment和svc
[root@abcdocker-k8s01 jenkins]# kubectl apply -f jenkins_pv.yaml 
persistentvolume/opspv created
persistentvolumeclaim/opspvc created
[root@abcdocker-k8s01 jenkins]# kubectl apply -f jenkins_rbac.yaml 
serviceaccount/jenkins created
clusterrole.rbac.authorization.k8s.io/jenkins created
clusterrolebinding.rbac.authorization.k8s.io/jenkins created
[root@abcdocker-k8s01 jenkins]# kubectl apply -f jenkins_deployment.yaml 
deployment.extensions/jenkins created
[root@abcdocker-k8s01 jenkins]# kubectl apply -f jenkins_rbac.yaml 
serviceaccount/jenkins unchanged
clusterrole.rbac.authorization.k8s.io/jenkins unchanged
clusterrolebinding.rbac.authorization.k8s.io/jenkins unchanged
[root@abcdocker-k8s01 jenkins]# kubectl apply -f jenkins_svc.yaml 
service/jenkins created
```  
