1、概述

Velero是一个针对kubernetes集群资源和持久卷的一个备份和还原工具，可以运行在公有云或私有云中的应用。

它的主要由以下三个功能：
- 备份kubernetes的机器，并在丢失时恢复。
- 迁移集群的资源到另一个集群。
- 复制生成的集群到开发和测试的集群。

Velero可运行两种方式运行：
- 服务器： 运行在集群上
- 命令行工具： 运行在本地

Velero使用对象存储去存储备份，它还集成支持后端存储系统的快照功能。兼容的存储提供商参考：  
https://velero.io/docs/v1.2.0/supported-providers/

安装CLI
---
- 下载链接 https://github.com/vmware-tanzu/velero/releases/tag/v1.2.0
- 下载插件 https://github.com/vmware-tanzu/velero-plugin-for-aws/releases
- 解压缩软件，并把它放到可执行路径，如/usr/local/bin

1、安装和配置服务器端组件

支持两种方式安装服务器端组件

```
tar xvf velero-v1.2.0-linux-amd64.tar.gz
chmod u+x velero-v1.2.0-linux-amd64/velero
mv velero-v1.2.0-linux-amd64/velero /usr/local/bin/
```

命令介绍
```
backup                 #备份
backup-location        #备份的路径
bug
client                 #客户端命令
completion
create                 #创建资源
delete                 #删除资源
describe               #查看资源相关信息
get                    #查看有哪些备份
help                   #帮助
install                #安装velero
plugin                 #指定插件
restic                 #备份pv数据
restore                #还原
schedule               #定时任务，定时备份
snapshot-location      #快照位置
version                #版本
```

2、命令行的安装方式
```
# 创建文件名为credentials-velero
cat credentials-velero
[default]
aws_access_key_id=NS5RAUUR0GJ9P24Y0Q19
aws_secret_access_key=GmAs5aecYNqVwRZBIoak0VEXYw9uLTEJYBD7CmGj
```

```
velero install \
    --provider aws \
    --plugins velero/velero-plugin-for-aws:v1.0.0 \
    --bucket first-bucket \
    --backup-location-config region=US,s3ForcePathStyle="true",s3Url=http://192.168.20.82 \
    --snapshot-loation-config region=US \
    --secret-file ./credentials-velero 
```
- --provider 指定提供者
- --bucket 指定bucket名
- --backup-location-config 指定备份位置
- --namespace 指定要部署的名称空间
在客户端命令行上指定名称空间
```
velero client config set namespace=<NAMESPACE_VALUE>
```


3、安装完后查看namespace及pod
```
kubectl get ns |grep velero
velero            Active          7s

kubectl get pods -n velero 
NAME                         READY    STATUS        RESTARTS       AGE
velero-65458bc75c-cv96dd     1/1      Running       0              23s
```

4、Velero删除
```
kubectl delete namespace/velero clusterrolebinding/velero
kubectl delete crds -l component=velero
```

使用
---

添加卷提供商到Velero
```
velero plugin add <registry/image:version>
```

添加卷快照提供商
```
velero snapshot-location-create <NAME>\
--provider <PROVIDER_NAME> \
[--config <PROVIDER_CONFIGN>]  #可选
```

使用 Velero 进行数据备份和恢复
---

给 Pod 加注解

使用 Restic 给带有 PVC 的 Pod 进行备份，必须先给 Pod 加上注解。

先看一看基本语法：
```
$ kubectl -n YOUR_POD_NAMESPACE annotate pod/YOUR_POD_NAME backup.velero.io/backup-volumes=YOUR_VOLUME_NAME_1,YOUR_VOLUME_NAME_2,...
```
在来看一个实例，这里使用一个 Elasticsearch 的 Pod 为例：
```
$ kubectl -n elasticsearch annotate pod elasticsearch-master-0 backup.velero.io/backup-volumes=elasticsearch-master
$ kubectl get pod -n elasticsearch elasticsearch-master-0 -o jsonpath='{.metadata.annotations}'
map[backup.velero.io/backup-volumes:elasticsearch-master]
```



备份排除项目
---
可为资源添加指定标签，添加标签的资源在备份的时候被排除。
```
# 添加标签
kubectl label -n <ITEM_NAMESPACE> <RESOURCE>/<NAME> velero.io/exclude-from-backup=true
# 为 default namespace 添加标签
kubectl label -n default namespace/default velero.io/exclude-from-backup=true
```


