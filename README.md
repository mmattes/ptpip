# PTP/IP for Python
PTP/IP for Python (Picture Transfer Protocol/IP) is an implementation of the PTP/IP protocol used to communicate with digital cameras over TCP/IP, for example via Wifi with an Nikon D5300 camera.

Possible commands and response codes can be retrived from the Nikon SDK an may differ from the documented codes within this repository.

I've built, used and tested it with a Nikon D5300 only but it should work with other cameras which do support the PTP/IP protocol. 

Unfortunately there is not really a good documentation available how the PTP/IP protocol works in detail but this webpage here describes it briefly http://gphoto.org/doc/ptpip.php. Basically it is the PTP protocol, which is used to communicate over USB, adapted to a socket TCP/IP connection.

# Quickstart
```python
from ptpip import PtpIpConnection
from ptpip import PtpIpCmdRequest
from threading import Thread

# open up a PTP/IP connection, default IP and Port is host='192.168.1.1', port=15740
ptpip = PtpIpConnection()
ptpip.open()

# Start the Thread which is constantly checking the status of the camera and which is
# processing new command packages which should be send
thread = Thread(target=ptpip.communication_thread)
thread.daemon = True
thread.start()

# create a PTP/IP command request object and add it to the queue of the PTP/IP connection object
ptpip_cmd = PtpIpCmdRequest(cmd=0x9207, param1=0xffffffff, param2=0x0000)
ptpip_packet = ptpip.cmd_queue.append(ptpip_cmd)
```

# Basic concepts

The PtpIpConnection is the basic connection to the camera, the communcation_thread takes what ever PtpIpCmdRequest is appended to the cmd_queue of the PtpIpConnection and sends it to the camera to be processed. 

Whenever the camera is doing something it will create an event which can be queried by a PtpIpCmdRequest which queries the events into the event_queue of the PtpIpConnection

## Query PtpIpEvents
```python
PtpIpCmdRequest(cmd=0x9207, param1=0xffffffff, param2=0x0000)
```

You can now go through the event_queue to find the event you are looking for. For example an 0x4002 ObjectAdded event. This event gives you an object id in the event.event_parameter which can be retrieved with another PtpIpCmdRequest, any object recieved will be added to the object_queue of the PtpIpConnection

## Get an Object
```python
PtpIpCmdRequest(cmd=0x1009, param1=event.event_parameter)
```
