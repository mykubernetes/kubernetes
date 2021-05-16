Taints污点和Tolerations容忍概述
===
节点和Pod亲和力，是将Pod吸引到一组节点【根据拓扑域】（作为优选或硬性要求）。污点（Taints）则相反，它们允许一个节点排斥一组Pod。
- 容忍（Tolerations）应用于pod，允许（但不强制要求）pod调度到具有匹配污点的节点上。
- 污点（Taints）和容忍（Tolerations）共同作用，确保pods不会被调度到不适当的节点。一个或多个污点应用于节点；这标志着该节点不应该接受任何不容忍污点的Pod。

说明：我们在平常使用中发现pod不会调度到k8s的master节点，就是因为master节点存在污点。


Node的污点  
===
- NoSchedule:不能容忍此污点的新Pod对象不可调度至当前节点,属于强制型约束关系,节点上现存的 Pod 对象不受影响。

- PreferNoSchedule:NoSchedule的柔性约束版本,即不能容忍此污点的新 Pod 对象尽量不要调度至当前节点,不过无其他节点可供调度时也允许接受相应的Pod对象.节点上现存的Pod对象不受影响。

- NoExecute:不能容忍此污点的新Pod对象不可调度至当前节点,属于强制型约束关系,而且节点上现存的Pod对象因节点污点变动或Pod容忍度变动而不再满足匹配规则时,Pod对象将被驱逐。 

- 一个节点可以使用配置使用多个污点，一个pod对象也可以有多个容忍度

kubernetes内建使用的污点  
```
node.kubernetes.io/not-ready:    节点进入"NotReady"状态时被自动添加的污点
node.alpha.kubernetes.io/unreachable:   节点进入"NotReachable"状态时被自动添加的污点。 
node.kubernetes.io/out-of-disk:     节点进入"OutOfDisk"状态时被自动添加的污点
node.kubernetes.io/memory-pressure:    节点内存资源面临压力
node.kubernetes.io/ disk-pressure:   节点磁盘资源面临压力
node.kubernetes.io/network-unavailable:    节点网络不可用
node.kubernetes.io/unschedulable： 节点不可调度
node.cloudprovider.kubernetes.io/uninitialized:   kubelet由外部的云环境程序启动时,它将自动为节点添加此污点,待到云控制器管理器中的控制器初始化此节点时再将 其删除。 
```  

1、查看污点
```
$ kubectl get node
NAME            STATUS   ROLES    AGE    VERSION
k8s-master      Ready    master   102d   v1.16.6
k8s-node-2-12   Ready    <none>   102d   v1.16.6
k8s-node-2-13   Ready    <none>   102d   v1.16.6


$ kubectl describe nodes k8s-master
...
CreationTimestamp:  Sat, 23 Nov 2019 00:52:45 +0800
Taints:             node-role.kubernetes.io/master:PreferNoSchedule
Unschedulable:      false
...
```

2、为node设置taint
```
语法  
# kubectl taint nodes <node name> <key>=<value> : <effect>    #key和value可以根据自己需求任意定义  

## 设置污点并不允许 Pod 调度到该节点
# kubectl taint nodes node1 node-type=production:NoSchedule

## 设置污点尽量阻止污点调度到该节点
# kubectl taint nodes node2 node-role=admin:PreferNoSchedule

## 设置污点，不允许普通 Pod 调度到该节点，且将该节点上已经存在的 Pod 进行驱逐
# kubectl taint nodes node3 node-storage=ssd:NoExecute
```  

3、删除上面的taint  
```
语法：  
# kubectl taint nodes <node-name> <key>{:<effect>}-  

删除污点，可以不指定 value，指定 [effect] 值就可删除该 key:[effect] 的污点
# kubectl taint nodes node1 node-type:NoSchedule-
# kubectl taint nodes node2 node-role:PreferNoSchedule-
# kubectl taint nodes node3 node-storage:NoExecute-
```  

4、删除指定键名的所有污点  
```
## 也可以根据 key 直接将该 key 的所有 [effect] 都删除：
# kubectl taint nodes node1 node-type-
```  

5、删除节点上全部污点信息  
``` # kubectl patch nodes node1 -p '{"spec":{"taints":[]}}' ```  


Pod对象的容忍度  
===

1、概念
- 一个 Node 可以有多个污点。
- 一个 Pod 可以有多个容忍。
- Kuberentes 执行多个污点和容忍方法类似于过滤器。

