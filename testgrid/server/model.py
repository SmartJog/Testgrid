# copyright (c) 2013-2014 smartjog, released under the GPL license.

"""
Testgrid is a service designed to pair packages to nodes.

On deploy(), nodes are allocated to install packages,
depending on their compatibility and availability.

On undeploy(), packages are uninstalled, nodes are deallocated.
"""

__version__ = "20140402"

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
		return any(subnet == self for subnet in node.subnets)

class Node(object):
	"*abstract* interface to a object able to install packages and hosting services"

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

class UnknownPlanError(Exception): pass

class UnknownNodeError(Exception): pass

class DuplicatedNodeError(Exception): pass

class NodePoolExhaustedError(Exception): pass

def Null(*args, **kwargs): pass

class Grid(object):
	"handle nodes and packages"

	def __init__(
		self,
		name,
		nodes = None,
		plans = None,
		logger = None):
		self.name = name
		self.nodes = nodes or []
		self.plans = plans or {}
		self.logger = logger or Null

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.name)

	def __str__(self):
		return self.name

	def add_node(self, node):
		if not node in self.nodes:
			(self.logger)("%s: adding node %s" % (self, node))
			self.nodes.append(node)
		else:
			raise DuplicatedNodeError("%s" % node)

	def remove_node(self, node):
		if node in self.nodes:
			(self.logger)("%s: removing node %s" % (self, node))
			self.nodes.remove(node)
		else:
			raise UnknownNodeError("%s" % node)

	def quarantine_node(self, node):
		node.is_quarantined = True

	def rehabilitate_node(self, node):
		node.is_quarantined = False

	def is_quarantined(self, node):
		return hasattr(node, "is_quarantined") and getattr(node, "is_quarantined")

	def _get_allocated_nodes(self):
		"return the list of allocated nodes"
		for _, plan in self.plans.items():
			for _, node in plan:
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

	def __iter__(self):
		for node in self.nodes:
			yield node

	def __len__(self):
		return len(self.nodes)

	def _create_node(self, sysname = None, pkg = None):
		"spawn a new node using system $sysname or able to install package $pkg"
		raise NodePoolExhaustedError()

	def _find_node(self, sysname = None, pkg = None, excluded = ()):
		"find a compatible available node or create one"
		for node in self._get_available_nodes():
			if not node in excluded and (not pkg or node.is_installable(pkg)):
				break
			(self.logger)("%s: node %s incompatible with (sysname=%s, pkg=%s)" % (
				self,
				node,
				sysname,
				pkg))
		else:
			(self.logger)("%s: no compatible node found for (sysname=%s, pkg=%s)" % (
				self,
				sysname,
				pkg))
			node = self._create_node(pkg = pkg)
			assert\
				node.is_installable(pkg),\
				"%s: invalid node, please report this issue" % (node, pkg)
			self.is_transient = True
		return node

	def is_transient(self, node):
		return hasattr(node, "is_transient") and getattr(node, "is_transient")

	def allocate_node(self, name, sysname = None, pkg = None):
		"fetch a single node and mark it as allocated in the named plan"
		(self.logger)("%s: %s: allocating node (sysname=%s, pkg=%s)" % (self, name, sysname, pkg))
		node = self._find_node(sysname = sysname, pkg = pkg)
		self.plans[name] = self.plans.get(name, []) + [(None, node)]
		return node

	def release_node(self, name, node):
		"release node from the named plan"
		if name in self.plans:
			if (None, node) in self.plans[name]:
				(self.logger)("%s: %s: releasing node %s" % (self, name, node))
				try:
					if node.is_transient:
						node.terminate()
				except:
					self.quarantine_node(node)
				self.plans[name].remove((None, node))
			else:
				raise UnknownNodeError("%s" % node)
		else:
			raise UnknownPlanError("%s" % name)

	def _get_deployment_plan(self, packages):
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
		return plan

	def _undeploy_plan(self, plan):
		for pkg, node in plan:
			try:
				if pkg:
					node.uninstall(pkg)
				if self.is_transient(_node):
					node.terminate()
			except:
				self.quarantine_node(node)

	def undeploy(self, name):
		"undo and unregister the named plan"
		if name in self.plans:
			self._undeploy_plan(self.plans[name])
			del self.plans[name]
		else:
			raise UnknownPlanError("%s" % name)

	def deploy(self, name, packages):
		"get, apply, register and return a named plan"
		plan = self._get_deployment_plan(packages)
		done = []
		try:
			for pkg, node in plan:
				node.install(pkg)
				done.append((pkg, node))
			self.plans[name] = self.plans.get(name, []) + plan
			return plan
		except:
			self._undeploy_plan(done)
			raise

	def get_plan_names(self):
		return self.plans.keys()

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

