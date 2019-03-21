一、部署  
1、部署  
``` > # kubectl apply -f jenkins.yaml ```  
2、web访问  
``` http://192.168.20.171:30080/jenkins ```  
3、获取密码  
``` > # kubectl -n jenkins exec jenkins-0 -it -- cat /var/jenkins_home/secrets/initialAdminPassword ```  

二、配置ci  
1、安装kubernetes插件  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins001.png)  
2、进入系统设置，到最后  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins002.png)  
3、添加一个云  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins003.png)  
4、获取集群IP地址添加到下图kuberneted地址里  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins004.png)  
5、配置jenkins连接到api  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins005.png)  
6、添加一个job测试  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins006.png)  
7、配置pipeline脚本  
```
podTemplate(
    label: 'kubernetes',
    containers: [
        containerTemplate(name: 'maven', image: 'maven:alpine', ttyEnabled: true, command: 'cat'),
        containerTemplate(name: 'golang', image: 'golang:alpine', ttyEnabled: true, command: 'cat')
    ]
) {
    node('kubernetes') {
        container('maven') {
            stage('build') {
                sh 'mvn --version'
            }
            stage('unit-test') {
                sh 'java -version'
            }
        }
        container('golang') {
            stage('deploy') {
                sh 'go version'
            }
        }
    }
}
```  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins007.png)  
8、构建  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins008.png)  
9、查看控制台  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins010.png)  
10、控制台输出完成，任务执行成功  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins011.png)  
11、命令查看build空间会多出一个job任务，任务完成后会消失  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins009.png)  
12、查看管理节点，会多出一个主机，任务完成后会消失  
![image](https://github.com/mykubernetes/linux-install/blob/master/image/jenkins012.png)  
