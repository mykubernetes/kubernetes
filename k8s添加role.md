给k8s添加角色
```
1、查看角色
# kubectl get nodes
NAME         STATUS     ROLES    AGE     VERSION
k8s-node01   NotReady   <none>   2m9s    v1.13.1
k8s-node02   NotReady   <none>   2m16s   v1.13.1

2、添加角色
kubectl label node k8s-node01 node-role.kubernetes.io/master=
kubectl label node k8s-node01 node-role.kubernetes.io/node=

3、查看角色
# kubectl get nodes
NAME         STATUS     ROLES                    AGE     VERSION
k8s-node01   NotReady   k8s-node01,k8s-node01    2m9s    v1.13.1
k8s-node02   NotReady   <none>                   2m16s   v1.13.1
```
