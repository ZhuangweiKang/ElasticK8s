#!/usr/bin/python3
# -*- coding: utf-8 -*-

import docker
import zmq
import time

image_name = 'zhuangweikang/streamingml_ds'
master_address = '129.59.107.138'
master_port = '2342'
haproxy_address = '129.59.107.139'
haproxy_port = '2341'


def run_container(name, start, end):
    command = 'python /home/DataSource.py -a ' + haproxy_address + ' -p' + haproxy_port + ' -s' + str(start) + ' -e' + str(end)
    client = docker.from_env()
    client.containers.run(image=image_name, detach=True, name=name, tty=True, stdin_open=True, command=command)


def connect_master():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    connect_str = 'tcp://' + master_address + ':' + master_port
    socket.connect(connect_str)
    return socket


def main():
    socket = connect_master()
    start = 1
    end = 50
    for i in range(5):
        # notify master node to create deployment
        socket.send_string('scale-in')
        socket.recv_string()
        time.sleep(20)
        name = 'source' + str(i)
        run_container(name, start, end)
        start = end + 1
        end = end * i
        time.sleep(60)
    time.sleep(10)
    for i in range(5):
        # notify master node to delete deployment
        socket.send_string('scale-out')
        socket.recv_string()
        time.sleep(30)


main()