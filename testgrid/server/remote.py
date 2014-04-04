# copyright (c) 2013-2014 smartjog, released under the GPL license.

import service, shell, model

class ServiceManager(model.ServiceManager):

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

class Node(model.Node):

	def __init__(self, hoststring):
		host = service.Host(hoststring = hoststring)
		srvmanager = ServiceManager(host = host)
		super(Node, self).__init__(srvmanager = srvmanager)
		self.host = host

	def __str__(self):
		return self.host.hoststring

	def type(self):
		return "remote node"

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
