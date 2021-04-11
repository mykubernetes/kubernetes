一、去掉污点
---
查看节点调度情况
```
[root@k8s001 ~]# kubectl get node 
NAME             STATUS   ROLES    AGE   VERSION
172.16.33.22   Ready    master   3d    v1.13.5
172.16.33.23   Ready    node     3d    v1.13.5
172.16.33.24   Ready    node     3d    v1.13.5
[root@k8s001 ~]# kubectl describe node 172.16.33.22
......
Events:
  Type    Reason              Age               From                     Message
  ----    ------              ----              ----                     -------
  Normal  NodeNotSchedulable  11s (x2 over 3d)  kubelet, 172.16.33.22  Node 172.16.33.22 status is now: NodeNotSchedulable
......
```
去除污点
```
[root@k8s001 ~]# kubectl uncordon 172.16.33.22
```

二、增加污点容忍
---
```
[root@k8s001 ~]# cat pod.yaml
......
spec:
   tolerations:
    - key: node-role.kubernetes.io/master
      operator: Exists
      effect: NoSchedule
   containers:
    - name: nginx-pod
......
```
