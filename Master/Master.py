#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import csv
import yaml
import zmq
import time
from kubernetes import client, config

image_name = 'zhuangweikang/streamingml_worker'
container_port = 2341
csv_file = './NodeInfo.csv'
backend_name = None


def read_csv():
    global csv_file
    with open(csv_file) as f:
        f_csv = csv.DictReader(f)
        return f_csv


def write_csv(rows):
    global csv_file
    headers = ['Node', 'Address', 'Port', 'Status']
    with open(csv_file, 'w') as f:
        f_csv = csv.DictWriter(f, headers)
        f_csv.writeheader()
        f_csv.writerows(rows)

# create a deployment on a specific node
def create_deployment(node_name, deployment_name, pod_label, container_name):
    global image_name
    global container_port

    # Load config from default location
    config.load_kube_config()
    extension = client.ExtensionsV1beta1Api()

    container = client.V1Container(
        name=container_name,
        image=image_name,
        ports=[client.V1ContainerPort(container_port=container_port)],
        tty=True,
        stdin=True,
        command=['bin/bash'])

    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": pod_label}),
        spec=client.V1PodSpec(node_name=node_name ,containers=[container]))

    selector = client.V1LabelSelector(match_labels={'app': pod_label})

    # Create the specification of deployment
    spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=2,
        selector=selector,
        template=template
    )

    # Instantiate the deployment object
    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=spec)

    # create deployment
    extension.create_namespaced_deployment(namespace="default", body=deployment)


# Create a service using NodePort manner
# node_port starts from 30000
def create_svc(svc_name, selector_label, _port, _node_port):
    config.load_kube_config()
    api_instance = client.CoreV1Api()
    service = client.V1Service()

    service.api_version = "v1"
    service.kind = "Service"

    # define meta data
    service.metadata = client.V1ObjectMeta(name=svc_name)

    # define spec part
    spec = client.V1ServiceSpec()
    spec.selector = {"app": selector_label}
    spec.type = "NodePort"
    spec.ports = [client.V1ServicePort(
        protocol="TCP", 
        port=_port, 
        target_port=_node_port)]

    service.spec = spec

    # create service
    api_instance.create_namespaced_service(namespace="default", body=service)


# Build a socket to recv msg from Mangager
def build_REP_socket():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:2342')
    return socket


# Build a socket to send msg to HAproxy
def build_REQ_socket(address, port):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect('tcp://' + address + ':' + port)  
    return socket


# Add new deploymeny into the K8s cluster
def scale_in(socket, count, node_port):
     # create deployment here
    deployment_name = 'worker' + str(count) + '-deployment'
    pod_label = 'worker' + str(count)
    container_name = 'worker' + str(count)

    # CSV operations
    rows = read_csv()
    _rows = [row for row in rows]
    for i, row in enumerate(_rows):
        if row['Status'] == 'Free':
            target_row = row
            _rows[i]['Status'] = 'Running'
            _rows[i]['Deployment'] = deployment_name
    write_csv(_rows)

    node_name = target_row['Node']
    create_deployment(node_name, deployment_name, pod_label, container_name)
    print('Create new deployment: '+ deployment_name)

    # create service here
    svc_name = 'worker' + str(count) + '-service'
    selector_label = pod_label
    _port = 2343
    create_svc(svc_name, selector_label, _port, node_port)
    print('Create new service: ' + svc_name)

    # notify haproxy to update configuration file
    notify_haproxy(socket, 'scale-in', backend_name, node_name, target_row['Address'], target_row['Port'])


# Delete the last added deployment
def scale_out(socket, count):
    # delete deployment
    deployment_name = 'worker' + str(count) + '-deployment'
    drop_deployment = 'kubectl delete deployment ' + deployment_name
    os.system(drop_deployment)

    # CSV operations
    rows = read_csv()
    _rows = [row for row in rows]
    for i, row in enumerate(_rows[:]):
        if row['Deployment'] == deployment_name:
            target_row = row
            _rows[i]['Status'] = 'Free'
            _rows[i]['Deployment'] = 'None'
    write_csv(_rows)
    
    print('Delete deployment: ' + deployment_name)
    time.sleep(5)

    # delete service
    svc_name = 'worker' + str(count) + '-service'
    drop_svc = 'kubectl delete svc ' + svc_name
    os.system(drop_svc)
    print('Delete service: ' + svc_name)

    # notify haproxy to update configuration file
    notify_haproxy(socket, 'scale-out', backend_name, target_row['Node'], target_row['Address'], target_row['Port'])

# Notify HAproxy to update
def notify_haproxy(socket, option, backend, host_name, address, port):
    msg = {'option': option, 'backend': backend, 'host_name': host_name, 'address': address, 'port': port}
    socket.send_json(msg)
    _recv = socket.recv_string()
    print('Recv Ack msg from HAproxy server: %s' % _recv)


def main(haproxy_address, haproxy_port):
    rep_socket = build_REP_socket()
    req_socket = build_REQ_socket(haproxy_address, haproxy_port)
    count = 0
    node_port = 30000
    while True:
        msg = rep_socket.recv_string()
        if msg == 'scale-in':
            count += 1
            scale_in(req_socket, count, node_port)
        elif msg == 'scale-out':
            scale_out(req_socket, count)
            count -= 1
        else:
            print('Current max number is ' + msg)
        rep_socket.send_string('Ack')

