# this script will will generate an output file FTD-device-list.csv containing the appliance inventory managed by FMC

#BASE_URL variable needs to be updated with the IP address of the FMC

import requests
from requests.auth import HTTPBasicAuth
import json
import csv
import os
import sys
from datetime import date

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()

# Global Variables
BASE_URL = 'https://x.x.x.x'

# prompt user for FMC credentials
# login to FMC and return the value of auth tokens and domain UUID from the response headers
# exit with an error message if a valid response is not received
def login():
    print('\n\nEnter FMC Credentials')
    user = input("USERNAME: ").strip()
    passwd = input("PASSWORD: ").strip()
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
       BASE_URL + '/api/fmc_config/v1/domain/' + DUUID + '/devices/devicerecords',
       headers={'X-auth-access-token':token},
       params=querystring,
       verify=False,
    )
    
    data = response.json()
    return data


def main():

    devicerecords_outfile = 'FTD-device-list.csv'
    outfile_columns = ['name', 'id', 'type', 'links']
    result = login()
    token = result.get('X-auth-access-token')
    DUUID = result.get('DOMAIN_UUID')
    devicerecords = get_devicerecords(token, DUUID)
    with open(devicerecords_outfile, "w") as file:
        writer = csv.DictWriter(file, fieldnames=outfile_columns)
        for item in devicerecords['items']:
            writer.writerow(item)
        
if __name__ == "__main__":
    main()
