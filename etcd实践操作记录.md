# etcd实践操作记录

> etcd是kubernetes的核心中的核心.kubernetes所有数据都存储在etcd,怎么检索删除etcd数据怎么备份恢复etcd数据?

## 1.etcd的api版本说明
```
flannel操作etcd使用的是v2的API,而kubernetes操作etcd使用的v3的API,所以在下面我们执行etcdctl的时候需要设置ETCDCTL_API环境变量,该变量默认值为2.

Etcd V2和V3之间的数据结构完全不同,互不兼容,也就是说使用V2版本的API创建的数据只能使用V2的API访问,V3的版本的API创建的数据只能使用V3的API访问.
这就造成我们访问etcd中保存的flannel的数据需要使用etcdctl的V2版本的客户端,而访问kubernetes的数据需要设置ETCDCTL_API=3环境变量来指定V3版本的API.
```

## 2.基础操作记录

- v2 api的操作记录

> kubernetes默认使用的api
```
etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem --version
etcdctl version: 3.3.7
API version: 2
```

> 检索节点信息,etcd使用的是leader模式.
```
etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem member list
1c83ad9421d77430: name=k8s-node3 peerURLs=https://192.168.174.130:2380 clientURLs=https://192.168.174.130:2379 isLeader=false
5eec694677c3c515: name=k8s-node2 peerURLs=https://192.168.174.129:2380 clientURLs=https://192.168.174.129:2379 isLeader=true
65f8d952bfce7d85: name=k8s-node1 peerURLs=https://192.168.174.128:2380 clientURLs=https://192.168.174.128:2379 isLeader=false
```

> api v2检索etcd的所有数据,存储的是flannel网络信息
```
etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem ls 
/kubernetes

etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem ls /kubernetes
/kubernetes/network

etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem ls /kubernetes/network
/kubernetes/network/config
/kubernetes/network/subnets
```

> 检索flannel网络信息,可见使用的是vxlan模式
```
etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem get /kubernetes/network/config
{"Network":"172.30.0.0/16",
"SubnetLen": 24, "Backend": {"Type": "vxlan"}}
```


> 对比下,下面是写入etcd网络信息时的命令
```
 etcdctl --endpoints=${ETCD_ENDPOINTS} --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/flanneld/cert/flanneld.pem --key-file=/etc/flanneld/cert/flanneld-key.pem set ${FLANNEL_ETCD_PREFIX}/config '{"Network":"'${CLUSTER_CIDR}'",
> "SubnetLen": 24, "Backend": {"Type": "vxlan"}}'
```

> 检索flannel节点子网分配情况,一个节点分配一个子网
```
etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem ls /kubernetes/network/subnets
/kubernetes/network/subnets/172.30.75.0-24
/kubernetes/network/subnets/172.30.49.0-24
/kubernetes/network/subnets/172.30.77.0-24
```


## 3.v3 api的操作记录

> 操作前设置api,export ETCDCTL_API=3

> 注意api v3的操作命令和v2不一样.

> 设置api,检索版本
```
export ETCDCTL_API=3

etcdctl version
etcdctl version: 3.3.7
API version: 3.3
```

# etcdctl命令参考
```
etcdctl -h
NAME:
	etcdctl - A simple command line client for etcd3.

USAGE:
	etcdctl

VERSION:
	3.3.7

API VERSION:
	3.3


COMMANDS:
	get			Gets the key or a range of keys
	put			Puts the given key into the store
	del			Removes the specified key or range of keys [key, range_end)
	txn			Txn processes all the requests in one transaction
	compaction		Compacts the event history in etcd
	alarm disarm		Disarms all alarms
	alarm list		Lists all alarms
	defrag			Defragments the storage of the etcd members with given endpoints
	endpoint health		Checks the healthiness of endpoints specified in `--endpoints` flag
	endpoint status		Prints out the status of endpoints specified in `--endpoints` flag
	endpoint hashkv		Prints the KV history hash for each endpoint in --endpoints
	move-leader		Transfers leadership to another etcd cluster member.
	watch			Watches events stream on keys or prefixes
	version			Prints the version of etcdctl
	lease grant		Creates leases
	lease revoke		Revokes leases
	lease timetolive	Get lease information
	lease list		List all active leases
	lease keep-alive	Keeps leases alive (renew)
	member add		Adds a member into the cluster
	member remove		Removes a member from the cluster
	member update		Updates a member in the cluster
	member list		Lists all members in the cluster
	snapshot save		Stores an etcd node backend snapshot to a given file
	snapshot restore	Restores an etcd member snapshot to an etcd directory
	snapshot status		Gets backend snapshot status of a given file
	make-mirror		Makes a mirror at the destination etcd cluster
	migrate			Migrates keys in a v2 store to a mvcc store
	lock			Acquires a named lock
	elect			Observes and participates in leader election
	auth enable		Enables authentication
	auth disable		Disables authentication
	user add		Adds a new user
	user delete		Deletes a user
	user get		Gets detailed information of a user
	user list		Lists all users
	user passwd		Changes password of user
	user grant-role		Grants a role to a user
	user revoke-role	Revokes a role from a user
	role add		Adds a new role
	role delete		Deletes a role
	role get		Gets detailed information of a role
	role list		Lists all roles
	role grant-permission	Grants a key to a role
	role revoke-permission	Revokes a key from a role
	check perf		Check the performance of the etcd cluster
	help			Help about any command

OPTIONS:
      --cacert=""				verify certificates of TLS-enabled secure servers using this CA bundle
      --cert=""					identify secure client using this TLS certificate file
      --command-timeout=5s			timeout for short running command (excluding dial timeout)
      --debug[=false]				enable client-side debug logging
      --dial-timeout=2s				dial timeout for client connections
  -d, --discovery-srv=""			domain name to query for SRV records describing cluster endpoints
      --endpoints=[127.0.0.1:2379]		gRPC endpoints
      --hex[=false]				print byte strings as hex encoded strings
      --insecure-discovery[=true]		accept insecure SRV records describing cluster endpoints
      --insecure-skip-tls-verify[=false]	skip server certificate verification
      --insecure-transport[=true]		disable transport security for client connections
      --keepalive-time=2s			keepalive time for client connections
      --keepalive-timeout=6s			keepalive timeout for client connections
      --key=""					identify secure client using this TLS key file
      --user=""					username[:password] for authentication (prompt if password is not supplied)
  -w, --write-out="simple"			set the output format (fields, json, protobuf, simple, table)
```


