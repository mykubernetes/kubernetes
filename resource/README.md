```
        resources:
          requests:
            memory: 100Mi
            cpu: 100m
          limits:
            memory: 100Mi
            cpu: 200m
```  
- memory: 100Mi 表示使用100兆的内存
- cpu: 100m 表示使用0.1核的cpu,如果没有单位则表示使用几个核心的cpu。1核心cpu等1000m,所有100m等于0.1核cpu