class UnknownSessionError(Exception): pass

class Session(object):
	"a session links a user to a deployment plan which nodes are isolated in a subnet"

	def __init__(self, grid, name = None, subnet = None):
		self.grid = grid
		self.name = name
		self.subnet = subnet
		if not self.name:
			self.name = "%s@%s" % (getpass.getuser(), time.strftime("%Y%m%d%H%M%S", time.localtime()))
			self.is_anonymous = True
		else:
			self.is_anonymous = False

	def __repr__(self): return "%s(%s)" % (type(self).__name__, self.name)

	def __str__(self): return self.name

	def exists(self):
		return self.name in self.grid.get_plan_names()

	def __del__(self):
		if self.exists() and self.is_anonymous:
			self.close()

	def allocate_node(self, sysname = None, pkg = None):
		node = self.grid.allocate_node(name = self.name, sysname = sysname, pkg = pkg)
		if self.subnet:
			node.join(self.subnet) # isolate node in a subnet if possible
		return node

	def release_node(self, node):
		if self.subnet:
			node.leave(self.subnet)
		self.grid.release_node(name = self.name, node = node)

	def get_nodes(self):
		"list session nodes"
		if self.name in self.grid.plans:
			return tuple(node for _, node in self.grid.plans[self.name])
		else:
			raise UnknowSessionError("%s" % self)

	def deploy(self, packages):
		plan = self.grid.deploy(name = self.name, packages = packages)
		if self.subnet:
			for pkg, node in plan:
				node.join(self.subnet)
		return plan

	def undeploy(self):
		if self.name in self.grid.plans:
			if self.subnet:
				plan = self.grid.plans[self.name]
				for _, node in plan:
					node.leave(self.subnet)
			self.grid.undeploy(name = self.name)
		else:
			raise UnknownSessionError("%s" % self)

	def close(self):
		self.undeploy()

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

	def get_subnets(self):
		return self.subnets

	def join(self, subnet):
		assert not subnet in self.subnets
		self.subnets.append(subnet)

	def leave(self, subnet):
		assert subnet in self.subnets
		self.subnets.remove(subnet)

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
		return self

	def uninstall(self, pkg):
		assert not self.terminated
		assert self.is_installed(pkg), "%s: not yet installed" % pkg
		self.service.remove(name = pkg.name)
		self.installed.remove(pkg)

	def is_installed(self, pkg):
		assert not self.terminated
		return pkg in self.installed

	def is_installable(self, pkg):
		assert not self.terminated
		return True

class FakeGrid(Grid):

	ref = 0

	def _create_node(self, **opts):
		node = FakeNode("transientnode%i" % FakeGrid.ref)
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

class SelfTest(unittest.TestCase):

	def test_fake_node(self):
		node = FakeNode(name = "node")
		pkg = FakePackage(name = "pkg", version = "1.0")
		node.install(pkg)
		assert node.is_installed(pkg)
		node.uninstall(pkg)
		assert not node.is_installed(pkg)

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
				if session.subnet:
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
			if session.subnet:
				assert not node in session.subnet, "%s: still in %s" % (node, session.subnet)

	@staticmethod
	def mkenv(nb_nodes, nb_packages):
		nodes = tuple(FakeNode("node%i" % i) for i in xrange(nb_nodes))
		packages = tuple(FakePackage("pkg%i" % i, "1.0") for i in xrange(nb_packages))
		grid = Grid(name = "grid", nodes = nodes) # use a non-generative grid
		session = Session(grid, Subnet("vlan14"))
		return (nodes, packages, session)

	def test_bijective_cycle(self):
		"deploy and undeploy packages, where |nodes| = |packages|"
		nodes, packages, session = self.mkenv(nb_nodes = 10, nb_packages = 10)
		plan = session.deploy(packages)
		self.assertDeployment(packages, plan, session)
		# assert we cannot deploy again:
		self.assertRaises(Exception, session.deploy, *packages)
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
		self.assertRaises(Exception, session.deploy, *packages)
		# assert everything is cleaned up:
		self.assertUndeployment(nodes, session)

	def test_node_creation(self):
		"test deployment on a generative grid"
		grid = FakeGrid(name = "test")
		assert len(grid) == 0
		foo = FakePackage("foo", "1.0")
		bar = FakePackage("bar", "1.0")
		# assert nodes are created:
		grid.deploy(name = "test", packages = (foo, bar))

if __name__ == "__main__": unittest.main(verbosity = 2)
