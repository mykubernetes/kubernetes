# 一、概述

etcd 是一个响应快、分布式、一致的 key-value 存储

# 二、操作

## 2.1、进入etcd容器
```
# 1、获取etcd pod
# kubectl get pods -n kube-system
NAME                                              READY   STATUS        RESTARTS   AGE
etcd-apiserver.cluster.local                      1/1     Running       9          40d

# 2、exec进入etcd内
# kubectl exec -n kube-system etcd-apiserver.cluster.local -it -- /bin/sh

# 3、容器内etcd的目录结构
# find / -name 'etcd' -print
/etc/kubernetes/pki/etcd   # 证书目录
/usr/local/bin/etcd        # 二进制程序
/var/lib/etcd              # 数据目录
```

## 2.2、etcdctl

etcd3 API
- 从kubernetes 1.6开始，etcd集群使用version 3

```
# 1、下载etcdctl, 以在etcd容器外访问etcd接口
# https://github.com/etcd-io/etcd/releases
# cp etcdctl /usr/local/bin/

# 2、设置API版本为3
# 必须先指定API的版本才能使用 --cert等参数指定证书, api2的参数与3不一致。
# export ETCDCTL_API=3

# 3、指定证书获取 endpoint的状态
# etcdctl --endpoints=https://localhost:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key  endpoint health
https://localhost:2379 is healthy: successfully committed proposal: took = 2.706905334s

# 4、可以声明 etcdctl的环境变量
# vim /etc/profile
# etcd
export ETCDCTL_API=3
export ETCDCTL_DIAL_TIMEOUT=3s;
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt;
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt;
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key;
export ETCD_ENDPOINTS=https://localhost:2379

# source /etc/profile

# 5、可以不用指定证书了
# etcdctl endpoint health
127.0.0.1:2379 is healthy: successfully committed proposal: took = 827.031484ms
```


### 2.2.1 etcdctl 操作

#### 1、读取数据key
```
# 1、使用以下命令列出所有的key
ETCDCTL_API=3 etcdctl --endpoints=<etcd-ip-1>:2379,<etcd-ip-2>:2379,<etcd-ip-3>:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt  --key=/etc/kubernetes/pki/apiserver-etcd-client.key  --cert=/etc/kubernetes/pki/apiserver-etcd-client.crt get / --prefix --keys-only

# 2、可以使用alias来重命名etcdctl一串的命令
alias ectl='ETCDCTL_API=3 etcdctl --endpoints=<etcd-ip-1>:2379,<etcd-ip-2>:2379,<etcd-ip-3>:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt  --key=/etc/kubernetes/pki/apiserver-etcd-client.key  --cert=/etc/kubernetes/pki/apiserver-etcd-client.crt'
```

#### 2. 集群数据

##### node
```
/registry/minions/<node-ip-1>
/registry/minions/<node-ip-2>
/registry/minions/<node-ip-3>
```

其他信息：
```
/registry/leases/kube-node-lease/<node-ip-1>
/registry/leases/kube-node-lease/<node-ip-2>
/registry/leases/kube-node-lease/<node-ip-3>

/registry/masterleases/<node-ip-2>
/registry/masterleases/<node-ip-3>
```

##### 3. k8s对象数据

k8s对象数据的格式
3.1. namespace
```
/registry/namespaces/default
/registry/namespaces/game
/registry/namespaces/kube-node-lease
/registry/namespaces/kube-public
/registry/namespaces/kube-system
```

##### 3.2. namespace级别对象
```
/registry/{resource}/{namespace}/{resource_name}
```

