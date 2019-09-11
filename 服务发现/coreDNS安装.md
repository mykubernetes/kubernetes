1、Coredns 项目下载  
```
# git clone https://github.com/coredns/deployment.git

# cd deployment/kubernetes

# ll
total 44
-rw-r--r-- 1 root root 3379 Sep  8 12:36 CoreDNS-k8s_version.md
-rw-r--r-- 1 root root 3771 Sep  8 12:36 coredns.yaml.sed
drwxr-xr-x 2 root root   22 Sep  8 12:36 corefile-tool
-rwxr-xr-x 1 root root 3791 Sep  8 12:36 deploy.sh
-rw-r--r-- 1 root root 4985 Sep  8 12:36 FAQs.md
drwxr-xr-x 2 root root   22 Sep  8 12:36 migration
-rw-r--r-- 1 root root 2706 Sep  8 12:36 README.md
-rwxr-xr-x 1 root root 1337 Sep  8 12:36 rollback.sh
-rw-r--r-- 1 root root 7159 Sep  8 12:36 Scaling_CoreDNS.md
-rw-r--r-- 1 root root 7911 Sep  8 12:36 Upgrading_CoreDNS.md
```  

2、重要文件介绍  
deploy.sh 是一个用于在已经运行kube-dns的集群中生成运行CoreDNS部署文件（manifest）的工具脚本。它使用 coredns.yaml.sed文件作为模板，创建一个ConfigMap和CoreDNS的deployment，然后更新集群中已有的kube-dns 服务的selector使用CoreDNS的deployment。重用已有的服务并不会在服务的请求中发生冲突  


3、deploy 脚本使用方法  
```
usage: ./deploy.sh [ -r REVERSE-CIDR ] [ -i DNS-IP ] [ -d CLUSTER-DOMAIN ] [ -t YAML-TEMPLATE ]
 
    -r : Define a reverse zone for the given CIDR. You may specifcy this option more
         than once to add multiple reverse zones. If no reverse CIDRs are defined,
         then the default is to handle all reverse zones (i.e. in-addr.arpa and ip6.arpa)
    -i : Specify the cluster DNS IP address. If not specificed, the IP address of
         the existing "kube-dns" service is used, if present.
    -s : Skips the translation of kube-dns configmap to the corresponding CoreDNS Corefile configuration.
```  

4、Coredns 与 kubernetes 版本匹配  
```
参考地址：
https://github.com/coredns/deployment/blob/master/kubernetes/CoreDNS-k8s_version.md
Kubernetes  v1.14   ==> CoreDNS  v1.3.1
Kubernetes  v1.13   ==> CoreDNS  v1.2.6       <<===本环境使用版本
```  

5、生成安装配置文件  
```
./deploy.sh -r 10.96.0.0/16 -i 10.96.0.10  -d cluster.local -t coredns.yaml.sed -s >coredns.yaml
```  


6、验证配置文件核心配置
```
# cat coredns.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        ready
        kubernetes cluster.local  10.96.0.0/16 {      #此处配置以更改
          pods insecure
          fallthrough in-addr.arpa ip6.arpa
        }
        prometheus :9153
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }

--------------------------------------------------
      containers:
      - name: coredns
        image: coredns/coredns:1.2.6                《===修改镜像版本：image: coredns/coredns:1.2.6
        imagePullPolicy: IfNotPresent
        resources:
          limits:
            memory: 170Mi
          requests:
            cpu: 100m
            memory: 70Mi
        args: [ "-conf", "/etc/coredns/Corefile" ]
        volumeMounts:
        - name: config-volume
          mountPath: /etc/coredns
          readOnly: true

```  

7、应用配置文件  
```
kubectl apply -f coredns.yaml 
serviceaccount/coredns created
clusterrole.rbac.authorization.k8s.io/system:coredns created
clusterrolebinding.rbac.authorization.k8s.io/system:coredns created
configmap/coredns created
deployment.apps/coredns created
service/kube-dns created
```  


8、直接安装方法  
```
首先要确定使用镜像是对的，执行方法如下：
./deploy.sh -r 10.96.0.0/16 -i 10.96.0.10  -t coredns.yaml  -d | kubectl apply -f -
```  






