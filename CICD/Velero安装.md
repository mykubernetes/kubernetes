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
restic
restore                #还原
schedule               #定时任务，定时备份
snapshot-location      #快照位置
version                #版本
```

命令行的安装方式
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