> 检索节点信息
```
etcdctl  member list -w table
+------------------+---------+-----------+------------------------------+------------------------------+
|        ID        | STATUS  |   NAME    |          PEER ADDRS          |         CLIENT ADDRS         |
+------------------+---------+-----------+------------------------------+------------------------------+
| 1c83ad9421d77430 | started | k8s-node3 | https://192.168.174.130:2380 | https://192.168.174.130:2379 |
| 5eec694677c3c515 | started | k8s-node2 | https://192.168.174.129:2380 | https://192.168.174.129:2379 |
| 65f8d952bfce7d85 | started | k8s-node1 | https://192.168.174.128:2380 | https://192.168.174.128:2379 |
+------------------+---------+-----------+------------------------------+------------------------------+
```

> 简单命令用用
```
[root@k8s-node1 ~]# etcdctl endpoint health
127.0.0.1:2379 is healthy: successfully committed proposal: took = 2.628115ms

[root@k8s-node1 ~]# etcdctl endpoint status
127.0.0.1:2379, 65f8d952bfce7d85, 3.3.7, 23 MB, false, 276, 1555337

[root@k8s-node1 ~]# etcdctl endpoint hashkv
127.0.0.1:2379, 3210071622
```

> 检索保存的所有数据目录,所有数据都保存在/registry目录

> 参数解释,–prefix:默认为true可以看到所有的子目录.–keys-only:默认为true,只显示key,如果设置为false,会显示key的所有值.

