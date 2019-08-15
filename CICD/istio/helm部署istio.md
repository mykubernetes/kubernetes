1、下载istio  
https://github.com/istio/istio/releases  
```
# wget https://github.com/istio/istio/releases/download/1.2.4/istio-1.2.4-linux.tar.gz
# tar xvf istio-1.2.4-linux.tar.gz
```  

2、部署istio  
```
# 创建名称空间
# kubectl create namespace istio-system
# cd istio-1.2.4/install/kubernetes/helm/istio-init

# 修改下载镜像地址
# vim values.yaml
global:
  # Default hub for Istio images.
  # Releases are published to docker hub under 'istio' project.
  # Daily builds from prow are on gcr.io, and nightly builds from circle on docker.io/istionightly
  hub: registry.cn-hangzhou.aliyuncs.com/imooc-istio

  # Default tag for Istio images.
  tag: 1.2.4

  # imagePullPolicy is applied to istio control plane components.
  # local tests require IfNotPresent, to avoid uploading to dockerhub.
  # TODO: Switch to Always as default, and override in the local tests.
  imagePullPolicy: IfNotPresent

certmanager:
  enabled: false
  
生成yaml配置文件
# helm template . --name imooc-istio-init --namespace istio-system > istio-init.yaml

应用配置文件
# kubectl apply -f istio-init.yaml

查看部署状态
# kubectl get pod -n istio-system
```  

