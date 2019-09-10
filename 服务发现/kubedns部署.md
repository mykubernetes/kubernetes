官方部署文件  
https://github.com/kubernetes/kubernetes/tree/release-1.8/cluster/addons/dns  

下载对应文件  
```
wget https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.8/cluster/addons/dns/kubedns-cm.yaml
wget https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.8/cluster/addons/dns/kubedns-controller.yaml.base
wget https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.8/cluster/addons/dns/kubedns-sa.yaml
wget https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.8/cluster/addons/dns/kubedns-svc.yaml.base

查看下载的文件
ls *.yaml *.base
kubedns-cm.yaml  kubedns-sa.yaml  kubedns-controller.yaml.base  kubedns-svc.yaml.base

将base结尾的文件重命名
mv kubedns-controller.yaml.base kubedns-controller.yaml
mv kubedns-svc.yaml.base kubedns-svc.yaml
```  

修改kubedns-controller.yaml 配置文件  
```
# cat kubedns-controller.yaml 
# Copyright 2016 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Should keep target in cluster/addons/dns-horizontal-autoscaler/dns-horizontal-autoscaler.yaml
# in sync with this file.

# __MACHINE_GENERATED_WARNING__

apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: kube-dns
  namespace: kube-system
  labels:
    k8s-app: kube-dns
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
spec:
  # replicas: not specified here:
  # 1. In order to make Addon Manager do not reconcile this replicas parameter.
  # 2. Default is 1.
  # 3. Will be tuned in real time if DNS horizontal auto-scaling is turned on.
  strategy:
    rollingUpdate:
      maxSurge: 10%
      maxUnavailable: 0
  selector:
    matchLabels:
      k8s-app: kube-dns
  template:
    metadata:
      labels:
        k8s-app: kube-dns
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ''
    spec:
      tolerations:
      - key: "CriticalAddonsOnly"
        operator: "Exists"
      volumes:
      - name: kube-dns-config
        configMap:
          name: kube-dns
          optional: true
      containers:
      - name: kubedns
        image: k8s.gcr.io/k8s-dns-kube-dns-amd64:1.14.10
        resources:
          # TODO: Set memory limits when we've profiled the container for large
          # clusters, then set request = limit to keep this container in
          # guaranteed class. Currently, this container falls into the
          # "burstable" category so the kubelet doesn't backoff from restarting it.
          limits:
            memory: 170Mi
          requests:
            cpu: 100m
            memory: 70Mi
        livenessProbe:
          httpGet:
            path: /healthcheck/kubedns
            port: 10054
            scheme: HTTP
          initialDelaySeconds: 60
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8081
            scheme: HTTP
          # we poll on pod startup for the Kubernetes master service and
          # only setup the /readiness HTTP server once that's available.
          initialDelaySeconds: 3
          timeoutSeconds: 5
        args:
        - --domain=cluster.local.           # 修改后
        - --dns-port=10053
        - --config-dir=/kube-dns-config
        - --v=2
        env:
        - name: PROMETHEUS_PORT
          value: "10055"
        ports:
        - containerPort: 10053
          name: dns-local
          protocol: UDP
        - containerPort: 10053
          name: dns-tcp-local
          protocol: TCP
        - containerPort: 10055
          name: metrics
          protocol: TCP
        volumeMounts:
        - name: kube-dns-config
          mountPath: /kube-dns-config
      - name: dnsmasq
        image: k8s.gcr.io/k8s-dns-dnsmasq-nanny-amd64:1.14.10
        livenessProbe:
          httpGet:
            path: /healthcheck/dnsmasq
            port: 10054
            scheme: HTTP
          initialDelaySeconds: 60
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5
        args:
        - -v=2
        - -logtostderr
        - -configDir=/etc/k8s/dns/dnsmasq-nanny
        - -restartDnsmasq=true
        - --
        - -k
        - --cache-size=1000
        - --no-negcache
        - --log-facility=-
        - --server=/cluster.local/127.0.0.1#10053      # 修改后
        - --server=/in-addr.arpa/127.0.0.1#10053
        - --server=/ip6.arpa/127.0.0.1#10053
        ports:
        - containerPort: 53
          name: dns
          protocol: UDP
        - containerPort: 53
          name: dns-tcp
          protocol: TCP
        # see: https://github.com/kubernetes/kubernetes/issues/29055 for details
        resources:
          requests:
            cpu: 150m
            memory: 20Mi
        volumeMounts:
        - name: kube-dns-config
          mountPath: /etc/k8s/dns/dnsmasq-nanny
      - name: sidecar
        image: k8s.gcr.io/k8s-dns-sidecar-amd64:1.14.10
        livenessProbe:
          httpGet:
            path: /metrics
            port: 10054
            scheme: HTTP
          initialDelaySeconds: 60
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5
        args:
        - --v=2
        - --logtostderr
        - --probe=kubedns,127.0.0.1:10053,kubernetes.default.svc.__PILLAR__DNS__DOMAIN__,5,A
        - --probe=dnsmasq,127.0.0.1:53,kubernetes.default.svc.__PILLAR__DNS__DOMAIN__,5,A
        ports:
        - containerPort: 10054
          name: metrics
          protocol: TCP
        resources:
          requests:
            memory: 20Mi
            cpu: 10m
      dnsPolicy: Default  # Don't use cluster DNS.
      serviceAccountName: kube-dns
```  
kubedns-controller 运行了 三个容器：kubedns dnsmasq sidecar，sidecar 是一个监控健康模块，同时向外暴露metrics记录。