> 以下是检索的所有目录和子目录
```
etcdctl get /  --prefix --keys-only
/registry/apiregistration.k8s.io/apiservices/v1.

/registry/apiregistration.k8s.io/apiservices/v1.apps

/registry/apiregistration.k8s.io/apiservices/v1.authentication.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1.authorization.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1.autoscaling

/registry/apiregistration.k8s.io/apiservices/v1.batch

/registry/apiregistration.k8s.io/apiservices/v1.coordination.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1.networking.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1.rbac.authorization.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1.scheduling.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1.storage.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.admissionregistration.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.apiextensions.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.apps

/registry/apiregistration.k8s.io/apiservices/v1beta1.authentication.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.authorization.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.batch

/registry/apiregistration.k8s.io/apiservices/v1beta1.certificates.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.coordination.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.events.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.extensions

/registry/apiregistration.k8s.io/apiservices/v1beta1.networking.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.node.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.policy

/registry/apiregistration.k8s.io/apiservices/v1beta1.rbac.authorization.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.scheduling.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta1.storage.k8s.io

/registry/apiregistration.k8s.io/apiservices/v1beta2.apps

/registry/apiregistration.k8s.io/apiservices/v2beta1.autoscaling

/registry/apiregistration.k8s.io/apiservices/v2beta2.autoscaling

/registry/clusterrolebindings/auto-approve-csrs-for-group

/registry/clusterrolebindings/cluster-admin

/registry/clusterrolebindings/kubelet-bootstrap

/registry/clusterrolebindings/node-client-cert-renewal

/registry/clusterrolebindings/node-server-cert-renewal

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

/registry/clusterrolebindings/system:kubernetes

/registry/clusterrolebindings/system:node

/registry/clusterrolebindings/system:node-proxier

/registry/clusterrolebindings/system:public-info-viewer

/registry/clusterrolebindings/system:user-nonresource-bind

/registry/clusterrolebindings/system:volume-scheduler

/registry/clusterroles/admin

/registry/clusterroles/approve-node-server-renewal-csr

/registry/clusterroles/cluster-admin

/registry/clusterroles/discover_base_url

/registry/clusterroles/edit

/registry/clusterroles/system:aggregate-to-admin

/registry/clusterroles/system:aggregate-to-edit

/registry/clusterroles/system:aggregate-to-view

/registry/clusterroles/system:auth-delegator

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

/registry/clusterroles/system:kubernetes-to-kubelet

/registry/clusterroles/system:node

/registry/clusterroles/system:node-bootstrapper

/registry/clusterroles/system:node-problem-detector

/registry/clusterroles/system:node-proxier

/registry/clusterroles/system:persistent-volume-provisioner

/registry/clusterroles/system:public-info-viewer

/registry/clusterroles/system:volume-scheduler

/registry/clusterroles/view

/registry/configmaps/default/mysql-config

/registry/configmaps/default/mysql-config2

/registry/configmaps/kube-system/coredns

/registry/configmaps/kube-system/extension-apiserver-authentication

/registry/deployments/default/httpd-app

/registry/deployments/default/httpd-pod

/registry/deployments/default/mysql-t

/registry/deployments/default/mysql-test

/registry/deployments/default/wordpress-pod

/registry/deployments/kube-system/coredns

/registry/events/default/busybox.15da92b45565ca8a

/registry/events/default/busybox.15da92b46083229a

/registry/events/default/busybox.15da92b4841c0188

/registry/events/default/httpd.15da92b59a43e346

/registry/events/default/httpd.15da92ba858fde0a

/registry/events/default/httpd.15da92f22acf3927

/registry/leases/kube-node-lease/k8s-node1

/registry/leases/kube-node-lease/k8s-node2

/registry/leases/kube-node-lease/k8s-node3

/registry/masterleases/192.168.174.128

/registry/masterleases/192.168.174.129

/registry/masterleases/192.168.174.130

/registry/minions/k8s-node1

/registry/minions/k8s-node2

/registry/minions/k8s-node3

/registry/namespaces/default

/registry/namespaces/kube-node-lease

/registry/namespaces/kube-public

/registry/namespaces/kube-system

/registry/persistentvolumeclaims/default/mysql-pvc1

/registry/persistentvolumes/mysql-pv1

/registry/pods/default/busybox

/registry/pods/default/httpd

/registry/pods/default/httpd-app-6665fb7898-7x9vd

/registry/pods/default/httpd-app-6665fb7898-8w9k6

/registry/pods/default/httpd-app-6665fb7898-js8vv

/registry/pods/default/httpd-app-6665fb7898-q744z

/registry/pods/default/httpd-app-6665fb7898-xmksq

/registry/pods/default/httpd-pod-586b66458-vs4rm

/registry/pods/default/mysql-t-54666b579c-7m5rv

/registry/pods/default/mysql-test-647b8db96b-qdxw6

/registry/pods/default/wordpress-pod-74c47cd8dd-t4gmr

/registry/pods/kube-system/coredns-5fb99965-brwjq

/registry/pods/kube-system/coredns-5fb99965-svpvn

/registry/priorityclasses/system-cluster-critical

/registry/priorityclasses/system-node-critical

/registry/ranges/serviceips

/registry/ranges/servicenodeports

/registry/replicasets/default/httpd-app-6665fb7898

/registry/replicasets/default/httpd-pod-586b66458

/registry/replicasets/default/httpd-pod-5b8d447886

/registry/replicasets/default/httpd-pod-6bd9576bc9

/registry/replicasets/default/mysql-t-54666b579c

/registry/replicasets/default/mysql-test-647b8db96b

/registry/replicasets/default/wordpress-pod-74c47cd8dd

/registry/replicasets/kube-system/coredns-5fb99965

/registry/rolebindings/default/system:user-nonresource-bind

/registry/rolebindings/kube-public/system:controller:bootstrap-signer

/registry/rolebindings/kube-system/system::extension-apiserver-authentication-reader

/registry/rolebindings/kube-system/system::leader-locking-kube-controller-manager

/registry/rolebindings/kube-system/system::leader-locking-kube-scheduler

/registry/rolebindings/kube-system/system:controller:bootstrap-signer

/registry/rolebindings/kube-system/system:controller:cloud-provider

/registry/rolebindings/kube-system/system:controller:token-cleaner

/registry/roles/kube-public/system:controller:bootstrap-signer

/registry/roles/kube-system/extension-apiserver-authentication-reader

/registry/roles/kube-system/system::leader-locking-kube-controller-manager

/registry/roles/kube-system/system::leader-locking-kube-scheduler

/registry/roles/kube-system/system:controller:bootstrap-signer

/registry/roles/kube-system/system:controller:cloud-provider

/registry/roles/kube-system/system:controller:token-cleaner

/registry/secrets/default/default-token-fwtch

/registry/secrets/default/mysecret

/registry/secrets/default/mysecret2

/registry/secrets/kube-node-lease/default-token-76lpr

/registry/secrets/kube-public/default-token-6fvpw

/registry/secrets/kube-system/attachdetach-controller-token-7hc8p

/registry/secrets/kube-system/bootstrap-signer-token-7xshb

/registry/secrets/kube-system/certificate-controller-token-dwqx4

/registry/secrets/kube-system/clusterrole-aggregation-controller-token-gr77d

/registry/secrets/kube-system/coredns-token-52bg6

/registry/secrets/kube-system/cronjob-controller-token-2xkff

/registry/secrets/kube-system/daemon-set-controller-token-pcdln

/registry/secrets/kube-system/default-token-82pm9

/registry/secrets/kube-system/deployment-controller-token-2t9xj

/registry/secrets/kube-system/disruption-controller-token-q982v

/registry/secrets/kube-system/endpoint-controller-token-28zb9

/registry/secrets/kube-system/expand-controller-token-f9ht9

/registry/secrets/kube-system/generic-garbage-collector-token-6llv2

/registry/secrets/kube-system/horizontal-pod-autoscaler-token-6kdkn

/registry/secrets/kube-system/job-controller-token-7dgtm

/registry/secrets/kube-system/namespace-controller-token-8w94q

/registry/secrets/kube-system/node-controller-token-x4q8s

/registry/secrets/kube-system/persistent-volume-binder-token-pknv8

/registry/secrets/kube-system/pod-garbage-collector-token-gr2c4

/registry/secrets/kube-system/pv-protection-controller-token-ctcrj

/registry/secrets/kube-system/pvc-protection-controller-token-7kc5j

/registry/secrets/kube-system/replicaset-controller-token-5z6sw

/registry/secrets/kube-system/replication-controller-token-jgk96

/registry/secrets/kube-system/resourcequota-controller-token-zbx8g

/registry/secrets/kube-system/service-account-controller-token-cnsn6

/registry/secrets/kube-system/service-controller-token-gv47w

/registry/secrets/kube-system/statefulset-controller-token-np2qv

/registry/secrets/kube-system/token-cleaner-token-mtpht

/registry/secrets/kube-system/ttl-controller-token-lr8nz

/registry/serviceaccounts/default/default

/registry/serviceaccounts/kube-node-lease/default

/registry/serviceaccounts/kube-public/default

/registry/serviceaccounts/kube-system/attachdetach-controller

/registry/serviceaccounts/kube-system/bootstrap-signer

/registry/serviceaccounts/kube-system/certificate-controller

/registry/serviceaccounts/kube-system/clusterrole-aggregation-controller

/registry/serviceaccounts/kube-system/coredns

/registry/serviceaccounts/kube-system/cronjob-controller

/registry/serviceaccounts/kube-system/daemon-set-controller

/registry/serviceaccounts/kube-system/default

/registry/serviceaccounts/kube-system/deployment-controller

/registry/serviceaccounts/kube-system/disruption-controller

/registry/serviceaccounts/kube-system/endpoint-controller

/registry/serviceaccounts/kube-system/expand-controller

/registry/serviceaccounts/kube-system/generic-garbage-collector

/registry/serviceaccounts/kube-system/horizontal-pod-autoscaler

/registry/serviceaccounts/kube-system/job-controller

/registry/serviceaccounts/kube-system/namespace-controller

/registry/serviceaccounts/kube-system/node-controller

/registry/serviceaccounts/kube-system/persistent-volume-binder

/registry/serviceaccounts/kube-system/pod-garbage-collector

/registry/serviceaccounts/kube-system/pv-protection-controller

/registry/serviceaccounts/kube-system/pvc-protection-controller

/registry/serviceaccounts/kube-system/replicaset-controller

/registry/serviceaccounts/kube-system/replication-controller

/registry/serviceaccounts/kube-system/resourcequota-controller

/registry/serviceaccounts/kube-system/service-account-controller

/registry/serviceaccounts/kube-system/service-controller

/registry/serviceaccounts/kube-system/statefulset-controller

/registry/serviceaccounts/kube-system/token-cleaner

/registry/serviceaccounts/kube-system/ttl-controller

/registry/services/endpoints/default/httpd-svc

/registry/services/endpoints/default/kubernetes

/registry/services/endpoints/default/mysql-t

/registry/services/endpoints/default/mysql-test

/registry/services/endpoints/default/wordpress

/registry/services/endpoints/kube-system/kube-controller-manager

/registry/services/endpoints/kube-system/kube-dns

/registry/services/endpoints/kube-system/kube-scheduler

/registry/services/specs/default/httpd-svc

/registry/services/specs/default/kubernetes

/registry/services/specs/default/mysql-t

/registry/services/specs/default/mysql-test

/registry/services/specs/default/wordpress

/registry/services/specs/kube-system/kube-dns
```


> 检索pod信息

