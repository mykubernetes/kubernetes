一、删除node节点
---
1、先查看一下这个node节点上的pod信息
```
kubectl get pod -o wide 
```
     
2、驱逐这个node节点上的pod
```
# kubectl drain node02 --delete-local-data --force --ignore-daemonsets
```

3、删除这个node节点
```
# kubectl delete nodes node02
```

4、然后在node06这个节点上执行如下命令：
```
kubeadm reset
systemctl stop kubelet
systemctl stop docker
rm -rf /var/lib/cni/
rm -rf /var/lib/kubelet/*
rm -rf /etc/cni/
ifconfig cni0 down
ifconfig flannel.1 down
ifconfig docker0 down
ip link delete cni0
ip link delete flannel.1
systemctl start docker
systemctl start kubelet
```
如果不做上面的操作的话会导致这个节点上的pod无法启动，具体报错信息为：networkPlugin cni failed to set up pod "alertmanager-main-1_monitoring" network: failed to set bridge ad has an IP address different from 10.244.5.1/24 ，意思是已经集群网络cni已经有一个不同于10.244.51.1/24 的网络地址，所以需要执行上述命令重置节点网络。


二、重新加入这个node节点 
---
节点加入集群的命令格式：kubeadm join --token <token> <master-ip>:<master-port> --discovery-token-ca-cert-hash sha256:<hash>　

由于默认token的有效期为24小时，当过期之后，该token就不可用了，解决方法如下：

重新生成新的token ==> kubeadm token create　

1.查看当前的token列表
```
kubeadm token list
```

2.重新生成新的token
```
kubeadm token create
```

3.再次查看当前的token列表
```
kubeadm token list
```

4.获取ca证书sha256编码hash值
```
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'
```

5.节点加入集群
```
kubeadm join 172.16.40.2:58443 --token 369tcl.oe4punpoj9gaijh7(新的token) --discovery-token-ca-cert-hash sha256:7ae10591aa593c2c36fb965d58964a84561e9ccd416ffe7432550a0d0b7e4f90(ca证书sha256编码hash值) 
```
再次在master节点查看node发现已经加入到集群了。

6、或者直接在创建token的时候生成产全部命令
```
kubeadm token create --print-join-command
``` 
