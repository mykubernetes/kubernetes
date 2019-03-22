1、设置web访问地址  
``` # JENKINS_ADDR=www.jenkins.com ```  

2、部署  
``` # helm install stable/jenkins --name jenkins --namespace jenkins --values helm/jenkins-values.yml --set Master.HostName=$JENKINS_ADDR ``` 

3、web访问  
http://192.168.101.66/jenkins  

4、获取密码  
```
# JENKINS_PASS=$(kubectl -n jenkins get secret jenkins \
-o jsonpath="{.data.jenkins-admin-password}" \
| base64 --decode; echo)

# echo $JENKINS_PASS
```
