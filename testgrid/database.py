# copyright (c) 2013-2014 smartjog, released under the GPL license.

"database helper"

import unittest, inspect, sqlite3, time, abc, sys, os

from testgrid import model, parser

class DatabaseError(Exception): pass

SCHEMA = """
create table Nodes (
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	name text not null,
	is_transient integer default 0,
	is_quarantined integer default 0,
	quarantine_reason text,
	data text not null,
	unique(modulename, typename, data)
);

create table Subnets (
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	netid text not null,
	data text not null,
	is_allocated integer default 0,
	unique(modulename, typename, data)
);

create table Users (
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	name text not null,
	data text not null,
	unique(modulename, typename, data)
);

create table Sessions (
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	name text not null,
	user_id integer not null references Users(id) on delete restrict,
	subnet_id integer references Subnets(id) on delete restrict,
	data text not null,
	unique(name)
);

create table Packages (
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	name text not null,
	version text,
	data text not null,
	unique(name, version)
);

-- a node can be allocated only once (node <1-1> package)
create table Pairs (
	id integer primary key autoincrement,
	session_id integer not null references Sessions(id) on delete cascade,
	package_id integer references Packages(id) on delete restrict,
	node_id integer not null references Nodes(id) on delete restrict,
	unique(session_id, node_id)
);
"""

class Storable(object):

	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def marshall(self):
		"convert memory representation to storage representation"
		pass

	@classmethod
	@abc.abstractmethod
	def unmarshall(cls, data):
		"convert storage representation to memory representation"
		pass

	def __eq__(self, other):
		return type(self) is type(other) and self.marshall() == other.marshall()

	def __ne__(self, other):
		return not (self == other)

