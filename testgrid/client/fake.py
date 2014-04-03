# copyright (c) 2013-2014 smartjog, released under the GPL license.

import testgrid

class Package(testgrid.server.model.Package):

	def get_install_commands(self): pass

	def get_uninstall_commands(self): pass
	
	def get_is_installed_commands(self): pass

	def get_is_installable_commands(self): pass

class ServiceManager(testgrid.server.model.ServiceManager):

	def __init__(self):
		self.versions = {}

	def add_service(self, name, version):
		self.versions[name] = version

	def remove_service(self, name):
		del self.versions[name]

	def start(self): pass

	def stop(self): pass

	def restart(self): pass

	def reload(self): pass

	def is_running(self, name):
		return True

	def get_version(self, name):
		return self.versions[name]

class Node(testgrid.server.model.FakeNode):

	def __init__(self):
		super(Node, self).__init__(srvmanager = ServiceManager())

	def install(self, package):
		res = super(Node, self).install(package)
		self.service.add_service(package.name, package.version)
		return res

	def uninstall(self, package):
		res = super(Node, self).uninstall(package)
		self.service.remove_service(package.name)
		return res

class Grid(testgrid.server.model.FakeGrid):

	def _create_node(self, **opts):
		return Node()

class Client(object):

	def __init__(self):
		self.grid = Grid(name = "fakegrid") # generative grid of fake.Node nodes.
		self.sessions = {}

	def list_sessions(self):
		return self.sessions.values()

	def create_session(self, key = None):
		return testgrid.server.model.Session(grid = self.grid, key = key)
