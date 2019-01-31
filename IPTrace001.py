import paramiko
from getpass import getpass
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

# If there is an issue, paramiko will throw an exception,
# so the SSH request must have succeeded.

print('--- Success! connecting to: ', gateway_ip)
print('---               Username: ')
print('---               Password: ')
print('-----------------------------------------------------------\n')

stdin, stdout, stderr = ssh_client.exec_command(f'show ip arp ' + ip_trace)

arp_list = stdout.readlines()
arp_entry = arp_list[14]
arp_split_space_list = arp_entry.split(' ')
mac_address = arp_split_space_list[16]
print(f'The associated mac address is: ' + mac_address)

ssh_client = paramiko.SSHClient()

# Must set missing host key policy since we don't have the SSH key
# stored in the 'known_hosts' file
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Make the connection to our host
ssh_client.connect(hostname=gateway_ip,
                   username=username,
                   password=password)

stdin2, stdout2, stderr2 = ssh_client.exec_command(f'show mac address-table address ' + mac_address)
mac_list = stdout.readlines()
mac_entry = mac_list[25]
print(mac_entry)

mac_interface_list = mac_entry.split(' ')
mac_interface = mac_interface_list[22]
print(mac_interface)

ssh_client = paramiko.SSHClient()

# Must set missing host key policy since we don't have the SSH key
# stored in the 'known_hosts' file
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Make the connection to our host
ssh_client.connect(hostname=gateway_ip,
                   username=username,
                   password=password)

stdin, stdout, stderr = ssh_client.exec_command(f'show cdp neighbors ' + mac_interface + 'detail')
neighbor_ip = stdout.readlines()
neighbor_ip_line_list = neighbor_ip.splitlines()
neighbor_ip_line = neighbor_ip_line_list[6]
print(neighbor_ip_line)
ssh_client.close()


file.close()
