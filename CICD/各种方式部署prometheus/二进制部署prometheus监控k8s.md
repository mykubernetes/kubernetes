安装 Prometheus  
---

1、下载二进制包  
```
# wget https://github.com/prometheus/prometheus/releases/download/v2.6.1/prometheus-2.6.1.linux-amd64.tar.gz
# tar zxfv prometheus-2.6.1.linux-amd64.tar.gz
# mv prometheus-2.6.1.linux-amd64 /data/apps/prometheus
```  

2、配置系统服务  
```
# vim /usr/lib/systemd/system/prometheus.service
[Unit]
Description=prometheus
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/data/apps/prometheus/prometheus \
--config.file=/data/apps/prometheus/prometheus.yml \
--storage.tsdb.path=/data/apps/prometheus/data \
--web.console.libraries=/data/apps/prometheus/console_libraries \
--web.console.templates=/data/apps/prometheus/consoles \
--web.enable-lifecycle
Restart=on-failure

[Install]
WantedBy=multi-user.target
```  

3、创建用户  
```
# groupadd prometheus
# useradd -g prometheus -m -d /data/apps/prometheus/data -s /sbin/nologin prometheus
```  

4、验证安装  
```
# systemctl start prometheus
# systemctl enable prometheus
# /data/apps/prometheus/prometheus --version
prometheus, version 2.6.1 (branch: HEAD, revision:
b639fe140c1f71b2cbad3fc322b17efe60839e7e)
build user: root@4c0e286fe2b3
build date: 20190115-19:12:04
go version: go1.11.4

# curl localhost:9090
<a href="/graph">Found</a>.
```  

5、配置prometheus  
```
# vim prometheus.yml
# my global config
global:
  scrape_interval: 15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - 127.0.0.1:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  - "rules/*.rules"
  #- "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.
    
    static_configs:
    - targets: ['alertmanager-edge.test.ziji.work:9090']
  - job_name: 'kubernetes-nodes'
    static_configs:
      - targets:
        - 10.211.18.7:9100
        - 10.211.18.3:9100
        - 10.211.18.14:9100
        - 10.211.18.17:9100
        - 10.211.18.6:9100
        - 10.211.18.10:9100
  
  - job_name: 'ceph'
    static_configs:
      - targets: ['127.0.0.1:9128']
        labels:
          instance: 10.211.18.5

  - job_name: 'kube-state-metrics'
    static_configs:
      - targets: ['kube-edge.test.ziji.work']
        labels:
          instance: kube-state-metrics
          k8scluster: test-k8s-cluster

  - job_name: kubernetes-nodes-kubelet
    static_configs:
      - targets:
        - 10.211.18.7:10250
        - 10.211.18.3:10250
        - 10.211.18.14:10250
        - 10.211.18.17:10250
        - 10.211.18.6:10250
        labels:
          k8scluster: test-k8s-cluster
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)
    scheme: https
    tls_config:
      ca_file: /data/apps/prometheus/rbac/ca.crt
      insecure_skip_verify: true
    bearer_token_file: /data/apps/prometheus/rbac/token
  - job_name: kubernetes-nodes-cadvisor
    static_configs:
      - targets:
        - 10.211.18.7:10250
        - 10.211.18.3:10250
        - 10.211.18.14:10250
        - 10.211.18.17:10250
        - 10.211.18.6:10250
        labels:
          k8scluster: test-k8s-cluster
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)
    - target_label: __metrics_path__
      replacement: /metrics/cadvisor
    scheme: https
    tls_config:
      ca_file: /data/apps/prometheus/rbac/ca.crt
      insecure_skip_verify: true
    bearer_token_file: /data/apps/prometheus/rbac/token
```  

安装node_exporter  
---

1、下载二进制包
```
# wget https://github.com/prometheus/node_exporter/releases/download/v0.17.0/node_exporter-0.17.0.linux-amd64.tar.gz
# tar zxf node_exporter-0.17.0.linux-amd64.tar.gz
# mv node_exporter-0.17.0.linux-amd64 /data/apps/node_exporter
```  

2、创建Systemd服务  
```
[Unit]
Description=https://prometheus.io

[Service]
Restart=on-failure
ExecStart=/data/apps/node_exporter/node_exporter --collector.systemd \
--collector.systemd.unit-whitelist=(docker|kubelet|kube-proxy|flanneld).service

[Install]
WantedBy=multi-user.target
``` 

3、启动Node exporter  
```
# systemctl enable node_exporter
# systemctl start node_exporter
```  
Node Exporter 默认的抓取地址为 http://IP:9100/metrics  


安装 grafana
---

1、下载rpm包  
```
# wget https://dl.grafana.com/oss/release/grafana-6.2.0-1.x86_64.rpm
# yum localinstall grafana-6.2.0-1.x86_64.rpm
```  

2、启动grafana服务  
```
# systemctl enable grafana-server
# systemctl start grafana-server
```  

部署 kube-state-metrics  
---

