secret使用方法
===
创建secret有三种模式  
```
docker-registry       下载docker仓库镜像保存的密码文件
generic               连接数据库等需要保密的密码文件
tls                   https证书的文件
```  

一、命令创建方式  
---
1、创建secret generic类型资源用户密码
```
# kubectl create secret generic mysql-auth --from-literal=username=root --from-literal=password=ikubernetes
```  

2、获取创建的资源  
```
# kubectl get secrets mysql-auth -o yaml
apiVersion: v1
data:
  password: aWt1YmVybmV0ZXM=
  username: cm9vdA==
kind: Secret
metadata:
······
type: Opaque
```  

3、解码  
```
# echo aWt1YmVybmV0ZXM= | base64 -d
ikubernetes
```  


二、文件创建方式
---
1、配置ssh认证的Secret对象  
```
# ssh-keygen -t rsa -p '' -f ${HOME}/.ssh/id_sra
```  
2、创建secret  
```
# kubectl create secret generic ssh-key-secret --from-file=ssh-privatekey=${HOME}/.ssh/id_rsa --from-file=ssh-publickey=${HOME}/.ssh/id_rsa.pub
```  

三、通过配置文件方式创建  
---
```
1、将明文转换为密文
# echo -n "admin" | base64
YWRtaW4=

# echo -n "1f2d1e2e67df" | base64
MWYyZDFlMmU2N2Rm

2、创建配置文件
# vim secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysecret
type: Opaque
data:
  password: MWYyZDFlMmU2N2Rm
  username: YWRtaW4=

# kubectl apply -f secrets.yaml
```  

四、使用方式  
---
1、将Secret挂载到Volume中  
```
apiVersion: v1
kind: Pod
metadata:
  labels:
    name: seret-test
  name: seret-test
spec:
  volumes:
  - name: secrets
    secret:
      secretName: mysecret
  containers:
  - image: hub.atguigu.com/library/myapp:v1
    name: db
    volumeMounts:
    - name: secrets
      mountPath: "/etc/secrets"
      readOnly: true
```  

2、将Secret导出到环境变量中  
```
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: pod-deployment
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: pod-deployment
  spec:
    containers:
    - name: pod-1
      image: hub.atguigu.com/library/myapp:v1
      ports:
      - containerPort: 80
      env:
      - name: TEST_USER
        valueFrom:
          secretKeyRef:
            name: mysecret
            key: username
      - name: TEST_PASSWORD
        valueFrom:
          secretKeyRef:
            name: mysecret
            key: password
```  

五、基于私钥和数字证书文件创建用于SSL/TLS通信的Secret对象  
---
1、用命令生成私钥和自签证书  
```
# (umask 077 ; openssl genrsa -out nginx.key 2048)
# openssl req -new -x509 -key nginx.key -out nginx.crt \
-subj /C=CN/ST=Beijing/L=Beijing/O=DevOps/CN=www.ilinux.io
```  

2、无论用户提供的证书和私钥文件使用的是什么名称，它们一律会被转换为分别以tls.key（私钥）和tls. crt（证书）为其键名  
```
# kubectl create secret tls nginx-ssl --key=./nginx.key --cert=./nginx.crt
```  

3、类型为kubernetes.io/tls  
```
# kubectl get secrets nginx-ssl
NAME          TYPE                   DATA           AGE
nginx-ssl    kubernetes.io/tls         2             37s
```  

4、清单式创建  
```
apiVersion: v1
kind: Secret
metadata:
  name: secret-demo
stringData:                   #以明文方式在创建时自动转换为base64编码格式，如果用改用data需要先转码
  username: redis
  password: redispass
type: Opaqu
```  

5、挂着secret卷挂着到pod  
```
apiVersion: v1
kind: Pod
metadata:
  name: secret-volume-demo
  namespace: default
spec:
  containers:
  - image: nginx:alpine
    name: web-server
    volumeMounts:
    - name: nginxcert
      mountPath: /etc/nginx/ssl/
      readOnly: true
  volumes:
  - name: nginxcert
    secret:
      secretName: nginx-ssl  

进入容器查看挂载证书
# kubectl exec secret-volume-demo ls /etc/nginx/ssl/
tls.crt
tls.key
```  


六、imagePullSecret 资源对象
---
1、创建imagepullsecret资源对象  
```
# kubectl create secret docker-registry local-reqistry --docker-username=Ops \
--docker-password=Opspass --docker-email=ops@ilinux.io
```  

2、此类 Secret 对象打印的类型信息为kubernetes.io/dockerconfigjson  
```
# kubectl get secrets local-registry
NAME               TYPE                                              DATA       AGE
local-registry    kubernetes.io/dockerconfigjson       1             7s
```  

3、挂着secret卷挂着到pod  
```
apiVersion: v1
kind: Pod
metadata:
  name: secret-imagepull-demo
  namespace: default
spec:
  imagePullSecrets:
  - name: local-registry
  containers:
  - image: registry.ikubernetes.io/dev/myimage
    name: myapp
```  
