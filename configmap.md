configmap
=========
1、通过命令方式创建configmap  
```
# kubectl create configmap nginx-config --from-literal=nginx_port=80 --from-literal=server_name=www.node1.com
```  
-  -from-literal 参数传递配置信息，该参数可以使用多次

2、通过命令方式传递配置文件创建configmap  
```
#cat www.conf
server {
            server_name www.node2.com;
            listen 80;
            root /data/web/html/;
}

# kubectl create configmap nginx-www --from-file=./www.conf
```  
- -from-file 这个参数可以使用多次

3、通过配置文件方式创建configmap
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: kube-system 
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: EnsureExists
data:
  prometheus.yml: |
    scrape_configs:
    - job_name: prometheus
      static_configs:
      - targets:
        - localhost:9090
```  

4、通过目录方式创建  
```
#  ls /opt/configmap/dir/
game.properties
ui.properties

# cat /opt/configmap/dir/game.properties
enemies=aliens
lives=3
enemies.cheat=true
enemies.cheat.level=noGoodRotten
secret.code.passphrase=UUDDLRLRBABAS
secret.code.allowed=true
secret.code.lives=30

# cat /opt/configmap/dir/ui.properties
color.good=purple
color.bad=yellow
allow.textmode=true
how.nice.to.look=fairlyNice

# kubectl create configmap game-config --from-file=/opt/configmap/dir
```  
- -from-file 指定在目录下的所有文件都会被用在 ConfigMap 里面创建一个键值对，键的名字就是文件名，值就是文件的内容


configmap挂载到容器
=========

一、通过env的方式将环境变量传递给pod,通过env传递的环境变量只能在pod启动时读取  
```
# cat configmap-env.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: busybox-httpd-config
  namespace: default
data:
  httpd_port: "8080"
  verbose_level: "-vv"
---
apiVersion: v1
kind: Pod
metadata:
  name: configmap-env-demo
  namespace: default
spec:
  containers:
  - image: busybox
    name: busybox-httpd
    command: ["/bin/httpd"]
    args: ["-f","-p","$(HTTPD_PORT)","$(HTTPD_LOG_VERBOSE)"]
    env:
    - name: HTTPD_PORT
      valueFrom:
        configMapKeyRef:
          name: busybox-httpd-config
          key: httpd_port
    - name: HTTPD_LOG_VERBOSE
      valueFrom:
        configMapKeyRef:
          name: busybox-httpd-config
          key: verbose_level
          optional: true
```  

二、通过envfrom方式传递环境变量  
```
# cat configmap-envfrom-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-envfrom-demo
  namespace: default
spec:
  containers:
  - image: busybox
    name: busybox-httpd
    command: ["/bin/httpd"]
    args: ["-f","-p","$(HTCFG_httpd_port)","$(HTCFG_verbose_level)"]
    envFrom:
    - prefix: HTCFG_
      configMapRef:
        name: busybox-httpd-config
        optional: false
```  

三、通过数据卷的方式传递环境变量  
```
# cat configmap-volume-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-volume-demo
  namespace: default
spec:
  containers:
  - image: nginx:alpine
    name: web-server
    volumeMounts:
    - name: ngxconfig
      mountPath: /etc/nginx/conf.d/
      readOnly: true
  volumes:
  - name: ngxconfig
    configMap:
      name: nginx-config-files
      defaultMode: 0755
```  


四、根据卷挂载的方式挂载多个文件configmap  
```
# cat myserver-status.cfg
location /nginx-status {
    stub_status on;
    access_log off;
}


# cat myserver.conf
server {
    listen 8080;
    server_name www.ikubernetes.io;

    include /etc/nginx/conf.d/myserver-*.cfg;

    location / {
        root /usr/share/nginx/html;
    }
}


# cat configmap-volume-pod-3.yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-volume-demo-3
  namespace: default
