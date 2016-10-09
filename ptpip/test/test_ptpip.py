#!/usr/bin/env python
# -*- coding: utf-8 -
import pytest
import struct
import time
from ptpip.ptpip import PtpIpConnection
from ptpip.ptpip import PtpIpInitCmdReq
from ptpip.ptpip import PtpIpInitCmdAck
from ptpip.ptpip import PtpIpEventReq
from ptpip.ptpip import PtpIpEventAck
from ptpip.ptpip import PtpIpCmdRequest
from ptpip.ptpip import PtpIpCmdResponse


class TestPtpIp():

    def test_connect_init_and_event(self):
        ptpip = PtpIpConnection()
        ptpip.open()
        # ptip_cmd = PtpIpInitCmdReq()
        # ptip_packet = ptpip.send_recieve_ptpip_packet(ptip_cmd)
        # assert isinstance(ptip_packet, PtpIpInitCmdAck)
        # session_id = ptip_packet.session_id
        # print session_id
        # ptpip2 = PtpIpConnection()
        # assert ptpip2.connect()
        # ptip_cmd = PtpIpEventReq(session_id=session_id)
        # ptip_packet = ptpip2.send_recieve_ptpip_packet(ptip_cmd)
        # assert isinstance(ptip_packet, PtpIpEventAck)

        # 0x1002 OpenSession
        # ptip_cmd = PtpIpCmdRequest(cmd=0x1002, args=ptpip.session_id)
        # ptip_packet = ptpip.send_recieve_ptpip_packet(ptip_cmd, ptpip.session)
        # assert isinstance(ptip_packet, PtpIpCmdResponse)
        time.sleep(10)

        args = struct.pack('L', 0xffffffff) + struct.pack('L', 0x0000)
        ptip_cmd = PtpIpCmdRequest(cmd=0x9207, args=args)
        ptip_packet = ptpip.send_ptpip_cmd(ptip_cmd)

        time.sleep(20)

        args = struct.pack('L', 0xffffffff) + struct.pack('L', 0x0000)
        ptip_cmd = PtpIpCmdRequest(cmd=0x9207, args=args)
        ptip_packet = ptpip.send_ptpip_cmd(ptip_cmd)

        time.sleep(20)

        args = struct.pack('L', 0xffffffff) + struct.pack('L', 0x0000)
        ptip_cmd = PtpIpCmdRequest(cmd=0x9207, args=args)
        ptip_packet = ptpip.send_ptpip_cmd(ptip_cmd)
        # assert isinstance(ptip_packet, PtpIpCmdResponse)
        # ptip_cmd = PtpIpCmdRequest(cmd=0x90c8, args='')
        # ptip_cmd = PtpIpCmdRequest(cmd=0x90c8, args='')
        # 0x2019
        # ptip_packet = ptpip.send_recieve_ptpip_packet(ptip_cmd, ptpip.session)
        # while (ptip_packet.ptp_response_code == 0x2001 or ptip_packet.ptp_response_code == 0x2019):
        #     ptip_packet = ptpip.send_recieve_ptpip_packet(ptip_cmd, ptpip.session)
        #     print "Device Ready"
        #     pass
        # print ptpip.recieve_data(ptpip.session_events)
        # test = raw_input("Pause:")
        # ptip_cmd = PtpIpCmdRequest(cmd=0x90CB)
        # ptip_packet = ptpip.send_recieve_ptpip_packet(ptip_cmd)
        # assert isinstance(ptip_packet, PtpIpCmdResponse)
        # ptip_cmd = PtpIpCmdRequest(cmd=0x9201)
        # ptip_packet = ptpip.send_recieve_ptpip_packet(ptip_cmd)
        # assert isinstance(ptip_packet, PtpIpCmdResponse)
