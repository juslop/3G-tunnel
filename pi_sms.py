#!/usr/bin/python

# Huawei 3131 3G dongle python API
# Based on the work of http://chaddyhv.wordpress.com/2012/08/13/programming-and-installing-huawei-hilink-e3131-under-linux/
# Usage: Import in your python project and use: send_sms and read_sms
# Test your Dongle by running this file from console and send smss to you dongle
# python /path_to_file/pi_sms.py


import requests
from BeautifulSoup import BeautifulSoup, NavigableString
import time
import sys
import logging
import datetime


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

SMS_LIST_TEMPLATE = '<request>' +\
    '<PageIndex>1</PageIndex>' +\
    '<ReadCount>20</ReadCount>' +\
    '<BoxType>1</BoxType>' +\
    '<SortType>0</SortType>' +\
    '<Ascending>0</Ascending>' +\
    '<UnreadPreferred>0</UnreadPreferred>' +\
    '</request>'

SMS_READ_TEMPLATE = '<request><Index>{index}</Index></request>'

SMS_SEND_TEMPLATE = '<request>' +\
    '<Index>-1</Index>' +\
    '<Phones><Phone>{phone}</Phone></Phones>' +\
    '<Sca></Sca>' +\
    '<Content>{content}</Content>' +\
    '<Length>{length}</Length>' +\
    '<Reserved>1</Reserved>' +\
    '<Date>{timestamp}</Date>' +\
    '</request>'

BASE_URL = 'http://hi.link/api/'

SMS_READ_HEADER = {'referer': 'http://hi.link/html/smsinbox.html?smsinbox'}

class NotConnected(Exception):
    pass

class DeviceNotReachable(Exception):
    pass

def _pretty_traffic(n):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024.0:
            return "%3.1f %s" % (n ,x)
        n /= 1024.0
    return 'unknown'

def _connected(s):
    r1 = s.get(BASE_URL + 'monitoring/status')
    resp = BeautifulSoup(r1.content)
    if resp.connectionstatus.string == u'901':
        return True
    else:
        return False

def _sms_count(s):
    r1 = s.get(BASE_URL + 'monitoring/check-notifications')
    resp = BeautifulSoup(r1.content)
    return int(resp.unreadmessage.string)

def _read_sms_list(s):
    result = []
    r1 = s.post(BASE_URL + 'sms/sms-list', data=SMS_LIST_TEMPLATE, headers=SMS_READ_HEADER)
    resp = BeautifulSoup(r1.content)
    if int(resp.count.string):
        for msg in resp.messages:
            if not isinstance(msg, NavigableString):
                logger.info('SMS Received. From number: {phone}, Content: {content}'.format(phone=msg.phone.string, content=msg.content.string.encode('ascii', 'replace')))
                result.append({'phone':msg.phone.string, 'content':msg.content.string})
                _delete_sms(s, msg.find('index').string)
    return result

def _delete_sms(s, ind):
    r1 = s.post(BASE_URL + 'sms/delete-sms', data=SMS_READ_TEMPLATE.format(index=ind))

def _read_sms(s):
    if _connected(s):
        if _sms_count(s):
            return _read_sms_list(s)
        else:
            return []
    else:
        raise NotConnected('No data link')

def info(s):
    r1 = s.get(BASE_URL + 'monitoring/traffic-statistics')
    resp = BeautifulSoup(r1.content)
    upload = int(resp.totalupload.string)
    download = int(resp.totaldownload.string)
    return 'Modem status: connected: {con}, upload: {up}, download: {down}, total: {tot}'.format(con=_connected(s), up=_pretty_traffic(upload), down=_pretty_traffic(download), tot=_pretty_traffic(upload+download))

def read_sms(s):
    try:
        return _read_sms(s)
    except requests.exceptions.ConnectionError, e:
        raise DeviceNotReachable('Unable to connect to device')

def send_sms(s, phone, content):
    timestamp = datetime.datetime.now() + datetime.timedelta(seconds=15)
    r1 = s.post(BASE_URL + 'sms/send-sms', data=SMS_SEND_TEMPLATE.format(phone=phone, content=content, length=len(content), timestamp=str(timestamp.strftime("%Y-%m-%d %H:%M:%S"))))
    resp = BeautifulSoup(r1.content)
    if resp.response.string == 'OK':
        logger.info('sms sent. Number: {phone}, Content: {content}'.format(phone=phone, content=content))
    else:
        logger.error('sms sending failed. Response from dongle: {r}'.format(r=resp))

if __name__ == "__main__":
    logger.addHandler(logging.StreamHandler())
    s = requests.Session()
    print info(s)
    while True:
        try:
            smss = _read_sms(s)
            if smss:
                print smss
        except requests.exceptions.ConnectionError, e:
            print e
            sys.exit(1)
        time.sleep(10)
