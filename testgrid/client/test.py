# copyright (c) 2013-2014 smartjog, released under the GPL license.

import unittest, testgrid, fake, local, rest

class TestCase(unittest.TestCase):
	"base test class, to be derived by changing the client module"

	cls = fake.Client

	def setUp(self):
		self.client = (self.cls)()

	def test_simple_debian_package(self):
		session = self.client.create_session()
		fleche = testgrid.server.debian.Package("fleche", version = "16.5-1")
		node = session.allocate_node(pkg = fleche)
		assert node.install(fleche)
		self.assertEqual(node.service.fleche.version, "16.5-1")
		self.assertTrue(node.service.fleche.is_running())

class LocalTest(TestCase):

	cls = local.Client

class RestTest(TestCase):

	cls = rest.Client

if __name__ == "__main__": unittest.main(verbosity = 2)
