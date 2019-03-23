官方githu托管地址  
https://github.com/coreos/flannel  
```
flannel支持三种方式  
	vxlan:隧道方式，速到快，同时可以添加直接路由，同一网段使用直接路由方式，不同网段降级到vxlan方式。推荐  
	host-gw:直连路由，可通过查看路由表的方式快速找到对端主机，只能在同一网段通信，跨网段无法通行，速到最快。  
	udp:udp协议传输，速到最慢，不推荐使用。
                #直连路由，只能在同一路由内，不能跨路由通信  
网络传输方式  
pod"network"-->cni0-->flannel.1-->eno167777736到对端主机  
```  
1、安装下载官方提供kube-flannel.yml并修改configmap字段  
``` wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml ```  

vxlan方式，默认不用修改  
```
kind: ConfigMap
apiVersion: v1
metadata:
  name: kube-flannel-cfg
  namespace: kube-system
  labels:
    tier: node
    app: flannel
data:
  cni-conf.json: |
    {
      "name": "cbr0",
      "plugins": [
        {
          "type": "flannel",
          "delegate": {
            "hairpinMode": true,
            "isDefaultGateway": true
          }
        },
        {
          "type": "portmap",
          "capabilities": {
            "portMappings": true
          }
        }
      ]
    }
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "Backend": {
        "Type": "vxlan"
      }
    }
```  

vxlan+直接路由方式，修改configmap字段  
```
kind: ConfigMap
apiVersion: v1
metadata:
  name: kube-flannel-cfg
  namespace: kube-system
  labels:
    tier: node
    app: flannel
data:
  cni-conf.json: |
    {
      "name": "cbr0",
      "plugins": [
        {
          "type": "flannel",
          "delegate": {
            "hairpinMode": true,
            "isDefaultGateway": true
          }
        },
        {
          "type": "portmap",
          "capabilities": {
            "portMappings": true
          }
        }
      ]
    }
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "Backend": {
        "Type": "vxlan",
        "Directrouting": true
      }
    }
```

host-gw方式传输
```
kind: ConfigMap
apiVersion: v1
metadata:
  name: kube-flannel-cfg
  namespace: kube-system
  labels:
    tier: node
    app: flannel
data:
  cni-conf.json: |
    {
      "name": "cbr0",
      "plugins": [
        {
          "type": "flannel",
          "delegate": {
            "hairpinMode": true,
            "isDefaultGateway": true
          }
        },
        {
          "type": "portmap",
          "capabilities": {
            "portMappings": true
          }
        }
      ]
    }
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "Backend": {
        "Type": "host-gw"
      }
    }
```  
