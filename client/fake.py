# test doubles designed to test tests :)

import server

class Subnet(object): pass

class DummyNode(server.model.Node):

	def __init__(self, subnet, cls):
		self.terminated = False
		self.installed = []
		self.subnet = subnet

	ping = lambda self, node: self.subnet == node.subnet

	def terminate(self):
		self.terminated = True

	def install(self, package):
		assert not self.terminated
		self.installed.append(package)
		return self

	def uninstall(self, package):
		assert not self.terminated
		self.installed.remove(package)

	def is_installable(self, package):
		assert not self.terminated
		return True

class DummyGrid(server.model.Grid):

	create_node = lambda self, subnet, cls: DummyNode(subnet = subnet, cls = cls)

grid = DummyGrid()

sessions = {}

class Session(object):

	def __init__(self, name = None):
		self.subnet = Subnet()
		self.name = name
		if name:
			assert not name in sessions
			sessions[name] = self.subnet

	def close(self):
		if self.name:
			del sessions[self.name]

	def __del__(self):
		if not self.name:
			self.close()

	allocate_node = lambda self, subnet, cls: grid.create_node(subnet = self.subnet, cls = cls)

	deploy = lambda self, *packages: grid.deploy(*packages)
