secret使用方法
创建secret有三种模式
docker-registry  Create a secret for use with a Docker registry
generic               Create a secret from a local file, directory or literal value
tls                        Create a TLS secret

docker-registry  下载docker仓库镜像保存的密码文件
generic               连接数据库等需要保密的密码文件
tls                       https证书的文件

1、https证书的文件
# cat nginx.crt
-----BEGIN CERTIFICATE-----
MIIDkTCCAnmgAwIBAgIJALBCrUUTeoE+MA0GCSqGSIb3DQEBCwUAMF8xCzAJBgNV
BAYTAkNOMRAwDgYDVQQIDAdCZWlqaW5nMRAwDgYDVQQHDAdCZWlqaW5nMQ8wDQYD
VQQKDAZEZXZPcHMxGzAZBgNVBAMMEnd3dy5pa3ViZXJuZXRlcy5pbzAeFw0xODAz
MTgwMjA4MTNaFw0xODA0MTcwMjA4MTNaMF8xCzAJBgNVBAYTAkNOMRAwDgYDVQQI
DAdCZWlqaW5nMRAwDgYDVQQHDAdCZWlqaW5nMQ8wDQYDVQQKDAZEZXZPcHMxGzAZ
BgNVBAMMEnd3dy5pa3ViZXJuZXRlcy5pbzCCASIwDQYJKoZIhvcNAQEBBQADggEP
ADCCAQoCggEBALCAnyXQJi91ZuDMqevjSicsWEyfFVWjFTuh0eQU0iCmbdJX/ejy
Sf8hJRG9DHFZW5YmornT5QqT0Agd7xv/1Zn1vH110S38VDcDROwW3pIja3YmujvR
/q0EKMp1kYu8ac+sMG3/RkjPoplz9hlWb+wUjruaX+pkVYQVJMj1T91Sx09blWNC
gN9Fl9YBNUd+AJpp0u785V9Ql63gMbItGlTja4AZxlKbiY9ra3+D49WH0Jt9NNGd
fCtLujz7xd8B6acruKXL5jTvjBhfhTyRUhl+eI5YW2f3N9aioXZ2/tnShSsR8Rsv
oxUPmTETwdHMnl9aAQ4txeDSq6eUH0nSMy0CAwEAAaNQME4wHQYDVR0OBBYEFDoY
BFe4jCZdhXKW2ZxO/SdbAKyhMB8GA1UdIwQYMBaAFDoYBFe4jCZdhXKW2ZxO/Sdb
AKyhMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAK79vO0BBjPERkEg
SJ75Gfm2tdQyOCGA+b4iE2xnGMeeao7emxPV/BG9RwcrZ829PWKogRwm3QicPR/R
+HV3ay9ihOv7BjrNMAWjIEP0ToWvvugb4Rb4vsXH8+w3lU80ZG8a8bHhqosIXHyn
LWZIMM1/7n4KEDPcle1gSR5P+0pqQjkZmk30KcQDYi4eiYetLGqiwwerU2NfAvZI
fg8kxxiE+5IJq5gTNzISFtasBBRMufHHZ4tNqP/c8bg21RIcUfPNLbkyCgnpy7RT
pj94yVAnlOExZXj0ERquriWPCuanc3b8qgmWd6E2RqvPKS16uxT6j1JjyGHerwuP
YDppazo=
-----END CERTIFICATE-----


