官网  
https://istio.io/zh/  
官方helm安装文档  
https://istio.io/zh/docs/setup/kubernetes/install/helm/  

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
# helm template . --name istio-init --namespace istio-system > istio-init.yaml

应用配置文件
# kubectl apply -f istio-init.yaml

查看部署状态等待部署完成
# kubectl get pod -n istio-system
NAME                      READY   STATUS              RESTARTS   AGE
istio-init-crd-10-ljgsq   0/1     ContainerCreating   0          2s
istio-init-crd-11-plqtm   0/1     ContainerCreating   0          2s
istio-init-crd-12-ktn5s   0/1     ContainerCreating   0          2s

创建完成
# kubectl get pod -n istio-system -w
NAME                      READY   STATUS      RESTARTS   AGE
istio-init-crd-10-ljgsq   0/1     Completed   0          8m35s
istio-init-crd-11-plqtm   0/1     Completed   0          8m35s
istio-init-crd-12-ktn5s   0/1     Completed   0          8m35s

查看部署后的crd
# kubectl get crds | grep istio
adapters.config.istio.io                2019-08-28T09:14:52Z
attributemanifests.config.istio.io      2019-08-28T09:14:51Z
authorizationpolicies.rbac.istio.io     2019-08-28T09:14:05Z
clusterrbacconfigs.rbac.istio.io        2019-08-28T09:14:50Z
destinationrules.networking.istio.io    2019-08-28T09:14:50Z
envoyfilters.networking.istio.io        2019-08-28T09:14:50Z
gateways.networking.istio.io            2019-08-28T09:14:50Z
handlers.config.istio.io                2019-08-28T09:14:52Z
httpapispecbindings.config.istio.io     2019-08-28T09:14:50Z
httpapispecs.config.istio.io            2019-08-28T09:14:51Z
instances.config.istio.io               2019-08-28T09:14:52Z
meshpolicies.authentication.istio.io    2019-08-28T09:14:50Z
policies.authentication.istio.io        2019-08-28T09:14:50Z
quotaspecbindings.config.istio.io       2019-08-28T09:14:51Z
quotaspecs.config.istio.io              2019-08-28T09:14:51Z
rbacconfigs.rbac.istio.io               2019-08-28T09:14:51Z
rules.config.istio.io                   2019-08-28T09:14:51Z
serviceentries.networking.istio.io      2019-08-28T09:14:50Z
servicerolebindings.rbac.istio.io       2019-08-28T09:14:51Z
serviceroles.rbac.istio.io              2019-08-28T09:14:51Z
sidecars.networking.istio.io            2019-08-28T09:14:47Z
templates.config.istio.io               2019-08-28T09:14:52Z
virtualservices.networking.istio.io     2019-08-28T09:14:50Z
```  

3、部署istio  
```
# cd istio-1.2.4/install/kubernetes/helm/istio
生成模板文件
# helm template . --name imooc-istio --name istio-system > istio.yaml
#应用配置文件
# kubectl apply -f istio.yaml

或者安装官方文档直接部署
# helm install . --name istio --namespace istio-system

查看部署的容器
# kubectl get pod -n istio-system
NAME                                      READY   STATUS                 RESTARTS   AGE
istio-citadel-76f9586b8b-mrrzv            1/1     Running                1          29m
istio-galley-78f65c8469-jg89t             1/1     Running                1          29m
istio-ingressgateway-677756fc66-fcplj     1/1     Running                1          29m
istio-init-crd-10-ljgsq                   0/1     Completed              0          59m
istio-init-crd-11-plqtm                   0/1     Completed              0          59m
istio-init-crd-12-ktn5s                   0/1     Completed              0          59m
istio-pilot-65cb5648bf-ntrpf              2/2     Running                0          29m
istio-policy-8596cc6554-8tdcr             2/2     Running                4          29m
istio-sidecar-injector-76f487845d-rrtnf   1/1     Running                1          29m
istio-telemetry-5c6b6d59f6-nljxl          2/2     Running                8          29m
prometheus-5679cb4dcd-28s46               1/1     Running                2          29m

查看系统日志是否有报错
# journalctl -f 
```  
