helm 部署jenkins
=============
1、部署jenkins名称空间  
```
# cat jenkins-ns.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: jenkins

---

apiVersion: v1
kind: Namespace
metadata:
  name: build

---

apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins
  namespace: jenkins

---

kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: jenkins
  namespace: build
rules:
- apiGroups: [""]
  resources: ["pods", "pods/exec", "pods/log"]
  verbs: ["*"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]

---

apiVersion: rbac.authorization.k8s.io/v1beta1
kind: RoleBinding
metadata:
  name: jenkins
  namespace: build
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: jenkins
subjects:
- kind: ServiceAccount
  name: jenkins
  namespace: jenkins



# kubectl apply -f jenkins-ns.yaml
```  

2、搜索jenkins  
```
# helm search jenkins
NAME          	CHART VERSION	APP VERSION	DESCRIPTION                                                 
stable/jenkins	0.35.2       	lts        	Open source continuous integration server. It supports mu...
```  

3、部署文档版jenkins  
``` helm install stable/jenkins --name jenkins --namespace jenkins ```  

4、web访问  
 http://192.168.101.66:NodePort/jenkins  

5、获取密码  
``` kubectl -n jenkins get secret jenkins -o jsonpath="{.data.jenkins-admin-password}" | base64 --decode; echo ```

6、查看jenkins详细信息  
``` helm inspect stable/jenkins ```  

7、查看状态  
``` helm status jenkins ```  

8、删除jenkins  
1)不删除chart文件  
``` helm delete jenkins ```  
查看状态会显示jenkins  
``` helm status jenkins ```  
2)同时删除chart文件  
``` helm delete jenkins --purge ```  
查看状态不会显示jenkins  
``` helm status jenkins ```  

Helm 定制安装和回滚
============
1、搜索jenkins  
``` helm search jenkins ```

2、查看 values 文件  
``` helm inspect stable/jenkins ```  

3、查看全部信息  
``` helm inspect stable/jenkins ```  

4、根据查看信息的描述定制部署jenkins修改镜像标签  
``` helm install stable/jenkins --name jenkins --namespace jenkins --set Master.ImageTag=2.112-alpine ```  

5、web访问  
http://192.168.101.66:NodePort  

6、更新新版本jenkins  
``` helm upgrade jenkins stable/jenkins --set Master.ImageTag=2.116-alpine --reuse-values ```  

7、查看jenkins更新版本  
``` helm list ```  

8、回滚上一个版本  
``` helm rollback jenkins 0 ```  

9、查看当前版本  
``` helm list ```  
