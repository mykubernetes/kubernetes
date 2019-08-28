官网  
https://istio.io/zh/  

1、下载istio  
https://github.com/istio/istio/releases  
```
# wget https://github.com/istio/istio/releases/download/1.2.4/istio-1.2.4-linux.tar.gz
# tar xvf istio-1.2.4-linux.tar.gz
```  

2、部署istio_crd  
```
# 创建名称空间
# kubectl create namespace istio-system
# cd istio-1.2.4/install/kubernetes/helm/istio-init

生成yaml配置文件
# helm template . --name imooc-istio-init --namespace istio-system > istio-init.yaml

应用配置文件
# kubectl apply -f istio-init.yaml

查看部署状态
# kubectl get pod -n istio-system

查看部署后的crd
kubectl get crds | grep istio
```  

3、部署istio  
```
# cd istio-1.2.4/install/kubernetes/helm/istio
生成模板文件
# helm template . --name imooc-istio --name istio-system > istio.yaml

#应用配置文件
# kubectl apply -f istio.yaml
```  
