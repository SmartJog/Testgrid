# copyright (c) 2013-2014 smartjog, released under the GPL license.

import unittest, testgrid

class FakeTest(unittest.TestCase):
	"base test class, to be derived by changing the client module"

	cls = testgrid.client.fake.Client

	def setUp(self):
		self.client = (self.cls)()

	def test_simple_debian_package(self):
		session = self.client.create_session()
		fleche = testgrid.server.debian.Package("fleche", version = "16.5-1")
		node = session.allocate_node(sysname = "wheezy64")
		if node.is_installed(fleche):
			node.uninstall(fleche)
		node.install(fleche)
		assert node.is_installed(fleche), "fleche is not installed on %s" % node
		self.assertEqual(node.service.fleche.version, "16.5-1")
		self.assertTrue(node.service.fleche.is_running(), "fleche is not running on %s" % node)
		node.uninstall(fleche)

class LocalTest(FakeTest):

	cls = testgrid.client.local.Client

class RestTest(FakeTest):

	cls = testgrid.client.rest.Client

if __name__ == "__main__": unittest.main(verbosity = 2)
