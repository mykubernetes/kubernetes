
1、安装  
```
git clone https://github.com/coreos/kube-prometheus.git
cd kube-prometheus
kubectl create -f manifests/setup
kubectl create -f manifests/
```

2、修改kubelet服务发现配置
```
# cd manifests/
# cat prometheus-serviceMonitorKubelet.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    k8s-app: kubelet
  name: kubelet                    #定义的名称
  namespace: monitoring
spec:
  endpoints:
  - bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    honorLabels: true
    interval: 30s
    port: http-metrics              #去掉https-metrics的s    #这里定义的就是在svc上的端口名称
    scheme: http                    #去掉https的s
#    tlsConfig:                     #注释证书
#      insecureSkipVerify: true     #
  - bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
    honorLabels: true
    interval: 30s
    path: /metrics/cadvisor
    port: http-metrics              #去掉https-metrics的s    #这里定义的就是在svc上的端口名称
    scheme: http                    #去掉https的s
#    tlsConfig:                     #注释证书
#      insecureSkipVerify: true     #
  jobLabel: k8s-app
  namespaceSelector:                #匹配命名空间，代表去匹配kube-system命名空间下匹配，具有k8s-app=kubelet的标签，会将匹配的标签纳入我们prometheus监控中
    matchNames:
    - kube-system
  selector:                         #匹配kube-system命名空间下具有k8s-app=kube-scheduler标签的svc
    matchLabels:
      k8s-app: kubelet
```

查看svc是否有标签
```
# kubectl get svc -n kube-system -l k8s-app=kubelet
NAME      TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)     AGE
kubelet   ClusterIP   None         <none>        10250/TCP   3d
```

此处忽略，理解即可
```
  endpoints:
  - port: http
    scheme: http
    path: /prometheus/metrics
```

查看是否发现后端服务
```
# kubectl get ep -n kube-system |grep kubelet
kubelet                                        10.4.192.35:10255,10.4.192.35:4194,10.4.192.35:10250       3d
```

如果kubelet需要认证，需要手动添加正式测试
```
curl -k --cert /etc/kubernetes/ssl/node.pem --key /etc/kubernetes/ssl/node-key.pem https://10.4.192.35:10250/metrics/cadvisor
```

3、查看crd是否部署成功
```
# kubectl get crd |grep coreos
alertmanagers.monitoring.coreos.com     48m
prometheuses.monitoring.coreos.com      48m
prometheusrules.monitoring.coreos.com   48m
servicemonitors.monitoring.coreos.com   48m
```

4、查看prometheus是否部署成功
```
# kubectl get pod -n monitoring
NAME                                   READY   STATUS    RESTARTS   AGE
alertmanager-main-0                    2/2     Running   0          49m
alertmanager-main-1                    2/2     Running   0          48m
alertmanager-main-2                    2/2     Running   0          48m
grafana-545d8c5576-8lgvg               1/1     Running   0          51m
kube-state-metrics-c86f5648c-4ffdb     4/4     Running   0          25s
node-exporter-7hthp                    2/2     Running   0          51m
node-exporter-r7np2                    2/2     Running   0          51m
node-exporter-ssbdr                    2/2     Running   0          51m
node-exporter-wd7jm                    2/2     Running   0          51m
prometheus-adapter-66fc7797fd-bd7gx    1/1     Running   0          51m
prometheus-k8s-0                       3/3     Running   1          49m
prometheus-k8s-1                       3/3     Running   1          49m
prometheus-operator-7cfc488cdd-wtm8w   1/1     Running   0          51m
```

5、prometheus和alertmanager采用的StatefulSet创建,其他的Pod则采用deployment创建
```
# kubectl get statefulsets -n monitoring
NAME                READY   AGE
alertmanager-main   3/3     52m
prometheus-k8s      2/2     52m

# kubectl get deployments -n monitoring
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
grafana               1/1     1            1           53m
kube-state-metrics    1/1     1            1           53m
prometheus-adapter    1/1     1            1           53m
prometheus-operator   1/1     1            1           53m
```  

6、查看service
```
# kubectl get svc -n monitoring |egrep  "prometheus|grafana|alertmanage"
alertmanager-main       ClusterIP   10.106.59.84            9093/TCP            59m
alertmanager-operated   ClusterIP   None                    9093/TCP,6783/TCP   57m
grafana                 ClusterIP   10.110.58.16            3000/TCP            59m
prometheus-adapter      ClusterIP   10.105.34.241           443/TCP             59m
prometheus-k8s          ClusterIP   10.102.246.32           9090/TCP            59m
prometheus-operated     ClusterIP   None                    9090/TCP            57m
prometheus-operator     ClusterIP   None                    8080/TCP            59m
```  

