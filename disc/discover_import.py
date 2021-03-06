#!/usr/bin/env python
# -*- coding: utf-8 -*-

#@Author: Carl Dubois
#@Email: c.dubois@f5.com
#@Description: BIGIQ / BIGIP Trust and Discover LTM
#@Product: BIGIQ
#@VersionIntroduced: 5.x

"""
Copyright 2017 by F5 Networks Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import base64
import string
import os.path
import argparse
import requests
import time

## Disable request package warnings.
requests.packages.urllib3.disable_warnings()

try:
    import json
except ImportError:
    import simplejson as json

def device_trust(config):
    print "\n"
    print '####Begin a trust task between BIGIQ {0} and BIGIP {1}####'.format(config['bigiq'], config['bigip'])

    ## Request DATA
    data = {"address":config['bigip'],"userName":config['ip_user'],"password":config['ip_pass'],"clusterName":'',"useBigiqSync":'false',"deployWhenDscChangesPending":'false'}
    uri = 'https://' + config['bigiq'] + '/mgmt/cm/global/tasks/device-trust'

    ## Request POST
    response = requests.post(uri, data=str(data), auth=(config['iq_user'], config['iq_pass']), verify=False)
    ## DEBUG ##
    #print json.dumps(response.json(), default=lambda o: o.__dict__, sort_keys=True, indent=4)
    ###########
    t=1
    if response.status_code in [200, 202]:
        uri_trust = response.json()['selfLink'].replace('localhost', config['bigiq'])

        while True:
            response = requests.get(uri_trust, auth=(config['iq_user'], config['iq_pass']), verify=False)
            if response.json()['status'] == 'FINISHED':
                print "Trust task status is FINSIHED."
                return response.json()['machineId']
            elif response.json()['status'] == 'FAILED':
                print "Trust task status FAILED."
                print "ERROR: {0}".format(response.json()['errorMessage'])
                return False
            else:
                print str(t) + " sec - {0}".format(response.json()['currentStep'])
                time.sleep(1)
                t+=1
                continue
    else:
        print "INFO: {0}".format(response.json()['message'])
        return False

def enable_statistics(config, dev_id):
    print "\n"
    print '####Enable statistics for Device, DNS and LTM on BIGIQ {0} to collect from BIGIP {1}####'.format(config['bigiq'], config['bigip'])

    ## Request DATA
    link = "https://localhost/mgmt/cm/system/machineid-resolver/" + str(dev_id)
    data = {"targetDeviceReference":{"link":str(link)},"enabled":'true',"modules":[{"module":"DEVICE"},{"module":"DNS"},{"module":"LTM"}]}
    uri = 'https://' + config['bigiq'] + '/mgmt/cm/shared/stats-mgmt/agent-install-and-config-task'
    
    ## Request POST
    response = requests.post(uri, data=str(data), auth=(config['iq_user'], config['iq_pass']), verify=False)
    ## DEBUG ##
    # print json.dumps(response.json(), default=lambda o: o.__dict__, sort_keys=True, indent=4)
    ###########

    t=1
    if response.status_code in [200, 202]:
        uri_stats = response.json()['selfLink'].replace('localhost', config['bigiq'])
        while True:
            response = requests.get(uri_stats, auth=(config['iq_user'], config['iq_pass']), verify=False)
            if response.json()['status'] == 'FINISHED':
                print "Enabling statistic task complete. Status is FINSIHED.\n"
                return response.json()['machineId']
            elif response.json()['status'] == 'FAILED':
                print "Enable statistics FAILED."
                print "ERROR: {0}".format(response.json()['errorMessage'])
                return False
            else:
                print str(t) + " sec - {0}".format(response.json()['currentStep'])
                time.sleep(1)
                t+=1
                continue
    else:
        print "INFO: {0}".format(response.json()['message'])
        sys.exit(1)
        
def device_discover(config, dev_id, adc=None, afm=None, asm=None):
    print "\n"
    print '####Discover modules selected LTM, AFM, ASM via resource BIGIP {0}####'.format(config['bigip'])

    ## URI
    uri = 'https://' + config['bigiq'] + '/mgmt/cm/global/tasks/device-discovery'
    
    ## Reference link to BIGIP
    link = 'cm/system/machineid-resolver/' + str(dev_id)

    ## Request DATA
    adc_data = {'deviceReference': {"link": str(link)}, 'moduleList': [{'module': 'adc_core'}], 'userName': config['ip_user'], 'password': config['ip_user'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}
    adc_afm_data = {'deviceReference': {"link": str(link)}, 'moduleList': [{'module': 'adc_core'}, {'module': 'firewall'},{'module': 'security_shared'}], 'userName': config['ip_user'], 'password': config['ip_pass'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}
    adc_asm_data = {'deviceReference': {"link": str(link)}, 'moduleList': [{'module': 'adc_core'}, {'module': 'asm'},{'module': 'security_shared'}], 'userName': config['ip_user'], 'password': config['ip_pass'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}
    all_data = {'deviceReference': {"link": str(link)}, 'moduleList': [{'module': 'adc_core'}, {'module': 'firewall'}, {'module': 'asm'},{'module': 'security_shared'}], 'userName': config['ip_user'], 'password': config['ip_pass'], 'rootUser': config['root_username'], 'rootPassword' : config['root_password'], 'automaticallyUpdateFramework' : 'true'}

    ## Request POST
    if config['module'] == 'adc':
        response = requests.post(uri, data=str(adc_data), auth=(config['iq_user'], config['iq_pass']), verify=False)
    elif config['module'] == 'afm':
        response = requests.post(uri, data=str(adc_afm_data), auth=(config['iq_user'], config['iq_pass']), verify=False)
    elif config['module'] == 'asm':
        response = requests.post(uri, data=str(adc_asm_data), auth=(config['iq_user'], config['iq_pass']), verify=False)
    elif config['module'] == 'all':
        response = requests.post(uri, data=str(all_data), auth=(config['iq_user'], config['iq_pass']), verify=False)
    else:
        print "INFO: {0}".format(response.json()['message'])
        sys.exit(1)

    ## DEBUG ##
    print json.dumps(response.json(), default=lambda o: o.__dict__, sort_keys=True, indent=4)
    ###########

    ## Get status of task
    t=1
    if response.status_code in [200, 202]:
        uri_disc = response.json()['selfLink'].replace('localhost', config['bigiq'])
        while True:
            response = requests.get(uri_disc, auth=(config['iq_user'], config['iq_pass']), verify=False)
            if response.json()['status'] == 'FINISHED':
                print "Start discovery task complete. Status is FINSIHED.\n"
                return True
            elif response.json()['status'] == 'FAILED':
                print "Discovery FAILED."
                return False
            else:
                print str(t) + " sec - {0}".format(response.json()['status'])
                time.sleep(1)
                t+=1
                continue                    
    else:
        print "INFO: {0}".format(response.json()['message'])
        sys.exit(1)

def device_import(config, dev_id):
    print "\n"
    print '####Import module configuration selected LTM, AFM, ASM via resource BIGIP####'
    uris = []

    ## Reference link to BIGIP
    link = 'https://localhost/mgmt/cm/system/machineid-resolver/' + str(dev_id)
    data = {"createChildTasks":'false',"skipDiscovery":'true','deviceReference': {'link': str(link)}, "useBigiqSync":'false'}

    if config['module'] == 'afm':
        print "ADC and AFM import"
        uri_adc = '/mgmt/cm/adc-core/tasks/declare-mgmt-authority'
        uris.append(uri_adc)
        uri_afm = '/mgmt/cm/firewall/tasks/declare-mgmt-authority'
        uris.append(uri_afm)
    elif config['module'] == 'asm':
        print "ADC and ASM import"
        uri_adc = '/mgmt/cm/adc-core/tasks/declare-mgmt-authority'
        uris.append(uri_adc)
        uri_asm = '/mgmt/cm/asm/tasks/declare-mgmt-authority'
        uris.append(uri_asm)
    else:
        print "ADC, AFM and ASM import"
        uri_adc = '/mgmt/cm/adc-core/tasks/declare-mgmt-authority'
        uris.append(uri_adc)
        uri_afm = '/mgmt/cm/firewall/tasks/declare-mgmt-authority'
        uris.append(uri_afm)
        uri_asm = '/mgmt/cm/asm/tasks/declare-mgmt-authority'
        uris.append(uri_asm)

    ## POST
    for uri in uris:
        uri_path = 'https://' + config['bigiq'] + uri
        ## GET
        response = requests.get(uri_path, auth=(config['iq_user'], config['iq_pass']), verify=False)
        for item in response.json()['items']:
            if item['selfLink']:
                uri_import = item['selfLink'].replace('localhost', config['bigiq'])
                ## DELETE
                response = requests.delete(uri_import, auth=(config['iq_user'], config['iq_pass']), verify=False)
                if response.status_code in [200, 202]:
                    print "Deleted pre-existing import task."
                else:
                    print "No Task to delete."

        ## POST a new import task.
        response = requests.post(uri_path, data=str(data), auth=(config['iq_user'], config['iq_pass']), verify=False)

        ## DEBUG ##
        #print json.dumps(response.json(), default=lambda o: o.__dict__, sort_keys=True, indent=4)
        ###########
        t=1
        if response.status_code in [200, 202]:
            uri = response.json()['selfLink'].replace('localhost', config['bigiq'])
            while True:
                response = requests.get(uri, auth=(config['iq_user'], config['iq_pass']), verify=False)
                ## Poll for status of import task completion.

                if response.json()['status'] == 'FINISHED':
                    print "\nImport adc and {0} configuration for BIGIP {1} complete. Status is FINSIHED.\n".format(config['module'], config['bigip'])
                    break
                else:
                    print str(t) + " sec - {0}".format(response.json()['currentStep'])
                    time.sleep(2)
                    t+=1
                    continue             
    return True

if __name__ == '__main__':
    config = {}
    parser = argparse.ArgumentParser(description='Discover, Enable Statistics, Import configuration.')
    parser.add_argument('--config', type=str, help='Configuration, IQ-IP address, user, pass.')

    args = parser.parse_args()
    
    #==========================
    # Read config file
    #==========================    
    file = args.config
    
    infile = open (file, 'r')

    for line in infile:
        (key, val) = line.split(' = ')
        config[str(key)] = val.strip('\n')

    #==========================
    # device_trust
    #==========================
    dev_id = device_trust(config)
    if dev_id == False:
        sys.exit(1)

    time.sleep(3)
    #==========================
    # enable_statistics
    #==========================
    dev_id = enable_statistics(config, dev_id)
    if dev_id == False:
        sys.exit(1)

    time.sleep(3)
    #==========================
    # device_discovery
    #==========================
    result = device_discover(config, dev_id)
    time.sleep(3)

    #==========================
    # ltm_import
    #==========================
    result = device_import(config, dev_id)
    
    if dev_id == True or result == True:
        print "Trust, Discovery and Import successfully established."
    else:
        print "Trust and Discovery and Import failed."
