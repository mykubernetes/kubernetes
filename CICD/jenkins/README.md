使用说明：  
1、部署  
``` > # kubectl apply -f jenkins.yaml ```  
2、web访问  
``` http://192.168.20.171:30080/jenkins ```  
3、获取密码  
``` > # kubectl -n jenkins exec jenkins-0 -it -- cat /var/jenkins_home/secrets/initialAdminPassword ```  
