# copyright (c) 2013-2014 smartjog, released under the GPL license.

"Ansible-based Programmable Test Environments - PTE - management framework"

import ansible.inventory, ansible.runner, subprocess, unittest, weakref, time, abc

class UnreachableHostError(Exception):

	def __init__(self, host):
		super(UnreachableHostError, self).__init__("%s: host unreachable" % host)

class OperationError(Exception):

	def __init__(self, operation, target, *args):
		super(OperationError, self).__init__("@%s, %s: operation failed with %s" % (
			target,
			op,
			" ".join("%s" % arg for arg in args) if args else "no details"))

def ansible_run(hoststring, modname, modargs, sudo = False):
	"execute ansible module with specified arguments"
	res = ansible.runner.Runner(
		inventory = ansible.inventory.Inventory("%s," % hoststring),
		module_name = modname,
		module_args = modargs,
		sudo = sudo,
		forks = 0).run()
	if not hoststring in res["contacted"]:
		raise UnreachableHostError(hoststring)
	res = res["contacted"][hoststring]
	if "failed" in res:
		raise OperationError(modname, hoststring, res["msg"])
	return res

def local_run(argv, warn_only = False):
	"execute local command"
	sp = subprocess.Popen(
		args = argv,
		shell = isinstance(argv, str), # use shell if $argv is a string
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = sp.communicate()
	code = sp.returncode
	if code and not warn_only:
		raise OperationError(argv, "localhost", code, stderr.strip())
	return (code, stdout, stderr)

class Package(object):
	"a package abstracts anything installable on & removable from a node"

	__metaclass__ = abc.ABCMeta

	def __init__(self, name, version = None):
		self.name = name
		self.version = version

	def __str__(self):
		return "%s%s" % (self.name, ("-%s" % self.version) if self.version else "")

	def __eq__(self, other):
		return self.name == other.name and self.version == other.version

	def __ne__(self, other):
		return not (self == other)

	@abc.abstractmethod
	def install(self, node):
		"install package on $node, raise exception on error"
		pass

	@abc.abstractmethod
	def uninstall(self, node):
		"uninstall package from $node, raise exception on error"
		pass

	@abc.abstractmethod
	def is_installed(self, node):
		"return True if the package is installed on $node, False otherwise"
		pass

	@abc.abstractmethod
	def is_installable(self, node):
		"return True if the package is installable on $node, False otherwise"
		pass

class Service(object):
	"a service abstracts anything startable & stoppable on a node"

	__metaclass__ = abc.ABCMeta

	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

	def __eq__(self, other):
		return self.name == other.name

	def __ne__(self, other):
		return not (self == other)

	def _run(self, node, state):
		return ansible_run(
			hoststring = node.get_hoststring(),
			modname = "service",
			modargs = "name=%s state=%s" % (self.name, state))

	def start(self, node):
		return self._run(node, state = "started")

	def stop(self, hoststring):
		return self._run(node, state = "stopped")

	def restart(self, hoststring):
		return self._run(node, state = "restarted")

	def reload(self, hoststring):
		return self._run(node, state = "reloaded")

	@abc.abstractmethod
	def is_started(self, node): pass

	@abc.abstractmethod
	def get_version(self, node): pass

class Subnet(object):

	def __init__(self, id):
		self.id = id

	def __eq__(self, other):
		return self.id == other.id

	def __ne__(self, other):
		return not (self == other)

	def __contains__(self, node):
		return any(subnet == self for subnet in node.get_subnets())

class Hoststring(str):

	def split(self):
		if "@" in self:
			userpass, hostport = super(Hoststring, self).split("@")
		else:
			userpass, hostport = (None, "%s" % self)
		if ":" in userpass:
			username, password = userpass.split(":")
		else:
			username, password = (userpass, None)
		if ":" in hostport:
			hostname, port = hostport.split(":")
		else:
			hostname, port = (hostport, None)
		return (username, password, hostname, port)

class Node(object):
	"a node abstracts any object supporting packages & services"

	__metaclass__ = abc.ABCMeta

	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

	def get_info(self):
		return "no details"

	@abc.abstractmethod
	def has_support(self, **opts):
		"return True if all specified options are supported"
		pass

	@abc.abstractmethod
	def get_load(self):
		"return a float as a composition of load measures"
		pass

	@abc.abstractmethod
	def join(self, subnet):
		"setup a network interface on the specified subnet"
		pass

	@abc.abstractmethod
	def leave(self, subnet):
		"remove the network interface on the specified subnet"
		pass

	@abc.abstractmethod
	def get_subnets(self):
		"return the list of subnets the node belongs to"
		pass

	@abc.abstractmethod
	def get_hoststring(self):
		"return node hoststring as [user[:pass]@]hostname[:port]"
		pass

	# clean but too slow on unreachable nodes and no timeout parameter...
	def _disabled_is_up(self):
		"return True if the node is reachable, False otherwise"
		hoststring = self.get_hoststring()
		res = ansible.runner.Runner(
			inventory = ansible.inventory.Inventory("%s," % hoststring),
			module_name = "ping",
			forks = 0,
		).run()
		return hoststring in res["contacted"]

	# poorman replacement for the above routine
	def is_up(self):
		"return True if the node is reachable, False otherwise"
		username, password, hostname, port = self.get_hoststring().split()
		code, stdout, stderr = local_run("ping -t 1 -c 1 %s" % hostname, warn_only = True)
		return code == 0

	def start(self, service):
		return service.start(node = self)

	def stop(self, service):
		return service.stop(node = self)

	def restart(self, service):
		return service.restart(node = self)

	def reload(self, service):
		return service.reload(node = self)

	def install(self, package):
		return package.install(node = self)

	def uninstall(self, package):
		return package.uninstall(node = self)

	def is_installed(self, package):
		return package.is_installed(node = self)

	def is_installable(self, package):
		return package.is_installable(node = self)

	@abc.abstractmethod
	def get_installed_packages(self): pass

	def execute(self, args):
		"execute args, return tuple (code, stdout, stderr)"
		hoststring = self.get_hoststring()
		res = ansible_run(
			hoststring = hoststring,
			modname = "command",
			modargs = args)
		return (res["rc"], res["stdout"], res["stderr"])

class SessionNotEmptyError(Exception):

	def __init__(self, session):
		super(SessionNotEmptyError, self).__init__("%s: session not empty" % session)

class NoSuchItemError(Exception):

	def __init__(self, item, container):
		super(NoSuchItemError, self).__init__("%s: no such %s in %s" % (
			item,
			type(item).__name__.lower(),
			container))

class User(object):

	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

	def __eq__(self, other):
		if self.name == other.name:
			return True
		return False

class Session(object):
	"""
	A session holds a deployment plan and an associated subnet.
	As long as a session is not terminated, it can be re-opened through the grid.
	"""

	def __init__(self, gridref, name, user, plan = None, subnet = None):
		self.gridref = gridref
		self.name = name
		self.user = user
		self.plan = plan if plan is not None else [] # list of pairs (package, node)
		self.subnet = subnet # optional, maybe None

	def __str__(self):
		return self.name

	def __iter__(self):
		for _, node in self.plan:
			yield node

	def __len__(self):
		return len(self.plan)

	def allocate_node(self, pkg = None, **opts):
		"fetch a node available and compatible with $pkg and map it to the session"
		node = self.gridref().find_node(pkg = pkg, **opts)
		if self.subnet:
			node.join(self.subnet)
		self.plan.append((None, node))
		return node

	def _release_pair(self, pkg, node):
		if self.gridref()._is_transient(node):
			self.gridref()._terminate(node)
		else:
			if pkg:
				node.uninstall(pkg)
			if self.subnet:
				node.leave(self.subnet)

		# try:
		#	if self.gridref()._is_transient(node):
		#		self.gridref()._terminate(node)
		#	else:
		#		if pkg:
		#			node.uninstall(pkg)
		#		if self.subnet:
		#			node.leave(self.subnet)
		# except Exception as e:
		#	self.gridref().quarantine(node = node, reason = e)

	def release(self, node):
		"release the node from the session"
		for pkg, _node in self.plan:
			if _node == node:
				self._release_pair(pkg, _node)
				break
		else:
			raise NoSuchItemError(node, self)
		self.plan.remove((pkg, _node))
		if self.gridref()._is_transient(node):
			self.gridref().remove_node(node)

	def deploy(self, packages):
		"get, apply, register and return a named plan"
		plan = self.gridref().get_deployment_plan(packages)
		done = []
		try:
			for pkg, node in plan:
				if self.subnet:
					node.join(self.subnet)
				node.install(pkg)
				done.append((pkg, node))
			self.plan += plan
			return plan
		except:
			for pkg, node in done: # cleanup partial install
				self._release_pair(pkg, node)
			raise

	def undeploy(self):
		for pkg, node in self.plan:
			self._release_pair(pkg, node)
		del self.plan[:]

	def close(self, force = False):
		if self.plan and not force:
			raise SessionNotEmptyError(self)
		else:
			self.undeploy()
			self.gridref()._remove_session(self)

class SubnetPoolExhaustedError(Exception):

	def __init__(self):
		super(SubnetPoolExhaustedError, self).__init__("subnet pool exhausted")

class NodePoolExhaustedError(Exception):

	def __init__(self):
		super(NodePoolExhaustedError, self).__init__("node pool exhausted")

class DuplicatedSubnetError(Exception):

	def __init__(self, subnet, container):
		super(DuplicatedSubnetError, self).__init__("%s: subnet already in %s" % (
			subnet,
			container))

class DuplicatedNodeError(Exception):

	def __init__(self, node, container):
		super(DuplicatedNodeError, self).__init__("%s: node already in %s" % (
			node,
			container))

class SubnetInUseError(Exception):

	def __init__(self, subnet, referrer):
		super(SubnetInUseError, self).__init__("%s: subnet used by %s" % (
			subnet,
			referrer))

class NodeInUseError(Exception):

	def __init__(self, node, referrer):
		super(NodeInUseError, self).__init__("%s: node used by %s" % (
			node,
			referrer))

class AccessViolation(Exception):

	def __init__(self, user, resource):
		super(AccessViolation, self).__init__("%s: user cannot access %s" % (
			user,
			resource))

class Grid(object):
	"handle nodes and packages"

	__metaclass__ = abc.ABCMeta

	def __init__(self, name, nodes = None, subnets = None, sessions = None):
		self.name = name
		self.nodes = nodes if nodes is not None else []
		self.subnets = subnets if subnets is not None else []
		self.sessions = sessions if sessions is not None else []

	def __str__(self):
		return self.name

	def __iter__(self):
		for node in self.nodes:
			yield node

	def __len__(self):
		return len(self.nodes)

	def add_node(self, node):
		if not node in self.nodes:
			self.nodes.append(node)
		else:
			raise DuplicatedNodeError(node, self)

	def remove_node(self, node, force = False):
		if node in self.nodes:
			for session in self.sessions:
				if node in session:
					if force:
						session.release(node)
						break
					else:
						raise NodeInUseError(node, session)
			self.nodes.remove(node)
		else:
			raise NoSuchItemError(node, self)

	def add_subnet(self, subnet):
		if not subnet in self.subnets:
			self.subnets.append(subnet)
		else:
			raise DuplicatedSubnetError(subnet, self)

	def remove_subnet(self, subnet, force = False):
		if subnet in self.subnets:
			for session in self.sessions:
				if session.subnet == subnet:
					if force:
						raise NotImplementedError("cannot force subnet removal yet")
					else:
						raise SubnetInUseError(subnet, session)
			self.subnets.remove(subnet)
		else:
			raise NoSuchItemError(subnet, self)

	def quarantine(self, node, reason):
		"make a node unavailable for allocation"
		assert not self.is_quarantined(node), "%s: already quarantined" % node
		assert not self.is_allocated(node), "%s: node allocated, release it first" % node
		node.is_quarantined = reason

	def rehabilitate(self, node):
		"remove a node from quarantine"
		node.is_quarantined = False

	def is_quarantined(self, node):
		return hasattr(node, "is_quarantined") and bool(getattr(node, "is_quarantined"))

	def get_quarantine_reason(self, node):
		assert self.is_quarantined(node), "%s: not quarantined" % node
		res = "%s" % node.is_quarantined
		if isinstance(Exception, self.is_quarantined):
			res = "%s, %s" % (type(self.is_quarantined).__name__, res)
		return res

	def _set_transient(self, node):
		node._is_transient = True

	def _is_transient(self, node):
		return hasattr(node, "_is_transient") and getattr(node, "_is_transient")

	def _get_allocated_nodes(self):
		"return the list of allocated nodes"
		for session in self.sessions:
			for node in session:
				yield node

	def _get_available_nodes(self):
		"return the list of nodes neither allocated nor quarantined"
		for node in self.nodes:
			if not self.is_quarantined(node) and not node in self._get_allocated_nodes():
				yield node

	def is_available(self, node):
		return node in self._get_available_nodes()

	def is_allocated(self, node):
		return node in self._get_allocated_nodes()

	def get_status(self, node):
		if self.is_available(node):
			return "available"
		elif self.is_allocated(node):
			return "allocated"
		elif self.is_quarantined(node):
			return "quarantined: %s" % self.get_quarantine_reason(node)

	def _create_node(self, pkg = None, **opts):
		"""
		Override to create a new node (hereafter called a "transient node"):
		  * compatible with package $pkg
		  * supporting specified options $opts
		Warning: do not call this directly, it's invoked by find_node on demand.
		"""
		raise NodePoolExhaustedError()

	def _terminate(self, node):
		"destroy a transient node created with _create_node()"
		assert False, "%s: _terminate invoked on non-generative grid" % node

	def find_node(self, pkg = None, excluded = (), **opts):
		"find a node available and compatible with $pkg - or - create one"
		for node in self._get_available_nodes():
			if not node in excluded\
			and node.has_support(**opts)\
			and (not pkg or node.is_installable(pkg)):
				break
		else:
			node = self._create_node(pkg = pkg, **opts)
			self.add_node(node)
			self._set_transient(node)
		return node

	def get_deployment_plan(self, packages):
		"""
		Pair packages to nodes depending on their compatibility and availability.
		Return the deployment plan as a tuple of pairs (pkg, node).
		"""
		used = []
		plan = []
		for pkg in packages:
			node = self.find_node(pkg = pkg, excluded = used)
			used.append(node)
			plan.append((pkg, node))
		return plan

	def _get_available_subnet(self):
		"return a subnet not already allocated for a session"
		if self.subnets:
			for subnet in self.subnets:
				for session in self.sessions:
					if session.subnet == subnet:
						break
				else:
					return subnet
			else:
				raise SubnetPoolExhaustedError()
		else:
			return None

	def open_session(self, name, user, session_cls = Session, **opts):
		# re-open session if it exists...
		for session in self.sessions:
			if session.name == name:
				if not session.user == user:
					raise AccessViolation(user, session)
				break
		# ...create new session otherwise
		else:
			session = (session_cls)(
				gridref = weakref.ref(self),
				name = name,
				user = user,
				subnet = self._get_available_subnet(),
				**opts)
			self.sessions.append(session)
		return session

	def _remove_session(self, session):
		"do not use directly -- called by the session on closing"
		assert session in self.sessions, "session '%s' unknown" % session
		self.sessions.remove(session)

	def reset(self):
		"terminate all sessions, remove all nodes"
		for session in tuple(session for session in self.sessions):
			session.close(force = True)
		for node in tuple(node for node in self.nodes):
			self.remove_node(node)

	def _get_node_session(self, node):
		"return session associated to node or None"
		for session in self.sessions:
			if node in session:
				return session

	def node_equal(self, lnode, rnode):
		return self._get_node_session(lnode) == self._get_node_session(rnode)\
			and lnode == rnode

################
# test doubles #
################

class FakePackage(Package):

	def get_typename(self):
		return "fake package"

	def install(self, node):
		assert not node.terminated
		assert\
			not node.is_installed(self),\
			"package '%s' already installed on node '%s', cannot install" % (self, node)
		node.installed.append(self)

	def uninstall(self, node):
		assert not node.terminated
		assert\
			node.is_installed(self),\
			"package '%s' not yet installed on node '%s', cannot uninstall" % (self, node)
		node.installed.remove(self)

	def is_installed(self, node):
		assert not node.terminated
		return self in node.installed

	def is_installable(self, node):
		assert not node.terminated
		return True

class FakeNode(Node):

	def __init__(self, name):
		super(FakeNode, self).__init__(name = name)
		self.terminated = False
		self.installed = []
		self.subnets = []

	def has_support(self, **opts):
		return True

	def is_up(self):
		return not self.terminated

	def get_load(self):
		assert not self.terminated
		return .0

	def join(self, subnet):
		assert not self.terminated
		assert subnet, "node '%s' cannot join null subnet" % self
		assert not subnet in self.subnets
		self.subnets.append(subnet)

	def leave(self, subnet):
		assert not self.terminated
		assert subnet, "node '%s' cannot leave null subnet" % self
		assert subnet in self.subnets
		self.subnets.remove(subnet)

	def get_subnets(self):
		assert not self.terminated
		return self.subnets

	def get_hoststring(self): pass

	def get_installed_packages(self):
		return self.installed

	def terminate(self):
		self.terminated = True

class FakeGenerativeGrid(Grid):
	"generative grid of fake nodes"

	ref = 0

	def _create_node(self, **opts):
		node = FakeNode("tnode%i" % self.ref)
		FakeGenerativeGrid.ref += 1
		return node

	def _terminate(self, node):
		node.terminate()

def unzip(pairs):
	"split a list of pairs into two lists with first and second elements"
	firsts = ()
	seconds = ()
	for x, y in pairs:
		firsts += (x,)
		seconds += (y,)
	class Unzipped: pass
	res = Unzipped()
	res.firsts = firsts
	res.seconds = seconds
	return res

#########
# tests #
#########

class SelfTest(unittest.TestCase):
	"all grid subclasses must pass those tests, derive and adapt $cls below"

	cls = {
		"generative_grid": FakeGenerativeGrid, # generative grid
		"package": FakePackage,
		"subnet": Subnet,
		"node": FakeNode,
		"user": User,
		"grid": Grid, # non-generative grid
	}

	def test_mocks(self):
		"test mocks"
		node = self.cls["node"](name = "node")
		pkg = self.cls["package"](name = "package", version = "1.0")
		node.install(pkg)
		assert node.is_installed(pkg)
		node.uninstall(pkg)
		assert not node.is_installed(pkg)
		subnet = self.cls["subnet"]("subnet")
		node.join(subnet)
		assert node in subnet
		node.leave(subnet)
		assert not node in subnet

	def test_add_remove_node(self):
		"test node management operations"
		grid = self.cls["grid"]("grid")
		node = self.cls["node"]("node")
		grid.add_node(node)
		self.assertIn(node, grid)
		self.assertRaises(DuplicatedNodeError, grid.add_node, node)
		grid.remove_node(node)
		self.assertNotIn(node, grid)
		self.assertRaises(NoSuchItemError, grid.remove_node, node)

	def test_add_remove_subnet(self):
		"test subnet management operations"
		grid = self.cls["grid"]("grid")
		self.assertIs(grid._get_available_subnet(), None)
		subnet = self.cls["subnet"]("subnet")
		grid.add_subnet(subnet)
		self.assertEqual(grid._get_available_subnet(), subnet)
		self.assertRaises(DuplicatedSubnetError, grid.add_subnet, subnet)
		grid.remove_subnet(subnet)
		self.assertIs(grid._get_available_subnet(), None)
		self.assertRaises(NoSuchItemError, grid.remove_subnet, subnet)

	def test_open_close_session(self):
		grid = self.cls["grid"]("grid")
		user = self.cls["user"]("user")
		session = grid.open_session(name = "session", user = user)
		self.assertIn(session, grid.sessions)
		self.assertEqual(len(grid.sessions), 1)
		grid.open_session(name ="session", user = user).close()
		self.assertEqual(len(grid.sessions), 0)

	def test_grid_reset(self):
		"test grid closing on a generative grid"
		grid = self.cls["generative_grid"]("grid")
		user = self.cls["user"]("user")
		for i in xrange(10):
			session = grid.open_session(name = "session%i" % i, user = user)
			node = session.allocate_node()
		grid.reset()
		self.assertEquals(len(grid), 0)
		self.assertEquals(len(grid.sessions), 0)

	def assert_deployment(self, packages, plan, grid, session):
		"assert deployment is correct"
		# assert each allocated nodes is allocated once
		self.assertEqual(len(set(unzip(plan).seconds)), len(plan))
		# assert all nodes are in the session subnet
		if session.subnet:
			for _, node in plan:
				assert node in session.subnet,\
					"node '%s' not in subnet '%s' (node subnets: %s)" % (
						node,
						session.subnet,
						node.get_subnets())
				assert grid.is_allocated(node),\
					"node '%s' not allocated" % node
		# assert all packages are installed
		for src_pkg in packages:
			for tgt_pkg, node in plan:
				if src_pkg == tgt_pkg:
					self.assertTrue(node.is_installed(src_pkg))
					break
			else:
				raise Exception("package '%s' not installed" % src_pkg)

	def assert_undeployment(self, nodes, grid, session):
		"assert undeployment is correct"
		for node in nodes:
			assert grid.is_available(node),\
				"node '%s' not available (status=%s)" % (
					node,
					grid.get_status(node))
			# assert node have no package installed
			assert not node.get_installed_packages(),\
				"packages '%s' not uninstalled from node '%s'" % (
					node.get_installed_packages(),
					node)
			# assert node has left the session subnet
			if session.subnet:
				assert not node in session.subnet,\
					"node '%s' still in subnet '%s'" % (
						node,
						session.subnet)

	def mkenv(self, nb_nodes, nb_packages):
		"create test objects using a non-generative grid"
		nodes = [self.cls["node"]("node%i" % i) for i in xrange(nb_nodes)]
		packages = [self.cls["package"]("pkg%i" % i, "1.0") for i in xrange(nb_packages)]
		subnets = [self.cls["subnet"]("subnet")]
		grid = self.cls["grid"](name = "grid", subnets = subnets, nodes = nodes)
		user = self.cls["user"](name = "user")
		session = grid.open_session(name = "session", user = user)
		return (nodes, packages, grid, session)

	def test_bijective_cycle(self):
		"deploy and undeploy packages, where |nodes| = |packages|"
		nodes, packages, grid, session = self.mkenv(nb_nodes = 10, nb_packages = 10)
		plan = session.deploy(packages)
		self.assert_deployment(packages, plan, grid, session)
		# assert we cannot deploy again:
		self.assertRaises(Exception, session.deploy, packages = packages)
		# assert everything is cleaned up:
		session.close(force = True)
		self.assert_undeployment(nodes, grid, session)

	def test_injective_cycle(self):
		"deploy and undeploy packages, where |nodes| > |packages|"
		nodes, packages, grid, session = self.mkenv(nb_nodes = 20, nb_packages = 10)
		plan1 = session.deploy(packages)
		plan2 = session.deploy(packages)
		# assert the deployments are correct:
		self.assert_deployment(packages, plan1, grid, session)
		self.assert_deployment(packages, plan2, grid, session)
		# assert everything is cleaned up:
		session.close(force = True)
		self.assert_undeployment(nodes, grid, session)

	def test_surjective_cycle(self):
		"deploy and undeploy packages, where |nodes| < |packages|"
		nodes, packages, grid, session = self.mkenv(nb_nodes = 10, nb_packages = 20)
		# assert deployment fails:
		self.assertRaises(Exception, session.deploy, packages = packages)
		# assert everything is cleaned up:
		self.assert_undeployment(nodes, grid, session)

	def test_node_creation(self):
		"test deployment on a generative grid"
		grid = self.cls["generative_grid"](name = "test") # empty grid
		assert len(grid) == 0
		foo = self.cls["package"]("foo", "1.0")
		bar = self.cls["package"]("bar", "1.0")
		packages = [foo, bar]
		user = self.cls["user"]("user")
		session = grid.open_session(name = "session", user = user)
		# assert nodes are created and are transient:
		plan = session.deploy(packages = packages)
		for pkg, node in plan:
			self.assertTrue(grid._is_transient(node), "node '%s' not transient" % node)
		self.assert_deployment(packages, plan, grid, session)
		session.close(force = True)
		for pkg, node in plan:
			self.assertFalse(node.is_up(), "node '%s' still up" % node)

	def test_access_violation(self):
		grid = self.cls["grid"]("grid")
		user1 = self.cls["user"]("user1")
		session1 = grid.open_session("session1", user = user1)
		user2 = self.cls["user"]("user2")
		self.assertRaises(AccessViolation, grid.open_session, "session1", user2)

if __name__ == "__main__": unittest.main(verbosity = 2)
