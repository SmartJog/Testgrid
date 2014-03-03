import cStringIO
import sys
import os
import json
import paramiko
from paramiko import DSSKey
import socket
import shutil
from paramiko import Transport
import subprocess


SSH_PATH_SFTP = ".ssh/"
AUTHORIZED_KEYS = "authorized_keys"
NEW_USER = "testUser"


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
    def sendKeyssh(hostname, keyPair, keyPath, ssh):
        try:
            sftp = ssh.open_sftp()
            sftp.mkdir(SSH_PATH_SFTP)
            sftp.close()
        except IOError:
            pass
            f = sftp.open("{0}{1}.pub".format(SSH_PATH_SFTP, hostname), 'wb')
            f.write(keyPair.publicKey)
            f.close()
            f = sftp.open("{0}{1}".format(SSH_PATH_SFTP, hostname), 'wb')
            f.write(keyPair.privateKey)
            f.close()
        except paramiko.SFTPError as e:
            print "sendkeyssh %s" % e
        sshConnection.setAuthorizedKey(keyPath, ssh)

    @staticmethod
    def setAuthorizedKey(keyPath, ssh):
        try:
            sftp = ssh.open_sftp()
            f = sftp.open("{0}{1}".format(SSH_PATH_SFTP, AUTHORIZED_KEYS), 'ab')
            fServer = open(keyPath, "r")
            ks = fServer.read()
            f.write(ks)
            f.write("\n")
            f.close()
            fServer.close()
        except paramiko.SFTPError as e:
            print "setAuthorizedKey %s" % e
            
    @staticmethod         
    def newClientKeyInit(hostname, keyPath, ssh):
        keyPair = sshConnection.createSSHKeyPair()
        sshConnection.sendKeyssh(hostname, keyPair, keyPath, ssh)
        return keyPair
            
    @staticmethod         
    def checkNewClient(hostname, userName ,passw, serverkeyPath):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, username=userName, password=passw, look_for_keys=False, allow_agent=False)
            keyPair = sshConnection.newClientKeyInit(hostname, serverkeyPath, ssh)
            ssh.close()
            return keyPair
        except(paramiko.AuthenticationException, paramiko.SSHException, 
               paramiko.BadHostKeyException, socket.error):
            return None
            #raise Exception 

    


    
