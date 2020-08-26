apiserver有三种级别的客户端认证方式
1、HTTPS证书认证：基于CA根证书签名的双向数字证书认证方式
2、HTTP Token认证：通过一个Token来识别合法用户
3、HTTP Base认证：通过用户名+密码的认证方式

HTTP Token认证：通过一个Token来识别合法用户
```
1、获取TOKEN信息
# kubectl describe secrets $(kubectl get secrets -n kube-system |grep admin |cut -f1 -d ' ') -n kube-system |grep -E '^token' |cut -f2 -d':'|tr -d '	'|tr -d ' '

2、定义TOKEN环境变量
# TOKEN=$(kubectl describe secrets $(kubectl get secrets -n kube-system |grep admin |cut -f1 -d ' ') -n kube-system |grep -E '^token' |cut -f2 -d':'|tr -d '	'|tr -d ' ')

3、获取api-server地址
# kubectl config view |grep server|cut -f 2- -d ":" | tr -d " "

4、设置api-server地址环境变量
# APISERVER=$(kubectl config view |grep server|cut -f 2- -d ":" | tr -d " ")
```

通过TOKEN方式访问api-server
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
