# copyright (c) 2013-2014 smartjog, released under the GPL license.

"service for creating on-demand, isolated, programmable test environments"

__version__ = "20140407-2"

import\
	ansible.inventory, ansible.runner, subprocess,\
	unittest, weakref, getpass, time, abc

class UnreachableHostError(Exception): pass

class OperationError(Exception): pass

def ansible_run(hoststring, modname, modargs, sudo = False):
	res = ansible.runner.Runner(
		inventory = ansible.inventory.Inventory("%s," % hoststring),
		module_name = modname,
		module_args = modargs,
		sudo = sudo,
		forks = 0).run()
	if not hoststring in res["contacted"]:
		raise UnreachableHostError("%s: unreachable" % hoststring)
	res = res["contacted"][hoststring]
	if "failed" in res:
		raise OperationError("%s: module %s: %s" % (hoststring, modname, res["msg"]))
	return res

def local_run(argv, warn_only = False):
	sp = subprocess.Popen(
		args = argv,
		shell = isinstance(argv, str), # use shell if $argv is a string
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = sp.communicate()
	code = sp.returncode
	if code and not warn_only:
		raise OperationError("%s: command (%i): %s" % (argv, code, stderr.strip()))
	return (code, stdout, stderr)

class Package(object):

	__metaclass__ = abc.ABCMeta

	def __init__(self, name, version = None):
		self.name = name
		self.version = version

	def __str__(self):
		return "%s%s" % (self.name, ("-%s" % self.version) if self.version else "")

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self)

	def __eq__(self, other):
		return self.name == other.name and self.version == other.version

	def __ne__(self, other):
		return not (self == other)

	@abc.abstractmethod
	def install(self, node):
		"install package on $node, raise exception on error"
		raise NotImplementedError()

	@abc.abstractmethod
	def uninstall(self, node):
		"uninstall package from $node, raise exception on error"
		raise NotImplementedError()

	@abc.abstractmethod
	def is_installed(self, node):
		"return True if the package is installed on $node, False otherwise"
		raise NotImplementedError()

	@abc.abstractmethod
	def is_installable(self, node):
		"return True if the package is installable on $node, False otherwise"
		raise NotImplementedError()

class Service(object):

	__metaclass__ = abc.ABCMeta

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.name)

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
	def is_started(self, node):
		raise NotImplementedError()

	@abc.abstractmethod
	def get_version(self, node):
		raise NotImplementedError()

class Subnet(object):

	def __init__(self, id):
		self.id = id

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.id)

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
	"abstract interface to an object able to install packages and hosting services"

	__metaclass__ = abc.ABCMeta

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.name)

	def __str__(self):
		return self.name

	@abc.abstractmethod
	def get_typename(self):
		"return human-readable type string"
		return "node"

	@abc.abstractmethod
	def has_support(self, **opts):
		"return True if all specified options are supported"
		raise NotImplementedError()

	@abc.abstractmethod
	def get_load(self):
		"return a float abstracting the overall node load"
		raise NotImplementedError()

	@abc.abstractmethod
	def join(self, subnet):
		"setup a network interface on the specified subnet"
		raise NotImplementedError()

	@abc.abstractmethod
	def leave(self, subnet):
		"remove the network interface on the specified subnet"
		raise NotImplementedError()

	@abc.abstractmethod
	def get_subnets(self):
		"return the list of subnets the node belongs to"
		raise NotImplementedError()

	@abc.abstractmethod
	def get_hoststring(self):
		raise NotImplementedError()

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

	def execute(self, args):
		"execute args, return tuple (code, stdout, stderr)"
		hoststring = self.get_hoststring()
		res = ansible_run(
			hoststring = hoststring,
			modname = "command",
			modargs = args)
		return (res["rc"], res["stdout"], res["stderr"])

class UnknownNodeError(Exception): pass

class Session(object):
	"a session holds a deployment plan and the associated subnet"

	def __init__(self, gridref, username, name = None, plan = None, subnet = None):
		self.gridref = gridref
		self.username = username
		self.name = name
		self.plan = plan or [] # list of pairs (package, node)
		self.subnet = subnet
		if not self.name:
			self.name = "%s@%s" % (self.username, time.strftime("%Y%m%d%H%M%S", time.localtime()))
			self.is_anonymous = True
		else:
			self.is_anonymous = False

	def __repr__(self): return "%s(%s)" % (type(self).__name__, self.name)

	def __str__(self): return self.name

	def __iter__(self):
		for _, node in self.plan:
			yield node

	def __len__(self):
		return len(self.plan)

	def allocate_node(self, pkg = None, **opts):
		"fetch a node available and compatible with $pkg and map it to the session"
		node = self.gridref().find_node(pkg = pkg, **opts)
		assert not node in self, "%s: node already allocated, please report this bug" % node
		if self.subnet:
			node.join(self.subnet)
		self.plan.append((None, node))
		return node

	def _release_pair(self, pkg, node):
		try:
			if self.gridref().is_transient(node):
				self.gridref().terminate_node(node)
			else:
				if pkg:
					node.uninstall(pkg)
				if self.subnet:
					node.leave(self.subnet)
		except Exception as e:
			self.gridref().quarantine_node(node = node, exc = e)

	def release_node(self, node):
		"release the node from the session"
		for pkg, _node in self.plan:
			if _node == node:
				self._release_pair(pkg, _node)
				break
		else:
			raise UnknownNodeError("%s" % node)

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
		self.plan = []

	def __del__(self):
		if self.gridref()\
		and self in self.gridref().get_sessions()\
		and self.is_anonymous:
			self.close()

	def close(self):
		self.undeploy()
		self.gridref()._close_session(self)

