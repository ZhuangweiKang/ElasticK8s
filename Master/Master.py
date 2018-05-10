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


def build_socket():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:2342')
    return socket


def main():
    socket = build_socket()
    count = 0
    while True:
        msg = socket.recv_string()
        if msg == 'scale-in':
            count += 1
            deployment_name = 'worker' + str(count) + '-deployment'
            pod_label = 'worker' + str(count)
            container_name = 'worker' + str(count)
            create_deployment(deployment_name, pod_label, container_name)
        elif msg == 'scale-out':
            deployment_name = 'worker' + str(count) + '-deployment'
            drop_deployment = 'kubectl delete deployment ' + deployment_name
            os.system(drop_deployment)
            time.sleep(10)
            count -= 1
        socket.send_string('Ack')


main()
