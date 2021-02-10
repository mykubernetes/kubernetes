查看公钥证书
```
#自建CA，生成ca.key与ca.crt
openssl x509 -in ca.crt -noout -text

#apiserver的私钥与公钥证书
openssl x509 -in apiserver.crt -noout -text
```
