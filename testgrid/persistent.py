import unittest
#import testgrid
import database
import model
import inspect
import os
import shutil

class persistentSession(model.Session):
	def __init__(self, hdl , gridref, username, name = None, subnet = None):
		self.hdl = hdl
		self.gridref = gridref
		super(persistentSession, self).__init__(gridref, username, name, subnet)

	def __iter__(self):
		self.plan = self.hdl.get_plans(self)
		for _, node in self.plan:
			yield node

	def allocate_node(self, pkg = None, **opts):
		node = super(persistentSession, self).allocate_node(pkg, **opts)
		self.hdl.add_plan(self, (None, node))
		return node

	def _release_pair(self, pkg ,node):
		#super(persistentSession, self)._release_pair(pkg ,node)
		self.hdl.remove_plan(self, (node, pkg))

	def deploy(self, packages):
		plan = super(persistentSession, self).deploy(packages)
		self.hdl.add_plan(self, plan)
	
	def __del__(self):
		if self.is_anonymous:
			self.close()

	def close(self):
		self.hdl.close_session(self)
		self.gridref._close_session()
		#super(persistentSession, self).close()

class Grid(model.Grid):
        def __init__(self, name, databasepath="testgrid.db", scriptSqlPath="testgrid/testgrid.sql", *args, **kwargs):
		super(Grid, self).__init__(name, *args, **kwargs)
		self.hdl = database.Database(databasePath=databasepath, scriptSqlPath=scriptSqlPath)
		self.nodes = self.hdl.get_nodes()
		self.sessions = self.get_sessions()

        def add_node(self, node):
		self.nodes = self.hdl.get_nodes()
		super(Grid, self).add_node(node)
		self.hdl.add_node(node)
		

        def remove_node(self, node):
		super(Grid, self).remove_node(node)
		self.hdl.remove_node(node)

        def quarantine_node(self, node, exc):
		super(Grid, self).quarantine_node(node, exc)
		self.hdl.quarantine_node(node, exc)

        def rehabilitate_node(self, node):
		super(Grid, self).rehabilitate_node(node)
		self.hdl.rehabilitate_node(node)

	def is_quarantined(self, node):
		if hasattr(node, "is_quarantined"):
			self.hdl.is_quarantined(node)
		super(Grid, self).is_quarantined(node)
	
	def is_transient(self, node):
		if hasattr(node, "is_transient"):
			self.hdl.is_transient(node)
		super(Grid, self).is_transient(node)

        def _get_allocated_nodes(self):
		self.sessions = self.get_sessions()
		for session in self.sessions:
			for node in session:
				yield node

        def _get_available_nodes(self):
		self.nodes = self.hdl.get_nodes()
		for node in self.nodes:
			if not self.is_quarantined(node) and not node in self._get_allocated_nodes():
				yield node
			
        
        
	def get_sessions(self):
		return self.hdl.get_sessions(persistentSession, self)

	def open_session(self, username = None, name = None):
		self.sessions = self.get_sessions()
		username = username or getpass.getuser()
		for session in self.sessions:
			if session.name == name:
				assert session.username == username, "%s: access violation" % name
				break
		else:
			session = persistentSession(hdl = self.hdl,
						    gridref = self,
						    username = username,
						    name = name,
						    subnet = self._allocate_subnet())
			self.hdl.open_session(session)
			self.sessions.append(session)	
		return session

	def _close_session(self):
		self.sessions = self.get_sessions()

	def close_database(self):
		self.hdl.close()

	def remove_database(self):
		os.remove(self.hdl.dbPath)
##############
# unit tests #
##############

class SelfTest(unittest.TestCase):
	def setUp(self):
		if not os.path.exists("db_test"):
			os.mkdir("db_test")
		
	def tearDown(self):
		shutil.rmtree("db_test/")
		

	def test_persistent_nodes(self):
		pg = Grid(name="persistentGrid", databasepath="db_test/persistentNodes.db")
		node = model.FakeNode("fake node")
		pg.add_node(node)
		self.assertEqual(len(pg.nodes), 1)
		pg.close_database()
		secondpg = Grid(name=" persistentGridsecond", databasepath="db_test/persistentNodes.db")
		self.assertEqual(len(secondpg.nodes), 1)
	    #secondpg.remove_node(node)
	    #self.assertEqual(len(secondpg.nodes), 0)
		secondpg.close_database()
		#secondpg.remove_database()

	def test_persistent_sessions(self):
		pg = Grid(name=" persistentGrid", databasepath="db_test/persistentSessions.db")
		session = pg.open_session("persistent", "test")
		anonymous_session = pg.open_session("persistent_anonymous")
		sessions = pg.get_sessions()
		self.assertEqual(len(sessions), 2)
		anonymous_session.close()
		secondpg = Grid(name="persistentGridsecond", databasepath="db_test/persistentSessions.db")
		sessions = secondpg.get_sessions()
		self.assertEqual(len(sessions), 1)

	def test_persistent_plan(self):
		pg = Grid(name=" persistentGrid", databasepath="db_test/persistentPlan.db")
		node = model.FakeNode("fake node")
		pg.add_node(node)
		session = pg.open_session("persistent", "test")
		allocated_node = session.allocate_node()
		self.assertRaises(model.NodePoolExhaustedError,session.allocate_node)
		pg.close_database()
		pg2 = Grid(name=" persistentGrid", databasepath="db_test/persistentPlan.db")
		session2 = pg2.open_session("persistent2", "test2")
		self.assertRaises(model.NodePoolExhaustedError, session2.allocate_node)
		node2 = model.FakeNode("fake node")
		pg2.close_database()
		pg2.remove_database()

if __name__  == "__main__": unittest.main(verbosity = 2)
