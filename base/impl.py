import database
import model
import os
import unittest
import sshOperation
import subprocess
import command

SSH_CONFIG = "config"
SSH_CONFIG_CONTENT = "StrictHostKeyChecking no\n"

class Deployment(model.Deployment): pass

class IndexedDeployment(model.Deployment): pass

class Session(model.Session):
	def __init__(self, login):
		self.login = login

class IndexedSession(model.Session):

	def __init__(self, hdl, index):
		self.hdl = hdl
		self.index = index

class Node(model.Node):

	def __init__(self, hostname, rootpass, username, userpass, publickey, privatekey, isvirtual=False):
		self.hostname = hostname
		self.rootpass = rootpass
		self.username = username
		self.userpass = userpass
		self.publickey = publickey
		self.privatekey = privatekey
		self.isvirtual = isvirtual

	def __eq__(self, other):
		return self.hostname == other.hostname

	def __ne__(self, other):
		return not (self == other)

class IndexedNode(model.Node):

	def __init__(self, hdl, index):
		self.hdl = hdl
		self.index = index

	def __eq__(self, other):
		return self.index == other.index

	def __ne__(self, other):
		return not (self == other)

	@property
	def hostname(self):
		return self.hdl.getHostname(self.index)

	@property
	def rootpass(self):
		return self.hdl.getRootPass(self.index)

	@property
	def username(self):
		return self.hdl.getUsername(self.index)

	@property
	def userpass(self):
		return self.hdl.getUserpass(self.index)

	def toUsed(self):
		self.hdl.setUsedNode(self.index)


class NodeTable(object):

	def __init__(self, hdl):
		self.hdl = hdl

	def append(self, node):
		self.hdl.addNode(node.hostname,
				 node.username,
				 node.userpass,
				 node.publickey,
				 node.privatekey,
				 node.rootpass,
				 node.isvirtual)

	def remove(self, hostname):
		self.hdl.deleteNode(hostname)
	
	def exist(self, hostname):
		return self.hdl.nodeExist(hostname)

	def getUnsuedNode(self):
		for index in self.hdl.getUnusedNode():
			yield IndexedNode(self.hdl, index)
		


	def __iter__(self):
		for index in self.hdl.listIndex():
			yield IndexedNode(self.hdl, index)

class SessionTable(object):

	def __init__(self, hdl):
		self.hdl = hdl
	
	def exist(self, login):
		return self.hdl.sessionExist(login)

	def append(self, session):
		self.hdl.addSession(session.login)
	
	def remove(self, login):
		self.hdl.deleteSession(login)

	def maxId(self):
		return self.hdl.maxSessionId()

	def indexedSession(self, login):
		index = self.hdl.getSessionIndex(login)
		if index is None:
			return None
		return IndexedSession(self.hdl, index)

class DeploymentTable(object):

	def __init__(self, hdl):
		self.hdl = hdl

	def append(self, session, package, node):
		self.hdl.addDeployment(session.index, node.index, package.name, package.version)
	
	def remove(self, login):
		self.hdl.deleteDeployment()
	

class TestGrid(model.TestGrid):

	def __init__(self, pathDatabase ="TestGrid1.db", sshPath=".ssh/", sshKeyName="testGridkey"):
		hdl = database.Database(databasePath=pathDatabase)
		self.nodes = NodeTable(hdl)
		self.sshConfig(sshPath, sshKeyName)
		self.deployments = DeploymentTable(hdl)
		self.session = SessionTable(hdl)

	def sshConfig(self,sshPath, sshKeyName):
		"initialize testgrid controller ssh configuration"
		try:
			fullSSHPath = "{0}{1}".format(os.path.expanduser("~/"), sshPath)
			if not os.path.exists(fullSSHPath):
				os.mkdir(fullSSHPath)
			if not os.path.exists("{0}{1}".format(fullSSHPath, sshKeyName)) or not os.path.exists(
				"{0}{1}.pub".format(fullSSHPath, sshKeyName)):
				keyPair = sshOperation.sshConnection.createSSHKeyFile(sshKeyName, fullSSHPath)
				sshOperation.sshConnection.initSSHConfigFile("{0}{1}".format(fullSSHPath, SSH_CONFIG), SSH_CONFIG_CONTENT)
				p = subprocess.Popen(["ssh-add","{0}{1}".format(fullSSHPath, sshKeyName)]
						     , stdout=subprocess.PIPE)
				output, err = p.communicate()
				if p.returncode or err:
					raise Exception
				
		except Exception as e:
			print "couldn't init testGridController %s" % e

	def deploy(self, session, package):
		unused = self.nodes.getUnsuedNode()
		for node in unused:
			success = command.Command.installPackage(node.hostname, package.name, package.version)
			if success == True:
				self.deployments.append(session, package, node)
				node.toUsed()
				return "package {0}{1} has been installed successfully on node {2}".format(package.name, package.version, node.hostname) 
		return "couldn't install package {0}{1}".format(package.name, package.version)
			
			
	

############
# test     #
############
class testNode(unittest.TestCase):
	def testInitNode(self):
		"node syncronisation with database"
		test = TestGrid(pathDatabase="testdb.db")
		node = Node("localhost", 
			    "root", 
			    "testuser", 
			    "test", 
			    "publickey", 
			    "privatekey", 
			    False)
		test.nodes.append(node)
		test.nodes.append(node)
		i = 0
		for n in test.nodes:
			i = i + 1
		self.assertEqual(i, 1)
		for n in test.nodes:
			self.assertEqual(node.hostname, n.hostname)
			self.assertEqual(node.username, n.username)
			self.assertEqual(node.userpass, n.userpass)
			self.assertEqual(node.rootpass, n.rootpass)
		test.nodes.remove(node.hostname)
		i = 0
		for n in test.nodes:
			i = i + 1
		self.assertEqual(i, 0)
		self.assertRaises("test")
if __name__ == '__main__':
	unittest.main(verbosity = 2)

# Exemple API REST
#
# tg = TestGrid("my.db")
#
# @post("/add?<hostname>")
# def add(req, hostname, *args, **kwargs):
#	 if admin:
#		 x = addInstance(?)
#		 node = Node(x.hostname, ...)
#		 tg.hosts.append(node)
#

