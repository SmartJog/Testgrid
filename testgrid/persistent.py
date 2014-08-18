#copyright (c) 2014 arkena, released under the GPL license.

"persistent grid implementation"

import unittest, weakref, inspect, random, shutil, string, time, os

from testgrid import model, database

class Nodes(object):
	"list of nodes ORM"

	def __init__(self, db):
		self.db = db

	def __iter__(self):
		for node in self.db.get_nodes():
			yield node

	def __contains__(self, node):
		try:
			self.db._get_node_id(node, force = False)
			return True
		except:
			return False

	def __len__(self):
		return self.db.count_nodes()

	def append(self, node):
		self.db.add_node(node)

	def remove(self, node):
		self.db.remove_node(node)

class Subnets(object):
	"list of subnets ORM"

	def __init__(self, db):
		self.db = db

	def __iter__(self):
		for subnet in self.db.get_subnets():
			yield subnet

	def __contains__(self, subnet):
		try:
			self.db._get_subnet_id(subnet, force = False)
			return True
		except:
			return False

	def __len__(self):
		return self.db.count_subnets()

	def append(self, subnet):
		self.db.add_subnet(subnet)

	def remove(self, subnet):
		self.db.remove_subnet(subnet)

class Sessions(object):
	"list of sessions ORM"

	def __init__(self, db, gridref):
		self.db = db
		self.gridref = gridref

	def __iter__(self):
		for session in self.db.get_sessions(self.gridref):
			yield session

	def __contains__(self, session):
		try:
			self.db._get_session_id(session, force = False)
			return True
		except:
			return False

	def __len__(self):
		return self.db.count_sessions()

	def append(self, session):
		self.db.add_session(session)

	def remove(self, session):
		self.db.remove_session(session)

class Grid(model.Grid):

	def __init__(self, name, dbpath = "~/testgrid.db"):
		self.db = database.Database(dbpath = dbpath)
		super(Grid, self).__init__(
			name = name,
			nodes = Nodes(db = self.db),
			subnets = Subnets(db = self.db),
			sessions = Sessions(db = self.db, gridref = weakref.ref(self)))

	def quarantine(self, node, reason):
		super(Grid, self).quarantine(node = node, reason = reason)
		self.db.quarantine_node(obj =  node, reason = reason)

	def rehabilitate(self, node):
		super(Grid, self).rehabilitate(node)
		self.db.rehabilitate_node(node)

	def is_quarantined(self, node):
		return self.db.is_quarantined(node)

	def get_quarantine_reason(self, node):
		return self.db.get_quarantine_reason(node)

	def _set_transient(self, node):
		self.db.set_node_transient(node)

	def _is_transient(self, node):
		return self.db.is_transient(node)

	def open_session(self, name, user):
		session = super(Grid, self).open_session(
			name = name,
			user = user,
			session_cls = database.StorableSession)
		session.plan = database.Database.Plan(db = self.db, session = session)
		return session

	def __del__(self):
		self.db.close()

	def reset(self):
		super(Grid, self).reset()

################
# test doubles #
################

disk = {}

class FakePackage(model.FakePackage, database.StorablePackage): pass

class FakeNode(model.FakeNode, database.StorableNode):

	def __init__(self, name, key = None):
		if key is None:
			self.key = "%s-%s" % (name, time.strftime("%Y%m%d%H%M%S", time.localtime()))
			disk[self.key] = {}
			super(FakeNode, self).__init__(name)
		else:
			self.key = key
			model.Node.__init__(self, name = name)

	@property
	def terminated(self):
		return disk[self.key]["terminated"]

	@terminated.setter
	def terminated(self, value):
		disk[self.key]["terminated"] = value

	@property
	def installed(self):
		return disk[self.key]["installed"]

	@installed.setter
	def installed(self, value):
		disk[self.key]["installed"] = value

	@property
	def subnets(self):
		return disk[self.key]["subnets"]

	@subnets.setter
	def subnets(self, value):
		disk[self.key]["subnets"] = value

	def marshall(self):
		return "%s" % {
			"name": self.name,
			"key": self.key,
		}

class TempGrid(Grid):

	def __init__(self, name, nodes = None, subnets = None, sessions = None):
		dbpath = "/tmp/%s.db" % time.strftime("%Y%m%d%H%M%S", time.localtime())
		super(TempGrid, self).__init__(name = name, dbpath = dbpath)
		if nodes:
			for node in nodes:
			   self.nodes.append(node)
		if subnets:
			for subnet in subnets:
			   self.subnets.append(subnet)

	def __del__(self):
		self.db.close(delete_storage = True)

class FakeTempGrid(TempGrid):
	"generative grid of fake nodes"

	ref = 0

	def _create_node(self, **opts):
		node = FakeNode("tnode%i" % FakeTempGrid.ref)
		FakeTempGrid.ref += 1
		return node

	def _terminate(self, node):
		node.terminate()

#########
# tests #
#########

class SelfTest(model.SelfTest):

	def test_FakeNode(self):
		node1 = FakeNode("node1")
		subnet = database.StorableSubnet("subnet")
		node1.join(subnet)
		self.assertIn(subnet, node1.get_subnets())
		node2 = FakeNode("node2", key = node1.key)
		self.assertIn(subnet, node2.get_subnets())

	cls = {
		"generative_grid": FakeTempGrid,
		"package": FakePackage,
		"subnet": database.StorableSubnet,
		"user": database.StorableUser,
		"node": FakeNode,
		"grid": TempGrid,
	}

	def test_node_persistency(self):
		grid1 = TempGrid("grid1")
		node = FakeNode("node")
		grid1.add_node(node)
		self.assertIn(node, grid1)
		grid2 = Grid(name = "grid", dbpath = grid1.db.dbpath)
		self.assertIn(node, grid2)

	def test_subnet_persistency(self):
		grid1 = TempGrid("grid1")
		subnet = database.StorableSubnet("subnet")
		grid1.add_subnet(subnet)
		self.assertIn(subnet, grid1.subnets)
		grid2 = Grid(name = "grid2", dbpath = grid1.db.dbpath)
		self.assertIn(subnet, grid2.subnets)

	def test_session_persistency(self):
		grid1 = TempGrid("grid1")
		user = database.StorableUser("user")
		session = grid1.open_session(name = "session", user = user)
		self.assertIn(session, grid1.sessions)
		grid2 = Grid(name = "grid", dbpath = grid1.db.dbpath)
		self.assertIn(session, grid2.sessions)

if __name__  == "__main__": unittest.main(verbosity = 2)
