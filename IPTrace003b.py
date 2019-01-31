import paramiko
from getpass import getpass
import re
import sys

ip_trace = input('What is the IP you want to trace? ')
username = input('Username: ')
password = getpass('Password: ')
gateway_ip_list = ip_trace.split('.')
gateway_ip = (gateway_ip_list[0] + '.'
            + gateway_ip_list[1] + '.'
            + gateway_ip_list[2] + '.1')

print(f'Logging into gateway IP: ' + gateway_ip)
print('\n------------------------------------------------------------')
print('--- Attempting ssh connection to: ', gateway_ip)
# Create paramiko session
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname=gateway_ip,
                   username=username,
                   password=password)
stdin, stdout, stderr = ssh_client.exec_command(f'show ip arp ' + ip_trace)
# parse the output for a mac address
arp_bytes = stdout.read()
arp_output = arp_bytes.decode(encoding='utf-8')
mac_pattern = re.compile('[0-9a-fA-F]{4}.[0-9a-fA-F]{4}.[0-9a-fA-F]{4}')
mac_match = mac_pattern.search(arp_output)
if mac_match:
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
    if int_match:
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
        if ip_match:
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
            if int_match:
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
            else:
                print('Cannot find SNMP location' )
        else:
            print('Cannot find associated CDP Neighbor' )
    else:
        print('Cannot find associated interface' )
else:
    print('Cannot find associated mac address')
