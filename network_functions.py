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
from getpass import getpass
from pprint import pprint

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
mac_pattern = re.compile('([0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4})')
int_pattern = re.compile('([a-zA-Z]{1,2}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2})')
po_int_pattern = re.compile('([A-Z]{1}[a-z]{1}[0-9]{1,4})')
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
username = ''
password = ''

def get_creds():
    global username
    global password
    username = input('Username: ')
    password = getpass('Password: ')
    return

def vumc_ip_type(ip):
    global ip_type
    ip_type = 0
    octet_list = ip.split('.')
    if octet_list[0] == '10':
        if octet_list[1] == '248' or octet_list[1] == '249' or octet_list[1] == '250' or octet_list[1] == '251':
            print(f'{ip} is a VUMC Wireless IP')
            ip_type = 1
            return ip_type
        else:
            print(f'{ip} is a VUMC wired IP')
            ip_type = 2
            return ip_type
    elif octet_list[0] == '160' and octet_list[1] == '129':
        print(f'{ip} is a VUMC public IP address')
        ip_type = 3
        return ip_type
    elif octet_list[0] == '129' and octet_list[1] == '59':
        print(f'{ip} is a VU public IP address')
        ip_type = 4
        return ip_type
    else:
        print(f'{ip} is not a VUMC IP address')
        ip_type = 5
        return ip_type

def find_gateway(ip_trace, root_ip):
    hop_list = traceroute(ip_trace)
    if hop_list != 'unreachable':
        print(f'Contacting gateway device {hop_list[-2]}')
        return hop_list[-2]

    print ('Beginning ip route trace to locate gateway...')

    print ('Contacting device: ' + root_ip + ' to look for routes to ' + ip_trace + '...')
    next_hop = get_next_hop(ip_trace, root_ip)
    while True:
        print ('contacting the next-hop: ' + next_hop)
        hop_ip = next_hop
        next_hop = get_next_hop(ip_trace, next_hop)
        if next_hop == ip_only_pattern.search(next_hop):
            continue
        elif next_hop == 'connected':
            response = ssh_login(hop_ip, iproute_cmd, ip_trace)
            ssh_output = response.read()
            raw_output = ssh_output.decode(encoding='utf-8')
            connected = parse(raw_output, connected_pattern)
            route = parse(raw_output, next_hop_pattern)
            static = parse(raw_output, static_route_pattern)

            match = connected_pattern.search(raw_output)
            vlan_id = match.group(1)
            svi = "vlan" + vlan_id
            response = ssh_login(hop_ip, show_run_int_cmd, svi)
            svi_ip_config = parse(response, ip_config_pattern)
            gateway_ip = parse(svi_ip_config, ip_only_pattern)
            print (gateway_ip)
            return gateway_ip

        else:
            return

# function to get log in to a network device and get the next hop for a route.
def get_next_hop(ip_trace, hop_ip):
    #log in to current hop and return show ip route output
    print ('Looking for next hop to the Gateway IP for ' + ip_trace + ' .....')
    response = ssh_login(hop_ip, iproute_cmd, ip_trace)
    ssh_output = response.read()
    raw_output = ssh_output.decode(encoding='utf-8')
    connected = parse(raw_output, connected_pattern)
    route = parse(raw_output, next_hop_pattern)
    static = parse(raw_output, static_route_pattern)

    print ('\n ')
    print ('--------------------------')
    print ('Route Results Summary: ')
    print ('--------------------------\n')
    print ('Static: ' + static)
    print ('Route: ' + route)
    print ('Connected: ' + connected)
    print ('--------------------------\n')

    if static != "Not Found":
        print ('-----------------------------------------')
        print ("Found a static next-hop: " + route + '\n')
        print ('-----------------------------------------')
        #extract just the IP from the route
        match = ip_only_pattern.search(route)
        if match:
            next_hop_ip = match.group(0)
            # gather arp information to identify use for outgoing interface identification
            response = ssh_login(hop_ip, arp_command, next_hop_ip)
            arp_mac = parse(response, mac_pattern)
            print ("Next Hop ARP MAC is: " + arp_mac)
            response = ssh_login(hop_ip, mac_command, arp_mac)
            arp_int = parse(response, po_int_pattern)
            print ("Next Hop interface is: " + arp_int)
            response = ssh_login(hop_ip, show_run_int_cmd, arp_int)
            ssh_output = response.read()
            raw_output = ssh_output.decode(encoding='utf-8')
            print ('-----------------------------------------\n')
            print ('Next Hop Interface Config: ')
            print (raw_output)
            print ('\n \n')
            return 'static'
        else:
            print ('No Static \n')

    elif route != "Not Found":
        print ('-----------------------------------------')
        print ("Found a best ucast next-hop: " + route)
        print ('-----------------------------------------\n')
        #extract just the IP from the route
        match = ip_only_pattern.search(route)
        if match:
            next_hop_ip = match.group(0)
            print ("Next Hop IP is: " + next_hop_ip)
            print ("\n \n")
            return next_hop_ip
        else:
            print ('No Route \n \n')

    elif connected != 'Not Found':
        return 'connected'

    else:
        print ("Next-hop Error. Exiting. \n \n")
        return

