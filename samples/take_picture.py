#!/usr/bin/env python
# -*- coding: utf-8 -
import struct
from ptpip.ptpip import PtpIpConnection
from ptpip.ptpip import PtpIpCmdRequest

# open up a PTP/IP connection, default IP and Port is host='192.168.1.1', port=15740
ptpip = PtpIpConnection()
ptpip.open()

# create a PTP/IP command request object and add it to the queue of the PTP/IP connection object
args = struct.pack('L', 0xffffffff) + struct.pack('L', 0x0000)
ptpip_cmd = PtpIpCmdRequest(cmd=0x9207, args=args)
ptpip_packet = ptpip.send_ptpip_cmd(ptpip_cmd)
