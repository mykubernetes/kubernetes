安装 ChartMuseum仓库
================
chart仓库，nginx,http等都可以作为chart仓库  
1、安装ChartMuseum  
链接：https://pan.baidu.com/s/15kczilfAGHGFeTOWNw5Pww 提取码：alp8 
```
# wget https://s3.amazonaws.com/chartmuseum/release/latest/bin/linux/amd64/chartmuseum 
# chmod +x chartmuseum
# mv chartmuseum /usr/local/bin/
```  

2、启动chartmuseum服务  
``` # chartmuseum --debug --port=8089 --storage="local" --storage-local-rootdir="./chartstorage" --basic-auth-user admin --basic-auth-pass admin123 ```  

3、检查健康状态  
``` # curl http://192.168.101.67:8089/health ```  

4、访问ChartMuseum仓库  
``` # curl -u admin:admin123 http://192.168.101.67:8089/index.yaml ```  





添加自定义chart仓库
===============

1、添加自定义仓库  
``` # helm repo add chartmuseum http://192.168.101.67:8089 --username admin --password admin123 ```  

2、安装上传自定义仓库插件  
``` # helm plugin install https://github.com/chartmuseum/helm-push ```  

3、将本地文件上传到chartmuseum仓库  
``` # helm push jenkins chartmuseum --username admin --password admin123 ```  
注：jenkins是目录

4、查看上传文件信息  
``` # curl http://192.168.101.67:8089/index.yaml -u admin:admin123 ```  

5、搜索chartmuseum仓库内容，发现是空的，这时候需要更新仓库  
```# helm search chartmuseum/ ```  

6、更新仓库  
``` # helm repo update ```  

7、再次搜索  
``` # helm search chartmuseum/ ```  

8、查看详细信息  
``` # helm inspect chartmuseum/jenkins ```  

9、删除文件  
``` # curl -XDELETE "http://192.168.101.67:8089/api/charts/jenkins/0.1.0" -u admin:admin123 ```  