spec:
  containers:
  - image: nginx:alpine
    name: web-server
    volumeMounts:
    - name: ngxconfig
      mountPath: /etc/nginx/conf.d/myserver.conf
      subPath: myserver.conf
      readOnly: true
    - name: ngxconfig
      mountPath: /etc/nginx/conf.d/myserver-status.cfg
      subPath: myserver-status.cfg
      readOnly: true
  volumes:
  - name: ngxconfig
    configMap:
      name: nginx-config-file
```  

五、如果变量值有多个可以使用items的方式挑选适用的几个变量传递  
```
# cat myserver-gzip.cfg
gzip on;
gzip_comp_level 5;
gzip_proxied     expired no-cache no-store private auth;
gzip_types text/plain text/html text/css application/xml text/javascript;



# cat configmap-volume-pod-2.yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-volume-demo-2
  namespace: default
spec:
  containers:
  - image: nginx:alpine
    name: web-server
    volumeMounts:
    - name: ngxconfig
      mountPath: /etc/nginx/conf.d/
      readOnly: true
  volumes:
  - name: ngxconfig
    configMap:
      name: nginx-config-files
      items:
      - key: myserver.conf
        path: myserver.conf
        mode: 0644
      - key: myserver-gzip.cfg
        path: myserver-compression.cfg
```  


六、通过downwardAPI获取主机变量的方式传递参数  
```
apiVersion: v1
kind: Pod
metadata:
  name: env-demo
  labels:
    purpose: demonstrate-environment-variables
spec:
  containers:
  - name: env-demo-container
    image: busybox
    command: ["httpd"]
    args: ["-f"]
    env:
    - name: HELLO_WORLD
      value: just a demo
    - name: MY_NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName
    - name: MY_NODE_IP
      valueFrom:
        fieldRef:
          fieldPath: status.hostIP
    - name: MY_POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
  restartPolicy: OnFailure
```  
- spec.nodeName: 节点名称
- status.hostIP: 节点IP地址
- metadata.name: POD名称
- metadata.namespace: POD所在的名称空间
- status.podIP: POD的IP地址
- spec.serviceAccountName: POD使用的ServiceAccount资源的名称
- metadata.uid: POD的UID
- metadata.labels['KEY']: POD对象标签指定键的值，例如 metadata.labels['mylabel']
- metadata.annotations['KEY']:  POD对象注解信息中的指定键的值

七、通过downwardAPI获取主机变量挂载方式的传递参数  
```
kind: Pod
apiVersion: v1
metadata:
  labels:
    zone: east-china
    cluster: downward-api-test-cluster1
    rack: rack-101
    app: dapi-vol-pod
  name: dapi-vol-pod
  annotations:
    annotation1: "test-value-1"
    annotation2: "test-value-2"
spec:
  containers:
    - name: volume-test-container
      image: busybox
      command: ["sh", "-c", "sleep 864000"]
      resources:
        requests:
          memory: "32Mi"
          cpu: "125m"
        limits:
          memory: "64Mi"
          cpu: "250m"
      volumeMounts:
      - name: podinfo
        mountPath: /etc/podinfo
        readOnly: false
  volumes:
  - name: podinfo
    downwardAPI:
      defaultMode: 420
      items:
      - fieldRef:
          fieldPath: metadata.name
        path: pod_name
      - fieldRef:
          fieldPath: metadata.namespace
        path: pod_namespace
      - fieldRef:
          fieldPath: metadata.labels
        path: pod_labels
      - fieldRef:
          fieldPath: metadata.annotations
        path: pod_annotations
      - resourceFieldRef:
          containerName: volume-test-container
          resource: limits.cpu
        path: "cpu_limit"
      - resourceFieldRef:
          containerName: volume-test-container
          resource: requests.memory
          divisor: "1Mi"
        path: "mem_request"
```

八、通过command和args的方式添加启动参数  
```
# cat command-demo.yaml
apiVersion: v1
kind: Pod
metadata:
  name: command-demo
  labels:
    purpose: demonstrate-command
spec:
  containers:
  - name: command-demo-container
    image: busybox
    command: ["httpd"]
    args: ["-f"]
  restartPolicy: OnFailure
```  
