import database
import model

class Deployment(model.Deployment): pass

class IndexedDeployment(model.Deployment): pass

class Node(model.Node):

	def __init__(self, hostname, rootpass, username, userpass, publickey, privatekey):
		self.hostname
		self.rootpass
		self.username
		self.userpass
		self.publickey
		self.privatekey

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
		raise NotImplementedError()

	@property
	def rootpass(self):
		raise NotImplementedError()

	@property
	def username(self):
		raise NotImplementedError()

	@property
	def userpass(self):
		raise NotImplementedError()

class NodeTable(object):

	def __init__(self, hdl):
		self.hdl

	def append(self, node):
		self.hdl.addPhysicalInstance(
			node.hostname,
			node.username,
			node.userpass,
			node.publickey,
			node.privatekey,
			node.rootpass)

	def remove(self, node):
		self.hdl.deletePhysicalInstance(node.hostname)

	def __iter__(self):
		for index in self.hdl.listInstance():
			yield IndexedNode(self.hdl, index)

class TestGrid(model.TestGrid):

	def __init__(self, path):
		hdl = database.initDatabase.ManageDatabase()
		self.nodes = NodeTable(hdl)
		self.deployments = Deployment(hdl)

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

