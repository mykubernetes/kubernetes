官网https://kubernetes.io/zh/docs/concepts/  
https://www.kubernetes.org.cn/k8s  
https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.15/#-strong-api-overview-strong-  
实用中文文档http://docs.kubernetes.org.cn/  
https://v1-14.docs.kubernetes.io/zh/docs/concepts/services-networking/ingress/  
阿里云使用kubernetes  
https://help.aliyun.com/document_detail/86420.html?spm=a2c4g.11186623.6.586.5c791be1iCa4aC  

https://blog.csdn.net/qq_32641153 或 http://www.mydlq.club/about/menu/
===

pod的几种常见状态
- Pendding 未匹配到满足pod运行的节点，未调度
- containerCreating 调查成功，后创建容器状态，此状态持续时间不长
- Running 容器创建成功后处于运行中的状态
- Succeeded 成功运行，只有job和cronjob可出现此状态，容器运行结束正常退出，退出值为0
- Failed 失败运行，只有job和cronjob可出现此状态，容器运行结束退出，退出值为非0
- Ready 健康检查成功后的状态
- CrashLoopBackOff 未通过健康检查的状态
- Unkown 为api_server没有收到相关pod的汇报（kubelet和api的通信问题）
- Terminating 为pod终止时的状态

解决pod一直未被终止问题  
kubectl delete pod [pod name] --force --grace-period=0 -n [namespace]  

pod生命周期  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod_lifecycle.png)  

pod创建过程  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod.png)  

pod终止过程  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/pod_kill.png)  


