查看公钥证书
```
#自建CA，生成ca.key与ca.crt
openssl x509 -in ca.crt -noout -text

#apiserver的私钥与公钥证书
openssl x509 -in apiserver.crt -noout -text
```

Kubernetes 监控工具 Weave Scope  
参考官方文档:https://www.weave.works/docs/scope/latest/installing/#k8s
```
kubectl apply --namespace weave -f "https://cloud.weave.works/k8s/scope.yaml?k8s-version=$(kubectl version | base64 | tr -d '\n')"
kubectl patch svc $(kubectl get svc -n weave |grep weave-scope-app |awk '{print $1}') -p '{"spec":{"type": "NodePort"}}' -n weave
```