# cat nginx.key
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAsICfJdAmL3Vm4Myp6+NKJyxYTJ8VVaMVO6HR5BTSIKZt0lf9
6PJJ/yElEb0McVlbliaiudPlCpPQCB3vG//VmfW8fXXRLfxUNwNE7BbekiNrdia6
O9H+rQQoynWRi7xpz6wwbf9GSM+imXP2GVZv7BSOu5pf6mRVhBUkyPVP3VLHT1uV
Y0KA30WX1gE1R34AmmnS7vzlX1CXreAxsi0aVONrgBnGUpuJj2trf4Pj1YfQm300
0Z18K0u6PPvF3wHppyu4pcvmNO+MGF+FPJFSGX54jlhbZ/c31qKhdnb+2dKFKxHx
Gy+jFQ+ZMRPB0cyeX1oBDi3F4NKrp5QfSdIzLQIDAQABAoIBACFG3rp+V/SyqcbQ
T2kN3TktfyhTBe6zZJltlOjvk/5b4nC57kExDQpw8VA62FG2izHv7tYiQRiRbbNa
EW6x+U+hqPvubpXA8Q++Kgxo82WSD/yiqJIGsYFlO1uQdvRlfX2N9UOH0XSA0SMl
XczBIzDbX123aUYDzKuuYNUSixAq7qcO/ahby7FhqXrr72IIu9h+Z6ZLirwULCAo
i7l8MWo7kF9lrLrc8Hjeanmh/isaUKV7t/ghhBQjbffpk47ucuKi6bu6+H8LFOsu
57uxGVvYdRVxLkR23JSag7KzhljtCH42s8/NUMmMdO8+I3rfKujZF9nKHXV0SM8N
dxo/7XECgYEA6nCQuK5h6UxypBeSJUwGegTrL5t1mqnlTywfVbLWBfqahQO3ZVc6
j+P2keuoZDGcDjbzna+3v4osGXwmKUrD6oPpMGwJx9Q3Z6Aj196T9zzmgVkHn3Pn
GhFsAkcP1Q3SJZctZhGH7W+NNZLZ3NBd9LdZb1iPwNRFFud4AyJO9q8CgYEAwLwI
q/1c0fnPKdlWu339/hBZ6+j35bE3EWNoRMq3ZxghZeLGZ+6qFaTZeTF5teaKzRZ2
QB34tfcTJzCPGKHKw1zSEEBKcWBlhGRDkqCvwy5vq1aqvf28ZCRfTpsSxmu2wE7f
8WtCF8sxCZ9SniB0l8FHaZ8I3F3RKPG0Y5knauMCgYA+m70qdPeU9GORSvIun7UD
FRkx55Rqr4Cbui7MFixuAFUPvMRXfgoXr0uEAKlByLXiXe6FaA3sSxwn2i3ezSax
FHVMBy49fYEmXW/1EG33kv4EASC2Bp/rKEft+8hQn5ZFj7ACGCBy2l2dtxATllnh
Jq3tvHr3hjjFOx+jxp/L5QKBgFhhocRk4fy0BojVTo2aADBShTnGUm91LaB+qmDp
aOMQ0LftHzin3D0ipEuMIZkFiF71zvImDFg9Xf4ZqXUNNHMUDIxBPyHwp3znkYka
wJ7Lm4/BpXiMc6ikeUQNnrV4zYwwX0dQ/TT2C52y/ureTTkN+9Z2hFSxfOm+tQ77
O3UrAoGBAOQ2qnu5lLX3Imi0vEPwe3Suj9NQjzMtYROvV2Q+KioSO4ngV5igTVd1
L1lmbsqwhqpPya3PUBtddgRGrGIHE/rmjJAMgorqzXXgAl3dXl2Rv381u4G4LObd
+Btex44ahNKKuptR/ZJssAfSIBXNO0/wkkKTqkpYWGT+pyxUhRc5
-----END RSA PRIVATE KEY-----

#cat secret-volume-pod.yaml
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


2、下载docker仓库镜像保存的密码文件
# cat secret-imagepull-pod.yaml
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

3、连接数据库等需要保密的密码文件
1)创建secret
# kubectl create secret generic redis-root-password --from-literal=password=Myp@ss123

2)查看secret数据为空
# kubectl get secret redis-root-password

3)查看yaml格式的secret可以显示加密格式的密码
# kubectl get secret redis-root-password -o yaml
apiVersion: v1
data:
  password: TXlQQHNzMTIz

4)把加密格式的密码通过base64编码转换正常密码
# echo TXlQQHNzMTIz |base64 -d
MyP@ss123

5)创建一个secret文件
# cat secret-demo.yaml
apiVersion: v1
kind: Secret
metadata:
  name: secret-demo
stringData:
  username: redis
  password: redispass
type: Opaque