以下以常见k8s对象为例：
```
# deployment
/registry/deployments/default/game-2048
/registry/deployments/kube-system/prometheus-operator

# replicasets
/registry/replicasets/default/game-2048-c7d589ccf

# pod
/registry/pods/default/game-2048-c7d589ccf-8lsbw

# statefulsets
/registry/statefulsets/kube-system/prometheus-k8s

# daemonsets
/registry/daemonsets/kube-system/kube-proxy

# secrets
/registry/secrets/default/default-token-tbfmb

# serviceaccounts
/registry/serviceaccounts/default/default

service

# service
/registry/services/specs/default/game-2048

# endpoints
/registry/services/endpoints/default/game-2048
```

service
```
# service
/registry/services/specs/default/game-2048

# endpoints
/registry/services/endpoints/default/game-2048
```


# 三、Kubernetes资源

## 3.1、etcdctl ls脚本

v3版本的数据存储没有目录层级关系了，而是采用平展（flat)模式，换句话说/a与/a/b并没有嵌套关系，而只是key的名称差别而已，这个和AWS S3以及OpenStack Swift对象存储一样，没有目录的概念，但是key名称支持/字符，从而实现看起来像目录的伪目录，但是存储结构上不存在层级关系。

### 读取数据value

#### 1、由于k8s默认etcd中的数据是通过protobuf格式存储，因此看到的key和value的值是一串字符串。
```
# ectl get /registry/namespaces/test -w json |jq
{
  "header": {
    "cluster_id": 12113422651334595000,
    "member_id": 8381627376898157000,
    "revision": 12321629,
    "raft_term": 20
  },
  "kvs": [
    {
      "key": "L3JlZ2lzdHJ5L25hbWVzcGFjZXMvdGVzdA==",
      "create_revision": 11670741,
      "mod_revision": 11670741,
      "version": 1,
      "value": "azhzAAoPCgJ2MRIJTmFtZXNwYWNlElwKQgoEdGVzdBIAGgAiACokYWM1YmJjOTQtNTkxZi0xMWVhLWJiOTQtNmM5MmJmM2I3NmI1MgA4AEIICJuf3fIFEAB6ABIMCgprdWJlcm5ldGVzGggKBkFjdGl2ZRoAIgA="
    }
  ],
  "count": 1
}
```

#### 2、其中key可以通过base64解码出来
```
echo "L3JlZ2lzdHJ5L25hbWVzcGFjZXMvdGVzdA==" | base64 --decode

# output
/registry/namespaces/test
```

#### 3、value是值可以通过安装etcdhelper工具解析出来
```
# ehelper get /registry/namespaces/test
/v1, Kind=Namespace
{
  "kind": "Namespace",
  "apiVersion": "v1",
  "metadata": {
    "name": "test",
    "uid": "ac5bbc94-591f-11ea-bb94-6c92bf3b76b5",
    "creationTimestamp": "2020-02-27T05:11:55Z"
  },
  "spec": {
    "finalizers": [
      "kubernetes"
    ]
  },
  "status": {
    "phase": "Active"
  }
}
```


也就是说etcdctl无法使用类似v2的ls命令。但是我还是习惯使用v2版本的etcdctl ls查看etcdctl存储的内容
```
# vim etcd_ls.sh
#!/bin/bash
PREFIX=${1:-/}
ORIG_PREFIX=${PREFIX}

LAST_CHAR=${PREFIX:${#PREFIX}-1:1}
if [[ $LAST_CHAR != '/' ]];
then
    # Append  '/' at the end if not exist
    PREFIX="$PREFIX/"
fi

for ITEM in $(etcdctl get "$PREFIX" --prefix=true --keys-only | grep "$PREFIX");
do
    PREFIX_LEN=${#PREFIX}
    CONTENT=${ITEM:$PREFIX_LEN}
    POS=$(expr index "$CONTENT" '/')

    if [[ $POS -le 0 ]];
    then
        # No '/', it's not dir, get whole str
        POS=${#CONTENT}
    fi

    CONTENT=${CONTENT:0:$POS}
    LAST_CHAR=${CONTENT:${#CONTENT}-1:1}

    if [[ $LAST_CHAR == '/' ]];
    then
        CONTENT=${CONTENT:0:-1}
    fi

    echo ${PREFIX}${CONTENT}

done | sort | uniq
```

