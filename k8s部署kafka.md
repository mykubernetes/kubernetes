kubernetes集群部署kafka
===

https://github.com/cuishuaigit/k8s-kafka

# 一、部署前准备
- 创建好的至少三个节点的kubernetes集群(这里我们使用的版本1.13.10)
- 创建好的存储类StorageClass(这里我们使用的是cephfs)

# 二、部署yaml文件
1.部署zookeeper的yaml文件
```
[root@k8s001 kafka]# cat zookeeper.yaml 
apiVersion: v1
kind: Service
metadata:
  name: zk-hs
  namespace: kafka
  labels:
    app: zk
spec:
  ports:
  - port: 2888
    name: server
  - port: 3888
    name: leader-election
  clusterIP: None
  selector:
    app: zk
---
apiVersion: v1
kind: Service
metadata:
  name: zk-cs
  namespace: kafka
  labels:
    app: zk
spec:
  ports:
  - port: 2181
    name: client
  selector:
    app: zk
---
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: zk-pdb
  namespace: kafka
spec:
  selector:
    matchLabels:
      app: zk
  maxUnavailable: 1
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: zk
  namespace: kafka
spec:
  selector:
    matchLabels:
      app: zk
  serviceName: zk-hs
  replicas: 3
  updateStrategy:
    type: RollingUpdate
  podManagementPolicy: Parallel
  template:
    metadata:
      labels:
        app: zk
    spec:
      nodeSelector:
          travis.io/schedule-only: "kafka"
      tolerations:
      - key: "travis.io/schedule-only"
        operator: "Equal"
        value: "kafka"
        effect: "NoSchedule"
      - key: "travis.io/schedule-only"
        operator: "Equal"
        value: "kafka"
        effect: "NoExecute"
        tolerationSeconds: 3600
      - key: "travis.io/schedule-only"
        operator: "Equal"
        value: "kafka"
        effect: "PreferNoSchedule"
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: "app"
                    operator: In
                    values:
                    - zk
              topologyKey: "kubernetes.io/hostname"
      containers:
      - name: kubernetes-zookeeper
        imagePullPolicy: IfNotPresent
        image: fastop/zookeeper:3.4.10
        resources:
          requests:
            memory: "200Mi"
            cpu: "0.1"
        ports:
        - containerPort: 2181
          name: client
        - containerPort: 2888
          name: server
        - containerPort: 3888
          name: leader-election
        command:
        - sh
        - -c
        - "start-zookeeper \
          --servers=3 \
          --data_dir=/var/lib/zookeeper/data \
          --data_log_dir=/var/lib/zookeeper/data/log \
          --conf_dir=/opt/zookeeper/conf \
          --client_port=2181 \
          --election_port=3888 \
          --server_port=2888 \
          --tick_time=2000 \
          --init_limit=10 \
          --sync_limit=5 \
          --heap=512M \
          --max_client_cnxns=60 \
          --snap_retain_count=3 \
          --purge_interval=12 \
          --max_session_timeout=40000 \
          --min_session_timeout=4000 \
          --log_level=INFO"
        readinessProbe:
          exec:
            command:
            - sh
            - -c
            - "zookeeper-ready 2181"
          initialDelaySeconds: 10
          timeoutSeconds: 5
        livenessProbe:
          exec:
            command:
            - sh
            - -c
            - "zookeeper-ready 2181"
          initialDelaySeconds: 10
          timeoutSeconds: 5
        volumeMounts:
        - name: datadir
          mountPath: /var/lib/zookeeper
      # 这里我们需要将runAsuser和fsGroup用户调整为0，也就是管理员用户允许，否则会提示权限的报错
      securityContext:
        runAsUser: 0
        fsGroup: 0
  volumeClaimTemplates:
  - metadata:
      name: datadir
    spec:
      accessModes: [ "ReadWriteMany" ]
      storageClassName: cephfs
      resources:
        requests:
          storage: 20Gi
```