> 先用kubectl命令看看多少pod
```
kubectl get pod  --all-namespaces
NAMESPACE     NAME                             READY   STATUS             RESTARTS   AGE
default       busybox                          1/1     Running            23         5d22h
default       httpd                            0/1     CrashLoopBackOff   131        23h
default       httpd-app-6665fb7898-7x9vd       1/1     Running            4          7d3h
default       httpd-app-6665fb7898-8w9k6       1/1     Running            4          7d3h
default       httpd-app-6665fb7898-js8vv       1/1     Running            4          7d3h
default       httpd-app-6665fb7898-q744z       1/1     Running            4          7d3h
default       httpd-app-6665fb7898-xmksq       1/1     Running            4          7d3h
default       httpd-pod-586b66458-vs4rm        1/1     Running            3          6d4h
default       mysql-t-54666b579c-7m5rv         1/1     Running            2          3d23h
default       mysql-test-647b8db96b-qdxw6      1/1     Running            1          21h
default       wordpress-pod-74c47cd8dd-t4gmr   1/1     Running            3          5d22h
kube-system   coredns-5fb99965-brwjq           1/1     Running            12         20d
kube-system   coredns-5fb99965-svpvn           1/1     Running            12         20d
```

> etcd里查找pod信息,见下
```
 etcdctl get /registry/pods  --prefix --keys-only
/registry/pods/default/busybox

/registry/pods/default/httpd

/registry/pods/default/httpd-app-6665fb7898-7x9vd

/registry/pods/default/httpd-app-6665fb7898-8w9k6

/registry/pods/default/httpd-app-6665fb7898-js8vv

/registry/pods/default/httpd-app-6665fb7898-q744z

/registry/pods/default/httpd-app-6665fb7898-xmksq

/registry/pods/default/httpd-pod-586b66458-vs4rm

/registry/pods/default/mysql-t-54666b579c-7m5rv

/registry/pods/default/mysql-test-647b8db96b-qdxw6

/registry/pods/default/wordpress-pod-74c47cd8dd-t4gmr

/registry/pods/kube-system/coredns-5fb99965-brwjq

/registry/pods/kube-system/coredns-5fb99965-svpvn
```

> 检索单个pod详细信息,输出格式有四种,但是protobuf和simple会乱码,这里使用json格式,见下
```
etcdctl get /registry/pods/default/busybox  -w json
{"header":{"cluster_id":8418215620332445483,"member_id":7347861741483490693,"revision":596755,"raft_term":276},"kvs":[{"key":"L3JlZ2lzdHJ5L3BvZHMvZGVmYXVsdC9idXN5Ym94","create_revision":448381,"mod_revision":594625,"version":52,"value":"azhzAAoJCgJ2MRIDUG9kEqIMCowECgdidXN5Ym94EgAaB2RlZmF1bHQiACokYzZmZjg2YmItMGM5ZC00NTg0LWFhOTQtYjczN2Q5ZTFhMWI4MgA4AEIICMSA1O4FEABivQMKMGt1YmVjdGwua3ViZXJuZXRlcy5pby9sYXN0LWFwcGxpZWQtY29uZmlndXJhdGlvbhKIA3siYXBpVmVyc2lvbiI6InYxIiwia2luZCI6IlBvZCIsIm1ldGFkYXRhIjp7ImFubm90YXRpb25zIjp7fSwibmFtZSI6ImJ1c3lib3giLCJuYW1lc3BhY2UiOiJkZWZhdWx0In0sInNwZWMiOnsiY29udGFpbmVycyI6W3siY29tbWFuZCI6WyJzbGVlcCIsIjM2MDAiXSwiaW1hZ2UiOiJidXN5Ym94OjEuMjguNCIsImltYWdlUHVsbFBvbGljeSI6IklmTm90UHJlc2VudCIsIm5hbWUiOiJidXN5Ym94Iiwidm9sdW1lTW91bnRzIjpbeyJtb3VudFBhdGgiOiIvZXRjL3Rlc3QiLCJuYW1lIjoidGVzdCIsInJlYWRPbmx5Ijp0cnVlfV19XSwicmVzdGFydFBvbGljeSI6IkFsd2F5cyIsInZvbHVtZXMiOlt7Im5hbWUiOiJ0ZXN0Iiwic2VjcmV0Ijp7InNlY3JldE5hbWUiOiJteXNlY3JldDIifX1dfX0KegAS5wMKGAoEdGVzdBIQMg4KCW15c2VjcmV0MhikAwoxChNkZWZhdWx0LXRva2VuLWZ3dGNoEhoyGAoTZGVmYXVsdC10b2tlbi1md3RjaBikAxLDAQoHYnVzeWJveBIOYnVzeWJveDoxLjI4LjQaBXNsZWVwGgQzNjAwKgBCAEoXCgR0ZXN0EAEaCS9ldGMvdGVzdCIAMgBKSgoTZGVmYXVsdC10b2tlbi1md3RjaBABGi0vdmFyL3J1bi9zZWNyZXRzL2t1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQiADIAahQvZGV2L3Rlcm1pbmF0aW9uLWxvZ3IMSWZOb3RQcmVzZW50gAEAiAEAkAEAogEERmlsZRoGQWx3YXlzIB4yDENsdXN0ZXJGaXJzdEIHZGVmYXVsdEoHZGVmYXVsdFIJazhzLW5vZGUxWABgAGgAcgCCAQCKAQCaARFkZWZhdWx0LXNjaGVkdWxlcrIBNgocbm9kZS5rdWJlcm5ldGVzLmlvL25vdC1yZWFkeRIGRXhpc3RzGgAiCU5vRXhlY3V0ZSisArIBOAoebm9kZS5rdWJlcm5ldGVzLmlvL3VucmVhY2hhYmxlEgZFeGlzdHMaACIJTm9FeGVjdXRlKKwCwgEAyAEA8AEBGqYECgdSdW5uaW5nEiMKC0luaXRpYWxpemVkEgRUcnVlGgAiCAjEgNTuBRAAKgAyABIdCgVSZWFkeRIEVHJ1ZRoAIggIia3z7gUQACoAMgASJwoPQ29udGFpbmVyc1JlYWR5EgRUcnVlGgAiCAiJrfPuBRAAKgAyABIkCgxQb2RTY2hlZHVsZWQSBFRydWUaACIICMSA1O4FEAAqADIAGgAiACoPMTkyLjE2OC4xNzQuMTI4MgsxNzIuMzAuNzcuMzoICMSA1O4FEABCzQIKB2J1c3lib3gSDBIKCggIiK3z7gUQABpyGnAIABAAGglDb21wbGV0ZWQiACoICPeQ8+4FEAAyCAiHrfPuBRAAOklkb2NrZXI6Ly9jNTQ3YmFlZWZkZTFmNDg5ZGE4NTc0YTFkYjhlZWZhYWJhYTViNzFhYWJiYjNmOGYyOWIzNjk1YmU2ZGQ4OGJlIAEoGDIOYnVzeWJveDoxLjI4LjQ6YWRvY2tlci1wdWxsYWJsZTovL2J1c3lib3hAc2hhMjU2OjE0MWMyNTNiYzRjM2ZkMGEyMDFkMzJkYzFmNDkzYmNmM2ZmZjAwM2I2ZGY0MTZkZWE0ZjQxMDQ2ZTBmMzdkNDdCSWRvY2tlcjovLzhkZGU1NDc2ODAxMWY1YWI4ZmIwYWVmNzJjNjg0YWEwNTQyNDNlZTU1NTdiN2EyMzQ3OWNiMDQwY2I1ODA3YzFKCkJlc3RFZmZvcnRaABoAIgA="}],"count":1}
```

