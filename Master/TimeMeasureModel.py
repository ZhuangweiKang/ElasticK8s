#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import csv
import simplejson
import zmq
import time
from K8sOperations import K8sOperations as K8sOp

# Measure the time required to downloading image and make the container ready
# total_time = creating_deployment + schedual_deployment + downloading_image + create_container
def measureContainerPrepareTime(pod_label):
    ready_flag = init_flag = False
    while (ready_flag and init_flag) is False:
        try:
            command = 'kubectl get pods -l app=%s -o json' % pod_label
            obj = os.popen(command)
            obj = simplejson.loads(obj.read())
            conditions = obj['items'][0]['status']['conditions']
            for condition in conditions:
                if condition['type'] == 'Initialized' and condition['status'] == 'True':
                    init_flag = True
                    initialized = {'type': 'Initialized', 'time': condition['lastTransitionTime']}
                if condition['type'] == 'Ready' and condition['status'] == 'True':
                    ready_flag = True
                    ready = {'type': 'Ready', 'time': condition['lastTransitionTime']}
        except Exception:
            continue

    print('Initialized: %s' % initialized)
    print('Ready: %s' % ready)

    # get duration between initialized state and ready state
    def parse_time(_time):
        _time = _time.split('T')[1].split('Z')[0].split(':')
        hour = int(_time[0])
        minute = int(_time[1])
        second = int(_time[2])
        return hour, minute, second

    _inits = parse_time(initialized['time'])
    _ready = parse_time(ready['time'])

    duration = 3600 * (_ready[0] - _inits[0]) + 60 * (_ready[1] - _inits[1]) + (_ready[2] - _inits[2])

    print('Total time of making container ready is %ds' % duration)
    return duration


def timeMeasurementExperiment(hasImage):
    images = ['docgroupvandy/xceptionkeras', 'docgroupvandy/k8s-demo', 'docgroupvandy/vgg16keras', 'docgroupvandy/vgg19keras', 'docgroupvandy/resnet50keras', 'docgroupvandy/inceptionv3keras', 'docgroupvandy/inceptionresnetv2keras', 'docgroupvandy/mobilenetkeras', 'docgroupvandy/densenet121keras', 'docgroupvandy/densenet169keras', 'docgroupvandy/densenet201keras', 'docgroupvandy/word2vec_google', 'docgroupvandy/speech-to-text-wavenet', 'docgroupvandy/word2vec_glove']
    def clear_deploy():
        command = 'kubectl delete deploy --all'
        _exec = os.popen(command)
        print(_exec.read())

    def write_csv(row, csv_file='./ContainerPrepareTimeReport.csv'):
        headers = ['Image', 'Test1', 'Test2', 'Test3', 'Test4', 'Test5', 'Test6', 'Test7', 'Test8', 'Test9', 'Test10', 'Average']
        with open(csv_file, 'a') as f:
            f_csv = csv.DictWriter(f, headers)
            data = {}
            for i in range(len(row)):
                data.update({headers[i]:row[i]})
            f_csv.writerow(data)


    def connect_worker(address='tcp://129.59.107.141:2555'):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(address)
        return socket


    # create one deployment in each node
    k8sop = K8sOp()
    if hasImage is False:
        worker_socket = connect_worker()
    clear_deploy()
    time.sleep(3)
    for j in range(len(images)):
        print('Image: %s\n' % images[j])
        total_time = [images[j]]
        for k in range(10):
            print('Test-%d' % (k+1))
            node_name = 'kang4'
            deployment_name = 'kang4-deployment'
            pod_label = 'worker4'
            image_name = images[j]
            container_name = pod_label
            cpu_requests = '0.5'
            cpu_limits = '1.0'
            k8sop.create_deployment(node_name, deployment_name, pod_label, image_name, container_name,  cpu_requests, cpu_limits, container_port=7000)

            while True:
                get_deploy = 'kubectl get deploy -o json'
                _exec = os.popen(get_deploy)
                deploy = simplejson.loads(_exec.read())
                if len(deploy['items']) != 0:
                    break

            total_time.append(measureContainerPrepareTime(pod_label))
            clear_deploy()
            print('Waiting for pod to be deleted.')
            while True:
                check_pod = 'kubectl get pods -o json'
                _exec_ = os.popen(check_pod)
                items = simplejson.loads(_exec_.read())
                if len(items['items']) == 0:
                    break

            # notify node to delete image and wait until container is removed
            if hasImage is False:
                worker_socket.send_string('delete:' + images[j])
                worker_socket.recv_string()

        total_time.append(sum(total_time[1:])/10)
        for m, item in enumerate(total_time[:]):
            if m != 0:
                total_time[m] = str(item) + 's'
            else:
                total_time[m] = str(item)
        if hasImage is False:
            write_csv(total_time)
        else:
            write_csv(total_time, 'ContainerPrepareTimeReport(image-available).csv')
        total_time.clear()


timeMeasurementExperiment(False)
timeMeasurementExperiment(True)