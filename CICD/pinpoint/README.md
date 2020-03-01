主流系统：zipkin、skywalking、pinpoint

Docker部署:
```
git clone https://github.com/naver/pinpoint-docker.git
cd pinpoint-docker
docker-compose pull && docker-compose up -d
```
访问页面
http://IP:8079

pinpoint agent部署
tomcat
```
# catalina.sh
CATALINA_OPTS="$CATALINA_OPTS -javaagent:$AGENT_PATH/pinpoint-bootstrap-$VERSIONO.jar"
CATALINA_OPTS="$CATALINA_OPTS -Dpinpoint.agentId=$AGENT_ID"
CATALINA_OPTS="$CATALINA_OPTS -Dpinpoint.applicationName=$APPLICATION_NAME"
````
jar
```
java -jar -javaagent:$AGENT_PATH/pinpoint-bootstrap-$VERSION.jar -Dpinpoint.agentID=$AGENT_ID -Dpinpoint.applicationName=$APPLICATION_NAME xxx.jar
```