class DuplicatedNodeError(Exception): pass

class NodePoolExhaustedError(Exception): pass

class SubnetPoolExhaustedError(Exception): pass

class Grid(object):
	"handle nodes and packages"

	def __init__(self, name, nodes = None, subnets = None, sessions = None):
		self.name = name
		self.nodes = nodes or []
		self.subnets = subnets # may be None
		self.sessions = sessions or []

	def __del__(self):
		"cleanup transient nodes -- to be overloaded for a persistent grid"
		for node in self.nodes:
			if self.is_transient(node):
				self.terminate_node(node)

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.name)

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
			raise DuplicatedNodeError("%s" % node)

	def remove_node(self, node):
		if node in self.nodes:
			for session in self.sessions:
				if node in session:
					session.remove_node(node)
			self.nodes.remove(node)
		else:
			raise UnknownNodeError("%s" % node)

	def quarantine_node(self, node, exc):
		node.is_quarantined = exc

	def rehabilitate_node(self, node):
		node.is_quarantined = False

	def is_quarantined(self, node):
		return hasattr(node, "is_quarantined") and bool(getattr(node, "is_quarantined"))

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

	def create_node(self, pkg = None, **opts):
		"""
		Create a new node (hereafter called a "transient node"):
		  * compatible with package $pkg
		  * supporting specified options $opts
		"""
		raise NodePoolExhaustedError()

	def terminate_node(self, node):
		"destroy a transient node (created with create_node())"
		raise NotImplementedError()

	def find_node(self, pkg = None, excluded = (), **opts):
		"find a node available and compatible with $pkg or create one"
		for node in self._get_available_nodes():
			if not node in excluded\
			and node.has_support(**opts)\
			and (not pkg or node.is_installable(pkg)):
				break
		else:
			node = self.create_node(pkg = pkg, **opts)
			assert\
				not pkg or node.is_installable(pkg),\
				"%s: node cannot install %s, please report this issue" % (node, pkg)
			node.is_transient = True
			self.add_node(node)
		return node

	def is_transient(self, node):
		return hasattr(node, "is_transient") and getattr(node, "is_transient")

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

	def _allocate_subnet(self):
		if self.subnets:
			try:
				return self.subnets.pop()
			except IndexError:
				raise SubnetPoolExhaustedError("%s" % self)
		else:
			return None

	def _release_subnet(self, subnet):
		if self.subnets:
			assert\
				not subnet in self.subnets,\
				"%s: already has %s, please report this issue" % (self, subnet)
			self.subnets.append(subnet)

	def get_sessions(self):
		return self.sessions

	def open_session(self, username = None, name = None):
		username = username or getpass.getuser()
		for session in self.sessions:
			if session.name == name:
				assert session.username == username, "%s: access violation" % name
				break
		else:
			session = Session(
				gridref = weakref.ref(self),
				username = username,
				name = name,
				subnet = self._allocate_subnet())
			self.sessions.append(session)
		return session

	def _close_session(self, session):
		"do not use directly -- called by the session on closing"
		assert session in self.sessions, "%s: unknown session" % session
		self.sessions.remove(session)
		self._release_subnet(session.subnet)

class UnknownGridError(Exception): pass

class DuplicatedGridError(Exception): pass

class Grids(Grid):

	def __init__(self, *grids):
		raise NotImplementedError("!!! work in progress !!!")
		self.grids = grids or []

	def add_grid(self, grid):
		if not grid in self.grids:
			self.grids.append(grid)
		else:
			raise DuplicatedGridError("%s" % grid)

	def remove_grid(self, grid):
		if grid in self.grids:
			self.grids.remove(grid)
		else:
			raise UnknownGridError("%s" % grid)

################
# test doubles #
################

class FakePackage(Package):

	def install(self, node):
		assert not node.terminated
		assert not node.is_installed(self), "%s: %s: already installed" % (node, self)
		node.installed.append(self)

	def uninstall(self, node):
		assert not node.terminated
		assert node.is_installed(self), "%s: %s: not yet installed" % (node, self)
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

	def get_typename(self):
		return "fake node"

	def has_support(self, **opts):
		return True

	def is_up(self):
		return not self.terminated

	def get_load(self):
		assert not self.terminated
		return .0

	def join(self, subnet):
		assert not self.terminated
		assert subnet, "%s: cannot join null subnet" % self
		assert not subnet in self.subnets
		self.subnets.append(subnet)

	def leave(self, subnet):
		assert not self.terminated
		assert subnet, "%s: cannot leave null subnet" % self
		assert subnet in self.subnets
		self.subnets.remove(subnet)

	def get_subnets(self):
		assert not self.terminated
		return self.subnets

	def get_hoststring(self): pass

