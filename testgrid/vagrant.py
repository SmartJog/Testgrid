# copyright (c) 2014 smartjog, released under the GPL license.

import model, shell

class Node(model.Node):

	def __init__(self, name, url):
		super(Node, self).__init__(name = name, srvmanager = None)
		self.path = "tg-vagrantnode-%s" % name
		assert not os.path.exists(self.path), "%s: already exists" % self.path
		os.mkdir(self.path)

	def __del__(self):
		shell.run("rm -rf %s" % self.path, logger = shell.Stderr)

	def get_typename(self):
		return "vagrant node"

	def join(self, subnet):
		raise NotImplementedError()

	def leave(self, subnet):
		raise NotImplementedError()

	def get_subnets(self):
		raise NotImplementedError()

	def terminate(self):
		raise NotImplementedError()

	def run(self, *commands):
		raise NotImplementedError()

	def log(self, tag, msg):
		raise NotImplementedError()

class Grid(model.Grid):

	def __init__(self, name, logger = None):
		# read directories here
		super(Grid, self).__init__(name = name, logger = logger)

	def _create_node(self, sysname = None, pkgname = None):
		return Node()
