helm部署jenkins
=============
1、部署jenkins名称空间  
``` kubectl apply -f jenkins-ns.yaml ```  

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