1、创建yaml文件  
```
# mkdir prometheus
# cd prometheus
# vim kube-state-metrics-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube-state-metrics
  namespace: kube-system
  labels:
    k8s-app: kube-state-metrics
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
    version: v1.3.0
spec:
  selector:
    matchLabels:
      k8s-app: kube-state-metrics
      version: v1.3.0
  replicas: 1
  template:
    metadata:
      labels:
        k8s-app: kube-state-metrics
        version: v1.3.0
    spec:
      priorityClassName: system-cluster-critical
      serviceAccountName: kube-state-metrics
      containers:
      - name: kube-state-metrics
        image: quay.io/coreos/kube-state-metrics:v1.3.0
        ports:
        - name: http-metrics
          containerPort: 8080
        - name: telemetry
          containerPort: 8081
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 5
          timeoutSeconds: 5
      - name: addon-resizer
        image: k8s.gcr.io/addon-resizer:1.8.5
        resources:
          limits:
            cpu: 100m
            memory: 30Mi
          requests:
            cpu: 100m
            memory: 30Mi
        env:
          - name: MY_POD_NAME
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
          - name: MY_POD_NAMESPACE
            valueFrom:
              fieldRef:
                fieldPath: metadata.namespace
        volumeMounts:
          - name: config-volume
            mountPath: /etc/config
        command:
          - /pod_nanny
          - --config-dir=/etc/config
          - --container=kube-state-metrics
          - --cpu=100m
          - --extra-cpu=1m
          - --memory=100Mi
          - --extra-memory=2Mi
          - --threshold=5
          - --deployment=kube-state-metrics
      volumes:
        - name: config-volume
          configMap:
            name: kube-state-metrics-config
---
# Config map for resource configuration.
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-state-metrics-config
  namespace: kube-system
  labels:
    k8s-app: kube-state-metrics
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
data:
  NannyConfiguration: |-
    apiVersion: nannyconfig/v1alpha1
    kind: NannyConfiguration
```  

2、创建RBAC文件  
```
# vim kube-state-metrics-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kube-state-metrics
  namespace: kube-system
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kube-state-metrics
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
rules:
- apiGroups: [""]
  resources:
  - configmaps
  - secrets
  - nodes
  - pods
  - services
  - resourcequotas
  - replicationcontrollers
  - limitranges
  - persistentvolumeclaims
  - persistentvolumes
  - namespaces
  - endpoints
  verbs: ["list", "watch"]
- apiGroups: ["extensions"]
  resources:
  - daemonsets
  - deployments
  - replicasets
  verbs: ["list", "watch"]
- apiGroups: ["apps"]
  resources:
  - statefulsets
  verbs: ["list", "watch"]
- apiGroups: ["batch"]
  resources:
  - cronjobs
  - jobs
  verbs: ["list", "watch"]
- apiGroups: ["autoscaling"]
  resources:
  - horizontalpodautoscalers
  verbs: ["list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: kube-state-metrics-resizer
  namespace: kube-system
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
rules:
- apiGroups: [""]
  resources:
  - pods
  verbs: ["get"]
- apiGroups: ["extensions"]
  resources:
  - deployments
  resourceNames: ["kube-state-metrics"]
  verbs: ["get", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kube-state-metrics
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kube-state-metrics
subjects:
- kind: ServiceAccount
  name: kube-state-metrics
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kube-state-metrics
  namespace: kube-system
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kube-state-metrics-resizer
subjects:
- kind: ServiceAccount
  name: kube-state-metrics
  namespace: kube-system
```  

3、创建 kube-state-metrics-service.yaml  
```
# vim kube-state-metrics-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: kube-state-metrics
  namespace: kube-system
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
    kubernetes.io/name: "kube-state-metrics"
  annotations:
    prometheus.io/scrape: 'true'
spec:
  ports:
  - name: http-metrics
    port: 8080
    targetPort: http-metrics
    protocol: TCP
  - name: telemetry
    port: 8081
    targetPort: telemetry
    protocol: TCP
  selector:
    k8s-app: kube-state-metrics
```  

安装alertmanager
---

1、下载二进制包  
```
# wget https://github.com/prometheus/alertmanager/releases/download/v0.16.2/alertmanager-0.16.2.linux-amd64.tar.gz
# tar zxvf alertmanager-0.16.2.linux-amd64.tar.gz
# mv alertmanager-0.16.2.linux-amd64 /data/apps/alertmanager
```  

2、创建系统服务  
```
# vim /usr/lib/systemd/system/alertmanager.service
[Unit]
Description=Alertmanager
After=network.target

[Service]
Type=simple
User=alertmanager
ExecStart=/data/apps/alertmanager/alertmanager \
--config.file=/data/apps/alertmanager/alertmanager.yml \
--storage.path=/data/apps/alertmanager/data
Restart=on-failure

[Install]
WantedBy=multi-user.target
```  

3、启动服务  
```
# systemctl enable alertmanager
# systemctl start alertmanager
```  

