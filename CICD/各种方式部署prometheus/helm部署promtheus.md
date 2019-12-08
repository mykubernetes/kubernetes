二进制部署需要修改

发现ControllerManager
---
```
kubeControllerManager:
  enabled: true

  ## If your kube controller manager is not deployed as a pod, specify IPs it can be found on
  ##
  endpoints: []           #去掉中括号，并条件IP地址
  # - 10.141.4.22
  # - 10.141.4.23
  # - 10.141.4.24

  ## If using kubeControllerManager.endpoints only the port and targetPort are used
  ##
  service:
    port: 10252
    targetPort: 10252
    # selector:           #如果使用endpoints需要注释此两行
    #   component: kube-controller-manager

  serviceMonitor:
    ## Scrape interval. If not set, the Prometheus default scrape interval is used.
    ##
    interval: ""

    ## Enable scraping kube-controller-manager over https.
    ## Requires proper certs (not self-signed) and delegated authentication/authorization checks
    ##
    https: false          #如果是https的话使用true
```


发现etcd
---
```
kubeEtcd:
  enabled: true

  ## If your etcd is not deployed as a pod, specify IPs it can be found on
  ##
  endpoints: []            #去掉中括号，并条件IP地址
  # - 10.141.4.22
  # - 10.141.4.23
  # - 10.141.4.24

  ## Etcd service. If using kubeEtcd.endpoints only the port and targetPort are used
  ##
  service:
    port: 2379
    targetPort: 2379
    # selector:            #如果使用endpoints需要注释此两行
    #   component: etcd

  ## Configure secure access to the etcd cluster by loading a secret into prometheus and
  ## specifying security configuration below. For example, with a secret named etcd-client-cert
  ##
  ## serviceMonitor:
  ##   scheme: https
  ##   insecureSkipVerify: false
  ##   serverName: localhost
  ##   caFile: /etc/prometheus/secrets/etcd-client-cert/etcd-ca
  ##   certFile: /etc/prometheus/secrets/etcd-client-cert/etcd-client
  ##   keyFile: /etc/prometheus/secrets/etcd-client-cert/etcd-client-key
  ##
  serviceMonitor:
    ## Scrape interval. If not set, the Prometheus default scrape interval is used.
    ##
    interval: ""
    scheme: http              #修改成https
    insecureSkipVerify: false
    serverName: ""
    caFile: ""                #添加/etc/prometheus/secrets/etcd-client-cert/ca.pem
    certFile: ""              #添加/etc/prometheus/secrets/etcd-client-cert/etcd.pem
    keyFile: ""               #添加/etc/prometheus/secrets/etcd-client-cert/etcd-key.pem

    ## 	metric relabel configs to apply to samples before ingestion.
    ##
    metricRelabelings: []
    # - action: keep
    #   regex: 'kube_(daemonset|deployment|pod|namespace|node|statefulset).+'
    #   sourceLabels: [__name__]

    # 	relabel configs to apply to samples before ingestion.
    ##
    relabelings: []
    # - sourceLabels: [__meta_kubernetes_pod_node_name]
    #   separator: ;
    #   regex: ^(.*)$
    #   targetLabel: nodename
    #   replacement: $1
    #   action: replace
```

创建etcd的secret文件
```
# kubectl create secret generic etcd-certs -n monitoring --from-file=/etc/kubernetes/pki/ca.pem --from-file=/etc/kubernetes/pki/etcd-key.pem --from-file=/etc/kubernetes/pki/etcd.pem

查看是否创建
#kubectl get secret -n monitoring etcd-certs -o yaml
```