其他脚本
```
#!/bin/bash
KEY_FILE=/etc/kubernetes/pki/etcd/server.key
CERT_FILE=/etc/kubernetes/pki/etcd/server.crt
CA_FILE=/etc/kubernetes/pki/etcd/ca.crt
ENDPOINTS=https://127.0.0.1:2379
PREFIX=${1:-/}
ORIG_PREFIX="$PREFIX"

LAST_CHAR=${PREFIX:${#PREFIX}-1:1}
if [[ $LAST_CHAR != '/' ]]; then
    PREFIX="$PREFIX/" # Append  '/' at the end if not exist
fi

for ITEM in $(etcdctl --key="$KEY_FILE" \
                      --cert="$CERT_FILE" \
                      --cacert="$CA_FILE" \
                      --endpoints "$ENDPOINTS" \
                      get "$PREFIX" --prefix=true --keys-only | grep "$PREFIX"); do
    PREFIX_LEN=${#PREFIX}
    CONTENT=${ITEM:$PREFIX_LEN}
    POS=$(expr index "$CONTENT" '/')
    if [[ $POS -le 0 ]]; then
	    POS=${#CONTENT} # No '/', it's not dir, get whole str
    fi
    CONTENT=${CONTENT:0:$POS}
    LAST_CHAR=${CONTENT:${#CONTENT}-1:1}
    if [[ $LAST_CHAR == '/' ]]; then
        CONTENT=${CONTENT:0:-1}
    fi
    echo "${PREFIX}${CONTENT}"
done | sort | uniq

etcdctl --key="$KEY_FILE" \
        --cert="$CERT_FILE"  \
        --cacert="$CA_FILE" \
        --endpoints "$ENDPOINTS" get "$ORIG_PREFIX"
```

## 3.2、获取所有key
- 由于Kubernetes的所有数据都以/registry为前缀，因此首先查看/registry

```
./etcd_ls.sh /registry
/registry/apiregistration.k8s.io
/registry/clusterrolebindings
/registry/clusterroles
/registry/configmaps
/registry/controllerrevisions
/registry/daemonsets
/registry/deployments
/registry/events
/registry/leases
/registry/masterleases
/registry/minions
/registry/namespaces
/registry/persistentvolumeclaims
/registry/persistentvolumes
/registry/pods
/registry/podsecuritypolicy
/registry/priorityclasses
/registry/ranges
/registry/replicasets
/registry/rolebindings
/registry/roles
/registry/secrets
/registry/serviceaccounts
/registry/services
/registry/statefulsets
/registry/storageclasses
```

## 3.3、获取key值
```
./etcd_ls.sh /registry/ranges/servicenodeports |strings
/registry/ranges/servicenodeports
RangeAllocation
30000-32767

./etcd_ls.sh /registry/ranges/serviceips | strings
/registry/ranges/serviceips
RangeAllocation
10.96.0.0/16
```
- 如上为什么需要使用strings命令，那是因为除了/registry/apiregistration.k8s.io是直接存储JSON格式的，其他资源默认都不是使用JSON格式直接存储，而是通过protobuf格式存储，当然这么做的原因是为了性能，除非手动配置–storage-media-type=application/json

# 四、etcdhelper

- 使用proto提高了性能，但也导致有时排查问题时不方便直接使用etcdctl读取内容，可幸的是openshift项目已经开发了一个强大的辅助工具 etcdhelper 可以读取etcd内容并解码proto。

