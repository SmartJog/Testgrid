#!/usr/bin/python
import sys
import os
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
          self.func_map = {"add" : self.AddInstance, "rm" : self.deleteInstance, "list" : self.listInstance}#, "deploy" : self.deployPackage, "rm" : self.deleteInstance}
          home = os.path.expanduser("~/")
          if not os.path.exists("../generate_key"):
               os.mkdir("../generate_key")
          if not os.path.exists("../generate_key/testGridkey"):
               sshInit.createSshKey("testGridkey", "../generate_key", False)
               p = subprocess.Popen(["ssh-add","../generate_key/testGridkey"], stdout=subprocess.PIPE)
               output, err = p.communicate()
               if p.returncode or err:
                    print 'couldn''t add testgridkey to agent...'
          if not os.path.exists("%s.ssh/" % home):
               os.mkdir("%s.ssh/" % home)
          shutil.copy("../generate_key/testGridkey", "%s.ssh/testGridkey" % home)
          shutil.copy("../generate_key/testGridkey.pub", "%s.ssh/testGridkey.pub" % home)
          #os.chmod("%s.ssh/testGridkey.pub" % home, 600)
          #os.chmod("%s.ssh/testGridkey" % home, 600)
      
         # print "output %s" % output

     def ManageArg(self, comArray):
          if comArray[1] in self.func_map:
               self.func_map[comArray[1]](comArray);
          else:
                print "Bad argument: %s" % comArray[1]
     def getRootPwd(self):
          pwd = getpass.getpass('root password:')
          return pwd
 
     def AddInstance(self,comArray):
          #print "add instance %s" % comArray[2]
          if len(comArray) < 3:
               sys.stderr.write('Usage Testgrid: add')
               return 
          if self.data.CheckIfPhysicalInstanceExist(comArray[2])==True:
               sys.stderr.write("%s already exist in testGrid database\n" % comArray[2])
               return

          try:
               pwd = self.getRootPwd()
               sshInit.checkNewClient(comArray[2], "root" ,pwd, "../generate_key/testGridkey.pub")
               UserData = sshInit.newClientInitInfo(comArray[2], pwd, self.data)
               if UserData == None:
                    print "can't add %s" % comArray[2]
               self.data.AddPhysicalInstance(UserData.IpAdd , UserData.UserName, UserData.pwd, UserData.pubKey, UserData.privKey, UserData.pwdRoot)
          except Exception as e:
               print e

     def deleteInstance(self, comArray):
          if len(comArray) < 3:
               sys.stderr.write('Usage Testgrid: rm')
               return
          self.data.DeletePhysicalInstance(comArray[2])

     def listInstance(self, comArray):
          if len(comArray) < 2:
               sys.stderr.write('Usage Testgrid: rm')
               return
          self.data.listInstance()
#    def deployPackage(self, comArray):

if __name__ == '__main__':
     if len(sys.argv) >= 2:
          com = Command()
          com.ManageArg(sys.argv)
     else:
          print "Usage: %s" % sys.argv[0]
     sys.exit(1)
