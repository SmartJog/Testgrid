import sys
import os
import json
import paramiko
from paramiko import DSSKey
import socket
from binascii import hexlify
import shutil

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
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(Ip, username=userName, password=passw)
        print "test"
        stdin, stdout, stderr = ssh.exec_command('uname')
        #print "OS %s" % stdout
        sshInit.createSshKey(Ip, "../generate_key")
        home = os.path.expanduser("~/")
        kh = open("%s.ssh/known_hosts" % home, "a+")
        print "open %s" % home
        key = open("../generate_key/%s.pub" % Ip, "r")
        keyval = key.read();
        kh.write(keyval);
        kh.close()
        key.close()
        try:

            sftp = ssh.open_sftp();
            print "sftp avan"
        #sftp.mkdir(".ssh")
            print "sftp avan"
            sftp.put("../generate_key/%s.pub" % Ip, ".ssh/")
            print "sftp avan"
            sftp.put("../generate_key/%s" % Ip, ".ssh/")
            print "sftp apres"
        except SFTPError as e:
            print e
        try:
            sftp.stat("~/.ssh/authorirized_keys")
            sftp.get("~/.ssh/authorirized_keys", "../tmp/authorirized_keys")
            f = open("../tmp/authorirized_keys", "a+")
            fServer = open(serverkey, "r")
            ks = fServer.read()
            f.write(ks)
            f.close()
            fServer.close()
            sftp.put("../tmp/authorirized_keys", "~/.ssh/authorirized_keys")
        except SFTPError:
            print "sftp error"
            sftp.put(serverkey, "~/.ssh/authorirized_keys")
        sftp.close()
        ssh.close()
