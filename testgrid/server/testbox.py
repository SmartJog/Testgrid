# copyright (c) 2014 arkena, released under the GPL license.

"https://confluence.arkena.net/display/QA/Portable+Test+Boxes"

import unittest
import pipes
import os

import debian
import model
import shell

class Node(model.Node):
	"preconfigured wheezy64 box"

	idx = 0

	def __init__(self, entry_path, tag = None):
	#def __init__(self, use_proxy, bridge, tag = None):
		super(Node, self).__init__()
		self.path = "testbox-%i" % Node.idx
		Node.idx += 1
		self.entry_path = entry_path
		#self.use_proxy = use_proxy
		#self.bridge = bridge
		assert not os.path.exists(self.path), "%s: already exists" % self.path
		shell.run("git clone git@git.smartjog.net:florent.claerhout/testbox.git %s" % self.path, logger = shell.Stderr)
		if tag:
			shell.run("cd %s && git checkout %s" % (self.path, tag), logger = shell.Stderr)
		shell.run("cd %s && %s up" % (self.path, entry_path), logger = shell.Stderr)
		#shell.run("cd %s && USE_PROXY=%s BRIDGE=%s make -C %s up" % (self.path, self.use_proxy, self.bridge), logger = shell.Stderr)

	def __del__(self):
		shell.run("make -C %s deepclean" % self.path, logger = shell.Stderr)
		shell.run("rm -rf %s" % self.path, logger = shell.Stderr)

	log = lambda self, tag, msg:\
		shell.run("cd %s && vagrant ssh -c 'logger -t %s %s'" % (self.path, tag, msg))

	def run(self, *commands):
		res = shell.Success()
		for cmd in commands:
			res += shell.run(
				"cd %s && vagrant ssh -c %s" % (self.path, pipes.quote("%s" % cmd)),
				logger = shell.Stderr,
				warn_only = cmd.warn_only)
		return res

class Grid(model.Grid):

#	def __init__(self, use_proxy, bridge, host=None, port=None ,*args, **kwargs):
	def __init__(self, entry_path, host=None, port=None, *args, **kwargs):
		super(Grid, self).__init__(*args, **kwargs)
		self.host = host
		self.port = port
		self.entry_path = entry_path
		#self.use_proxy = use_proxy
		#self.bridge = bridge

	create_node = lambda self, sysname = None, pkg = None: Node(entry_path=self.entry_path)


