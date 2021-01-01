maven打包构建命令
---
```
mvn clean package
依次执行clean、resources、compile、testResources、testCompile、test、jar(打包)等７个阶段。

mvn clean install
依次执行clean、resources、compile、testResources、testCompile、test、jar(打包)、install等8个阶段。

mvn clean deploy
依次执行clean、resources、compile、testResources、testCompile、test、jar(打包)、install、deploy等９个阶段。
```
package、install、deploy区别
- package 命令完成了项目编译、单元测试、打包功能，但没有把打好的可执行jar包（war包或其它形式的包）布署到本地maven仓库和远程maven私服仓库.
- install 命令完成了项目编译、单元测试、打包功能，同时把打好的可执行jar包（war包或其它形式的包）布署到本地maven仓库，但没有布署到远程maven私服仓库.
- deploy 命令完成了项目编译、单元测试、打包功能，同时把打好的可执行jar包（war包或其它形式的包）布署到本地maven仓库和远程maven私服仓库.

常用命令
---
- mvn archetype:generate 创建Maven项目
- mvn compile 编译源代码
- mvn deploy 发布项目
- mvn test-compile 编译测试源代码
- mvn test 运行应用程序中的单元测试
- mvn site 生成项目相关信息的网站
- mvn clean 清除项目目录中的生成结果
- mvn package 根据项目生成的jar
- mvn install 在本地Repository中安装jar
- mvn eclipse:eclipse 生成eclipse项目文件
- mvn jetty:run 启动jetty服务
- mvn tomcat:run 启动tomcat服务
- mvn clean package -Dmaven.test.skip=true:清除以前的包后重新打包，跳过测试类
- mvn dependency:tree -Dverbose -Dincludes=asm:asm 查询包的依赖树结构
