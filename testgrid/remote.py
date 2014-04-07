# copyright (c) 2013-2014 smartjog, released under the GPL license.

import unittest

import testgrid

class ServiceManager(testgrid.model.ServiceManager):

	def __init__(self, host):
		self.host = host

	def start(self, name):
		return self.host.start(name)

	def stop(self, name):
		return self.host.stop(name)

	def restart(self, name):
		return self.host.restart(name)

	def reload(self, name):
		return self.host.reload(name)

	def get_version(self, name):
		return self.host.version(name)

	def is_running(self, name):
		return bool(self.host.running(name, warn_only = True))

class Node(testgrid.model.Node):

	def __init__(self, name, hoststring):
		host = testgrid.service.Host(hoststring = hoststring)
		srvmanager = ServiceManager(host = host)
		super(Node, self).__init__(name = name, srvmanager = srvmanager)
		self.host = host

	def __str__(self):
		return self.host.hoststring

	def get_typename(self):
		return "remote node"

	def join(self, subnet):
		raise NotImplementedError("remote.Node.join")

	def leave(self, subnet):
		raise NotImplementedError("remote.Node.leave")

	def get_subnets(self):
		raise NotImplementedError("remote.Node.get_subnets")

	def terminate(self):
		raise NotImplementedError("remote.Node.terminate")

	def run(self, *commands):
		res = testgrid.shell.Success()
		for cmd in commands:
			res += self.host(cmd.cmdline, warn_only = cmd.warn_only)
		return res

	def log(self, tag, msg):
		return self.host("logger -t '%s' '%s'" % (tag, msg))

##############
# unit tests #
##############

class SelfTest(unittest.TestCase):

	def test(self):
		node = Node("test", "root@test")

if __name__ == "__main__": unittest.main(verbosity = 2)
