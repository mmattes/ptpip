#!/usr/bin/env python
# -*- coding: utf-8 -
import uuid
import time
import socket
import struct

from threading import Thread


class PtpIpConnection(object):

    """docstring for PtpIP"""
    def __init__(self):
        super(PtpIpConnection, self).__init__()
        self.session = None
        self.session_events = None
        self.session_id = None
        self.cmd_queue = []
        self.event_queue = []
        self.object_queue = []

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
        while True:
            if len(self.cmd_queue) == 0:
                # do a ping receive a pong (same as ping) as reply to keep the connection alive
                # couldnt get any reply onto a propper PtpIpPing packet so i am querying the status
                # of the device
                ptpip_packet_reply = self.send_recieve_ptpip_packet(PtpIpCmdRequest(cmd=0x90C8),
                    self.session)
                if isinstance(ptpip_packet_reply, PtpIpCmdResponse):
                    time.sleep(1)
                    continue
            else:
                # get the next command from command the queue
                ptip_cmd = self.cmd_queue.pop()
                ptpip_packet_reply = self.send_recieve_ptpip_packet(ptip_cmd, self.session)
                if (ptpip_packet_reply.ptp_response_code == 0x2001 and \
                        ptpip_packet_reply.ptp_response_code == 0x2019):
                    print "Cmd send successfully"
                else:
                    print "cmd reply is: " + str(ptpip_packet_reply.ptp_response_code)

            # wait 1 second before new packets are processed/send to the camera
            time.sleep(1)
            pass

    def send_ptpip_cmd(self, ptpip_packet):
        self.cmd_queue.append(ptpip_packet)

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
        if isinstance(ptpip_packet, PtpIpInitCmdReq):
            self.send_data(ptpip_packet.data(), session)

            # set the session id of the object if the reply is of type PtpIpInitCmdAck
            ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

            if isinstance(ptpip_packet_reply, PtpIpInitCmdAck):
                self.session_id = ptpip_packet_reply.session_id

        elif isinstance(ptpip_packet, PtpIpEventReq):
            self.send_ptpip_event_req(ptpip_packet, session)

            ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

        elif isinstance(ptpip_packet, PtpIpCmdRequest) and ptpip_packet.ptp_cmd == 0x90C7:
            self.send_data(ptpip_packet.data(), session)

            ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

            if isinstance(ptpip_packet_reply, PtpIpStartDataPacket):
                data_length = struct.unpack('I', ptpip_packet_reply.length)[0]
                ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))
                data = ptpip_packet_reply.data
                while isinstance(ptpip_packet_reply, PtpIpDataPacket):
                    data = data + ptpip_packet_reply.data
                    ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

            if data_length == len(data):
                events = PtpIpEventFactory(data).get_events()
                for event in events:
                    self.event_queue.append(event)

            ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

        elif isinstance(ptpip_packet, PtpIpCmdRequest) and ptpip_packet.ptp_cmd == 0x1009:
            self.send_data(ptpip_packet.data(), session)

            ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

            if isinstance(ptpip_packet_reply, PtpIpStartDataPacket):
                data_length = struct.unpack('I', ptpip_packet_reply.length)[0]
                ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))
                data = ptpip_packet_reply.data
                while isinstance(ptpip_packet_reply, PtpIpDataPacket):
                    data = data + ptpip_packet_reply.data
                    ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

            if data_length == len(data):
                self.object_queue.append(PtpIpDataObject(ptpip_packet.param1, data))

            ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

        else:
            self.send_data(ptpip_packet.data(), session)

            ptpip_packet_reply = PtpIpPacket().factory(data=self.recieve_data(session))

        return ptpip_packet_reply

    def send_ptpip_event_req(self, ptpip_packet, session):
        # add the session id of the object itself if it is not specified in the package
        if ptpip_packet.session_id is None:
                ptpip_packet.session_id = self.session_id
        self.send_data(ptpip_packet.data(), session)

    def send_data(self, data, session):
        session.send(struct.pack('I', len(data) + 4) + data)

    def recieve_data(self, session):
        data = session.recv(4)
        (data_length,) = struct.unpack('I', data)
        print "Laenge des Paketes: " + str(data_length)
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
            print "Cmd Type: " + str(struct.unpack('I', data[0:4])[0])
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
        elif self.cmdtype == 9:
            return PtpIpStartDataPacket(data[4:])
        elif self.cmdtype == 10:
            return PtpIpDataPacket(data[4:])
        elif self.cmdtype == 12:
            return PtpIpEndDataPacket(data[4:])
        elif self.cmdtype == 13:
            return PtpIpPing(data[4:])

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
    Operation Code Description
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
    0x1014 GetDevicePropDesc
    0x1015 GetDevicePropValue
    0x1016 SetDevicePropValue
    0x101B GetPartialObject
    0x90C0 InitiateCaptureRecInSdram
    0x90C1 AfDrive
    0x90C2 ChangeCameraMode
    0x90C3 DeleteImagesInSdram
    0x90C4 GetLargeThumb
    0x90C7 GetEvent
    0x90C8 DeviceReady
    0x90C9 SetPreWbData
    0x90CA GetVendorPropCodes
    0x90CB AfAndCaptureRecInSdram
    0x90CC GetPicCtrlData
    0x90CD SetPicCtrlData
    0x90CE DeleteCustomPicCtrl
    0x90CF GetPicCtrlCapability
    0x9201 StartLiveView
    0x9202 EndLiveView
    0x9203 GetLiveViewImage
    0x9204 MfDrive
    0x9205 ChangeAfArea
    0x9206 AfDriveCancel
    0x9207 InitiateCaptureRecInMedia
    0x9209 GetVendorStorageIDs
    0x920A StartMovieRecInCard
    0x920B EndMovieRec
    0x920C TerminateCapture
    0x9400 GetPartialObjectHighSpeed
    0x9407 SetTransferListLock
    0x9408 GetTransferList
    0x9409 NotifyFileAcquisitionStart
    0x940A NotifyFileAcquisitionEnd
    0x940B GetSpecificSizeObject
    0x9801 GetObjectPropsSupported
    0x9802 GetObjectPropDesc
    0x9803 GetObjectPropValue
    0x9805 GetObjectPropList
    """
    def __init__(self, data=None, cmd=None, param1=None, param2=None, param3=None, param4=None,
                param5=None):
        super(PtpIpCmdRequest, self).__init__()
        self.cmdtype = struct.pack('I', 0x06)
        self.unkown = struct.pack('I', 0x01)
        self.ptp_cmd = cmd
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3
        self.param4 = param4
        self.param5 = param5
        # Todo: Transaction ID generieren
        self.transaction_id = struct.pack('I', 0x06)
        self.args = ''
        if self.param1 is not None:
            self.args = self.args + struct.pack('L', self.param1)

        if self.param2 is not None:
            self.args = self.args + struct.pack('L', self.param2)

        if self.param3 is not None:
            self.args = self.args + struct.pack('L', self.param3)

        if self.param4 is not None:
            self.args = self.args + struct.pack('L', self.param4)

        if self.param5 is not None:
            self.args = self.args + struct.pack('L', self.param5)

    def data(self):
        return self.cmdtype + self.unkown + struct.pack('H', self.ptp_cmd) + \
            self.transaction_id + self.args


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


class PtpIpStartDataPacket(PtpIpPacket):
    """docstring for Start_Data_Packet"""
    def __init__(self, data=None):
        self.cmdtype = struct.pack('I', 0x09)
        super(PtpIpStartDataPacket, self).__init__()
        if data is not None:
            self.transaction_id = data[0:4]
            self.length = data[4:8]


class PtpIpDataPacket(PtpIpPacket):
    """docstring for Start_Data_Packet"""
    def __init__(self, data=None):
        self.cmdtype = struct.pack('I', 0x10)
        super(PtpIpDataPacket, self).__init__()
        if data is not None:
            self.transaction_id = data[0:4]
            self.data = data[4:]


class PtpIpCancelTransaction(PtpIpPacket):
    """docstring for Start_Data_Packet"""
    def __init__(self, data=None):
        self.cmdtype = struct.pack('I', 0x11)
        super(PtpIpCancelTransaction, self).__init__()
        if data is not None:
            self.transaction_id = data[0:4]


class PtpIpEndDataPacket(PtpIpPacket):
    """docstring for Start_Data_Packet"""
    def __init__(self, data=None):
        self.cmdtype = struct.pack('I', 0x12)
        super(PtpIpEndDataPacket, self).__init__()
        if data is not None:
            self.transaction_id = data[0:4]
            print "transaction_id: " + str(struct.unpack('I', self.transaction_id)[0])
            self.data = data[4:]


class PtpIpPing(PtpIpPacket):
    """docstring for Start_Data_Packet"""
    def __init__(self, data=None):
        self.cmdtype = struct.pack('I', 0x13)
        super(PtpIpPing, self).__init__()
        if data is not None:
            self.data = ''

    def data(self):
        return self.cmdtype


class PtpIpEvent(object):
    """
    EventCode Description
    0x4001 CancelTransaction
    0x4002 ObjectAdded
    0x4003 ObjectRemoved
    0x4004 StoreAdded
    0x4005 StoreRemoved
    0x4006 DevicePropChanged
    0x4007 ObjectInfoChanged
    0x4008 DeviceInfoChanged
    0x4009 RequestObjectTransfer
    0x400A StoreFull
    0x400C StorageInfoChanged
    0x400D CaptureComplete
    0xC101 ObjectAddedInSdram
    0xC102 CaptureCompleteRecInSdram
    0xC105 RecordingInterrupted

    """
    def __init__(self, event_code, event_parameter):
        super(PtpIpEvent, self).__init__()
        self.event_code = int(event_code)
        self.event_parameter = int(event_parameter)


class PtpIpEventFactory(object):
    """
    This is a factory to produce an array of PtpIpEvent objects if it got passd a data reply
    from a GetEvent request 0x90C7
    """
    def __init__(self, data):
        super(PtpIpEventFactory, self).__init__()
        # create an empty array for the PtpIpEvent object which will be replied
        self.events = []

        # get the amount of events passed from the data passed to the factory
        amount_of_events = struct.unpack('H', data[0:2])[0]

        # set an counter and an offset of 2 as the first two bytes are already processed
        counter = 1
        offset = 2
        while counter <= amount_of_events:
            # get the event_code which consists of two bytes
            event_code = str(struct.unpack('H', data[offset:offset+2])[0])

            # get the event_parameter which consists of 4 bytes
            event_parameter = str(struct.unpack('I', data[offset+2:offset+6])[0])
            self.events.append(PtpIpEvent(event_code, event_parameter))

            # increase the offset by 6 to get to the next event_code and event_parameter pair
            offset = offset + 6
            counter = counter + 1

    def get_events(self):
        return self.events


class PtpIpDataObject(object):
    """docstring for PtpIpDataObject"""
    def __init__(self, object_handle, data):
        super(PtpIpDataObject, self).__init__()
        self.object_handle = object_handle
        self.data = data
