#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, json

config_file = '/etc/haproxy/haproxy.cfg'

def fetch():
    records = []
    # Read file into a list
    with open(config_file, 'r') as robj:
        for line in robj:
            records.append(line)
    return records

def write_back(records):
    # Write new configuration info back
    with open(config_file, 'w') as wobj:
        for line in records:
            wobj.write(line)
    print('HAproxy configuration file has been changed.')


def add_server(backend, host_name, address, port):
    records = fetch()
    hasBackend = False
    # insert new server info into list if expected backend is avaliable
    for i, line in enumerate(records[:]):
        if line.strip().startswith('backend ' + backend):
            hasBackend = True
        if i != len(records)-1 and line.strip().startswith('server') and records[i+1].strip().startswith('server') is False:
            new_record = '    server ' + host_name + ' ' + address + ':' + str(port) + ' check inter 100 maxconn 256\n'
            records.insert(i+1, new_record)
            print('Insert new server under backend %s.' % backend)
            break
    
    # if expected backend is unavailable, insert a new backend at the end of file
    if hasBackend is False:
        print('Expected backend is unavailable, backend %s will be inserted at the end of configuration file.' % backend)
        new_records = 'backend ' + backend + '\n' + '    mode tcp\n    fullconn 10000\n    balance source\n' +  '    server ' + host_name + ' ' + address + ':' + str(port) + ' check inter 100 maxconn 256\n'
        records.append(new_records)

    write_back(records)

    # hot reload haproxy


def delete_server(backend, server):
    records = []
    records = fetch()
    hasBackend = False
    for i, line in enumerate(records[:]):
        if line.strip().startswith('backend ' + backend):
            hasBackend = True
        if line.strip().startswith('server ' + server):
            del records[i]
    if hasBackend is False:
        print('Specified backend is unavailable.')
    else:
        write_back(records)
    
    # hot reload haproxy


def hot_reload():
    pass


