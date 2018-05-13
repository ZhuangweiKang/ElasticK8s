#!/usr/bin/python3
# -*- coding: utf-8 -*-


from kubernetes import client, config


class K8sOperations:
    # Create a deployment on a specific node
    def create_deployment(self, node_name, deployment_name, pod_label, image_name, container_name, container_port=2341):
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
    def create_svc(self, svc_name, selector_label, _port=2343, _node_port=30000):
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
