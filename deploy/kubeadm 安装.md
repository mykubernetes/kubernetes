kubeadm 安装
============
一、准备环境  
1、关闭防火墙：  
```
$ systemctl stop firewalld
$ systemctl disable firewalld
```  
2、关闭selinux：  
```
$ sed -i 's/enforcing/disabled/' /etc/selinux/config
$ setenforce 0
```  
3、关闭swap：  
```
$ swapoff -a $ 临时
$ vim /etc/fstab $ 永久
```  
4、添加主机名与IP对应关系（记得设置主机名）：  
```
$ cat /etc/hosts
192.168.0.11 k8s-master
192.168.0.12 k8s-node1
192.168.0.13 k8s-node2
```  
5、将桥接的IPv4流量传递到iptables的链：  
```
$ cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

$ sysctl --system
```  


二、所有节点安装Docker/kubeadm/kubelet  
Kubernetes默认CRI（容器运行时）为Docker，因此先安装Docker。  
1、安装Docker  
```
$ wget -O /etc/yum.repos.d/docker-ce.repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo 
$ yum -y install docker-ce-18.06.1.ce-3.el7
$ systemctl enable docker && systemctl start docker
$ docker --version
Docker version 18.06.1-ce, build e68fc7a2
```  

2、添加阿里云YUM软件源  
```
$ cat > /etc/yum.repos.d/kubernetes.repo << EOF
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg
https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
```  

3、安装kubeadm，kubelet和kubectl  
由于版本更新频繁，这里指定版本号部署：  
```
$ yum install -y kubelet-1.13.3 kubeadm-1.13.3 kubectl-1.13.3
$ systemctl enable kubelet
```  

4、部署Kubernetes Master  
```
$ kubeadm init \
--kubernetes-version=v1.13.3 \
--pod-network-cidr=10.244.0.0/16 \
--service-cidr=10.96.0.0/12 \
--ignore-preflight-errors=Swap
```  

5、使用kubectl工具：  
```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
$ kubectl get nodes
```  

6、安装Pod网络插件（CNI）  
```
$ kubectl apply -f
https://raw.githubusercontent.com/coreos/flannel/a70459be0084506e4ec919aa1c114638878db11b/Documentation/kube-flannel.yml
```  

7、加入Kubernetes Node  
向集群添加新节点，执行在kubeadm init输出的kubeadm join命令：  
```
$ kubeadm join 192.168.31.64:6443 --token l79g5t.6ov4jkddwqki1dxe --discovery-token-ca-cert-hash sha256:4f07f9068c543130461c9db368d62b4aabc22105451057f887defa35f47fa076
```  

8、部署Dashboard  
``` $ kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v1.10.1/src/deploy/recommended/kubernetes-dashboard.yaml ```  

默认Dashboard只能集群内部访问，修改Service为NodePort类型，暴露到外部：  
```
kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  type: NodePort
  ports:
  - port: 443
    targetPort: 8443
    nodePort: 30001
  selector:
    k8s-app: kubernetes-dashboard
```  

```
$ kubectl apply -f kubernetes-dashboard.yaml
```  

访问地址：http://NodeIP:30001  

创建service account并绑定默认cluster-admin管理员集群角色：  
```
$ kubectl create serviceaccount dashboard-admin -n kube-system
$ kubectl create clusterrolebinding dashboard-admin --clusterrole=cluster-admin --serviceaccount=kube-system:dashboard-admin
$ kubectl describe secrets -n kube-system $(kubectl -n kube-system get secret | awk '/dashboard-admin/{print $1}')
```

