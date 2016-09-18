#!/usr/bin/env python
# -*- coding: utf-8 -
import io
import sys
import time

from PIL import Image
from ptpip.ptpip import PtpIpConnection
from ptpip.ptpip import PtpIpCmdRequest

# open up a PTP/IP connection, default IP and Port is host='192.168.1.1', port=15740
ptpip = PtpIpConnection()
ptpip.open()

# create a PTP/IP command request object and add it to the queue of the PTP/IP connection object
ptpip_cmd = PtpIpCmdRequest(cmd=0x9207, param1=0xffffffff, param2=0x0000)
ptpip_packet = ptpip.send_ptpip_cmd(ptpip_cmd)

# give the thread / connection some time to process the command and thenn close the connection
time.sleep(5)

# get the events from the camera, they will be stored in the event_queue of the ptpip object
ptpip_cmd = PtpIpCmdRequest(cmd=0x90C7)
ptpip_packet = ptpip.send_ptpip_cmd(ptpip_cmd)

# give the thread some time to process the events it recived from the camera
time.sleep(2)

# query the events for the event you are looking for, for example the 0x4002 ObjectAdded if you look
# for a image captured
for event in ptpip.event_queue:
    if event.event_code == 0x4002:
        ptpip_cmd = PtpIpCmdRequest(cmd=0x1009, param1=event.event_parameter)
        ptpip_packet = ptpip.send_ptpip_cmd(ptpip_cmd)

# give the thread some time to get the object
time.sleep(2)

for data_object in ptpip.object_queue:
    data_stream = io.BytesIO(data_object.data)
    img = Image.open(data_stream)
    img.save('/tmp/test.jpg')

# give the thread / connection some time to process the command and thenn close the connection
time.sleep(5)

time.sleep(50000000)

sys.exit()
