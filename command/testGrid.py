#!/usr/bin/python
import sys
import os
import subprocess
import json
import sshOperation
from sshOperation import sshConnection
from sshOperation import sshKey
import execCommand
from execCommand import execCommand
import socket
sys.path.append('../database/')
import initDatabase
import shutil
import getpass
import testGridString
from testGridString import *

class testGridController:
     def __init__(self):
         
          self.command = execCommand()
          try:
               home = os.path.expanduser("~/")
               if not os.path.exists(SSH_PATH.format(home)):
                    os.mkdir(SSH_PATH.format(home))
               if not os.path.exists("{0}{1}".format(SSH_PATH.format(home), TESTGRID_KEY_NAME)) or not os.path.exists("{0}{1}.pub".format(SSH_PATH.format(home), TESTGRID_KEY_NAME)):
                 keyPair = sshConnection.createSSHKeyFile(TESTGRID_KEY_NAME, SSH_PATH.format(home))
                 sshConnection.initSSHConfigFile("{0}{1}".format(SSH_PATH.format(home), SSH_CONFIG), SSH_CONFIG_CONTENT)
                 p = subprocess.Popen(["ssh-add","{0}{1}".format(SSH_PATH.format(home), TESTGRID_KEY_NAME)]
                                      , stdout=subprocess.PIPE)
                 output, err = p.communicate()
                 if p.returncode or err:
                     print 'couldn''t add testgridkey to agent...'
          except Exception as e:
               print "couldn't init testGridController %s" % e

     def manageArg(self, httpArg):
          result = self.command.execCommand(httpArg)
          return result


"""if __name__ == '__main__':
if len(sys.argv) >= 2:
         testGrid.manageArg(sys.argv[1:])
    else:
         print "Usage: %s" % sys.argv[0]
    sys.exit(1)"""
