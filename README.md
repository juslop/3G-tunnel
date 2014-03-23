3G-dongle-tunnel
================

Access your home network behind 3G Dongle from outside.  Huawei 3131 API included.

3G modems typically do not have public IP address you can connect to from outside. Also operators may have NAT/Firewall solutions that cut down always-on tcp connections that are not regularly used.

This solution enables you to send sms to Huawei 3G dongle, which opens a reverse SSH tunnel to a "cloud" server with public IP address. You can then connect to your home network thru the "cloud" server. For example you can watch live video from RaspiCams.


Requirements
============

- Home computer with Linux or OSX operating system, not tested with Windows:
  - Python 2.7
  - Python libraries: BeautifulSoup, requests (sudo pip install BeautifulSoup, requests)
  - Huawei 3131 modem set to connect automatically (HiLink mode).
    - plug the modem to your pc and navigate in your browser to http://hi.link and set this there
  - usb-modeswitch library installed (sudo apt-get install usb-modeswitch)
- A cloud server with public IP address running open ssh, most unix and linux distros have it

SSH Setup
=========
- You need to create public ssh key in your home network machine: cd ~/.ssh, ssh-keygen -t rsa
- copy it to your cloud server
  - ssh-copy-id id_rsa.pub user@host
- Python script can now connect your cloud server without password

Setup
=====

If you use raspberry pi, you need to connect the 3G dongle to powered USB hub. Pi's USB interface does not provide enough power.

In pi check with command lsusb that 3G modem has switched from storage mode to modem mode. It should show ID 12d1:14db:
- Bus 001 Device 013: ID 12d1:14db Huawei Technologies Co., Ltd. 

In pi the Huawei 3131 emulates eth port, eth1. You need to get IP address from operator before the script starts to work. You can check if device has ip address by: 
- ifconfig eth1

eth1      Link encap:Ethernet  HWaddr 58:2c:80:13:92:63  
          inet addr:192.168.1.100  Bcast:192.168.1.255  Mask:255.255.255.0
...

- if no inet addr, run: dhclient eth1