def ssh_login(switch_ip, command, command_param):
    ssh_client.connect(hostname=switch_ip,
                       username=username,
                       password=password)
    stdin, stdout, stderr = ssh_client.exec_command(command + command_param)
    return stdout

def parse(response, pattern):
    try:
        ssh_output = response.read()
        raw_output = ssh_output.decode(encoding='utf-8')
    except:
        raw_output = response
    match = pattern.search(raw_output)
#    return matched_value
    if match:
        matched_value = match.group(0)
        return matched_value
    else:
        return 'Not Found'

def parse_cdp(response, pattern):
    ssh_output = response.read()
    raw_output = ssh_output.decode(encoding='utf-8')
    match = pattern.search(raw_output)
    global cdp_neighbors
    if match:
        phone_match = phone_pattern.search(raw_output)
        if phone_match:
            cdp_neighbors = cdp_neighbors + 1
        else:
            matched_value = match.group(1)
            return matched_value
    else:
        cdp_neighbors = cdp_neighbors + 1
        return

def getWirelessIpInfo(ipaddr):
    user = username
    pw = password
    print(user)
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
        return 'unreachable'
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
            ip_type = 1
            return ip_type
        else:
            print(f'{ip} is a VUMC wired IP')
            ip_type = 2
            return ip_type
    elif octet_list[0] == '160' and octet_list[1] == '129':
        print(f'{ip} is a VUMC public IP address')
        ip_type = 3
        return ip_type
    elif octet_list[0] == '129' and octet_list[1] == '59':
        print(f'{ip} is a VU public IP address')
        ip_type = 4
        return ip_type
    else:
        print(f'{ip} is not a VUMC IP address')
        ip_type = 5
        return ip_type

def mac_trace(gateway_ip, ip_trace):
    mac_command = 'show mac address-table address '
    arp_command = 'show ip arp '
    snmp_command = 'show snmp location'
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    mac_pattern = re.compile('([0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4})')
    int_pattern = re.compile('([a-zA-Z]{1,2}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2})')
    ip_pattern = re.compile('IP address: ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')

    print(f'The gateway is {gateway_ip}')
    print(f'Logging into the local router for ' + ip_trace + ': ' + gateway_ip)
    print('\n------------------------------------------------------------')

    stdout = ssh_login(gateway_ip, arp_command, ip_trace)
    mac_address = parse(stdout, mac_pattern)
    print(f"The mac address associated with {ip_trace} is: " + mac_address)

    stdout = ssh_login(gateway_ip, mac_command, mac_address)
    interface = parse(stdout, int_pattern)
    print(f"The associated interface with {mac_address} is: " + interface)

    cdp_ip = gateway_ip

    while cdp_neighbors == 0:
        cdp_command = (f'show cdp neighbors ')
        cdp_param = (f'{interface} detail')
        stdout = ssh_login(cdp_ip, cdp_command, cdp_param)
        cdp_ip = parse_cdp(stdout, ip_pattern)
        if cdp_neighbors == 0:
            print(f"The switch IP address associated with {interface} is: " + cdp_ip)
            stdout = ssh_login(cdp_ip, mac_command, mac_address)
            interface = parse_cdp(stdout, int_pattern)
            print(f"The associated interface with {mac_address} is: " + interface)
            last_switch_ip = cdp_ip
        else:
            print(f'The device is connected to switch {last_switch_ip} port {interface}')
    stdout = ssh_login(last_switch_ip, snmp_command, '')
    snmp_list = stdout.readlines()
    snmp_loc = snmp_list[9]

    # print out location result.
    print(f"Location: {snmp_loc}")
    return snmp_loc
