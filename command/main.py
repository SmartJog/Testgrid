#!/usr/bin/python
import sys
import json
import paramiko
from paramiko import DSSKey
import socket
sys.path.append('../database/')
import initDatabase
from initDatabase import *
import sshClient
from sshClient import *
#import ansible.runner
#import ansible.playbook
import getpass

class State(object):
     Free = 0
     VMinstance = 1
     PHinstance = 2



class Command:
     def __init__(self):
          self.data = ManageDatabase()
          self.func_map = {"add" : self.AddInstance} #, "list" : self.listInstance, "deploy" : self.deployPackage, "rm" : self.deleteInstance}
          home = os.path.expanduser("~/")
          if not os.path.exists("../generate_key"):
               os.mkdir("../generate_key")
          if not os.path.exists("../generate_key/testGridkey"):
               sshInit.createSshKey("testGridkey", "../generate_key");
               if not os.path.exists("%s.ssh/" % home):
                    os.mkdir("%s.ssh/" % home)
               
          shutil.copy("../generate_key/testGridkey", "%s.ssh/testGridkey" % home)
          shutil.copy("../generate_key/testGridkey.pub", "%s.ssh/testGridkey.pub" % home)

     def ManageArg(self, comArray):
          if comArray[1] in self.func_map:
               self.func_map[comArray[1]](comArray);
          else:
                print "Bad argument: %s" % comArray[1]
     def getRootPwd(self):
          pwd = getpass.getpass('root password:')
          print "pwd %s" % pwd
          return pwd
 
     def AddInstance(self,comArray):
          print "add instance %s" % comArray[2]
          if len(comArray) < 3:
               sys.stderr.write('Usage Testgrid: add')
               return 
          if self.data.CheckIfPhysicalInstanceExist(comArray[2])==True:
               sys.stderr.write("%s already exist in testGid database" % comArray[2])
               return

          try:
               print "root"
               pwd = self.getRootPwd()
               sshInit.checkNewClient(comArray[2], "root" ,pwd, "../generate_key/testGridkey.pub")
               print "after check"
               sshInit.newClientInitInfo(comArray[2])
          except Exception as e:
               print e
               """ agent = paramiko.Agent()
               agent_keys = agent.get_keys()
               print "agent key %s" % len(agent_keys)
               if len(agent_keys) == 0:
               return
               try:
               for key in agent_keys:
               print 'Trying ssh-agent key %s' % hexlify(key.get_fingerprint()),
               ssh = paramiko.SSHClient()
               ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
               ssh.load_system_host_keys()
               ssh.connect(comArray[2], username=comArray[3], pkey=key, allow_agent=True, look_for_keys=True)
               #ssh.auth_publickey(comArray[3], key)
               print '... success!'
               return
               #except paramiko.PasswordRequiredException:
               #    print "need pass"
               except paramiko.SSHException:
               print '... nope.'
               print "agent close"
               agent.close();
               
               print "data"
               self.data.AddPhysicalInstance(comArray[2], comArray[3], comArray[4])
               except Exception as e:
               print e"""
                    
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