> 也可以用curl命令来获取这个信息,见下

> 可以通过命令来获取pod的etcd存储路径selflink
```
kubectl get pod busybox -o yaml |grep self
  selfLink: /api/v1/namespaces/default/pods/busybox
```

```
curl https://192.168.174.127:8443/api/v1/namespaces/default/pods/busybox  --cacert /etc/kubernetes/cert/ca.pem --cert /etc/kubernetes/cert/kubernetes.pem --key /etc/kubernetes/cert/kubernetes-key.pem
{
  "kind": "Pod",
  "apiVersion": "v1",
  "metadata": {
    "name": "busybox",
    "namespace": "default",
    "selfLink": "/api/v1/namespaces/default/pods/busybox",
    "uid": "c6ff86bb-0c9d-4584-aa94-b737d9e1a1b8",
    "resourceVersion": "594625",
    "creationTimestamp": "2019-11-20T08:58:44Z",
    "annotations": {
      "kubectl.kubernetes.io/last-applied-configuration": "{\"apiVersion\":\"v1\",\"kind\":\"Pod\",\"metadata\":{\"annotations\":{},\"name\":\"busybox\",\"namespace\":\"default\"},\"spec\":{\"containers\":[{\"command\":[\"sleep\",\"3600\"],\"image\":\"busybox:1.28.4\",\"imagePullPolicy\":\"IfNotPresent\",\"name\":\"busybox\",\"volumeMounts\":[{\"mountPath\":\"/etc/test\",\"name\":\"test\",\"readOnly\":true}]}],\"restartPolicy\":\"Always\",\"volumes\":[{\"name\":\"test\",\"secret\":{\"secretName\":\"mysecret2\"}}]}}\n"
    }
  },
  "spec": {
    "volumes": [
      {
        "name": "test",
        "secret": {
          "secretName": "mysecret2",
          "defaultMode": 420
        }
      },
      {
        "name": "default-token-fwtch",
        "secret": {
          "secretName": "default-token-fwtch",
          "defaultMode": 420
        }
      }
    ],
    "containers": [
      {
        "name": "busybox",
        "image": "busybox:1.28.4",
        "command": [
          "sleep",
          "3600"
        ],
        "resources": {
          
        },
        "volumeMounts": [
          {
            "name": "test",
            "readOnly": true,
            "mountPath": "/etc/test"
          },
          {
            "name": "default-token-fwtch",
            "readOnly": true,
            "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount"
          }
        ],
        "terminationMessagePath": "/dev/termination-log",
        "terminationMessagePolicy": "File",
        "imagePullPolicy": "IfNotPresent"
      }
    ],
    "restartPolicy": "Always",
    "terminationGracePeriodSeconds": 30,
    "dnsPolicy": "ClusterFirst",
    "serviceAccountName": "default",
    "serviceAccount": "default",
    "nodeName": "k8s-node1",
    "securityContext": {
      
    },
    "schedulerName": "default-scheduler",
    "tolerations": [
      {
        "key": "node.kubernetes.io/not-ready",
        "operator": "Exists",
        "effect": "NoExecute",
        "tolerationSeconds": 300
      },
      {
        "key": "node.kubernetes.io/unreachable",
        "operator": "Exists",
        "effect": "NoExecute",
        "tolerationSeconds": 300
      }
    ],
    "priority": 0,
    "enableServiceLinks": true
  },
  "status": {
    "phase": "Running",
    "conditions": [
      {
        "type": "Initialized",
        "status": "True",
        "lastProbeTime": null,
        "lastTransitionTime": "2019-11-20T08:58:44Z"
      },
      {
        "type": "Ready",
        "status": "True",
        "lastProbeTime": null,
        "lastTransitionTime": "2019-11-26T07:38:49Z"
      },
      {
        "type": "ContainersReady",
        "status": "True",
        "lastProbeTime": null,
        "lastTransitionTime": "2019-11-26T07:38:49Z"
      },
      {
        "type": "PodScheduled",
        "status": "True",
        "lastProbeTime": null,
        "lastTransitionTime": "2019-11-20T08:58:44Z"
      }
    ],
    "hostIP": "192.168.174.128",
    "podIP": "172.30.77.3",
    "startTime": "2019-11-20T08:58:44Z",
    "containerStatuses": [
      {
        "name": "busybox",
        "state": {
          "running": {
            "startedAt": "2019-11-26T07:38:48Z"
          }
        },
        "lastState": {
          "terminated": {
            "exitCode": 0,
            "reason": "Completed",
            "startedAt": "2019-11-26T06:38:47Z",
            "finishedAt": "2019-11-26T07:38:47Z",
            "containerID": "docker://c547baeefde1f489da8574a1db8eefaabaa5b71aabbb3f8f29b3695be6dd88be"
          }
        },
        "ready": true,
        "restartCount": 24,
        "image": "busybox:1.28.4",
        "imageID": "docker-pullable://busybox@sha256:141c253bc4c3fd0a201d32dc1f493bcf3fff003b6df416dea4f41046e0f37d47",
        "containerID": "docker://8dde54768011f5ab8fb0aef72c684aa054243ee5557b7a23479cb040cb5807c1"
      }
    ],
    "qosClass": "BestEffort"
  }
```

> 通过etcd删除pod,删除下面两个pod
```
kubectl get pod
NAME                             READY   STATUS             RESTARTS   AGE
httpd-app-6665fb7898-7x9vd       1/1     Running            4          7d4h
httpd-app-6665fb7898-8w9k6       1/1     Running            4          7d4h
httpd-app-6665fb7898-js8vv       1/1     Running            4          7d4h
httpd-app-6665fb7898-q744z       1/1     Running            4          7d4h
httpd-app-6665fb7898-xmksq       1/1     Running            4          7d4h
httpd-pod-586b66458-vs4rm        1/1     Running            3          6d5h
```

> 检索deployment
```
etcdctl get /registry/deployment --keys-only --prefix
/registry/deployments/default/httpd-app

/registry/deployments/default/httpd-pod
```

