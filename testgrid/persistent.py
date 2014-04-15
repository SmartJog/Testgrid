# copyright (c) 2013-2014 smartjog, released under the GPL license.
import unittest
import testgrid
import database
import inspect
import os
import shutil

"persistent grid implementation"

class Session(testgrid.model.Session):
	def __init__(self, hdl , gridref, username, name = None, subnet = None):
		self.hdl = hdl
		self.gridref = gridref
		super(Session, self).__init__(gridref, username, name, subnet)

	def __iter__(self):
		self.plan = self.hdl.get_plans(self)
		for _, node in self.plan:
			yield node

	def allocate_node(self, pkg = None, **opts):
		node = super(Session, self).allocate_node(pkg, **opts)
		self.hdl.add_plan(self, (None, node))
		return node

	def _release_pair(self, pkg ,node):
		super(persistentSession, self)._release_pair(pkg ,node)
		self.hdl.remove_plan(self, (node, pkg))

	def deploy(self, packages):
		plan = super(Session, self).deploy(packages)
		self.hdl.add_plan(self, plan)

	def remove_node(self, node):
		self.hdl.remove_plan(self, node)
		for p in self.plan:
			pkg, n = p
			if n.id == node.id:
				self.plan.remove(p)
	def __del__(self):
		if self.is_anonymous:
			self.close()

	def close(self):
		self.hdl.close_session(self)
		self.gridref._close_session()
		#FIXME
		#super(persistentSession, self).close()

class Grid(testgrid.model.Grid):
        def __init__(self, name, dbpath="testgrid.db", 
		     script_path="testgrid/testgrid.sql", *args, **kwargs):
		super(Grid, self).__init__(name, *args, **kwargs)
		self.hdl = database.Database(dbpath=dbpath, script_path=script_path)
		if (self.nodes):
			for node in self.nodes:
				self.add_node(node)

		self.nodes = self.hdl.get_nodes()
		self.sessions = self.get_sessions()
		
        def add_node(self, node):
		self.nodes = self.hdl.get_nodes()
		super(Grid, self).add_node(node)
		self.hdl.add_node(node)

        def remove_node(self, node):
		self.nodes = self.hdl.get_nodes()
		for n in self.nodes:
			if n.id == node.id:
				for session in self.sessions:
					for session_node in session:
						if session_node.id == node.id:
							session.remove_node(node)
				self.nodes.remove(n)
				self.hdl.remove_node(node)
				return
		raise testgrid.model.UnknownNodeError("%s" % node)
		

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
			
	def is_available(self, node):
		available_nodes = self._get_available_nodes()
		for n in available_nodes:
			if int(node.id) == int(n.id):
				return node

        def is_allocated(self, node):
		for n in _get_allocated_node:
			if int(node.id) == int(n.id):
				return node

	def get_sessions(self):
		return self.hdl.get_sessions(Session, self)

	def open_session(self, username = None, name = None):
		self.sessions = self.get_sessions()
		username = username or getpass.getuser()
		for session in self.sessions:
			if session.name == name:
				assert session.username == username, "%s: access violation" % name
				break
		else:
			session = Session(hdl = self.hdl,
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
		os.remove(self.hdl.dbpath)
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
		"test add , remove node persistency"
		#perform operation with first grid
		pg = Grid(name="persistentGrid", dbpath="db_test/persistentNodes.db")
		node = testgrid.model.FakeNode("fake node")
		pg.add_node(node)
		node2 = testgrid.model.FakeNode("fake node")
		pg.add_node(node2)
		self.assertEqual(len(pg.nodes), 2)
		pg.remove_node(node2)
		self.assertEqual(len(pg.nodes), 1)
		pg.close_database()
		#perform operation with second  grid using same db
		secondpg = Grid(name=" persistentGridsecond", dbpath="db_test/persistentNodes.db")
		self.assertEqual(len(secondpg.nodes), 1)
		self.assertRaises(testgrid.model.UnknownNodeError, secondpg.remove_node, node2)
		secondpg.close_database()

	def test_persistent_sessions(self):
		"test persistent session persistency, assert anonymous session is removed after being closed"
		#perform operation with first grid
		pg = Grid(name=" persistentGrid", dbpath="db_test/persistentSessions.db")
		session = pg.open_session("persistent", "test")
		anonymous_session = pg.open_session("anonymous")
		sessions = pg.get_sessions()
		self.assertEqual(len(sessions), 2)
		anonymous_session.close()
		#perform operation with second  grid using same db
		secondpg = Grid(name="persistentGridsecond", dbpath="db_test/persistentSessions.db")
		sessions = secondpg.get_sessions()
		self.assertEqual(len(sessions), 1)

	def test_persistent_plan(self):
		"test plan persistency associate to specific session"
		#perform operation with first grid
		pg = Grid(name=" persistentGrid", dbpath="db_test/persistentPlan.db")
		node = testgrid.model.FakeNode("fake node")
		pg.add_node(node)
		session = pg.open_session("persistent", "test")
		allocated_node = session.allocate_node()
		self.assertRaises(testgrid.model.NodePoolExhaustedError,session.allocate_node)
		pg.close_database()
		#perform operation with second  grid using same db
		pg2 = Grid(name=" persistentGrid", dbpath="db_test/persistentPlan.db")
		session2 = pg2.open_session("persistent2", "test2")
		self.assertRaises(testgrid.model.NodePoolExhaustedError, session2.allocate_node)
		pg2.remove_node(allocated_node)
		pg2.close_database()
		#check remove node persistency
		pg = Grid(name=" persistentGrid", dbpath="db_test/persistentPlan.db")
		self.assertEqual(len(pg.nodes), 0)
		session = pg.open_session("persistent", "test")
		self.assertEqual(len(session.plan), 0)
		
		

if __name__  == "__main__": unittest.main(verbosity = 2)
