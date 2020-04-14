备份 etcd 集群  
---
https://mp.weixin.qq.com/s/SR4ju03uMM28wDHBdNmVDA

所有 Kubernetes 对象都存储在 etcd 上。定期备份 etcd 集群数据对于在灾难场景（例如丢失所有主节点）下恢复 Kubernetes 集群非常重要。快照文件包含所有 Kubernetes 状态和关键信息。为了保证敏感的 Kubernetes 数据的安全，可以对快照文件进行加密。  

一、备份 etcd 集群可以通过两种方式完成：etcd 内置快照和卷快照。  
1、内置快照  
etcd 支持内置快照，因此备份 etcd 集群很容易。快照可以从使用 etcdctl snapshot save 命令的活动成员中获取，也可以通过从 etcd 数据目录 复制 member/snap/db 文件，该 etcd 数据目录目前没有被 etcd 进程使用。datadir 位于 $DATA_DIR/member/snap/db。获取快照通常不会影响成员的性能。  

下面是一个示例，用于获取 $ENDPOINT 所提供的键空间的快照到文件 snapshotdb：  
```
ETCDCTL_API=3 etcdctl --endpoints $ENDPOINT snapshot save snapshotdb
# exit 0

# 验证快照
ETCDCTL_API=3 etcdctl --write-out=table snapshot status snapshotdb
+----------+----------+------------+------------+
|   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
+----------+----------+------------+------------+
| fe01cf57 |       10 |          7 | 2.1 MB     |
+----------+----------+------------+------------+
```  

2、卷快照  
如果 etcd 运行在支持备份的存储卷（如 Amazon 弹性块存储、Aliyun）上，则可以通过获取存储卷的快照来备份 etcd 数据。  


备份与恢复
---
1、备份示例
```
# 分别在etcd集群执行如下命令
mkdir -p /data/apps-backup/etcd

export ETCDCTL_API=3
etcdctl --endpoints="https://127.0.0.1:2379" --cert=/data/apps/etcd/ssl/etcd.pem --key=/data/apps/etcd/ssl/etcd-key.pem --cacert=/data/apps/etcd/ssl/etcd-ca.pem   snapshot save  /data/apps-backup/etcd/`hostname`-etcd_`date +%Y%m%d%H%M`.db


[root@ziji-work-etcd0-apiserver-192-168-1-12 etcd]# ls -l /data/apps-backup/etcd/
total 27200
-rw-r--r-- 1 root root 13922336 Jul 22 09:59 ziji-work-etcd0-apiserver-192-168-1-12-etcd_201907220959.db
-rw-r--r-- 1 root root 13922336 Jul 22 10:01 ziji-work-etcd0-apiserver-192-168-1-12-etcd_201907221001.db
```  

2、恢复  
查看etcd集群信息  
```
export ETCDCTL_API=3

etcdctl --endpoints="https://127.0.0.1:2379" --cert=/data/apps/etcd/ssl/etcd.pem --key=/data/apps/etcd/ssl/etcd-key.pem --cacert=/data/apps/etcd/ssl/etcd-ca.pem member list
399b596d3999ba01, started, etcd2, https://192.168.1.14:2380, https://127.0.0.1:2379,https://192.168.1.14:2379
7b170c49403f28a9, started, etcd0, https://192.168.1.12:2380, https://127.0.0.1:2379,https://192.168.1.12:2379
be31245426ce45a9, started, etcd1, https://192.168.1.13:2380, https://127.0.0.1:2379,https://192.168.1.13:2379
```  

三、测试  
1、停止Kubernetes集群中的kube-apiserver组件和etcd组件  
```
systemctl stop kube-apiserver
systemctl stop etcd
```  

2、将集群内宿主机现有的etcd目录删除，或使用mv命令对目录进行改名
```
mv /var/lib/etcd/default.etcd  /var/lib/etcd/default.etcd.bak
```  

3、恢复数据(分别在三个节点执行如下命令)  
```
export ETCDCTL_API=3
etcdctl snapshot restore  etcd_2019_07_22.db \
--endpoints=127.0.0.1:2379 \
--name=etcd0 \
--cert=/data/apps/etcd/ssl/etcd.pem \
--key=/data/apps/etcd/ssl/etcd-key.pem \
--cacert=/data/apps/etcd/ssl/etcd-ca.pem \
--initial-advertise-peer-urls=https://127.0.0.1:2380 \
--initial-cluster-token=BigBoss \
--initial-cluster=etcd0=https://192.168.1.12:2380,etcd1=https://192.168.1.13:2380,etcd2=https://192.168.1.14:2380 \
--data-dir=/var/lib/etcd/default.etcd
```  
注意： 恢复后的文件需要修改权限为 etcd:etcd ，并启动etcd进程  


4、检查数据是否恢复  
```
使用kubectl查看资源对象是否已恢复或直接get all
kubectl get all --all-namespace
```  

四、备份脚本  
```
#!/bin/bash
# etcd 3.2备份脚本
# create: 2019/07/22 10:00
# authory: cheng.mi

BACKUP_DIR="/data/apps-backup/etcd"
export ETCDCTL_API=3

etcdctl --endpoints="https://127.0.0.1:2379" \
--cert=/data/apps/etcd/ssl/etcd.pem \
--key=/data/apps/etcd/ssl/etcd-key.pem \
--cacert=/data/apps/etcd/ssl/etcd-ca.pem   snapshot save  $BACKUP_DIR/`hostname`-etcd_`date +%Y%m%d%H%M`.db

if [ -d $BACKUP_DIR ]; then
   cd ${BACKUP_DIR} && find . -mtime +15 |xargs rm -f {} \;
fi
```  
