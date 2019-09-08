1、定义chart  
```
# helm create mychart
Creating mychart
# tree mychart/
mychart/
├── charts
├── Chart.yaml
├── templates
│ ├── deployment.yaml
│ ├── _helpers.tpl
│ ├── ingress.yaml
│ ├── NOTES.txt
│ └── service.yaml
└── values.yaml
2 directories, 7 files
```  
- NOTES.txt：chart 的 “帮助⽂本”。这会在⽤户运⾏ helm install 时显示给⽤户。
- deployment.yaml：创建 Kubernetes deployment 的基本 manifest
- service.yaml：为 deployment 创建 service 的基本 manifest
- ingress.yaml: 创建 ingress 对象的资源清单⽂件
- _helpers.tpl：放置模板助⼿的地⽅，可以在整个 chart 中重复使⽤


2、内置对象  
- Release：这个对象描述了 release 本身。它⾥⾯有⼏个对象：
  - Release.Name：release 名称
  - Release.Time：release 的时间
  - Release.Namespace：release 的 namespace（如果清单未覆盖）
  - Release.Service：release 服务的名称（始终是 Tiller）。
  - Release.Revision：此 release 的修订版本号，从1开始累加。
  - Release.IsUpgrade：如果当前操作是升级或回滚，则将其设置为 true。
  - Release.IsInstall：如果当前操作是安装，则设置为 true。
- Values：从 values.yaml  ⽂件和⽤户提供的⽂件传⼊模板的值。默认情况下，Values 是空的。
- Chart： Chart.yaml  ⽂件的内容。所有的 Chart 对象都将从该⽂件中获取。chart 指南中Charts Guide列出了可⽤字段，可以前往查看。
- Files：这提供对 chart 中所有⾮特殊⽂件的访问。虽然⽆法使⽤它来访问模板，但可以使⽤它来访问 chart 中的其他⽂件。请参阅 "访问⽂件" 部分。
  - Files.Get 是⼀个按名称获取⽂件的函数（.Files.Get config.ini）
  - Files.GetBytes 是将⽂件内容作为字节数组⽽不是字符串获取的函数。这对于像图⽚这样的东⻄很有⽤。
- Capabilities：这提供了关于 Kubernetes 集群⽀持的功能的信息。
  - Capabilities.APIVersions 是⼀组版本信息。
  - Capabilities.APIVersions.Has $version 指示是否在群集上启⽤版本（batch/v1）。
  - Capabilities.KubeVersion 提供了查找 Kubernetes 版本的⽅法。它具有以下值：Major，Minor，GitVersion，GitCommit，GitTreeState，BuildDate，GoVersion，Compiler，和Platform。
  - Capabilities.TillerVersion 提供了查找 Tiller 版本的⽅法。它具有以下值：SemVer，GitCommit，和 GitTreeState。
- Template：包含有关正在执⾏的当前模板的信息
- Name：到当前模板的⽂件路径（例如 mychart/templates/mytemplate.yaml）
- BasePath：当前 chart 模板⽬录的路径（例如 mychart/templates）。
