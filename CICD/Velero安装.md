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
    --velero-pod-cpu-request 200m \
    --velero-pod-mem-request 200Mi \
    --velero-pod-cpu-limit 200m \
    --velero-pod-mem-limit 200Mi \
    --namespace velero
    --use-volume-snapshots=true \
#    --use-restic \                      #注释的为可选参数
#    --restic-pod-cpu-request 200m \
#    --restic-pod-mem-request 200Mi \
#    --restic-pod-cpu-limit 200m \
#    --restic-pod-mem-limit 200Mi \
    --secret-file ./credentials-velero 
```
- --provider 指定提供者
- --plugins 根据使用的不同对象存储指定不同的插件
- --bucket 指定bucket名
- --backup-location-config 指定备份位置
- --snapshot-loation-config 指定快照位置
- --use-restic 开启restic集成，默认不开启，如果运行了velero install未开启restic，可以再运行一次开启该集成的命令安装
- --namespace 指定要部署的名称空间
- --secret-file 验证机制，文件
- --no-secret 不使用验证
- --velero-pod-cpu-request velero使用的cpu or mem 的资源
- --restic-pod-cpu-request restic使用的cpu or mem 的资源
- --dry-run -o yaml 不进行创建，只显示yaml文件
在客户端命令行上指定名称空间
```
velero client config set namespace=<NAMESPACE_VALUE>
```

Restic可以将本地数据加密后传输到指定的仓库。支持的仓库有 Local、SFTP、Aws S3、Minio、OpenStack Swift、Backblaze B2、Azure BS、Google Cloud storage、Rest Server。

restic项目地址：https://github.com/restic/restic
```
--use-restic
--use-volume-snapshots=true
```

3、安装完后查看namespace及pod
```
kubectl get ns |grep velero
velero            Active          7s

kubectl get pods -n velero 
NAME                         READY    STATUS        RESTARTS       AGE
velero-65458bc75c-cv96dd     1/1      Running       0              23s
```

4、查看创建的CRD
```
# kubectl -n velero get crds -l component=velero
NAME                                CREATED AT
backups.velero.io                   2019-08-28T03:19:56Z
backupstoragelocations.velero.io    2019-08-28T03:19:56Z
deletebackuprequests.velero.io      2019-08-28T03:19:56Z
downloadrequests.velero.io          2019-08-28T03:19:56Z
podvolumebackups.velero.io          2019-08-28T03:19:56Z
podvolumerestores.velero.io         2019-08-28T03:19:56Z
resticrepositories.velero.io        2019-08-28T03:19:56Z
restores.velero.io                  2019-08-28T03:19:56Z
schedules.velero.io                 2019-08-28T03:19:56Z
serverstatusrequests.velero.io      2019-08-28T03:19:56Z
volumesnapshotlocations.velero.io   2019-08-28T03:19:56Z
```

5、Velero删除
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

1、创建备份的基本命令语法
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

2、恢复一个备份数据的基本命令语法
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

使用 Velero 进行数据备份和恢复
---

部署一个测试nginx资源
---
```
---
apiVersion: v1
kind: Namespace
metadata:
  name: nginx-example
  labels:
    app: nginx

---
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: nginx-example
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - image: nginx:1.7.9
        name: nginx
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  labels:
    app: nginx
  name: my-nginx
  namespace: nginx-example
spec:
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: nginx
  type: LoadBalancer
```

备份
---
可以全量备份，也可以只备份需要备份的一个namespace,本处只备份一个namespace：nginx-example
```
velero backup create nginx-example-backup --include-namespaces nginx-example

Backup request "nginx-example-backup" submitted successfully.
Run `velero backup describe nginx-example-backup` or `velero backup logs nginx-example-backup` for more details.
```

查看当前状态
```
# namespace nginx-example仍然存在
kubectl get ns
NAME            STATUS   AGE
default         Active   2d22h
kube-public     Active   2d22h
kube-system     Active   2d22h
nginx-example   Active   8m34s
velero          Active   120m

# nginx-example下面pod的相关信息
kubectl get po -n nginx-example -o wide
NAME                                READY   STATUS    RESTARTS   AGE     IP             NODE                           NOMINATED NODE
nginx-deployment-5c689d88bb-855h8   1/1     Running   0          2m31s   172.20.0.114   cn-zhangjiakou.192.168.1.144   <none>
nginx-deployment-5c689d88bb-k5j9z   1/1     Running   0          2m31s   172.20.0.115   cn-zhangjiakou.192.168.1.144   <none>

# nginx-example下面deployment的相关信息
kubectl get deployment -n nginx-example -o wide
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS   IMAGES        SELECTOR
nginx-deployment   2         2         2            2           5m2s   nginx        nginx:1.7.9   app=nginx

# nginx-example下面service的相关信息
kubectl get svc -n nginx-example -o wide
NAME       TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)        AGE     SELECTOR
my-nginx   LoadBalancer   172.21.9.159   47.92.44.156   80:32088/TCP   6m36s   app=nginx
```

模拟一次误操作导致namespace nginx-example被误删
```
kubectl delete namespaces nginx-example
```

恢复
---
使用velero restore命令来恢复之前的备份
```
velero  restore create --from-backup nginx-example-backup

Restore request "nginx-example-backup-20190523200227" submitted successfully.
Run `velero restore describe nginx-example-backup-20190523200227` or `velero restore logs nginx-example-backup-20190523200227` for more details.
```

检查下namespace nginx-example及其下面的资源是否被恢复
```
# 检查下namespace nginx-example是否已被创建
kubectl get ns
NAME            STATUS   AGE
default         Active   2d22h
kube-public     Active   2d22h
kube-system     Active   2d22h
nginx-example   Active   68s
velero          Active   112m