class Database(object):

	def __init__(self, dbpath):
		if dbpath != ":memory:":
			self.dbpath = os.path.expanduser(dbpath)
		else:
			self.dbpath = dbpath
		if dbpath == ":memory:" or not os.path.exists(self.dbpath):
			self.con = sqlite3.connect(self.dbpath)
			self.con.executescript(SCHEMA)
		else:
			self.con = sqlite3.connect(self.dbpath)
		self.con.isolation_level = 'EXCLUSIVE'
		self.cur = self.con.cursor()
		self.cur.execute("PRAGMA foreign_keys = ON")

	def close(self, delete_storage = False):
		"close database connection, delete backend file if requested"
		if self.con:
			self.con.close()
			self.con = None
		if delete_storage and os.path.exists(self.dbpath):
			os.remove(self.dbpath)

	def __del__(self):
		self.close()

	#########
	# nodes #
	#########

	def add_node(self, node):
		self.cur.execute(
			"""
				INSERT INTO Nodes(modulename, typename, name, data)
				VALUES (?, ?, ?, ?)
			""", (
				type(node).__module__,
				type(node).__name__,
				node.name,
				node.marshall()))
		self.con.commit()
		return self.cur.lastrowid

	def remove_node(self, obj):
		self.cur.execute(
			"""
				DELETE FROM Nodes
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Nodes")
		self.con.commit()

	def _get_node_id(self, obj, force = False):
		"add node if it's not stored yet, return node id"
		self.cur.execute(
			"""
				SELECT id
				FROM Nodes
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		for id, in self.cur.fetchall():
			return id
		else:
			if force:
				return self.add_node(obj)
			else:
				raise model.NoSuchItemError(obj, "table Nodes")

	def _get_node(self, id):
		self.cur.execute(
			"""
				SELECT modulename, typename, data
				FROM Nodes WHERE id = ?
			""",
			(id,))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(id, "table Nodes")
		else:
			modulename, typename, data = row
			return parser.get_subclass(
				typename,
				model.Node,
				modulename).unmarshall(data)

	def get_nodes(self):
		self.cur.execute("SELECT modulename, typename, data FROM Nodes")
		return tuple(
			parser.get_subclass(
				typename,
				model.Node,
				modulename).unmarshall(data)
			for modulename, typename, data in self.cur.fetchall())

	def count_nodes(self):
		self.cur.execute("SELECT count(*) FROM Nodes")
		cnt, = self.cur.fetchone()
		return cnt

	def quarantine_node(self, obj, reason):
		self.cur.execute(
			"""
				UPDATE Nodes
				SET is_quarantined = 1, quarantine_reason = ?
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				"%s" % reason,
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Nodes")
		self.con.commit()

	def get_quarantine_reason(self, obj):
		self.cur.execute(
			"""
				SELECT quarantine_reason
				FROM Nodes
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(obj, "table Nodes")
		else:
			reason, = row
			return reason

	def rehabilitate_node(self, obj):
		self.cur.execute(
			"""
				UPDATE Nodes
				SET is_quarantined = 0, quarantine_reason = NULL
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Nodes")
		self.con.commit()

	def set_node_transient(self, obj):
		self.cur.execute(
			"""
				UPDATE Nodes
				SET is_transient = 1
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Nodes")
		self.con.commit()

	def is_quarantined(self, obj):
		self.cur.execute(
			"""
				SELECT is_quarantined
				FROM Nodes
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(obj, "table Nodes")
		else:
			is_quarantined, = row
			return bool(is_quarantined)

	def is_transient(self, obj):
		self.cur.execute(
			"""
				SELECT is_transient
				FROM Nodes
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(obj, "table Nodes")
		else:
			is_transient, = row
			return bool(is_transient)

	###########
	# subnets #
	###########

	def add_subnet(self, subnet):
		self.cur.execute(
			"""
				INSERT INTO Subnets(modulename, typename, netid, data)
				VALUES (?, ?, ?, ?)
			""", (
				type(subnet).__module__,
				type(subnet).__name__,
				subnet.id,
				subnet.marshall()))
		self.con.commit()
		return self.cur.lastrowid

	def remove_subnet(self, obj):
		self.cur.execute(
			"""
				DELETE FROM Subnets
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Subnets")
		self.con.commit()

	def _get_subnet_id(self, obj, force = False):
		"add subnet if it's not stored yet, return subnet id"
		self.cur.execute(
			"""
				SELECT id
				FROM Subnets
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		for id, in self.cur.fetchall():
			return id
		else:
			if force:
				return self.add_subnet(obj)
			else:
				raise model.NoSuchItemError(obj, "table Subnets")

	def _get_subnet(self, id):
		self.cur.execute(
			"""
				SELECT modulename, typename, data
				FROM Subnets WHERE id = ?
			""",
			(id,))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(id, "table Subnets")
		else:
			modulename, typename, data = row
			return parser.get_subclass(
				typename,
				model.Subnet,
				modulename).unmarshall(data)

	def get_subnets(self):
		self.cur.execute("SELECT modulename, typename, data FROM Subnets")
		return tuple(
			parser.get_subclass(
				typename,
				model.Subnet,
				modulename).unmarshall(data)
			for modulename, typename, data in self.cur.fetchall())

	def count_subnets(self):
		self.cur.execute("SELECT count(*) FROM Subnets")
		cnt, = self.cur.fetchone()
		return cnt

	def allocate_subnet(self, obj):
		self.cur.execute(
			"""
				UPDATE Subnets
				SET is_allocated = 1
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Subnets")
		self.con.commit()

	def is_subnet_allocated(self, obj):
		self.cur.execute(
			"""
				SELECT is_allocated
				FROM Subnets
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(obj, "table Subnets")
		else:
			is_transient, = row
			return bool(is_transient)

	def release_subnet(self, obj):
		self.cur.execute(
			"""
				UPDATE Subnets
				SET is_allocated = 0
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Subnets")
		self.con.commit()

	#########
	# users #
	#########

	def add_user(self, user):
		self.cur.execute(
			"""
				INSERT INTO Users(modulename, typename, name, data)
				VALUES (?, ?, ?, ?)
			""", (
				type(user).__module__,
				type(user).__name__,
				user.name,
				user.marshall()))
		self.con.commit()
		return self.cur.lastrowid

	def remove_user(self, obj):
		self.cur.execute(
			"""
				DELETE FROM Users
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Users")
		self.con.commit()

	def _get_user_id(self, obj, force = False):
		"add user if it's not stored yet, return user id"
		self.cur.execute(
			"""
				SELECT id
				FROM Users
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		for id, in self.cur.fetchall():
			return id
		else:
			if force:
				return self.add_user(obj)
			else:
				raise model.NoSuchItemError(obj, "table Users")

	def _get_user(self, id):
		self.cur.execute(
			"""
				SELECT modulename, typename, data
				FROM Users WHERE id = ?
			""",
			(id,))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(id, "table Users")
		else:
			modulename, typename, data = row
			return parser.get_subclass(
				typename,
				model.User,
				modulename).unmarshall(data)

	def get_users(self):
		self.cur.execute("SELECT modulename, typename, data FROM Users")
		return tuple(
			parser.get_subclass(
				typename,
				model.User,
				modulename).unmarshall(data)
			for modulename, typename, data in self.cur.fetchall())

	def count_users(self):
		self.cur.execute("SELECT count(*) FROM Users")
		cnt, = self.cur.fetchone()
		return cnt

	############
	# packages #
	############

	def add_package(self, package):
		self.cur.execute(
			"""
				INSERT INTO Packages(modulename, typename, name, version, data)
				VALUES (?, ?, ?, ?, ?)
			""", (
				type(package).__module__,
				type(package).__name__,
				package.name,
				package.version,
				package.marshall()))
		self.con.commit()
		return self.cur.lastrowid

	def remove_package(self, obj):
		self.cur.execute(
			"""
				DELETE FROM Packages
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Packages")
		self.con.commit()

	def _get_package_id(self, obj, force = False):
		"add package if it's not stored yet, return package id"
		self.cur.execute(
			"""
				SELECT id
				FROM Packages
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		for id, in self.cur.fetchall():
			return id
		else:
			if force:
				return self.add_package(obj)
			else:
				raise model.NoSuchItemError(obj, "table Packages")

	def _get_package(self, id):
		self.cur.execute(
			"""
				SELECT modulename, typename, data
				FROM Packages WHERE id = ?
			""",
			(id,))
		row = self.cur.fetchone()
		if not row:
			raise model.NoSuchItemError(id, "table Packages")
		else:
			modulename, typename, data = row
			return parser.get_subclass(
				typename,
				model.Package,
				modulename).unmarshall(data)

	def get_packages(self):
		self.cur.execute(
			"""
				SELECT modulename, typename, data
				FROM Packages
			""")
		return tuple(
			parser.get_subclass(
				typename,
				model.Package,
				modulename).unmarshall(data)
			for modulename, typename, data in self.cur.fetchall())

	def count_packages(self):
		self.cur.execute("SELECT count(*) FROM Packages")
		cnt, = self.cur.fetchone()
		return cnt

	#########
	# pairs #
	#########

	def _add_pair_nocommit(self, session_id, pair):
		package, node = pair
		if package is not None:
			package_id = self._get_package_id(package, force = True) # add package
		else:
			package_id = None
		node_id = self._get_node_id(node, force = True) # add node
		self.cur.execute(
			"""
				INSERT INTO Pairs(session_id, node_id, package_id)
				VALUES (?, ?, ?)
			""", (
				session_id,
				node_id,
				package_id))

	def _add_pair(self, *args, **kwargs):
		self._add_pair_nocommit(*args, **kwargs)
		self.con.commit()

	def remove_pair(self, session_id, pair):
		_, node = pair
		node_id = self._get_node_id(node)
		self.cur.execute(
			"""
				DELETE FROM Pairs
				WHERE session_id = ? AND node_id = ?
			""", (
				session_id,
				node_id))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Users")
		self.con.commit()

	def _get_pairs(self, session_id):
		self.cur.execute(
			"""
				SELECT package_id, node_id
				FROM Pairs
				WHERE session_id = ?
			""",
			(session_id,))
		pairs = []
		for package_id, node_id in self.cur.fetchall():
			if package_id is None:
				package = None
			else:
				package = self._get_package(package_id)
			pair = (package, self._get_node(node_id))
			pairs.append(pair)
		return tuple(pairs)

	def count_pairs(self):
		self.cur.execute("SELECT count(*) FROM Pairs")
		cnt, = self.cur.fetchone()
		return cnt

	def clear_pairs(self):
		self.cur.execute("DELETE FROM Pairs")
		self.con.commit()

	############
	# sessions #
	############

	def add_session(self, session):
		user_id = self._get_user_id(session.user, force = True) # add user
		if session.subnet:
			subnet_id = self._get_subnet_id(session.subnet, force = True) # add subnet
		else:
			subnet_id = None
		self.cur.execute(
			"""
				INSERT INTO Sessions(modulename, typename, name, user_id, subnet_id, data)
				VALUES (?, ?, ?, ?, ?, ?)
			""", (
				type(session).__module__,
				type(session).__name__,
				session.name,
				user_id,
				subnet_id,
				session.marshall()))
		session_id = self.cur.lastrowid
		for pair in session.plan:
			self._add_pair_nocommit(session_id, pair)
		self.con.commit()
		return session_id

	def remove_session(self, obj):
		self.cur.execute(
			"""
				DELETE FROM Sessions
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		if self.cur.rowcount < 1:
			raise model.NoSuchItemError(obj, "table Sessions")
		self.con.commit()

	def _get_session_id(self, obj, force = False):
		"add session if it's not stored yet, return session id"
		self.cur.execute(
			"""
				SELECT id
				FROM Sessions
				WHERE modulename = ? AND typename = ? AND data = ?
			""", (
				type(obj).__module__,
				type(obj).__name__,
				obj.marshall()))
		for id, in self.cur.fetchall():
			return id
		else:
			if force:
				return self.add_session(obj)
			else:
				raise model.NoSuchItemError(obj, "table Sessions")

	class Plan(object):
		"list of pairs ORM"

		def __init__(self, db, session):
			self.db = db
			self.session = session

		def __eq__(self, other):
			if isinstance(other, (tuple, list)):
				return [pair for pair in self] == [pair for pair in other]
			else:
				return self.db == other.db and self.session == other.session

		def __ne__(self, other):
			return not (self == other)

		def __getattr__(self, key):
			if key == "session_id":
				self.session_id = self.db._get_session_id(self.session)
				return self.session_id
			else:
				raise AttributeError(key)

		def __iter__(self):
			for pair in self.db._get_pairs(self.session_id):
				yield pair

		def __len__(self):
			return self.db.count_pairs()

		def append(self, pair):
			self.db._add_pair(session_id = self.session_id, pair = pair)

		def remove(self, pair):
			self.db.remove_pair(session_id = self.session_id, pair = pair)

		def __iadd__(self, other):
			for pair in other:
				self.append(pair)
			return self

		def __delitem__(self, key):
			if isinstance(key, slice):
				self.db.clear_pairs()
			else:
				raise NotImplementedError("__delitem__(idx) not available")

	def get_sessions(self, gridref = None):
		self.cur.execute(
			"""
				SELECT id, modulename, typename, user_id, subnet_id, data
				FROM Sessions
			""")
		sessions = []
		for session_id, modulename, typename, user_id, subnet_id, data in self.cur.fetchall():
			session = parser.get_subclass(
				typename,
				model.Session,
				modulename).unmarshall(data)
			session.gridref = gridref
			session.user = self._get_user(user_id)
			session.plan = self.Plan(db = self, session = session)
			if subnet_id is not None:
				session.subnet = self._get_subnet(subnet_id)
			sessions.append(session)
		return tuple(sessions)

	def count_sessions(self):
		self.cur.execute("SELECT count(*) FROM Sessions")
		cnt, = self.cur.fetchone()
		return cnt

####################
# storable objects #
####################

class StorablePackage(Storable, model.Package):

	def marshall(self):
		return "%s" % {
			"name": self.name,
			"version": self.version,
		}

	@classmethod
	def unmarshall(cls, data):
		return (cls)(**eval(data))

class StorableSubnet(Storable, model.Subnet):

	def marshall(self):
		return "%s" % {"id": self.id}

	@classmethod
	def unmarshall(cls, data):
		return (cls)(**eval(data))

class StorableNode(Storable, model.Node):

	def marshall(self):
		return "%s" % {"name": self.name}

	@classmethod
	def unmarshall(cls, data):
		return (cls)(**eval(data))

class StorableUser(Storable, model.User):

	def marshall(self):
		return "%s" % {"name": self.name}

	@classmethod
	def unmarshall(cls, data):
		return (cls)(**eval(data))

class StorableSession(Storable, model.Session):


	def marshall(self):
		return "%s" % {
			"gridref": None, # filled-in by get_sessions() and open_session()
			"name": self.name,
			"user": None, # filled-in by get_sessions() and open_session()
			"plan": None, # filled-in by get_sessions() and open_session()
			"subnet": None, # filled-in by get_sessions() and open_session()
		}

	@classmethod
	def unmarshall(cls, data):
		return (cls)(**eval(data))

	def __eq__(self, other):
		return\
			self.name == other.name\
			and self.user == other.user\
			and self.plan == other.plan\
			and self.subnet == other.subnet

#################
# tests doubles #
#################

class FakeNode(StorableNode):

	def get_hoststring(self): pass

	def get_installed_packages(self): pass

	def get_load(self): pass

	def get_subnets(self): pass

	def has_support(self, **opts): pass

	def join(self, subnet): pass

	def leave(self, subnet): pass

class FakePackage(StorablePackage):

	def install(self, node): pass

	def uninstall(self, node): pass

	def is_installed(self, node): pass

	def is_installable(self, node): pass

#########
# tests #
#########

class CrudTest(object):

	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def Object(self): pass

	@abc.abstractmethod
	def get_objects(self): pass

	@abc.abstractmethod
	def add_object(self, obj): pass

	@abc.abstractmethod
	def remove_object(self, obj): pass

	def setUp(self):
		self.db = Database(dbpath = ":memory:")

	def tearDown(self):
		self.db.close()

	def test_add_remove_object(self):
		self.assertEqual(self.count_objects(), 0)
		self.assertEqual(self.get_objects(), ())
		obj = self.Object()
		self.add_object(obj)
		self.assertEqual(self.count_objects(), 1)
		self.assertEqual(self.get_objects(), (obj,))
		self.remove_object(obj)
		self.assertEqual(self.count_objects(), 0)
		self.assertEqual(self.get_objects(), ())

	def test_add_object_twice(self):
		obj = self.Object()
		self.add_object(obj)
		self.assertRaises(Exception, self.add_object, obj)

	def test_remove_object_twice(self):
		obj = self.Object()
		self.add_object(obj)
		self.remove_object(obj)
		self.assertRaises(model.NoSuchItemError, self.remove_object, obj)

class NodeTest(CrudTest, unittest.TestCase):

	def Object(self):
		return FakeNode(name = "node")

	def get_objects(self):
		return self.db.get_nodes()

	def add_object(self, obj):
		return self.db.add_node(obj)

	def remove_object(self, obj):
		return self.db.remove_node(obj)

	def count_objects(self):
		return self.db.count_nodes()

	def test_quarantine_rehabilitate_node(self):
		node = FakeNode(name = "node")
		self.db.add_node(node = node)
		self.assertIn(node, self.db.get_nodes())
		self.assertFalse(self.db.is_quarantined(node))
		self.db.quarantine_node(node, "test")
		self.assertTrue(self.db.is_quarantined(node))
		self.assertEqual(self.db.get_quarantine_reason(node), "test")
		self.db.rehabilitate_node(node)
		self.assertFalse(self.db.is_quarantined(node))

	def test_set_transient_node(self):
		node = FakeNode(name = "node")
		self.db.add_node(node = node)
		self.assertFalse(self.db.is_transient(node))
		self.db.set_node_transient(node)
		self.assertTrue(self.db.is_transient(node))

class PackageTest(CrudTest, unittest.TestCase):

	def Object(self):
		return FakePackage(name = "package", version = "1.0")

	def get_objects(self):
		return self.db.get_packages()

	def add_object(self, obj):
		return self.db.add_package(obj)

	def remove_object(self, obj):
		return self.db.remove_package(obj)

	def count_objects(self):
		return self.db.count_packages()

class SubnetTest(CrudTest, unittest.TestCase):

	def Object(self):
		return StorableSubnet(id = "subnet")

	def get_objects(self):
		return self.db.get_subnets()

	def add_object(self, obj):
		return self.db.add_subnet(obj)

	def remove_object(self, obj):
		return self.db.remove_subnet(obj)

	def count_objects(self):
		return self.db.count_subnets()

	def test_allocate_release_subnet(self):
		sn = self.Object()
		self.add_object(sn)
		self.assertFalse(self.db.is_subnet_allocated(sn))
		self.db.allocate_subnet(sn)
		self.assertTrue(self.db.is_subnet_allocated(sn))
		self.db.release_subnet(sn)
		self.assertFalse(self.db.is_subnet_allocated(sn))

class UserTest(CrudTest, unittest.TestCase):

	def Object(self):
		return StorableUser(name = "user")

	def get_objects(self):
		return self.db.get_users()

	def add_object(self, obj):
		return self.db.add_user(obj)

	def remove_object(self, obj):
		return self.db.remove_user(obj)

	def count_objects(self):
		return self.db.count_users()

class SessionTest(CrudTest, unittest.TestCase):

	def Object(self):
		return StorableSession(
			gridref = None,
			name = "session",
			user = StorableUser("user"),
			plan = ((FakePackage("package"), FakeNode("node")),),
			subnet = StorableSubnet(id = "subnet"))

	def get_objects(self):
		return self.db.get_sessions()

	def add_object(self, obj):
		return self.db.add_session(obj)

	def remove_object(self, obj):
		return self.db.remove_session(obj)

	def count_objects(self):
		return self.db.count_sessions()

	def test_user_removal_constraint(self):
		"assert a user cannot be removed if used by a session"
		session = self.Object()
		self.db.add_session(session)
		self.assertRaises(sqlite3.IntegrityError, self.db.remove_user, session.user)
		self.db.remove_session(session)
		self.db.remove_user(session.user)

	def test_subnet_removal_constraint(self):
		"assert a subnet cannot be removed if used by a session"
		session = self.Object()
		self.db.add_session(session)
		self.assertRaises(sqlite3.IntegrityError, self.db.remove_subnet, session.subnet)
		self.db.remove_session(session)
		self.db.remove_subnet(session.subnet)

if __name__ == "__main__": unittest.main(verbosity = 2)
