
1、编辑jenkins.pipeline
```
# vim jenkins.pipeline

node {
   
   def BUILD_DIR = "/root/build-workspace/"
   env.BUILD_DIR = "/root/build-workspace/"
   env.MODULE = "web-demo"
   env.HOST = "k8s-web.mooc.com"
    
   stage('Preparation') { // for display purposes
      // Get some code from a GitHub repository
      git 'https://gitee.com/pa/mooc-k8s-demo-docker.git'
   }
   stage('Maven Build') {
      // Run the maven build
      sh "mvn -pl ${MODULE} -am -Dmaven.test.failure.ignore clean package"
   }
   stage('Build Image') {
      sh "/root/script/build-image-web.sh"
   }
   stage('Deploy') {
       sh "/root/script/deploy.sh"
   }
}
```  

2、编写镜像构建脚本
```
#!/bin/bash

if [ "${BUILD_DIR}" == "" ];then
    echo "env 'BUILD_DIR' is not set"
    exit 1
fi

DOCKER_DIR=${BUILD_DIR}/${JOB_NAME}

if [ ! -d ${DOCKER_DIR} ];then
    mkdir -p ${DOCKER_DIR}
fi

echo "docker workspace: ${DOCKER_DIR}"

JENKINS_DIR=${WORKSPACE}/${MODULE}

echo "jenkins workspace: ${JENKINS_DIR}"

if [ ! -f ${JENKINS_DIR}/target/*.war ];then
    echo "target war file not found ${JENKINS_DIR}/target/*.war"
    exit 1
fi

cd ${DOCKER_DIR}
rm -fr *
unzip -oq ${JENKINS_DIR}/target/*.war -d ./ROOT

mv ${JENKINS_DIR}/Dockerfile .
if [ -d ${JENKINS_DIR}/dockerfiles ];then
    mv ${JENKINS_DIR}/dockerfiles .
fi

VERSION=$(date +%Y%m%d%H%M%S)
IMAGE_NAME=hub.mooc.com/kubernetes/${JOB_NAME}:${VERSION}

echo "${IMAGE_NAME}" > ${WORKSPACE}/IMAGE

echo "building image: ${IMAGE_NAME}"
docker build -t ${IMAGE_NAME} .

docker push ${IMAGE_NAME}
```  

3、编写dockerfile
```
# vim  Dockerfile 
FROM hub.mooc.com/kubernetes/tomcat:8.0.51-alpine

COPY ROOT /usr/local/tomcat/webapps/ROOT

COPY dockerfiles/start.sh /usr/local/tomcat/bin/start.sh

ENTRYPOINT ["sh" , "/usr/local/tomcat/bin/start.sh"]
```  

```
# mkdir dockerfiles
# vim  dockerfiles/start.sh 
#!/bin/bash

sh /usr/local/tomcat/bin/startup.sh

tail -f /usr/local/tomcat/logs/catalina.out

```  

4、编写部署脚本  
```
#!/bin/bash

name=${JOB_NAME}
image=$(cat ${WORKSPACE}/IMAGE)
host=${HOST}

echo "deploying ... name: ${name}, image: ${image}, host: ${host}"

rm -f web.yaml
cp $(dirname "${BASH_SOURCE[0]}")/template/web.yaml .
echo "copy success"
sed -i "s,{{name}},${name},g" web.yaml
sed -i "s,{{image}},${image},g" web.yaml
sed -i "s,{{host}},${host},g" web.yaml
echo "ready to apply"
kubectl apply -f web.yaml
echo "apply ok"

cat web.yaml

# 健康检查
success=0
count=60
IFS=","
sleep 5
while [ ${count} -gt 0 ]
do
    replicas=$(kubectl get deploy ${name} -o go-template='{{.status.replicas}},{{.status.updatedReplicas}},{{.status.readyReplicas}},{{.status.availableReplicas}}')
    echo "replicas: ${replicas}"
    arr=(${replicas})
    if [ "${arr[0]}" == "${arr[1]}" -a "${arr[1]}" == "${arr[2]}" -a "${arr[2]}" == "${arr[3]]}" ];then
        echo "health check success!"
        success=1
        break
    fi
    ((count--))
    sleep 2
done

if [ ${success} -ne 1 ];then
    echo "health check failed!"
    exit 1
fi
```  

5、编写对应yaml
```
# vim web.yaml

#deploy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{name}}
spec:
  selector:
    matchLabels:
      app: {{name}}
  replicas: 1
  template:
    metadata:
      labels:
        app: {{name}}
    spec:
      containers:
      - name: {{name}}
        image: {{image}}
        ports:
        - containerPort: 8080
---
#service
apiVersion: v1
kind: Service
metadata:
  name: {{name}}
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 8080
  selector:
    app: {{name}}
  type: ClusterIP

---
#ingress
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: {{name}}
spec:
  rules:
  - host: {{host}}
    http:
      paths:
      - path: /
        backend:
          serviceName: {{name}}
          servicePort: 80
```  
