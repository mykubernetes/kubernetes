https://blog.csdn.net/educast/article/details/89957284

准备工作
---

1、所有机器都必须关闭selinux
```
setenforce 0
sed -i --follow-symlinks 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux
```

2、配置防火墙
在master机器上
```
firewall-cmd --permanent --add-port=6443/tcp
firewall-cmd --permanent --add-port=2379-2380/tcp
firewall-cmd --permanent --add-port=10250/tcp
firewall-cmd --permanent --add-port=10251/tcp
firewall-cmd --permanent --add-port=10252/tcp
firewall-cmd --permanent --add-port=10255/tcp
firewall-cmd --reload
modprobe br_netfilter
echo '1' > /proc/sys/net/bridge/bridge-nf-call-iptables
sysctl -w net.ipv4.ip_forward=1
```

如果关闭了防火墙，则只需执行最下面三行。
在node机器上
```
firewall-cmd --permanent --add-port=10250/tcp
firewall-cmd --permanent --add-port=10255/tcp
firewall-cmd --permanent --add-port=30000-32767/tcp
firewall-cmd --permanent --add-port=6783/tcp
firewall-cmd  --reload
echo '1' > /proc/sys/net/bridge/bridge-nf-call-iptables
sysctl -w net.ipv4.ip_forward=1
```

或者关闭防火墙
```
systemctl stop firewalld
```

3、在ansible-client机器上安装ansible
```
yum install epel-release
yum install ansible
```

4、安装jinja2
```
easy_install pip
pip2 install jinja2 --upgrade

升级jinja2
pip install --upgrade pip
pip2 install jinja2 --upgrade
```

5、安装Python 3.6
```
yum install python36 –y
```

6、ssh互信
```
ssh-keygen

ssh-copy-id root@172.20.0.88
ssh-copy-id root@172.20.0.89
ssh-copy-id root@172.20.0.90
ssh-copy-id root@172.20.0.91
ssh-copy-id root@172.20.0.92
```


在ansible-client机器上安装kubespray
---

1、下载源码
```
git clone https://github.com/kubernetes-sigs/kubespray.git
```

2、安装kubespray需要的包：
```
cd kubespray
pip install -r requirements.txt
```

3 拷贝inventory/sample ，命名为inventory/mycluster ，mycluster可以改为其他的名字
```
cp -r inventory/sample inventory/mycluster
```

4 使用inventory_builder，初始化inventory文件
```
# declare -a IPS=(172.20.0.88 172.20.0.89 172.20.0.90 172.20.0.91 172.20.0.92)
# CONFIG_FILE=inventory/mycluster/hosts.ini python36 contrib/inventory_builder/inventory.py ${IPS[@]}
```

5、此时生成的配置文件
```
cat inventory/mycluster/host.ini

[k8s-cluster:children]
kube-master      
kube-node        

[all]
node1    ansible_host=172.20.0.88 ip=172.20.0.88
node2    ansible_host=172.20.0.89 ip=172.20.0.89
node3    ansible_host=172.20.0.90 ip=172.20.0.90
node4    ansible_host=172.20.0.91 ip=172.20.0.91
node5    ansible_host=172.20.0.92 ip=172.20.0.92

[kube-master]
node1    
node2    

[kube-node]
node1    
node2    
node3    
node4    
node5    

[etcd]
node1    
node2    
node3    

[calico-rr]

[vault]
node1    
node2    
node3 
```

6、使用ansible playbook部署kubespray
```
ansible-playbook -i inventory/mycluster/hosts.ini cluster.yml
```

修改全局变量
```
vim inventory/mycluster/k8s-cluster/k8s-cluster.yml
kube_service_addresses: 10.233.0.0/18
kube_pods_subnet: 10.233.64.0/18
kube_network_plugin: calico

#配置dns
dns_mode: coredns
```


```
vim group_vars/all/all.yml
# 负载均衡域名，提前配置好DNS解析
apiserver_loadbalancer_domain_name: "kubernetes.7mxing.com"
     
# 负载均衡
loadbalancer_apiserver:
  address: 10.0.128.160
  port: 6443
```

开始自定义部署
```
ansible-playbook -i inventory/mycluster/hosts.ini cluster.yml -b -v \
  --private-key=~/.ssh/private_key
```

添加节点
```
ansible-playbook -i inventory/mycluster/hosts.ini scale.yml -b -v \
  --private-key=~/.ssh/private_key
```

删除节点
```
ansible-playbook -i inventory/mycluster/hosts.ini remove-node.yml -b -v \
--private-key=~/.ssh/private_key \
--extra-vars "node=nodename,nodename2"
```

卸载
```
ansible-playbook -i inventory/mycluster/hosts.ini reset.yml
```

升级  
https://github.com/kubernetes-sigs/kubespray/blob/master/docs/upgrades.md