## 4.1、编译etcdhelper
```
# 源代码url
# https://github.com/openshift/origin/blob/master/tools/etcdhelper/etcdhelper.go

# 编译
# 使用gomod编译etcdhelper
#  go mod init etcdhelper
go: creating new go.mod: module etcdhelper

# go test
# cat go.mod
module etcdhelper

go 1.14

require (
    github.com/coreos/etcd v3.3.22+incompatible // indirect
    github.com/coreos/pkg v0.0.0-20180928190104-399ea9e2e55f // indirect
    github.com/openshift/api v0.0.0-20200714125145-93040c6967eb
    go.etcd.io/etcd v3.3.22+incompatible
    go.uber.org/zap v1.15.0 // indirect
    k8s.io/apimachinery v0.18.6
    k8s.io/kubectl v0.18.6
)

# 正常情况下，go test之后就可以进行编译了，报错了需要先解决错误。
# go build etcdhelper.go
go: finding module for package github.com/coreos/go-systemd/journal
/root/go/pkg/mod/github.com/coreos/etcd@v3.3.22+incompatible/pkg/logutil/zap_journal.go:29:2: no matching versions for query "latest"

# 这个问题主要看这个 [issues](https://github.com/etcd-io/etcd/issues/11345)
# 先将 go-systemd 下载到本地
# mkdir -p $GOPATH/src/github.com/coreos/go-systemd/
# git clone https://github.com/coreos/go-systemd.git $GOPATH/src/github.com/coreos/go-systemd/
# cd $myproject

# 修改 go.mod，将依赖改为本地包
# vim go.mod
replace (
  github.com/coreos/go-systemd => github.com/coreos/go-systemd/v22 latest
)

# 再执行go test
# go test

# 执行编译，并生成可执行文件etcdhelper
# go build etcdhelper.go
# ll
total 46668
-rwxr-xr-x. 1 root root 47737965 Jul 20 15:59 etcdhelper
-rw-r--r--. 1 root root     4988 Jul 16 17:00 etcdhelper.go
-rwxr--r--. 1 root root      706 Jul 16 16:45 etcd_ls.sh
-rw-r--r--. 1 root root      515 Jul 20 15:54 go.mod
-rw-r--r--. 1 root root    32493 Jul 20 15:54 go.sum
```

## 4.2、使用etcdhelper
```
# 将etcdhelper 加入PATH
# mv etcdhelper $HOME/go/bin

# Usage
# ./etcdhelper  -h
Usage of ./etcdhelper:
  -cacert string
        Server TLS CA certificate.
  -cert string
        TLS client certificate.
  -endpoint string
        etcd endpoint. (default "https://127.0.0.1:2379")
  -key string
        TLS client key.

# 设置别名
# alias etcdhelper='etcdhelper -cacert /etc/kubernetes/pki/etcd/ca.crt \
                              -key /etc/kubernetes/pki/etcd/server.key \
                              -cert /etc/kubernetes/pki/etcd/server.crt'
```

获取key值，现在可以看到存储在etcd中JSON格式的数据了
```
# etcdhelper get /registry/namespaces/default && echo
/v1, Kind=Namespace
{
  "kind": "Namespace",
  "apiVersion": "v1",
  "metadata": {
    "name": "default",
    "uid": "6ee8cecc-37f3-4df5-a415-27d1e5023266",
    "creationTimestamp": "2019-11-28T09:00:35Z"
  },
  "spec": {
    "finalizers": [
      "kubernetes"
    ]
  },
  "status": {
    "phase": "Active"
  }
}
```

etcd的secret默认仅仅使用了base64编码而并没有加密
```
etcdhelper get /registry/secrets/kube-system/istio.kube-proxy \
>   | sed -n '2,$p' \
>   | jq '.data."key.pem"' \
>   | tr -d '"' |base64 -d
```





# RBAC 相关key

