"""
To Do:
1. Create new code that logs into the cores and checks the static routes to find
    the real gateway
2. Find and implement a library that enables sending API calls to get info from Prime
3. Rework code to define functions in separate blocks
4. Create for loop logic in method so that we can trace the IP no matter how many
    switches we have to go through
5. Create conditional code that deals with what to do when info for a particular
    IP, mac, or interface cannot be found
6. Create a block of code that Pings the device before tracing to make sure the
    ARP table is current
7. Use Django to create a web interface for the app
8. Figure out Authentication

"""


import paramiko
from getpass import getpass
import re
import sys
# get input from user
ip_trace = input('What is the IP you want to trace? ')
username = input('Username: ')
password = getpass('Password: ')
#split the ip address into a list of each octet
gateway_ip_list = ip_trace.split('.')
# assign the first three octets to a separate variable
first_octet = gateway_ip_list[0]
second_octet = gateway_ip_list[1]
third_octet = gateway_ip_list[2]
gateway_ip = first_octet + '.' + second_octet + '.' + third_octet + '.1'

print(f'Logging into gateway IP: ' + gateway_ip)
print('\n------------------------------------------------------------')
print('--- Attempting ssh connection to: ', gateway_ip)
# Create paramiko session
ssh_client = paramiko.SSHClient()
# Must set missing host key policy since we don't have the SSH key
# stored in the 'known_hosts' file
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# Make the connection to our host
ssh_client.connect(hostname=gateway_ip,
                   username=username,
                   password=password)
# send show ip arp command to switch
stdin, stdout, stderr = ssh_client.exec_command(f'show ip arp ' + ip_trace)
# parse the output for a mac address
arp_bytes = stdout.read()
arp_output = arp_bytes.decode(encoding='utf-8')
mac_pattern = re.compile('[0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4}')
mac_match = mac_pattern.search(arp_output)
mac_address = mac_match.group(0)
print(f"The mac_address associated with {ip_trace} is: " + mac_address)
# establish SSH connection
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname=gateway_ip,
                   username=username,
                   password=password)
stdin, stdout, stderr = ssh_client.exec_command(f'show mac address-table addres ' + mac_address)
# parse output to get the interface associated with the mac_address
mac_bytes = stdout.read()
mac_output  = mac_bytes.decode(encoding='utf-8')
int_pattern = re.compile('[a-zA-Z]{1,2}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2}?')
int_match = int_pattern.search(mac_output)
interface = int_match.group(0)
print(f"The associated interface with {mac_address} is: " + interface)
# establish SSH connection
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname=gateway_ip,
                   username=username,
                   password=password)
stdin, stdout, stderr = ssh_client.exec_command(f'show cdp neighbors ' + interface + ' detail')
# Parse CDP output to get the ip address of the switch connected to the interface
cdp_bytes = stdout.read()
cdp_output = cdp_bytes.decode(encoding='utf-8')
ip_pattern = re.compile('IP address: ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
ip_match = ip_pattern.search(cdp_output)
cdp_ip = ip_match.group(1)
print(f"The switch IP address associated with {interface} is: " + cdp_ip)

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname=cdp_ip,
                   username=username,
                   password=password)
stdin, stdout, stderr = ssh_client.exec_command(f'show mac address-table addres ' + mac_address)
# Parse output to get the interface associated with the mac_address
mac_bytes = stdout.read()
mac_output  = mac_bytes.decode(encoding='utf-8')
int_pattern = re.compile('[a-zA-Z]{1,2}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2}?')
int_match = int_pattern.search(mac_output)
interface = int_match.group(0)
print(f"The associated interface with {mac_address} is: " + interface)
# establish SSH connection
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname=cdp_ip,
                   username=username,
                   password=password)
stdin, stdout, stderr = ssh_client.exec_command(f'show snmp location')
# Parse output and print SNMP Location of switch
snmp_list = stdout.readlines()
snmp_loc = snmp_list[9]
print(f"Location: {snmp_loc}")
