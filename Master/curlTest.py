import os
import simplejson

command = 'time curl -X POST -F image=@owl.jpg \'http://129.59.107.141:30016/predict\''
_exec = os.popen(command)
data = _exec.read()
data = simplejson.loads(data)
print(data)
