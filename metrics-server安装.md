metrics-server安装
====================
1、官方代码托管  
https://github.com/kubernetes/kubernetes/tree/master/cluster/addons/metrics-server   

2、下载托管代码下的所有yaml文件
``` # for file in auth-delegator.yaml auth-reader.yaml metrics-apiservice.yaml metrics-server-deployment.yaml  metrics-server-service.yaml  resource-reader.yaml ;do wget https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/metrics-server/$file ; done ```  

3、应用
``` # kubectl apply -f . ```  
