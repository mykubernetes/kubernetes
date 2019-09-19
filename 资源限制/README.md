1、pod资源限制  
```
spec:
  containers:
  - image: xxxx
    imagePullPolicy: Always
    name: auth
    ports:
    - containerPort: 8080
      protocol: TCP
    resources:
      limits:
        cpu: "4"
        memory: 2Gi
      requests:
        cpu: 250m
        memory: 250Mi
```  

2、计算资源配额 
```
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: spark-cluster
spec:
  hard:
    pods: "20"
    requests.cpu: "20"
    requests.memory: 100Gi
    limits.cpu: "40"
    limits.memory: 200Gi
```  

3、配置对象数量配额限制
```
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
  namespace: spark-cluster
spec:
  hard:
    configmaps: "10"
    persistentvolumeclaims: "4"
    replicationcontrollers: "20"
    secrets: "10"
    services: "10"
    services.loadbalancers: "2"
```  

4、配置 CPU 和 内存 LimitRange  
```
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit-range
spec:
  limits:
  - default:
      memory: 50Gi
      cpu: 5
    defaultRequest:
      memory: 1Gi
      cpu: 1
    type: Container
```  
- default 即 limit 的值
- defaultRequest 即 request 的值

```

我的手机 2019/9/19 10:59:57
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota-example
spec:
  hard:
    pods: "5"                                    #POD 资源限制的总量限额
    requests.cpu: "1"                            #CPU 资源需求的总量限额
    requests.memory: 1Gi                         #内存资源需求的总量限额
    limits.cpu: "2"                              #CPU 资源限制的总量限
    limits.memory: 2Gi                           #内存资源限制的总量限额
    count/deployments.apps: "2"
    count/deployments.extensions: "2"
    persistentvolumeclaims: "2"                  #可以创建的 PVC 总数
    requests.storage: "5"                        #所有 PVC 存储需求的总量限额
    <storage-class-name>.storageclass.storage.k8s.io/requests.storage: "10"          #指定存储类上可使用的所有PVC存储需求的总量限额
    <storage-class-name>.storageclass.storage.k8s.io/persistentvolumeclaims: "10"    #指定存储类上可使用的PVC总数
    requests.ephemeral-storage: "20"             #所有Pod可用的本地临时存储需求的总量
    limits.ephemeral-storage: "20"               #所有Pod可用的本地临时存储限制的总量
```  

```
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-limit-range
spec:
  limits:
  - default:                          #用于定义默认的资源限制 
      cpu: 1000m
    defaultRequest:                   #定义默认的资源需求
      cpu: 1000m
    min:                              #定义最小的资源用量
      cpu: 500m
    max:                              #定义最大的资源用量
      cpu: 2000m
    maxLimitRequestRatio:             #最小用量的指定倍数
      cpu: 4
    type: Container                   #类型是容器

```  
