安装
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
```
istioctl manifest generate --set profile=demo | kubectl delete -f -
```
