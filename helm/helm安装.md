客户端 helm  
服务器端tiller  

tiller下载  
链接：https://pan.baidu.com/s/1S19LfZY1lRT3nf7J9mR2tg 提取码：7naj   

一、安装  
1、下载  
https://github.com/helm/helm 各种版本  
wget https://storage.googleapis.com/kubernetes-helm/helm-v2.9.1-linux-amd64.tar.gz  
mv helm /usr/bin  

2、配置权限  
配置RBAC权限让helm 初始化首先联系apiserver  
https://github.com/helm/helm/blob/master/docs/rbac.md  

```
# cat tiller.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
应用文件
# kubectl apply -f tiller.yaml
```  

3、初始化 helm  
``` helm init --service-account tiller ```  


4、添加阿里云tiller仓库  
``` helm repo add chart-aliyun https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts ```  


5、helm官方网站  
https://helm.sh  

官方仓库  
https://hub.kubeapps.com/  
https://hub.helm.sh/  

6、使用  
搜索  
``` helm search memcache ```  
安装  
``` helm install --name mem1 stable/memcached ```  

helm常用命令  
```
	release管理
		install        #安装
		delete       #删除
		upgrade    #更新
		rollback     #回滚
		list              #查
		history       #release历史
		status        #获取release状态信息
	chart管理
		create
		fetch         #下载并展开
		get            #下载不展开
		inspect      #查了chart详细信息
		package    #本地打包
		verify         #校验
```  
helm下载目录  
``` cd ~/.helm/repository/cache/archive ```  

如果修改values.yaml需要指定新的文件并应用  
``` helm install --name redis1 -f values.yaml stable/redis ```  

官方介绍chart适用  
https://helm.sh/docs/developing_charts/#charts  
