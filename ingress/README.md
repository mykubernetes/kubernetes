官方自定义configmap配置示例  
https://github.com/kubernetes/ingress-nginx/tree/master/docs/examples  

官网  
https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/  

grafana监控nginx-ingress  
https://github.com/kubernetes/ingress-nginx/tree/master/deploy/grafana/dashboards  

```
# kubectl get cm -n ingress-nginx 
NAME                                DATA   AGE
ingress-controller-leader-nginx     0      1d
nginx-configuration                 0      1d
tcp-services                        0      1d
udp-services                        0      1d

# cat tcp-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tcp-services
  namespace: ingress-nginx
data:
  "30000": dev/web-demo:80

# kubectl apply -f tcp-config.yaml
在宿主机上查看端口
netstat -tnlp |grep 30000
tcp        0       0   0.0.0.0:30000           0.0.0.0:*      LISTEN  23514/nginx: master
tcp6       0       0   :::30000                :::*           LISTEN  23514/nginx: master


# cat nginx-config.yaml
kind: ConfigMap
apiVersion: v1
metadata:
  name: nginx-configuration
  namespace: ingress-nginx
  labels:
    app: ingress-nginx
data:
  proxy-body-size: "64m"
  proxy-read-timeout: "180"
  proxy-send-timeout: "180"

```  
