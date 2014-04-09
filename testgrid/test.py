# copyright (c) 2013-2014 smartjog, released under the GPL license.

"functional tests"

import unittest

import testgrid

class FakeTest(unittest.TestCase):

	cls = testgrid.client.FakeClient

	def setUp(self):
		self.client = (self.cls)()

	def test_simple_debian_package(self):
		session = self.client.open_session()
		fleche = self.client.get_package(
			name = "fleche",
			version = "16.5-1",
			typename = "debian package")
		node = session.allocate_node(sysname = "wheezy64") # FIXME sysname!!!
		if node.is_installed(fleche):
			node.uninstall(fleche)
		node.install(fleche)
		assert node.is_installed(fleche), "fleche is not installed on %s" % node
		#self.assertEqual(node.service.fleche.get_version(), "16.5-1")
		#self.assertTrue(node.service.fleche.is_running(), "fleche is not running on %s" % node)
		node.uninstall(fleche)

class LocalTest(FakeTest):

	cls = testgrid.local.Client

class RestTest(FakeTest):

	cls = testgrid.rest.Client

if __name__ == "__main__": unittest.main(verbosity = 2)
