#!/usr/bin/python

# monitor Huawei USB dongle and when sms arrives set up
# a reverse ssh tunnel to a cloud server to enable
# outside apps to contact the pis in your network
# note: this assumes you have generated public ssh key
# and copied it to your cloud server
# cd ~/.ssh, ssh-keygen -t rsa, ssh-copy-id -i id_rsa.pub <u>@<host>
# setup cloud server open ssh server to use public key auth:
# http://www.linux.org/threads/how-to-force-ssh-login-via-public-key-authentication.4253/

# thru the tunnel you can ssh commands to other pi's in the network
# to allow uplink comms, set up pi as a router

import pi_sms
import requests
import logging
import os
import signal
import time
import subprocess
import threading
import atexit

NORMAL_POLL = 15
ACCEPTED_NUMBERS = [u'+xxxxxxx']
CLOUD_USER = 'zzz'
CLOUD_SERVER = 'xxxx'
SSH_PIPE_UP = 3600
ACK_SMS = False
SEND_FAULT_SMS = True
OPEN_COMMAND = 'open'
CLOSE_COMMAND = 'close'
INFO_COMMAND = 'info'

logger = logging.getLogger(__file__)

@atexit.register
def log_exit():
    logger.info('Program terminated')


class PiComms(object):
    def __init__(self):
        self.s = requests.Session()
        self.huawei_found = False
        self.connected = False
        self.ssh_pipe = None
        self.sleep = NORMAL_POLL
        self.ssh_tunnel = None
        self.timer = None
        # this is not needed due to interpreter lock
        self.lock = threading.Semaphore()
        logger.info('Pi client started')

    def handle_sms(self, sms):
        phone = sms.get('phone')
        content = sms.get('content')
        if phone in ACCEPTED_NUMBERS:
            cmd = content.strip().lower()
            if cmd == OPEN_COMMAND:
                self.phone = phone
                self.open_reverse_ssh()
            elif cmd == CLOSE_COMMAND:
                self.phone = phone
                self.clear_ssh_tunnel(reason='User command')
            elif cmd == INFO_COMMAND:
                #todo for future
                pass

    def clear_ssh_tunnel(self, reason='timeout'):
        self.lock.acquire()
        error_flag = False
        if self.ssh_tunnel:
            proc_status = self.ssh_tunnel.poll()
            if proc_status is None:
                os.kill(self.ssh_tunnel.pid, signal.SIGUSR1)
                logger.info('ssh reverse tunnel closed. Reason: {reason}'.format(reason = reason))
            elif proc_status:
                errors = ', '.join([line.strip() for line in self.ssh_tunnel.stderr])
                if errors:
                    logger.error('ssh exited with errors: {errors}'.format(errors=errors))
                if SEND_FAULT_SMS and self.phone:
                    pi_sms.send_sms(self.s, self.phone, 'SSH tunnel error. Log: {log}'.format(log=errors))
                    error_flag = True
            ssh_info = ', '.join([l.strip() for l in self.ssh_tunnel.stdout])
            if ssh_info:
                logger.info('ssh event: {event}'.format(event=ssh_info))
        if self.timer:
            self.timer.cancel()
            self.timer = None
        if ACK_SMS and self.phone and not error_flag:
            pi_sms.send_sms(self.s, self.phone, 'SSH tunnel closed')
        self.ssh_tunnel = None
        self.phone = None
        self.lock.release()

    def open_reverse_ssh(self):
        if not self.ssh_tunnel:
            logger.info('Opened reverse SSH tunnel via {user}:{server}'.format(user=CLOUD_USER, server=CLOUD_SERVER))
            self.ssh_tunnel = subprocess.Popen(['ssh', '-nNT', '-o', 'TCPKeepAlive=yes', '-R', '2222:localhost:22', CLOUD_USER + '@' + CLOUD_SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ACK_SMS and self.phone:
                time.sleep(10)
                if self.ssh_tunnel.poll() is None:
                    pi_sms.send_sms(self.s, self.phone, 'SSH tunnel set up')
            self.timer = threading.Timer(SSH_PIPE_UP, self.clear_ssh_tunnel)
            self.timer.start()

    def run(self):
        while True:
            try:
                smss = pi_sms.read_sms(self.s)
                if not self.huawei_found:
                    self.huawei_found = True
                    logger.info('Found Huawei Dongle')
                if not self.connected:
                    self.connected = True
                    logger.info('Data Connection Found')
                for sms in smss:
                    self.handle_sms(sms)
                if self.ssh_tunnel and not self.ssh_tunnel.poll() is None:
                    self.clear_ssh_tunnel()
            except pi_sms.DeviceNotReachable, e:
                if self.huawei_found:
                    self.huawei_found = False
                    self.connected = False
                    logger.error('Lost Huawei Dongle: %s' % str(e))
            except pi_sms.NotConnected, e:
                if self.connected:
                    self.connected = False
                    logger.error('Huawei dropped from network')
                if not self.huawei_found:
                    self.huawei_found = True
                    logger.info('Found Huawei Dongle')
            except Exception, e:
                logger.error('unexpected exception: %s' % str(e))
            time.sleep(self.sleep)

if __name__ == "__main__":
    fname = os.path.join(os.path.dirname(__file__), 'picommslogger.log')
    logging.basicConfig(filename=fname, format='%(levelname)s: %(asctime)s %(message)s',level=logging.WARNING)
    logger.setLevel(logging.INFO)

    pi_comm = PiComms()
    pi_comm.run()
