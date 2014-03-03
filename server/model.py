#!/usr/bin/python2.7
# copyright 2013-2014 arkena, released under the GPL license.

"""
Testgrid is a service designed to pair packages to nodes.

On deploy(), nodes are allocated to install packages,
depending on their compatibility and availability.

On undeploy(), packages are uninstalled, nodes are deallocated.
"""

__version__ = "0.2"

class Command(object):

	def __init__(self, cmdline, warn_only = False):
		self.warn_only = warn_only
		self.cmdline = cmdline

	__repr__ = lambda self: "%s(%s)" % (type(self).__name__, self.cmdline)

	__str__ = lambda self: self.cmdline

class Platform(object): pass

class Package(object):

	def __init__(self, name, version = None):
		self.name = name
		self.version = version

	__repr__ = lambda self: "%s(%s-%s)" % (
		type(self).__name__,
		self.name,
		self.version or "last")

	__str__ = lambda self: "%s-%s" % (self.name, self.version or "last")

	__eq__ = lambda self, other:\
		self.name == other.name\
		and self.version == other.version

	__ne__ = lambda self, other: not (self == other)

	def get_install_commands(self):
		raise NotImplementedError()

	def get_uninstall_commands(self):
		raise NotImplementedError()

	def get_is_installed_commands(self):
		raise NotImplementedError()

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

class Node(object):
	"a node is an interface to a physical or virtual machine"

	def terminate(self):
		raise NotImplementedError()

	def run(self, *commands):
		raise NotImplementedError()

	def log(self, tag, msg):
		raise NotImplementedError()

	def install(self, package):
		self.log("TESTGRID", "installing %s" % package)
		return self.run(*package.get_install_commands())

	def uninstall(self, package):
		self.log("TESTGRID", "uninstalling %s" % package)
		return self.run(*package.get_uninstall_commands())

	is_installed = lambda self, package: self.run(*package.get_is_installed_commands())

	is_installable = lambda self, package: self.run(*package.get_is_installable_commands())

class NodePoolExhausted(Exception): pass

class Grid(object):

	def __init__(self, *nodes):
		self.quarantined_nodes = []
		self.transient_nodes = []
		self.nodes = nodes or ()
		self.plans = []

	def __del__(self):
		for node in self.transient_nodes:
			node.terminate()

	def __iter__(self):
		for node in self.nodes:
			yield node

	def get_allocated_nodes(self):
		"return the list of allocated nodes"
		for plan in self.plans:
			for _, node in plan:
				yield node

	def get_available_nodes(self):
		"return the list of nodes neither allocated nor quarantined"
		for node in self.nodes + tuple(self.transient_nodes):
			if not node in self.quarantined_nodes\
			and not node in self.get_allocated_nodes():
				yield node

	def create_node(self, cls):
		"""
		Create and return a new compnode,
		$cls is a subclass of either Package or Platform.
		"""
		assert issubclass(cls, Package) or issubclass(cls, Platform)
		raise NodePoolExhausted()

	def get_deployment_plan(self, *packages):
		"""
		Pair packages to nodes depending on their compatibility and availability.
		Return the deployment plan as a tuple of pairs (pkg, node).
		"""
		used = []
		plan = []
		for pkg in packages:
			for node in self.get_available_nodes():
				if not node in used and node.is_installable(pkg):
					used.append(node)
					plan.append((pkg, node))
					break
			else:
				node = self.create_node(type(pkg))
				self.nodes += (node,)
				assert\
					node.is_installable(pkg),\
					"new node %s cannot install package %s, please report this bug" % (node, pkg)
				plan.append((pkg, node))
		return tuple(plan)

	def undeploy(self, plan):
		"unapply and unregister plan, put any node on error in quarantine"
		for pkg, node in plan:
			try:
				node.uninstall(pkg)
			except:
				self.quarantined_nodes.append(node)
		if plan in self.plans:
			self.plans.remove(plan)

	def deploy(self, *packages):
		"get, apply, register and return deployment plan"
		plan = self.get_deployment_plan(*packages)
		done = []
		try:
			for pkg, node in plan:
				node.install(pkg)
				done.append((pkg, node))
			self.plans.append(plan)
			return plan
		except:
			self.undeploy(done)
			raise

import server

################
# test doubles #
################

class DummyNode(Node):

	def __init__(self):
		self.installed = []
		self.terminated = False

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

class DummyGrid(Grid):

	create_node = lambda self, cls: DummyNode()

#############
# self test #
#############

import unittest

class SelfTest(unittest.TestCase):

	def assertDeployment(self, packages, plan):
		"assert each package is installed and that nodes are allocated once"
		self.assertEqual(len(set(unzip(plan).seconds)), len(plan))
		for pkg in packages:
			for _pkg, node in plan:
				if _pkg == pkg:
					self.assertEqual(node.installed, [pkg])
					break
			else:
				raise Exception("%s: not deployed" % pkg)

	def test_bijective_cycle(self):
		"deploy and undeploy packages, where |packages| = |nodes|"
		nb_nodes = 10
		nb_packages = 10
		nodes = tuple(DummyNode() for i in xrange(nb_nodes))
		packages = tuple(Package("pkg%i" % i, "1.0") for i in xrange(nb_packages))
		grid = Grid(*nodes)
		plan = grid.deploy(*packages)
		# assert the deployment is correct:
		self.assertDeployment(packages, plan)
		# assert we cannot deploy again:
		self.assertRaises(Exception, grid.deploy, *packages)
		grid.undeploy(plan)
		assert all(not node.installed for node in nodes)

	def test_injective_cycle(self):
		"deploy and undeploy packages, where |packages| < |nodes|"
		nb_nodes = 20
		nb_packages = 10
		nodes = tuple(DummyNode() for i in xrange(nb_nodes))
		packages = tuple(Package("pkg%i" % i, "1.0") for i in xrange(nb_packages))
		grid = Grid(*nodes)
		plan1 = grid.deploy(*packages)
		plan2 = grid.deploy(*packages)
		# assert the deployments are correct:
		self.assertDeployment(packages, plan1)
		self.assertDeployment(packages, plan2)

	def test_sujective_cycle(self):
		"deploy and undeploy packages, where |packages| > |nodes|"
		nb_nodes = 20
		nb_packages = 30
		nodes = tuple(DummyNode() for i in xrange(nb_nodes))
		packages = tuple(Package("pkg%i" % i, "1.0") for i in xrange(nb_packages))
		grid = Grid(*nodes)
		self.assertRaises(Exception, grid.deploy, *packages)

	def test_node_creation(self):
		"test deployment on an empty grid able to spawn nodes"
		grid = DummyGrid()
		assert not grid.nodes
		foo = Package("foo", "1.0")
		bar = Package("bar", "1.0")
		grid.deploy(foo, bar)

if __name__ == "__main__": unittest.main(verbosity = 2)