7、集群外访问prometheus
```
kubectl edit svc -n monitoring prometheus-k8s
kubectl edit svc -n monitoring grafana
kubectl edit svc -n monitoring alertmanager-main

修改 type: NodePort
```  


8、解决kube-controller连接拒绝的问题
```
# cat /etc/kubernetes/manifests/kube-controller-manager-kubeconfig.yaml 
apiVersion: v1
kind: Pod
metadata:
  name: kube-controller-manager
  namespace: kube-system
  labels:
    k8s-app: kube-controller-manager
  annotations:
    kubespray.etcd-cert/serial: "840C46312E82CBFB"
    kubespray.controller-manager-cert/serial: "C22517CF831DDCC5"
spec:
  hostNetwork: true
  dnsPolicy: ClusterFirst
  containers:
  - name: kube-controller-manager
    image: 10.4.192.35:5000/quay.io/coreos/hyperkube:v1.9.0_viper_pach3_coreos.0
    imagePullPolicy: IfNotPresent
    resources:
      limits:
        cpu: 1000m
        memory: 1024M
      requests:
        cpu: 100m
        memory: 100M
    command:
    - /hyperkube
    - controller-manager
    - --kubeconfig=/etc/kubernetes/kube-controller-manager-kubeconfig.yaml
    - --leader-elect=true
    - --service-account-private-key-file=/etc/kubernetes/ssl/apiserver-key.pem
    - --root-ca-file=/etc/kubernetes/ssl/ca.pem
    - --cluster-signing-cert-file=/etc/kubernetes/ssl/ca.pem
    - --cluster-signing-key-file=/etc/kubernetes/ssl/ca-key.pem
    - --enable-hostpath-provisioner=false
    - --node-monitor-grace-period=60s
    - --node-monitor-period=20s
    - --pod-eviction-timeout=10s
    - --profiling=false
    - --terminated-pod-gc-threshold=12500
    - --v=2
    - --use-service-account-credentials=true
    - --allocate-node-cidrs=true
    - --cluster-cidr=10.224.0.0/13
    - --service-cluster-ip-range=10.233.0.0/18
    - --node-cidr-mask-size=24
    - --feature-gates=CustomPodDNS=true,Initializers=true,PersistentLocalVolumes=true,VolumeScheduling=true,MountPropagation=true,Accelerators=true
    - --address=127.0.0.1     #将监听地址修改为0.0.0.0
    livenessProbe:
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10252
      initialDelaySeconds: 30
      timeoutSeconds: 10
    volumeMounts:
    - mountPath: /etc/ssl
      name: ssl-certs-host
      readOnly: true
    - mountPath: /etc/pki/tls
      name: etc-pki-tls
      readOnly: true
    - mountPath: /etc/pki/ca-trust
      name: etc-pki-ca-trust
      readOnly: true
    - mountPath: "/etc/kubernetes/ssl"
      name: etc-kube-ssl
      readOnly: true
    - mountPath: "/etc/kubernetes/kube-controller-manager-kubeconfig.yaml"
      name: kubeconfig
      readOnly: true
  volumes:
  - name: ssl-certs-host
    hostPath:
      path: /etc/ssl
  - name: etc-pki-tls
    hostPath:
      path: /etc/pki/tls
  - name: etc-pki-ca-trust
    hostPath:
      path: /etc/pki/ca-trust
  - name: etc-kube-ssl
    hostPath:
      path: "/etc/kubernetes/ssl"
  - name: kubeconfig
    hostPath:
      path: "/etc/kubernetes/kube-controller-manager-kubeconfig.yaml"
```  
# 修改完成后将配置文件移除，再移入


