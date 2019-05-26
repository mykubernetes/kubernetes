# 需要安装 Metrics Server 和 custom metrics api  
1、创建一个测试pod  
``` # kubectl run myapp --image=ikubernetes/myapp:v1 --replicas=1 --requests='cpu=50m,memory=256Mi' --limits='cpu=50m,memory=256Mi' --labels='app=myapp' --expose --port=80 ```  

2、打补丁开启外网访问  
``` # kubectl patch svc myapp -p '{"spec":{"type":"NodePort"}}' ```  

3、设置hpa  
``` # kubectl autoscale deployment myapp --min=1 --max=8 --cpu-percent=60 ```  

4、压力测试  
``` # ab -c 1000 -n 500000 http://192.168.1.72:30718/index.html ```  

5、使用v2 的api支持内存  
```
apiVersion: autoscaling/v2beta1
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa-v2
spec:
  scaleTargetRef:                        #要缩放的目标资源
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 1                         #自动伸缩可缩减至的pod副本数的下限
  maxReplicas: 10                        #自动伸缩可扩展至的pod副本数的上线，其值不能低于minReplicas
  metrics:                               #用于计算所需pod副本数量的指标列表
  - type: Resource                       #表示指标源的类型，其值可为Objects、pod或Resource 
    resource:                            #引用资源指标，即当前被伸缩的pod对象中的requests和limits中定义的指标
      name: cpu
      targetAverageUtilization: 55
  - type: Resource
    resource:
      name: memory
      targetAverageValue: 50Mi
```  


根据自定义资源指标实现水平伸缩  
镜像  
ikubernetes/metrics-app  

配置文件  
```
apiVersion: autoscaling/v2beta1
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa-v2
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metricName: http_requests
      targetAverageValue: 800m
```  
详细方法参考https://www.jianshu.com/p/9abb697cd833
