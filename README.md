# PTP/IP for Python
PTP/IP for Python (Picture Transfer Protocol/IP) is an implementation of the PTP/IP protocol used to communicate with digital cameras over TCP/IP, for example via Wifi with an Nikon D5300 camera.

Possible commands and response codes can be retrived from the Nikon SDK an may differ from the documented codes within this repository.

I've built, used and tested it with a Nikon D5300 only but it should work with other cameras which do support the PTP/IP protocol. 

Unfortunately there is not really a good documentation available how the PTP/IP protocol works in detail but this webpage here describes it briefly http://gphoto.org/doc/ptpip.php. Basically it is the PTP protocol, which is used to communicate over USB, adapted to a socket TCP/IP connection.