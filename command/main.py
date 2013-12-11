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
OBfrom sshClient import *
import ansible.runner
import ansible.playbook


class State(object):
     Free = 0
     VMinstance = 1
     PHinstance = 2



class Command:
     def __init__(self):
          self.data = ManageDatabase()
          self.func_map = {"add" : self.AddInstance} #, "list" : self.listInstance, "deploy" : self.deployPackage, "rm" : self.deleteInstance}
          if not os.path.exists("../generate_key"):
               os.mkdir("../generate_key")
          if not os.path.exists("../generate_key/testGridkey"):
               sshInit.createSshKey("testGridkey", "../generate_key");
               

     def ManageArg(self, comArray):
          if comArray[1] in self.func_map:
               self.func_map[comArray[1]](comArray);
          else:
                print "Bad argument: %s" % comArray[1]
 
     def AddInstance(self,comArray):
          print "add instance %s" % comArray[2]
          if len(comArray) >= 5:
          #if self.data.CheckIfPhysicalInstanceExist(comArray[2])==False:
           #    print "%s already exist in testGid database" % comArray[2]
            #   return

               try:
                    print "wtf"
                    #if self.data.CheckIfPhysicalInstanceExist(comArray[2])==False:
                    sshInit.checkNewClient(comArray[2], comArray[3], comArray[4], "../generate_key/testGridkey.pub")
                    print "wtf2"
                    agent = paramiko.Agent()
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
                    print e
                    
                    #ssh.close()
               #except(paramiko.AuthenticationException, paramiko.SSHException, paramiko.BadHostKeyException, socket.error) as eMsg:
                    #print "try to add invalide node %s" % eMsg
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
