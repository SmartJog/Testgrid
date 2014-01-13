import cStringIO
import sys
import os
import json
import paramiko
from paramiko import DSSKey
import socket
import shutil
from paramiko import Transport
import string
import random
import crypt
import subprocess
import ansible.runner
import testGridString 
from testGridString import *

class userInfo:
    def __init__(self, Ip, userName, password, publicKey, privateKey, rootpwd):
        self.IpAdd = Ip
        self.UserName = userName
        self.pwd = password
        self.pubKey = publicKey
        self.privKey = privateKey
        self.pwdRoot = rootpwd
        self.operatingSystem = ""


class sshKey:
    def __init__(self, priv, pub):
        self.privateKey = priv
        self.publicKey = pub

class sshConnection:
    @staticmethod
    def createSSHKeyFile(name, path):
        try:
            key = DSSKey.generate()
            key.write_private_key_file("{0}{1}".format(path, name))
            with open("{0}{1}.pub".format(path, name), 'w') as f:
                f.write( "{0} {1}".format(key.get_name(), key.get_base64()))
                f.close()
        except Exception as e:
            print "sshKeyTofile %s" % e

    @staticmethod
    def initSSHConfigFile(path, content):
        try:
            with open(path, 'w') as f:
                f.write(content)
                f.close()
        except Exception as e:
            print e
    
            
    @staticmethod
    def createSSHKeyPair():
        try:
            key = DSSKey.generate()
            privKey = cStringIO.StringIO()
            key.write_private_key(privKey)
            keyPair = sshKey(privKey.getvalue(), "{0} {1}".format(key.get_name(), key.get_base64()))
            privKey.close()
            return keyPair
        except Exception as eMsg:
            raise paramiko.SSHException("can't generate ssh key %s" % eMsg)

    @staticmethod
    def sendKeyssh(Ip, keyPair,serverkeyPath, ssh):
        try:
            sftp = ssh.open_sftp()
            sftp.mkdir(SSH_PATH_SFTP)
            sftp.close()
        except IOError:
            pass
            f = sftp.open("{0}{1}.pub".format(SSH_PATH_SFTP, Ip), 'wb')
            f.write(keyPair.publicKey)
            f.close()
            f = sftp.open("{0}{1}".format(SSH_PATH_SFTP, Ip), 'wb')
            f.write(keyPair.privateKey)
            f.close()
        except paramiko.SFTPError as e:
            print "sendkeyssh %s" % e
        sshConnection.setAuthorizedKey(serverkeyPath, ssh)

    @staticmethod
    def setAuthorizedKey(serverkeyPath, ssh):
        try:
            sftp = ssh.open_sftp()
            f = sftp.open("{0}{1}".format(SSH_PATH_SFTP, AUTHORIZED_KEYS), 'ab')
            fServer = open(serverkeyPath, "r")
            ks = fServer.read()
            f.write(ks)
            f.write("\n")
            f.close()
            fServer.close()
        except paramiko.SFTPError as e:
            print "setAuthorizedKey %s" % e
            
    @staticmethod         
    def newClientKeyInit(Ip, serverkeyPath, ssh):
        keyPair = sshConnection.createSSHKeyPair()
        sshConnection.sendKeyssh(Ip, keyPair, serverkeyPath, ssh)
        return keyPair
            
    @staticmethod         
    def checkNewClient(Ip, userName ,passw, serverkeyPath):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(Ip, username=userName, password=passw, look_for_keys=False, allow_agent=False)
            keyPair = sshConnection.newClientKeyInit(Ip, serverkeyPath, ssh)
            #stdin, stdout, stderr = ssh.exec_command('uname')
            #print "operating system: %s" % stdout.read()
            ssh.close()
            return keyPair
        except(paramiko.AuthenticationException, paramiko.SSHException, 
               paramiko.BadHostKeyException, socket.error) as eMsg:
            print "error connection"
            return None # raise

    @staticmethod        
    def generateNewPassword():
        characters = string.ascii_letters + string.digits
        password =  "".join(random.choice(characters) for x in range(random.randint(5, 8)))
        return password

    @staticmethod         
    def newClientInitInfo(Ip, rootPass, keyPair):

        ssh = paramiko.SSHClient()
        password = sshConnection.generateNewPassword()
        encPass = crypt.crypt(password,"22")
        stringArg = "name=testUser  password={0} shell=/bin/bash update_password=always".format(encPass)    
        inv = [Ip]
        results = ansible.runner.Runner(forks=10,module_name='user', 
                                        module_args=stringArg ,timeout=10, remote_user='root', pattern=Ip, host_list=inv).run()
        if results is None:
            print "No hosts found"
        if len(results['contacted']) == 0:
            print "can't connect to %s" % Ip
        for (hostname, result) in results['contacted'].items():
            if 'failed' in result:
                print "%s >>> %s" % (hostname, result['msg'])
                return None
        return  userInfo(Ip, NEW_USER, password, keyPair.publicKey , keyPair.privateKey, rootPass)
