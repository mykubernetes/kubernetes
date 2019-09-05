官方托管代码  
https://github.com/kubernetes/ingress-nginx/tree/master/deploy  
https://kubernetes.github.io/ingress-nginx/deploy/  
官方配置文档   
https://kubernetes.io/docs/concepts/services-networking/ingress/  
1、下载部署文件ingress-nginx  
``` # wget https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.21.0/deploy/mandatory.yaml ```  

2、执行部署文件  
```
# kubectl apply -f mandatory.yaml 
namespace/ingress-nginx created
configmap/nginx-configuration created
serviceaccount/nginx-ingress-serviceaccount created
clusterrole.rbac.authorization.k8s.io/nginx-ingress-clusterrole created
role.rbac.authorization.k8s.io/nginx-ingress-role created
rolebinding.rbac.authorization.k8s.io/nginx-ingress-role-nisa-binding created
clusterrolebinding.rbac.authorization.k8s.io/nginx-ingress-clusterrole-nisa-binding created
deployment.extensions/nginx-ingress-controller created
```  

3、nodeport方式对外提供服务  
```
# vim service-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: ingress-nginx
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
spec:
  type: NodePort
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
      nodePort: 30080
    - name: https
      port: 443
      targetPort: 443
      protocol: TCP
      nodePort: 30443
  selector:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx



# kubectl apply -f service-nodeport.yaml
service/ingress-nginx created
```  


可选操作，配置nginx-ingress-controller通过标签选择器，调度到对应机器上  
```
给node打标签
# kubectl label node node003 app=ingress

编辑配置文件添加标签选择
# vim mandatory.yaml
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
      app.kubernetes.io/part-of: ingress-nginx
  template:
    metadata:
      labels:
        app.kubernetes.io/name: ingress-nginx
        app.kubernetes.io/part-of: ingress-nginx
      annotations:
        prometheus.io/port: "10254"
        prometheus.io/scrape: "true"
    spec:
      serviceAccountName: nginx-ingress-serviceaccount
      hostNetwork: true     #添加hostnetwork
      nodeSelector:         #添加标签选择器
        app: ingress
      containers:
        - name: nginx-ingress-controller
          image: quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.21.0
          args:
            - /nginx-ingress-controller
            - --configmap=$(POD_NAMESPACE)/nginx-configuration
            - --tcp-services-configmap=$(POD_NAMESPACE)/tcp-services
            - --udp-services-configmap=$(POD_NAMESPACE)/udp-services
            - --publish-service=$(POD_NAMESPACE)/ingress-nginx
            - --annotations-prefix=nginx.ingress.kubernetes.io
          securityContext:
            capabilities:
              drop:
                - ALL
              add:
                - NET_BIND_SERVICE
            # www-data -> 33
            runAsUser: 33
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
          ports:
            - name: http
              containerPort: 80
            - name: https
              containerPort: 443
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /healthz
              port: 10254
              scheme: HTTP
            initialDelaySeconds: 10
            periodSeconds: 10
            successThreshold: 1
            timeoutSeconds: 1
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /healthz
              port: 10254
              scheme: HTTP
            periodSeconds: 10
            successThreshold: 1
            timeoutSeconds: 1
```  


4、查看ingress-nginx组件状态  
```
# kubectl get pod -n ingress-nginx 
NAME                                        READY   STATUS    RESTARTS   AGE
nginx-ingress-controller-6bdcbbdfdc-wd2bn   1/1     Running   0          24s
查看创建的ingress service暴露的端口 
# kubectl get svc -n ingress-nginx 
NAME            TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
ingress-nginx   NodePort   10.104.138.113   <none>        80:30737/TCP,443:31952/TCP   13s
```  

5、创建ingress-nginx后端服务  
```
# vim deploy-demon.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  selector:
    app: myapp
    release: canary
  ports:
  - name: http
    port: 80
    targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deploy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
      release: canary
  template:
    metadata:
      labels:
        app: myapp
        release: canary
    spec:
      containers:
      - name: myapp
        image: ikubernetes/myapp:v2
        ports:
        - name: httpd
          containerPort: 80
```  


6、创建相关服务及检查状态是否就绪  
```
# kubectl apply -f deploy-demon.yaml 
service/myapp unchanged
deployment.apps/myapp-deploy configured

# kubectl get pods                   
NAME                             READY   STATUS    RESTARTS   AGE
myapp-deploy-5cc79fc966-2228d    1/1     Running   0          62s
myapp-deploy-5cc79fc966-42w2d    1/1     Running   0          62s
```

7、创建基于域名访问虚拟主机的Ingress配置  
```
# vim  ingress-myapp.yaml 
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: ingress-myapp
  namespace: default
  annotations:
    kubernets.io/ingress.class: "nginx"
spec:
#  tls:                                    #tls模式需要先创建secret资源，并且为tls格式
#  - hosts:
#    - myapp.node01.com 
#    secretName: tomcat-ingress-secret     #指定secret资源名
  rules:
  - host: myapp.node01.com
    http:
      paths:
      - path: 
        backend:
          serviceName: myapp
          servicePort: 80
```  

8、查看创建的ingress规则  
```
# kubectl apply -f ingress-myapp.yaml  
ingress.extensions/ingress-myapp created
# kubectl get ingress
NAME            HOSTS              ADDRESS   PORTS   AGE
ingress-myapp   myapp.node01.com             80      11s
```  

9、进入容器查看nginx配置  
```
# kubectl exec -n ingress-nginx -ti nginx-ingress-controller-6bdcbbdfdc-wd2bn -- /bin/sh
$ cat nginx.conf
...... 
       ## start server myapp.node01.com
        server {
                server_name myapp.node01.com ;

                listen 80;

                set $proxy_upstream_name "-";

                location / {

                        set $namespace      "default";
                        set $ingress_name   "ingress-myapp";
                        set $service_name   "myapp";
                        set $service_port   "80";
                        set $location_path  "/";
...... 
```  

9、配置外部主机houst文件进行域名访问  
```
cat /etc/hosts
192.168.101.66  myapp.node01.com  
192.168.101.67  myapp.node01.com  
192.168.101.68  myapp.node01.com  
```  

10、浏览器访问  


11、通过域名下不同的路径转发到不同的服务上去的Ingress配置  
```
vim my-k8s-ingress.yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: my-k8s-ingress
  namespace: kube-system
  annotations:
    ingress.kubernetes.io/rewrite-target: /              #添加此端配置
spec:
  rules:
  - host: my.k8s.ingress
    http:
      paths:
      - path: /dashboard
        backend:
          serviceName: kubernetes-dashboard
          servicePort: 80
      - path: /kibana
        backend:
          serviceName: kibana-logging
          servicePort: 5601

# 重新应用或替换 ingress
$ kubectl apply -f my-k8s-ingress.yaml 或者 kubectl replace -f my-k8s-ingress.yaml
```  