# 检查下pod 
kubectl get po -n nginx-example -o wide
NAME                                READY   STATUS    RESTARTS   AGE    IP             NODE                           NOMINATED NODE
nginx-deployment-5c689d88bb-855h8   1/1     Running   0          3m2s   172.20.0.131   cn-zhangjiakou.192.168.1.145   <none>
nginx-deployment-5c689d88bb-k5j9z   1/1     Running   0          3m2s   172.20.0.132   cn-zhangjiakou.192.168.1.145   <none>

# nginx-example下面deployment的相关信息
kubectl get deployment -n nginx-example -o wide
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS   IMAGES        SELECTOR
nginx-deployment   2         2         2            2           4m52s   nginx        nginx:1.7.9   app=nginx

# nginx-example下面service的相关信息
kubectl get svc -n nginx-example -o wide
NAME       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE    SELECTOR
my-nginx   LoadBalancer   172.21.3.239   39.98.8.5     80:30351/TCP   7m9s   app=nginx
```
可以看到resource name都保持不变，但是相关的ip，nodeport，LB地址等都会重新分配


验证恢复的形态是什么样的
---
额外部署一个tomcat的deployment
```
kubectl get deployment -n nginx-example
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   2         2         2            2           3m23s
tomcat             2         2         2            2           27s
```
做一次restore，观察下是否会删除掉tomcat这个deployment
```
velero  restore create --from-backup nginx-example-backup

kubectl get deployment -n nginx-example
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   2         2         2            2           6m32s
tomcat             2         2         2            2           3m36s
```
可以看到，restore的行为不是覆盖

把最初backup中存在的nginx删除掉
---
```
kubectl delete deployment nginx-deployment -n nginx-example
deployment.extensions "nginx-deployment" deleted

kubectl get deployment -n nginx-example
NAME     DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
tomcat   2         2         2            2           6m49s
```
再来一次restore,之前backup中有nginx，没有tomcat，那restore之后是什么样
```
velero  restore create --from-backup nginx-example-backup

kubectl get deployment -n nginx-example
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   2         2         2            2           3s
tomcat             2         2         2            2           8m33s
```

将nginx的image版本升级成latest，那在restore之后是什么样
---
```
# 升级nginx的image从1.7.9到latest，并查看当前的image版本
kubectl get deployment -n nginx-example -o wide
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS   IMAGES          SELECTOR
nginx-deployment   2         2         2            2           2m29s   nginx        nginx:latest    app=nginx
tomcat             2         2         2            2           10m     tomcat       tomcat:latest   app=tomcat

# restore backup
velero  restore create --from-backup nginx-example-backup
# 再来看下nginx的image版本，并没有恢复到最初的版本
kubectl get deployment -n nginx-example -o wide
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS   IMAGES          SELECTOR
nginx-deployment   2         2         2            2           3m15s   nginx        nginx:latest    app=nginx
tomcat             2         2         2            2           11m     tomcat       tomcat:latest   app=tomcat
```
结论：velero恢复不是直接覆盖，而是会恢复当前集群中不存在的resource，已有的resource不会回滚到之前的版本，如需要回滚，需在restore之前提前删除现有的resource。

备份持久数据卷
---
1、备份恢复持久卷
```
# velero backup create nginx-backup-volume --snapshot-volumes --include-namespaces nginx-example
```
该备份会在集群所在region给云盘创建快照（当前还不支持NAS和OSS存储），快照恢复云盘只能在同region完成。

2、恢复命令
```
# velero restore create --from-backup nginx-backup-volume --restore-volumes
```

使用Restic给带有PVC的Pod进行备份，必须先给Pod加上注解。
---
基本语法：
```
# kubectl -n YOUR_POD_NAMESPACE annotate pod/YOUR_POD_NAME backup.velero.io/backup-volumes=YOUR_VOLUME_NAME_1,YOUR_VOLUME_NAME_2,...
```
1、使用Elasticsearch的Pod为例，为Elasticsearch的annotate打标签
```
# kubectl -n elasticsearch annotate pod elasticsearch-master-0 backup.velero.io/backup-volumes=elasticsearch-master

# kubectl get pod -n elasticsearch elasticsearch-master-0 -o jsonpath='{.metadata.annotations}'
map[backup.velero.io/backup-volumes:elasticsearch-master]
```


2、创建一个备份
```
# velero create backup es --include-namespaces=elasticsearch
```
注：Restic会使用 Path Style，而阿里云禁止Path style需要使用Virtual-Hosted，所以暂时备份没有办法备份 PV 到 OSS。

备份创建成功后会创建一个名为 backups.velero.io 的 CRD 对象。

3、恢复一个备份数据
```
# velero restore create back --from-backup es
```
恢复成功后，同样也会创建一个 restores.velero.io CRD 对象。

4、备份资源查看
```
# velero backup get
```

5、查看可恢复备份
```
# velero restore get
```

6、删除备份
```
# 通过命令直接删除
velero delete backups <BACKUP_NAME>

# 设置备份自动过期，在创建备份时，加上TTL参数
velero backup create <BACKUP-NAME> --ttl <DURATION>
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
# velero schedule get
```



使用 Velero 进行集群数据迁移
---
在集群1上做一个备份：
```
# velero backup create <BACKUP-NAME> --snapshot-volumes
```
在集群2上做一个恢复：
```
# velero restore create --from-backup <BACKUP-NAME> --restore-volumes
```

