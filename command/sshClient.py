import sys
import os
import json
import paramiko
from paramiko import DSSKey
from paramiko import HostKeys
import socket
from binascii import hexlify
import shutil
from paramiko import Transport
import string
from random import *

#import ansible.runner

class sshInit:
    @staticmethod
    def createSshKey(name, path):
        try:
            if not os.path.exists("../generate_key/%s" % name):
                prv = DSSKey.generate()
                prv.write_private_key_file(name)
                pub = DSSKey(filename="%s" % name)
                with open("%s.pub" % name, 'w') as f:
                    f.write("%s %s" % (pub.get_name(), pub.get_base64()))
                shutil.move('%s.pub' % name , path)
                shutil.move('%s' % name , path)
            else:
                return 
        except(paramiko.AuthenticationException, paramiko.SSHException, paramiko.BadHostKeyException, socket.error) as eMsg:
            print "paramiko error create ssh key"

    @staticmethod
    def sendKeyssh(Ip, ssh, serverkey):
        try:
            sftp = ssh.open_sftp()
            sftp.mkdir(".ssh/")
        except IOError:
            print '(assuming .ssh/ already exists)'
            sftp.put("../generate_key/%s.pub" % Ip, ".ssh/%s.pub" % Ip)
            print "sftp avan"
            sftp.put("../generate_key/%s" % Ip, ".ssh/%s" % Ip)
            print "sftp apres"
        except paramiko.SFTPError as e:
            print e
            return
        try:
            print "stat"
            sftp.stat(".ssh/authorized_keys")
            sftp.get(".ssh/authorized_keys", "../generate_key/authorized_keys")
            f = open("../generate_key/authorized_keys", "a+")
            fServer = open(serverkey, "r")
            ks = fServer.read()
            f.write("\n")
            f.write(ks)
            f.close()
            fServer.close()
            sftp.put("../generate_key/authorized_keys", ".ssh/authorized_keys")
            sftp.close()
        except IOError:
            print "creating ~/.ssh/authorized_keys"
            sftp.put(serverkey,".ssh/authorized_keys")
            sftp.close()

    @staticmethod         
    def newClientKeyInit(Ip,ssh, serverkey):
        """try:
            sshInit.createSshKey(Ip, "../generate_key")
            home = os.path.expanduser("~/")
            kh = open("%s.ssh/known_hosts" % home, "a+")
            print "open %s" % home
            key = open("../generate_key/%s.pub" % Ip, "r")
            keyval = key.read();
            kh.write(keyval)
            kh.close()
            key.close()
        except IOError:
            print "IOError"""
        sshInit.sendKeyssh(Ip, ssh, serverkey)
            
    @staticmethod         
    def checkNewClient(Ip, userName ,passw, serverkey):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #ssh.load_system_host_keys()
            print "bissss"
            ssh.connect(Ip, username=userName, password=passw, look_for_keys=False, allow_agent=False)
            #uname
            print "bissss"
            sshInit.newClientKeyInit(Ip, ssh, serverkey)
            ssh.close()
            print "bissss3"
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #ssh.load_system_host_keys()
            ssh.connect(Ip, username=userName, look_for_keys=True, allow_agent=True)
            
            stdin, stdout, stderr = ssh.exec_command('uname')
            print "OS %s" % stdout.read()
            hk = HostKeys()
            home = os.path.expanduser("~/")
            
            hk.save("%s.ssh/known_hosts" % home)
            ssh.close()

            print "wtf????"
        except(paramiko.AuthenticationException, paramiko.SSHException, 
               paramiko.BadHostKeyException, socket.error, paramiko.SFTPError) as eMsg:
            print eMsg

    @staticmethod         
    def newClientInitInfo(Ip):
        characters = string.ascii_letters + string.digits
        password =  "".join(choice(characters) for x in range(randint(5, 8)))
        print password
        print Ip
        stringArg = "name=test update_password=always password=test"#.format(password) 
        """results = ansible.runner.Runner(
        pattern=Ip, forks=10,
        module_name='user', module_args=stringArg ,timeout=10, remote_user='root').run()
        print "ici"
        if results is None:
            print "No hosts found"
            sys.exit(1)
            
        for (hostname, result) in results['contacted'].items():
            if not 'failed' in result:
                print "sucess ??????????????" #%s >>> %s" % (hostname, result['stdout'])

                for (hostname, result) in results['dark'].items():
                    print "%s >>> %s" % (hostname, result)"""

        """ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.load_system_host_keys()
        key = open("../generate_key/%s.pub" % Ip, "r")
        keyval = key.read();
        key.close """
        
        