修改kubedns-svc.yaml配置文件
```
# cat kubedns-svc.yaml 
# Copyright 2016 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# __MACHINE_GENERATED_WARNING__

apiVersion: v1
kind: Service
metadata:
  name: kube-dns
  namespace: kube-system
  labels:
    k8s-app: kube-dns
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
    kubernetes.io/name: "KubeDNS"
spec:
  selector:
    k8s-app: kube-dns
  clusterIP: 10.96.0.10       #修改为我们设定的cluster的IP,其它默认。
  ports:
  - name: dns
    port: 53
    protocol: UDP
  - name: dns-tcp
    port: 53
```  


应用配置文件  
```
kubectl -f .
configmap/kube-dns created
deployment.extensions/kube-dns created
serviceaccount/kube-dns created
service/kube-dns created



# kubectl get pod -n kube-system
NAME                             READY   STATUS             RESTARTS   AGE
etcd-node01                      1/1     Running            3          170d
kube-apiserver-node01            1/1     Running            3          170d
kube-controller-manager-node01   1/1     Running            4          170d
kube-dns-5c974d6985-j5wmr        3/3     Running            0          4m42s
kube-dns-dbb9475bc-8nqbp         3/3     Running            0          19m
kube-flannel-ds-amd64-79qvl      1/1     Running            0          170d
kube-flannel-ds-amd64-8qrwj      1/1     Running            2          170d
kube-flannel-ds-amd64-qgmnv      1/1     Running            5          170d
kube-proxy-5xbfw                 1/1     Running            0          170d
kube-proxy-89vxp                 1/1     Running            0          170d
kube-proxy-xl5fl                 1/1     Running            2          170d
kube-scheduler-node01            1/1     Running            3          170d
tiller-deploy-dbb85cb99-5t9cl    1/1     Running            0          170d
```  


kubedns水平扩缩容
---
官方托管代码  
https://github.com/kubernetes/kubernetes/tree/release-1.8/cluster/addons/dns-horizontal-autoscaler

下载  
```
wget https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.8/cluster/addons/dns-horizontal-autoscaler/dns-horizontal-autoscaler-rbac.yaml
wget https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.8/cluster/addons/dns-horizontal-autoscaler/dns-horizontal-autoscaler.yaml
```  

应用配置  
```
# kubectl -f .
serviceaccount/kube-dns-autoscaler created
clusterrole.rbac.authorization.k8s.io/system:kube-dns-autoscaler created
clusterrolebinding.rbac.authorization.k8s.io/system:kube-dns-autoscaler created
deployment.extensions/kube-dns-autoscaler created


# kubectl get pod -n kube-system |grep kube-dns-autoscaler
kube-dns-autoscaler-6686fffcd4-c9g7d   1/1       Running             0          1m
```  
