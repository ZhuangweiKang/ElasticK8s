#!/usr/bin/python3
# -*- coding: utf-8 -*-

import zmq
import simplejson

_max = 0


def bind_port(port):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:' + port)
    return socket


def recv_data(socket):
    while True:
        msg = socket.recv_string()
        msg = simplejson.loads(msg)
        reply = max(_max, msg['data'])
        socket.send_string(str(reply))


def main():
    socket = bind_port('2341')
    recv_data(socket)


main()