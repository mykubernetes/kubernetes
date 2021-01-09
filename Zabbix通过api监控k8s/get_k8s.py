#!/usr/bin/python3
import json
import datetime
import sys
import os
import math
import urllib3
import requests
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

zabbix_sender = "/usr/local/zabbix/bin/zabbix_sender"
zabbix_server = "192.168.1.233"
clientname = "k8s_master"


#k8s的api地址
url = "https://192.168.1.140:6443"

#k8s的token
token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJkYXNoYm9hcmQtYWRtaW4tdG9rZW4tenZkanAiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGFzaGJvYXJkLWFkbWluIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiNjFiZjJmYjgtODQ1Zi0xMWVhLWEyNmYtMDA1MDU2YTFiMGMyIiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50Omt1YmUtc3lzdGVtOmRhc2hib2FyZC1hZG1pbiJ9.a5GgFmbfvVr81rXiqnwsPQWFSpxOKDiiL5yPI150th4phbFaeffkSSSXxsUIxv87FuGHyQVewF_7qbdwIhH6oUvyZK2GZUmY6WfjXE-I1LH3XF1evTUq_-f8A2wyOtMJp0njdz0o_XASb0HXeAdS_HDcMTjl424QfV8hikty14_VU4aGDbAauaVbAZWtsBZaX01-lLJCiqqYzBMrAB1ippS9sq6njEWhdFmvsYyFlkhwOESgbFHF7bX2OCTRx00J5eu0JMXFmm12P4oVVkD2AEnnWxLZrMeZK7oSCBkWPs8yrCRQL_MWXZmDht1x0oIXXVLcJKr2CI_Qtl6-BHN46w"

def get_result(api_name):
   headers = {"Authorization":"Bearer "+token}
   json_data = requests.get(url+api_name,headers=headers,verify=False)
   return json_data.json()

#时间转换,把所有服务的创建时间变成运行时间
def Trantime(time_data):
    time = re.match(r"(\d+)-(\d+)-(\d+).*?(\d+):(\d+):(\d+)",time_data)
    total_send = round((datetime.datetime.now()-datetime.datetime(int(time.group(1)),int(time.group(2)),int(time.group(3)),int(time.group(4)),int(time.group(5)),int(time.group(6)))).total_seconds())
    return str(math.floor(total_send/86400)).split(".")[0]+"d"+str(math.floor((total_send%86400)/3600)).split(".")[0]+"h"   

#把所有的单位转换成b
def Tranunit(unit_data):
    unit = re.match(r"(\d+)(.*)",unit_data)
    value = int(unit.group(1))
    if unit.group(2) == "K":
       return value*1000
    elif unit.group(2) == "Ki":
       return value*1024
    elif unit.group(2) == "M":
       return value*1000*1000
    elif unit.group(2) == "Mi":
       return value*1024*1024
    elif unit.group(2) == "G":
       return value*1000*1000*1000
    elif unit.group(2) == "Gi":
        return value*1024*1024*1024
    elif unit.group(2) == "n":
        return math.ceil(value/1000/1000)
    elif unit.group(2) == "m":
        return value
    else:
        return value

#对数据进行zabbix_sender发送
def send_data(data,dis_key,key):
    result = json.dumps({"data":data},sort_keys=True,ensure_ascii=False)
    cmd = "{0} -z {1} -s {2} -k {3} -o '{4}'>/dev/null".format(zabbix_sender,zabbix_server,clientname,dis_key,result)
    os.system(cmd)
    for i in data:
        for value in i.keys():
         if value !="{#NAME}":
           cmd = "{0} -z {1} -s {2} -k {3}[{4}.{5}] -o '{6}'>/dev/null".format(zabbix_sender,zabbix_server,clientname,key,i["{#NAME}"],i[value][0],i[value][1])
           os.system(cmd)
           print(cmd)     
#获取所有k8s节点的信息
def get_node():
    get_nodes = []
    node_result = get_result("/api/v1/nodes")
    node_use_result = get_result("/apis/metrics.k8s.io/v1beta1/nodes")
    for j in node_use_result.get("items"):
          for i in node_result.get("items"):
            if i.get("metadata").get("name") == j.get("metadata").get("name"):
              data={"{#NAME}": i.get("metadata").get("name"),
                               "{#STATUS}": ["status",i.get("status").get("conditions")[-1].get("type") if i.get("status").get("conditions")[-1].get("status") == "True" else "NotReady"],
                                "{#IP}": ["ip",i.get("status").get("addresses")[0].get("address")],
                                "{#KUBELET_VERSION}": ["version",i.get("status").get("nodeInfo").get("kubeletVersion")],
                                "{#OS_IMAGE}": ["os_image",i.get("status").get("nodeInfo").get("osImage")],
                                 "{#CPU}": ["cpu",i.get("status").get("capacity").get("cpu")],
                                 "{#MEMORY}": ["memory",Tranunit(i.get("status").get("capacity").get("memory"))],
                                 "{#LIMIT_STORAGE}": ["storage",Tranunit(i.get("status").get("capacity").get("ephemeral-storage"))],
                                 "{#RUNTIME}":["runtime",Trantime(i.get("metadata").get("creationTimestamp"))],
                                 "{#USECPU}":["usecpu",Tranunit(j.get("usage").get("cpu"))],
                                 "{#USEMEMORY}":["usememory",Tranunit(j.get("usage").get("memory"))]
                                 }
       
          get_nodes.append(data)
    send_data(get_nodes,"getnode","node")

#获取k8s组件的健康信息
def get_health():
    get_healths = []
    health_result = get_result("/api/v1/componentstatuses") 
    for i in health_result.get("items"):
        data = {} 
        data = {"{#NAME}": i.get("metadata").get("name"),
                "{#STATUS}": ["status",i.get("conditions")[0].get("type")],
                "{#MESSAGE}":["message",i.get("conditions")[0].get("message")]                 
                }
        get_healths.append(data)
    send_data(get_healths,"gethealth","health")

#获取k8s的所有pod
def get_pod(): 
    get_pods = []
    pod_result = get_result("/api/v1/pods")
    for i in pod_result.get("items"):
           data = {"{#NAME}":i.get("metadata").get("name"),
                   "{#RUNTIME}":["runtime",Trantime(i.get("metadata").get("creationTimestamp"))],  
                   "{#STATUS}":["status",i.get("status").get("phase")],
                   "{#RESTARTCOUNT}":["restartcount",i.get("status").get("containerStatuses")[0].get("restartCount")]
                      }
            
           get_pods.append(data)
    send_data(get_pods,"getpod","pod")
        
if __name__ == "__main__":
   cmd = "{0}()".format(sys.argv[1])
   eval(cmd)
   print("采集完成")
