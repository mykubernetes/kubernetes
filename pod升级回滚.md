
暂停更新
```
kubectl rollout pause deploy web-rollingupdate -n dev
```
恢复更新
```
kubectl rollout resume deploy web-rollingupdate -n dev
```
回滚到上一个版本
```
kubectl rollout undo deploy web-rollingupdate -n dev
```
查看历史版本
```
kubectl rollout history deploy web-rollingupdate -n dev
```
查看当前状态
```
kubectl rollout status deploy web-rollingupdate -n dev
```

测试
---
1、部署一个简单的 Nginx 应用  
```
# cat nginx-deployment.yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.7.9
        ports:
        - containerPort: 80
```  

```
# kubectl create -f https://kubernetes.io/docs/user-guide/nginx-deployment.yaml --record
```  
- --record参数可以记录命令，我们可以很方便的查看每次revision的变化

2、扩容  
```
# kubectl scale deployment nginx-deployment --replicas 10
```  

3、通过horizontal pod autoscaling实现为Deployment设置自动扩展  
```
# kubectl autoscale deployment nginx-deployment --min=10 --max=15 --cpu-percent=80
```  

4、更新镜像  
```
# kubectl set image deployment/nginx-deployment nginx=nginx:1.9.1
```  

5、回滚  
```
# kubectl rollout undo deployment/nginx-deployment
```  

6、查看回滚的状态  
```
# kubectl rollout status deployment/nginx-deployment
```  

7、查看历史更新版本
```
# kubectl rollout history deployment/nginx-deployment
```  

8、回滚上一个版本和回滚指定版本
```
# kubectl rollout undo deployment/nginx-deployment
# kubectl rollout undo deployment/nginx-deployment --to-revision=2 ## 可以使用 --revision参数指定某个历史版本
```  

9、暂停的更新  
```
# kubectl rollout pause deployment/nginx-deployment
```  
