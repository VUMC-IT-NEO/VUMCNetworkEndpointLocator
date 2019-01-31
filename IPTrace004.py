import paramiko
from getpass import getpass
import re
import sys

def find_gateway(ip_trace):
    #split the ip address into a list of each octet
    gateway_ip_list = ip_trace.split('.')
    # assign the first three octets to a separate variable
    first_octet = gateway_ip_list[0]
    second_octet = gateway_ip_list[1]
    third_octet = gateway_ip_list[2]
    gateway_ip = first_octet + '.' + second_octet + '.' + third_octet + '.1'
    switch_ip = find_gateway(ip_trace)

def ssh_login(switch_ip, command):
    # Create paramiko session
    ssh_client = paramiko.SSHClient()
    # Must set missing host key policy since we don't have the SSH key
    # stored in the 'known_hosts' file
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Make the connection to our host
    ssh_client.connect(hostname=switch_ip,
                       username=username,
                       password=password)
    # send show ip arp command to switch
    stdin, stdout, stderr = ssh_client.exec_command({command})
    return stdout

def find_mac():
    # parse the output for a mac address
    arp_bytes = stdout.read()
    arp_output = arp_bytes.decode(encoding='utf-8')
    mac_pattern = re.compile('[0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4}')
    mac_match = mac_pattern.search(arp_output)
    mac_address = mac_match.group(0)
    print(f"The mac_address associated with {ip_trace} is: " + mac_address)
    return mac_address

def find_interface():
    # Parse output for associated interface
    mac_bytes = stdout.read()
    mac_output  = mac_bytes.decode(encoding='utf-8')
    int_pattern = re.compile('[a-zA-Z]{1,2}[0-9]{1}/[0-9]{1,2}/?[0-9]{1,2}?')
    int_match = int_pattern.search(mac_output)
    interface = int_match.group(0)
    print(f"The associated interface with {mac_address} is: " + interface)
    return interface

def find_cpd_ip():
    # Parse CDP output to get the ip address of the switch connected to the interface
    cdp_bytes = stdout.read()
    cdp_output = cdp_bytes.decode(encoding='utf-8')
    ip_pattern = re.compile('IP address: ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})')
    ip_match = ip_pattern.search(cdp_output)
    cdp_ip = ip_match.group(1)
    print(f"The switch IP address associated with {interface} is: " + cdp_ip)
    return cdp_ip

def find_snmp_loc():
    # Parse output and print SNMP Location of switch
    snmp_list = stdout.readlines()
    snmp_loc = snmp_list[9]
    print(f"Location: {snmp_loc}")
    return snmp_loc

# METHOD ============================================================
ip_trace = input('What is the IP you want to trace? ')
username = input('Username: ')
password = getpass('Password: ')

print(f'Logging into gateway IP: ' + gateway_ip)
print('\n------------------------------------------------------------')
print('--- Attempting ssh connection to: ', gateway_ip)

arp_command = 'show ip arp {ip_trace}'
    ssh_login(switch_ip, arp_command)
find_mac()
mac_command = 'show mac address-table address {mac_address}'
ssh_login(switch_ip, mac_command)
find_interface()
int_command = 'show cdp neighbors {interface} detail'
ssh_login(switch_ip, int_command)
find_cpd_ip()
ssh_login(cdp_ip, mac_command)
find_interface()
snmp_command = 'show snmp location'
ssh_login(cdp_ip, snmp_command)
find_snmp_loc()
