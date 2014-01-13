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
          self.func_map = {commandName.ADD : self.addInstance,
                           commandName.RM : self.deleteInstance, commandName.LIST : self.listInstance}#, "--deploy" : self.deployPackage}
          self.parser = parseCommand(self.func_map)


     def execCommand(self, argHttp):
          result = self.parser.execParser(argHttp)
          return result

     def getRootPwd(self):
          pwd = getpass.getpass('root password:')
          return pwd
 
     def addInstance(self, arg):
          result = None
          for host in arg.hostname:
               if self.data.checkIfPhysicalInstanceExist(host)==True:
                    result = "%s already exist in testGrid database\n" % host
                    return result
               else:
                    try:
                         home = os.path.expanduser("~/")
                         keyPair = sshConnection.checkNewClient(host, "root" , arg.root,"{0}{1}.pub".format(SSH_PATH.format(home), TESTGRID_KEY_NAME))
                         if keyPair == None:
                              result = "can't add %s to testgrid\n" % host
                              return result
                              continue
                         UserData = sshConnection.newClientInitInfo(host, arg.root, keyPair)
                         if UserData == None:
                              result = "can't add %s to testgrid\n" % host
                              return result
                              continue
                         result = self.data.addPhysicalInstance(UserData.IpAdd , UserData.UserName, UserData.pwd, UserData.pubKey, UserData.privKey, UserData.pwdRoot)
                         return "testUser has been created pass = %s" % UserData.pwd  + '\n' + result
                    except Exception as e:
                         print e
     def deleteInstance(self, arg):
          for host in arg.hostname:
               result = self.data.deletePhysicalInstance(host)
               return result

     def listInstance(self, arg):
          result = self.data.listInstance()
          return result
#    def deployPackage(self, comArray):


