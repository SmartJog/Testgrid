# copyright (c) 2013-2014 smartjog, released under the GPL license.

import server

class Package(server.model.Package):

	def get_install_commands(self): pass

	def get_uninstall_commands(self): pass
	
	def get_is_installed_commands(self): pass

	def get_is_installable_commands(self): pass

class ServiceManager(server.model.ServiceManager):

	def __init__(self):
		self.versions = {}

	def set_version(self, name, version):
		self.versions[name] = version

	def start(self): pass

	def stop(self): pass

	def restart(self): pass

	def reload(self): pass

	def is_running(self, name):
		return True

	def get_version(self, name):
		return self.versions[name]

class Node(server.model.FakeNode):

	service = ServiceManager()

class Grid(server.model.FakeGrid):

	def create_node(self, **opts):
		return Node()

class Client(object):

	def __init__(self):
		self.grid = Grid() # generative grid of fake.Node nodes.
		self.sessions = {}

	def list_sessions(self):
		return self.sessions.values()

	def create_session(self, key = None):
		return server.model.Session(grid = self.grid, key = key)
