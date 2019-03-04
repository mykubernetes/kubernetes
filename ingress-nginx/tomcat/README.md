1、创建https证书和serce  
``` openssl genrsa -out tls.key 2048 ```  
``` openssl req -new -x509 -key tls.key -out tls.crt -subj /C=CN/ST=Beijing/L=Beijing/O=devOps/CN=wwww.tomcat.com ```
``` kubectl create secret tls tomcat-ingress-secret --cert=tls.crt --key=tls.key ```  
2、部署tomcat服务  
tomcat.yaml  
3、部署非https的tomcat前后端  
ingress-tomcat.yaml  
4、部署https的前后端
ingress-tomcat-tls.yaml
