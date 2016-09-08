#!/usr/bin/env python
# -*- coding: utf-8 -
import socket
import struct
import uuid
import time

from threading import Thread


class PtpIpConnection(object):

    """docstring for PtpIP"""
    def __init__(self):
        super(PtpIpConnection, self).__init__()
        self.session = None
        self.session_events = None
        self.session_id = None
        self.queue = []

    def open(self, host='192.168.1.1', port=15740):
        # Open both session, first one for for commands, second for events
        self.session = self.connect(host=host, port=port)
        self.send_recieve_ptpip_packet(PtpIpInitCmdReq(), self.session)
        self.session_events = self.connect(host=host, port=port)
        self.send_recieve_ptpip_packet(PtpIpEventReq(), self.session_events)

        # 0x1002 OpenSession
        ptip_cmd = PtpIpCmdRequest(cmd=0x1002, param1=struct.unpack('L', self.session_id)[0])
        self.send_recieve_ptpip_packet(ptip_cmd, self.session)

        # Start the Thread which is constantly checking the status of the camera and which is
        # processing new command packages which should be send
        thread = Thread(target=self.communication_thread)
        thread.daemon = True
        thread.start()

    def communication_thread(self):
        ptip_cmd = PtpIpCmdRequest(cmd=0x90c8)
        ptip_packet = self.send_recieve_ptpip_packet(ptip_cmd, self.session)

        while (ptip_packet.ptp_response_code == 0x2001 or ptip_packet.ptp_response_code == 0x2019):
            if (ptip_packet.ptp_response_code == 0x2001 and len(self.queue) > 0):
                self.send_recieve_ptpip_packet(self.queue.pop(), self.session)
            else:
                ptip_cmd = PtpIpCmdRequest(cmd=0x90c8)
                ptip_packet = self.send_recieve_ptpip_packet(ptip_cmd, self.session)

            # wait 1 second before new packets are processed/send to the camera
            time.sleep(1)
            pass

    def send_ptpip_cmd(self, ptpip_packet):
        self.queue.append(ptpip_packet)

    def connect(self, host='192.168.1.1', port=15740):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            s.connect((host, port))
        except socket.error, (value, message):
            if s:
                s.close()
            print "Could not open socket: " + message
        return s

    def send_recieve_ptpip_packet(self, ptpip_packet, session):
        if isinstance(ptpip_packet, PtpIpEventReq):
            if ptpip_packet.session_id is None:
                ptpip_packet.session_id = self.session_id

        self.send_data(ptpip_packet.data(), session)

        ptpip_packet = PtpIpPacket().factory(data=self.recieve_data(session))

        if isinstance(ptpip_packet, PtpIpInitCmdAck):
            self.session_id = ptpip_packet.session_id

        return ptpip_packet

    def send_data(self, data, session):
        session.send(struct.pack('I', len(data) + 4) + data)

    def recieve_data(self, session):
        data = session.recv(4)
        (data_length,) = struct.unpack('I', data)
        while (data_length) > len(data):
            data += session.recv(data_length - len(data))
        return data[4:]


class PtpIpPacket(object):
    """docstring for PtpIpCmd"""
    def __init__(self):
        super(PtpIpPacket, self).__init__()

    def factory(self, data=None):
        if data is None:
            self.cmdtype = None
        else:
            self.cmdtype = struct.unpack('I', data[0:4])[0]

        if self.cmdtype == 1:
            return PtpIpInitCmdReq(data[4:])
        elif self.cmdtype == 2:
            return PtpIpInitCmdAck(data[4:])
        elif self.cmdtype == 3:
            return PtpIpEventReq(data[4:])
        elif self.cmdtype == 4:
            return PtpIpEventAck(data[4:])
        elif self.cmdtype == 5:
            return PtpIpInitFail(data[4:])
        elif self.cmdtype == 6:
            return PtpIpCmdRequest(data[4:])
        elif self.cmdtype == 7:
            return PtpIpCmdResponse(data[4:])

    def data(self):
        pass


class PtpIpInitCmdReq(PtpIpPacket):
    """docstring for PtpIpInitCmd"""
    def __init__(self, data=None):
        super(PtpIpInitCmdReq, self).__init__()
        self.cmdtype = struct.pack('I', 0x01)
        if data is None:
            guid = uuid.uuid4()
            self.guid = guid.bytes
            self.hostname = socket.gethostname() + '\x00'
            self.hostname = self.hostname.encode()
        else:
            self.guid = data[0:16]
            self.hostname = data[16:0]

    def data(self):
        return self.cmdtype + self.guid + self.hostname


class PtpIpInitCmdAck(PtpIpPacket):
    """docstring for PtpIpInitCmd"""
    def __init__(self, data=None):
        super(PtpIpInitCmdAck, self).__init__()
        self.cmdtype = struct.pack('I', 0x02)
        if data is not None:
            self.session_id = data[0:4]
            self.guid = data[4:20]
            self.hostname = data[20:]


