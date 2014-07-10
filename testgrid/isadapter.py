# copyright (c) 2014 smartjog, released under the GPL license.

"installsystems.Hypervisor adapter for testgrid"

from testgrid import database, persistent, installsystems, model, shell

class Node(database.StorableNode):
	def __init__(self, name, hoststring, arg, profile_name):
		self.arg = arg
		self.name = name
		self.hoststring =  hoststring
                self.profile_name = profile_name

	def marshall(self):
		return "%s" % {
			"name": self.name,
			"hoststring": self.hoststring,
			"arg": self.arg,
                        "profile_name":  self.profile_name,
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

        def get_info(self):
		return "is"


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
                hostname = opts["name"]
		if profile_name == "pg":
                        hoststring = installsystems.normalized_playground_hostname(opts["name"])
                        hostname = hoststring
                        profile = self.profiles.get_profile(image_name = image_name, profile_name = profile_name, ipstore = self.ipstore, domain_name = hoststring)
                else:
                        profile = self.profiles.get_profile(image_name = image_name, profile_name = profile_name, ipstore = self.ipstore, domain_name = hostname)
		self.hv.create_domain(
			profile = profile,
			on_stdout_line = shell.Stdout, # stdout reserved for result
			on_stderr_line = shell.Stderr)
                if profile_name is not "pg":
                        if profile.interfaces:
                                hoststring = self._get_interface(profile.interfaces)
                        else:
                                hoststring = profile.values["domain_name"]

		node = Node(hostname, hoststring, profile.get_argv(), profile_name)
		return node

	def _terminate(self, node):
		kwargs = {"on_stdout_line": shell.Stdout,
			  "on_stderr_line": shell.Stderr,}

		self.hv.stop_domain(
			name = node.name,
			force = True,
			warn_only = True,
			**kwargs)
                if node.profile_name == "pg":
                        self.hv.delete_domain(
                                name = node.name,
                                ipstore = None,
                                interfaces = None,
                                **kwargs)
                else:
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

class TempGrid(Grid):
	def __del__(self):
		self.db.close(delete_storage = True)


#########
# tests #
#########
import tempfile

class FakeTempGrid(TempGrid):
	def __init__(self, name, hoststring, dbpath):
		super(Grid, self).__init__(name = name, dbpath = dbpath)
		self.hoststring = hoststring
		self.hv = installsystems.Hypervisor(run = installsystems.FakeRunner())
		self.ipstore = installsystems.FakeIPStore(host = "fake", port = 0)
		self.ipstore.cache["/tg/allocate?reason=hv"] = "42.42.42.42"
		self.ipstore.cache["/release/42.42.42.42"] = "released 42.42.42.42"
		with tempfile.NamedTemporaryFile() as f:
			f.write("""
			{
				"debian-smartjog": {
					"tg:basic": {
						"description": "",
						"format": [
							"--hostname", "%(domain_name)s"
						]
					}
				}
			}
			""")
			f.flush()
			self.profiles = installsystems.Profiles(path = f.name)

import unittest, time
class FakeTest(unittest.TestCase):

	def setUp(self):
		self.grid = FakeTempGrid(name = "fake_is_test", hoststring = "fakehoststring", dbpath = "/tmp/fake_is.db")
                self.profile = "tg:basic"


	def test(self):
                user = database.StorableUser("user")
                opts = {"image_name": "debian-smartjog",
                        "profile_name": self.profile,
                        "name": "test-isadapter-%s"
                        % time.strftime("%Y%m%d%H%M%S", time.localtime())}
                session = self.grid.open_session(name = "test", user = user)
                node = session.allocate_node(**opts)
                del session
                session = self.grid.open_session(name = "test", user = user) # re-open
                self.assertIn(node, session)
                session.release(node)
                self.assertNotIn(node, session)

class SelfTestQAP(FakeTest):
	def setUp(self):
		#!!! VPN !!!
		self.grid = TempGrid(name = "testis_qap", hoststring = "root@10.69.44.1", profile_path = "testgrid/profiles.json" , ipstore_host = "ipstore.qa.arkena.com",ipstore_port=80 ,dbpath = "/tmp/istest-qap.db")
		self.profile = "tg:basic"

class SelfTestPG(FakeTest):
	def setUp(self):
		#!!! VPN !!!
		self.grid = TempGrid(name = "testis_pg", hoststring = "root@hkvm-pg-1-1.pg-1.arkena.net", profile_path = "testgrid/profiles.json" , ipstore_host = "ipstore.qa.arkena.com",ipstore_port=80 ,dbpath = "/tmp/istest-pg.db")
		self.profile = "pg"


if __name__ == "__main__": unittest.main(verbosity = 2)