4、配置 alertmanager 告警通知  
```
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.139.com:25'
  smtp_from: 'zijiwork@139.com'
  smtp_auth_username: 'username'
  smtp_auth_password: 'password'
  smtp_require_tls: false

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'mail'

receivers:
- name: 'mail'
  #webhook_configs:
  email_configs:
  #- url: 'http://127.0.0.1:5001/'
  - to: 'admin@ziji.work'
    send_resolved: true
```  

5、配置rules规则  
```
# mkdir rules && cd rules

# vim general.rules
groups:
- name: general.rules
  rules:

  #Alert for any instance that is unreachable for >5 minutes.
  - alert: InstanceDown
    expr: up == 0
    for: 1m
    labels:
      severity: error
    annotations:
      summary: "Instance {{ $labels.instance }} down"
      description: "{{ $labels.instance }} of job {{ $labels.job }} hasbeen down for more than 1 minutes."
      
      
# vim kubernetes.rules
groups:
- name: general.rules
  rules:

  # Alert for any instance that is unreachable for >5 minutes.
  - alert: InstanceDown
    expr: up == 0
    for: 1m
    labels:
      severity: error
    annotations:
      summary: "Instance {{ $labels.instance }} down"
      description: "{{ $labels.instance }} of job {{ $labels.job }} hasbeen down for more than 1 minutes."

# cat kubernetes.rules
groups:
- name: kubernetes
  rules:
  - alert: PodDown
    expr: kube_pod_status_phase{phase="Unknown"} == 1 or kube_pod_status_phase{phase="Failed"} == 1
    for: 1m
    labels:
      severity: error
      service: prometheus_bot
      receiver_group: "{{ $labels.k8scluster}}_{{ $labels.namespace }}"
    annotations:
      summary: Pod Down
      k8scluster: "{{ $labels.k8scluster}}"
      namespace: "{{ $labels.namespace }}"
      pod: "{{ $labels.pod }}"
      container: "{{ $labels.container }}"
  - alert: PodRestart
    expr: changes(kube_pod_container_status_restarts_total{pod !~"analyzer.*"}[10m]) > 0
    for: 1m
    labels:
      severity: error
      service: prometheus_bot
      receiver_group: "{{ $labels.k8scluster}}_{{ $labels.namespace }}"
    annotations:
      summary: Pod Restart
      k8scluster: "{{ $labels.k8scluster}}"
      namespace: "{{ $labels.namespace }}"
      pod: "{{ $labels.pod }}"
      container: "{{ $labels.container }}"
  - alert: NodeUnschedulable
    expr: kube_node_spec_unschedulable == 1
    for: 5m
    labels:
      severity: error
      service: prometheus_bot
      receiver_group: "{{ $labels.k8scluster}}_{{ $labels.namespace }}"
    annotations:
      summary: Node Unschedulable
      k8scluster: "{{ $labels.k8scluster}}"
      node: "{{ $labels.node }}"
  - alert: NodeStatusError
    expr: kube_node_status_condition{condition="Ready", status!="true"} == 1
    for: 5m
    labels:
      severity: error
      service: prometheus_bot
      receiver_group: "{{ $labels.k8scluster}}_{{ $labels.namespace }}"
    annotations:
      summary: Node Status Error
      k8scluster: "{{ $labels.k8scluster}}"
      node: "{{ $labels.node }}"
  - alert: DaemonsetUnavailable
    expr: kube_daemonset_status_number_unavailable > 0
    for: 5m
    labels:
      severity: error
      service: prometheus_bot
      receiver_group: "{{ $labels.k8scluster}}_{{ $labels.namespace }}"
    annotations:
      summary: Daemonset Unavailable
      k8scluster: "{{ $labels.k8scluster}}"
      namespace: "{{ $labels.namespace }}"
      daemonset: "{{ $labels.daemonset }}"
  - alert: JobFailed
    expr: kube_job_status_failed == 1
    for: 5m
    labels:
      severity: error
      service: prometheus_bot
      receiver_group: "{{ $labels.k8scluster}}_{{ $labels.namespace }}"
    annotations:
      summary: Job Failed
      k8scluster: "{{ $labels.k8scluster}}"
      namespace: "{{ $labels.namespace }}"
      job: "{{ $labels.exported_job }}"


# vim node.rules
groups:
- name: node.rules
  rules:
  - alert: NodeFilesystemUsage
    expr: 100 - (node_filesystem_free_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"} * 100) > 80
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "{{$labels.instance}}: {{$labels.mountpoint }} 分区使用过高"
      description: "{{$labels.instance}}: {{$labels.mountpoint }} 分区使用大于 80% (当前值: {{ $value }})"
  - alert: NodeMemoryUsage
    expr: 100 - (node_memory_MemFree_bytes+node_memory_Cached_bytes+node_memory_Buffers_bytes) / node_memory_MemTotal_bytes * 100 > 80
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "{{$labels.instance}}: 内存使用过高"
      description: "{{$labels.instance}}: 内存使用大于 80% (当前值:{{ $value }})"
  - alert: NodeCPUUsage
    expr: 100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance) * 100) > 80
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "{{$labels.instance}}: CPU 使用过高"
      description: "{{$labels.instance}}: CPU 使用大于 80% (当前值:{{ $value }})"
```  
