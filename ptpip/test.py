#!/usr/bin/env python
# -*- coding: utf-8 -
import socket


def Socket():
    host = 'localhost'
    # host = '192.168.1.1'
    port = 15740
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    while 1:
        (clientsocket, address) = s.accept()
        print 'Connected with ' + address[0] + ':' + str(address[1])
        daten = clientsocket.recv(1024)
        print daten

Socket()
