部署Traefik
=============
官方文档：https://docs.traefik.io/user-guide/kubernetes/  
项目地址：https://github.com/containous/traefik  

https://github.com/containous/traefik/tree/v1.7/examples/k8s  

1、部署rbac.yaml  
``` # kubectl apply -f https://raw.githubusercontent.com/containous/traefik/v1.7/examples/k8s/traefik-rbac.yaml ```  

2、部署traefik  
``` # kubectl apply -f https://raw.githubusercontent.com/containous/traefik/v1.7/examples/k8s/traefik-deployment.yaml ```  

3、查看运行的pod  
```
# kubectl get pod -n kube-system -o wide -l k8s-app=traefik-ingress-lb
NAME                                         READY   STATUS    RESTARTS   AGE     IP           NODE     NOMINATED NODE   READINESS GATES
traefik-ingress-controller-8c8b85bbc-6hsrv   1/1     Running   0          4m27s   10.244.1.3   node02   <none>           <none>
```  

4、查看service，暴露的nodeport为31494  
```
# kubectl get svc -n kube-system
NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                       AGE
kube-dns                  ClusterIP   10.96.0.10       <none>        53/UDP,53/TCP                 139m
tiller-deploy             ClusterIP   10.107.124.240   <none>        44134/TCP                     87m
traefik-ingress-service   NodePort    10.103.194.16    <none>        80:31155/TCP,8080:31494/TCP   5m5s
```  

5、访问traefik的dashboard  
http://192.168.101.68:31494  


6、Ingress方式访问taefik dashboard  
``` kubectl apply -f https://raw.githubusercontent.com/containous/traefik/v1.7/examples/k8s/ui.yaml ```  

7、查看yaml配置：  
包含了一个service和一个ingress规则  
```
---
apiVersion: v1
kind: Service
metadata:
  name: traefik-web-ui
  namespace: kube-system
spec:
  selector:
    k8s-app: traefik-ingress-lb
  ports:
  - name: web
    port: 80
    targetPort: 8080
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: traefik-web-ui
  namespace: kube-system
  annotations:
    kubernetes.io/ingress.class: traefik
spec:
  rules:
  - host: traefik-ui.minikube
    http:
      paths:
      - path: /
        backend:
          serviceName: traefik-web-ui
          servicePort: web
```  

8、查看ingress  
```
# kubectl get ingress -n kube-system
NAME             HOSTS                 ADDRESS   PORTS   AGE
traefik-web-ui   traefik-ui.minikube             80      2m4s



# kubectl describe ingress traefik-web-ui -n kube-system
Name:             traefik-web-ui
Namespace:        kube-system
Address:          
Default backend:  default-http-backend:80 (<none>)
Rules:
  Host                 Path  Backends
  ----                 ----  --------
  traefik-ui.minikube  
                       /   traefik-web-ui:web (10.244.1.3:8080)
Annotations:
  kubectl.kubernetes.io/last-applied-configuration:  {"apiVersion":"extensions/v1beta1","kind":"Ingress","metadata":{"annotations":{},"name":"traefik-web-ui","namespace":"kube-system"},"spec":{"rules":[{"host":"traefik-ui.minikube","http":{"paths":[{"backend":{"serviceName":"traefik-web-ui","servicePort":"web"},"path":"/"}]}}]}}

Events:  <none>



# kubectl get service -n kube-system 
NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                       AGE
kube-dns                  ClusterIP   10.96.0.10       <none>        53/UDP,53/TCP                 150m
tiller-deploy             ClusterIP   10.107.124.240   <none>        44134/TCP                     99m
traefik-ingress-service   NodePort    10.103.194.16    <none>        80:31155/TCP,8080:31494/TCP   16m
traefik-web-ui            ClusterIP   10.101.131.216   <none>        80/TCP                        6m
```  

修改集群外主机hosts:  
```
192.168.101.66 traefik-ui.minikube
192.168.101.67 traefik-ui.minikube
192.168.101.68 traefik-ui.minikube
```  

http://traefik-ui.minikube:31494/dashboard/


9、通过域名下不同的路径转发到不同的服务上去的 Ingress 配置  
```
$ vim my-k8s-traefik.yaml

apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: my-k8s-traefik
  namespace: kube-system
  annotations:
    kubernetes.io/ingress.class: traefik
    traefik.frontend.rule.type: PathPrefixStrip          #根据不同路径做转发需要配置此项
spec:
  rules:
  - host: my.k8s.traefik
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

$ kubectl create -f my-k8s-traefik.yaml
ingress "my-k8s-traefik" created

$ kubectl get ingress --all-namespaces
NAMESPACE     NAME                        HOSTS                                   ADDRESS   PORTS     AGE
kube-system   dashboard-ela-k8s-traefik   dashboard.k8s.traefik,ela.k8s.traefik             80        12m
kube-system   my-k8s-traefik              my.k8s.traefik                                    80        4s
kube-system   traefik-web-ui              traefik-ui.k8s                                    80        43m
```  
- 注意：这里我们根据路径来转发，需要指明 rule 为 PathPrefixStrip，配置为 traefik.frontend.rule.type: PathPrefixStrip  



