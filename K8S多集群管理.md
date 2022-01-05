在实际生产环境中，往往需要维护多个k8s集群，在多个环境和节点之间切换，影响工作效率，不符合devops的理念，因此尝试在单个节点下面维护多个k8s集群。

## 1) 模拟存在两套k8s集群

第一个k8s集群：
```
[root@k8smaster ~]# kubectl get nodes
NAME         STATUS     ROLES          VERSION
k8smaster    Ready      controlplane   v1.23.1
k8slave      Ready      worker         v1.23.1
```
- k8smaster：182.168.40.180
- k8slave：192.168.40.181

第二个k8s集群
```
[root@k8smaster2]# kubectl get nodes
NAME          STATUS     ROLES         VERSION
k8smaster2    Ready      controlplane  v1.23.1
k8slave2      Ready      worker        v1.23.1
```
- k8smaster2：192.168.40.185
- k8slave2：  192.168.40.186

## 2) kubeconfig文件

查看kubeconfig文件可以使用kubectl config命令,也可以直接查看/root/.kube/config（默认位置）

k8smaster集群
```
[root@k8smaster ~]#kubectl  config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://192.168.40.180:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
```

k8smaster2集群                     
```
[root@k8smaster2~]# kubectl  config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://192.168.40.185:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name:kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
```

### 3) 在k8smaster上配置k8smaster2的cluster、user、context

a、添加cluster
```
[root@k8smaster]#kubectl config set-cluster k8smaster2 --server=https://192.168.40.185:6443--insecure-skip-tls-verify=true
```

b、添加user
```
[root@k8smaster]#kubeadm token create --print-join-command
[root@k8smaster]#kubectl config set-credentials k8smaster2-user --token= clknqa.km25oi82urcuja9u
```

c、添加context
```
[root@k8smaster]# kubectl config set-context k8smaster2-context--cluster= k8smaster2  --user=k8smaster2-user
```

d、切换context管理k8s集群
```
[root@k8smaster]#kubectl config use-context k8smaster2-context
```

至此，在k8smaster节点上维护了两个k8s集群，按照同样的办法可以添加更多的k8s集群，只是通过不同的context进行切换。
