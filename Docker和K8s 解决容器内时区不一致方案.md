Docker/K8s 解决容器内时区不一致方案
===================================
使用 docker 容器启动服务后，如果使用默认 Centos 系统作为基础镜像，就会出现系统时区不一致的问题，因为默认 Centos 系统时间为 UTC 协调世界时 (Universal Time Coordinated)，一般本地所属时区为 CST（＋8 时区，上海时间），时间上刚好相差 8 个小时。  

```
# 查看本地时间
$ date
Wed Mar  6 16:41:08 CST 2019

# 查看容器内 centos 系统默认时区
$ docker run -it centos /bin/sh
sh-4.2# date
Wed Mar  6 08:41:45 UTC 2019
```  

1、Dockerfile中处理  
可以直接修改 Dockerfile，在构建系统基础镜像或者基于基础镜像再次构建业务镜像时，添加时区修改配置即可。  
```
$ cat Dockerfile.date
FROM centos

RUN rm -f /etc/localtime \
&& ln -sv /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo "Asia/Shanghai" > /etc/timezone

# 构建容器镜像
$ docker build -t centos7-date:test -f Dockerfile.date .
Sending build context to Docker daemon  4.426GB
Step 1/2 : FROM centos
 ---> 1e1148e4cc2c
Step 2/2 : RUN rm -f /etc/localtime && ln -sv /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone
 ---> Running in fe2e931c3cf2
'/etc/localtime' -> '/usr/share/zoneinfo/Asia/Shanghai'
Removing intermediate container fe2e931c3cf2
 ---> 2120143141c8
Successfully built 2120143141c8
Successfully tagged centos7-date:test

$ docker run -it centos7-date:test /bin/sh
sh-4.2# date
Wed Mar  6 16:40:01 CST 2019
```  
可以看到，系统时间正常了，个人比较推荐这种方式  

2、容器启动时处理  
在容器启动时通过挂载主机时区配置到容器内，前提是主机时区配置文件正常。  
```
# 挂载本地 /etc/localtime 到容器内覆盖配置
$ docker run -it -v /etc/localtime:/etc/localtime centos /bin/sh
sh-4.2# date
Wed Mar  6 16:42:38 CST 2019

# 或者挂载本地 /usr/share/zoneinfo/Asia/Shanghai 到容器内覆盖配置
$ docker run -it -v /usr/share/zoneinfo/Asia/Shanghai:/etc/localtime centos /bin/sh
sh-4.2# date
Wed Mar  6 16:42:52 CST 2019
```  
以上两种方式，其实原理都一样，在 Centos 系统中，/usr/share/zoneinfo/Asia/Shanghai 和 /etc/localtime 二者是一致的，我们一般会将二者软连接或者直接 cp 覆盖。  

3、进入容器内处理  
还有一种方式，就是进入到容器内处理，如果容器删除后重新启动新的容器，还需要我们进入到容器内配置，非常不方便。  
```
# 进入到容器内部配置
$ docker run -it centos /bin/sh
sh-4.2# date
Wed Mar  6 08:43:29 UTC 2019
sh-4.2# rm -f /etc/localtime && ln -sv /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
'/etc/localtime' -> '/usr/share/zoneinfo/Asia/Shanghai'
sh-4.2# date
Wed Mar  6 16:43:54 CST 2019
```  

4、k8s 解决容器时间不一致  
通过挂载主机时间配置的方式解决  
```
$ cat busy-box-test.yaml
apiVersion: v1
kind: Pod
metadata:
  name: busy-box-test
  namespace: default
spec:
  restartPolicy: OnFailure
  containers:
  - name: busy-box-test
    image: busybox
    imagePullPolicy: IfNotPresent
    volumeMounts:
    - name: date-config
      mountPath: /etc/localtime
    command: ["sleep", "60000"]
  volumes:
  - name: date-config
    hostPath:
      path: /etc/localtime
               
```  
注意：如果主机 /etc/localtime 已存在且时区正确的话，可以直接挂载，如果本地 /etc/localtime 不存在或时区不正确的话，那么可以直接挂载 /usr/share/zoneinfo/Asia/Shanghai 到容器内 /etc/localtime，都是可行的。




