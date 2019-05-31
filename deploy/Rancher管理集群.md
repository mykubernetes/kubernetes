# 如何管理多Kubernetes集群

为了业务的稳定性，通常我们会考虑将业务部署到不同的可用区，不同的地域，甚至是不同的云提供商环境中，这样当某个可用区、地域、云提供商不可用时依然不会影响业务的可用性。为了将我们的业务进行冗余部署，我们通常需要部署、管理多个Kubernetes集群，那我们如何轻松部署、管理多个Kubernetes集群呢，Kubernetes官方的解决方案是集群联邦，在这里我们不谈集群联邦，我们会使用一个第三方的管理工具来管理多个Kubernetes集群，这个管理工具就是Rancher。

## Rancher简介

Rancher是一个开源的Kubernetes管理平台，Rancher能够实现多Kubernetes集群的统一纳管，通过Rancher我们可以部署Kubernetes到各种云服务器上，也可以导入我们自己部署的Kubernetes集群进行管理。

Rancher专为使用容器、微服务和Kubernetes的组织而设计，可提高开发的速度，增强应用程序的可靠性，降低基础架构成本。Rancher平台由3个核心组件组成：

- **Rancher Kubernetes Engine（RKE）** 一个Kubernetes发行版，用于部署Kubernetes集群。
- **统一集群管理** 一个中心化管理引擎，它能够让我们在各云平台部署Kubernetes集群，也可管理我们自己部署的集群。
- **应用管理** Rancher Kubernetes拥有直观简洁的用户界面，同时还提供了LDAP认证、实时监控告警、日志以及CI/CD流水线等一系列拓展功能。

Rancher主要优势:

- **快速部署Kubernetes集群** 用户可以通过Rancher自动创建Kubernetes集群，并轻松地通过API、CLI或Web UI扩展控制平面和基础架构。一旦集群配置完成，组织中的管理员和用户都可以获得管理资格，团队因而可以在任何基础架构上部署、扩展和管理Kubernetes集群。
- **统一纳管公有云上托管的Kubernetes集群** 现在，几乎每个大型云提供商都提供托管的Kubernetes服务。通过这些服务，用户可以简单快速地建立Kubernetes集群，且后期只需要很少的持续维护，因为云提供商会负责操作和升级Kubernetes。Rancher是第一个为各个云提供商托管的Kubernetes集群提供一致、集中管理的平台。通过Rancher，企业能够应用标准安全策略和集中访问控制，且组织中部署的每个Kubernetes集群的都是可见的。
- **中央IT可视性和控制** Kubernetes在近一年里被快速且大量地采用，大规模的Kubernetes集群已非常普遍，企业用户需要针对不同版本、不同配置的Kubernetes保持一致的控制。不论是本地部署还是云中部署的Kubernetes集群，Rancher都可以为企业用户的IT管理员提供成熟的集中身份验证、访问控制、监控、告警和策略管理的解决方案。
- **助力开发人员和DevOps团队加速落地Kubernetes** 通过Rancher简洁、直观的用户界面，用户可以在Kubernetes上轻松部署服务，并可以查看集群上运行的所有内容。用户可以直接从用户界面获得常用配置选项，包括定义调度规则、健康检查、ingress controllers、secrets、存储和其他关键配置选项。高阶用户也可以直接使用完整的kubectl命令行以及Rancher的API和CLI。
- **应用程序部署与管理** Rancher的企业应用服务目录（Catalog），Rancher支持Helm charts，让企业数据中心复杂的应用管理部署像使用AppStore一样简单。用户可以访问社区贡献的Helm charts以及Rancher认证的应用模板。此外，用户还可以在Rancher中导入和管理私有的应用程序目录，并与指定的用户共享它们。


## 部署Rancher
官方文档 https://rancher.com/docs/rancher/v1.6/zh/kubernetes/addons/
### 安装helm

