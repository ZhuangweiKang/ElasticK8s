import zmq
import os

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind('tcp://*:2555')

while True:
    msg = socket.recv_string()
    msg = msg.split(':')[1]
    command = 'docker rmi %s' % msg
    _exec = os.popen(command)
    print(_exec.read())
    socket.send_string('Ack')