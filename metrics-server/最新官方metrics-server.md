1、克隆仓库到本地  
```
git clone https://github.com/kubernetes-incubator/metrics-server.git --depth=1
```  

2、修改yaml文件  
替换image镜像，增加args部分  
```
# vim metrics-server/deploy/1.8+/metrics-server-deployment.yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: metrics-server
  namespace: kube-system
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: metrics-server
  namespace: kube-system
  labels:
    k8s-app: metrics-server
spec:
  selector:
    matchLabels:
      k8s-app: metrics-server
  template:
    metadata:
      name: metrics-server
      labels:
        k8s-app: metrics-server
    spec:
      serviceAccountName: metrics-server
      volumes:
      # mount in tmp so we can safely use from-scratch images and/or read-only containers
      - name: tmp-dir
        emptyDir: {}
      containers:
      - name: metrics-server
        image: mirrorgooglecontainers/metrics-server-amd64:v0.3.3
        imagePullPolicy: Always
        volumeMounts:
        - name: tmp-dir
          mountPath: /tmp
        args:
        - --kubelet-insecure-tls
        - --kubelet-preferred-address-types=InternalIP
```  

3、部署yaml文件  
```
# kubectl create -f deploy/1.8+/

# kubectl -n kube-system get pods | grep metrics
metrics-server-7ccb6455b9-nzhck      1/1     Running   0          36s
```  

4、验证  
```
#查看node资源
# kubectl top nodes
NAME         CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%   
k8s-master   258m         12%    880Mi           23%       
k8s-node1    96m          4%     562Mi           14%       
k8s-node2    139m         6%     601Mi           15%

#查看pod资源
# kubectl -n kube-system top pods
NAME                                 CPU(cores)   MEMORY(bytes)   
coredns-bccdc95cf-5wqq6              4m           12Mi            
coredns-bccdc95cf-p8xzq              3m           11Mi            
etcd-k8s-master                      21m          52Mi            
kube-apiserver-k8s-master            32m          268Mi           
kube-controller-manager-k8s-master   15m          42Mi            
kube-flannel-ds-amd64-pgwgb          3m           14Mi            
kube-flannel-ds-amd64-v5j5q          3m           13Mi            
kube-flannel-ds-amd64-zjpq8          2m           11Mi            
kube-proxy-nf688                     1m           15Mi            
kube-proxy-tfb6q                     1m           15Mi            
kube-proxy-wsx7d                     4m           15Mi            
kube-scheduler-k8s-master            2m           12Mi            
metrics-server-7ccb6455b9-nzhck      1m           12Mi   
```  

5、查看Metrics API数据  
#启动代理，直接查看接口数据，可获取的资源：nodes和pods  
```
$ kubectl proxy --port=8080

$ curl localhost:8080/apis/metrics.k8s.io/v1beta1
{
  "kind": "APIResourceList",
  "apiVersion": "v1",
  "groupVersion": "metrics.k8s.io/v1beta1",
  "resources": [
    {
      "name": "nodes",
      "singularName": "",
      "namespaced": false,
      "kind": "NodeMetrics",
      "verbs": [
        "get",
        "list"
      ]
    },
    {
      "name": "pods",
      "singularName": "",
      "namespaced": true,
      "kind": "PodMetrics",
      "verbs": [
        "get",
        "list"
      ]
    }
  ]
}
```  
