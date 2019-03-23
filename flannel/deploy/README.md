deploy_flannel
============
1、vxlan模式：  
``` # kubectl apply -f fannel_vxlan.yaml ```  

2、vxlan+直接路由模式：  
``` # kubectl apply -f flannel_vxlan_route.yaml ```  

3、host-gw模式：  
``` # kubectl apply -f flannel_host-gw.yaml ``` 
