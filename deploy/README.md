查看日志
```
journalctl -l -u kube-apiserver
journalctl -l -u kube-controller-manager
journalctl -l -u kube-scheduler
journalctl -l -u kubelet
journalctl -l -u kube-proxy
journalctl -l -u etcd
journalctl -l -u flanneld
```  

查看证书时间  
```
openssl x509 -in apiserver.crt -text -noout
```  
