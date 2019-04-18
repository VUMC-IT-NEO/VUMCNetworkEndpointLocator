##############################################################################
# VUMC Network Endpoint Locator
# -----------------------------
#
# Notes:
# Cisco Prime integration using the GET Devices API
# documentation found at https://10.109.24.16/webacs/api/v4/data/Devices?_docs
###
#To Do
# IP validation
# determine switch platform/version for proper commands
##############################################################################

import paramiko
from getpass import getpass
import re
import sys
# testing out github. here's my change
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
mac_pattern = re.compile('([0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4})')
int_pattern = re.compile('([a-zA-Z]{1,2}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2})')
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

def find_gateway(ip_trace, root_ip):

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

# =========================== Main =================================

print ('######################################################')
print ('##### Welcome to the VUMC NEO - IP Trace Program #####')
print ('#####                                            #####')
print ('##### This program will find information about   #####')
print ('##### where the device associated with an IP     #####')
print ('##### is, or was last connected to the network.  ##### ')
print ('###################################################### \n')

# Gather user data
print ('Enter the following information for use with all searches:')
username = input('Username: ')
password = getpass('Password: ')

# Code to allow dynamic input of the network root_ip
#root_ip = input('Enter the IP of a root device in your network (ex. Core-rtr):')

#Code for static root_ip entries
root_ip = '10.224.0.251'
alt_root_ip = '10.224.0.252'

while True:
    # gather IP to trace
    ip_trace = input('What is the IP you want to trace? ')

    # trace to the subnet gateway and router
    gateway_ip = find_gateway(ip_trace, root_ip)

    # if the gateway is not found, Notify user and retry or exit.
    if not gateway_ip:
        print (f'Gateway IP Not Found. \n')
        retry = input('Would you like to trace another IP? <Y or N>:')
        if retry == 'y' or retry == 'Y':
            continue
        else:
            exit()

    # Print updates about gateway IP
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

    # code to loop the program until a user wants to exit.
    name = input('Would you like to trace another IP? <Y or N>:')
    if name == 'y' or name == 'Y':
        continue
    else:
        exit()
