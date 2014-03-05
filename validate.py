#!/usr/bin/python2.7

import unittest
import client

class TestCase(unittest.TestCase):

	Session = client.fake.Session

	def test_usecase_1(self):
		"test deployment of a simple debian package, Fleche 16.3-1"
		session = self.Session()
		pkg = client.debian.Package("fleche", version = "16.3-1")
		plan = session.deploy(pkg)
		for pkg, node in plan:
			self.assertEqual(node.service.fleche.version, "16.3-1")
			self.assertTrue(node.service.fleche.is_running())

#class TestBox(TestCase):

#	Session = client.testbox.Session

if __name__ == "__main__": unittest.main(verbosity = 2)
