# copyright (c) 2013-2014 smartjog, released under the GPL license.

import testgrid

class Node(testgrid.model.Node):

	def __init__(self, name, sysname, hoststring):
		super(Node, self).__init__(name = name)
		self.hoststring = hoststring
		self.sysname = sysname

	def get_typename(self):
		return "remote node/%s" % self.sysname

	def has_support(self, sysname = None, **opts):
		return not opts and (not sysname or sysname == self.sysname)

	def get_load(self):
		return .0

	def join(self, subnet):
		raise NotImplementedError()

	def leave(self, subnet):
		raise NotImplementedError()

	def get_subnets(self):
		raise NotImplementedError()

	def get_hoststring(self):
		return testgrid.model.Hoststring(self.hoststring)
