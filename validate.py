# copyright (c) 2014 arkena, released under the GPL license.

import unittest
import testgrid

class TestCase(unittest.TestCase):
	"base test class, to be derived by changing the client module"

	client = testgrid.client.fake

	def test_simple_debian_package(self):
		session = self.client.Session()
		fleche = testgrid.server.debian.Package("fleche", version = "16.5-1")
		node = session.allocate_node()
		#assert node.install(fleche)
		#self.assertEqual(node.service.fleche.version, "16.5-1")
		#self.assertTrue(node.service.fleche.is_running())

# 	def test_simple_aksetup_package(self):
#		session = self.client.Session()
#		fleche = testgrid.client.aksetup.Package("fleche", version = "16.3-1")
#		plan = session.deploy(fleche)
#		for pkg, node in plan:
#			if pkg == fleche:
#				self.assertEqual(node.service.fleche.version, "16.3-1")
#				self.assertTrue(node.service.fleche.is_running())

	#def test_linearisator_aksetup_package(self):
	#	session = self.client.Session()
	#	linearisator = self.client.aksetup.Package("linearisator", version = "0.1.5-1")
	#	plan = session.deploy(linearisator)
	#	for pkg, node in plan:
	#		if pkg == linearisator:
	#			self.assertEqual(node.service.linearisator.version, "0.1.5-1")
	#			self.assertTrue(node.service.linearisator.is_running())"""

class TestLocal(TestCase):
	"use a local client, based on testboxes, allowing anonymous sessions only"

	client = testgrid.client.local
	def test_simple_debian_node(self):
		session = self.client.Session()
		fleche = testgrid.server.debian.Package("fleche", version = "16.5-1")
		n = session.allocate_node()
	#assert n.install(fleche)

	def test_rest(self):
		s = testgrid.client.restclient.Session("127.0.0.1", 8080)
		n = s.allocate_node()
		assert type(n) is testgrid.common.simplifiedModel.responseObject
		assert type(n.data) is testgrid.common.simplifiedModel.Node


if __name__ == "__main__": unittest.main(verbosity = 2)
