#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import csv
import yaml
import zmq
import time
from K8sOperations import K8sOperations


class CSV_Operations:
    def read_csv(self, csv_file):
        with open(csv_file) as f:
            f_csv = csv.DictReader(f)
            return f_csv


    def write_csv(self, rows, csv_file):
        headers = ['Node', 'Address', 'Port', 'Status', 'Deployment']
        with open(csv_file, 'w') as f:
            f_csv = csv.DictWriter(f, headers)
            f_csv.writeheader()
            f_csv.writerows(rows)


class ZMQ_Operations:
    # Build a REP socket
    def build_REP_socket(self, port):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind('tcp://*:' + port)
        return socket


    # Build a REQ socket
    def build_REQ_socket(self, address, port):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect('tcp://' + address + ':' + port)  
        return socket


class ElasticK8s:
    def __init__(self, port1, haproxy_address, port2):
        # port1: used to listen message from manager
        # port2: used to connect to haproxy server 
        self.csv_op = CSV_Operations()
        self.zmq_op = ZMQ_Operations()
        self.k8s_op = K8sOperations()
        self.rep_socket = self.zmq_op.build_REP_socket(port1)
        self.req_socket = self.zmq_op.build_REQ_socket(haproxy_address, port2)
        self.csv_file = './NodeInfo.csv'
        self.image_name = 'zhuangweikang/streamingml_worker'
        self.container_port = 2341
        self.backend_name = None


    # Add new deploymeny into the K8s cluster
    def scale_in(self, count, node_port):
        # create deployment here
        deployment_name = 'worker' + str(count) + '-deployment'
        pod_label = 'worker' + str(count)
        container_name = 'worker' + str(count)

        # CSV operations
        rows = self.csv_op.read_csv(self.csv_file)
        _rows = [row for row in rows]
        for i, row in enumerate(_rows):
            if row['Status'] == 'Free':
                target_row = row
                _rows[i]['Status'] = 'Running'
                _rows[i]['Deployment'] = deployment_name
        self.csv_op.write_csv(_rows, self.csv_file)

        node_name = target_row['Node']
        self.k8s_op.create_deployment(node_name, deployment_name, pod_label, self.image_name, container_name)
        print('Create new deployment: '+ deployment_name)

        # create service here
        svc_name = 'worker' + str(count) + '-service'
        selector_label = pod_label
        _port = 2343
        self.k8s_op.create_svc(svc_name, selector_label, _port, node_port)
        print('Create new service: ' + svc_name)

        # notify haproxy to update configuration file
        self.notify_haproxy('scale-in', self.backend_name, node_name, target_row['Address'], target_row['Port'])


    # Delete the last added deployment
    def scale_out(self, socket, count):
        # delete deployment
        deployment_name = 'worker' + str(count) + '-deployment'
        drop_deployment = 'kubectl delete deployment ' + deployment_name
        os.system(drop_deployment)

        # CSV operations
        rows = self.csv_op.read_csv(self.csv_file)
        _rows = [row for row in rows]
        for i, row in enumerate(_rows[:]):
            if row['Deployment'] == deployment_name:
                target_row = row
                _rows[i]['Status'] = 'Free'
                _rows[i]['Deployment'] = 'None'
        self.csv_op.write_csv(_rows, self.csv_file)
        print('Delete deployment: ' + deployment_name)

        # delete service
        svc_name = 'worker' + str(count) + '-service'
        drop_svc = 'kubectl delete svc ' + svc_name
        os.system(drop_svc)
        print('Delete service: ' + svc_name)

        # notify haproxy to update configuration file
        self.notify_haproxy('scale-out', self.backend_name, target_row['Node'], target_row['Address'], target_row['Port'])

    # Notify HAproxy to update
    def notify_haproxy(self, option, backend, host_name, address, port):
        msg = {'option': option, 'backend': backend, 'host_name': host_name, 'address': address, 'port': port}
        self.req_socket.send_json(msg)
        _recv = self.req_socket.recv_string()
        print('Recv Ack msg from HAproxy server: %s' % _recv)
