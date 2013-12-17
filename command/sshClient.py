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
import crypt
import subprocess


import ansible.runner

class userInfo:
    def __init__(self, Ip, userName, password, publicKey, privateKey, rootpwd):
        self.IpAdd = Ip
        self.UserName = userName
        self.pwd = password
        self.pubKey = publicKey
        self.privKey = privateKey
        self.pwdRoot = rootpwd

class sshInit:
    @staticmethod
    def createSshKey(name, path, isKnownHost):
        try:
            if not os.path.exists("../generate_key/%s" % name):
                prv = DSSKey.generate()
                prv.write_private_key_file(name)
                pub = DSSKey(filename="%s" % name)
                with open("%s.pub" % name, 'w') as f:
                    f.write("%s %s" % (pub.get_name(), pub.get_base64()))
                    f.close()
                shutil.move('%s.pub' % name , path)
                shutil.move('%s' % name , path)
                """if isKnownHost == True:
                    print "TRUE"
                    hk = HostKeys()
                    hk.add(name,"ssh-dss", pub)
                    home = os.path.expanduser("~/")
                    hk.save("%s.ssh/known_hosts" % home)"""
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
            sftp.put("../generate_key/%s" % Ip, ".ssh/%s" % Ip)
        except paramiko.SFTPError as e:
            print e
            return
        try:
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
        sshInit.createSshKey(Ip, "../generate_key", True)
        sshInit.sendKeyssh(Ip, ssh, serverkey)
            
    @staticmethod         
    def checkNewClient(Ip, userName ,passw, serverkey):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(Ip, username=userName, password=passw, look_for_keys=False, allow_agent=False)
            sshInit.newClientKeyInit(Ip, ssh, serverkey)
            ssh.close()
            #ssh = paramiko.SSHClient()
            #ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #ssh.load_system_host_keys()
            #ssh.connect(Ip, username=userName, look_for_keys=True, allow_agent=True)
            
            #stdin, stdout, stderr = ssh.exec_command('uname')
            #print "OS %s" % stdout.read()
            #ssh.close()
        except(paramiko.AuthenticationException, paramiko.SSHException, 
               paramiko.BadHostKeyException, socket.error, paramiko.SFTPError) as eMsg:
            print "error connection"
            sys.exit(1)

        
    @staticmethod         
    def newClientInitInfo(Ip, rootPass):
        characters = string.ascii_letters + string.digits
        password =  "".join(choice(characters) for x in range(randint(5, 8)))
        ssh = paramiko.SSHClient()
        defPass = password
        password ="toto"
        encPass = crypt.crypt(defPass,"22")
        home = os.path.expanduser("~/")
        stringArg = "name=testUser  password={0} shell=/bin/bash update_password=always".format(encPass)    
        print "stringArg %s" % stringArg
        results = ansible.runner.Runner(
            pattern=Ip, forks=10,
            module_name='user', module_args=stringArg ,timeout=10, remote_user='root').run()
        if results is None:
            print "No hosts found"
            sys.exit(1)
            
        for (hostname, result) in results['contacted'].items():
            if not 'failed' in result:
                print "testUser has been created pass = %s" % defPass #%s >>> %s" % (hostname, result['stdout'])
            else:
                print "%s >>> %s" % (hostname, result['msg'])

                for (hostname, result) in results['dark'].items():
                    print "%s >>> %s" % (hostname, result)
                return None
        return  userInfo(Ip, "testUser", password, " ", " ", rootPass)
