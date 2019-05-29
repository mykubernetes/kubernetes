升级Kubernetes集群  
===
升级master节点  
---

1、列出kubeadm所有可用的版本  
``` # yum list --showduplicates kubeadm --disableexcludes=kubernetes ```  

2、升级kubeadm为最新版本  
``` # yum upgrade -y kubeadm-1.14.2-0 --disableexcludes=kubernetes ```  

3、查看kubeadm版本  
``` # kubeadm version ```  

4、查看kubeadm的升级计划  
``` # kubeadm upgrade plan ```  

5、通过kubeadm upgrade plan命令输出的可升级执行的命令升级  
``` # kubeadm upgrade apply v1.14.2 ```  


6、升级kubectl和kubelet两个包  
``` # yum upgrade -y kubelet-1.14.2-0 kubectl-1.14.2-0 --disableexcludes=kubernetes ```  

7、获取kubelet新版本的配置  
``` # kubeadm upgrade node config --kubelet-version v1.14.2 ```  

8、重启kubelet  
```
# systemctl daemon-reload
# systemctl restart kubelet
```  

9、升级第二台master  
``` # yum install -y kubeadm-1.14.2-0 kubelet-1.14.2-0 kubectl-1.14.2-0 --disableexcludes=kubernetes ```  

10、升级控制平面  
``` # kubeadm upgrade node experimental-control-plane ```  

11、更新kubelet的配置  
``` # kubeadm upgrade node config --kubelet-version v1.14.2 ```

12、重启kubelet  
```
# systemctl daemon-reload
# systemctl restart kubelet
```  

升级work节点
---
1、在master节点将升级node01节点的pod驱逐走  
``` # kubectl drain node01 --ignore-daemonsets --force ```  

2、查看node01节点是否为不可调动状态  
```
# kubectl get nodes
NAME      STATUS                                   POLES      AGE    VERSION
node01    Ready,SchedulingDisabled     <none>    26d      v1.14.1
```  

3、升级node01节点三个软件包  
``` # yum upgrade -y kubeadm-1.14.1-0 kubelet-1.14.1-0 kubectl-1.14.1-0--disableexcludes=kubernetes ```  

4、更新kubelet的配置  
``` # kubeadm upgrade node config --kubelet-version v1.14.2 ```  

5、重启kubelet  
```
# systemctl daemon-reload
# systemctl restart kubelet
```  

6、将node01节点设置成可调度节点  
``` # kubectl uncordon node01 ```  

7、查看work节点是否为可调动状态  
```
# kubectl get nodes
NAME      STATUS      POLES      AGE    VERSION
node01    Ready        <none>    26d      v1.14.2
```  
