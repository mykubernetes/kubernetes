helm安装
========

helm官方网站  
https://helm.sh  


官方仓库  
https://hub.kubeapps.com/  
https://hub.helm.sh/charts/stable
https://developer.aliyun.com/hub#/?_k=6zd4g9&tdsourcetag=s_pctim_aiomsg  
https://github.com/cloudnativeapp/charts  


一、安装  
1、下载  
```
https://github.com/helm/helm 各种版本  
wget https://storage.googleapis.com/kubernetes-helm/helm-v2.9.1-linux-amd64.tar.gz  
mv helm /usr/bin  
```  

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


4、仓库管理  
```
添加阿里云仓库
# helm repo add chart-aliyun https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts

官方incubator仓库
# helm repo add incubator https://storage.googleapis.com/kubernetes-charts-incubator

每天自动向谷歌拉取最新的chart
# helm repo add stable https://cnych.github.io/kube-charts-mirror/
"stable" has been added to your repositories

删除仓库
# helm repo remove stable
"stable" has been removed from your repositories

更新仓库
# helm repo update

列出所有仓库
# helm repo list
NAME URL
stable https://cnych.github.io/kube-charts-mirror/
local http://127.0.0.1:8879/charts
```  


5、helm的使用   

helm下载目录
```
cd ~/.helm/repository/cache/archive
```

release管理
| 命令 | 说明 |
|------|-----|
| get | 下载一个release |
| delete | 根据给定的release name，从Kubernetes中删除指定的release |
| install | 安装一个chart |
| list | 显示release列表 |
| upgrade | 升级release |
| rollback | 回滚release到之前的一个版本 |
| status | 显示release状态信息 |
| history | Fetch release历史信息 |

chart管理
| 命令 | 说明 |
|------|-----|
| get | 下载一个release |
| delete | 根据给定的release name，从Kubernetes中删除指定的release |
| install | 安装一个chart |
| list | 显示release列表 |
| upgrade | 升级release |
| rollback | 回滚release到之前的一个版本 |
| status | 显示release状态信息 |
| history | Fetch release历史信息 |



helm常用命令
```
搜索  
# helm search mysql

查看详细信息
# helm inspect stable/mysql

查看mysql的所有选项
# helm inspect values stable/mysql

安装  
# helm install --name mysql stable/mysql


查看渲染后的yaml文件
# helm get manifest mysql

修改配置安装
# helm install stable/mysql --set service.type=NodePort

指定values.yaml文件安装  
# helm install --name redis1 -f values.yaml stable/redis

查看运行的服务
# helm list

获取release状态
# helm status mysql

通过修改value.yaml文件进行更新
# helm upgrade mysql -f value.yaml stable/mysql

查看更新的历史版本,每次更新版版会+1，回滚也会+1
# helm history mysql

回滚到指定版本
# helm rollback mysql 1

删除,保留configmap方式
# helm delete mysql

保留configmap的方式是可以查看被删除的信息
# helm ls --deleted
# helm ls --all

彻底删除服务
helm delete mysql --purge

生成模板文件
# helm template . --name istio --name istio-system > istio.yaml

将charts文件打包
# helm package mychart/
mychart-0.1.0.tgz
```  


