

## 3.1 为什么需要Helm？

K8S上的应用对象，都是由特定的资源描述组成，包括deployment、service等。都保存各自文件中或者集中写到一个配置文件。然后kubectl apply –f 部署。

![image](https://k8s-1252881505.cos.ap-beijing.myqcloud.com/k8s-2/yaml-all.png)

如果应用只由一个或几个这样的服务组成，上面部署方式足够了。

而对于一个复杂的应用，会有很多类似上面的资源描述文件，例如微服务架构应用，组成应用的服务可能多达十个，几十个。如果有更新或回滚应用的需求，可能要修改和维护所涉及的大量资源文件，而这种组织和管理应用的方式就显得力不从心了。

且由于缺少对发布过的应用版本管理和控制，使Kubernetes上的应用维护和更新等面临诸多的挑战，主要面临以下问题：

1. **如何将这些服务作为一个整体管理**
2. **这些资源文件如何高效复用**
3. **不支持应用级别的版本管理**

## 3.2 Helm 介绍

Helm是一个Kubernetes的包管理工具，就像Linux下的包管理器，如yum/apt等，可以很方便的将之前打包好的yaml文件部署到kubernetes上。

Helm有两个重要概念：

- **helm：**一个命令行客户端工具，主要用于Kubernetes应用chart的创建、打包、发布和管理。

- **Chart：**应用描述，一系列用于描述 k8s 资源相关文件的集合。
- **Release：**基于Chart的部署实体，一个 chart 被 Helm 运行后将会生成对应的一个 release；将在k8s中创建出真实运行的资源对象。

## 3.3 Helm v3 变化

**2019年11月13日，** Helm团队发布 `Helm v3 `的第一个稳定版本。

**该版本主要变化如下：**

### 1、 架构变化

**最明显的变化是 `Tiller `的删除**

![](https://k8s-1252881505.cos.ap-beijing.myqcloud.com/k8s-2/helm-arch.png)



### 2、`Release`名称可以在不同命名空间重用

### 3、支持将 Chart 推送至 Docker 镜像仓库中  

### 4、使用JSONSchema验证chart values  

### 5、其他

1）为了更好地协调其他包管理者的措辞 `Helm CLI `个别更名

```
helm delete` 更名为 `helm uninstall
helm inspect` 更名为 `helm show
helm fetch` 更名为 `helm pull
```

但以上旧的命令当前仍能使用。

2）移除了用于本地临时搭建 `Chart Repository `的 `helm serve` 命令。

3）自动创建名称空间

在不存在的命名空间中创建发行版时，Helm 2创建了命名空间。Helm 3遵循其他Kubernetes对象的行为，如果命名空间不存在则返回错误。

4） 不再需要`requirements.yaml`, 依赖关系是直接在`chart.yaml`中定义。 

## 3.4 Helm客户端

### 1、部署Helm客户端

Helm客户端下载地址：https://github.com/helm/helm/releases

解压移动到/usr/bin/目录即可。

```
wget https://get.helm.sh/helm-v3.0.0-linux-amd64.tar.gz
tar zxvf helm-v3.0.0-linux-amd64.tar.gz 
mv linux-amd64/helm /usr/bin/
```

### 2、Helm常用命令

| **命令**   | **描述**                                                     |
| ---------- | ------------------------------------------------------------ |
| create     | 创建一个chart并指定名字                                      |
| dependency | 管理chart依赖                                                |
| get        | 下载一个release。可用子命令：all、hooks、manifest、notes、values |
| history    | 获取release历史                                              |
| install    | 安装一个chart                                                |
| list       | 列出release                                                  |
| package    | 将chart目录打包到chart存档文件中                             |
| pull       | 从远程仓库中下载chart并解压到本地  # helm pull stable/mysql --untar |
| repo       | 添加，列出，移除，更新和索引chart仓库。可用子命令：add、index、list、remove、update |
| rollback   | 从之前版本回滚                                               |
| search     | 根据关键字搜索chart。可用子命令：hub、repo                   |
| show       | 查看chart详细信息。可用子命令：all、chart、readme、values    |
| status     | 显示已命名版本的状态                                         |
| template   | 本地呈现模板                                                 |
| uninstall  | 卸载一个release                                              |
| upgrade    | 更新一个release                                              |
| version    | 查看helm客户端版本                                           |

### 3、配置国内Chart仓库

- 微软仓库（http://mirror.azure.cn/kubernetes/charts/）这个仓库强烈推荐，基本上官网有的chart这里都有。
- 阿里云仓库（https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts  ）
- 官方仓库（https://hub.kubeapps.com/charts/incubator）官方chart仓库，国内有点不好使。

添加存储库：

```
helm repo add stable http://mirror.azure.cn/kubernetes/charts
helm repo add aliyun https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts 
helm repo update
```

查看配置的存储库：

```
helm repo list
helm search repo stable
```

一直在stable存储库中安装charts，你可以配置其他存储库。

删除存储库：

```
helm repo remove aliyun
```

## 3.5 Helm基本使用

主要介绍三个命令：

- chart install

- chart update

- chart rollback

### 1、使用chart部署一个应用

查找chart：

```
# helm search repo
# helm search repo mysql
```

为什么mariadb也在列表中？因为他和mysql有关。

查看chart信息：

```
# helm show chart stable/mysql
```

安装包：

```
# helm install db stable/mysql
```

查看发布状态：

```
# helm status db 
```

### 2、安装前自定义chart配置选项

上面部署的mysql并没有成功，这是因为并不是所有的chart都能按照默认配置运行成功，可能会需要一些环境依赖，例如PV。

所以我们需要自定义chart配置选项，安装过程中有两种方法可以传递配置数据：

- --values（或-f）：指定带有覆盖的YAML文件。这可以多次指定，最右边的文件优先
- --set：在命令行上指定替代。如果两者都用，--set优先级高

--values使用，先将修改的变量写到一个文件中

```
# helm show values stable/mysql
# cat config.yaml 
persistence:
  enabled: true
  storageClass: "managed-nfs-storage"
  accessMode: ReadWriteOnce
  size: 8Gi
mysqlUser: "k8s"
mysqlPassword: "123456"
mysqlDatabase: "k8s"
# helm install db -f config.yaml stable/mysql
# kubectl get pods
NAME                                      READY   STATUS    RESTARTS   AGE
db-mysql-57485b68dc-4xjhv                 1/1     Running   0          8m51s
```

以上将创建具有名称的默认MySQL用户k8s，并授予此用户访问新创建的k8s数据库的权限，但将接受该图表的所有其余默认值。

命令行替代变量：

```
# helm install db --set persistence.storageClass="managed-nfs-storage" stable/mysql
```

也可以把chart包下载下来查看详情：

```
# helm pull stable/mysql --untar
```

values yaml与set使用：

![](https://k8s-1252881505.cos.ap-beijing.myqcloud.com/k8s-2/yaml-set.png)

**该helm install命令可以从多个来源安装：**

- chart存储库
- 本地chart存档（helm install foo-0.1.1.tgz）
- chart目录（helm install path/to/foo）
- 完整的URL（helm install https://example.com/charts/foo-1.2.3.tgz）

### 3、构建一个Helm Chart

先给学员自动生成目录讲解，然后再手动给学员创建目录和各个文件。

```
# helm create mychart
Creating mychart
# tree mychart/
mychart/
├── charts
├── Chart.yaml
├── templates
│   ├── deployment.yaml
│   ├── _helpers.tpl
│   ├── ingress.yaml
│   ├── NOTES.txt
│   └── service.yaml
└── values.yaml
```

- Chart.yaml：用于描述这个 Chart的基本信息，包括名字、描述信息以及版本等。
- values.yaml ：用于存储 templates 目录中模板文件中用到变量的值。
- Templates： 目录里面存放所有yaml模板文件。
- charts：目录里存放这个chart依赖的所有子chart。
- NOTES.txt ：用于介绍Chart帮助信息， helm install 部署后展示给用户。例如：如何使用这个 Chart、列出缺省的设置等。
- _helpers.tpl：放置模板助手的地方，可以在整个 chart 中重复使用

创建Chart后，接下来就是将其部署：

```
helm install web mychart/
```

也可以打包推送的charts仓库共享别人使用。

```
# helm package mychart/
mychart-0.1.0.tgz
```

### 4、升级、回滚和删除

发布新版本的chart时，或者当您要更改发布的配置时，可以使用该`helm upgrade` 命令。

```
# helm upgrade --set imageTag=1.17 web mychart
# helm upgrade -f values.yaml web mychart
```

如果在发布后没有达到预期的效果，则可以使用`helm rollback `回滚到之前的版本。

例如将应用回滚到第一个版本：

```
# helm rollback web 2
```

卸载发行版，请使用以下`helm uninstall`命令：

```
# helm uninstall web
```

查看历史版本配置信息

```
# helm get --revision 1 web
```

## 3.6 Chart模板

Helm最核心的就是模板，即模板化的K8S manifests文件。

它本质上就是一个Go的template模板。Helm在Go template模板的基础上，还会增加很多东西。如一些自定义的元数据信息、扩展的库以及一些类似于编程形式的工作流，例如条件语句、管道等等。这些东西都会使得我们的模板变得更加丰富。

### 1、模板

有了模板，我们怎么把我们的配置融入进去呢？用的就是这个values文件。这两部分内容其实就是chart的核心功能。

```
# rm -rf mychart/templates/*
# vi templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - image: nginx:1.16
        name: nginx
```

实际上，这已经是一个可安装的Chart包了，通过 `helm install`命令来进行安装：

```
# helm install web mychart
```

这样部署，其实与直接apply没什么两样。

然后使用如下命令可以看到实际的模板被渲染过后的资源文件：

```
# helm get manifest web
```

可以看到，这与刚开始写的内容是一样的，包括名字、镜像等，我们希望能在一个地方统一定义这些会经常变换的字段，这就需要用到Chart的模板了。

```
# vi templates/deployment.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - image: nginx:1.16
        name: nginx
```

这个deployment就是一个Go template的模板，这里定义的Release模板对象属于Helm内置的一种对象，是从values文件中读取出来的。这样一来，我们可以将需要变化的地方都定义变量。

再执行helm install chart 可以看到现在生成的名称变成了**web-deployment**，证明已经生效了。也可以使用命令helm get manifest查看最终生成的文件内容。

### 2、调试

Helm也提供了`--dry-run --debug`调试参数，帮助你验证模板正确性。在执行`helm install`时候带上这两个参数就可以把对应的values值和渲染的资源清单打印出来，而不会真正的去部署一个release。

比如我们来调试上面创建的 chart 包：

```
# helm install web2 --dry-run /root/mychart
```

### 3、内置对象

刚刚我们使用 `{{.Release.Name}}`将 release 的名称插入到模板中。这里的 Release 就是 Helm 的内置对象，下面是一些常用的内置对象：

| Release.Name      | release 名称                                  |
| ----------------- | --------------------------------------------- |
| Release.Time      | release 的时间                                |
| Release.Namespace | release 的 namespace（如果清单未覆盖）        |
| Release.Service   | release 服务的名称                            |
| Release.Revision  | 此 release 的修订版本号，从1开始累加          |
| Release.IsUpgrade | 如果当前操作是升级或回滚，则将其设置为 true。 |
| Release.IsInstall | 如果当前操作是安装，则设置为 true。           |

### 4、Values

Values对象是为Chart模板提供值，这个对象的值有4个来源：

- chart 包中的 values.yaml 文件

- 父 chart 包的 values.yaml 文件

- 通过 helm install 或者 helm upgrade 的 `-f`或者 `--values`参数传入的自定义的 yaml 文件

- 通过 `--set` 参数传入的值

chart 的 values.yaml 提供的值可以被用户提供的 values 文件覆盖，而该文件同样可以被 `--set`提供的参数所覆盖。

这里我们来重新编辑 mychart/values.yaml 文件，将默认的值全部清空，然后添加一个副本数：

```
# cat values.yaml 
replicas: 3
image: "nginx"
imageTag: "1.17"
# cat templates/deployment.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
spec:
  replicas: {{ .Values.replicas }}
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - image: {{ .Values.image }}:{{ .Values.imageTag }}
        name: nginx
```

查看渲染结果：

```
# helm install --dry-run web ../mychart/
```

values 文件也可以包含结构化内容，例如：

```
# cat values.yaml 
...
label:
  project: ms
  app: nginx

# cat templates/deployment.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment 
spec:
  replicas: {{ .Values.replicas }} 
  selector:
    matchLabels:
      project: {{ .Values.label.project }}
      app: {{ .Values.label.app }}
  template:
    metadata:
      labels:
        project: {{ .Values.label.project }}
        app: {{ .Values.label.app }}
    spec:
      containers:
      - image: {{ .Values.image }}:{{ .Values.imageTag }} 
        name: nginx
```

查看渲染结果：

```
# helm install --dry-run web ../mychart/
```

### 5、管道与函数

前面讲的模块，其实就是将值传给模板引擎进行渲染，模板引擎还支持对拿到数据进行二次处理。

例如从.Values中读取的值变成字符串，可以使用`quote`函数实现：

```
# vi templates/deployment.yaml
app: {{ quote .Values.label.app }}
# helm install --dry-run web ../mychart/ 
        project: ms
        app: "nginx"
```

quote .Values.label.app 将后面的值作为参数传递给quote函数。

模板函数调用语法为：functionName arg1 arg2...

另外还会经常使用一个default函数，该函数允许在模板中指定默认值，以防止该值被忽略掉。

例如忘记定义，执行helm install 会因为缺少字段无法创建资源，这时就可以定义一个默认值。

```
# cat values.yaml 
replicas: 2
# cat templates/deployment.yaml 
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
```

```
- name: {{ .Values.name | default "nginx" }}
```

**其他函数：**

缩进：{{ .Values.resources | indent 12 }}

大写：{{ upper .Values.resources }}

首字母大写：{{ title .Values.resources }}

### 6、流程控制

流程控制是为模板提供了一种能力，满足更复杂的数据逻辑处理。

Helm模板语言提供以下流程控制语句：

- `if/else` 条件块
- `with` 指定范围
- `range` 循环块

#### if

`if/else`块是用于在模板中有条件地包含文本块的方法，条件块的基本结构如下：

```
{{ if PIPELINE }}
  # Do something
{{ else if OTHER PIPELINE }}
  # Do something else
{{ else }}
  # Default case
{{ end }}
```

条件判断就是判断条件是否为真，如果值为以下几种情况则为false：

- 一个布尔类型的 `假`

- 一个数字 `零`

- 一个 `空`的字符串

- 一个 `nil`（空或 `null`）

- 一个空的集合（ `map`、 `slice`、 `tuple`、 `dict`、 `array`）

除了上面的这些情况外，其他所有条件都为 `真`。

例如，如果.Values.env.hello值为world，则值为hello: true

```
# cat values.yaml 
replicas: 2
label:
  project: ms
  app: product
env:
  hello: "world"
```

```
# cat templates/deploymemt.yaml
        env:
        {{ if eq .Values.env.hello "world" }}
          - name: hello
            value: 123
        {{ end }}
```

其中运算符 `eq`是判断是否相等的操作，除此之外，还有 `ne`、 `lt`、 `gt`、 `and`、 `or`等运算符。

通过模板引擎来渲染一下，会得到如下结果：

```
# helm install --dry-run web ../mychart/ 
...
        env:
        
          - name: hello
            value: 123
```

可以看到渲染出来会有多余的空行，这是因为当模板引擎运行时，会将控制指令删除，所有之前占的位置也就空白了，需要使用{{- if ...}} 的方式消除此空行：

```
# cat templates/deploymemt.yaml
...
        env:
        {{- if eq .Values.env.hello "world" }}
          - name: hello
            value: 123
        {{- end }}
```

现在是不是没有多余的空格了，如果使用`-}}`需谨慎，比如上面模板文件中：

```
# cat templates/deploymemt.yaml
...
       env:
        {{- if eq .Values.env.hello "world" -}}
           - hello: true
        {{- end }}
```

这会渲染成：

```
        env:- hello: true
```

因为`-}}`它删除了双方的换行符。

#### with

with ：控制变量作用域。

其语法和一个简单的 `if`语句比较类似：

```
{{ with PIPELINE }}
  #  restricted scope
{{ end }}
```

`with`语句可以允许将当前范围 `.`设置为特定的对象，比如我们前面一直使用的 `.Values.label`，我们可以使用 `with`来将 `.`范围指向 `.Values.label`：

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.name | default "web" }}
spec:
  replicas: {{ .Values.replicas }}
  selector:
    matchLabels:
      project: {{ .Values.label.project }}
      app: {{ .Values.label.app }}
  template:
    metadata:
      labels:
        project: {{ .Values.label.project }}
        app: {{ .Values.label.app }}
      {{- with .Values.label }}
        project: {{ .project }}
        app: {{ .app }}
      {{- end }}  
```

上面增加了一个{{- with .Values.label }} xxx {{- end }}的一个块，这样的话就可以在当前的块里面直接引用 `.project`和 `.app`了。

需要注意的在 `with`声明的范围内，将无法从父范围访问到其他对象了，比如：

```
      {{- with .Values.label }}
        project: {{ .project }}
        app: {{ .app }}
        {{ .Release.Name }}
      {{- end }}
```

#### range

在 Helm 模板语言中，使用 `range`关键字来进行循环操作。

我们在 `values.yaml`文件中添加上一个变量列表：

```
# cat values.yaml 
replicas: 2
label:
  project: ms
  app: product
env:
  hello: "world"
  test: "yes"
```

循环打印该列表：

```
        env:
        {{- range .Values.env }}
           {{ . }}
        {{- end }}
```

循环内部我们使用的是一个 `.`，这是因为当前的作用域就在当前循环内，这个 `.`引用的当前读取的元素。

但结果并不是我们所期望的：

        env:
           - name: world
             value: world


