# copyright (c) 2013-2014 smartjog, released under the GPL license.

import service
import shell
import model

import logging

logging.basicConfig(level = logging.DEBUG)

class Node(model.Node):

	def __init__(self, hoststring):
		super(Node, self).__init__(srvmanager = None)
		self.host = service.Host(hoststring = hoststring)

	def __str__(self):
		return self.host.hoststring

	def run(self, *commands):
		res = shell.Success()
		for cmd in commands:
			res += self.host(cmd.cmdline, warn_only = cmd.warn_only)
		return res

	def _setup_interface(self, subnet):
		raise NotImplementedError("remote.Node._setup_interface")

	def _cleanup_interface(self, subnet):
		raise NotImplementedError("remote.Node._cleanup_interface")

	def log(self, tag, msg):
		return self.host("logger -t '%s' '%s'" % (tag, msg))

	def terminate(self):
		raise NotImplementedError("remote.Node.terminate")
