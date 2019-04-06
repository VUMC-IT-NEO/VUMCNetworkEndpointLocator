#######################################################################
# Collection of Network functions for Python
#
# Author: VUMC IT Network Engineering and Operations
#
#######################################################################

import json
import re
import os
import subprocess
import sys
import paramiko
import pexpect
from piapi import PIAPI
import getpass



def getWirelessIpInfo(un, passw, ip_addr):
    user = un
    pw = passw
    ipaddr = ip_addr

    api = PIAPI("https://10.109.24.16/", user, pw, verify=False)

    reply = api.request("ClientDetails", params={".full": "true", "ipAddress": ipaddr})
    attached_ap = reply[0]['clientDetailsDTO']['apName']
    ssid = reply[0]['clientDetailsDTO']['clientInterface']
    location = reply[0]['clientDetailsDTO']['location']
    ipInfo = "The device you searched for was last seen in " + location + " connected to " + attached_ap + " on the " + ssid + " network."
    return ipInfo



#MAIN:

user = input("Username: ")
pw = getpass.getpass('Password: ')
ipaddr = input('IP Address: ')

prime_resp = getWirelessIpInfo(user, pw, ipaddr)

print (prime_resp)