2.部署kafka的yaml文件
```
[root@k8s001 kafka]# cat kafka.yaml 
---
apiVersion: v1
kind: Service
metadata:
  name: kafka-svc
  namespace: kafka
  labels:
    app: kafka
spec:
  ports:
  - port: 9092
    name: server
  clusterIP: None
  selector:
    app: kafka
---
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: kafka-pdb
  namespace: kafka
spec:
  selector:
    matchLabels:
      app: kafka
  minAvailable: 2
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
  namespace: kafka
spec:
  selector:
     matchLabels:
        app: kafka
  serviceName: kafka-svc
  replicas: 3
  template:
    metadata:
      labels:
        app: kafka
    spec:
      nodeSelector:
          travis.io/schedule-only: "kafka"
      tolerations:
      - key: "travis.io/schedule-only"
        operator: "Equal"
        value: "kafka"
        effect: "NoSchedule"
      - key: "travis.io/schedule-only"
        operator: "Equal"
        value: "kafka"
        effect: "NoExecute"
        tolerationSeconds: 3600
      - key: "travis.io/schedule-only"
        operator: "Equal"
        value: "kafka"
        effect: "PreferNoSchedule"
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: "app"
                    operator: In
                    values: 
                    - kafka
              topologyKey: "kubernetes.io/hostname"
        podAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
             - weight: 1
               podAffinityTerm:
                 labelSelector:
                    matchExpressions:
                      - key: "app"
                        operator: In
                        values: 
                        - zk
                 topologyKey: "kubernetes.io/hostname"
      terminationGracePeriodSeconds: 300
      containers:
      - name: k8s-kafka
        imagePullPolicy: IfNotPresent
        image: fastop/kafka:2.2.0
        resources:
          requests:
            memory: "600Mi"
            cpu: 500m
        ports:
        - containerPort: 9092
          name: server
        command:
        - sh
        - -c
        - "exec kafka-server-start.sh /opt/kafka/config/server.properties --override broker.id=${HOSTNAME##*-} \
          --override listeners=PLAINTEXT://:9092 \
          --override zookeeper.connect=zk-0.zk-hs.kafka.svc.cluster.local:2181,zk-1.zk-hs.kafka.svc.cluster.local:2181,zk-2.zk-hs.kafka.svc.cluster.local:2181 \
          --override log.dir=/var/lib/kafka \
          --override auto.create.topics.enable=true \
          --override auto.leader.rebalance.enable=true \
          --override background.threads=10 \
          --override compression.type=producer \
          --override delete.topic.enable=false \
          --override leader.imbalance.check.interval.seconds=300 \
          --override leader.imbalance.per.broker.percentage=10 \
          --override log.flush.interval.messages=9223372036854775807 \
          --override log.flush.offset.checkpoint.interval.ms=60000 \
          --override log.flush.scheduler.interval.ms=9223372036854775807 \
          --override log.retention.bytes=-1 \
          --override log.retention.hours=168 \
          --override log.roll.hours=168 \
          --override log.roll.jitter.hours=0 \
          --override log.segment.bytes=1073741824 \
          --override log.segment.delete.delay.ms=60000 \
          --override message.max.bytes=1000012 \
          --override min.insync.replicas=1 \
          --override num.io.threads=8 \
          --override num.network.threads=3 \
          --override num.recovery.threads.per.data.dir=1 \
          --override num.replica.fetchers=1 \
          --override offset.metadata.max.bytes=4096 \
          --override offsets.commit.required.acks=-1 \
          --override offsets.commit.timeout.ms=5000 \
          --override offsets.load.buffer.size=5242880 \
          --override offsets.retention.check.interval.ms=600000 \
          --override offsets.retention.minutes=1440 \
          --override offsets.topic.compression.codec=0 \
          --override offsets.topic.num.partitions=50 \
          --override offsets.topic.replication.factor=3 \
          --override offsets.topic.segment.bytes=104857600 \
          --override queued.max.requests=500 \
          --override quota.consumer.default=9223372036854775807 \
          --override quota.producer.default=9223372036854775807 \
          --override replica.fetch.min.bytes=1 \
          --override replica.fetch.wait.max.ms=500 \
          --override replica.high.watermark.checkpoint.interval.ms=5000 \
          --override replica.lag.time.max.ms=10000 \
          --override replica.socket.receive.buffer.bytes=65536 \
          --override replica.socket.timeout.ms=30000 \
          --override request.timeout.ms=30000 \
          --override socket.receive.buffer.bytes=102400 \
          --override socket.request.max.bytes=104857600 \
          --override socket.send.buffer.bytes=102400 \
          --override unclean.leader.election.enable=true \
          --override zookeeper.session.timeout.ms=6000 \
          --override zookeeper.set.acl=false \
          --override broker.id.generation.enable=true \
          --override connections.max.idle.ms=600000 \
          --override controlled.shutdown.enable=true \
          --override controlled.shutdown.max.retries=3 \
          --override controlled.shutdown.retry.backoff.ms=5000 \
          --override controller.socket.timeout.ms=30000 \
          --override default.replication.factor=1 \
          --override fetch.purgatory.purge.interval.requests=1000 \
          --override group.max.session.timeout.ms=300000 \
          --override group.min.session.timeout.ms=6000 \
          --override inter.broker.protocol.version=2.2.0 \
          --override log.cleaner.backoff.ms=15000 \
          --override log.cleaner.dedupe.buffer.size=134217728 \
          --override log.cleaner.delete.retention.ms=86400000 \
          --override log.cleaner.enable=true \
          --override log.cleaner.io.buffer.load.factor=0.9 \
          --override log.cleaner.io.buffer.size=524288 \
          --override log.cleaner.io.max.bytes.per.second=1.7976931348623157E308 \
          --override log.cleaner.min.cleanable.ratio=0.5 \
          --override log.cleaner.min.compaction.lag.ms=0 \
          --override log.cleaner.threads=1 \
          --override log.cleanup.policy=delete \
          --override log.index.interval.bytes=4096 \
          --override log.index.size.max.bytes=10485760 \
          --override log.message.timestamp.difference.max.ms=9223372036854775807 \
          --override log.message.timestamp.type=CreateTime \
          --override log.preallocate=false \
          --override log.retention.check.interval.ms=300000 \
          --override max.connections.per.ip=2147483647 \
          --override num.partitions=4 \
          --override producer.purgatory.purge.interval.requests=1000 \
          --override replica.fetch.backoff.ms=1000 \
          --override replica.fetch.max.bytes=1048576 \
          --override replica.fetch.response.max.bytes=10485760 \
          --override reserved.broker.max.id=1000 "
        env:
        - name: KAFKA_HEAP_OPTS
          value : "-Xmx512M -Xms512M"
        - name: KAFKA_OPTS
          value: "-Dlogging.level=INFO"
        volumeMounts:
        - name: datadir
          mountPath: /var/lib/kafka
        readinessProbe:
          tcpSocket:
            port: 9092
          timeoutSeconds: 1
          initialDelaySeconds: 5
      securityContext:
        runAsUser: 1000
        fsGroup: 1000
  volumeClaimTemplates:
  - metadata:
      name: datadir
    spec:
      accessModes: [ "ReadWriteMany" ]
      storageClassName: cephfs
      resources:
        requests:
          storage:  20Gi
```

