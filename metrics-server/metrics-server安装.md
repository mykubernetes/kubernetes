metrics-server安装
====================
1、官方代码托管  
https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/metrics-server  

2、下载托管代码下的所有yaml文件  
```
# for file in auth-delegator.yaml auth-reader.yaml metrics-apiservice.yaml metrics-server-deployment.yaml metrics-server-service.yaml resource-reader.yaml;do wget https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.11/cluster/addons/metrics-server/$file; done
```  

3、修改配置文件  
```
# vim metrics-server-deployment.yaml
- --source=kubernetes.summary_api:''                 #注释本行
- --source=kubernetes.summary_api:https://kubernetes.default?kubeletHttps=true&kubeletPort=10250&insecure=true    #添加本行

# vim resource-reader.yaml
resources:
  - pods
  - nodes
  - namespaces
  - nodes/stats     #新加
```  

4、应用  
``` # kubectl apply -f . ```  

5、查看pod是否正常运行  
```
# kubectl get pods -n kube-system
NAME                                    READY     STATUS    RESTARTS   AGE
coredns-78fcdf6894-cj6tn                1/1       Running   42         26d
coredns-78fcdf6894-wfvk8                1/1       Running   42         26d
elasticsearch-logging-0                 1/1       Running   45         4d
elasticsearch-logging-1                 1/1       Running   47         4d
etcd-master                             1/1       Running   42         26d
grafana-7f8bcdfbbf-qzln5                1/1       Running   4          13d
kibana-logging-7444956bf8-x8qqd         1/1       Running   2          4d
kube-apiserver-master                   1/1       Running   47         26d
kube-controller-manager-master          1/1       Running   43         26d
kube-flannel-ds-m4f4j                   1/1       Running   33         26d
kube-flannel-ds-xvssj                   1/1       Running   18         26d
kube-proxy-5lw6z                        1/1       Running   39         26d
kube-proxy-qlhg7                        1/1       Running   18         26d
kube-scheduler-master                   1/1       Running   39         26d
kubernetes-dashboard-767dc7d4d-4bt48    1/1       Running   5          5d
metrics-server-v0.2.1-84678c956-hbz2b   2/2       Running   0          2m
```  

6、查看是否安装成功  
```
# kubectl api-versions
metrics.k8s.io/v1beta1     #metrics控制器，有说明成功 
```  

7、master新开一个反向代理端口  
```
# kubectl proxy --port=8080
Starting to serve on 127.0.0.1:8080

# curl http://localhost:8080/apis/metrics.k8s.io/v1beta1/nodes
{
  "kind": "NodeMetricsList",
  "apiVersion": "metrics.k8s.io/v1beta1",
  "metadata": {
    "selfLink": "/apis/metrics.k8s.io/v1beta1/nodes"
  },
  "items": [
    {
      "metadata": {
        "name": "master",
        "selfLink": "/apis/metrics.k8s.io/v1beta1/nodes/master",
        "creationTimestamp": "2018-09-25T09:48:21Z"
      },
      "timestamp": "2018-09-25T09:48:00Z",
      "window": "1m0s",
      "usage": {
        "cpu": "211m",
        "memory": "2905388Ki"
      }
    },
    {
      "metadata": {
        "name": "node01",
        "selfLink": "/apis/metrics.k8s.io/v1beta1/nodes/node01",
        "creationTimestamp": "2018-09-25T09:48:21Z"
      },
      "timestamp": "2018-09-25T09:48:00Z",
      "window": "1m0s",
      "usage": {
        "cpu": "150m",
        "memory": "3670276Ki"
      }
    }
  ]
}
```  

8、验证命令是否可用  
```
# kubectl top nodes    
error: metrics not available yet       #说明还未成功，需要等待一会

查看主机资源
# kubectl top node
NAME      CPU(cores)   CPU%      MEMORY(bytes)   MEMORY%   
master    207m         10%       2832Mi          76%       
node01    144m         4%        3619Mi          37% 

查看pod资源
# kubectl top pods -n kube-system
NAME                                    CPU(cores)   MEMORY(bytes)   
coredns-78fcdf6894-cj6tn                2m           11Mi            
coredns-78fcdf6894-wfvk8                1m           11Mi            
elasticsearch-logging-0                 6m           1347Mi          
elasticsearch-logging-1                 6m           1326Mi          
etcd-master                             17m          84Mi            
```  
