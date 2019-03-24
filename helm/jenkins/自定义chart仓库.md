自定义chart仓库
===============

1、添加自定义仓库  
``` # helm repo add chartmuseum http://192.168.20.174:8089 --username admin --password admin123 ```  

2、安装上传自定义仓库插件  
``` # helm plugin install https://github.com/chartmuseum/helm-push ```  

3、将本地文件上传到chartmuseum仓库  
``` # helm push ./helm/go-demo-3/ chartmuseum --username admin --password admin123 ```  

4、查看上传文件信息  
``` # curl http://192.168.20.174:8089/index.yaml -u admin:admin123 ```  

5、搜索chartmuseum仓库内容，发现是空的，这时候需要更新仓库  
```# helm search chartmuseum/ ```  

6、更新仓库  
``` # helm repo update ```  

7、再次搜索  
``` # helm search chartmuseum/ ```  

8、查看详细信息  
``` # helm inspect chartmuseum/go-demo-3 ```  
