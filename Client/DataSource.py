#!/usr/bin/python3
# -*- coding: utf-8 -*-

import zmq
import simplejson
import argparse
import time

data_path = 'home/SourceData.txt'


# Connect to HAproxy VM
def connect_2_k8s(address, port):
    connect_str = 'tcp://' + address + ':' + port
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(connect_str)
    return socket


# Send data to HAproxy VM
def send_data(socket, start, end):
    index = 0
    with open(data_path, 'r') as f:
        for line in f:
            index += 1
            if start <= index < end:
                data = {'data': line.strip(), 'time': time.time()}
                data = simplejson.dumps(data)
                socket.send_string(data)
                socket.recv_string()
                time.sleep(10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', type=str, help='IP address of HAproxy server.')
    parser.add_argument('-p', '--port', type=str, help='Port number of HAproxy server.')
    parser.add_argument('-s', '--start', type=int, help='Start position for sending data.')
    parser.add_argument('-e', '--end', type=int, help='End position for sending data.')
    args = parser.parse_args()
    address = args.address
    port = args.port
    start = args.start
    end = args.end
    socket = connect_2_k8s(address, port)
    if socket is not None:
        send_data(socket, start, end)

main()