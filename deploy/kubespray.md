
配置inventory
---

```
## Configure 'ip' variable to bind kubernetes services on a
## different ip than the default iface
node1 ip=192.168.0.10 ansible_ssh_host=192.168.0.10 ansible_user=root
node2 ip=192.168.0.11 ansible_ssh_host=192.168.0.11 ansible_user=root
node3 ip=192.168.0.12 ansible_ssh_host=192.168.0.12 ansible_user=root
node4 ip=192.168.0.13 ansible_ssh_host=192.168.0.13 ansible_user=root
node5 ip=192.168.0.14 ansible_ssh_host=192.168.0.14 ansible_user=root
node6 ip=192.168.0.15 ansible_ssh_host=192.168.0.15 ansible_user=root

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

[k8s-cluster:children]
kube-node
kube-master
```

开始自定义部署
```
ansible-playbook -i inventory/mycluster/hosts.yml cluster.yml -b -v \
  --private-key=~/.ssh/private_key
```

添加节点
```
ansible-playbook -i inventory/mycluster/hosts.yml scale.yml -b -v \
  --private-key=~/.ssh/private_key
```

删除节点
---
```
ansible-playbook -i inventory/mycluster/hosts.yml remove-node.yml -b -v \
--private-key=~/.ssh/private_key \
--extra-vars "node=nodename,nodename2"
```
