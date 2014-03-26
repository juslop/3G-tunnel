3G-tunnel
================

Access your home network behind 3G Dongle from outside.  Huawei 3131 API included.

3G modems typically do not have public IP address you can connect to from outside. Also operators may have NAT/Firewall solutions that cut down always-on tcp connections that are not regularly used.

This solution enables you to send sms to Huawei 3G dongle, which opens a reverse SSH tunnel to a "cloud" server with public IP address. Cloud server port 2222 is used to route ssh connections to your pi. You can then connect with ssh to your home network thru the "cloud" server.

- sms to your Huawei phone number. Content: "open"
- wait 15 seconds and access your pi with ssh via your cloud server
  - ssh -p 2222 pi_username@your.cloudserver.com
  - this ssh connection would contact you pi

Requirements
============

- Raspberry Pi, (tested also in Mac):
  - clone this repository to your pi
  - Python 2.7 (included in Raspbian)
  - Python libraries: BeautifulSoup, requests (sudo pip install BeautifulSoup, requests)
  - Huawei 3131 modem set to connect automatically (HiLink mode).
    - plug the modem to your pc and navigate in your browser to http://hi.link and set this there
    - while there send sms to your phone to check the phone number of dongle
  - usb-modeswitch library installed (sudo apt-get install usb-modeswitch)
- A cloud server with public IP address running open ssh
  - most unix and linux distros have it

SSH Setup
=========
- You need to create public ssh key in pi: cd ~/.ssh, ssh-keygen -t rsa
- copy it to your cloud server
  - ssh-copy-id id_rsa.pub user@host
- Python script can now connect your cloud server without password
- allow port forwarding in cloud server open ssh settings file

Setup modem in Raspberry Pi
===========================

Connect the 3G dongle to powered USB hub. Pi's USB interface does not provide enough power.

In pi check with command lsusb that 3G modem has switched from storage mode to modem mode. It should show ID 12d1:14db:
- Bus 001 Device 013: ID 12d1:14db Huawei Technologies Co., Ltd. 

In pi the Huawei 3131 emulates eth port, eth1. You need to get IP address from operator before the script starts to work. 
- add following to /etc/network/interfaces
  - allow-hotplug eth1
  - iface eth1 inet dhcp

After reboot check if device has ip address by. This also shows Huawei is emulating eth1 port: 
- ifconfig eth1

eth1      Link encap:Ethernet  HWaddr 58:2c:80:13:92:63  
          inet addr:192.168.1.100  Bcast:192.168.1.255  Mask:255.255.255.0

Setup this script to run as Daemon:
===================================

- change the paths to point to your install location in script file
- Script copied from:
  - http://blog.scphillips.com/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/
- Another alternative would be to use Python supervisor library

- chmod 755 client.py
- copy the 3G-tunnel.sh script to etc/init.d (sudo needed)
- chmod it again
- sudo update-rc.d 3G-tunnel.sh defaults
