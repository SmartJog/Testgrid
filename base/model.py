# copyright 2014 smartjog, released under the GPL license.
# testgrid minimalist abstract data model.
# to implement a testgrid variant:
#   * derive Package()
#   * derive Node()
#   * derive Session()

import unittest

class Package(object):

	def __init__(self, name, version=None):
		self.name = name
		self.version = version

	__repr__ = lambda self: "%s(%s-%s)" % (
		type(self).__name__,
		self.name,
		self.version)

	__eq__ = lambda self, other:\
		self.name == other.name\
		and self.version == other.version

	__ne__ = lambda self, other: not (self == other)

class Deliverable(object):
	"a deliverable is a set of one or more packages"

	def __init__(self, name, version, package, *packages):
		self.name = name
		self.version = version
		self.packages = set((package,) + packages)

	__repr__ = lambda self: "%s(%s-%s)" % (
		type(self).__name__,
		self.name,
		self.version)

	def __iter__(self):
		for package in self.packages:
			yield package

	__eq__ = lambda self, other:\
		self.name == other.name\
		and self.version == other.version\
		and self.packages == other.packages

	__ne__ = lambda self, other: not (self == other)

class Node(object):

	def can_install(self, package):
		raise NotImplementedError()

	def install(self, package):
		"install package on node, return node"
		raise NotImplementedError()

	def uninstall(self, package):
		raise NotImplementedError()

	def terminate(self):
		"destroy virtual node or shutdown physical node"
		raise NotImplementedError()

class Session(object): pass
class Command(object): pass

class Deployment(object):

	def __init__(self, session , deliverable, plan):
		self.session = session
		self.deliverable = deliverable
		self.plan = set(plan) # set of (package, node)

	__eq__ = lambda self, other:\
		self.session == other.session\
		and self.deliverable == other.deliverable\
		and self.plan == other.plan

	__ne__ = lambda self, other: not (self == other)

	@property
	def nodes(self):
		for package, node in self.plan:
			yield node

class NoAvailableHost(Exception): pass

class NotDeployed(Exception): pass

class TestGrid(object):

	def __init__(self, nodes = None, deployments = None):
		self.nodes = nodes or []
		self.deployments = deployments or []
		self.session = Session or []
	def using(self, node):
		"True if node is already used for a deployment, False otherwise"
		for deployment in self.deployments:
			if node in deployment.nodes:
				return True
		return False

	def get_deployment_plan(self, deliverable):
		"return pairs (package, host) to deploy deliverable or raise NoAvailableHost"
		plan = []
		used = []
		for package in deliverable:
			for node in self.nodes:
				if (not node in used) and (not self.using(node)) and node.can_install(package):
					plan.append((package, node))
					used.append(node)
					break
			else:
				raise NoAvailableHost("%s: no available host for installation" % package)
		return plan

	def is_deployable(self, deliverable):
		"return True if the deliverable can be deployed, False otherwise"
		try:
			self.get_deployment_plan(deliverable)
			return True
		except NoAvailableHost:
			return False

	def deploy(self, session, deliverable):
		"""
		Deploy deliverable and return the deployment plan.
		On error:
		  * raise NoAvailableHost if the deliverable cannot be deployed
      * or InstallationFailure if a package installation failed
      * and restore all hosts.
		"""
		plan = self.get_deployment_plan(deliverable)
		done = []
		try:
			for package, src_node in plan:
				tgt_node = src_node.install(package)
				if tgt_node != src_node:
					# register new node spawned only to install package
					tgt_node.transient = True
					self.nodes.append(tgt_node)
				else:
					tgt_node.transient = False
				done.append((package, tgt_node))
		except:
			self.undo(done)
			raise
		dpl = Deployment(session, deliverable, done)
		self.deployments.append(dpl)
		return dpl

	def undo(self, plan):
		"""
		Uninstall packages, terminate transient nodes.
		Raise no exception, a node is marked as failed on any error.
		"""
		for package, node in plan:
			try:
				if node.transient:
					node.terminate()
					self.nodes.remove(node)
				else:
					node.uninstall(package)
			except Exception as e:
				node.failed = (package, e) # FIXME

	def undeploy(self, session, deliverable):
		"undo deployment plan for the specified deliverable or raise NotDeployed"
		for deployment in self.deployments:
			if deployment.session == session and deployment.deliverable == deliverable:
				self.undo(deployment.plan)
				self.deployments.remove(deployment)
				return
		raise NotDeployed(deliverable)

############
# selftest #
############

class DummyNode(Node):

	can_install = lambda self, package: True

	def install(self, package):
		self.installed = package
		return self

	def uninstall(self, package):
		self.installed = None

	def terminate(self):
		raise Exception("shutting down non-transient node")

class SelfTest(unittest.TestCase):

	def testCycle(self):
		"deploy and undeploy a minimal deliverable"
		n = DummyNode()
		tg = TestGrid(nodes = (n,))
		p = Package("foo", "1.0")
		dlv = Deliverable("foo", "1.0", p)
		s1 = Session()
		dpl = tg.deploy(s1, dlv)
		assert dpl
		assert dpl in tg.deployments
		assert dpl == Deployment(s1, dlv, ((p, n),))
		assert n.installed == p
		self.assertRaises(NoAvailableHost, tg.deploy, s1, dlv)
		s2 = Session()
		self.assertRaises(NotDeployed, tg.undeploy, s2, dlv)
		tg.undeploy(s1, dlv)
		assert not dpl in tg.deployments
		assert not n.installed

	def testAllocation(self):
		"deploy multi-packages deliverable"
		n1 = DummyNode()
		n2 = DummyNode()
		n3 = DummyNode()
		tg = TestGrid(nodes = (n1, n2, n3))
		p1 = Package("foo", "1.0")
		p2 = Package("bar", "1.0")
		p3 = Package("baz", "1.0")
		dlv = Deliverable("foobar", "1.0", p1, p2, p3)
		s = Session()
		dpl = tg.deploy(s, dlv)
		assert dpl
		assert set((p1, p2, p3)) == set((n1.installed, n2.installed, n3.installed))
		self.assertRaises(NoAvailableHost, tg.deploy, s, dlv)

if __name__ == "__main__": unittest.main(verbosity = 2)

