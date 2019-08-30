1、部署prometheus  
1)部署prometheus的configmap  
```
cat prometheus.configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: kube-system
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      scrape_timeout: 15s
    scrape_configs:
    - job_name: 'prometheus'
      static_configs:
      - targets: ['localhost:9090']
```  
- scrape_interval:表示prometheus抓取指标数据的频率，默认是15s
- evaluation_interval:用来控制评估规则的频率，prometheus使用规则产生新的时间序列数据或者产生警报
- rule_files模块制定了规则所在的位置
- scrape_configs用于控制prometheus监控哪些资源。


```
# kubectl create -f prometheus.configmap.yaml
configmap/prometheus-config created

# kubectl get configmaps -n kube-system |grep prometheus
prometheus-config                    1      2m23s
```  

2)部署prometheus  
```
cat prometheus.deploy.yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: prometheus
  namespace: kube-system
  labels:
    app: prometheus
spec:
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      serviceAccountName: prometheus
      containers:
      - image: prom/prometheus:v2.4.3
        name: prometheus
        command:
        - "/bin/prometheus"
        args:
        - "--config.file=/etc/prometheus/prometheus.yml"
        - "--storage.tsdb.path=/prometheus"
        - "--storage.tsdb.retention=30d"
        - "--web.enable-admin-api"  # 控制对admin HTTP API的访问，其中包括删除时间序列等功能
        - "--web.enable-lifecycle"  # 支持热更新，直接执行localhost:9090/-/reload立即生效
        ports:
        - containerPort: 9090
          protocol: TCP
          name: http
        volumeMounts:
        - mountPath: "/prometheus"
          subPath: prometheus
          name: data
        - mountPath: "/etc/prometheus"
          name: config-volume
        resources:
          requests:
            cpu: 100m
            memory: 512Mi
          limits:
            cpu: 100m
            memory: 512Mi
      securityContext:
        runAsUser: 0
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: prometheus
      - configMap:
          name: prometheus-config
        name: config-volume
```  
- storage.tsdb.path指定了TSDB数据的存储路径
- storage.tsdb.rentention设置了保留多长时间的数据
- web.enable-lifecyle用来开启支持热更新,通过执行localhost:9090/-/reload就会立即生效
- securityContext 其中runAsUser设置为0，这是因为prometheus运行过程中使用的用户是nobody，如果不配置可能会出现权限问题


3)配置prometheus的存储卷  
```
cat prometheus-volume.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: prometheus
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  nfs:
    server: 10.4.82.138
    path: /data/k8s

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus
  namespace: kube-system
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```  

```
# kubectl create -f prometheus-volume.yaml
persistentvolume/prometheus created
persistentvolumeclaim/prometheus created

# kubectl get pvc --all-namespaces
NAMESPACE     NAME         STATUS   VOLUME       CAPACITY   ACCESS MODES   STORAGECLASS   AGE
kube-system   prometheus   Bound    prometheus   10Gi       RWO                           47s

# kubectl get pv prometheus
NAME         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                    STORAGECLASS   REASON   AGE
prometheus   10Gi       RWO            Recycle          Bound    kube-system/prometheus    
```  

4)部署prometheus的rbac  
```
cat prometheus-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
- apiGroups:
  - ""
  resources:
  - nodes
  - services
  - endpoints
  - pods
  - nodes/proxy
  verbs:
  - get
  - list
  - watch
- apiGroups:
  - ""
  resources:
  - configmaps
  - nodes/metrics
  verbs:
  - get
- nonResourceURLs:
  - /metrics
  verbs:
  - get
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: kube-system
```  

```
# kubectl create -f prometheus-rbac.yaml
serviceaccount/prometheus created
clusterrole.rbac.authorization.k8s.io/prometheus created
clusterrolebinding.rbac.authorization.k8s.io/prometheus created
```  

5)ConfigMap volume rbac 创建完毕后，就可以创建prometheus.deploy.yaml  
```
# kubectl create -f prometheus.deploy.yaml
deployment.extensions/prometheus created

# kubectl get pod -n kube-system |grep prometheus
prometheus-dd856f675-jn9v2              1/1     Running            0          15s
```  

6)创建prometheus的svc  
```
cat prometeheus-svc.yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: kube-system
  labels:
    app: prometheus
spec:
  selector:
    app: prometheus
  type: NodePort
  ports:
    - name: web
      port: 9090
      targetPort: http
```  

```
# kubectl create -f prometeheus-svc.yaml
service/prometheus created

# kubectl get svc -n kube-system |grep prometheus
prometheus             NodePort    10.101.143.162           9090:32331/TCP           18s
```  
通过浏览器访问prometheus的web接口，端口号为32331  





