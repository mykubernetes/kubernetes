查看公钥证书
```
#自建CA，生成ca.key与ca.crt
openssl x509 -in ca.crt -noout -text

#apiserver的私钥与公钥证书
openssl x509 -in apiserver.crt -noout -text
```



Weave Scope安装
---
- Kubernetes 监控工具 Weave Scope  
参考官方文档:https://www.weave.works/docs/scope/latest/installing/#k8s


1.安装Weave Scopea
```
kubectl apply --namespace weave -f "https://cloud.weave.works/k8s/scope.yaml?k8s-version=$(kubectl version | base64 | tr -d '\n')"
namespace/weave created
serviceaccount/weave-scope created
clusterrole.rbac.authorization.k8s.io/weave-scope created
clusterrolebinding.rbac.authorization.k8s.io/weave-scope created
deployment.apps/weave-scope-app created
service/weave-scope-app created
deployment.apps/weave-scope-cluster-agent created
daemonset.apps/weave-scope-agent created
```

2.资源查看
```
# kubectl get all -n weave 
NAME                                            READY   STATUS    RESTARTS   AGE
pod/weave-scope-agent-hx4t2                     1/1     Running   0          103s
pod/weave-scope-agent-vmbqr                     1/1     Running   0          103s
pod/weave-scope-agent-zd8x7                     1/1     Running   0          103s
pod/weave-scope-app-b99fb9585-77rld             1/1     Running   0          104s
pod/weave-scope-cluster-agent-58f5b5454-vnckm   1/1     Running   0          103s

NAME                      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/weave-scope-app   ClusterIP   10.99.31.182   <none>        80/TCP    105s

NAME                               DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
daemonset.apps/weave-scope-agent   3         3         3       3            0           <none>          104s

NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/weave-scope-app             1/1     1            1           105s
deployment.apps/weave-scope-cluster-agent   1/1     1            1           105s

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/weave-scope-app-b99fb9585             1         1         1       105s
replicaset.apps/weave-scope-cluster-agent-58f5b5454   1         1         1       105s
```


3.对外访问
```
kubectl patch svc $(kubectl get svc -n weave |grep weave-scope-app |awk '{print $1}') -p '{"spec":{"type": "NodePort"}}' -n weave
```

4.登录url：http://172.27.9.131:30022/
