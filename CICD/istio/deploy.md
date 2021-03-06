安装
---
```
wget https://github.com/istio/istio/releases/download/1.4.2/istio-1.4.2-linux.tar.gz
tar istio-1.4.2-linux.tar.gz
cd istio-1.4.2
cp /bin/istioctl /usr/bin/
istiotl manifst apply --set profile=demo
kubectl get pods -n istio-system
kubectl get svc -n istio-system
```

卸载
---
```
istioctl manifest generate --set profile=demo | kubectl delete -f -
```

部署httpbin Web示例：
---
```
cd istio-1.4.2/samples/httpbin
```

手动注入
```
kubectl apply -f <(istioctl kube-inject -f httpbin-nodeport.yaml)
或者
istioctl kube-inject -f httpbin-nodeport.yaml |kubectl apply -f -
```

自动注入
```
kubectl label namespace default istio-injection=enabled

kubectl apply -f httpbin-gateway.yaml
```

NodePort访问地址
http://IP:31928
