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
import random
from K8sOperations import K8sOperations as K8sOp


images = ['docgroupvandy/xceptionkeras', 'docgroupvandy/k8s-demo', 'docgroupvandy/vgg16keras', 'docgroupvandy/vgg19keras', 'docgroupvandy/resnet50keras', 'docgroupvandy/inceptionv3keras', 'docgroupvandy/inceptionresnetv2keras',
          'docgroupvandy/mobilenetkeras', 'docgroupvandy/densenet121keras', 'docgroupvandy/densenet169keras', 'docgroupvandy/densenet201keras', 'docgroupvandy/word2vec_google', 'docgroupvandy/speech-to-text-wavenet', 'docgroupvandy/word2vec_glove']

def timeMeasurementExperiment(hasImage, output_file, node_name, node_address):
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
    if hasImage is False:
        worker_socket = connect_worker()

    for j in range(len(images)):
        print('Image: %s\n' % images[j])
        total_time = [images[j]]
        for k in range(10):
            print('Test-%d' % (k+1))

            # create deployment here
            node_name = node_name
            deployment_name = node_name + '-' + str(random.randint(1, 1000)) + '-deployment'
            pod_label = node_name + '-' + str(random.randint(1, 1000)) + '-pod'
            image_name = images[j]
            container_name = pod_label
            # cpu_requests = '0.5'
            # cpu_limits = '1.0'
            start = datetime.datetime.now()
            k8sop.create_deployment(node_name, deployment_name, pod_label, image_name, container_name,  cpu_requests, cpu_limits, container_port=7000)
            print('Create deployment: %s' % deployment_name)

            svc_name = node_name + '-' + str(random.randint(1, 1000)) + '-service'
            selector_label = pod_label
            k8sop.create_svc(svc_name, selector_label)
            print('Create service: %s' % svc_name)
            
            print('Waiting for container to load model...')
            
            while True:
                try:
                    url = 'http://%s:30000/predict' % node_address
                    crl = pycurl.Curl()
                    crl.setopt(pycurl.POST, 1)
                    crl.setopt(pycurl.HTTPPOST, [("image", (crl.FORM_FILE, "owl.jpg"))])
                    crl.setopt(pycurl.URL, url)
                    crl.perform()

                    break
                except pycurl.error as er:
                    print(er)

            end = datetime.datetime.now()

            duration = (end - start).seconds
            total_time.append(duration)

            os.system('kubectl delete svc %s' % svc_name)
            os.system('kubectl delete deploy --all')

            # notify node to delete image
            if hasImage is False:
                worker_socket.send_string('delete:' + images[j])
                worker_socket.recv_string()
            time.sleep(10)

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
    timeMeasurementExperiment(False, 'ContainerPrepareTimeReport.csv', 'kang4', '129.59.107.141')
    timeMeasurementExperiment(True, 'ContainerPrepareTimeReport(image-available)', 'kang5', '129.59.107.144')

if __name__ == '__main__':
    main()
