# copyright (c) 2013-2014 smartjog, released under the GPL license.

"client managing sessions for a controller-less grid"

import testgrid

######################################
# concrete types of nodes for parser #
######################################

class RemoteNode(testgrid.server.remote.Node): pass

class DebianNode(testgrid.server.debian.Node): pass

##########
# client #
##########

class UnknownSessionError(Exception): pass

class Client(object):

	def __init__(self, name = "grid", ini = "~/grid.ini"):
		self.grid = testgrid.server.parser.parse_grid(name, ini, __name__)
		self.sessions = {}
		for key in self.grid.get_session_keys():
			self.sessions[key] = testgrid.model.Session(grid = self.grid, key = key) # FIXME subnet

	def get_nodes(self):
		return [node for node in self.grid]

	def add_node(self, typename):
		cls = parser.get_subclass(typename, testgrid.model.Node, __name__)
		node = (cls)()
		self.grid.add_node(node)

	def is_available(self, node):
		return self.grid.is_available(node)

	def is_allocated(self, node):
		return self.grid.is_allocated(node)

	def is_quarantined(self, node):
		return self.grid.is_quarantined(node)

	def get_sessions(self):
		return self.sessions.values()

	def open_session(self, key = None):
		if not key in self.sessions:
			session = testgrid.server.model.Session(
				grid = self.grid,
				key = key,
				subnet = None) # FIXME subnet
			self.sessions[key] = session
		return self.sessions[key]

	def close_session(self, key):
		if key in self.sessions:
			self.sessions[key].close()
			del self.sessions[key]
		else:
			raise UnknownSessionError("%s" % key)
