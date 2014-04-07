# copyright (c) 2013-2014 smartjog, released under the GPL license.

"service for creating on-demand, isolated, programmable test environments"

__version__ = "20140407"

import unittest, getpass, logging, time, abc

class Command(object):

	def __init__(self, cmdline, warn_only = False):
		self.warn_only = warn_only
		self.cmdline = cmdline

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.cmdline)

	def __str__(self):
		return self.cmdline

class Package(object):

	__metaclass__ = abc.ABCMeta

	def __init__(self, name, version = None):
		self.name = name
		self.version = version

	def __repr__(self):
		return "%s(%s-%s)" % (
			type(self).__name__,
			self.name,
			self.version or "last")

	def __str__(self):
		return "%s-%s" % (self.name, self.version or "last")

	def __eq__(self, other):
		return self.name == other.name and self.version == other.version

	def __ne__(self, other):
		return not (self == other)

	@abc.abstractmethod
	def get_install_commands(self):
		raise NotImplementedError()

	@abc.abstractmethod
	def get_uninstall_commands(self):
		raise NotImplementedError()

	@abc.abstractmethod
	def get_is_installed_commands(self):
		raise NotImplementedError()

	@abc.abstractmethod
	def get_is_installable_commands(self):
		raise NotImplementedError()

class Packages(Package):
	"set of packages"

	def __init__(self, name, version, packages = None):
		super(Packages, self).__init__(name, version)
		self.packages = set(packages or ())

	def get_install_commands(self):
		commands = ()
		for pkg in self.packages:
			commands += pkg.get_install_commands()
		return commands

	def get_uninstall_commands(self):
		commands = ()
		for pkg in self.packages:
			commands += pkg.get_uninstall_commands()
		return commands

	def get_is_installed_commands(self):
		commands = ()
		for pkg in self.packages:
			commands += pkg.get_is_installed_commands()
		return commands

	def get_is_installable_commands(self):
		commands = ()
		for pkg in self.packages:
			commands += pkg.get_is_installable_commands()
		return commands

class Service(object):

	def __init__(self, manager, name):
		self.manager = manager
		self.name = name

	def start(self):
		return self.manager.start(self.name)

	def stop(self):
		return self.manager.stop(self.name)

	def restart(self):
		return self.manager.restart(self.name)

	def reload(self):
		return self.manager.reload(self.name)

	def is_running(self):
		return self.manager.is_running(self.name)

	@property
	def version(self):
		return ("%s" % self.manager.get_version(self.name)).strip()

class ServiceManager(object):

	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def start(self, name):
		raise NotImplementedError()

	@abc.abstractmethod
	def stop(self, name):
		raise NotImplementedError()

	@abc.abstractmethod
	def restart(self, name):
		raise NotImplementedError()

	@abc.abstractmethod
	def reload(self, name):
		raise NotImplementedError()

	@abc.abstractmethod
	def is_running(self, name):
		raise NotImplementedError()

	@abc.abstractmethod
	def get_version(self, name):
		raise NotImplementedError()

	def __getitem__(self, name):
		return Service(manager = self, name = name)

	def __getattr__(self, name):
		return Service(manager = self, name = name)

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

class Node(object):
	"abstract interface to an object able to install packages and hosting services"

	__metaclass__ = abc.ABCMeta

	def __init__(self, name, srvmanager):
		self.service = srvmanager
		self.name = name

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.name)

	def __str__(self):
		return self.name

	@abc.abstractmethod
	def get_typename(self):
		"return human-friendly type string"
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
	def terminate(self):
		"shutdown physical node or destroy virtual machine"
		raise NotImplementedError()

	@abc.abstractmethod
	def run(self, *commands):
		"run list of commands and return the result"
		raise NotImplementedError()

	@abc.abstractmethod
	def log(self, tag, msg):
		"add system log entry"
		raise NotImplementedError()

	def install(self, package):
		self.log("TESTGRID", "installing %s" % package)
		return self.run(*package.get_install_commands())

	def uninstall(self, package):
		self.log("TESTGRID", "uninstalling %s" % package)
		return self.run(*package.get_uninstall_commands())

	def is_installed(self, package):
		return self.run(*package.get_is_installed_commands())

	def is_installable(self, package):
		return self.run(*package.get_is_installable_commands())

class UnknownNodeError(Exception): pass

class Session(object):
	"a session holds a deployment plan and the associated subnet"

	def __init__(self, grid, username, name = None, plan = None, subnet = None):
		self.grid = grid
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
		node = self.grid.find_node(pkg = pkg, **opts)
		assert not node in self, "%s: node already allocated, please report this bug" % node
		if self.subnet:
			node.join(self.subnet)
		self.plan.append((None, node))
		return node

	def _release_pair(self, pkg, node):
		try:
			if pkg:
				node.uninstall(pkg)
				if self.subnet:
					node.leave(self.subnet)
			if self.grid.is_transient(node):
				node.terminate()
		except Exception as e:
			self.grid.quarantine_node(node = node, exc = e)

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
		plan = self.grid.get_deployment_plan(packages)
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
		if self in self.grid.get_sessions() and self.is_anonymous:
			self.close()

	def close(self):
		self.undeploy()
		self.grid._close_session(self)

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
		logging.debug("%s: set %s in quarantine, %s" % (self, node, exc))
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

	def _create_node(self, pkg = None, **opts):
		"""
		Create a new node:
		  * compatible with package $pkg
		  * supporting specified options $opts
		"""
		raise NodePoolExhaustedError()

	def find_node(self, pkg = None, excluded = (), **opts):
		"find a node available and compatible with $pkg or create one"
		for node in self._get_available_nodes():
			if not node in excluded and (not pkg or node.is_installable(pkg)):
				break
		else:
			node = self._create_node(pkg = pkg, **opts)
			assert\
				node.is_installable(pkg),\
				"%s: invalid node, please report this issue" % (node, pkg)
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
				grid = self,
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

	def get_install_commands(self): pass

	def get_uninstall_commands(self): pass

	def get_is_installed_commands(self): pass

	def get_is_installable_commands(self): pass

