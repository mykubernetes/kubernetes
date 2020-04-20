nginx rpm包：http://nginx.org/packages/rhel/7/x86_64/RPMS/

安装配置nginx
```
# rpm -vih http://nginx.org/packages/rhel/7/x86_64/RPMS/nginx-1.16.0-1.el7.ngx.x86_64.rpm
# vim /etc/nginx/nginx.conf
……
stream {

    log_format  main  '$remote_addr $upstream_addr - [$time_local] $status $upstream_bytes_sent';

    access_log  /var/log/nginx/k8s-access.log  main;

    upstream k8s-apiserver {
                server 192.168.31.63:6443;
                server 192.168.31.64:6443;
            }
    
    server {
       listen 6443;
       proxy_pass k8s-apiserver;
    }
}
……

# systemctl start nginx
# systemctl enable nginx
```

Nginx+Keepalived高可用

主节点：
```
#配置
# yum install keepalived
# vi /etc/keepalived/keepalived.conf
global_defs { 
   notification_email { 
     acassen@firewall.loc 
     failover@firewall.loc 
     sysadmin@firewall.loc 
   } 
   notification_email_from Alexandre.Cassen@firewall.loc  
   smtp_server 127.0.0.1 
   smtp_connect_timeout 30 
   router_id NGINX_MASTER
} 

vrrp_script check_nginx {
    script "/etc/keepalived/check_nginx.sh"
}

vrrp_instance VI_1 { 
    state MASTER 
    interface ens33
    virtual_router_id 51 # VRRP 路由 ID实例，每个实例是唯一的 
    priority 100    # 优先级，备服务器设置 90 
    advert_int 1    # 指定VRRP 心跳包通告间隔时间，默认1秒 
    authentication { 
        auth_type PASS      
        auth_pass 1111 
    }  
    virtual_ipaddress { 
        192.168.31.60/24
    } 
    track_script {
        check_nginx
    } 
}


#编写脚本
# cat /etc/keepalived/check_nginx.sh 
#!/bin/bash
count=$(ps -ef |grep nginx |egrep -cv "grep|$$")

if [ "$count" -eq 0 ];then
    exit 1
else
    exit 0
fi

#启动
# systemctl start keepalived
# systemctl enable keepalived
```

备节点：
```
#配置
# cat /etc/keepalived/keepalived.conf 
     
global_defs { 
   notification_email { 
     acassen@firewall.loc 
     failover@firewall.loc 
     sysadmin@firewall.loc 
   } 
   notification_email_from Alexandre.Cassen@firewall.loc  
   smtp_server 127.0.0.1 
   smtp_connect_timeout 30 
   router_id NGINX_BACKUP
} 

vrrp_script check_nginx {
    script "/etc/keepalived/check_nginx.sh"
}

vrrp_instance VI_1 { 
    state BACKUP 
    interface ens33
    virtual_router_id 51 # VRRP 路由 ID实例，每个实例是唯一的 
    priority 90    # 优先级，备服务器设置 90 
    advert_int 1    # 指定VRRP 心跳包通告间隔时间，默认1秒 
    authentication { 
        auth_type PASS      
        auth_pass 1111 
    }  
    virtual_ipaddress { 
        192.168.31.60/24
    } 
    track_script {
        check_nginx
    } 
}


#编写脚本
# cat /etc/keepalived/check_nginx.sh 
#!/bin/bash
count=$(ps -ef |grep nginx |egrep -cv "grep|$$")

if [ "$count" -eq 0 ];then
    exit 1
else
    exit 0
fi

#启动
# systemctl start keepalived
# systemctl enable keepalived
```

测试
```
# ip a
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 00:0c:29:9d:ee:30 brd ff:ff:ff:ff:ff:ff
    inet 192.168.31.63/24 brd 192.168.31.255 scope global noprefixroute ens33
       valid_lft forever preferred_lft forever
    inet 192.168.31.60/24 scope global secondary ens33
       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe9d:ee30/64 scope link 
       valid_lft forever preferred_lft forever
```
关闭nginx测试VIP是否漂移到备节点。

测试VIP是否正常工作
```
# curl -k https://10.4.192.39:6443/version
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {
    
  },
  "status": "Failure",
  "message": "Unauthorized",
  "reason": "Unauthorized",
  "code": 401
}
```

将Node连接VIP
```
# cd /etc/kubernetes/cfg
# grep 192 *
bootstrap.kubeconfig:    server: https://192.168.31.63:6443
kubelet.kubeconfig:    server: https://192.168.31.636443
kube-proxy.kubeconfig:    server: https://192.168.31.63:6443

批量修改：
sed -i 's#192.168.31.63#192.168.31.60#g' 
```
