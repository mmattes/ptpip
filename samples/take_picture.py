#!/usr/bin/env python
# -*- coding: utf-8 -
import sys
import time
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

sys.exit()
