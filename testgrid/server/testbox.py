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
		super(Node, self).__init__()
		self.path = "testbox-%i" % Node.idx
		Node.idx += 1
		assert not os.path.exists(self.path), "%s: already exists" % self.path
		shell.run("git clone git@git.smartjog.net:florent.claerhout/testbox.git %s" % self.path, logger = shell.stderr)
		if tag:
			shell.run("cd %s && git checkout %s" % (self.path, tag), logger = shell.stderr)
		shell.run("cd %s && %s up" % (self.path, entry_path), logger = shell.stderr)

	def __del__(self):
		shell.run("make -C %s deepclean" % self.path, logger = shell.stderr)
		shell.run("rm -rf %s" % self.path, logger = shell.stderr)

	log = lambda self, tag, msg:\
		shell.run("cd %s && vagrant ssh -c 'logger -t %s %s'" % (self.path, tag, msg))

	def run(self, *commands):
		res = shell.Success()
		for cmd in commands:
			res += shell.run(
				"cd %s && vagrant ssh -c %s" % (self.path, pipes.quote("%s" % cmd)),
				logger = shell.stderr,
				warn_only = cmd.warn_only)
		return res

class En0Wifi(model.Grid):

	create_node = lambda self, sysname = None, pkg = None: Node(entry_path = "./en0wifi")

class Eth0Lan(model.Grid):

	create_node = lambda self, sysname = None, pkg = None: Node(entry_path = "./eth0lan")


class Eth2Lan(model.Grid):

	create_node = lambda self, sysname = None, pkg = None: Node(entry_path = "./eth2lan")
