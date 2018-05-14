#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import simplejson

# Measure the time required to downloading image and make the container ready
# total_time = creating_deployment + schedual_deployment + downloading_image + create_container
def measureContainerPrepareTime(self, pod_label):
    ready_flag = init_flag = False
    while (ready_flag and init_flag) is False:
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
