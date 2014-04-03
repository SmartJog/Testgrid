# copyright (c) 2013-2014 smartjog, released under the GPL license.

import service
import shell
import model

class Node(model.Node):

	def __init__(self, hoststring):
		self.host = service.Host(hoststring = hoststring)

	def run(self, *commands):
		res = shell.Success()
		for cmd in commands:
			res += self.host(cmd.cmdline, logger = shell.Stderr, warn_only = cmd.warn_only)
		return res

	def _setup_interface(self, subnet):
		raise NotImplementedError()

	def _cleanup_interface(self, subnet):
		raise NotImplementedError()

	def log(self, tag, msg):
		raise NotImplementedError()

	def terminate(self):
		raise NotImplementedError()
