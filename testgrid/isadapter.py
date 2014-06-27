# copyright (c) 2014 smartjog, released under the GPL license.

"installsystems.Hypervisor adapter for testgrid"

from testgrid import database, persistent, installsystems, model, shell

class Node(database.StorableNode):
	def __init__(self, name, hoststring, arg):
                self.arg = arg
		self.name = name
                self.hoststring = hoststring

	def marshall(self):
		return "%s" % {
			"name": self.name,
			"hoststring": self.hoststring,
			"arg": self.arg,
		}

	def __eq__(self, other):
		return isinstance(other, Node)\
		    and self.name == other.name

	def __ne__(self, other):
		return not (self == other)

	def get_subnets(self):
		raise NotImplementedError("isadapter.Node.get_subnets() not implemented yet")

	def get_typename(self):
		return "is image"

	def has_support(self, **opts):
		raise NotImplementedError("isadapter.Node.has_support() not implemented yet")

	def is_up(self):pass

	def get_load(self):
		raise NotImplementedError("isadapter.Node.get_load() not implemented yet")

	def join(self, subnet):
		raise NotImplementedError("isadapter.Node.join() not implemented yet")

	def leave(self, subnet):
		raise NotImplementedError("isadapter.Node.leave() not implemented yet")

	def get_hoststring(self):
		return model.Hoststring("root@%s" % self.hoststring)

	def terminate(self):pass


	def get_installed_packages(self):
		raise NotImplementedError("isadapter.Node.get_installed_packages() not implemented yet")



class Hypervisor(installsystems.Hypervisor):
	def __init__(self, hoststring):
		self.hoststring = hoststring
		self.run = lambda argv, *args, **kwargs: shell.ssh(hoststring = self.hoststring, argv = argv, *args, **kwargs)


class Grid(persistent.Grid):

	def __init__(self, name, hoststring, profile_path , ipstore_host, ipstore_port , dbpath):
		super(Grid, self).__init__(name = name, dbpath = dbpath)
		self.hoststring = hoststring
		self.hv = Hypervisor(hoststring)
		self.ipstore = installsystems.IPStore(host = ipstore_host, port = ipstore_port)
		self.profiles = installsystems.Profiles(path = profile_path)

	def _create_node(self, pkg = None, **opts):
		image_name = opts["image_name"]
		profile_name = opts["profile_name"]
		if profile_name == "pg":
			hostname = installsystems.normalized_playground_hostname(opts["hostname"])
		else:
			hostname = opts["name"]
		profile = self.profiles.get_profile(image_name = image_name, profile_name = profile_name, ipstore = self.ipstore, domain_name = hostname)
		self.hv.create_domain(
			profile = profile,
			on_stdout_line = shell.Stderr, # stdout reserved for result
			on_stderr_line = shell.Stderr)
                if profile.interfaces:
			hoststring = self._get_interface(profile.interfaces)
		else:
                        hoststring = profile.values["domain_name"]

		node = Node(hostname, hoststring, profile.get_argv())
		return node

	def _terminate(self, node):
                kwargs = {"on_stdout_line": shell.Stdout,
			  "on_stderr_line": shell.Stderr,}

		self.hv.stop_domain(
			name = node.name,
			force = True,
			warn_only = True,
			**kwargs)
                self.hv.delete_domain(
			name = node.name,
                        ipstore = self.ipstore,
                        interfaces = [node.hoststring],
			**kwargs)

        def _get_interface(self, interfaces):
		#FIXME: find accurate interface
		for interface in interfaces:
			interfaces = installsystems.parse_interface(str(interface))
			return interfaces['address']

#########
# tests #
#########
import unittest, time

class SelfTest(unittest.TestCase):
	def setUp(self):
		#!!! VPN !!!
		#playground root@hkvm-pg-1-1.pg-1.arkena.net
		self.grid = Grid(name = "testis", hoststring = "root@10.69.44.1", profile_path = "testgrid/profiles.json" , ipstore_host = "ipstore.qa.arkena.com",ipstore_port=80 ,dbpath = "/tmp/istest.db")

#	def tearDown(self):


	def test(self):
                user = database.StorableUser("user")
		opts = {"image_name": "debian-smartjog", "profile_name": "tg:basic", "name": "test-isadapter-%s" % time.strftime("%Y%m%d%H%M%S", time.localtime())}
                session = self.grid.open_session(name = "test", user = user)
		node = session.allocate_node(**opts)
#		self.assertTrue(node.is_up()) can't ping address unreachable
		del session
		session = self.grid.open_session(name = "test", user = user) # re-open
		self.assertIn(node, session)
                self.grid.reset()

if __name__ == "__main__": unittest.main(verbosity = 2)
