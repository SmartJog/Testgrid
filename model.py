# copyright 2014 smartjog, released under the GPL license.

import unittest

###################
# support objects #
###################

class Platform(object): pass

class Package(object):

	def __init__(self, name, version, platform):
		self.name = name
		self.version = version
		self.platform = platform

	__repr__ = lambda self: "%s(%s-%s)" % (
		type(self).__name__,
		self.name,
		self.version)

class Deliverable(object):
	"a deliverable is a set of one or more packages"

	def __init__(self, name, version, package, *packages):
		self.name = name
		self.version = version
		self.packages = [package] + packages

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

class Command(object): pass

class Host(object):

	def __init__(self, hostname, rootpass, platform):
		self.hostname = hostname
		self.rootpass = rootpass
		self.platform = platform
		self.package = None
		self.failed = False

	__repr__ = lambda self: "%s(%s)" % (type(self).__name__, self.hostname)

	def run(self, command):
		"execute command on host"
		raise NotImplementedError()

	def is_available(self):
		"return true if this host is available for deployment"
		return not self.package

	def can_install(self, package):
		return self.platform == package.platform

	def install(self, package):
		self.run(self.platform.install(package))
		self.package = package

	def uninstall(self, package):
		self.run(self.platform.uninstall(package))
		self.package = None

	def is_transient(self):
		"return true if this node was spawned to install a package"
		return False

	def terminate(self):
		"shutdown transient node, delete hkvm domain"
		raise NotImplementedError()

	def set_failed(self, package, exception):
		"mark this host as unusable due to a failed uninstallation"
		self.failed = (package, exception)

class Session(object):

	def __eq__(self, other):
		raise NotImplementedError()

	__ne__ = lambda self, other: not (self == other)

#######################
# exception hierarchy #
#######################

class NoAvailableHost(Exception): pass

class NotDeployed(Exception): pass

#############
# test grid #
#############

class TestGrid(object):

	@property
	def hosts(self):
		raise NotImplementedError()

	def register_host(self, host):
		raise NotImplementedError()

	def unregister_host(self, host):
		raise NotImplementedError()

	@property
	def deployments(self):
		"return list of deployments"
		raise NotImplementedError()

	def register_deployment(self, session, deliverable, plan):
		raise NotImplementedError()

	def unregister_deployment(self, session, deliverable):
		raise NotImplementedError()

	def get_deployment_plan(self, deliverable):
		"return pairs (package, host) to deploy deliverable or raise NoAvailableHost"
		plan = []
		for package in deliverable:
			for host in self.hosts:
				if host.is_available() and host.can_install(package):
					plan.append((package, host))
			else:
				raise NoAvailableHost("%s: no available host" % package)
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
			for package, host in plan:
				node = host.install(package)
				if not node in self.hosts:
					self.add_host(node)
				done.append((package, node))
		except:
			self.undo(done)
			raise
		self.register_deployment(session, deliverable, done)
		return done

	def undo(self, plan):
		"""
		Uninstall packages, terminate transient nodes.
		Raise no exception, a node is marked as failed on any error.
		"""
		for package, node in plan:
			try:
				if node.is_transient():
					node.terminate()
					self.remove_host(node)
				else:
					node.uninstall(package)
			except Exception as e:
				node.set_failed(package, e)

	def undeploy(self, session, deliverable):
		"undo deployment plan for the specified deliverable or raise NotDeployed"
		for ses, dlv, plan in self.deployments:
			if ses == session and dlv == deliverable:
				self.undo(plan)
				self.unregister_deployment(session, deliverable)
				return
		raise NotDeployed(deliverable)

############
# selftest #
############

class FakeHost(Host):

class TransientTestGrid(TestGrid):

	def __init__(self, hosts, deployments):
		self._hosts = hosts or []
		self._deployments = deployments or []

	hosts = property(lambda self: self._hosts)

	deployments = property(lambda self: self._deployments)

	def register_host(self, host):
		self._hosts.append(host)

	def unregister_host(self, host):
		self._hosts.remove(host)

	def register_deployment(self, deployment):
		self._deployments.append(deployment)

	def unregister_deployment(self, deployment):
		self._deployments.remove(deployment)

if __name__ == "__main__": unittest.main(verbosity = 2)

