># 准备基础环境

## 1、代码版本仓库 Gitlab

### 1.1 部署gitlab

```
docker run -d \
  --name gitlab \
  -p 8443:443 \
  -p 9999:80 \
  -p 9998:22 \
  -v $PWD/config:/etc/gitlab \
  -v $PWD/logs:/var/log/gitlab \
  -v $PWD/data:/var/opt/gitlab \
  -v /etc/localtime:/etc/localtime \
  lizhenliang/gitlab-ce-zh:latest
  gitlab/gitlab-ce:latest
```

访问地址：http://IP:9999

初次会先设置管理员密码 ，然后登陆，默认管理员用户名root，密码就是刚设置的。

### 1.2 创建项目，提交测试代码

https://github.com/lizhenliang/simple-microservice

代码分支说明：

- dev1  交付代码

- dev2 编写Dockerfile构建镜像

- dev3 K8S资源编排

- dev4 增加微服务链路监控

- master 最终上线

拉取dev3分支，推送到私有代码仓库：

```
git clone -b dev3 https://github.com/lizhenliang/simple-microservice
git clone http://192.168.31.70:9999/root/microservice.git
cp -rf simple-microservice/* microservice
cd microservice
git add .
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
git commit -m 'all'
git push origin master
```

## 2、镜像仓库 Harbor

### 2.1 安装docker与docker-compose

```
# wget http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo
# yum install docker-ce -y
# systemctl start docker
# systemctl enable docker
```

```
curl -L https://github.com/docker/compose/releases/download/1.25.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 2.2 解压离线包部署

```
# tar zxvf harbor-offline-installer-v1.9.1.tgz
# cd harbor
# vi harbor.yml
hostname: 192.168.31.70
# ./prepare
# ./install.sh --with-chartmuseum
# docker-compose ps 
```

--with-chartmuseum 参数表示启用Charts存储功能。

### 2.3 配置Docker可信任

由于habor未配置https，还需要在docker配置可信任。

```
# cat /etc/docker/daemon.json 
{"registry-mirrors": ["http://f1361db2.m.daocloud.io"],
  "insecure-registries": ["192.168.31.70"]
}
# systemctl restart docker
```

## 3、应用包管理器 Helm

### 3.1 安装Helm工具

```
# wget https://get.helm.sh/helm-v3.0.0-linux-amd64.tar.gz
# tar zxvf helm-v3.0.0-linux-amd64.tar.gz 
# mv linux-amd64/helm /usr/bin/
```

### 3.2 配置国内Chart仓库

```
# helm repo add stable http://mirror.azure.cn/kubernetes/charts
# helm repo add aliyun https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts 
# helm repo list
```

### 3.3 安装push插件

```
# helm plugin install https://github.com/chartmuseum/helm-push
```

如果网络下载不了，也可以直接解压课件里包：

```
# tar zxvf helm-push_0.7.1_linux_amd64.tar.gz
# mkdir -p /root/.local/share/helm/plugins/helm-push
# chmod +x bin/*
# mv bin plugin.yaml /root/.local/share/helm/plugins/helm-push
```

### 3.4 添加repo

```
# helm repo add  --username admin --password Harbor12345 myrepo http://192.168.31.70/chartrepo/library
```

### 3.5 推送与安装Chart

```
# helm push mysql-1.4.0.tgz --username=admin --password=Harbor12345 http://192.168.31.70/chartrepo/library
# helm install web --version 1.4.0 myrepo/demo
```

## 4、微服务数据库 MySQL

```
# yum install mariadb-server -y
# mysqladmin -uroot password '123456'
```

或者docker创建

```
docker run -d --name db -p 3306:3306 -v /opt/mysql:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=123456 mysql:5.7 --character-set-server=utf8
```

最后将微服务数据库导入。

## 5、K8S PV自动供给

先准备一台NFS服务器为K8S提供存储支持。

```
# yum install nfs-utils
# vi /etc/exports
/ifs/kubernetes *(rw,no_root_squash)
# mkdir -p /ifs/kubernetes
# systemctl start nfs
# systemctl enable nfs
```

并且要在每个Node上安装nfs-utils包，用于mount挂载时用。

由于K8S不支持NFS动态供给，还需要先安装上图中的nfs-client-provisioner插件：

```
# cd nfs-client
# vi deployment.yaml # 修改里面NFS地址和共享目录为你的
# kubectl apply -f .
# kubectl get pods
NAME                                     READY   STATUS    RESTARTS   AGE
nfs-client-provisioner-df88f57df-bv8h7   1/1     Running   0          49m
```

## 6、持续集成 Jenkins

由于默认插件源在国外服务器，大多数网络无法顺利下载，需修改国内插件源地址：

```
cd jenkins_home/updates
sed -i 's/http:\/\/updates.jenkins-ci.org\/download/https:\/\/mirrors.tuna.tsinghua.edu.cn\/jenkins/g' default.json && \
sed -i 's/http:\/\/www.google.com/https:\/\/www.baidu.com/g' default.json
```


插件介绍：https://github.com/jenkinsci/kubernetes-plugin
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins_k8s_01.png)

参考：https://github.com/jenkinsci/docker-jnlp-slave
```
FROM centos:7
LABEL maintainer lizhenliang

RUN yum install -y java-1.8.0-openjdk maven curl git libtool-ltdl-devel && \
  yum clean all && \
  rm -rf /var/cache/yum/* && \
  mkdir -p /usr/share/jenkins

COPY slave.jar /usr/share/jenkins/slave.jar
COPY jenkins-slave /usr/bin/jenkins-slave
COPY settings.xml /etc/maven/settings.xml
RUN chmod +x /usr/bin/jenkins-slave
COPY helm kubectl /usr/bin/

ENTRYPOINT ["jenkins-slave"]
```

插件介绍：  
https://github.com/jenkinsci/kubernetes-plugin  
https://plugins.jenkins.io/kubernetes/  
