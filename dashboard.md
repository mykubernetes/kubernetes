安装dashboard
=============
1、部署dashboard  
``` wget https://raw.githubusercontent.com/kubernetes/dashboard/v1.10.1/src/deploy/recommended/kubernetes-dashboard.yaml ```  

2、将service改为NodePort 类型
```
# vim kubernetes-dashboard.yaml 
kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  type: NodePort          #增加type: NodePort
  ports:
    - port: 443
      targetPort: 8443
      nodePort: 31620     #增加nodePort: 31620
  selector:
    k8s-app: kubernetes-dashboard
```  

3、应用配置文件
```
# kubectl create -f kubernetes-dashboard.yaml
secret/kubernetes-dashboard-certs created
serviceaccount/kubernetes-dashboard created
role.rbac.authorization.k8s.io/kubernetes-dashboard-minimal created
rolebinding.rbac.authorization.k8s.io/kubernetes-dashboard-minimal created
deployment.apps/kubernetes-dashboard created
service/kubernetes-dashboard created
```

4、下载镜像  
```
images=(
	kubernetes-dashboard-amd64:v1.10.0
)

for imageName in ${images[@]} ; do
    docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/$imageName
    docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/$imageName k8s.gcr.io/$imageName
done
```  

5、查看dashboard运行状态  
```
# kubectl get pod --namespace=kube-system -o wide | grep dashboard
kubernetes-dashboard-847f8cb7b8-wrm4l   1/1     Running   0          19m   10.244.2.5      k8s-node2    <none>           <none>
```  

6、查看svc地址  
```
# kubectl get service -n kube-system | grep dashboard
kubernetes-dashboard   NodePort    10.107.160.197   <none>        443:31620/TCP   32m
```  

7、创建dashboard-adminuser.yaml  
```
# vim dashboard-adminuser.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kube-system

应用配置文件
# kubectl create -f dashboard-adminuser.yaml
```  

8、查看admin-user账户的token
```
# kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep admin-user | awk '{print $1}')
Name:         admin-user-token-jtlbp
Namespace:    kube-system
Labels:       <none>
Annotations:  kubernetes.io/service-account.name: admin-user
              kubernetes.io/service-account.uid: a345b4d5-1006-11e9-b90d-000c291c25f3

Type:  kubernetes.io/service-account-token

Data
====
ca.crt:     1025 bytes
namespace:  11 bytes
token:      eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWp0bGJwIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJhMzQ1YjRkNS0xMDA2LTExZTktYjkwZC0wMDBjMjkxYzI1ZjMiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.uv3pzkM3_WQ8_gOwzEvKGrwfhXKtQmDYtfMpjmCDsPsq7OP3W5o0uFxKS7q2zbxw_pFZ3pFMyEk462RZo5z-Z6AB9gOXffvhqllSIQi3SzesvRcBqqW1n48SalGgBkCiqkX4DjjYDrHCAd5m-Uc7e3N28jWW5O4gUXEWwUtcobLVflEOnZ9Ykx9JBZPkmmS25toyoE6v8W7Zuv1moGBxmx4_AEnAFBUNDjZ7AxvmERQL-cQk6vsfrQ-hPejE1L3kgLbhpQnqQ3lJ3z7hrGMur31muW3WeOvd3Aciqr0TliyP1Wllf-hPuLPDsLdNZJpMx1B8O5jnw1cYbLsqQAaUXQ
```  

9、把获取到的Token复制到登录界面的Token输入框中  
