安装dashboard
=============
1、部署dashboard  
``` kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/recommended/kubernetes-dashboard.yaml ```  

2、下载镜像  
```
images=(
	kubernetes-dashboard-amd64:v1.10.0
)

for imageName in ${images[@]} ; do
    docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/$imageName
    docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/$imageName k8s.gcr.io/$imageName
done
```  


3、token认证  
1）创建dashboard用户  
``` kubectl create serviceaccount dashboard-admin -n kube-system ```  
2）
``` kubectl create clusterrolebinding dashboard-cluster-admin --clusterrole=cluster-admin --serviceaccount=kube-system:dashboard-admin ```  
3）
``` kubectl get secret -n kube-system ```  
4）
``` kubectl describe secret dashboard-admin-token-8wz6w -n kube-system ```  
5）第四部可现实token信息  
``` token:      eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJkYXNoYm9hcmQtYWRtaW4tdG9rZW4tOHd6NnciLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGFzaGJvYXJkLWFkbWluIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiNzA0MzJmZjEtZTVkNS0xMWU4LThmMDEtMDAwYzI5OGU0ODNkIiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50Omt1YmUtc3lzdGVtOmRhc2hib2FyZC1hZG1pbiJ9.BU8Hmp4_EMovOG4QZLVm0dGA9k4U3IG1mTPbhKraN0nECe8YZXaHFzrHsJwGIcK3hfwa01UtTIuB56_ElwXTyiE4K8n0o6loABJvtZOgrOnNAmcr3vrIKe4UDiflokdKjk5OjInvVWy4Q6dXVdR-9i-1C3KWEavscnwAl7bsipxufLbgfcCERjQABJ1KXDNvq6Io9tOdbXbSuXg6-GkaRg0enTLBslIV73CRWNwz71kF0QXOK7BTUw_D3wBMRJ7txSjV9aYfBW7Ll0Xxpsvd3WHnOBmN4PhaMKEWjrj-8V3N-yChtFnymul2IUcooYa70dANGASsL7eyXzMdRg_zlg ```  





4、证书认证  
1、  
``` kubectl create serviceaccount def-ns-admin -n default ```
2、  
``` kubectl create rolebinding def-ns-admin --clusterrole=admin --serviceaccount=default:def-ns-admin ```
     1、kubectl get secret  
     2、kubectl describe secret def-ns-admin-token-ptg7w  
     3、复制token到web 只能管理default权限  
3、  
``` kubectl config set-cluster kubernetes --certificate-authority=/etc/kubernetes/pki/ca.crt --server="https://192.168.101.66:6443" --embed-certs=true --kubeconfig=/root/def-ns-admin.conf ```
4、查看权限  
``` kubectl config view --kubeconfig=/root/def-ns-admin.conf ```  
5、复制token内容 两种方法  
```
kubectl get secret def-ns-admin-token-ptg7w -o json  
kubectl get secret def-ns-admin-token-ptg7w -o jsonpath={.data.token} | base64 -d
```  
6、 将复制的内容解码  
``` echo ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklpSjkuZXlKcGMzTWlPaUpyZFdKbGNtNWxkR1Z6TDNObGNuWnBZMlZoWTJOdmRXNTBJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5dVlXMWxjM0JoWTJVaU9pSmtaV1poZFd4MElpd2lhM1ZpWlhKdVpYUmxjeTVwYnk5elpYSjJhV05sWVdOamIzVnVkQzl6WldOeVpYUXVibUZ0WlNJNkltUmxaaTF1Y3kxaFpHMXBiaTEwYjJ0bGJpMXdkR2MzZHlJc0ltdDFZbVZ5Ym1WMFpYTXVhVzh2YzJWeWRtbGpaV0ZqWTI5MWJuUXZjMlZ5ZG1salpTMWhZMk52ZFc1MExtNWhiV1VpT2lKa1pXWXRibk10WVdSdGFXNGlMQ0pyZFdKbGNtNWxkR1Z6TG1sdkwzTmxjblpwWTJWaFkyTnZkVzUwTDNObGNuWnBZMlV0WVdOamIzVnVkQzUxYVdRaU9pSm1NV1UwTURKa1l5MWxOV1EzTFRFeFpUZ3RPR1l3TVMwd01EQmpNams0WlRRNE0yUWlMQ0p6ZFdJaU9pSnplWE4wWlcwNmMyVnlkbWxqWldGalkyOTFiblE2WkdWbVlYVnNkRHBrWldZdGJuTXRZV1J0YVc0aWZRLlNWdFdQUkt6N1FWTFZNNWtRS3pvWlFPMFowUWVqWVBoanlyc3dVM01OdzJjSlV2ZmtmSDdvLVVmSmNHbGk0WVJHdGZ2UFBnc0R6X3Uwc0FsZy1reENFQ3RFSHpoWi1sVXZZYWUxY1lxWUhhdDlMcF94N1llamhQZG9wM2k0dW5oa1JqUXpGQ2JfVVd1dzNrTGlYeXYzOVEyaWRuT2pnZmF1OEVRTjRKNURoOEJQalRxejQxeWw2WnNFSjN6c2FhcU5OVXphX0ZzMGZaLTdqa3Q0emNUeFNQei1wSWhGQjY1dmZMaTFvZS0yZXR6aWRTeHplMm1VcUxhNWtHcHdzRHFzUW9Sc3dIRXI4OEp5amc2U19janRKWlJHNXVqNjg2bjhXcGtRcHU2a1hUOWg0b19EclBSM09felVjSVBYem0tU3Q4VzVVelNlRGt3Z19CUzFqVUlpZw== | base64 -d ```  
7、变量为 上边复制的内容  
``` kubectl config set-credentials def-ns-admin --token=$DER_NS_ADMIN_TOKEN --kubeconfig=/root/def-ns-admin.conf ```  
8、 
``` kubectl config set-context def-ns-admin@kubernetes --cluster=kubernetes --user=def-ns-admin --kubeconfig=/root/def-ns-admin.conf ```  
9、切换用户  
``` kubectl config view --kubeconfig=/root/def-ns-admin.conf ```  
10、查看权限  
``` kubectl config view --kubeconfig=/root/def-ns-admin.conf ```  
11、拷贝到桌面  
``` sz /root/def-ns-admin.conf ```  
12、在浏览器里添加证书  