在prometheus字段里添加secret证书
```
prometheus:

  enabled: true

  ## Annotations for Prometheus
  ##
  annotations: {}

  ## Service account for Prometheuses to use.
  ## ref: https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/
  ##
  serviceAccount:
    create: true
    name: ""

  ## Configuration for Prometheus service
  ##
  service:
    annotations: {}
    labels: {}
    clusterIP: ""

    ## Port for Prometheus Service to listen on
    ##
    port: 9090

    ## To be used with a proxy extraContainer port
    targetPort: 9090

    ## List of IP addresses at which the Prometheus server service is available
    ## Ref: https://kubernetes.io/docs/user-guide/services/#external-ips
    ##
    externalIPs: []

    ## Port to expose on each node
    ## Only used if service.type is 'NodePort'
    ##
    nodePort: 30090

    ## Loadbalancer IP
    ## Only use if service.type is "loadbalancer"
    loadBalancerIP: ""
    loadBalancerSourceRanges: []
    ## Service type
    ##
    type: ClusterIP

    sessionAffinity: ""

  ## Configuration for creating a separate Service for each statefulset Prometheus replica
  ##
  servicePerReplica:
    enabled: false
    annotations: {}

    ## Port for Prometheus Service per replica to listen on
    ##
    port: 9090

    ## To be used with a proxy extraContainer port
    targetPort: 9090

    ## Port to expose on each node
    ## Only used if servicePerReplica.type is 'NodePort'
    ##
    nodePort: 30091

    ## Loadbalancer source IP ranges
    ## Only used if servicePerReplica.type is "loadbalancer"
    loadBalancerSourceRanges: []
    ## Service type
    ##
    type: ClusterIP

  ## Configure pod disruption budgets for Prometheus
  ## ref: https://kubernetes.io/docs/tasks/run-application/configure-pdb/#specifying-a-poddisruptionbudget
  ## This configuration is immutable once created and will require the PDB to be deleted to be changed
  ## https://github.com/kubernetes/kubernetes/issues/45398
  ##
  podDisruptionBudget:
    enabled: false
    minAvailable: 1
    maxUnavailable: ""

  ingress:
    enabled: false
    annotations: {}
    labels: {}

    ## Hostnames.
    ## Must be provided if Ingress is enabled.
    ##
    # hosts:
    #   - prometheus.domain.com
    hosts: []

    ## Paths to use for ingress rules - one path should match the prometheusSpec.routePrefix
    ##
    paths: []
    # - /

    ## TLS configuration for Prometheus Ingress
    ## Secret must be manually created in the namespace
    ##
    tls: []
      # - secretName: prometheus-general-tls
      #   hosts:
      #     - prometheus.example.com

  ## Configuration for creating an Ingress that will map to each Prometheus replica service
  ## prometheus.servicePerReplica must be enabled
  ##
  ingressPerReplica:
    enabled: false
    annotations: {}
    labels: {}

    ## Final form of the hostname for each per replica ingress is
    ## {{ ingressPerReplica.hostPrefix }}-{{ $replicaNumber }}.{{ ingressPerReplica.hostDomain }}
    ##
    ## Prefix for the per replica ingress that will have `-$replicaNumber`
    ## appended to the end
    hostPrefix: ""
    ## Domain that will be used for the per replica ingress
    hostDomain: ""

    ## Paths to use for ingress rules
    ##
    paths: []
    # - /

    ## Secret name containing the TLS certificate for Prometheus per replica ingress
    ## Secret must be manually created in the namespace
    tlsSecretName: ""

  ## Configure additional options for default pod security policy for Prometheus
  ## ref: https://kubernetes.io/docs/concepts/policy/pod-security-policy/
  podSecurityPolicy:
    allowedCapabilities: []

  serviceMonitor:
    ## Scrape interval. If not set, the Prometheus default scrape interval is used.
    ##
    interval: ""
    selfMonitor: true

    bearerTokenFile:

    ## 	metric relabel configs to apply to samples before ingestion.
    ##
    metricRelabelings: []
    # - action: keep
    #   regex: 'kube_(daemonset|deployment|pod|namespace|node|statefulset).+'
    #   sourceLabels: [__name__]

    # 	relabel configs to apply to samples before ingestion.
    ##
    relabelings: []
    # - sourceLabels: [__meta_kubernetes_pod_node_name]
    #   separator: ;
    #   regex: ^(.*)$
    #   targetLabel: nodename
    #   replacement: $1
    #   action: replace

  ## Settings affecting prometheusSpec
  ## ref: https://github.com/coreos/prometheus-operator/blob/master/Documentation/api.md#prometheusspec
  ##
  prometheusSpec:

    ## Interval between consecutive scrapes.
    ##
    scrapeInterval: ""

    ## Interval between consecutive evaluations.
    ##
    evaluationInterval: ""

    ## ListenLocal makes the Prometheus server listen on loopback, so that it does not bind against the Pod IP.
    ##
    listenLocal: false

    ## EnableAdminAPI enables Prometheus the administrative HTTP API which includes functionality such as deleting time series.
    ## This is disabled by default.
    ## ref: https://prometheus.io/docs/prometheus/latest/querying/api/#tsdb-admin-apis
    ##
    enableAdminAPI: false

    ## Image of Prometheus.
    ##
    image:
      repository: quay.io/prometheus/prometheus
      tag: v2.13.1

    ## Tolerations for use with node taints
    ## ref: https://kubernetes.io/docs/concepts/configuration/taint-and-toleration/
    ##
    tolerations: []
    #  - key: "key"
    #    operator: "Equal"
    #    value: "value"
    #    effect: "NoSchedule"

    ## Alertmanagers to which alerts will be sent
    ## ref: https://github.com/coreos/prometheus-operator/blob/master/Documentation/api.md#alertmanagerendpoints
    ##
    ## Default configuration will connect to the alertmanager deployed as part of this release
    ##
    alertingEndpoints: []
    # - name: ""
    #   namespace: ""
    #   port: http
    #   scheme: http

    ## External labels to add to any time series or alerts when communicating with external systems
    ##
    externalLabels: {}

    ## Name of the external label used to denote replica name
    ##
    replicaExternalLabelName: ""

    ## If true, the Operator won't add the external label used to denote replica name
    ##
    replicaExternalLabelNameClear: false

    ## Name of the external label used to denote Prometheus instance name
    ##
    prometheusExternalLabelName: ""

    ## If true, the Operator won't add the external label used to denote Prometheus instance name
    ##
    prometheusExternalLabelNameClear: false

    ## External URL at which Prometheus will be reachable.
    ##
    externalUrl: ""

    ## Define which Nodes the Pods are scheduled on.
    ## ref: https://kubernetes.io/docs/user-guide/node-selection/
    ##
    nodeSelector: {}

    ## Secrets is a list of Secrets in the same namespace as the Prometheus object, which shall be mounted into the Prometheus Pods.
    ## The Secrets are mounted into /etc/prometheus/secrets/. Secrets changes after initial creation of a Prometheus object are not
    ## reflected in the running Pods. To change the secrets mounted into the Prometheus Pods, the object must be deleted and recreated
    ## with the new list of secrets.
    ##
    secrets: []            #在此字段添加去掉中括号
    - etcd-certs           #添加刚才创建的secret证书
    
    ## ConfigMaps is a list of ConfigMaps in the same namespace as the Prometheus object, which shall be mounted into the Prometheus Pods.
    ## The ConfigMaps are mounted into /etc/prometheus/configmaps/.
    ##
    configMaps: []

```