9、解决kube-scheduler连接拒绝的问题
```
# cat /etc/kubernetes/manifests/kube-scheduler.manifest
apiVersion: v1
kind: Pod
metadata:
  name: kube-scheduler
  namespace: kube-system
  labels:
    k8s-app: kube-scheduler
  annotations:
    kubespray.scheduler-cert/serial: "C22517CF831DDCC4"
spec:
  hostNetwork: true
  dnsPolicy: ClusterFirst
  containers:
  - name: kube-scheduler
    image: 10.4.192.35:5000/quay.io/coreos/hyperkube:v1.9.0_viper_pach3_coreos.0
    imagePullPolicy: IfNotPresent
    resources:
      limits:
        cpu: 1000m
        memory: 1024M
      requests:
        cpu: 80m
        memory: 170M
    command:
    - /hyperkube
    - scheduler
    - --leader-elect=true
    - --kubeconfig=/etc/kubernetes/kube-scheduler-kubeconfig.yaml
    - --use-legacy-policy-config
    - --policy-config-file=/etc/kubernetes/kube-scheduler-policy.json
    - --profiling=false
    - --v=2
    - --feature-gates=CustomPodDNS=true,Initializers=true,PersistentLocalVolumes=true,VolumeScheduling=true,MountPropagation=true,Accelerators=true
    - --address=127.0.0.1          #将监听地址修改为0.0.0.0
    livenessProbe:
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: 10251
      initialDelaySeconds: 30
      timeoutSeconds: 10
    volumeMounts:
    - mountPath: /etc/ssl
      name: ssl-certs-host
      readOnly: true
    - mountPath: /etc/pki/tls
      name: etc-pki-tls
      readOnly: true
    - mountPath: /etc/pki/ca-trust
      name: etc-pki-ca-trust
      readOnly: true
    - mountPath: "/etc/kubernetes/ssl"
      name: etc-kube-ssl
      readOnly: true
    - mountPath: "/etc/kubernetes/kube-scheduler-kubeconfig.yaml"
      name: kubeconfig
      readOnly: true
    - mountPath: "/etc/kubernetes/kube-scheduler-policy.json"
      name: kube-scheduler-policy
      readOnly: true
  volumes:
  - name: ssl-certs-host
    hostPath:
      path: /etc/ssl
  - name: etc-pki-tls
    hostPath:
      path: /etc/pki/tls
  - name: etc-pki-ca-trust
    hostPath:
      path: /etc/pki/ca-trust
  - name: etc-kube-ssl
    hostPath:
      path: "/etc/kubernetes/ssl"
  - name: kubeconfig
    hostPath:
      path: "/etc/kubernetes/kube-scheduler-kubeconfig.yaml"
  - name: kube-scheduler-policy
    hostPath:
      path: "/etc/kubernetes/kube-scheduler-policy.json"
```
# 修改完成后将配置文件移除，再移入

10、解决kube-scheduler未发现相关pod  
查看标签
```
# kubectl get pod -n kube-system |grep kube-scheduler
kube-scheduler                        1/1       Running            1          5h

# kubectl describe  pod -n kube-system kube-scheduler |grep Labels:
Labels:       k8s-app=kube-scheduler
```

自定义一个svc配置并应用注意标签配置
```
# cat prometheus-kubeSchedulerService.yaml 
apiVersion: v1
kind: Service
metadata:
  namespace: kube-system
  name: kube-scheduler
  labels:
    k8s-app=kube-scheduler
spec:
  selector:
    k8s-app=kube-controller-manager
  ports:
  - name: http-metrics
    port: 10251
    targetPort: 10251
```  

查看svc是否有标签
```
# kubectl get svc -n kube-system -l k8s-app=kube-scheduler
NAME                                  TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)     AGE
kube-scheduler-prometheus-discovery   ClusterIP   None         <none>        10251/TCP   3d
```

查看是否发现后端服务
```
# kubectl get ep -n kube-system |grep kube-scheduler
kube-scheduler-prometheus-discovery            10.4.192.35:10251,10.4.192.35:10251                        3d
```

10、解决kube-controller未发现相关pod  
查看标签
```
# kubectl get pod -n kube-system |grep kube-controller
kube-controller-manager               1/1       Running            4          5h

# kubectl describe pod kube-controller-manager -n kube-system |grep Labels:
Labels:       k8s-app=kube-controller-manager
```

自定义一个svc配置并应用注意标签配置
```
# cat prometheus-kubeControllerService.yaml 
apiVersion: v1
kind: Service
metadata:
  namespace: kube-system
  name: kube-Controller
  labels:
    k8s-app: kube-Controller
spec:
  selector:
    k8s-app=kube-controller-manager
  ports:
  - name: http-metrics
    port: 10252
    targetPort: 10252
```  

查看svc是否有标签
```
# kubectl get svc -n kube-system -l k8s-app=kube-controller-manager
NAME                                           TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)     AGE
kube-controller-manager-prometheus-discovery   ClusterIP   None         <none>        10252/TCP   3d
```

查看是否发现后端服务
```
# kubectl get ep -n kube-system |grep controller
kube-controller-manager-prometheus-discovery   10.4.192.35:10252                                          3d
```
