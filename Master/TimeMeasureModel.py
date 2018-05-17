#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import csv
import zmq
import datetime
import time
import socket
import pycurl
import urllib
import socket
import simplejson
import random
import threading
from K8sOperations import K8sOperations as K8sOp


images = {
    'docgroupvandy/xceptionkeras' : 7000, 
    'docgroupvandy/vgg16keras': 7001, 
    'docgroupvandy/vgg19keras' : 7002, 
    'docgroupvandy/resnet50keras' : 7003, 
    'docgroupvandy/inceptionv3keras': 7004, 
    'docgroupvandy/inceptionresnetv2keras' : 7005,
    'docgroupvandy/mobilenetkeras' : 7006, 
    'docgroupvandy/densenet121keras' : 7007, 
    'docgroupvandy/densenet169keras' : 7008, 
    'docgroupvandy/densenet201keras' : 7009, 
    'docgroupvandy/word2vec_google': 7010, 
    'docgroupvandy/word2vec_glove': 7011}

def timeMeasurementExperiment(hasImage, output_file, node_name, node_address, node_port):
    def write_csv(row, csv_file=output_file):
        headers = ['Image', 'Test1', 'Test2', 'Test3', 'Test4', 'Test5', 'Test6', 'Test7', 'Test8', 'Test9', 'Test10', 'Average']
        with open(csv_file, 'a') as f:
            f_csv = csv.DictWriter(f, headers)
            data = {}
            for i in range(len(row)):
                data.update({headers[i]:row[i]})
            f_csv.writerow(data)


    def connect_worker(address='tcp://%s:2555' % node_address):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(address)
        return socket


    # create one deployment in each node
    k8sop = K8sOp()
    worker_socket = connect_worker()

    for j in range(len(images.items())):
        print('Image: %s\n' % images.items()[j][0])
        total_time = [images.items()[j][0]]
        for k in range(10):
            print('Test-%d' % (k+1))

            # create deployment here
            node_name = node_name
            deployment_name = node_name + '-' + str(random.randint(1, 1000)) + '-deployment'
            pod_label = node_name + '-' + str(random.randint(1, 1000)) + '-pod'
            image_name = images.items()[j][0]
            container_name = pod_label
            # cpu_requests = '3.0'
            # cpu_limits = '4.0'
            start = datetime.datetime.now()
            k8sop.create_deployment(node_name, deployment_name, pod_label, image_name, container_name, None, None, container_port=images.items()[j][1])
            print('Create deployment: %s' % deployment_name)

            svc_name = node_name + '-' + str(random.randint(1, 1000)) + '-service'
            selector_label = pod_label
            k8sop.create_svc(svc_name, selector_label, _node_port=node_port)
            print('Create service: %s' % svc_name)
            
            print('Waiting for container to load model...')
            
            while True:
                try:
                    url = 'http://%s:%d/predict' % (node_address, node_port)
                    crl = pycurl.Curl()
                    crl.setopt(pycurl.POST, 1)
                    crl.setopt(pycurl.HTTPPOST, [("image", (crl.FORM_FILE, "owl.jpg"))])
                    crl.setopt(pycurl.URL, url)
                    crl.setopt(pycurl.CONNECTTIMEOUT, 1)
                    crl.setopt(pycurl.TIMEOUT, 5)
                    crl.perform()
                    crl.close()
                    break
                except pycurl.error as er:
                    print(er)
                    crl.close()
                    time.sleep(1)

            end = datetime.datetime.now()

            duration = (end - start).seconds
            total_time.append(duration - 1)

            os.system('kubectl delete svc %s --force --now' % svc_name)
            os.system('kubectl delete deploy %s --now --force' % deployment_name)

            time.sleep(1)
            # notify node to delete image
            if hasImage is False:
                worker_socket.send_string('False:' + images.items()[j][0])
                worker_socket.recv_string()
            else:
                worker_socket.send_string('True:' + images.items()[j][0])
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


def main():
    thr1 = threading.Thread(target=timeMeasurementExperiment, args=(False, 'ContainerPrepareTimeReport.csv', 'kang4', '129.59.107.141', 30000, ))
    thr1.setDaemon(True)
    thr2 = threading.Thread(target=timeMeasurementExperiment, args=(True, 'ContainerPrepareTimeReport(image-available)', 'kang5', '129.59.107.144', 30001, ))
    thr2.setDaemon(True)

    thr1.start()
    thr2.start()

    while True:
        pass
    
if __name__ == '__main__':
    main()
