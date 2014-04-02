# copyright (c) 2013-2014 smartjog, released under the GPL license.

import unittest, fake

class TestCase(unittest.TestCase):
	"base test class, to be derived by changing the client module"

	client = fake.Client()

	def test_simple_debian_package(self):
		session = self.client.create_session()
		fleche = testgrid.server.debian.Package("fleche", version = "16.5-1")
		node = session.allocate_node()
		assert node.install(fleche)
		self.assertEqual(node.service.fleche.version, "16.5-1")
		self.assertTrue(node.service.fleche.is_running())

if __name__ == "__main__": unittest.main(verbosity = 2)
