#
#
# different system actions with bind
# files generating, zone modifications, etc
#
#

from main.models import View, Zone, Record, ServerConfig
from dns.config import config
import re
import time
import subprocess
import os

class GenerateZone:

    def __init__(self, zone_id):
        self.zone_id = zone_id
        self.message = []

    def updateSerial(self):

        today_date = time.strftime("%Y%m%d", time.localtime())

        # get current serial
        self.zn = Zone.objects.get(pk=self.zone_id)

        m = re.match(r'^(\d{8})(\d{2})$', str(self.zn.serial))
        if int(self.zn.serial) < int(today_date + '00'):
            new_serial = today_date + '00'
        elif not m:
            raise Exception('You have a strange serial right now')
        else:
            old_date = m.group(1)
            old_counter = m.group(2)

            # same day
            if int(old_counter) == 99:
                new_serial = str(int(old_date) + 1) + '00'
            else:
                new_counter = "%02d" % (int(old_counter) + 1)
                new_serial = str(old_date) + str(new_counter)
                    
        # update serial
        self.zn.serial = new_serial
        self.zn.save()

        self.message.append('[OK] Serial updated')

        return

    def printZone(self):

        filename = "%s_%s" % (self.zn.view, self.zn.zone)

        tmpfile = config['dns']['path']['tmp'] + filename
        workfile = config['dns']['path']['master_zones'] + filename
        backupfile = config['dns']['path']['master_backup'] + filename + str(self.zn.serial)

        try:
            f = open(tmpfile, 'w')
        except:
            raise Exception('Failed to open tmp file')

        # select SOA and write to tmp file
        f.write("{zone} {ttl} IN SOA {origin} {mail_addr} {serial} {refresh} {retry} {expire} {minimum}\n".format(zone=self.zn.zone, \
        ttl=self.zn.ttl, origin=self.zn.origin, mail_addr=self.zn.mail_addr, serial=self.zn.serial,\
        refresh=self.zn.refresh, retry=self.zn.retry, expire=self.zn.expire, minimum=self.zn.minimum))

        # select records and write to tmp file
        p_priority = ''
        p_host = self.zn.zone
        for record in self.zn.record_set.all():
            if record.priority == 0:
                p_priority = ''
            else:
                p_priority = record.priority
            
            if record.host == '@':
                p_host = self.zn.zone
            else:
                p_host = record.host + "." + self.zn.zone
        
            f.write("{host} {ttl} {record_type} {priority} {answer}\n".format(host=p_host,\
            ttl=record.ttl, record_type=record.get_record_type_display(), priority=p_priority, answer=record.answer))

        f.close()

        self.message.append('[OK] Records file created')

        # check zone
        p = subprocess.Popen([config['dns']['exec']['checkzone'], self.zn.zone, tmpfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    
        err = ''
        for line in p.stdout.readlines():
            err += str(line.strip().decode("utf-8"))
    
        if err and 'not loaded due to errors' in err:
            raise Exception("Zone check failed. %s" % err)

        self.message.append('[OK] Records file checked')

        # backup existing file
        if os.path.isfile(workfile):
            p = subprocess.call([config['dns']['exec']['cp'], workfile, backupfile], stderr=subprocess.PIPE)
        
            if p:
                raise Exception('Failed to create backupfile')

            self.message.append('[OK] Backup file created')
        
        # compile zone to prod
        p = subprocess.Popen([config['dns']['exec']['compilezone'], '-s', 'relative', '-o', workfile, self.zn.zone, tmpfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        err = ''
        for line in p.stderr.readlines():
            err += str(line.strip().decode("utf-8"))
        
        if err:
            raise Exception("Zone compilation failed. %s" % err)

        self.message.append('[OK] New zone compiled')
    
        # rndc reload zone_name
        p = subprocess.Popen([config['dns']['exec']['rndc'], 'reload', self.zn.zone, 'in', str(self.zn.view)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        err = ''
        for line in p.stderr.readlines():
            err += str(line.strip().decode("utf-8"))
        
        if err:
            raise Exception("rndc reload failed. %s" % err)
    
        self.message.append("[OK] rndc reload")

        return self.message

class SaveConfig:

    def __init__(self, config_id):

        self.config_id = config_id
        self.message = {}
        self.message['success'] = []
        self.message['warning'] = []

    def applyConfig(self):

        # get config
        try:
            self.server_config = ServerConfig.objects.get(pk=self.config_id)
        except:
            raise Exception('Failed to get config')

        # files
        current_ts = str(time.time())
        self.tmpfile = config['dns']['path']['tmp'] + self.server_config.name + current_ts
        self.workfile = config['dns']['path']['master_include'] + self.server_config.name
        self.backupfile = config['dns']['path']['master_backup'] + self.server_config.name + current_ts

        # add generation date to config
        now_date = time.strftime("%d%m%Y-%H:%M:%S", time.localtime())

        self.print_config = """
        #
        # Generated on %s
        #

        """ % now_date + self.server_config.config

        # print to TMP
        try:
            f = open(self.tmpfile, 'w')
        except:
            raise Exception('Failed to open tmp file')

        f.write(self.print_config)

        f.close()

        self.message['success'].append('[OK] Config file saved to tmp')

        # if local - check, backup and copy to prod, rndc
        if self.server_config.get_type_display() == 'local':
            self.deployLocal()
    
        # if remote - scp, check, backup, copy to prod, rndc
        else:
            self.deployRemote()
        return self.message

    def deployLocal(self):

        # check config
        err = ''
        p = subprocess.Popen([config['dns']['exec']['checkconf'], self.tmpfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    
        for line in p.stdout.readlines():
            err += str(line.strip().decode("utf-8"))
    
        if err:
            raise Exception('Local config check failed: %s' % err)

        self.message['success'].append('[OK] local config checked')

        # backup 
        if os.path.isfile(self.workfile):
            p = subprocess.call([config['dns']['exec']['cp'], self.workfile, self.backupfile], stderr=subprocess.PIPE)
        
            if p:
                raise Exception('Failed to create backupfile')

            self.message['success'].append('[OK] Backup local config created')
        
        # move to prod
        p = subprocess.call([config['dns']['exec']['mv'], self.tmpfile, self.workfile], stderr=subprocess.PIPE)

        if p:
            raise Exception('Failed to move local config to prod')

        self.message['success'].append('[OK] Moved local config to prod')

        # rndc
        p = subprocess.Popen([config['dns']['exec']['rndc'], 'reload'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        err = ''
        for line in p.stderr.readlines():
            err += str(line.strip().decode("utf-8"))
        
        if err:
            raise Exception("rndc reload failed. %s" % err)
        
        self.message['success'].append('[OK] rndc reload')

        return

    def deployRemote(self):
        # check config
        err = ''
        p = subprocess.Popen([config['dns']['exec']['checkconf'], self.tmpfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    
        for line in p.stdout.readlines():
            err += str(line.strip().decode("utf-8"))
    
        if err:
            raise Exception('Local config check failed: %s' % err)

        self.message['success'].append('[OK] local config checked')

        # create backup on servers and upload to servers
        for server in self.server_config.group.servers.all():
            self.remoteBackup(server)
            self.remoteCopyToProd(server)
            self.remoteRndc(server)


    def remoteBackup(self, server):

        err = ''

        p = subprocess.Popen(["""{ssh} -i {ssh_key} \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o ConnectTimeout=1s \
            {user}@{server} \
            "{cp} {workfile} {backupfile}"
            """.format(
                ssh=config['dns']['exec']['ssh'], 
                ssh_key=config['dns']['files']['ssh_private_key'],
                user=config['dns']['system']['ssh_user'],
                server=server,
                cp=config['dns']['exec']['cp'],
                workfile=self.workfile,
                backupfile=self.backupfile)],
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in p.stderr.readlines():
            if re.search(r'permanently added .+ to the list of known hosts', str(line.strip().decode("utf-8")), re.IGNORECASE):
                continue
            err += str(line.strip().decode("utf-8"))

        if err:
            self.message['warning'].append('Server: %s - failed to create backup: %s' % (server, err))
        else:
            self.message['success'].append('[OK] Server: %s - created backup' % server)
        return

    def remoteCopyToProd(self, server):

        err = ''
        p = subprocess.Popen(["""{scp} -i {ssh_key} \
            -o UserKnownHostsFile=/dev/null \
            -o StrictHostKeyChecking=no \
            -o ConnectTimeout=1s \
            {tmpfile} \
            {user}@{server}:{workfile}
            """.format(
                scp=config['dns']['exec']['scp'],
                ssh_key=config['dns']['files']['ssh_private_key'],
                tmpfile=self.tmpfile,
                user=config['dns']['system']['ssh_user'],
                server=server,
                workfile=self.workfile)],
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        for line in p.stderr.readlines():
            if re.search(r'permanently added .+ to the list of known hosts', str(line.strip().decode("utf-8")), re.IGNORECASE):
                continue
            err += str(line.strip().decode("utf-8"))

        if err:
            self.message['warning'].append('Server: %s - failed to copy to prod: %s' % (server, err))
        else:
            self.message['success'].append('[OK] Server: %s - copied to prod' % server)
        return


    def remoteRndc(self, server):

        err = ''

        p = subprocess.Popen(["""{rndc} -k {remote_key} -s {server} -p {port} reload""".format(
                rndc=config['dns']['exec']['rndc'], 
                remote_key=config['dns']['files']['rndc_remote_key'], 
                server=server,
                port=config['dns']['system']['rndc_remote_port'])],
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in p.stderr.readlines():
            err += str(line.strip().decode("utf-8"))

        if err:
            self.message['warning'].append('Server: %s - rndc failed: %s' % (server, err))
        else:
            self.message['success'].append('[OK] Server: %s - rndc reloaded' % server)
        return

class CloneZone:

    def __init__(self, zone_id, view_id):

        # zone_id of zone, that is going to be cloned
        self.zone_id = zone_id
        # view_id of view, to which zone is going to be cloned
        self.view_id = view_id

        self.message = []

    def cloneZone(self):

        # get zone info
        zn = Zone.objects.get(pk=self.zone_id)

        # create new zone
        zn.pk = None
        zn.save()

        self.message.append('[OK] Zone cloned')

        # change view
        vw = View.objects.get(pk=self.view_id)
        zn.view = vw
        zn.save()

        self.message.append('[OK] Changed view')

        # get old zone again
        zn_old = Zone.objects.get(pk=self.zone_id)
        
        # clone records to new zone
        for record in zn_old.record_set.all():
            record.pk = None
            record.save()
            zn.record_set.add(record)

        self.message.append('[OK] Records cloned')

        return
