# copyright (c) 2013-2014 smartjog, released under the GPL license.

import unittest

from testgrid import model

class Node(model.Node):

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

	def get_info(self):
		return "remote node/%s" % self.sysname

	def has_support(self, sysname = None, **opts):
		return not opts and (not sysname or sysname == self.sysname)

	def get_load(self):
		raise NotImplementedError("remote.Node.get_load() not implemented yet")

	def join(self, subnet):
		raise NotImplementedError("remote.Node.join() not implemented yet")

	def leave(self, subnet):
		raise NotImplementedError("remote.Node.leave() not implemented yet")

	def get_subnets(self):
		raise NotImplementedError("remote.Node.get_subnets() not implemented yet")

	def get_hoststring(self):
		return testgrid.model.Hoststring(self.hoststring)

	def get_installed_packages(self):
		raise NotImplementedError("remote.Node.get_installed_packages() not implemented yet")

#########
# tests #
#########

class SelfTest(unittest.TestCase):

	def test_FIXME(self):
		node = Node(name = "foo", sysname = "bar", hoststring = "bar")

if __name__ == "__main__": unittest.main(verbosity = 2)
