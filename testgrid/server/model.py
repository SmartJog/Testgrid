# copyright (c) 2013-2014 smartjog, released under the GPL license.

"""
Testgrid is a service designed to pair packages to nodes.

On deploy(), nodes are allocated to install packages,
depending on their compatibility and availability.

On undeploy(), packages are uninstalled, nodes are deallocated.
"""

__version__ = "0.2"

import unittest, getpass, time, abc

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

	def __init__(self, name, version, *packages):
		super(Packages, self).__init__(name, version)
		self.packages = set(packages)

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
			return "%s" % self.manager.get_version(self.name)

	def __getitem__(self, name):
		return self.Service(self, name)

	def __getattr__(self, name):
		return self.Service(self, name)

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
		return any(subnet == self for subnet in node.subnets)

class Node(object):
	"a node is an interface to a physical or virtual machine"

	__metaclass__ = abc.ABCMeta

	service = None # ServiceManager()

	def __init__(self):
		self.subnets = []

	@abc.abstractmethod
	def _setup_interface(self, subnet):
		"setup a network interface on the specified subnet"
		raise NotImplementedError()

	@abc.abstractmethod
	def _cleanup_interface(self, subnet):
		"remove the network interface on the specified subnet"
		raise NotImplementedError()

	def join(self, subnet):
		self.subnets.append(subnet)
		self._setup_interface(subnet)

	def leave(self, subnet):
		self.subnets.remove(subnet)
		self._cleanup_interface(subnet)

	@abc.abstractmethod
	def terminate(self):
		raise NotImplementedError()

	@abc.abstractmethod
	def run(self, *commands):
		raise NotImplementedError()

	@abc.abstractmethod
	def log(self, tag, msg):
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

class UnknownGridError(Exception): pass

class DuplicatedNodeError(Exception): pass

class DuplicatedGridError(Exception): pass

class NodePoolExhaustedError(Exception): pass

class Grid(object):
	"handle nodes and packages"

	def __init__(self, *nodes):
		self.quarantined_nodes = [] # nodes not properly deinstalled, need manual repair
		self.transient_nodes = [] # virtual nodes
		self.nodes = [] # nodes may be added or removed
		for node in nodes:
			self.add_node(node)
		self.plans = {} # indexed plans

	def add_node(self, node):
		if not node in self.nodes:
			self.nodes.append(node)
		else:
			raise DuplicatedNodeError("%s" % node)

	def remove_node(self, node):
		if node in self.nodes:
			self.nodes.remove(node)
		else:
			raise UnknownNodeError("%s" % node)

	def __del__(self):
		"terminate all transient nodes"
		for node in self.transient_nodes:
			node.terminate()

	def _get_allocated_nodes(self):
		"return the list of allocated nodes"
		for key, plan in self.plans.items():
			for _, node in plan:
				yield node

	def _get_available_nodes(self):
		"return the list of nodes neither allocated nor quarantined"
		for node in tuple(self.nodes) + tuple(self.transient_nodes):
			if not node in self.quarantined_nodes\
			and not node in self._get_allocated_nodes():
				yield node

	def __iter__(self):
		for node in self._get_available_nodes():
			yield node

	def __len__(self):
		return len(self._get_available_nodes())

	def _create_node(self, sysname = None, pkg = None):
		"spawn a new node using system $sysname or able to install package $pkg"
		raise NodePoolExhaustedError()

	def _find_node(self, sysname = None, pkg = None, excluded = []):
		"find a compatible available node or create one"
		for node in self._get_available_nodes():
			if not node in excluded and (not pkg or node.is_installable(pkg)):
				break
		else:
			node = self.create_node(pkg = pkg)
			assert\
				node.is_installable(pkg),\
				"%s: invalid node, please report this issue" % (node, pkg)
			self.transient_nodes += (node,)
		return node

	def allocate_node(self, key, sysname = None, pkg = None):
		"fetch a single node and mark it as allocated"
		node = self._find_node(sysname = sysname, pkg = pkg)
		self.plans[key] = self.plans.get(key, ()) + ((None, node),)
		return node

	def release_node(self, key, node):
		"undo allocate_node"
		self.plans[key].remove((None, node))

	def _get_deployment_plan(self, *packages):
		"""
		Pair packages to nodes depending on their compatibility and availability.
		Return the deployment plan as a tuple of pairs (pkg, node).
		"""
		used = []
		plan = []
		for pkg in packages:
			node = self._find_node(pkg = pkg, excluded = used)
			used.append(node)
			plan.append((pkg, node))
		return tuple(plan)

	def _undeploy(self, plan):
		"undo a deployment plan, put any node in error in quarantine"
		for pkg, node in plan:
			try:
				if pkg:
					node.uninstall(pkg)
			except:
				self.quarantined_nodes.append(node)

	def undeploy(self, key):
		"undo and unregister a deployment plan"
		self._undeploy(self.plans[key])
		del self.plans[key]

	def deploy(self, key, *packages):
		"get, apply, register and return deployment plan"
		plan = self._get_deployment_plan(*packages)
		done = []
		try:
			for pkg, node in plan:
				node.install(pkg)
				done.append((pkg, node))
			self.plans[key] = self.plans.get(key, ()) + plan
			return plan
		except:
			self._undeploy(done)
			raise

