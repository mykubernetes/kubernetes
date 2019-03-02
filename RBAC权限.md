RBAC权限管理
==========
一、Pod权限  
----------
1、创建一个admin账号  
``` kubectl create serviceaccount admin ```  

2、创建一个pod使用admin账号  
```
# cat serviceaccount.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-sa-demo
  namespace: default
  labels:
    app: myapp
spec:
  containers:
  - name: myapp
    image: ikubernetes/myapp:v1
    ports:
    - name: http
      containerPort: 80
  serviceAccountName: admin
```  

二、用户权限  
-----------
1、查看用户权限  
```
# kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://192.168.1.70:6443
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
2、生成用户使用的证书  
```
cd /etc/kubernetes/pki
(umask 077;openssl genrsa -out admin.key 2048; )
openssl req -new -key admin.key -out admin.csr -subj "/CN=admin"
openssl x509 -req -in admin.csr -CA ./ca.crt -CAkey ./ca.key -CAcreateserial -out admin.crt -days 365

查看证书
openssl x509 -in admin.crt -text -noout
```  

3、创建用户  
``` kubectl config set-credentials admin --client-certificate=./admin.crt --client-key=./admin.key --embed-certs=true ```  

4、用户赋予集群权限  
``` kubectl config set-context admin@kubernetes --cluster=kuberentes --user=admin ```  

5、查看权限  
```
# kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://192.168.1.70:6443
  name: kubernetes
contexts:
- context:
    cluster: kuberentes
    user: admin
  name: admin@kubernetes
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
- name: kubernetes-admin
  user:
    client-certificate-data: REDACTED
    client-key-data: REDACTED
```  

6、切换账号  
``` kubectl config use-context admin@kubernetes ```  

7、添加集群  
``` # kubectl config set-cluster mycluster --kubeconfig=/tmp/test.conf --server="https://192.168.1.70:6443" --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs=true ```  

8、查看集群  
```
# kubectl config view --kubeconfig=/tmp/test.conf
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://192.168.1.70:6443
  name: mycluster
contexts: []
current-context: ""
kind: Config
preferences: {}
users: []
```  
