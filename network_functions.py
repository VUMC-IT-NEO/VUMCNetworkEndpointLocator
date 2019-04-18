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
from pprint import pprint


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

# takes a single IP input, runs a traceroute, and returns a list of every IP hop
def traceroute(ip, max_hops=10, trace_timeout=500):
    ip_pattern = re.compile('([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
    unreach_pattern = re.compile('Request timed out')
    print(f'Tracing route to {ip}....')
    trace_response = subprocess.check_output(f'tracert -h {max_hops} -w {trace_timeout} {ip}', shell=True)
    raw_output = trace_response.decode(encoding='utf-8')
    print(raw_output)
    output_list = raw_output.split('\r\n')
    del output_list[-3:-1]
    match_unreach = unreach_pattern.search(output_list[-2])
    if match_unreach:
        print('Request timed out')
        print('This IP address is not on the network and cannot be traced')
    hop_list = []
    for line in output_list:
        match = ip_pattern.search(line)
        if match:
            matched_value = match.group(0)
            hop_list.append(matched_value)
        else:
            continue
    print('Hop List: \n')
    pprint(hop_list)
    return hop_list

# function to validate whether an IP is a valid VUMC network IP, a public IP, or
# a wireless IP and return the variable ip_type to be used later to determine
# which path the program should take
def vumc_ip_type(ip):
    global ip_type
    ip_type = 0
    octet_list = ip.split('.')
    if octet_list[0] == '10':
        if octet_list[1] == '248' or octet_list[1] == '249' or octet_list[1] == '250' or octet_list[1] == '251':
            print(f'{ip} is a VUMC Wireless IP')
            ip_type += 1
            return ip_type
        else:
            print(f'{ip} is a VUMC wired IP')
            ip_type += 2
            return ip_type
    elif octet_list[0] == '160' and octet_list[1] == '129':
        print(f'{ip} is a VUMC public IP address')
        ip_type += 3
        return ip_type
    elif octet_list[0] == '129' and octet_list[1] == '59':
        print(f'{ip} is a VU public IP address')
        ip_type += 4
        return ip_type
    else:
        print(f'{ip} is not a VUMC IP address')
        ip_type += 5
        return ip_type


#MAIN:

#hop_list = traceroute("10.100.60.8")
#print (hop_list)

'''
user = input("Username: ")
pw = getpass.getpass('Password: ')
ipaddr = input('IP Address: ')

prime_resp = getWirelessIpInfo(user, pw, ipaddr)

print (prime_resp)
'''
