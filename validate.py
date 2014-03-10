# copyright (c) 2014 arkena, released under the GPL license.

import unittest
import client

class TestCase(unittest.TestCase):
	"base test class, to be derived by changing the client module"

	client = client.fake

	def test_simple_debian_package(self):
		session = self.client.Session()
		fleche = self.client.debian.Package("fleche", version = "16.3-1")
		plan = session.deploy(fleche)
		for pkg, node in plan:
			if pkg == fleche:
				self.assertEqual(node.service.fleche.version, "16.3-1")
				self.assertTrue(node.service.fleche.is_running())

	def test_simple_aksetup_package(self):
		session = self.client.Session()
		fleche = self.client.aksetup.Package("fleche", version = "16.3-1")
		plan = session.deploy(fleche)
		for pkg, node in plan:
			if pkg == fleche:
				self.assertEqual(node.service.fleche.version, "16.3-1")
				self.assertTrue(node.service.fleche.is_running())

class TestLocal(TestCase):
	"use a local client, based on testboxes, allowing anonymous sessions only"

	client = client.local

if __name__ == "__main__": unittest.main(verbosity = 2)
