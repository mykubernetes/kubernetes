官网  
https://docs.projectcalico.org  
安装calico  
https://docs.projectcalico.org/v3.1/getting-started/kubernetes/  
整合flannel安装calico  
https://docs.projectcalico.org/v3.1/getting-started/kubernetes/installation/flannel  

1、安装  
```
kubectl apply -f \
https://docs.projectcalico.org/v3.1/getting-started/kubernetes/installation/hosted/canal/rbac.yaml

kubectl apply -f \
https://docs.projectcalico.org/v3.1/getting-started/kubernetes/installation/hosted/canal/canal.yaml
```  
2、说明文档  
``` # kubectl explain networkpolicy.spec ```  

3、规则测试  

1)创建两个测试名称空间  
```
# kubectl create namespace dev
# kubectl create namespace prod
```
2)配置ingress规则  
```
# cat deny-all-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```  
3)配置一个web测试pod  
```
# cat pod-a.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod1
spec:
  containers:
  - name: myapp
    image: ikubernetes/myapp:v1
```  
4)应用规则到dev  
``` # kubectl apply -f deny-all-ingress.yaml -n dev ```  
5)运行pod到两个不同名称空间测试  
```
kubectl apply -f pod-a.yaml -n dev
# curl 10.244.1.2

# kubectl apply -f pod-a.yaml -n prod
# curl 10.244.1.3
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
```  

6）允许所有规则  
```
# cat allow-all-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - {}

# kubectl apply -f deny-all-ingress.yaml -n dev
# curl 10.244.1.2
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
# curl 10.244.1.3
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
```  
7)允许一组pod可以访问  
```
# kubectl label pods pod1 app=myapp -n dev
# cat allow-netpol-demo.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-myapp-ingress
spec:
  podSelector:
    matchLabels:
      app: myapp
  ingress:
  - from: 
    - ipBlock:
        cidr: 10.244.0.0/16
        except:
        - 10.244.1.2/32
    ports:
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443

# kubectl apply -f allow-netpol-demo.yaml -n dev

# curl 10.244.1.2
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
# curl 10.244.1.3
Hello MyApp | Version: v1 | <a href="hostname.html">Pod Name</a>
```  
