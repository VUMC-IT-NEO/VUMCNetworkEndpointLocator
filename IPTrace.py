import paramiko
from getpass import getpass
import re
import sys
import network_functions
import subprocess
import os
import pprint

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
mac_pattern = re.compile('([0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4})')
int_pattern = re.compile('([a-zA-Z]{1,3}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2})')
po_int_pattern = re.compile('([a-zA-Z]){1,2}[0-9]{1,4}')
ip_pattern = re.compile('IP address: ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
subnet_pattern = re.compile('([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\/[0-9]{1,2})')
ip_only_pattern = re.compile('([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
ip_config_pattern = re.compile('ip address ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
next_hop_pattern = re.compile('\*via ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
static_route_pattern = re.compile('static')
connected_pattern = re.compile('directly connected, via Vlan([0-9]{1,4})')
phone_pattern = re.compile('(IP Phone)')
show_run_int_cmd = 'show run interface '
arp_command = 'show ip arp '
mac_command = 'show mac address-table address '
snmp_command = 'show snmp location'
iproute_cmd = 'show ip route '
cdp_neighbors = 0

# =========================== Main =================================

print ('######################################################')
print ('##### Welcome to the VUMC NEO - IP Trace Program #####')
print ('#####                                            #####')
print ('##### This program will find information about   #####')
print ('##### where the device associated with an IP     #####')
print ('##### is, or was last connected to the network.  ##### ')
print ('###################################################### \n')

# Gather user data
network_functions.get_creds()
root_ip = '10.224.0.251'
alt_root_ip = '10.224.0.252'

while True:
    ip = input('What is the IP you want to trace? ')
    ip_type = network_functions.vumc_ip_type(ip)
    if ip_type == 1:
        ip_info = network_functions.getWirelessIpInfo(ip)
        print(ip_info)
    elif ip_type == 5:
        print(f'{ip} is not a VUMC address and cannot be traced')
    else:
        gateway_info = network_functions.find_gateway(ip, root_ip)
        if gateway_info:
            trace = network_functions.mac_trace(gateway_info, ip)
        if not gateway_info:
            print (f'Gateway IP Not Found. \n')
            retry = input('Would you like to trace another IP? <Y or N>:')
            if retry == 'y' or retry == 'Y':
                continue
            else:
                exit()
    name = input('Would you like to trace another IP? <Y or N>:')
    if name == 'y' or name == 'Y':
        continue
    else:
        exit()