> 删除
```
etcdctl del /registry/deployments/default/httpd-app
1

etcdctl del /registry/deployments/default/httpd-pod
1
```

> 删除后检索,已经删除了
```
kubectl get deployment
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
mysql-t         1/1     1            1           4d
mysql-test      1/1     1            1           22h
wordpress-pod   1/1     1            1           5d23h
```

```
kubectl get pod
NAME                             READY   STATUS             RESTARTS   AGE
busybox                          1/1     Running            24         5d23h
httpd                            0/1     CrashLoopBackOff   151        24h
mysql-t-54666b579c-7m5rv         1/1     Running            2          4d
mysql-test-647b8db96b-qdxw6      1/1     Running            1          22h
wordpress-pod-74c47cd8dd-t4gmr   1/1     Running            3          5d23h
```

## 4.etcd数据备份

> 最好做个脚本每天备份

> 备份
```
etcdctl --endpoints 127.0.0.1:2379 snapshot save snashot.db
Snapshot saved at snashot.db

 ll -h
total 22M
-rw-r--r-- 1 root root 22M Nov 26 03:25 snashot.db
```


> 删除一个节点的数据再恢复

> 执行命令:systemctl stop etcd

> 执行命令:rm -rf /var/lib/etcd/

> 恢复
```
etcdctl --name=k8s-node1 --endpoints="https://192.168.174.128:2379" --cacert=/etc/kubernetes/cert/ca.pem --key=/etc/etcd/cert/etcd-key.pem --cert=/etc/etcd/cert/etcd.pem --initial-cluster-token=etcd-cluster-1 --initial-advertise-peer-urls=https://192.168.174.128:2380 --initial-cluster=k8s-node1=https://192.168.174.128:2380,k8s-node2=https://192.168.174.129:2380,k8s-node3=https://192.168.174.130:2380 --data-dir=/var/lib/etcd snapshot restore snashot.db
2019-11-26 03:36:36.038458 I | mvcc: restore compact to 598557
2019-11-26 03:36:36.046152 I | etcdserver/membership: added member 189141ea20f3026c [https://192.168.174.128:2380] to cluster 5a726f403538a406
2019-11-26 03:36:36.046181 I | etcdserver/membership: added member 2a5472cf06cd4b08 [https://192.168.174.129:2380] to cluster 5a726f403538a406
2019-11-26 03:36:36.046192 I | etcdserver/membership: added member d5b1c5fde22a3133 [https://192.168.174.130:2380] to cluster 5a726f403538a406
```

> 重启服务
```
systemctl daemon-reload && systemctl restart etcd
Job for etcd.service failed because the control process exited with error code. See "systemctl status etcd.service" and "journalctl -xe" for details.
```

> 服务起不来,报错
```
Nov 26 03:39:23 k8s-node1 etcd: etcd Version: 3.3.7
Nov 26 03:39:23 k8s-node1 etcd: Git SHA: 56536de55
Nov 26 03:39:23 k8s-node1 etcd: Go Version: go1.9.6
Nov 26 03:39:23 k8s-node1 etcd: Go OS/Arch: linux/amd64
Nov 26 03:39:23 k8s-node1 etcd: setting maximum number of CPUs to 1, total number of available CPUs is 1
Nov 26 03:39:23 k8s-node1 etcd: error listing data dir: /var/lib/etcd
Nov 26 03:39:23 k8s-node1 systemd: etcd.service: main process exited, code=exited, status=1/FAILURE
Nov 26 03:39:23 k8s-node1 systemd: Failed to start Etcd Server.
Nov 26 03:39:23 k8s-node1 systemd: Unit etcd.service entered failed state.
Nov 26 03:39:23 k8s-node1 systemd: etcd.service failed.
```

> 检查权限
```
修改数据目录权限,默认是root:root
chown -R k8s:k8s /var/lib/etcd
```

>  再重新启动,还是报错
```
systemctl status etcd -l
● etcd.service - Etcd Server
   Loaded: loaded (/etc/systemd/system/etcd.service; enabled; vendor preset: disabled)
   Active: activating (start) since Tue 2019-11-26 03:42:09 EST; 37s ago
     Docs: https://github.com/coreos
 Main PID: 46204 (etcd)
    Tasks: 6
   Memory: 29.2M
   CGroup: /system.slice/etcd.service
           └─46204 /opt/k8s/bin/etcd --data-dir=/var/lib/etcd --name=k8s-node1 --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem --trusted-ca-file=/etc/kubernetes/cert/ca.pem --peer-cert-file=/etc/etcd/cert/etcd.pem --peer-key-file=/etc/etcd/cert/etcd-key.pem --peer-trusted-ca-file=/etc/kubernetes/cert/ca.pem --peer-client-cert-auth --client-cert-auth --listen-peer-urls=https://192.168.174.128:2380 --initial-advertise-peer-urls=https://192.168.174.128:2380 --listen-client-urls=https://192.168.174.128:2379,http://127.0.0.1:2379 --advertise-client-urls=https://192.168.174.128:2379 --initial-cluster-token=etcd-cluster-0 --initial-cluster=k8s-node1=https://192.168.174.128:2380,k8s-node2=https://192.168.174.129:2380,k8s-node3=https://192.168.174.130:2380 --initial-cluster-state=new

Nov 26 03:42:47 k8s-node1 etcd[46204]: request sent was ignored (cluster ID mismatch: peer[2a5472cf06cd4b08]=74d382814c8f5f2b, local=5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request sent was ignored (cluster ID mismatch: peer[d5b1c5fde22a3133]=74d382814c8f5f2b, local=5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request cluster ID mismatch (got 74d382814c8f5f2b want 5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request cluster ID mismatch (got 74d382814c8f5f2b want 5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request sent was ignored (cluster ID mismatch: peer[d5b1c5fde22a3133]=74d382814c8f5f2b, local=5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request sent was ignored (cluster ID mismatch: peer[2a5472cf06cd4b08]=74d382814c8f5f2b, local=5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request cluster ID mismatch (got 74d382814c8f5f2b want 5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request cluster ID mismatch (got 74d382814c8f5f2b want 5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request cluster ID mismatch (got 74d382814c8f5f2b want 5a726f403538a406)
Nov 26 03:42:47 k8s-node1 etcd[46204]: request cluster ID mismatch (got 74d382814c8f5f2b want 5a726f403538a406)
```

> 很无奈的报错,只能删除所有节点的etcd存储目录数据,然后恢复

> 所有节点做下面操作
```
执行命令:systemctl stop etcd
执行命令:rm -rf /var/lib/etcd/
```

