# copyright (c) 2013-2014 smartjog, released under the GPL license.

import testgrid, unittest, getpass

class Client(object):

	def __init__(self, grid, username = None):
		self.grid = grid
		self.username = username or getpass.getuser()

	def get_nodes(self):
		"administration -- list all nodes in grid"
		for node in self.grid:
			yield node

	def get_node(self, name):
		for node in self.grid:
			if node.name == name:
				return node
		raise KeyError("%s" % name)

	def get_node_dictionary(self, name, ini):
		dic = testgrid.parser.parse_node_dictionary(name, ini)
		return dic

	def get_package(self, typename, name, version = None):
		cls = testgrid.parser.get_subclass(typename, testgrid.model.Package)
		pkg_name, pkg_version = name.partition("=")[::2]
		if pkg_version is "":
			v = None
		return cls(name = pkg_name, version = pkg_version)

	def add_node(self, name, ini):
		"administration -- instanciate and add node to grid from manifest, return instance"
		node = testgrid.parser.parse_node(name, ini = ini)
		self.grid.add_node(node)
		return node

	def remove_node(self, name):
		"administration -- instanciate and remove node from grid, return instance"
		node = self.get_node(name)
		self.grid.remove_node(node)
		return node

	def is_available(self, node):
		"administration -- return True if the node is available"
		return self.grid.is_available(node)

	def is_allocated(self, node):
		"administration -- return True if the node is allocated"
		return self.grid.is_allocated(node)

	def is_quarantined(self, node):
		"administration -- return True if the node is quarantined"
		return self.grid.is_quarantined(node)

	def is_transient(self, node):
		"administration -- return True if the node is transient"
		return self.grid.is_transient(node)

	def quarantine_node(self, name, reason):
		"administration"
		node = self.get_node(name)
		self.grid.quarantine_node(node, reason)

	def rehabilitate_node(self, name):
		"administration -- switch node from quarantined to available status"
		node = self.get_node(name)
		self.grid.rehabilitate_node(node)

	def get_sessions(self):
		return self.grid.get_sessions()

	def get_session(self, name):
		for session in self.grid.get_sessions():
			if session.name == name and session.username == self.username:
				return session
		raise KeyError(" %s" % name)

	def get_node_session(self, node):
		"return session that contains a specific node"
		for session in self.grid.get_sessions():
			if node in session:
				return session

	def open_session(self, name = None):
		return self.grid.open_session(username = self.username, name = name)

	def close_session(self, name):
		session = self.get_session(name)
                session.close()


##############
# unit tests #
##############

class FakeClient(Client):

	def __init__(self):
		grid = testgrid.model.FakeGrid(name = "grid") # generative grid of fake nodes
		super(FakeClient, self).__init__(grid = grid)

	def open_session(self):
		return super(FakeClient, self).open_session(name = None) # anonymous session only

	def get_package(self, typename, name, version = None):
		return testgrid.model.FakePackage(name = name, version = version)

class SelfTest(unittest.TestCase):

	client_cls = FakeClient

	def test(self):
		client = (self.client_cls)()
		session = client.open_session()
		node = session.allocate_node()
		self.assertTrue(client.is_transient(node), "%s: not transient" % node)
		self.assertIn(node, client.get_nodes())
		self.assertIn(node, session)
		self.assertTrue(client.is_allocated(node),"%s: not allocated" % node)
		self.assertIn(session, client.get_sessions())
		session.close()
		self.assertIn(node, client.get_nodes())
		self.assertNotIn(session, client.get_sessions())
		self.assertFalse(node.is_up(), "%s: still up" % node)

if __name__ == "__main__": unittest.main(verbosity = 2)