clusterrolebindings
```
/registry/clusterrolebindings/cluster-admin
/registry/clusterrolebindings/flannel
/registry/clusterrolebindings/galaxy
/registry/clusterrolebindings/helm
/registry/clusterrolebindings/kube-state-metrics
/registry/clusterrolebindings/kubeadm:kubelet-bootstrap
/registry/clusterrolebindings/kubeadm:node-autoapprove-bootstrap
/registry/clusterrolebindings/kubeadm:node-autoapprove-certificate-rotation
/registry/clusterrolebindings/kubeadm:node-proxier
/registry/clusterrolebindings/lbcf-controller
/registry/clusterrolebindings/prometheus-k8s
/registry/clusterrolebindings/prometheus-operator
/registry/clusterrolebindings/system:aws-cloud-provider
/registry/clusterrolebindings/system:basic-user
/registry/clusterrolebindings/system:controller:attachdetach-controller
/registry/clusterrolebindings/system:controller:certificate-controller
/registry/clusterrolebindings/system:controller:clusterrole-aggregation-controller
/registry/clusterrolebindings/system:controller:cronjob-controller
/registry/clusterrolebindings/system:controller:daemon-set-controller
/registry/clusterrolebindings/system:controller:deployment-controller
/registry/clusterrolebindings/system:controller:disruption-controller
/registry/clusterrolebindings/system:controller:endpoint-controller
/registry/clusterrolebindings/system:controller:expand-controller
/registry/clusterrolebindings/system:controller:generic-garbage-collector
/registry/clusterrolebindings/system:controller:horizontal-pod-autoscaler
/registry/clusterrolebindings/system:controller:job-controller
/registry/clusterrolebindings/system:controller:namespace-controller
/registry/clusterrolebindings/system:controller:node-controller
/registry/clusterrolebindings/system:controller:persistent-volume-binder
/registry/clusterrolebindings/system:controller:pod-garbage-collector
/registry/clusterrolebindings/system:controller:pv-protection-controller
/registry/clusterrolebindings/system:controller:pvc-protection-controller
/registry/clusterrolebindings/system:controller:replicaset-controller
/registry/clusterrolebindings/system:controller:replication-controller
/registry/clusterrolebindings/system:controller:resourcequota-controller
/registry/clusterrolebindings/system:controller:route-controller
/registry/clusterrolebindings/system:controller:service-account-controller
/registry/clusterrolebindings/system:controller:service-controller
/registry/clusterrolebindings/system:controller:statefulset-controller
/registry/clusterrolebindings/system:controller:ttl-controller
/registry/clusterrolebindings/system:coredns
/registry/clusterrolebindings/system:discovery
/registry/clusterrolebindings/system:kube-controller-manager
/registry/clusterrolebindings/system:kube-dns
/registry/clusterrolebindings/system:kube-scheduler
/registry/clusterrolebindings/system:node
/registry/clusterrolebindings/system:node-proxier
/registry/clusterrolebindings/system:public-info-viewer
/registry/clusterrolebindings/system:volume-scheduler
```

