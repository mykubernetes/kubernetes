官方文档  
https://helm.sh/blog/migrate-from-helm-v2-to-helm-v3/  

Helm V3 版本已经发布了第三个 Beta 版本了，由于 V2 和 V3 版本之间的架构变化较大，所以如果我们现在正在使用 V2 版本的话，要迁移到 V3 版本了就有点小麻烦，其中最重要的当然就是数据迁移的问题，为了解决这个版本迁移问题，官方提供了一个名为 helm-2to3 的插件可以来简化我们的迁移工作。  

安装 Helm V3
---
为了能够让Helm V2包还可以继续使用，这里就不直接覆盖，让两个版本版本共存，避免迁移有风险，等v3版本准备好后再移除V2版本  

helm下载地址  
https://github.com/helm/helm/releases  


验证  
```
# helm3 version
version.BuildInfo{Version:"v3.0.0-beta.3", GitCommit:"5cb923eecbe80d1ad76399aee234717c11931d9a", GitTreeState:"clean", GoVersion:"go1.12.9"}

# helm repo list
NAME            URL
stable          http://mirror.azure.cn/kubernetes/charts/
local           http://127.0.0.1:8879/charts

# helm3 repo list
Error: no repositories to show
```  

安装HELM-2TO3插件  
---
1、安装helm-2to3 插件就可以将Helm V2版本的配置和release迁移到Helm V3版本去，安装的Kubernetes对象不会被修改或者删除
```
# helm3 plugin install https://github.com/helm/helm-2to3
Downloading and installing helm-2to3 v0.1.1 ...
https://github.com/helm/helm-2to3/releases/download/v0.1.1/helm-2to3_0.1.1_darwin_amd64.tar.gz
Installed plugin: 2to3
```  

2、查看插件  
```
# helm3 plugin list
NAME    VERSION DESCRIPTION
2to3    0.1.1   migrate Helm v2 configuration and releases in-place to Helm v3

# helm3 2to3
Migrate Helm v2 configuration and releases in-place to Helm v3

Usage:
2to3 [command]

Available Commands:
convert     migrate Helm v2 release in-place to Helm v3
help        Help about any command
move        migrate Helm v2 configuration in-place to Helm v3

Flags:
-h, --help   help for 2to3
Use "2to3 [command] --help" for more information about a command.
```  
插件支持的功能主要有两个部分  
- 迁移Helm V2配置
- 迁移Helm V2 release


迁移Helm V2配置 
---
1、需要迁移Helm V2版本的相关配置和数据目录  
```
# helm3 2to3 move config
[Helm 2] Home directory: /Users/ych/.helm
[Helm 3] Config directory: /Users/ych/Library/Preferences/helm
[Helm 3] Data directory: /Users/ych/Library/helm
[Helm 3] Create config folder "/Users/ych/Library/Preferences/helm" .
[Helm 3] Config folder "/Users/ych/Library/Preferences/helm" created.
[Helm 2] repositories file "/Users/ych/.helm/repository/repositories.yaml" will copy to [Helm 3] config folder "/Users/ych/Library/Preferences/helm/repositories.yaml" .
[Helm 2] repositories file "/Users/ych/.helm/repository/repositories.yaml" copied successfully to [Helm 3] config folder "/Users/ych/Library/Preferences/helm/repositories.yaml" .
[Helm 3] Create data folder "/Users/ych/Library/helm" .
[Helm 3] data folder "/Users/ych/Library/helm" created.
[Helm 2] plugins "/Users/ych/.helm/plugins" will copy to [Helm 3] data folder "/Users/ych/Library/helm/plugins" .
[Helm 2] plugins "/Users/ych/.helm/plugins" copied successfully to [Helm 3] data folder "/Users/ych/Library/helm/plugins" .
[Helm 2] starters "/Users/ych/.helm/starters" will copy to [Helm 3] data folder "/Users/ych/Library/helm/starters" .
[Helm 2] starters "/Users/ych/.helm/starters" copied successfully to [Helm 3] data folder "/Users/ych/Library/helm/starters" .
```  
该操作会迁移  
- Chart starters
- Chart 仓库
- 插件

2、检查下所有的Helm V2下面的插件是否能够在Helm V3下面正常工作，把不起作用的插件删除即可  
```
# helm3 repo list
NAME            URL
stable          http://mirror.azure.cn/kubernetes/charts/
local           http://127.0.0.1:8879/charts

# helm3 plugin list
NAME    VERSION DESCRIPTION
2to3    0.1.1   migrate Helm v2 configuration and releases in-place to Helm v3
push    0.7.1   Push chart package to ChartMuseum
```  
上面的move config命令会创建Helm V3配置和数据目录（如果它们不存在），并将覆盖repositories.yaml文件（如果存在）  

