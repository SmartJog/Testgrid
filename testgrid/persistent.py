# copyright (c) 2013-2014 smartjog, released under the GPL license.

"persistent grid, store data in sqlite file"

import unittest
import testgrid
import database
import inspect
import os
import shutil

class Session(testgrid.model.Session):

	def __init__(self, hdl, gridref, username, name = None, subnet = None):
		super(Session, self).__init__(gridref, username, name, subnet)
		self.hdl = hdl
		#self.hdl.add_session(self)

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
		#join subnet fix
		plan = super(Session, self).deploy(packages)
		self.hdl.add_plan(self, plan)
		return plan

	def remove_node(self, node):
		self.hdl.remove_plan(self, node)
		for p in self.plan:
			pkg, n = p
			if n.id == node.id:
				self.plan.remove(p)

	def close(self):
		super(persistentSession, self).close()
		self.hdl.remove_session(self)

class Nodes(object):

	def __init__(self, hdl):
		self.hdl = hdl

	def __iter__(self):
		for node in self.hdl.get_nodes():
			yield node

	def __contains__(self, node):
		for n in self:
			if n.id == node.id:
				return True
		return False

	def append(self, node):
		self.hdl.add_node(node)

	def remove(self, node):
		self.hdl.remove(node)

class Subnets(object):

	def __init__(self, hdl):
		self.hdl = hdl

	def __iter__(self):
		for subnet in self.hdl.get_subnets():
			yield subnet

	def __contains__(self, session):
		for s in self:
			if s.id == session.id:
				return True
		return False

	def append(self, subnet):
		self.hdl.add_subnet(subnet)

	def remove(self, subnet):
		self.hdl.remove_subnet(subnet)

class Sessions(object):

	def __init__(self, hdl):
		self.hdl = hdl

	def __iter__(self):
		for session in self.hdl.get_sessions():
			yield session

	def __contains__(self, session):
		for s in self:
			if s.id == session.id:
				return True
		return False

	def append(self, session):
		self.hdl.add_session(session)

	def remove(self, session):
		self.hdl.remove_session(session)

class Grid(testgrid.model.Grid):

        def __init__(self, name, dbpath="testgrid.db",
		     script_path="testgrid/testgrid.sql", *args, **kwargs):
		super(Grid, self).__init__(name, *args, **kwargs)
                if (self.nodes):
			for node in self.nodes:
				self.add_node(node)
                #add subnet
		self.hdl = database.Database(dbpath = dbpath, script_path = script_path)
		self.nodes = Nodes(hdl = self.hdl)
		self.subnets = Subnets(hdl = self.hdl)
		self.sessions = Sessions(hdl = self.hdl)
		

        def __add_node(self, node):
		self.nodes = self.hdl.get_nodes()
		super(Grid, self).add_node(node)
		self.hdl.add_node(node)

        def __remove_node(self, node):
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
		self.hdl.quarantine_node(node, exc)

        def rehabilitate_node(self, node):
		self.hdl.rehabilitate_node(node)

	def is_quarantined(self, node):
		return self.hdl.is_quarantined(node)

	def is_transient(self, node):
		return self.hdl.is_transient(node)

	def open_session(self, username = None, name = None):
		session = super(Grid, self).open_session(
			username = username,
			name = name,
			session_cls = Session,
			hdl = self.hdl)
		self.hdl.add_session(session)
		return session

	def __del__(self):
		self.hdl.close()

##############
# unit tests #
##############

class SelfTest(unittest.TestCase):

	timeout = 2
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
		del pg
		#perform operation with second  grid using same db
		pg = Grid(name="persistentGridsecond", dbpath="db_test/persistentNodes.db")
		self.assertEqual(len(pg.nodes), 1)
		self.assertRaises(testgrid.model.UnknownNodeError, pg.remove_node, node2)
		#pg.remove_database()
		del pg

	def test_persistent_sessions(self):
		"test persistent session persistency, assert anonymous session is removed after being closed"
		#perform operation with first grid
		pg = Grid(name="persistentGrid", dbpath="db_test/persistentSessions.db")
		session = pg.open_session("persistent", "test")
		anonymous_session = pg.open_session("anonymous")
		sessions = pg.get_sessions()
		self.assertEqual(len(sessions), 2)
		anonymous_session.close()
		del pg
		#perform operation with second  grid using same db
		pg = Grid(name="persistentGridsecond", dbpath="db_test/persistentSessions.db")
		sessions = pg.get_sessions()
		self.assertEqual(len(sessions), 1)
		del pg

	def test_persistent_plan(self):
		"test plan persistency associate to specific session"
		#perform operation with first grid
		pg = Grid(name=" persistentGrid", dbpath="db_test/persistentPlan.db")
		node = testgrid.model.FakeNode("fake node")
		pg.add_node(node)
		session = pg.open_session("persistent", "test")
		allocated_node = session.allocate_node()
		self.assertRaises(testgrid.model.NodePoolExhaustedError,session.allocate_node)
		del pg
		#perform operation with second  grid using same db
		pg = Grid(name=" persistentGrid", dbpath="db_test/persistentPlan.db")
		session = pg.open_session("persistent2", "test2")
		self.assertRaises(testgrid.model.NodePoolExhaustedError, session.allocate_node)
		pg.remove_node(allocated_node)
		del pg
		#check remove node persistency
		pg = Grid(name=" persistentGrid", dbpath="db_test/persistentPlan.db")
		self.assertEqual(len(pg.nodes), 0)
		session = pg.open_session("persistent", "test")
		self.assertEqual(len(session.plan), 0)
		del pg

if __name__  == "__main__": unittest.main(verbosity = 2)