# 三、部署

这里zookeeper和kafka都是有状态的服务，不能使用deployment和rc这种控制器来部署，这里我们使用statefulset来部署zookeeper和kafka服务。

1、给节点打标签  
这里我们想在哪几台机器上来运行kafka，需要对节点进行打标签。
```
kubectl label node [node-name] travis.io/schedule-only=kafka 
```

当然，如果我们如果不想在哪些节点运行kafka，可以通过配置污点来进行。
```
kubectl taint node [node-name] travis.io/schedule-only=kafka:NoSchedule
```

2、创建名称空间
```
[root@k8s001 kafka]# kubectl create ns kafka
```

3、创建zookeeper服务
```
# 创建zookeeper服务
[root@k8s001 kafka]# kubectl apply -f zookeeper.yaml
# 查看zookeeper服务运行状态
[root@k8s001 kafka]# kubectl get pod -n kafka
NAME      READY   STATUS        RESTARTS   AGE
zk-0      1/1     Running       0          7m8s
zk-1      1/1     Running       0          7m8s
zk-2      1/1     Running       0          7m8s
```

4、创建kafka服务
```
[root@k8s001 kafka]# kubectl apply -f kafka.yaml
[root@k8s001 kafka]# kubectl get pod -n kafka
NAME      READY   STATUS    RESTARTS   AGE
kafka-0   1/1     Running   0          11m
kafka-1   1/1     Running   0          11m
kafka-2   1/1     Running   0          10m
zk-0      1/1     Running   0          6m44s
zk-1      1/1     Running   0          6m44s
zk-2      1/1     Running   0          6m44s
```

# 四、测试
```
测试zookeeper：
kubectl exec -it zk-0 -n kafka -- zkServer.sh status
kubectl exec -it zk-0 -n kafka -- zkCli.sh create /hello world
kubectl delete -f zookeeper.yaml
kubectl apply -f zookeeper.yaml
kubectl exec -it zk-0 -n kafka -- zkCli.sh get /hello
测试kafka:
kubectl exec -it kafka-0 -n kafka -- bash 
>kafka-topics.sh --create \
--topic test \
--zookeeper zk-0.zk-hs.kafka.svc.cluster.local:2181,zk-1.zk-hs.kafka.svc.cluster.local:2181,zk-2.zk-hs.kafka.svc.cluster.local:2181 \
--partitions 3 \
--replication-factor 2
kafka-topics.sh --list --zookeeper zk-0.zk-hs.kafka.svc.cluster.local:2181,zk-1.zk-hs.kafka.svc.cluster.local:2181,zk-2.zk-hs.kafka.svc.cluster.local:2181
kafka-console-consumer.sh --topic test --bootstrap-server localhost:9092
# 另起一个窗口，进入kafka-1容器
kubectl exec -it kafka-1 -n kafka -- bash
>kafka-console-producer.sh --topic test --broker-list localhost:9092
随便输入内容，观察kafka-0启动的kafka-console-consumer.sh的输出
```