发现Scheduler
---
```
kubeScheduler:
  enabled: true

  ## If your kube scheduler is not deployed as a pod, specify IPs it can be found on
  ##
  endpoints: []         #去掉中括号，添加IP地址
  # - 10.141.4.22
  # - 10.141.4.23
  # - 10.141.4.24

  ## If using kubeScheduler.endpoints only the port and targetPort are used
  ##
  service:
    port: 10251
    targetPort: 10251
    # selector:        #二进制部署不需要标签选择，注释此字段
    #   component: kube-scheduler

  serviceMonitor:
    ## Scrape interval. If not set, the Prometheus default scrape interval is used.
    ##
    interval: ""
    ## Enable scraping kube-controller-manager over https.
    ## Requires proper certs (not self-signed) and delegated authentication/authorization checks
    ##
    https: false       #查看是http还是https的

    ## Skip TLS certificate validation when scraping
    insecureSkipVerify: null
```  

修改kubelet
---

```
kubelet:
  enabled: true
  namespace: kube-system

  serviceMonitor:
    ## Scrape interval. If not set, the Prometheus default scrape interval is used.
    ##
    interval: ""

    ## Enable scraping the kubelet over https. For requirements to enable this see
    ## https://github.com/coreos/prometheus-operator/issues/926
    ##
    https: true            #修改为false

    ## Metric relabellings to apply to samples before ingestion
    ##
    cAdvisorMetricRelabelings: []
    # - sourceLabels: [__name__, image]
    #   separator: ;
    #   regex: container_([a-z_]+);
    #   replacement: $1
    #   action: drop
    # - sourceLabels: [__name__]
    #   separator: ;
    #   regex: container_(network_tcp_usage_total|network_udp_usage_total|tasks_state|cpu_load_average_10s)
    #   replacement: $1
    #   action: drop

    # 	relabel configs to apply to samples before ingestion.
    ##
    cAdvisorRelabelings: []
    # - sourceLabels: [__meta_kubernetes_pod_node_name]
    #   separator: ;
    #   regex: ^(.*)$
    #   targetLabel: nodename
    #   replacement: $1
    #   action: replace

    metricRelabelings: []
    # - sourceLabels: [__name__, image]
    #   separator: ;
    #   regex: container_([a-z_]+);
    #   replacement: $1
    #   action: drop
    # - sourceLabels: [__name__]
    #   separator: ;
    #   regex: container_(network_tcp_usage_total|network_udp_usage_total|tasks_state|cpu_load_average_10s)
    #   replacement: $1
    #   action: drop

    # 	relabel configs to apply to samples before ingestion.
    ##
    relabelings: []
    # - sourceLabels: [__meta_kubernetes_pod_node_name]
    #   separator: ;
    #   regex: ^(.*)$
    #   targetLabel: nodename
    #   replacement: $1
    #   action: replace

## Component scraping the kube controller manager
##
```

