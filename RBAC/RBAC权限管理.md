认证「Authentication」

认证有如下几种方式：
- 1、HTTP Token认证：通过一个Token来识别合法用户。
  - HTTP Token的认证是用一个很长的特殊编码方式的并且难以被模仿的字符串来表达客户的一种方式。每一个Token对应一个用户名，存储在API Server能访问的文件中。当客户端发起API调用请求时，需要在HTTP Header里放入Token。
- 2、HTTP Base认证：通过用户名+密码的方式认证
  - 用户名:密码 用base64算法进行编码后的字符串放在HTTP Request中的Heather Authorization 域里发送给服务端，服务端收到后进行解码，获取用户名和密码。
- 3、最严格的HTTPS证书认证：基于CA根证书签名的客户端身份认证方式

授权「Authorization」

认证只是确认通信的双方都是可信的，可以相互通信。而授权是确定请求方有哪些资源的权限。API Server目前支持如下几种授权策略（通过API Server的启动参数 --authorization-mode 设置）
- AlwaysDeny：表示拒绝所有请求。仅用于测试
- AlwaysAllow：表示允许所有请求。如果有集群不需要授权流程，则可以采用该策略
- Node：节点授权是一种特殊用途的授权模式，专门授权由 kubelet 发出的 API 请求
- Webhook：是一种 HTTP 回调模式，允许使用远程 REST 端点管理授权
- ABAC：基于属性的访问控制，表示使用用户配置的授权规则对用户请求进行匹配和控制
- RBAC：基于角色的访问控制，默认使用该规则



RBAC权限管理
==========
RoloBinding可以将角色中定义的权限授予用户或用户组，RoleBinding包含一组权限列表(subjects)，权限列表中包含有不同形式的待授予权限资源类型(users, groups, or service accounts)；RoloBinding可以绑定一个Role也可以绑定一个ClusterRole，而ClusterRoleBinding只能绑定ClusterRole

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

创建一个用户只能管理 dev 空间
```
# cat /root/devuser-csr.json
{
  "CN": "devuser",
  "hosts": [],
  "key": {
  "algo": "rsa",
  "size": 2048
},
"names": [
  {
    "C": "CN",
    "ST": "BeiJing",
    "L": "BeiJing",
    "O": "k8s",
    "OU": "System"
  }
]
}

# 下载证书生成工具
wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
mv cfssl_linux-amd64 /usr/local/bin/cfssl
wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
wget https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
mv cfssl-certinfo_linux-amd64 /usr/local/bin/cfssl-certinfo
# cfssl gencert -ca=ca.crt -ca-key=ca.key -profile=kubernetes /root/devuser-csr.json | cfssljson-bare devuser

# 设置集群参数
export KUBE_APISERVER="https://172.20.0.113:6443"
kubectl config set-cluster kubernetes \
--certificate-authority=/etc/kubernetes/ssl/ca.pem \
--embed-certs=true \
--server=${KUBE_APISERVER} \
--kubeconfig=devuser.kubeconfig

# 设置客户端认证参数
kubectl config set-credentials devuser \
--client-certificate=/etc/kubernetes/ssl/devuser.pem \
--client-key=/etc/kubernetes/ssl/devuser-key.pem \
--embed-certs=true \
--kubeconfig=devuser.kubeconfig

# 设置上下文参数
kubectl config set-context kubernetes \
--cluster=kubernetes \
--user=devuser \
--namespace=dev \
--kubeconfig=devuser.kubeconfig

# 设置默认上下文
kubectl config use-context kubernetes --kubeconfig=devuser.kubeconfig
cp -f ./devuser.kubeconfig /root/.kube/config
kubectl create rolebinding devuser-admin-binding --clusterrole=admin --user=devuser --namespace=dev
```  
- --certificate-authority 指定ca证书
- --embed-certs=true 指定是否加密认证
- --server 指定服务器api_server
- --kubeconfig 创建用户的kubeconfig的文件
- --client-certificate 指定证书
- --client-key 指定私钥
- --cluster 指定集群
- --user 指定用户
- --namespace 指定名称空间
