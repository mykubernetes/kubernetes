配置变量  
label_values(kube_pod_info{pod=~".*zookeeper.*"}, pod)
![image](https://github.com/mykubernetes/linux-install/blob/master/image/grafana6.png)

编写变量规则  
jvm_memory_bytes_used{pod="$pod"}
![image](https://github.com/mykubernetes/linux-install/blob/master/image/grafana7.png)

查看
![image](https://github.com/mykubernetes/linux-install/blob/master/image/grafana8.png)
