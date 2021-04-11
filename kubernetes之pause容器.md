一、简单说明
===
我们在启动Pod的时候，发现有很多pause容器运行。每次启动一个Pod，都会运行一个pause容器。那么这个pause容器究竟是干啥的，它到底有什么作用呢？

Pause容器又叫Infra容器，我们在启动kubelet的服务时，指定了下面的配置参数：
```
--pod-infra-container-image=mirrorgooglecontainers/pause-amd64:3.1
```
这个Pause容器的版本，我们可以自己构建，也可以直接采用官方提供的版本。关于pause容器的构建，可以参考https://github.com/kubernetes/kubernetes/tree/master/build/pause进行。

在kubernetes的node节点，执行docker ps，可以发现每个node上运行了很多的pause容器，具体如下：
```
[root@k8s002 ~]# docker ps |grep pause
d316fa79ddf6        mirrorgooglecontainers/pause-amd64:3.1   "/pause"                 6 days ago          Up 6 days                               k8s_POD_kafka-2_kafka_852a
6124-3870-11eb-95e3-000c295ccbe7_0406c946ee75c        mirrorgooglecontainers/pause-amd64:3.1   "/pause"                 6 days ago          Up 6 days                               k8s_POD_test-redis-5f79b66bc
8-5shqd_test_8cae9d57-386f-11eb-95e3-000c295ccbe7_040c96739a14e        mirrorgooglecontainers/pause-amd64:3.1   "/pause"                 6 days ago          Up 6 days                               k8s_POD_zk-2_kafka_749c97a
```
每个Pod都有一个特殊的被称为"根容器"的Pause容器，其它容器则为业务容器。这些业务容器共享Pause容器的网络栈和Volume挂载卷，因此它们之间通信和数据交换更为高效。在设计时，我们可以充分利用这一特性将一组密切相关的服务进程放入同一个Pod中。同一个Pod里的容器通过localhost就能互相通信。

二、kubernetes的pause容器功能
===
kubernetes的pause容器主要为每个业务容器提供,在pod中担任与其它容器namespace共享的基础

1）运行一个pause容器：
```
[root@k8s001 ~]# docker run -d --name pause -p 8080:80 registry.cn-hangzhou.aliyuncs.com/google_containers/pause-amd64:3.1
```

2）运行一个nginx容器，nginx将为localhost:2368创建一个代理
```
[root@k8s001 ~]# cat <<EOF >> nginx.conf
error_log stderr;
events { worker_connections  1024; }
http {
    access_log /dev/stdout combined;
    server {
        listen 80 default_server;
        server_name example.com www.example.com;
        location / {
            proxy_pass http://127.0.0.1:2368;
        }
    }
}
EOF
[root@k8s001 ~]# docker run -d --name nginx -v `pwd`/nginx.conf:/etc/nginx/nginx.conf --net=container:pause --ipc=container:pause --pid=container:pause nginx
```

3）为ghost创建一个应用容器(这是一个博客软件)
```
[root@k8s001 ~]# docker run -d --name ghost --net=container:pause --ipc=container:pause --pid=container:pause ghost
```

4）验证
```
# 查看运行的容器
[root@k8s001 ~]# docker ps | grep -E "pause|nginx|ghost"
f72edf025141        ghost                                                                 "docker-entrypoint.s…"   About a minute ago   Up About a minute                  
        ghost7ac2d677fbf7        nginx                                                                 "/docker-entrypoint.…"   2 minutes ago        Up 2 minutes                       
        nginxb33f3b7c705d        registry.cn-hangzhou.aliyuncs.com/google_containers/pause-amd64:3.1   "/pause"                 15 minutes ago       Up 15 minutes       0.0.0.0:8880->80
/tcp   pause
# 通过浏览器访问http://ip:8880端口，查看是否可以访问到ghost界面
# 或者通过curl抓取页面内容
[root@k8s001 ~]# curl http://localhost:8080
<!DOCTYPE html>
<html lang="en">
<head>

    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />

    <title>Ghost</title>
    <meta name="HandheldFriendly" content="True" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
......
```
从上面的步骤可见：
- pause容器将内部80端口映射到宿主机8080端口。
- pause容器在宿主机上设置好网络namespace后，nginx容器加入到该网络的namespace中。
- nginx容器启动的时候指定了-net=container:pause。
- ghost容器启动时，同样方式加入到该网络的namespace中。
- 这样三个容器共享了网络，互相之间就可以使用localhost直接通信。
- --ipc=container:pause，--pid=container:pause就是三个容器的ipc和pid处于同一个namespace中，init进程为pause。

这里，我们进入ghost容器内部查看：
```
[root@k8s001 ~]# docker exec -it f72edf025141 /bin/bash
root@b33f3b7c705d:/var/lib/ghost# ps aux
USER        PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root          1  0.0  0.0   1012     4 ?        Ss   02:45   0:00 /pause
root          8  0.0  0.0  10648  3400 ?        Ss   02:57   0:00 nginx: master process nginx -g daemon off;
101          37  0.0  0.0  11088  1964 ?        S    02:57   0:00 nginx: worker process
node         38  0.9  0.0 2006968 116572 ?      Ssl  02:58   0:06 node current/index.js
root        108  0.0  0.0   3960  2076 pts/0    Ss   03:09   0:00 /bin/bash
root        439  0.0  0.0   7628  1400 pts/0    R+   03:10   0:00 ps aux
```
在ghost容器中可以看到pause和nginx容器的进程，并且pause容器的PID为1，而在kubernetes中容器的PID=1的进程则为容器本身的业务进程。
