# this script will will generate an output file FTD-device-list.csv containing the appliance inventory managed by FMC
# FMC misreports the serial number of the appliances.  to obtain the serial associated with support contracts it will be queried
# directly from the cli of the appliance and extracted using regular expression. this technique currently only works on FTD
# appliances, not ASA running FTD code

#BASE_URL variable needs to be updated with the IP address of the FMC

import requests
from requests.auth import HTTPBasicAuth
import json
import csv
import os
import sys
from datetime import date
from paramiko.client import SSHClient, AutoAddPolicy, RejectPolicy
import re

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()

# Global Variables
BASE_URL = 'https://10.253.22.73'

# prompt user for FMC credentials
# login to FMC and return the value of auth tokens and domain UUID from the response headers
# exit with an error message if a valid response is not received
def login(user, passwd):
    
    response = requests.post(
       BASE_URL + '/api/fmc_platform/v1/auth/generatetoken',
       auth=HTTPBasicAuth(username=user, password=passwd),
       headers={'content-type': 'application/json'},
       verify=False,
    )
    if response:
        return {'X-auth-access-token': response.headers['X-auth-access-token'], 
        'X-auth-refresh-token':response.headers['X-auth-refresh-token'],
        'DOMAIN_UUID':response.headers['DOMAIN_UUID']}
    else:
        sys.exit('Unable to connect to ' + BASE_URL + ' using supplied credentials')


## return a dictionary object of the devicerecords API results
def get_devicerecords(token, DUUID):

    #query paramaters to control results limit and offset. 1000 is max limit
    limit = str(1000)
    offset = str(0)
    querystring = {'offset':offset,'limit':limit}
    
    #perform the query
    response = requests.get(
       BASE_URL + '/api/fmc_config/v1/domain/' + DUUID + '/devices/devicerecords?expanded=true',
       headers={'X-auth-access-token':token},
       params=querystring,
       verify=False,
    )
    
    data = response.json()
    return data


def main():

    devicerecords_outfile = 'FTD-device-list.csv'
    devices = []
    outfile_columns = ['name', 'hostName', 'model', 'serial', 'sw_version', 'deviceGroup', 'id']
    
    #there is an assumption that FMC and FTD login credentials are the same and only requested once
    print('\n\nEnter Firepower Credentials')
    user = input("USERNAME: ").strip()
    passwd = input("PASSWORD: ").strip()
    result = login(user, passwd)
    token = result.get('X-auth-access-token')
    DUUID = result.get('DOMAIN_UUID')
    
    #get standard device info available in FMC
    print('\nGathering data from FMC.....')
    devicerecords = get_devicerecords(token, DUUID)
    for item in devicerecords['items']:
        device = {'name':item['name'], 'hostName':item['hostName'], 'model':item['model'], 'sw_version':item['sw_version'], 'deviceGroup':item['deviceGroup']['name'], 'id':item['id']}
        devices.append(device)
    
    #FMC lies about device serial number.  the serial number associated with the support contract
    #can only be obtained from the FTD cli.  SSH to each appliance cli to grab the serial
    #for some reason ssh to FTD puts you in fxos mode rather than ftd mode so the show command is an fxos command
    #this direct SSH query only works on FTD appliances, not ASA devices running firepower
    #FTD appliances are very slow to intially connect with ssh, causing this code section to run slow
    print('Gathering serial numbers from appliances.....')
    for device in devices:
        print('Querying', device['name'], '...')
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy)
        ssh.connect(device['hostName'], 22, username=user, password=passwd)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("show chassis inventory")
        raw_output = ssh_stdout.read().decode()
        matches = re.search('([A-Z]{3}[A-Z,0-9]{8})', raw_output)
        if matches:
            serial = matches.group(0)
        else:
            serial = 'UNKNOWN'
        device['serial'] = serial
    
    #create output inventory file
    with open(devicerecords_outfile, "w", newline='') as file:
        writer = csv.DictWriter(file, fieldnames=outfile_columns)
        writer.writeheader()
        for device in devices:
            writer.writerow(device)
        
if __name__ == "__main__":
    main()
