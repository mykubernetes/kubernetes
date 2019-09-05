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


```
# vim mandatory.yaml
apiVersion: extensions/v1beta1
kind: aemonSet               #修改控制器
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: ingress-nginx
spec:
  replicas: 4                #修改副本数
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
        volumeMounts:                                                  #自定义挂载
          - mountPath: /etc/nginx/template
            name: nginx-template-volume
            readOnly: true
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
      volumes:                                    #自定义挂载
        - name: nginx-template-volume
          configMap:
            name: nginx-template
            items:
            - key: nginx.tmpl
              path: nginx.tmpl
              
创建对应的configmap
在运行的ingress-nginx主机上将配置导出
# docker cp 34dc:/etc/nginx/template/nginx.tmpl .
拷贝到master主机上
将配置文件创建成configmap资源
# kubectl create cm nginx-template --from-file nginx.tmpl -n ingress-nginx

# kubect get cm -n ingress-nginx nginx-template -o yaml
```  
