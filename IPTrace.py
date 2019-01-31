# Cisco Prime integration using the GET Devices API
# documentation found at https://10.109.24.16/webacs/api/v4/data/Devices?_docs
###
#To Do
# IP validation
# determine switch platform/version for proper commands
import paramiko
from getpass import getpass
import re
import sys

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
mac_pattern = re.compile('([0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4})')
int_pattern = re.compile('([a-zA-Z]{1,2}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2})')
ip_pattern = re.compile('IP address: ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
phone_pattern = re.compile('(IP Phone)')
arp_command = 'show ip arp '
mac_command = 'show mac address-table address '
snmp_command = 'show snmp location'
cdp_neighbors = 0

def find_gateway(ip_trace):
    gateway_ip_list = ip_trace.split('.')
    gateway_ip = (gateway_ip_list[0] + '.'
                + gateway_ip_list[1] + '.'
                + gateway_ip_list[2] + '.1')
    return gateway_ip

def ssh_login(switch_ip, command, command_param):
    ssh_client.connect(hostname=switch_ip,
                       username=username,
                       password=password)
    stdin, stdout, stderr = ssh_client.exec_command(f'{command}{command_param}')
    return stdout

def parse(response, pattern):
    ssh_output = response.read()
    raw_output = ssh_output.decode(encoding='utf-8')
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

# METHOD ============================================================
ip_trace = input('What is the IP you want to trace? ')
username = input('Username: ')
password = getpass('Password: ')
gateway_ip = find_gateway(ip_trace)
print(f'The gateway is {gateway_ip}')
print(f'Logging into gateway IP: ' + gateway_ip)
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
print(f"Location: {snmp_loc}")