3、该插件还支持将非默认的 Helm V2 主目录以及 Helm V3 配置和数据目录，使用如下配置使用即可  
```
# export HELM_V2_HOME=$HOME/.helm2
# export HELM_V3_CONFIG=$HOME/.helm3
# export HELM_V3_DATA=$PWD/.helm3
# helm3 2to3 move config
```  

迁移 Helm V2 Release
---

1、现在可以开始迁移releases了。查看命令的可用选项  
```
# helm3 2to3 convert -h
migrate Helm v2 release in-place to Helm v3

Usage:
2to3 convert [flags] RELEASE

Flags:
    --delete-v2-releases       v2 releases are deleted after migration. By default, the v2 releases are retained
    --dry-run                  simulate a convert
-h, --help                     help for convert
-l, --label string             label to select tiller resources by (default "OWNER=TILLER")
-s, --release-storage string   v2 release storage type/object. It can be 'secrets' or 'configmaps'. This is only used with the 'tiller-out-cluster' flag (default "secrets")
-t, --tiller-ns string         namespace of Tiller (default "kube-system")
    --tiller-out-cluster       when  Tiller is not running in the cluster e.g. Tillerless
```  

2、查看下Helm V2下面的release，然后选择一个来测试下迁移  
```
# helm list
NAME        REVISION    UPDATED                     STATUS      CHART               APP VERSION NAMESPACE
minio        1           Wed Sep 11 11:47:51 2019    DEPLOYED    minio-2.5.13    RELEASE.2019-08-07T01-59-21Z    argo
redis        1           Wed Sep 11 14:52:57 2019    DEPLOYED    redis-9.1.7         5.0.5       redis
```  

3、空跑测试，查看是否有报错，不真正运行通过--dry-run模式  
```
# helm3 2to3 convert --dry-run minio
NOTE: This is in dry-run mode, the following actions will not be executed.
Run without --dry-run to take the actions described below:
Release "minio" will be converted from Helm 2 to Helm 3.
[Helm 3] Release "minio" will be created.
[Helm 3] ReleaseVersion "minio.v1" will be created.
```  

4、未发现报错直接运行  
```
# helm3 2to3 convert minio
Release "minio" will be converted from Helm 2 to Helm 3.
[Helm 3] Release "minio" will be created.
[Helm 3] ReleaseVersion "minio.v1" will be created.
[Helm 3] ReleaseVersion "minio.v1" created.
[Helm 3] Release "minio" created.
Release "minio" was converted successfully from Helm 2 to Helm 3. Note: the v2 releases still remain and should be removed to avoid conflicts with the migrated v3 releases.
```  

5、迁移完成后，然后检查下是否成功  
```
# helm list
NAME        REVISION    UPDATED                     STATUS      CHART               APP VERSION NAMESPACE
minio        1           Wed Sep 11 11:47:51 2019    DEPLOYED    minio-2.5.13    RELEASE.2019-08-07T01-59-21Z    argo
redis        1           Wed Sep 11 14:52:57 2019    DEPLOYED    redis-9.1.7         5.0.5       redis

# helm3 list
NAME     NAMESPACE   REVISION    UPDATED                                 STATUS      CHART
```  

6、可以看到执行helm3 list命令并没有任何release信息，这是因为迁移的minio这个release是被安装在argo这个命名空间下面的，所以需要指定命名空间才可以看到  
```
# helm3 list -n argo
NAME     NAMESPACE   REVISION    UPDATED                                 STATUS      CHART
minio    argo        1           2019-09-11 03:47:51.239461137 +0000 UTC deployed    minio-2.5.13
```  
注意：由于没有指定 --delete-v2-releases选项，所以Helm V2 minio这个release信息还是存在，可以在以后使用kubectl进行删除。准备好迁移所有的releases的时候，可以循环helm list里面的所有release来自动的将每个Helm V2 release迁移到Helm V3版本去  

7、如果正在使用Tillerless Helm V2，只需要指定 --tiller-out-cluster选项来迁移release即可  
```
# helm3 2to3 convert minio --tiller-out-cluster
```  

清理 Helm V2 数据
---
最后清理之前版本的旧数据，这并不是必须的，但是还是建议清理，可以避免一些冲突。清理Helm V2的数据比较简单  
- 删除主文件夹 ~/.helm
- 如果没有使用 --delete-v2-releases选项，那么旧使用 kubectl 工具来删除 Tiller releases 数据
- 卸载 Tiller




可用性发生了几次CLI更改，包括  
- helm inspect 现在改成 helm show
- helm fetch 现在改成 helm pull
- helm delete 现在改成 helm uninstall，而不需要使用--purge参数，如果想保留历史记录，helm uninstall是使用--keep-history