> 恢复
```
[root@k8s-node1 etcd_db]# etcdctl --name=k8s-node1 --endpoints="https://192.168.174.128:2379" --cacert=/etc/kubernetes/cert/ca.pem --key=/etc/etcd/cert/etcd-key.pem --cert=/etc/etcd/cert/etcd.pem --initial-cluster-token=etcd-cluster-1 --initial-advertise-peer-urls=https://192.168.174.128:2380 --initial-cluster=k8s-node1=https://192.168.174.128:2380,k8s-node2=https://192.168.174.129:2380,k8s-node3=https://192.168.174.130:2380 --data-dir=/var/lib/etcd snapshot restore snashot.db

[root@k8s-node2 ~]# etcdctl --name=k8s-node2 --endpoints="https://192.168.174.129:2379" --cacert=/etc/kubernetes/cert/ca.pem --key=/etc/etcd/cert/etcd-key.pem --cert=/etc/etcd/cert/etcd.pem --initial-cluster-token=etcd-cluster-1 --initial-advertise-peer-urls=https://192.168.174.129:2380 --initial-cluster=k8s-node1=https://192.168.174.128:2380,k8s-node2=https://192.168.174.129:2380,k8s-node3=https://192.168.174.130:2380 --data-dir=/var/lib/etcd snapshot restore snashot.db

[root@k8s-node3 ~]# etcdctl --name=k8s-node3 --endpoints="https://192.168.174.130:2379" --cacert=/etc/kubernetes/cert/ca.pem --key=/etc/etcd/cert/etcd-key.pem --cert=/etc/etcd/cert/etcd.pem --initial-cluster-token=etcd-cluster-1 --initial-advertise-peer-urls=https://192.168.174.130:2380 --initial-cluster=k8s-node1=https://192.168.174.128:2380,k8s-node2=https://192.168.174.129:2380,k8s-node3=https://192.168.174.130:2380 --data-dir=/var/lib/etcd snapshot restore snashot.db
```

> 修改权限
```
chown -R k8s:k8s /var/lib/etcd
```

> 重启服务
```
systemctl daemon-reload && systemctl restart etcd
```

> 服务起来了
```
[root@k8s-node1 etcd_db]# systemctl status etcd
● etcd.service - Etcd Server
   Loaded: loaded (/etc/systemd/system/etcd.service; enabled; vendor preset: disabled)
   Active: active (running) since Tue 2019-11-26 03:53:26 EST; 25s ago
     Docs: https://github.com/coreos
 Main PID: 50373 (etcd)
    Tasks: 7
   Memory: 38.6M
   CGroup: /system.slice/etcd.service
           └─50373 /opt/k8s/bin/etcd --data-dir=/var/lib/etcd --name=k8s-node1 --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem --trusted-ca...

Nov 26 03:53:32 k8s-node1 etcd[50373]: read-only range request "key:\"/registry/deployments\" range_end:\"/registry/deploymentt\" count_only:true " took too...to execute
Nov 26 03:53:32 k8s-node1 etcd[50373]: setting up the initial cluster version to 3.3
Nov 26 03:53:32 k8s-node1 etcd[50373]: set the initial cluster version to 3.3
Nov 26 03:53:32 k8s-node1 etcd[50373]: enabled capabilities for version 3.3
Nov 26 03:53:33 k8s-node1 etcd[50373]: read-only range request "key:\"/registry/validatingwebhookconfigurations/\" range_end:\"/registry/validatingwebhookco...to execute
Nov 26 03:53:33 k8s-node1 etcd[50373]: read-only range request "key:\"/registry/controllerrevisions/\" range_end:\"/registry/controllerrevisions0\" limit:10...to execute
Nov 26 03:53:33 k8s-node1 etcd[50373]: read-only range request "key:\"/registry/deployments/\" range_end:\"/registry/deployments0\" limit:10000 " took too l...to execute
Nov 26 03:53:33 k8s-node1 etcd[50373]: read-only range request "key:\"/registry/apiregistration.k8s.io/apiservices/\" range_end:\"/registry/apiregistration....to execute
Nov 26 03:53:33 k8s-node1 etcd[50373]: read-only range request "key:\"/registry/apiregistration.k8s.io/apiservices/\" range_end:\"/registry/apiregistration....to execute
Nov 26 03:53:33 k8s-node1 etcd[50373]: read-only range request "key:\"/registry/apiregistration.k8s.io/apiservices/\" range_end:\"/registry/apiregistration....to execute
Hint: Some lines were ellipsized, use -l to show in full.
[root@k8s-node1 etcd_db]# etcdctl member list
189141ea20f3026c, started, k8s-node1, https://192.168.174.128:2380, https://192.168.174.128:2379
2a5472cf06cd4b08, started, k8s-node2, https://192.168.174.129:2380, https://192.168.174.129:2379
d5b1c5fde22a3133, started, k8s-node3, https://192.168.174.130:2380, https://192.168.174.130:2379
```

```
[root@k8s-node1 etcd_db]# kubectl get all --all-namespaces
NAMESPACE     NAME                                 READY   STATUS             RESTARTS   AGE
default       pod/busybox                          1/1     Running            24         5d23h
default       pod/httpd                            0/1     CrashLoopBackOff   163        25h
default       pod/mysql-t-54666b579c-7m5rv         1/1     Running            2          4d1h
default       pod/mysql-test-647b8db96b-qdxw6      1/1     Running            1          23h
default       pod/wordpress-pod-74c47cd8dd-t4gmr   1/1     Running            3          6d
kube-system   pod/coredns-5fb99965-brwjq           1/1     Running            12         20d
kube-system   pod/coredns-5fb99965-svpvn           1/1     Running            12         20d


NAMESPACE     NAME                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                  AGE
default       service/httpd-svc    NodePort    10.254.125.1     <none>        80:8400/TCP              7d5h
default       service/kubernetes   ClusterIP   10.254.0.1       <none>        443/TCP                  21d
default       service/mysql-t      ClusterIP   10.254.177.63    <none>        3306/TCP                 4d1h
default       service/mysql-test   ClusterIP   10.254.177.188   <none>        3306/TCP                 23h
default       service/wordpress    NodePort    10.254.208.45    <none>        8080:8800/TCP            6d
kube-system   service/kube-dns     ClusterIP   10.254.0.2       <none>        53/UDP,53/TCP,9153/TCP   20d


NAMESPACE     NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
default       deployment.apps/mysql-t         1/1     1            1           4d1h
default       deployment.apps/mysql-test      1/1     1            1           23h
default       deployment.apps/wordpress-pod   1/1     1            1           6d
kube-system   deployment.apps/coredns         2/2     2            2           20d

NAMESPACE     NAME                                       DESIRED   CURRENT   READY   AGE
default       replicaset.apps/mysql-t-54666b579c         1         1         1       4d1h
default       replicaset.apps/mysql-test-647b8db96b      1         1         1       23h
default       replicaset.apps/wordpress-pod-74c47cd8dd   1         1         1       6d
kube-system   replicaset.apps/coredns-5fb99965           2         2         2       20d
```