clusterroles
```
/registry/clusterroles/admin
/registry/clusterroles/cluster-admin
/registry/clusterroles/edit
/registry/clusterroles/flannel
/registry/clusterroles/kube-state-metrics
/registry/clusterroles/lbcf-controller
/registry/clusterroles/prometheus-k8s
/registry/clusterroles/prometheus-operator
/registry/clusterroles/system:aggregate-to-admin
/registry/clusterroles/system:aggregate-to-edit
/registry/clusterroles/system:aggregate-to-view
/registry/clusterroles/system:auth-delegator
/registry/clusterroles/system:aws-cloud-provider
/registry/clusterroles/system:basic-user
/registry/clusterroles/system:certificates.k8s.io:certificatesigningrequests:nodeclient
/registry/clusterroles/system:certificates.k8s.io:certificatesigningrequests:selfnodeclient
/registry/clusterroles/system:controller:attachdetach-controller
/registry/clusterroles/system:controller:certificate-controller
/registry/clusterroles/system:controller:clusterrole-aggregation-controller
/registry/clusterroles/system:controller:cronjob-controller
/registry/clusterroles/system:controller:daemon-set-controller
/registry/clusterroles/system:controller:deployment-controller
/registry/clusterroles/system:controller:disruption-controller
/registry/clusterroles/system:controller:endpoint-controller
/registry/clusterroles/system:controller:expand-controller
/registry/clusterroles/system:controller:generic-garbage-collector
/registry/clusterroles/system:controller:horizontal-pod-autoscaler
/registry/clusterroles/system:controller:job-controller
/registry/clusterroles/system:controller:namespace-controller
/registry/clusterroles/system:controller:node-controller
/registry/clusterroles/system:controller:persistent-volume-binder
/registry/clusterroles/system:controller:pod-garbage-collector
/registry/clusterroles/system:controller:pv-protection-controller
/registry/clusterroles/system:controller:pvc-protection-controller
/registry/clusterroles/system:controller:replicaset-controller
/registry/clusterroles/system:controller:replication-controller
/registry/clusterroles/system:controller:resourcequota-controller
/registry/clusterroles/system:controller:route-controller
/registry/clusterroles/system:controller:service-account-controller
/registry/clusterroles/system:controller:service-controller
/registry/clusterroles/system:controller:statefulset-controller
/registry/clusterroles/system:controller:ttl-controller
/registry/clusterroles/system:coredns
/registry/clusterroles/system:csi-external-attacher
/registry/clusterroles/system:csi-external-provisioner
/registry/clusterroles/system:discovery
/registry/clusterroles/system:heapster
/registry/clusterroles/system:kube-aggregator
/registry/clusterroles/system:kube-controller-manager
/registry/clusterroles/system:kube-dns
/registry/clusterroles/system:kube-scheduler
/registry/clusterroles/system:kubelet-api-admin
/registry/clusterroles/system:node
/registry/clusterroles/system:node-bootstrapper
/registry/clusterroles/system:node-problem-detector
/registry/clusterroles/system:node-proxier
/registry/clusterroles/system:persistent-volume-provisioner
/registry/clusterroles/system:public-info-viewer
/registry/clusterroles/system:volume-scheduler
/registry/clusterroles/view
```

rolebindings
```
/registry/rolebindings/kube-public/kubeadm:bootstrap-signer-clusterinfo
/registry/rolebindings/kube-public/system:controller:bootstrap-signer
/registry/rolebindings/kube-system/kube-proxy
/registry/rolebindings/kube-system/kube-state-metrics
/registry/rolebindings/kube-system/kubeadm:kubeadm-certs
/registry/rolebindings/kube-system/kubeadm:kubelet-config-1.14
/registry/rolebindings/kube-system/kubeadm:nodes-kubeadm-config
/registry/rolebindings/kube-system/system::extension-apiserver-authentication-reader
/registry/rolebindings/kube-system/system::leader-locking-kube-controller-manager
/registry/rolebindings/kube-system/system::leader-locking-kube-scheduler
/registry/rolebindings/kube-system/system:controller:bootstrap-signer
/registry/rolebindings/kube-system/system:controller:cloud-provider
/registry/rolebindings/kube-system/system:controller:token-cleaner
```

roles
```
/registry/roles/kube-public/kubeadm:bootstrap-signer-clusterinfo
/registry/roles/kube-public/system:controller:bootstrap-signer
/registry/roles/kube-system/extension-apiserver-authentication-reader
/registry/roles/kube-system/kube-proxy
/registry/roles/kube-system/kube-state-metrics-resizer
/registry/roles/kube-system/kubeadm:kubeadm-certs
/registry/roles/kube-system/kubeadm:kubelet-config-1.14
/registry/roles/kube-system/kubeadm:nodes-kubeadm-config
/registry/roles/kube-system/system::leader-locking-kube-controller-manager
/registry/roles/kube-system/system::leader-locking-kube-scheduler
/registry/roles/kube-system/system:controller:bootstrap-signer
/registry/roles/kube-system/system:controller:cloud-provider
/registry/roles/kube-system/system:controller:token-cleaner
```
