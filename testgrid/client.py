# copyright (c) 2013-2014 smartjog, released under the GPL license.

import unittest, getpass, abc

from testgrid import model, parser

class UnknownSessionError(Exception):

	def __init__(self, name):
		super(UnknownSessionError, self).__init__("%s: no such session" % name)

class UnknownNodeError(Exception):

	def __init__(self, name):
		super(UnknownNodeError, self).__init__("%s: no such node" % name)

class User(model.User):

	def marshall(self):
		return "%s" % {"name": self.name}

	@classmethod
	def unmarshall(cls, data):
		return (cls)(**eval(data))

def get_current_user():
	return User(name = getpass.getuser())

class AccessManager(object):

	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def is_administrator(self, user): pass

def restricted(f):
	"decorator -- grant function access to administrator only"
	def restricted_f(self, *args, **kwargs):
		if self.accessmgr.is_administrator(self.user):
			return f(self, *args, **kwargs)
		else:
			raise model.AccessViolation(
				user = self.user,
				resource = f)
	return restricted_f

import testgrid, unittest, getpass, jinja2, os, stat


class Client(object):
	"provide an access-controlled interface to sessions and grid"

	def __init__(self, grid, accessmgr, user = None):
		self.grid = grid
		self.accessmgr = accessmgr
		self.user = user or get_current_user()

	def get_nodes(self):
		"return all nodes if user is admin, return user's nodes otherwise"
		if self.accessmgr.is_administrator(self.user):
			for node in self.grid:
                                print node
				yield node
		else:
			for session in self.grid.sessions:
				if session.user == self.user:
					for node in session:
						yield node

	def get_node(self, name):
		"""
		Return named node or raise UnknownNodeError.
		If user is not admin, fails if the node is not in any user's session.
		"""
		for node in self.get_nodes():
                        print node.name
			if node.name == name:
				return node
		raise UnknownNodeError(name)

	def get_package(self, typename, name, version = None):
		"instanciate and return specified package"
		cls = parser.get_subclass(typename, model.Package)
		if version is None:
			pkg_name, _, pkg_version = name.partition("=")
			if pkg_version is "":
				version = pkg_version
		return cls(name = pkg_name, version = version)

	@restricted
	def add_node(self, name, ini):
		"from manifest, instanciate and add node to grid, return instance"
		node = parser.parse_node(name, ini = ini)
		self.grid.add_node(node)
		return node

	@restricted
	def remove_node(self, name):
		"instanciate and remove node from grid, return instance"
		node = self.get_node(name)
		self.grid.remove_node(node)
		return node

	def is_available(self, node):
		"return True if the node is available"
		return self.grid.is_available(node)

	def is_allocated(self, node):
		"return True if the node is allocated"
		return self.grid.is_allocated(node)

	def is_quarantined(self, node):
		"return True if the node is quarantined"
 		return self.grid.is_quarantined(node)

	@restricted
	def quarantine_node(self, name, reason):
		"push node into quarantine"
		node = self.get_node(name)
		self.grid.quarantine_node(node, reason)

	@restricted
	def rehabilitate_node(self, name):
		"pull node from quarantine"
		node = self.get_node(name)
		self.grid.rehabilitate_node(node)

	def get_sessions(self):
		"return all sessions if user is admin, return user's sessions otherwise"
		for session in self.grid.sessions:
			if self.accessmgr.is_administrator(self.user):
				yield session
			else:
				if session.user == self.user:
					yield session


	def get_node_session(self, node):
		"return session that contains a specific node"
		return self.grid._get_node_session(node)


	def get_session(self, name):
		"""
		Return named session or raise UnknownSessionError.
		If user is not admin, fails if it's not user's.
		"""
		for session in self.get_sessions():
			if session.name == name:
				return session
		raise UnknownSessionError(name)

	def open_session(self, name):
		return self.grid.open_session(name = name, user = self.user)

	def close_session(self, name):
		session = self.get_session(name)
		session.close()

#########
# tests #
#########

class DenyAll(AccessManager):

	def is_administrator(self, user):
		return False

class AllowUser(AccessManager):


	def __init__(self, user):
		self.admin = user

	def is_administrator(self, user):
		return self.admin == user

class SelfTest(unittest.TestCase):

	client_cls = Client

	def mkenv(self, nb_users, nb_nodes):
		grid = model.FakeGenerativeGrid(name = "grid")
		admin = User("admin")
		accessmgr = AllowUser(admin)
		admin_client = (self.client_cls)(
			grid = grid,
			accessmgr = accessmgr,
			user = admin)
		users = []
		clients = []
		sessions = []
		nodes = []
		for i in xrange(nb_users):
			user = User("user%i" % i)
			users.append(user)
			client = (self.client_cls)(
				grid = grid,
				accessmgr = accessmgr,
				user = user)
			clients.append(client)
			session = client.open_session("user%i_session" % i)
			sessions.append(session)
			for j in xrange(nb_nodes):
				nodes.append(session.allocate_node())
		return (admin_client, clients, sessions, nodes)

	def test_get_nodes(self):
		admin_client, clients, sessions, nodes = self.mkenv(10, 10)
		# admin get all nodes:
		self.assertEqual(
			set(n for n in admin_client.get_nodes()),
			set(nodes))
		# user get its nodes:
		for client in clients:
			self.assertEqual(
				set(n for n in client.get_nodes()),
				set(n for n in sessions[clients.index(client)]))

	def test_get_node(self):
		_, clients, sessions, nodes = self.mkenv(10, 10)
		for client in clients:
			for node in nodes:
                                print node.name
				# if node is user's, it can get it:
				if node in sessions[clients.index(client)]:
					self.assertEqual(node, client.get_node(node.name))
				# otherwise UnknownNodeError is raised:
				else:
					self.assertRaises(UnknownNodeError, client.get_node, node.name)

	def test_get_sessions(self):
		admin_client, clients, sessions, nodes = self.mkenv(10, 10)
		# admin get all sessions:
		self.assertEqual(
			set(s for s in admin_client.get_sessions()),
			set(sessions))
		# user get its sessions:
		for client in clients:
			expected, = client.get_sessions()
			actual = sessions[clients.index(client)]
			self.assertEqual(expected, actual)

	def test_get_session(self):
		_, clients, sessions, _ = self.mkenv(10, 10)
		for client in clients:
			for session in sessions:
				# if session is user's, it can get it:
				if session == sessions[clients.index(client)]:
					self.assertEqual(session, client.get_session(session.name))
				# otherwise UnknownSessionError is raised:
				else:
					self.assertRaises(UnknownSessionError, client.get_session, session.name)

	def test_restricted(self):
		grid = model.Grid(name = "grid")
		client = (self.client_cls)(
			grid = grid,
			accessmgr = DenyAll())
		self.assertRaises(model.AccessViolation, client.add_node, "", "")
		self.assertRaises(model.AccessViolation, client.remove_node, "")
		self.assertRaises(model.AccessViolation, client.quarantine_node, "", "")
		self.assertRaises(model.AccessViolation, client.rehabilitate_node, "")

if __name__ == "__main__": unittest.main(verbosity = 2)