class Grids(Grid):
	"!!! work in progress !!!"

	def __init__(self, *grids):
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

class Session(object):
	"handle subnets"

	def __init__(self, grid, subnet, key = None):
		self.grid = grid
		self.subnet = subnet
		if not key:
			key = "%s@%s" % (getpass.getuser(), time.strftime("%Y%m%d%H%M%S", time.localtime()))
			self.is_anonymous = True
		else:
			self.is_anonymous = False
		self.key = key

	def close(self):
		self.undeploy()

	def __del__(self):
		if self.is_anonymous:
			self.close()

	def allocate_node(self, sysname = None, pkg = None):
		node = self.grid.allocate_node(key = self.key, sysname = sysname, pkg = pkg)
		node.join(self.subnet)
		return node

	def release_node(self, node):
		node.leave(self.subnet)
		self.grid.release_node(node)

	def list_nodes(self):
		"list session nodes"
		if self.key in self.grid.plans:
			return tuple(node for node in self.grid.plans[self.key].values())
		else:
			return ()

	def deploy(self, *packages):
		plan = self.grid.deploy(self.key, *packages)
		for pkg, node in plan:
			node.join(self.subnet)
		return plan

	def undeploy(self):
		if self.key in self.grid.plans:
			plan = self.grid.plans[self.key]
			self.grid.undeploy(self.key)
			for pkg, node in plan:
				node.leave(self.subnet)

################
# test doubles #
################

class FakePackage(Package):

	def get_install_commands(self): pass

	def get_uninstall_commands(self): pass

	def get_is_installed_commands(self): pass

	def get_is_installable_commands(self): pass

class FakeNode(Node):

	def __init__(self):
		super(FakeNode, self).__init__()
		self.installed = []
		self.terminated = False

	def _setup_interface(self, subnet): pass

	def _cleanup_interface(self, subnet): pass

	def run(self, *commands): pass

	def log(self, tag, msg): pass

	def terminate(self):
		self.terminated = True

	def install(self, package):
		assert not self.terminated
		self.installed.append(package)
		return self

	def uninstall(self, package):
		assert not self.terminated
		self.installed.remove(package)

	def is_installable(self, package):
		assert not self.terminated
		return True

class FakeGrid(Grid):

	create_node = lambda self, **opts: FakeNode()

def unzip(pairs):
	"support function to split a list of pairs into two list with first and second elements"
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

	def assertDeployment(self, packages, plan, session):
		"""
		assert:
		1/ each package is installed
		2/ each allocated nodes is allocated once
		3/ all nodes are in the same subnet
		"""
		self.assertEqual(len(set(unzip(plan).seconds)), len(plan))
		for pkg in packages:
			for _pkg, node in plan:
				assert node in session.subnet, "%s: not in %s" % (node, session.subnet)
				if _pkg == pkg:
					self.assertEqual(node.installed, [pkg])
					break
			else:
				raise Exception("%s: not installed" % pkg)

	def assertUndeployment(self, nodes, session):
		"""
		assert:
		1/ nodes have no package installed
		2/ nodes are not in the session subnet
		"""
		for node in nodes:
			assert not node.installed, "%s: %s not uninstalled" % (node, node.installed)
			assert not node in session.subnet, "%s: still in %s" % (node, session.subnet)

	@staticmethod
	def mkenv(nb_nodes, nb_packages):
		nodes = tuple(FakeNode() for i in xrange(nb_nodes))
		packages = tuple(FakePackage("pkg%i" % i, "1.0") for i in xrange(nb_packages))
		grid = Grid(*nodes) # use a non-generative grid
		session = Session(grid, Subnet("test"))
		return (nodes, packages, session)

	def test_bijective_cycle(self):
		"deploy and undeploy packages, where |nodes| = |packages|"
		nodes, packages, session = self.mkenv(10, 10)
		plan = session.deploy(*packages)
		self.assertDeployment(packages, plan, session)
		# assert we cannot deploy again:
		self.assertRaises(Exception, session.deploy, *packages)
		# assert everything is cleaned up:
		session.close()
		self.assertUndeployment(nodes, session)

	def test_injective_cycle(self):
		"deploy and undeploy packages, where |nodes| > |packages|"
		nodes, packages, session = self.mkenv(20, 10)
		plan1 = session.deploy(*packages)
		plan2 = session.deploy(*packages)
		# assert the deployments are correct:
		self.assertDeployment(packages, plan1, session)
		self.assertDeployment(packages, plan2, session)
		# assert everything is cleaned up:
		session.close()
		self.assertUndeployment(nodes, session)

	def test_sujective_cycle(self):
		"deploy and undeploy packages, where |nodes| < |packages|"
		nodes, packages, session = self.mkenv(10, 20)
		# assert deployment fails:
		self.assertRaises(Exception, session.deploy, *packages)
		# assert nodes are clean:
		self.assertUndeployment(nodes, session)

	def test_node_creation(self):
		"test deployment on a generative grid"
		grid = FakeGrid()
		assert not grid.nodes
		foo = FakePackage("foo", "1.0")
		bar = FakePackage("bar", "1.0")
		# assert nodes are created:
		grid.deploy(foo, bar)

if __name__ == "__main__": unittest.main(verbosity = 2)
