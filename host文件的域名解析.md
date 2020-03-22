1、配置镜像中的 Hosts 文件
```
$ vim centos-deployment.yaml
kind: Deployment
apiVersion: apps/v1
metadata:
  name: centos7
  labels:
    app: centos7
spec:
  replicas: 1
  selector:
    matchLabels:
      app: centos7
  template:
    metadata:
      labels:
        app: centos7
    spec:
      #-------------------------------------------
      hostAliases:                   #配置hosts文件
      - ip: "192.168.2.1"            #配置解析的IP
        hostnames:
        - "www.baidu.com"            #配置域名
      #-------------------------------------------    
      containers:
      - name: service-provider
        image: centos:7.7.1908
        command:
        - "/bin/sh"
        args:
        - "-c"
        - "while true; do sleep 999999; done"
```

2、部署
```
$ kubectl apply -f centos-deployment.yaml
```

3、查找部署的 CentOS 的 Pod
```
$ kubectl get pod | grep centos7
centos7-585dd57b95-qsx2c   1/1     Running   0          5m30s
```

4、进入 Pod 内部
```
$ kubectl exec -it centos7-585dd57b95-qsx2c -n mydlqcloud /bin/bash
```

5、查看镜像中的 Hosts 文件
```
$ cat /etc/hosts
# Kubernetes-managed hosts file.
127.0.0.1       localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
fe00::0 ip6-mcastprefix
fe00::1 ip6-allnodes
fe00::2 ip6-allrouters
10.244.39.240   centos7-585dd57b95-qsx2c
# Entries added by HostAliases.
192.168.2.1     www.baidu.com
```

6、测试
```
$ ping www.baidu.com
PING www.baidu.com (192.168.2.1) 56(84) bytes of data.
64 bytes from www.baidu.com (192.168.2.1): icmp_seq=1 ttl=127 time=0.248 ms
64 bytes from www.baidu.com (192.168.2.1): icmp_seq=2 ttl=127 time=0.274 ms
64 bytes from www.baidu.com (192.168.2.1): icmp_seq=3 ttl=127 time=0.294 m
```
