class FakeServiceManager(ServiceManager):

	def __init__(self):
		self.services = {}

	def add(self, name, version, is_running):
		self.services[name] = {
			"version": version,
			"is_running": is_running,
		}

	def remove(self, name):
		del self.services[name]

	def start(self, name):
		self.services[name]["is_running"] = True

	def stop(self, name):
		self.services[name]["is_running"] = False

	def restart(self, name): self.start(name)

	def reload(self, name): pass

	def is_running(self, name):
		return self.services[name]["is_running"]

	def get_version(self, name):
		return self.services[name]["version"]

class FakeNode(Node):

	def __init__(self, name):
		super(FakeNode, self).__init__(name = name, srvmanager = FakeServiceManager())
		self.terminated = False
		self.installed = []
		self.subnets = []

	def get_typename(self):
		return "fake node"

	def join(self, subnet):
		assert subnet, "%s: cannot join null subnet" % self
		assert not subnet in self.subnets
		self.subnets.append(subnet)
		logging.debug("%s: joined %s" % (self, subnet))

	def leave(self, subnet):
		assert subnet, "%s: cannot leave null subnet" % self
		assert subnet in self.subnets
		self.subnets.remove(subnet)
		logging.debug("%s: left %s" % (self, subnet))

	def get_subnets(self):
		return self.subnets

	def run(self, *commands): pass

	def log(self, tag, msg): pass

	def terminate(self):
		self.terminated = True

	def install(self, pkg):
		assert not self.terminated
		assert not self.is_installed(pkg), "%s: already installed" % pkg
		self.installed.append(pkg)
		# WARNING: all packages are considered to be services
		self.service.add(name = pkg.name, version = pkg.version, is_running = True)
		logging.debug("%s: installed %s" % (self, pkg))

	def uninstall(self, pkg):
		assert not self.terminated
		assert self.is_installed(pkg), "%s: not yet installed" % pkg
		self.service.remove(name = pkg.name)
		self.installed.remove(pkg)
		logging.debug("%s: uninstalled %s" % (self, pkg))

	def is_installed(self, pkg):
		assert not self.terminated
		return pkg in self.installed

	def is_installable(self, pkg):
		assert not self.terminated
		return True

class FakeGrid(Grid):
	"generative grid of fake nodes"

	ref = 0

	def _create_node(self, **opts):
		node = FakeNode("tnode%i" % FakeGrid.ref)
		FakeGrid.ref += 1
		return node

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

#logging.basicConfig(level = logging.DEBUG)

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

	def assertDeployment(self, packages, plan, session):
		"assert deployment is correct"
		# assert each allocated nodes is allocated once
		self.assertEqual(len(set(unzip(plan).seconds)), len(plan))
		# assert all nodes are in the session subnet
		if session.subnet:
			for _, node in plan:
				assert node in session.subnet, "%s: not in %s" % (node, session.subnet)
				assert session.grid.is_allocated(node), "%s: not allocated" % node
		# assert all packages are installed
		for pkg in packages:
			for _pkg, node in plan:
				if _pkg == pkg:
					self.assertEqual(node.installed, [pkg])
					break
			else:
				raise Exception("%s: not installed" % pkg)

	def assertUndeployment(self, nodes, session):
		"assert undeployment is correct"
		for node in nodes:
			assert session.grid.is_available(node), "%s: not available" % node
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
		return (nodes, packages, session)

	def test_bijective_cycle(self):
		"deploy and undeploy packages, where |nodes| = |packages|"
		nodes, packages, session = self.mkenv(nb_nodes = 10, nb_packages = 10)
		plan = session.deploy(packages)
		self.assertDeployment(packages, plan, session)
		# assert we cannot deploy again:
		self.assertRaises(Exception, session.deploy, packages = packages)
		# assert everything is cleaned up:
		session.close()
		self.assertUndeployment(nodes, session)

	def test_injective_cycle(self):
		"deploy and undeploy packages, where |nodes| > |packages|"
		nodes, packages, session = self.mkenv(nb_nodes = 20, nb_packages = 10)
		plan1 = session.deploy(packages)
		plan2 = session.deploy(packages)
		# assert the deployments are correct:
		self.assertDeployment(packages, plan1, session)
		self.assertDeployment(packages, plan2, session)
		# assert everything is cleaned up:
		session.close()
		self.assertUndeployment(nodes, session)

	def test_surjective_cycle(self):
		"deploy and undeploy packages, where |nodes| < |packages|"
		nodes, packages, session = self.mkenv(nb_nodes = 10, nb_packages = 20)
		# assert deployment fails:
		self.assertRaises(Exception, session.deploy, packages = packages)
		# assert everything is cleaned up:
		self.assertUndeployment(nodes, session)

	def test_node_creation(self):
		"test deployment on a generative grid"
		grid = FakeGrid(name = "test")
		assert len(grid) == 0
		foo = FakePackage("foo", "1.0")
		bar = FakePackage("bar", "1.0")
		packages = (foo, bar)
		# assert nodes are created:
		session = grid.open_session()
		plan = session.deploy(packages = packages)
		self.assertDeployment(packages, plan, session)

if __name__ == "__main__": unittest.main(verbosity = 2)