class FakeGrid(Grid):
	"generative grid of fake nodes"

	ref = 0

	def create_node(self, **opts):
		node = FakeNode("tnode%i" % FakeGrid.ref)
		FakeGrid.ref += 1
		return node

	def terminate_node(self, node):
		node.terminated = True

def unzip(pairs):
	"support function to split a list of pairs into two lists with first and second elements"
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

##############
# unit tests #
##############

class SelfTest(unittest.TestCase):

	def test_fake_node(self):
		node = FakeNode(name = "node")
		pkg = FakePackage(name = "pkg", version = "1.0")
		node.install(pkg)
		assert node.is_installed(pkg)
		node.uninstall(pkg)
		assert not node.is_installed(pkg)
		subnet = Subnet("vlan14")
		node.join(subnet)
		assert node in subnet
		node.leave(subnet)
		assert not node in subnet

	def assertDeployment(self, packages, plan, grid, session):
		"assert deployment is correct"
		# assert each allocated nodes is allocated once
		self.assertEqual(len(set(unzip(plan).seconds)), len(plan))
		# assert all nodes are in the session subnet
		if session.subnet:
			for _, node in plan:
				assert node in session.subnet, "%s: not in %s" % (node, session.subnet)
				assert grid.is_allocated(node), "%s: not allocated" % node
		# assert all packages are installed
		for pkg in packages:
			for _pkg, node in plan:
				if _pkg == pkg:
					self.assertEqual(node.installed, [pkg])
					break
			else:
				raise Exception("%s: not installed" % pkg)

	def assertUndeployment(self, nodes, grid, session):
		"assert undeployment is correct"
		for node in nodes:
			assert grid.is_available(node), "%s: not available" % node
			# assert node have no package installed
			assert not node.installed, "%s: %s not uninstalled" % (node, node.installed)
			# assert node has left the session subnet
			if session.subnet:
				assert not node in session.subnet, "%s: still in %s" % (node, session.subnet)

	@staticmethod
	def mkenv(nb_nodes, nb_packages):
		"create test objects"
		nodes = tuple(FakeNode("node%i" % i) for i in xrange(nb_nodes))
		packages = tuple(FakePackage("pkg%i" % i, "1.0") for i in xrange(nb_packages))
		subnets = [Subnet("vlan14")]
		grid = Grid(name = "grid", subnets = subnets, nodes = nodes) # use a non-generative grid
		session = grid.open_session()
		return (nodes, packages, grid, session)

	def test_bijective_cycle(self):
		"deploy and undeploy packages, where |nodes| = |packages|"
		nodes, packages, grid, session = self.mkenv(nb_nodes = 10, nb_packages = 10)
		plan = session.deploy(packages)
		self.assertDeployment(packages, plan, grid, session)
		# assert we cannot deploy again:
		self.assertRaises(Exception, session.deploy, packages = packages)
		# assert everything is cleaned up:
		session.close()
		self.assertUndeployment(nodes, grid, session)

	def test_injective_cycle(self):
		"deploy and undeploy packages, where |nodes| > |packages|"
		nodes, packages, grid, session = self.mkenv(nb_nodes = 20, nb_packages = 10)
		plan1 = session.deploy(packages)
		plan2 = session.deploy(packages)
		# assert the deployments are correct:
		self.assertDeployment(packages, plan1, grid, session)
		self.assertDeployment(packages, plan2, grid, session)
		# assert everything is cleaned up:
		session.close()
		self.assertUndeployment(nodes, grid, session)

	def test_surjective_cycle(self):
		"deploy and undeploy packages, where |nodes| < |packages|"
		nodes, packages, grid, session = self.mkenv(nb_nodes = 10, nb_packages = 20)
		# assert deployment fails:
		self.assertRaises(Exception, session.deploy, packages = packages)
		# assert everything is cleaned up:
		self.assertUndeployment(nodes, grid, session)

	def test_node_creation(self):
		"test deployment on a generative grid"
		grid = FakeGrid(name = "test") # empty grid
		assert len(grid) == 0
		foo = FakePackage("foo", "1.0")
		bar = FakePackage("bar", "1.0")
		packages = (foo, bar)
		session = grid.open_session()
		# assert nodes are created:
		plan = session.deploy(packages = packages)
		for pkg, node in plan:
			self.assertTrue(grid.is_transient(node), "%s: not transient" % node)
		self.assertDeployment(packages, plan, grid, session)
		session.close()
		for pkg, node in plan:
			self.assertFalse(node.is_up(), "%s: still up" % node)

if __name__ == "__main__": unittest.main(verbosity = 2)