根据你的操作系选择适合你的helm包进行下载、安装。

    $ wget https://storage.googleapis.com/kubernetes-helm/helm-v2.13.1-linux-amd64.tar.gz
    $ tar xzvf helm-v2.13.1-linux-amd64.tar.gz
    $ linux-amd64/helm /usr/local/bin/
    $ chmod /usr/local/bin/helm

#### 创建服务账号tiller

    $ kubectl -n kube-system create serviceaccount tiller
    serviceaccount "tiller" created

#### 将账号和角色绑定

    $ kubectl create clusterrolebinding tiller \
    --clusterrole cluster-admin \
    --serviceaccount=kube-system:tiller
    clusterrolebinding "tiller” created

#### 初始化tiller安装

    $ helm init --tiller-image gcr.azk8s.cn/kubernetes-helm/tiller:v2.13.1 --skip-refresh --service-account tiller
    $HELM_HOME has been configured at /Users/<username>/.helm.

    Tiller (the Helm server-side component) has been installed into your Kubernetes Cluster.

    Please note: by default, Tiller is deployed with an insecure 'allow unauthenticated users' policy.
    To prevent this, run `helm init` with the --tiller-tls-verify flag.
    For more information on securing your installation see: https://docs.helm.sh/using_helm/#securing-your-helm-installation
    Happy Helming!

#### 等待tiller安装完成

    $ kubectl -n kube-system get pods
    NAME                                   READY     STATUS              RESTARTS   AGE
    ......
    tiller-deploy-56c4cf647b-ztt86         0/1       ContainerCreating   0          47s

    $ kubectl -n kube-system -o wide get pods
    NAME                                   READY     STATUS    RESTARTS   AGE       IP               NODE
    ......
    tiller-deploy-56c4cf647b-ztt86         1/1       Running   0          2m        10.42.2.2        172.16.2.10

### 安装rancher

#### 创建cattle-system命名空间

    $ kubectl create namespace cattle-system
    namespace "cattle-system” created

#### 创建证书secret（需要去证书颁发机构申请ssl证书）

    cd /etc/kubernetes/pki
    (umask 077;openssl genrsa -out rancher.hipstershop.cn.key 2048; )
    openssl req -new -key rancher.hipstershop.cn.key -out rancher.hipstershop.cn.csr -subj "/CN=rancher.hipstershop.cn"
    openssl x509 -req -in rancher.hipstershop.cn.csr -CA ./ca.crt -CAkey ./ca.key -CAcreateserial -out rancher.hipstershop.cn.crt -days 365

    查看证书
    openssl x509 -in rancher.hipstershop.cn.crt -text -noout

这个证书是我们用来通过HTTPS协议访问Rancher使用，我访问Rancher使用的域名是rancher.hipstershop.cn，我们需要为这个域名申请证书，并配置到Kubernetes中。

    $ kubectl -n cattle-system create secret tls tls-rancher-ingress --cert=./rancher.hipstershop.cn.crt --key=./rancher.hipstershop.cn.key
    secret "tls-rancher-ingress" created

如果这个证书有ca，同样需要为ca创建secret

    $ kubectl -n cattle-system create secret generic tls-ca \
    --from-file=DigiCert.ca
    secret "tls-ca” created

#### 添加rancher helm charts仓库

    $ helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
    "rancher-stable" has been added to your repositories

#### 使用helm部署rancher

    $ helm install rancher-stable/rancher \
    --name rancher \
    --namespace cattle-system \
    --set hostname=rancher.hipstershop.cn \
    --set ingress.tls.source=secret

    NAME:   rancher
    LAST DEPLOYED: Mon Oct  8 18:18:48 2018
    NAMESPACE: cattle-system
    STATUS: DEPLOYED

    RESOURCES:
    ==> v1/ClusterRoleBinding
    NAME     AGE
    rancher  6s

    ==> v1/Service
    NAME     TYPE       CLUSTER-IP     EXTERNAL-IP  PORT(S)  AGE
    rancher  ClusterIP  10.43.204.170  <none>       80/TCP   2s

    ==> v1beta1/Deployment
    NAME     DESIRED  CURRENT  UP-TO-DATE  AVAILABLE  AGE
    rancher  3        0        0           0          1s

    ==> v1beta1/Ingress
    NAME     HOSTS            ADDRESS  PORTS  AGE
    rancher  rancher.hipstershop.cn  80, 443  0s

    ==> v1/ServiceAccount
    NAME     SECRETS  AGE
    rancher  1        6s


    NOTES:
    Rancher Server has been installed.

    NOTE: Rancher may take several minutes to fully initialize. Please standby while Certificates are being issued and Ingress comes up.

    Check out our docs at https://rancher.com/docs/rancher/v2.x/en/

    Browse to https://rancher.hipstershop.com

    Happy Containering!

