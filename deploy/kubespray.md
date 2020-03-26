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

下载源码
```
git clone https://github.com/kubernetes-sigs/kubespray.git
```

修改配置文件
```
cp -r inventory/sample inventory/mycluster

vim inventory/mycluster/inventory
# ## Configure 'ip' variable to bind kubernetes services on a
# ## different ip than the default iface
# ## We should set etcd_member_name for etcd cluster. The node that is not a etcd member do not need to set the value, or can set the empty string value.
[all]
node1 ansible_host=95.54.0.12  # ip=10.3.0.1 etcd_member_name=etcd1
node2 ansible_host=95.54.0.13  # ip=10.3.0.2 etcd_member_name=etcd2
node3 ansible_host=95.54.0.14  # ip=10.3.0.3 etcd_member_name=etcd3
node4 ansible_host=95.54.0.15  # ip=10.3.0.4 etcd_member_name=etcd4
node5 ansible_host=95.54.0.16  # ip=10.3.0.5 etcd_member_name=etcd5
node6 ansible_host=95.54.0.17  # ip=10.3.0.6 etcd_member_name=etcd6

# ## configure a bastion host if your nodes are not directly reachable
# bastion ansible_host=x.x.x.x ansible_user=some_user

[kube-master]
node1
node2

[etcd]
node1
node2
node3

[kube-node]
node2
node3
node4
node5
node6

[calico-rr]

[k8s-cluster:children]
kube-master
kube-node
calico-rr
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
ansible-playbook -i inventory/mycluster/inventory cluster.yml -b -v \
  --private-key=~/.ssh/private_key
```

添加节点
```
ansible-playbook -i inventory/mycluster/inventory scale.yml -b -v \
  --private-key=~/.ssh/private_key
```

删除节点
```
ansible-playbook -i inventory/mycluster/inventory remove-node.yml -b -v \
--private-key=~/.ssh/private_key \
--extra-vars "node=nodename,nodename2"
```

升级  
https://github.com/kubernetes-sigs/kubespray/blob/master/docs/upgrades.md
