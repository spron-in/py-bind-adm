#
#
# dns health check
# 
#

import os
import subprocess
import simplejson as json
import re

from dns.config import config

class CheckHealthActions:

    def __init__(self, check):

        self.check = check
        self.param_dict = json.loads(check['parameter'])
        return

    def run(self):

        func_name = 'check_' + self.param_dict['type']
        getattr(self, func_name)()
        return self.check

    def check_ssh(self):

        return

    def check_rndc(self):

        p = subprocess.Popen(["{timeout} 2s {rndc} -k {remote_key} -p {port} -s {server} status".format(
            timeout=config['dns']['exec']['timeout'],
            rndc=config['dns']['exec']['rndc'],
            remote_key=config['dns']['files']['rndc_remote_key'],
            port=config['dns']['system']['rndc_remote_port'],
            server=self.param_dict['server'])],
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        err = ''
        for line in p.stderr.readlines():
            err += str(line.strip().decode("utf-8"))

        if err:
            self.check['message'] = err
            self.check['result'] = 1

        return

    def check_directory(self):

        tmpfile = self.param_dict['dir'] + '/check_health_file.tmp'

        try:
            f = open(tmpfile, 'w')
        except:
            self.check['message'] = 'Failed to create file'
            self.check['result'] = 1
            return

        f.close()

        p = subprocess.call([config['dns']['exec']['rm'], tmpfile], stderr=subprocess.PIPE)

        if p:
            self.check['message'] = 'Failed to remove file'
            self.check['result'] = 1
            
        return

    def check_transfer(self):

        p = subprocess.Popen(['{dig} +noedns +time=2 AXFR {zone} @{server}'.format(
            dig=config['dns']['exec']['dig'],
            zone=self.param_dict['zone'],
            server=self.param_dict['server'])],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )

        for line in p.stdout.readlines():

            line = str(line.strip().decode("utf-8"))
            if re.search(r'connection refused', line, re.IGNORECASE):
                self.check['message'] = 'connection refused'
                self.check['result'] = 1
                break
            elif re.search(r'connection timed out', line, re.IGNORECASE):
                self.check['message'] = 'connection timed out'
                self.check['result'] = 1
                break
            elif re.search(r'Transfer failed', line, re.IGNORECASE):
                self.check['message'] = 'Transfer failed'
                self.check['result'] = 1
                break
        return 

