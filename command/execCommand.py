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
import parseCommandLine
from parseCommandLine import parseCommand
import testGridString 
from testGridString import *
import parseCommandString
from parseCommandString import commandName

class execCommand:
     def __init__(self):
          self.data = initDatabase.ManageDatabase()
          self.func_map = {commandName.ADD : self.addInstance, commandName.RM : self.deleteInstance, commandName.LIST : self.listInstance}#, "--deploy" : self.deployPackage}
          self.parser = parseCommand(self.func_map)




     def execCommand(self, comArray):
          self.parser.execParser(comArray)

     def getRootPwd(self):
          pwd = getpass.getpass('root password:')
          return pwd
 
     def addInstance(self, arg):
          for host in arg.hostname:
               if self.data.checkIfPhysicalInstanceExist(host)==True:
                    sys.stderr.write("%s already exist in testGrid database\n" % host)
               else:
                    try:
                         pwd = self.getRootPwd()
                         home = os.path.expanduser("~/")
                         keyPair = sshConnection.checkNewClient(host, "root" ,pwd,"{0}{1}.pub".format(SSH_PATH.format(home), TESTGRID_KEY_NAME))
                         if keyPair == None:
                              sys.stderr.write("can't add %s to testgrid\n" % host)
                              continue
                         UserData = sshConnection.newClientInitInfo(host, pwd, keyPair)
                         if UserData == None:
                              sys.stderr.write("can't add %s to testgrid\n" % host)
                              continue
                         self.data.addPhysicalInstance(UserData.IpAdd , UserData.UserName, UserData.pwd, UserData.pubKey, UserData.privKey, UserData.pwdRoot)
                    except Exception as e:
                         print e

     def deleteInstance(self, arg):
          for host in arg.hostname:
               self.data.deletePhysicalInstance(host)

     def listInstance(self, arg):
          self.data.listInstance()
#    def deployPackage(self, comArray):


