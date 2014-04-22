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

@unittest.skip("deprecated")
class LocalTest(FakeTest):

	cls = testgrid.local.Client
	@staticmethod
	def get_file(content = ""):
		"generate a temporary file with the specified content"
		f = tempfile.NamedTemporaryFile()
		f.write(textwrap.dedent(content))
		f.flush()
		return f

	@staticmethod
	def persistency_data(self):
		"generate ini file and instantiate client object in order to test persistency"
		f = self.get_file("""
                          [grid]
                          type = persistentGrid
                          database = persistency.db""") #persistentGrid creates the database file
		client = testgrid.client.local.Client(name="grid", ini=f)
		secondclient = testgrid.client.local.Client(name="grid", ini=f)
		return (client, secondclient)

	def test_base_persistent_Grid(self):
		"add a node in a persistent grid"
		client, secondclient = persistency_data()
		node = testgrid.server.model.FakeNode()
		client.add_node(node)
		self.assertIn(node, secondclient.get_nodes())
		client.remove_node(node)
		self.assertNotIn(node, client.get_nodes())
		self.assertNotIn(node, secondclient.get_nodes())

	def test_session_persistent_Grid(self):
		"verify session persistency"
		client, secondclient = persistency_data()
		session = client.open_session()
		self.assertIn(session,  secondclient.get_sessions())
		session.close()
		self.assertNotIn(session, secondclient.get_sessions())
		self.assertNotIn(session, client.get_sessions())

	def test_session_node_allocation_persistent_Grid(self):
		"verify node allocation persistency"
		client, secondclient = persistency_data()
		session = client.open_session()
		node = testgrid.server.model.FakeNode()
		client.add_node(node)
		node = session.allocate_node()
		self.assertIn(node, session.get_nodes())
		secondsession = client.create_session()
		self.assertFalse(secondsession.is_available(node))

@unittest.skip("deprecated")
class RestTest(FakeTest):

	cls = testgrid.rest.Client

if __name__ == "__main__": unittest.main(verbosity = 2)
