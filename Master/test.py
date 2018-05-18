from K8sOperations import K8sOperations
import os
import time
import simplejson

command = 'kubectl delete svc kang4-service & kubectl delete deploy kang4-deployment'
_exec = os.popen(command)
print(_exec.read())

k8s = K8sOperations()
k8s.create_deployment('kang4', 'kang4-deployment', 'worker4', 'docgroupvandy/xceptionkeras', 'worker4',  0.5, 1.0, container_port=7000)
k8s.create_svc('kang4-service', 'worker4')


while True:
  try:
    command = 'curl -X POST -F image=@owl.jpg \'http://129.59.107.141:30000/predict\' | jq \'.\''
    _exec = os.popen(command)
    print(simplejson.loads(_exec.read()))
    break
  except Exception:
    continue

