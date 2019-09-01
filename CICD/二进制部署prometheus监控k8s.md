安装 Prometheus  
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
ExecStart=/data/apps/prometheus/prometheus --
config.file=/data/apps/prometheus/prometheus.yml \
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
  scrape_interval: 15s # Set the scrape interval to every 15 seconds.
Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default
is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - 127.0.0.1:9093

# Load rules once and periodically evaluate them according to the global
'evaluation_interval'.
rule_files:
  - "rules/*.rules"
  #- "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries
scraped from this config.
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


















