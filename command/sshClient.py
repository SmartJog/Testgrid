import sys
import os
import json
import paramiko
from paramiko import DSSKey
import socket
from binascii import hexlify
import shutil
from paramiko import Transport
class sshInit:
    @staticmethod
    def createSshKey(name, path):
        try:
            if not os.path.exists("../generate_key/%s" % name):
                prv = DSSKey.generate()
                prv.write_private_key_file(name, password=name)
                pub = DSSKey(filename="%s" % name, password=name)
                with open("%s.pub" % name, 'w') as f:
                    f.write("%s %s" % (pub.get_name(), pub.get_base64()))
                shutil.move('%s.pub' % name , path)
                shutil.move('%s' % name , path)
            else:
                return 
        except(paramiko.AuthenticationException, paramiko.SSHException, paramiko.BadHostKeyException, socket.error) as eMsg:
            print "paramiko error create ssh key"

    @staticmethod         
    def checkNewClient(Ip, userName, passw, serverkey):
        try:
            #t = Transport(Ip)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.load_system_host_keys()
            print "unlock private key??? wut"
            #t.auth_password(userName, passw)
            ssh.connect(Ip, username=userName, password=passw, look_for_keys=False, allow_agent=False)
            #print "cannot connect to this node"
            print "test"
            ssh.load_system_host_keys()
          
          #  agent_keys = agent.get_keys()
        #print "agent key %s" % len(agent_keys)
      
            
            stdin, stdout, stderr = ssh.exec_command('uname')
            print "OS %s" % stdout.read()
            sshInit.createSshKey(Ip, "../generate_key")
            home = os.path.expanduser("~/")
            kh = open("%s.ssh/known_hosts" % home, "a+")
            print "open %s" % home
            key = open("../generate_key/%s.pub" % Ip, "r")
            keyval = key.read();
        #print "keyval %s" % keyval
            kh.write(keyval);
            kh.close()
            key.close()
            sftp = ssh.open_sftp()
            try:
                sftp.mkdir(".ssh/")
            except IOError:
                print '(assuming demo_sftp_folder/ already exists)'
            sftp.put("../generate_key/%s.pub" % Ip, ".ssh/%s.pub" % Ip)
            print "sftp avan"
            sftp.put("../generate_key/%s" % Ip, ".ssh/%s" % Ip)
            print "sftp apres"
        except paramiko.SFTPError as e:
            print e
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
        except IOError:
            print "creating ~/.ssh/authorized_keys"
            sftp.put(serverkey,".ssh/authorized_keys")
        except(paramiko.AuthenticationException, paramiko.SSHException, 
               paramiko.BadHostKeyException, socket.error, paramiko.SFTPError) as eMsg:
            print eMsg
            
        sftp.close()
        ssh.close()
