安装  
```
kubectl apply -f .
查看elasticsearch
kubectl get svc -n kube-system
kubectl get statefulset -n kube-system
查看log-pilot
kubectl get ds -n kube-system
查看kibana
kubectl get deploy -n kube-system

修改hosts解析，对应ingress,http访问
```  

查看log-pilot日志  
```
docker ps |grep log-pilot
docker logs -f 131b426829ac
```  
