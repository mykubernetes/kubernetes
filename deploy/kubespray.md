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