1、基本命令语法
```
$ velero create backup NAME [flags]

--exclude-namespaces stringArray                  # 剔除 namespace
--exclude-resources stringArray                   # 剔除资源类型
--include-cluster-resources optionalBool[=true]   # 包含集群资源类型 
--include-namespaces stringArray                  # 包含 namespace
--include-resources stringArray                   # 包含 namespace 资源类型
--labels mapStringString                          # 给这个备份加上标签
-o, --output string                               Output display format. For create commands, display the object but do not send it to the server. Valid formats are 'table', 'json', and 'yaml'. 'table' is not valid for the install command.

-l, --selector labelSelector                      # 对指定标签的资源进行备份
--snapshot-volumes optionalBool[=true]            # 对 PV 创建快照
--storage-location string                         # 指定备份的位置
--ttl duration                                    # 备份数据多久删掉
--volume-snapshot-locations strings               # 指定快照的位置，也就是哪一个公有云驱动
```

创建一个备份

这里同样以上面提到的 elasticsearch 为例。
```
$ velero create backup es --include-namespaces=elasticsearch
```
注：Restic 会使用 Path Style，而阿里云禁止 Path style 需要使用 Virtual-Hosted，所以暂时备份没有办法备份 PV 到 OSS。

备份创建成功后会创建一个名为 backups.velero.io 的 CRD 对象。

恢复一个备份数据
---
基本命令语法
```
$ velero restore create [RESTORE_NAME] [--from-backup BACKUP_NAME | --from-schedule SCHEDULE_NAME] [flags]

      --exclude-namespaces stringArray                  namespaces to exclude from the restore
      --exclude-resources stringArray                   resources to exclude from the restore, formatted as resource.group, such as storageclasses.storage.k8s.io
      --from-backup string                              backup to restore from
      --from-schedule string                            schedule to restore from
  -h, --help                                            help for create
      --include-cluster-resources optionalBool[=true]   include cluster-scoped resources in the restore
      --include-namespaces stringArray                  namespaces to include in the restore (use '*' for all namespaces) (default *)
      --include-resources stringArray                   resources to include in the restore, formatted as resource.group, such as storageclasses.storage.k8s.io (use '*' for all resources)
      --label-columns stringArray                       a comma-separated list of labels to be displayed as columns
      --labels mapStringString                          labels to apply to the restore
      --namespace-mappings mapStringString              namespace mappings from name in the backup to desired restored name in the form src1:dst1,src2:dst2,...
  -o, --output string                                   Output display format. For create commands, display the object but do not send it to the server. Valid formats are 'table', 'json', and 'yaml'. 'table' is not valid for the install command.
      --restore-volumes optionalBool[=true]             whether to restore volumes from snapshots
  -l, --selector labelSelector                          only restore resources matching this label selector (default <none>)
      --show-labels                                     show labels in the last column
  -w, --wait
```


恢复一个备份数据
```
$ velero restore create back --from-backup es
```
恢复成功后，同样也会创建一个 restores.velero.io CRD 对象。

使用 Velero 进行集群数据迁移
---
首先，在集群 1 中创建备份（默认 TTL 是 30 天，你可以使用 --ttl 来修改）：
```
$ velero backup create <BACKUP-NAME>
```
然后，为集群 2 配置与集群 1 相同的备份位置 BackupStorageLocations 和快照路径 VolumeSnapshotLocations。

并确保 BackupStorageLocations 是只读的（使用 --access-mode=ReadOnly）。接下来，稍微等一会（默认的同步时间为 1 分钟），等待 Backup 对象创建成功。
```
# The default sync interval is 1 minute, so make sure to wait before checking.
# You can configure this interval with the --backup-sync-period flag to the Velero server.
$ velero backup describe <BACKUP-NAME>
```
最后，执行数据恢复：
```
$ velero restore create --from-backup <BACKUP-NAME>
$ velero restore get
$ velero restore describe <RESTORE-NAME-FROM-GET-COMMAND>
```

备份删除
```
velero delete backups <BACKUP_NAME>
```

备份资源查看
```
velero backup get
```

查看可恢复备份
```
$ velero restore get
```

定期备份
---

创建定期备份
```
# 每日1点进行备份
velero create schedule <SCHEDULE NAME> --schedule="0 1 * * *"
# 每日1点进行备份，备份保留48小时
velero create schedule <SCHEDULE NAME> --schedule="0 1 * * *" --ttl 48h
# 每6小时进行一次备份
velero create schedule <SCHEDULE NAME> --schedule="@every 6h"
# 每日对 web namespace 进行一次备份
velero create schedule <SCHEDULE NAME> --schedule="@every 24h" --include-namespaces web
```

查看定时备份
```
$ velero schedule get
```
