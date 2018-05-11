#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import yaml
import zmq
import time
from kubernetes import client, config

image_name = 'zhuangweikang/streamingml_worker'
container_port = 2341

def create_deployment(deployment_name, pod_label, container_name):
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
        spec=client.V1PodSpec(containers=[container]))

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
    spec.ports = [client.V1ServicePort(protocol="TCP", port=_port, target_port=_node_port)]

    service.spec = spec

    # create service
    api_instance.create_namespaced_service(namespace="default", body=service)


def build_socket():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:2342')
    return socket


def main():
    socket = build_socket()
    count = 0
    node_port = 30000
    while True:
        msg = socket.recv_string()
        if msg == 'scale-in':
            count += 1
            # create deployment here
            deployment_name = 'worker' + str(count) + '-deployment'
            pod_label = 'worker' + str(count)
            container_name = 'worker' + str(count)
            create_deployment(deployment_name, pod_label, container_name)
            print('Create new deployment: '+ deployment_name)

            # create service here
            svc_name = 'worker' + str(count) + '-service'
            selector_label = pod_label
            _port = 2341
            node_port += 1
            create_svc(svc_name, selector_label, _port, node_port)
            print('Create new service: ' + svc_name)

        elif msg == 'scale-out':
            # delete deployment
            deployment_name = 'worker' + str(count) + '-deployment'
            drop_deployment = 'kubectl delete deployment ' + deployment_name
            os.system(drop_deployment)
            print('Delete deployment: ' + deployment_name)
            time.sleep(10)
            count -= 1

            # delete service
            svc_name = 'worker' + str(count) + '-service'
            drop_svc = 'kubectl delete svc ' + svc_name
            os.system(drop_svc)
            print('Delete service: ' + svc_name)
            node_port -= 1
            
        else:
            print('Current max number is ' + msg)
        socket.send_string('Ack')


main()
