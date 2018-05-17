import zmq
import os

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind('tcp://*:2555')

while True:
    msg = socket.recv_string()
    image = msg.split(':')[1]

    get_container_id =  'docker ps | grep \'%s\' | awk \'{ print $1 }\'' % image
    while True:
        _exec = os.popen(get_container_id)
        if _exec.read() == '':
            break
    print('Container has been deleted.')

    command = 'docker rmi -f %s' % image
    _exec = os.popen(command)
    print(_exec.read())

    socket.send_string('Ack')