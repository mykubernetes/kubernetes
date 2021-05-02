hostPath卷指定type类型有多种  
---
| 值  | 行为 |
| :------: | :--------: |
|   | 空字符串（默认）用于向后兼容，这意味着在挂载 hostPath 卷之前不会执行任何检查 |
| DirectoryOrCreate | 如果在给定的路径上没有任何东西存在，那么将根据需要在那里创建一个空目录，权限设置为 0755，与 Kubelet 具有相同的组和所有权 |
| Directory | 给定的路径下必须存在目录 |
| FileOrCreate | 如果在给定的路径上没有任何东西存在，那么会根据需要创建一个空文件，权限设置为 0644，与 Kubelet 具有相同的组和所有权 |
| File | 给定的路径下必须存在文件 |
| Socket | 给定的路径下必须存在 UNIX 套接字 |
| CharDevice | 给定的路径下必须存在字符设备 |
| BlockDevice | 给定的路径下必须存在块设备 |

hostPath示例
```
apiVersion: v1
kind: Pod
metadata:
  name: test-pd
spec:
  containers:
  - image: k8s.gcr.io/test-webserver
    name: test-container
    volumeMounts:
    - mountPath: /test-pd
      name: test-volume
  volumes:
  - name: test-volume
    hostPath:
      # directory location on host
      path: /data
      # this field is optional
      type: Directory
```  

vol-hostpath.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: vol-hostpath-pod
spec:
  containers:
  - name: filebeat
    image: ikubernetes/filebeat:5.6.7-alpine
    env:
    - name: REDIS_HOST
      value: redis.ikubernetes.io:6379
    - name: LOG_LEVEL
      value: info
    volumeMounts:
    - name: varlog
      mountPath: /var/log
    - name: socket
      mountPath: /var/run/docker.sock
    - name: varlibdockercontainers
      mountPath: /var/lib/docker/containers
      readOnly: true
  terminationGracePeriodSeconds: 30
  volumes:
  - name: varlog
    hostPath:
      path: /var/log
  - name: varlibdockercontainers
    hostPath:
      path: /var/lib/docker/containers
  - name: socket
    hostPath:
      path: /var/run/docker.sock
```


vol-cinder.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: vol-cinder-pod
spec:
  containers:
   - image: mysql
      name: mysql
      args:
        - "--ignore-db-dir"
        - "lost+found"
      env:
        - name: MYSQL_ROOT_PASSWORD
          value: YOUR_PASS
      ports:
        - containerPort: 3306
          name: mysqlport
      volumeMounts:
        - name: mysqldata
          mountPath: /var/lib/mysql
  volumes:
    - name: mysqldata
      cinder:                                             #openstack构建的iaas环境中时，Cinder的块存储为pod提供外部持久存储
        volumeID: e2b8d2f7-wece-90d1-a505-4acf607a90bc    #用于标识Cinder中的存储卷的卷标识符，必选
        fsType: ext4                                      #要挂载存储卷的文件系统，默认为ext4
```

vol-emptydir.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: vol-emptydir-pod
spec:
  volumes:
  - name: html
    emptyDir: {}
  containers:
  - name: nginx
    image: nginx:1.12-alpine
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
  - name: pagegen
    image: alpine
    volumeMounts:
    - name: html
      mountPath: /html
    command: ["/bin/sh", "-c"]
    args:
    - while true; do
        echo $(hostname) $(date) >> /html/index.html;
        sleep 10;
      done
```

vol-gitrepo.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: vol-gitrepo
spec:
  containers:
  - name: nginx
    image: nginx:1.12-alpine
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
  volumes:
  - name: html
    gitRepo:
      repository: https://github.com/iKubernetes/k8s_book.git
      directory: .
      revision: "master"
```

vol-glusterfs.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: vol-glusterfs-pod
  labels:
    app: redis
spec:
  containers:
  - name: redis
    image: redis:alpine
    ports:
    - containerPort: 6379
      name: redisport
    volumeMounts:
    - mountPath: /data
      name: redisdata
  volumes:
    - name: redisdata
      glusterfs:
        endpoints: glusterfs-endpoints         #Endpoints资源的名称，此资源需要事先存在，用于提供Gluster集群的步伐节点信息，必选字段
        path: kube-redis                       #用到的GlusterFS机器的卷路径，必选字段
        readOnly: false                        #是否为只读卷
```

vol-nfs.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: vol-nfs-pod
  labels:
    app: redis
spec:
  containers:
  - name: redis
    image: redis:alpine
    ports:
    - containerPort: 6379
      name: redisport
    volumeMounts:
    - mountPath: /data
      name: redisdata
  volumes:
    - name: redisdata
      nfs:
        server: nfs.ikubernetes.io
        path: /data/redis
```

vol-rbd.yaml
```
apiVersion: v1
kind: Pod
metadata:
  name: vol-rbd-pod
spec:
  containers:
  - name: redis
    image: redis:4-alpine
    ports:
    - containerPort: 6379
      name: redisport
    volumeMounts:
    - mountPath: /data
      name: redis-rbd-vol
  volumes:
    - name: redis-rbd-vol
      rbd:
        monitors:                      #ceph存储监视器，必选字段
        - '172.16.0.56:6789'
        - '172.16.0.57:6789'
        - '172.16.0.58:6789'
        pool: kube                     #rados存储池名称，默认RBD
        image: redis                   #rados image的名称，必选字段
        fsType: ext4                   #要挂载的存储文件系统的类型，如ext4、xfs、ntfs等，默认为ext4
        readOnly: false                #是否为只读方式进行访问
        user: admin                    #rados用户名，默认admin
        secretRef:                     #RBD用户认证是使用的保存secret对象，会覆盖keyring字段的定义，此处未定义keyring
          name: ceph-secret
```
