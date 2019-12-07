- 第一步建立一个 ServiceMonitor 对象，用于 Prometheus 添加监控项
- 第二步为 ServiceMonitor 对象关联 metrics 数据接口的一个 Service 对象
- 第三步确保 Service 对象可以正确获取到 metrics 数据

```
$ kubectl get pods -n kube-system
NAME                                          READY     STATUS    RESTARTS   AGE
etcd-master                                   1/1       Running   0          2h
$ kubectl get pod etcd-master -n kube-system -o yaml
......
spec:
  containers:
  - command:
    - etcd
    - --peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
    - --listen-client-urls=https://127.0.0.1:2379               #修改为0.0.0.0:2379
    - --advertise-client-urls=https://127.0.0.1:2379
    - --client-cert-auth=true
    - --peer-client-cert-auth=true
    - --data-dir=/var/lib/etcd
    - --cert-file=/etc/kubernetes/pki/etcd/server.crt
    - --key-file=/etc/kubernetes/pki/etcd/server.key
    - --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    - --peer-key-file=/etc/kubernetes/pki/etcd/peer.key
    - --peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
    image: k8s.gcr.io/etcd-amd64:3.1.12
    imagePullPolicy: IfNotPresent
    livenessProbe:
      exec:
        command:
        - /bin/sh
        - -ec
        - ETCDCTL_API=3 etcdctl --endpoints=127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt
          --cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt --key=/etc/kubernetes/pki/etcd/healthcheck-client.key
          get foo
      failureThreshold: 8
      initialDelaySeconds: 15
      periodSeconds: 10
      successThreshold: 1
      timeoutSeconds: 15
    name: etcd
    resources: {}
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /var/lib/etcd
      name: etcd-data
    - mountPath: /etc/kubernetes/pki/etcd
      name: etcd-certs
......
  tolerations:
  - effect: NoExecute
    operator: Exists
  volumes:
  - hostPath:
      path: /var/lib/etcd
      type: DirectoryOrCreate
    name: etcd-data
  - hostPath:
      path: /etc/kubernetes/pki/etcd
      type: DirectoryOrCreate
    name: etcd-certs
......
```

可以看到 etcd 使用的证书都对应在节点的 /etc/kubernetes/pki/etcd 这个路径下面
```
$ kubectl -n monitoring create secret generic etcd-certs --from-file=/etc/kubernetes/pki/etcd/healthcheck-client.crt --from-file=/etc/kubernetes/pki/etcd/healthcheck-client.key --from-file=/etc/kubernetes/pki/etcd/ca.crt
secret "etcd-certs" created
```

```
# vim protmetheus-prometheus.yaml
  nodeSelector:
    beta.kubernetes.io/os: linux
  replicas: 2
  secrets:         #添加次选项
  - etcd-certs
  
#应用后kubernetes-k8s会重新创建
# kubectl apply -f protmetheus-prometheus.yaml

#可以查看prometheus资源对象
# kubectl get prometheus -n monitoring
NAME    AGE
k8s     9d

#可以查看证书配置是否生效
# kubectl get prometheus k8s -n monitoring -o yaml


#查看证书是否生效
$ kubectl exec -it prometheus-k8s-0 /bin/sh -n monitoring
Defaulting container name to prometheus.
Use 'kubectl describe pod/prometheus-k8s-0 -n monitoring' to see all of the containers in this pod.
/ $ ls /etc/prometheus/secrets/etcd-certs/
ca.crt      healthcheck-client.crt  healthcheck-client.key
```

创建 ServiceMonitor
---

# vim prometheus-serviceMonitorEtcd.yaml
```
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: etcd-k8s
  namespace: monitoring
  labels:
    k8s-app: etcd-k8s
spec:
  jobLabel: k8s-app           #取一个表情为k8s-app的对应上边的值为etcd-k8s
  endpoints:
  - port: port
    interval: 30s             #30秒采集一次数据
    scheme: https
    tlsConfig:
      caFile: /etc/prometheus/secrets/etcd-certs/ca.crt
      certFile: /etc/prometheus/secrets/etcd-certs/healthcheck-client.crt
      keyFile: /etc/prometheus/secrets/etcd-certs/healthcheck-client.key
      insecureSkipVerify: true
  selector:
    matchLabels:
      k8s-app: etcd
  namespaceSelector:
    matchNames:
    - kube-system
```

关于 ServiceMonitor 属性的更多用法可以查看文档：https://github.com/coreos/prometheus-operator/blob/master/Documentation/api.md


