获取所有标签  
```
# kubectl get pods --show-labels
```  

获取标签为app和run的值  
```
# kubectl get pods -L app,run
```  

获取带app标签的pod  
```
# kubectl get pods -l app
```  

获取带app标签的pod并显示此pod的所有标签  
```
# kubectl get pods -l app --show-lables
```  

获取标签为release=canary的  
```
# kubectl get pods -l release=canary
```  

获取标签为release!=canary的  
```
# kubectl get pods -l release!=canary
```  

获取集合  
```
                          key              value
# kubectl get pods -l "release in (canary,beta,alpha)"
# kubectl get pods -l "release notin (canary,beta,alpha)"
```  

给pod打标签  
```
# kubectl label pods pod-demon release=canary
```  

修改pod标签  
```
# kubectl label pods pod-demon release=stable --overwrite
```  

给节点打标签  
```
# kubectl label node node01 disktype=ssd
```  

查看节点标签  
```
# kubectl get nodes --show-labels
```  


```
#deploy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-demo
  namespace: dev
spec:
  selector:
    matchLabels:
      app: web-demo
    matchExpressions:
      - {key: group, operator: In, values: [dev,test]}
  replicas: 1
  template:
    metadata:
      labels:
        group: dev
        app: web-demo
    spec:
      containers:
      - name: web-demo
        image: hub.mooc.com/kubernetes/web:v1
        ports:
        - containerPort: 8080
      nodeSelector:
        disktype: ssd
---
#service
apiVersion: v1
kind: Service
metadata:
  name: web-demo
  namespace: dev
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 8080
  selector:
    app: web-demo
  type: ClusterIP

---
#ingress
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: web-demo
  namespace: dev
spec:
  rules:
  - host: web-dev.mooc.com
    http:
      paths:
      - path: /
        backend:
          serviceName: web-demo
          servicePort: 80
```