class PtpIpEventReq(PtpIpPacket):
    """docstring for PtpIpInitCmd"""
    def __init__(self, data=None, session_id=None):
        super(PtpIpEventReq, self).__init__()
        self.cmdtype = struct.pack('I', 0x03)
        self.session_id = None
        if data is not None:
            self.session_id = data[0:4]
        elif session_id is not None:
            self.session_id = session_id

    def data(self):
        return self.cmdtype + self.session_id


class PtpIpEventAck(PtpIpPacket):
    """docstring for PtpIpInitCmd"""
    def __init__(self, data=None):
        super(PtpIpEventAck, self).__init__()
        self.cmdtype = struct.pack('I', 0x04)


class PtpIpInitFail(PtpIpPacket):
    """docstring for PtpIpInitCmd"""
    def __init__(self, data=None):
        super(PtpIpInitFail, self).__init__()
        self.cmdtype = struct.pack('I', 0x05)


class PtpIpCmdRequest(PtpIpPacket):
    """
    Operation Code Operation Name
    0x1000 Undefined
    0x1001 GetDeviceInfo
    0x1002 OpenSession
    0x1003 CloseSession
    0x1004 GetStorageIDs
    0x1005 GetStorageInfo
    0x1006 GetNumObjects
    0x1007 GetObjectHandles
    0x1008 GetObjectInfo
    0x1009 GetObject
    0x100A GetThumb
    0x100B DeleteObject
    0x100C SendObjectInfo
    0x100D SendObject
    0x100E InitiateCapture
    0x100F FormatStore
    0x1010 ResetDevice
    0x1011 SelfTest
    0x1012 SetObjectProtection
    0x1013 PowerDown
    0x1014 GetDevicePropDesc
    0x1015 GetDevicePropValue
    0x1016 SetDevicePropValue
    0x1017 ResetDevicePropValue
    0x1018 TerminateOpenCapture
    0x1019 MoveObject
    0x101A CopyObject
    0x101B GetPartialObject
    0x101C InitiateOpenCapture
    """
    def __init__(self, data=None, cmd=None, param1=None, param2=None, param3=None, param4=None,
                param5=None):
        super(PtpIpCmdRequest, self).__init__()
        self.cmdtype = struct.pack('I', 0x06)
        self.unkown = struct.pack('I', 0x01)
        self.ptp_cmd = struct.pack('H', cmd)
        # Todo: Transaction ID generieren
        self.transaction_id = struct.pack('I', 0x01)
        self.args = ''
        if param1 is not None:
            self.args = self.args + struct.pack('L', param1)

        if param2 is not None:
            self.args = self.args + struct.pack('L', param2)

        if param3 is not None:
            self.args = self.args + struct.pack('L', param3)

        if param4 is not None:
            self.args = self.args + struct.pack('L', param4)

        if param5 is not None:
            self.args = self.args + struct.pack('L', param5)

    def data(self):
        return self.cmdtype + self.unkown + self.ptp_cmd + self.transaction_id + self.args


class PtpIpCmdResponse(PtpIpPacket):
    """
    ResponseCode Description
    0x2000 Undefined
    0x2001 OK
    0x2002 General Error
    0x2003 Session Not Open
    0x2004 Invalid TransactionID
    0x2005 Operation Not Supported
    0x2006 Parameter Not Supported
    0x2007 Incomplete Transfer
    0x2008 Invalid StorageID
    0x2009 Invalid ObjectHandle
    0x200A DeviceProp Not Supported
    0x200B Invalid ObjectFormatCode
    0x200C Store Full
    0x200D Object WriteProtected
    0x200E Store Read-Only
    0x200F Access Denied
    0x2010 No Thumbnail Present
    0x2011 SelfTest Failed
    0x2012 Partial Deletion
    0x2013 Store Not Available
    0x2014 Specification By Format Unsupported
    0x2015 No Valid ObjectInfo
    0x2016 Invalid Code Format
    0x2017 Unknown Vendor Code
    0x2018 Capture Already Terminated
    0x2019 Device Busy
    0x201A Invalid ParentObject
    0x201B Invalid DeviceProp Format
    0x201C Invalid DeviceProp Value
    0x201D Invalid Parameter
    0x201E Session Already Open
    0x201F Transaction Cancelled
    0x2020 Specification of Destination Unsupported
    """
    def __init__(self, data=None):
        super(PtpIpCmdResponse, self).__init__()
        self.cmdtype = struct.pack('I', 0x07)
        if data is not None:
            self.ptp_response_code = struct.unpack('H', data[0:2])[0]
            self.transaction_id = data[2:6]
            self.args = data[6:]