> --name 指定helm部署的名字为rancher
> --namespace 指定部署的命名空间为cattle-system
> --set hostname=rancher.hipstershop.cn 配置访问rancher使用的域名
> --set ingress.tls.source=secret 配置rancher使用的ssl证书

查看容器部署情况

    $ kubectl -n cattle-system -o wide get pods
    NAME                      READY     STATUS    RESTARTS   AGE       IP           NODE
    rancher-dbd67bf57-2wcxh   1/1       Running   0          9m        10.42.1.10   172.16.2.10
    rancher-dbd67bf57-b4ght   1/1       Running   0          9m        10.42.0.5    172.16.2.11
    rancher-dbd67bf57-fs7jl   1/1       Running   1          9m        10.42.2.3    172.16.2.12

部署ingress-nginx  
安装过程查看此文档  
https://github.com/mykubernetes/kubernetes/tree/master/ingress-nginx  

配置ingress-nginx  
```
$ vim rancher-ingress.yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: ingress-rancher
  namespace: cattle-system
  annotations:
    kubernets.io/ingress.class: "nginx"
spec:
  tls:
  - hosts:
    - rancher.hipstershop.cn
    secretName: tls-rancher-ingress
  rules:
  - host: rancher.hipstershop.cn
    http:
      paths:
      - path:
        backend:
          serviceName: rancher
          servicePort: 80
```  

## 使用Rancher

访问地址：https://rancher.hipstershop.cn:30443

第一次访问Rancher需要设置admin密码

![重置密码](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_reset_pwd.jpg)

设置Racher Server url

![设置 Racher Server url](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_server_url.jpg)

可以导入以前创建好的集群

![导入集群](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_import_k8s_cluster.jpg)

输入apiserver地址然后就可以导入以前创建好的集群了

![导入集群](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_import_k8s_cluster_2.jpg)

支持域认证，这个功能在企业里面是很实用的，如果你的企业是用域账号登录的，你就可以启用这个功能。

![域认证](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_ldap.jpg)

支持项目概念，原生的Kubernetes使用命名空间来隔离应用的，Rancher在命名空间的基础上有添加了项目这个概念，一个项目可以包含多命名空间，这很符合现实情况，我们的一个项目通常会包含多个微服务，这些微服务有一组开发工程师来维护，这样我们就可以为这组开发工程师赋予这个项目的权限，而其他工程师是无法看到这个项目里的应用的。

![域认证](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_project.jpg)

我们可以查看到这个Rancher管理的所有集群的集群信息

![查看本地集群信息](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_local_cluster.jpg)

进入到具体的项目，我们就可以查看到这个项目包含的所有微服务的部署情况

![工作负载](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_workload.jpg)

可以看到项目中微服务的负载均衡配置

![负载均衡](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_ingress.jpg)

也可以看到项目中的微服务的服务发现相关的信息

![服务发现](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_service.jpg)

另外，Rancher支持应用商店，我们可以像在手机上安装应用一样将服务部署到多个Kubernetes集群中

![服务](https://github.com/findsec-cn/k201/raw/master/imgs/1/rancher_catalog.jpg)

另外Ranchaer还可以导入已有的集群、创建新集群、对集群进行监控报警、对项目配置CI/CD流水线等。
