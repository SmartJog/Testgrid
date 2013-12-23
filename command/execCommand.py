#!/usr/bin/python
import sys
import os
import json
import sshOperation
from sshOperation import sshConnection
from sshOperation import userInfo
from sshOperation import sshKey
import socket
sys.path.append('../database/')
import initDatabase
import shutil
import getpass
import testGridString 
from testGridString import *



class execCommand:
     def __init__(self):
          self.data = initDatabase.ManageDatabase()
          self.func_map = {"add" : self.addInstance, "rm" : self.deleteInstance, "list" : self.listInstance}#, "--deploy" : self.deployPackage}
     

     def execArg(self, comArray):
          if comArray[1] in self.func_map:
               self.func_map[comArray[1]](comArray);
          else:
                print "Bad argument: {0}".format(comArray[1])

     def getRootPwd(self):
          pwd = getpass.getpass('root password:')
          return pwd
 
     def addInstance(self,comArray):
          if len(comArray) < 3:
               sys.stderr.write('Usage Testgrid: add\n')
               return 
          if self.data.checkIfPhysicalInstanceExist(comArray[2])==True:
               sys.stderr.write("%s already exist in testGrid database\n" % comArray[2])
               return

          try:
               pwd = self.getRootPwd()
               home = os.path.expanduser("~/")
               keyPair = sshConnection.checkNewClient(comArray[2], "root" ,pwd, os.path.exists("{0}{1}.pub".format(SSH_PATH.format(home), TESTGRID_KEY_NAME)))
               UserData = sshConnection.newClientInitInfo(comArray[2], pwd, keyPair)
               if UserData == None:
                    sys.stderr.write("can't add %s to testgrid" % comArray[2])
                    return
               self.data.addPhysicalInstance(UserData.IpAdd , UserData.UserName, UserData.pwd, UserData.pubKey, UserData.privKey, UserData.pwdRoot)
          except Exception as e:
               print e

     def deleteInstance(self, comArray):
          if len(comArray) < 3:
               sys.stderr.write('Usage Testgrid: rm')
               return
          self.data.deletePhysicalInstance(comArray[2])

     def listInstance(self, comArray):
          if len(comArray) < 2:
               sys.stderr.write('Usage Testgrid: rm')
               return
          self.data.listInstance()
#    def deployPackage(self, comArray):


