创建https证书和secre
``` openssl genrsa -out tls.key 2048 ```  
``` openssl req -new -x509 -key tls.key -out tls.crt -subj /C=CN/ST=Beijing/L=Beijing/O=devOps/CN=wwww.tomcat.com ```
``` kubectl create secret tls tomcat-ingress-secret --cert=tls.crt --key=tls.key ```  
