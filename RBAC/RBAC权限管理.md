RBAC权限管理
==========
一、Pod权限  
----------
1、创建一个pod账号和角色  
```
apiVersion: v1
kind: ServiceAccount                        #定义一个pod的账号
metadata:
  name: admin
  namespace: default
---
kind: Role                                  #定义一个角色
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: default
  name: pods-reader
rules:                                      #定义这个角色的规则
- apiGroups: [""]                           # "" 表示核心组
  resources: ["pods", "pods/log"]           #规则应用的目标资源名列表
  verbs: ["get", "list", "watch"]           #操作列表，get、list、create、update、patch、watch、proxy、redirect、delete和deletecollection
---
kind: RoleBinding                           #将pod的账号绑定到角色上
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: resource-reader
  namespace: default
subjects:                                   #pod账号绑定
- kind: User                                #资源类型
  name: admin                               #serviceaccount名
  apiGroup: rbac.authorization.k8s.io
roleRef:                                    #角色绑定
  kind: Role                                #资源类型
  name: pods-reader                         #role名
  apiGroup: rbac.authorization.k8s.io
```  
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
  serviceAccountName: admin                 #serviceAccount名
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

RBAC  
创建角色并拥有权限，将user或service绑定到角色上，这样user或service就有当前集群的权限  
将user或service绑定到clusterrolebinding上，这样user或service将有来了所有集群的权限  
将rolebindding绑定到clusterrolebinding上，这样user将有了当前集群的权限  
```
role
  operations
  objects
rolebindding
  user account OR service account
  role
clusterrole OR clusterrolebinding
```  
1、创建一个role  
``` kubectl create role pod-reader --verb=get,list,watch --resource=pods --dry-run -o yaml ```

2、查看权限  
```
kubectl get role
kubectl describe role pod-reader
```  
3、将用户绑定当rolebinding上  
``` kubectl create rolebinding read-pods --role=pod-reader --user=magedu --dry-run -o yaml ```

4、创建集群角色  
``` kubectl create clusterrole cluster-reader --verb=get,list,watch --resource=pods -o yaml --dry-run ```

5、将用户绑定到clusterrolebinding上  
``` kubectl create clusterrolebinding read-all-pods --clusterrole=cluster-reader --user=magedu --dry-run -o yaml ```
