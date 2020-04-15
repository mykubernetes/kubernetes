安装CLI
- 下载链接 https://github.com/vmware-tanzu/velero/releases/tag/v1.2.0
- 下载插件 https://github.com/vmware-tanzu/velero-plugin-for-aws/releases
- 解压缩软件，并把它放到可执行路径，如/usr/local/bin

1、安装和配置服务器端组件

支持两种方式安装服务器端组件

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
    --backup-location-config region=US,s3ForcePathStyle="true",s3Url=http://192.168.20.82
    --secret-file ./credentials-velero \
     

```
