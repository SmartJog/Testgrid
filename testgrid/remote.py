# copyright (c) 2013-2014 smartjog, released under the GPL license.

import testgrid

class Node(testgrid.model.Node):

	def __init__(self, name, sysname, hoststring):
		super(Node, self).__init__(name = name)
		self.hoststring = hoststring
		self.sysname = sysname

	def __eq__(self, other):
		if self.hoststring == other.hoststring:
			return True
		return False

	def __ne__(self, other):
		return not (self == other)

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

	def get_installed_packages(self):
		raise NotImplementedError()
