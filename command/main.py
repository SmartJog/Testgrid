#!/usr/bin/python
import MySQLdb
import sys
import json
import ansible.runner
import paramiko
from paramiko import DSSKey
import socket
sys.path.append('../database/')
import initDatabase
from initDatabase import *
from binascii import hexlify


class State(object):
     Free = 0
     VMinstance = 1
     PHinstance = 2



class Command:
     def __init__(self):
          self.func_map = {"add" : self.AddInstance} #, "list" : self.listInstance, "deploy" : self.deployPackage, "rm" : self.deleteInstance}
     #self.os_map = {}
     def ManageArg(self, comArray):
          if comArray[1] in self.func_map:
               self.func_map[comArray[1]](comArray);
          else:
                print "Bad argument: %s" % comArray[1]
 
     def AddInstance(self,comArray):
          print "add instance %s" % comArray[2]
          if len(comArray) >= 5:
               try:
                    prv = DSSKey.generate()
                    prv.write_private_key_file("test_grid", password="test_grid")
                    pub = DSSKey(filename="test_grid", password="test_grid")
                    with open("%s.pub" % "test_grid", 'w') as f:
                         f.write("%s %s" % (pub.get_name(), pub.get_base64()))
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #ssh.connect(comArray[2], username=comArray[3], password=comArray[4])
                    agent = paramiko.Agent()
                    agent_keys = agent.get_keys()
                    print "agent key %s" % len(agent_keys)
                    if len(agent_keys) == 0:
                         return
                    for key in agent_keys:
                         print 'Trying ssh-agent key %s' % hexlify(key.get_fingerprint()),
                         try:
                              ssh.connect(comArray[2], username=comArray[3], pkey=key)
                              #ssh.auth_publickey(comArray[3], key)
                              print '... success!'
                              return
                         except paramiko.SSHException:
                              print '... nope.'
                   
                    print "enter"
                    db = ManageDatabase()
                    print "data"
                    #paramiko.util.log_to_file('ssh.log')
                   
                    stdin, stdout, stderr = ssh.exec_command('uname -a')
                    print stdout.read()
                    #db.AddPhysicalInstance(comArray[2], comArray[3], comArray[4])
                    ssh.close()
               except(paramiko.AuthenticationException, paramiko.SSHException, paramiko.BadHostKeyException, socket.error) as eMsg:
                    print "try to add invalide node %s" % eMsg
          else:
               print "TestGrid Usage: "
    
#     def listInstance(self, comArray):
#    def deployPackage(self, comArray):
#     def deleteInstance(self, comArray):
if __name__ == '__main__':

     if len(sys.argv) >= 2:
          com = Command()
          com.ManageArg(sys.argv)
     else:
         print "Usage: %s" % sys.argv[0]
         sys.exit(1)
