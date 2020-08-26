apiserver有三种级别的客户端认证方式  
1、HTTPS证书认证：基于CA根证书签名的双向数字证书认证方式  
2、HTTP Token认证：通过一个Token来识别合法用户  
3、HTTP Base认证：通过用户名+密码的认证方式  

HTTP Token认证：通过一个Token来识别合法用户

1、创建可以访问api的用户
```
# 创建账号
kubectl create serviceaccount curl-admin -n kube-system

# 角色绑定
kubectl create clusterrolebinding curl-admin --clusterrole=cluster-admin --serviceaccount=kube-system:curl-admin

#查看TOKEN
kubectl describe secrets -n kube-system $(kubectl -n kube-system get secret | awk '/curl-admin/{print $1}')
```

2、设置环境变量
```
1、获取TOKEN信息
# kubectl describe secrets $(kubectl get secrets -n kube-system |grep admin |cut -f1 -d ' ') -n kube-system |grep -E '^token' |cut -f2 -d':'|tr -d '  '|tr -d ' '

2、定义TOKEN环境变量
# TOKEN=$(kubectl describe secrets $(kubectl get secrets -n kube-system |grep admin |cut -f1 -d ' ') -n kube-system |grep -E '^token' |cut -f2 -d':'|tr -d '  '|tr -d ' ')

3、获取api-server地址
# kubectl config view |grep server|cut -f 2- -d ":" | tr -d " "

4、设置api-server地址环境变量
# APISERVER=$(kubectl config view |grep server|cut -f 2- -d ":" | tr -d " ")
```

3、通过TOKEN方式访问api-server
```
# curl -H "Authorization: Bearer $TOKEN" $APISERVER/api  --insecure

{
  "kind": "APIVersions",
  "versions": [
    "v1"
  ],
  "serverAddressByClientCIDRs": [
    {
      "clientCIDR": "0.0.0.0/0",
      "serverAddress": "192.168.0.130:6443"
    }
  ]
}
```


```
# curl -H "Authorization: Bearer $TOKEN" $APISERVER  --insecure
{
  "paths": [
    "/api",
    "/api/v1",
    "/apis",
    "/apis/",
    "/apis/admissionregistration.k8s.io",
    "/apis/admissionregistration.k8s.io/v1beta1",
    "/apis/apiextensions.k8s.io",
    "/apis/apiextensions.k8s.io/v1beta1",
    "/apis/apiregistration.k8s.io",
    "/apis/apiregistration.k8s.io/v1",
    "/apis/apiregistration.k8s.io/v1beta1",
    "/apis/apps",
    "/apis/apps/v1",
    "/apis/apps/v1beta1",
    "/apis/apps/v1beta2",
    "/apis/authentication.k8s.io",
    "/apis/authentication.k8s.io/v1",
    "/apis/authentication.k8s.io/v1beta1",
    "/apis/authorization.k8s.io",
    "/apis/authorization.k8s.io/v1",
    "/apis/authorization.k8s.io/v1beta1",
    "/apis/autoscaling",
    "/apis/autoscaling/v1",
    "/apis/autoscaling/v2beta1",
    "/apis/autoscaling/v2beta2",
    "/apis/batch",
    "/apis/batch/v1",
    "/apis/batch/v1beta1",
    "/apis/certificates.k8s.io",
    "/apis/certificates.k8s.io/v1beta1",
    "/apis/coordination.k8s.io",
    "/apis/coordination.k8s.io/v1beta1",
    "/apis/events.k8s.io",
    "/apis/events.k8s.io/v1beta1",
    "/apis/extensions",
    "/apis/extensions/v1beta1",
    "/apis/networking.k8s.io",
    "/apis/networking.k8s.io/v1",
    "/apis/policy",
    "/apis/policy/v1beta1",
    "/apis/rbac.authorization.k8s.io",
    "/apis/rbac.authorization.k8s.io/v1",
    "/apis/rbac.authorization.k8s.io/v1beta1",
    "/apis/scheduling.k8s.io",
    "/apis/scheduling.k8s.io/v1beta1",
    "/apis/storage.k8s.io",
    "/apis/storage.k8s.io/v1",
    "/apis/storage.k8s.io/v1beta1",
    "/healthz",
    "/healthz/autoregister-completion",
    "/healthz/etcd",
    "/healthz/log",
    "/healthz/ping",
    "/healthz/poststarthook/apiservice-openapi-controller",
    "/healthz/poststarthook/apiservice-registration-controller",
    "/healthz/poststarthook/apiservice-status-available-controller",
    "/healthz/poststarthook/bootstrap-controller",
    "/healthz/poststarthook/ca-registration",
    "/healthz/poststarthook/generic-apiserver-start-informers",
    "/healthz/poststarthook/kube-apiserver-autoregistration",
    "/healthz/poststarthook/rbac/bootstrap-roles",
    "/healthz/poststarthook/scheduling/bootstrap-system-priority-classes",
    "/healthz/poststarthook/start-apiextensions-controllers",
    "/healthz/poststarthook/start-apiextensions-informers",
    "/healthz/poststarthook/start-kube-aggregator-informers",
    "/healthz/poststarthook/start-kube-apiserver-admission-initializer",
    "/logs",
    "/metrics",
    "/openapi/v2",
    "/swagger-2.0.0.json",
    "/swagger-2.0.0.pb-v1",
    "/swagger-2.0.0.pb-v1.gz",
    "/swagger.json",
    "/swaggerapi",
    "/version"
  ]
}
```

HTTPS证书认证：基于CA根证书签名的双向数字证书认证方式 
```
# cd /etc/kubernetes/pki/

创建私钥
# (umask 077; openssl genrsa -out curl.key 2048)
Generating RSA private key, 2048 bit long modulus
..............................+++
......+++
e is 65537 (0x10001)

建立证书签署请求
# openssl req -new -key curl.key -out curl.csr -subj "/O=curl/CN=www.api.com"

使用k8s的ca.key给之前的证书签证
# openssl x509 -req -in curl.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out curl.crt -days 365
Signature ok
subject=/O=curl/CN=www.api.com
Getting CA Private Key

不操作
# kubectl create secret generic curl-cert -n kube-system --from-file=curl.crt=./curl.crt --from-file=curl.key=./curl.key 
secret/curl-cert created


# curl -k --cert curl.csr --key curl.key https://192.168.101.66:6443/api
{
  "kind": "APIVersions",
  "versions": [
    "v1"
  ],
  "serverAddressByClientCIDRs": [
    {
      "clientCIDR": "0.0.0.0/0",
      "serverAddress": "192.168.101.66:6443"
    }
  ]
}
```

```
# curl -k --cert apiserver.crt --key apiserver.key https://192.168.101.66:6443/api
{
  "kind": "APIVersions",
  "versions": [
    "v1"
  ],
  "serverAddressByClientCIDRs": [
    {
      "clientCIDR": "0.0.0.0/0",
      "serverAddress": "192.168.101.66:6443"
    }
  ]
}
```
