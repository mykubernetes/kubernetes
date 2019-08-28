在k8s_1.3版本之前，设置kubectl命令自动补全是通过以下的方式  
```
source ./contrib/completions/bash/kubectl
```  

1.3版本以后，kubectl添加了一个completions的命令， 该命令可用于自动补全  
```
source <(kubectl completion bash)
```  

k8s命令自动补全  
```
yum install -y bash-completion
source /usr/share/bash-completion/bash_completion
source <(kubectl completion bash)
echo "source <(kubectl completion bash)" >> ~/.bashrc
```  
