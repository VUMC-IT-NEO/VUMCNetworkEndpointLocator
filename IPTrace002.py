import paramiko
from getpass import getpass
# Create paramiko session
def ssh_login(login_ip, ssh_command):
    ssh_client = paramiko.SSHClient()
# Must set missing host key policy since we don't have the SSH key
# stored in the 'known_hosts' file
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Make the connection to our host
    ssh_client.connect(hostname=login_ip,
                   username=username,
                   password=password)

# If there is an issue, paramiko will throw an exception,
# so the SSH request must have succeeded.

    print('--- Success! connecting to: ', login_ip)
    print('---               Username: ')
    print('-----------------------------------------------------------\n')
    stdin, stdout, stderr = ssh_client.exec_command(ssh_command)

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