> flanneld因为是v2的api,数据丢失,没有恢复
```
systemctl status flanneld
● flanneld.service - Flanneld overlay address etcd agent
   Loaded: loaded (/etc/systemd/system/flanneld.service; enabled; vendor preset: disabled)
   Active: active (running) since Mon 2019-11-25 20:38:06 EST; 7h ago
 Main PID: 1593 (flanneld)
    Tasks: 7
   Memory: 28.1M
   CGroup: /system.slice/flanneld.service
           └─1593 /opt/k8s/bin/flanneld -etcd-cafile=/etc/kubernetes/cert/ca.pem -etcd-certfile=/etc/flanneld/cert/flanneld.pem -etcd-keyfile=/etc/flanneld/cert/flann...

Nov 26 03:53:20 k8s-node1 flanneld[1593]: ; error #2: dial tcp 192.168.174.129:2379: getsockopt: connection refused
Nov 26 03:53:20 k8s-node1 flanneld[1593]: E1126 03:53:20.760062    1593 watch.go:43] Watch subnets: client: etcd cluster is unavailable or misconfigured; er...on refused
Nov 26 03:53:20 k8s-node1 flanneld[1593]: ; error #1: dial tcp 192.168.174.128:2379: getsockopt: connection refused
Nov 26 03:53:20 k8s-node1 flanneld[1593]: ; error #2: dial tcp 192.168.174.129:2379: getsockopt: connection refused
Nov 26 03:53:21 k8s-node1 flanneld[1593]: E1126 03:53:21.754201    1593 watch.go:171] Subnet watch failed: client: etcd cluster is unavailable or misconfigu...on refused
Nov 26 03:53:21 k8s-node1 flanneld[1593]: ; error #1: dial tcp 192.168.174.128:2379: getsockopt: connection refused
Nov 26 03:53:21 k8s-node1 flanneld[1593]: ; error #2: dial tcp 192.168.174.129:2379: getsockopt: connection refused
Nov 26 03:53:21 k8s-node1 flanneld[1593]: E1126 03:53:21.764048    1593 watch.go:43] Watch subnets: client: etcd cluster is unavailable or misconfigured; er...on refused
Nov 26 03:53:21 k8s-node1 flanneld[1593]: ; error #1: dial tcp 192.168.174.128:2379: getsockopt: connection refused
Nov 26 03:53:21 k8s-node1 flanneld[1593]: ; error #2: dial tcp 192.168.174.129:2379: getsockopt: connection refused
```

```
export ETCDCTL_API=2
etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem ls /kubernetes/network/subnets
Error:  100: Key not found (/kubernetes) [7]
```


> 重新生成flanneld的网络信息
```
[root@k8s-node1 etcd_db]# source /opt/k8s/bin/environment.sh

[root@k8s-node1 etcd_db]# echo ${ETCD_ENDPOINTS}
https://192.168.174.128:2379,https://192.168.174.129:2379,https://192.168.174.130:2379

[root@k8s-node1 etcd_db]# export ETCDCTL_API=2

[root@k8s-node1 etcd_db]# etcdctl --endpoints=${ETCD_ENDPOINTS} --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/flanneld/cert/flanneld.pem --key-file=/etc/flanneld/cert/flanneld-key.pem set ${FLANNEL_ETCD_PREFIX}/config '{"Network":"'${CLUSTER_CIDR}'","SubnetLen": 24, "Backend": {"Type": "vxlan"}}'
{"Network":"172.30.0.0/16","SubnetLen": 24, "Backend": {"Type": "vxlan"}}
```

> 重启flanneld服务,恢复正常
```
systemctl daemon-reload && systemctl restart flanneld
```

```
 systemctl status flanneld
● flanneld.service - Flanneld overlay address etcd agent
   Loaded: loaded (/etc/systemd/system/flanneld.service; enabled; vendor preset: disabled)
   Active: active (running) since Tue 2019-11-26 04:02:21 EST; 5s ago
  Process: 54301 ExecStartPost=/opt/k8s/bin/mk-docker-opts.sh -k DOCKER_NETWORK_OPTIONS -d /run/flannel/docker (code=exited, status=0/SUCCESS)
 Main PID: 54294 (flanneld)
    Tasks: 7
   Memory: 18.9M
   CGroup: /system.slice/flanneld.service
           └─54294 /opt/k8s/bin/flanneld -etcd-cafile=/etc/kubernetes/cert/ca.pem -etcd-certfile=/etc/flanneld/cert/flanneld.pem -etcd-keyfile=/etc/flanneld/cert/flan...

Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.936155   54294 main.go:238] Installing signal handlers
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.950943   54294 main.go:353] Found network config - Backend type: vxlan
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.950982   54294 vxlan.go:120] VXLAN config: VNI=1 Port=0 GBP=false DirectRouting=false
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.957841   54294 local_manager.go:201] Found previously leased subnet (172.30.77.0/24), reusing
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.971954   54294 local_manager.go:220] Allocated lease (172.30.77.0/24) to current node (192.168.174.128)
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.972219   54294 main.go:300] Wrote subnet file to /run/flannel/subnet.env
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.972227   54294 main.go:304] Running backend.
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.979256   54294 vxlan_network.go:60] watching for new subnet leases
Nov 26 04:02:20 k8s-node1 flanneld[54294]: I1126 04:02:20.996038   54294 main.go:396] Waiting for 22h59m59.969177096s to renew lease
Nov 26 04:02:21 k8s-node1 systemd[1]: Started Flanneld overlay address etcd agent.
```

```
etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem get /kubernetes/network/config
{"Network":"172.30.0.0/16","SubnetLen": 24, "Backend": {"Type": "vxlan"}}

 etcdctl --ca-file=/etc/kubernetes/cert/ca.pem --cert-file=/etc/etcd/cert/etcd.pem --key-file=/etc/etcd/cert/etcd-key.pem ls /kubernetes/network/subnets
/kubernetes/network/subnets/172.30.49.0-24
/kubernetes/network/subnets/172.30.77.0-24
/kubernetes/network/subnets/172.30.75.0-24
```

```
kubectl cluster-info
Kubernetes master is running at https://192.168.174.127:8443
CoreDNS is running at https://192.168.174.127:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```
