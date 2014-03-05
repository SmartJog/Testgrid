# copyright (c) 2014 arkena, released under the GPL license.

"https://confluence.arkena.net/display/QA/Portable+Test+Boxes"

import unittest
import pipes
import os

import debian
import model
import shell

class Wheezy64(model.Node):
	"preconfigured wheezy64 box"

	idx = 0

	def __init__(self):
		self.path = "testbox-%i" % Node.idx
		Node.idx += 1
		assert not os.path.exists(self.path), "%s: already exists" % self.path
		shell.run("git clone git@git.smartjog.net:florent.claerhout/testbox.git %s" % self.path, logger = shell.Stderr)
		shell.run("make -C %s up" % self.path, logger = shell.Stderr)

	def __del__(self):
		shell.run("make -C %s deepclean" % self.path, logger = shell.Stderr)
		shell.run("rm -rf %s" % self.path, logger = shell.Stderr)

	log = lambda self, tag, msg: shell.run("cd %s && vagrant ssh -c 'logger -t %s %s'" % (self.path, tag, msg))

	def run(self, *commands):
		res = shell.Success()
		for cmd in commands:
			res += shell.run(
				"cd %s && vagrant ssh -c %s" % (self.path, pipes.quote("%s" % cmd)),
				logger = shell.Stderr,
				warn_only = cmd.warn_only)
		return res

class Grid(model.Grid):

	def create_node(self, sysname = None, pkg = None):
		assert isinstance(pkg, debian.Package), "%s: package type not supported" % type(pkg).__name__
		assert not sysname or sysname == "wheezy64", "%s: unknown sysname" % sysname
		return Wheezy64()