2、注意
- 如果 Node 上带有污点 effect 为 NoSchedule，而 Node 上不带相应容忍，Kubernetes 就不会调度 Pod 到这台 Node 上。
- 如果 Node 上带有污点 effect 为 PreferNoShedule，这时候 Kubernetes 会努力不要调度这个 Pod 到这个 Node 上。
- 如果 Node 上带有污点 effect 为 NoExecute，这个已经在 Node 上运行的 Pod 会从 Node 上驱逐掉。没有运行在 Node 的 Pod 不能被调度到这个 Node 上。

```
## 容忍的 key、value 和对应 effect 也必须和污点 taints 保持一致
tolerations:                                        #spec字段下的容忍度配置              
- key: "node-type"                                  #可以容忍的自定义的key          
  operator: "Equal"                                 #污点信息完全匹配的等值
  value: "production"                               #可以容忍的自定义的value
  effect: "NoSchedule"                              #容忍的污点类型
  
## 容忍 tolerations 的 key 和要污点 taints 的 key 一致，且设置的 effect 也相同，不需要设置 value
tolerations:
- key: "node-role"
  operator: "Exists"                                ##Exists表示key存在就能容忍，value的值设置也不会不生效
  value: "admin"
  effect: "PreferNoSchedule"

##设置容忍时间
tolerations:
- key: "node.alpha.kubernetes.io/unreachable"
  operator: "Exists"                                #Exists表示key存在就能容忍，无需设置value
  effect: "NoExecute"
  tolerationSeconds: 6000                           #定义延迟驱逐当前Pod对象的时长，只能在NoExecute字段设置
```  
- 设置容忍但是没有指定 tolerationSeconds 参数的，那么该容忍永久生效。
- 设置容忍但是有指定 tolerationSeconds 参数的，那么在指定的时间内容忍有效，超过指定时间后将被剔除

3、Deployment 中设置容忍
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-demo-taint
  namespace: dev
spec:
  selector:
    matchLabels:
      app: web-demo-taint
  replicas: 1
  template:
    metadata:
      labels:
        app: web-demo-taint
    spec:
      containers:
      - name: web-demo-taint
        image: hub.mooc.com/kubernetes/web:v1
        ports:
        - containerPort: 8080
      tolerations:
      - key: "key"
        operator: "Equal"
        value: "value"
        effect: "NoSchedule"
```

4、容忍任何污点
例如一个空的key，将匹配所有的key、value、effect。即容忍任何污点。
```
tolerations:
- operator: "Exists"
```  

5、容忍某 key 值的污点
例如一个空的 effect，并且 key 不为空，那么将匹配所有与 key 相同的 effect：
```
tolerations:
- key: "key"
  operator: "Exists"
```  

6、示例
1) Node 上有一个污点

Node 和 Pod 的 key 为 key1、value1 与 effect 相同则能调度：
```
#污点
key1=value1:NoSchedule

#Pod设置
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
```

2) Node 上有多个污点

Node 的污点的 key、value、effect 和 Pod 容忍都相同则能调度：
```
# 设置污点
key1=value1:NoSchedule
key2=value2:NoExecute

# Pod设置容忍
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
- key: "key2"
  operator: "Equal"
  value: "value2"
  effect: "NoExecute"
```

3) Node 的污点和 Pod 的大部分都相同，不同的是 Node 污点 effect 为 PreferNoSchedule 的，可能会调度：
```
# 污点
key1=value1:NoSchedule
key2=value2:NoExecute
key3=value3:PreferNoSchedule

# Pod设置容忍
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
- key: "key2"
  operator: "Equal"
  value: "value2"
  effect: "NoExecute"
```

4) Node 的污点和 Pod 的大部分都相同，不同的是 Node 污点 effect 为 NoSchedule 和 NoExecute 的，不会被调度：
```
# 污点
key1=value1:NoSchedule
key2=value2:NoExecute
key3=value3:PreferNoSchedule

# Pod设置容忍
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
- key: "key3"
  operator: "Equal"
  value: "value3"
  effect: "PreferNoSchedule"
```

5、设置节点失效后 Pod 转移前等待时间
 当Pod运行所在的Node变成 unready 或者 unreachable 不可用状态时，Kubernetes 可以等待该 Pod 被调度到其他节点的最长等待时间。

```
tolerations:
- effect: NoExecutekey: node.alpha.kubernetes.io/notReady
  operator: Exists
  tolerationSeconds: 300
- effect: NoExecutekey: node.alpha.kubernetes.io/unreachable 
  key: operator: Exists 
  tolerationSeconds: 300 
```

