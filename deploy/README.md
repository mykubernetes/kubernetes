kubeadm安装官方文档  
https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm/

kops安装官方文档  
https://kubernetes.io/docs/setup/production-environment/tools/kops/  
https://github.com/kubernetes/kops

kubespray安装官方文档  
https://kubernetes.io/docs/setup/production-environment/tools/kubespray/  
https://github.com/kubernetes-sigs/kubespray

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
