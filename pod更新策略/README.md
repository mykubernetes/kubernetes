pod更新策略  
- web-recreate.yaml 为重建，会同时停止所有pod后再次创建，会短暂终止业务
- web-rollingupdate.yaml 滚动更新，根据控制器不同更新方式不同，会先停止一个服务再启动一个服务，根据更新策略而定



```
暂停更新
kubectl rollout pause deploy web-rollingupdate -n dev
恢复更新
kubectl rollout resume deploy web-rollingupdate -n dev
回滚到上一个版本
kubectl rollout undo deploy web-rollingupdate -n dev
查看历史版本
kubectl rollout history deploy web-rollingupdate -n dev
查看当前状态
kubectl rollout status deploy web-rollingupdate -n dev
```  
