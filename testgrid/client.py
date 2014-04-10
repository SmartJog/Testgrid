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

	def get_package(self, typename, name, version = None):
		cls = testgrid.parser.get_subclass(typename, testgrid.model.Package)
		return cls(name = name, version = version)

	def add_node(self, typename):
		"administration -- add node to grid"
		cls = parser.get_subclass(typename, testgrid.model.Node, __name__)
		node = (cls)()
		self.grid.add_node(node)

	def remove_node(self, node):
		"administration -- remove node from grid"
		self.grid.remove_node(node)

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

	def get_node_status(self, node):
		if self.is_available(node):
			return "available"
		elif self.is_allocated(node):
			return "allocated"
		elif self.is_quarantined(node):
			return "quarantined"
		assert False, "%s: unknown status, please report this bug" % node

	def rehabilitate_node(self, node):
		"administration -- switch node from quarantined to available status"
		self.grid.rehabilitate_node(node)

	def get_sessions(self):
		return self.grid.get_sessions()

	def open_session(self, name = None):
		return self.grid.open_session(username = self.username, name = name)

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

	cls = FakeClient

	def test(self):
		c = (self.cls)()
		session = c.open_session()
		node = session.allocate_node()
		self.assertTrue(c.is_transient(node), "%s: not transient" % node)
		self.assertIn(node, c.get_nodes())
		self.assertIn(node, session)
		self.assertTrue(c.is_allocated(node),"%s: not allocated" % node)
		self.assertIn(session, c.get_sessions())
		session.close()
		self.assertIn(node, c.get_nodes())
		self.assertNotIn(session, c.get_sessions())
		self.assertFalse(node.is_up(), "%s: still up" % node)

if __name__ == "__main__": unittest.main(verbosity = 2)