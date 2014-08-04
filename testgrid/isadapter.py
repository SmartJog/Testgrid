# copyright (c) 2014 smartjog, released under the GPL license.

"installsystems.Hypervisor adapter for testgrid"

from testgrid import database, persistent, installsystems, model, shell
import paramiko
import time
import os

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
			"profile_name":	 self.profile_name,
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
		# FIXME
		return self.profile_name == opts["profile_name"]

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

KEY ="""ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDn8KBFY3xQO+UCLTaAv/OETo9W6u0E4Gke+x/nfwYPK014Etr4oFdXyqJggzmK6flDDbokYCoHZuDhtZSE4FVDuMhWjweUg68/xb2rUFAC8nNpEsdcA9v5S9HPxND1nA765JWX1jcrLVjadiFQSgMvk+iyYMxFaSKsVoSZtYL2VBpdCIe2YZwAyF4OCU/plnEnd2YMevkAjUw+ArPw9kcjxQj6mpux5YeQt7NdZnYooa4Ux4OlB4jRfVQPZC1ytjY+A89FzmiPLWww8Hfrus542QXHZhEa5KbzcLyJJ2ImjN8SCsoiFGywqxBB6rESCj8HmjDQNr0c4iO0lQ+2lh17 root@testgrid-test.qap"""


class Grid(persistent.Grid):

	def __init__(self, name, hoststring, profile_path , ipstore_host, ipstore_port , dbpath, public_key = KEY):
		super(Grid, self).__init__(name = name, dbpath = dbpath)
		self.hoststring = hoststring
		self.hv = Hypervisor(hoststring)
		self.ipstore = installsystems.IPStore(host = ipstore_host, port = ipstore_port)
		self.profiles = installsystems.Profiles(path = profile_path)
		self.public_key = public_key

	def _create_node(self, pkg = None, **opts):
		image_name = opts["image_name"]
		profile_name = opts["profile_name"]
                if "name" in opts:
                        hostname = opts["name"]
                else:
                        hostname = "node-is%s" % time.strftime("%Y%m%d%H%M%S", time.localtime())
		if profile_name == "pg":
			hoststring = installsystems.normalized_domain_name(hostname)
			hostname = hoststring
			profile = self.profiles.get_profile(image_name = image_name, profile_name = profile_name, ipstore = self.ipstore, domain_name = hoststring)
		else:
			profile = self.profiles.get_profile(image_name = image_name, profile_name = profile_name, ipstore = self.ipstore, domain_name = hostname)
		self.hv.create_domain(
			profile = profile, public_key = self.public_key,
			on_stdout_line = None, # stdout reserved for result
			on_stderr_line = None)
		if profile_name is not "pg":
			if profile.interfaces:
				hoststring = self._get_interface(profile.interfaces)
			else:
				hoststring = profile.values["domain_name"]
		node = Node(hostname, hoststring, profile.get_argv(), profile_name)
		os.environ['SSHCONNECTTIMEOUT'] = "60" #FIXME
                timeout = time.time() + 5*60
                while  True:
                        try:
                                shell.run("ssh root@%s -o ConnectTimeout=1" % node.hoststring) # FIXME maybe fix a limit
                                break
                        except shell.CommandFailure:
                                if time.time() > timeout:
                                        raise Exception("can't reach %s for 5 minutes" % node.hoststring)
                                print "can't reach %s" % node.hoststring
                                time.sleep(1)
		shell.ssh(hoststring = "root@%s" %  node.hoststring, argv = "touch /etc/apt/apt.conf.d/proxyqap")
		shell.scp(hoststring = "root@%s" %  node.hoststring, remotepath= "/etc/apt/apt.conf.d/proxyqap", localpath="testgrid/apt.conf")
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
		self.ipstore.cache["/allocate?reason=hv+%7C+no+details"] = "42.42.42.42"
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
                self.opts = {"image_name": "debian-smartjog",
                             "profile_name": self.profile,
                             "name": "test-isadapter-%s"
                             % time.strftime("%Y%m%d%H%M%S", time.localtime())}
                self.grid.ipstore.cache["/tg/allocate?reason=hv+%7C+image_name%3Ddebian-smartjog+domain_name%3D" + self.opts["name"]] = "42.42.42.42"

	def test(self):
		user = database.StorableUser("user")
		session = self.grid.open_session(name = "test", user = user)
		node = session.allocate_node(**self.opts)
		del session
		session = self.grid.open_session(name = "test", user = user) # re-open
		self.assertIn(node, session)
		session.release(node)
		self.assertNotIn(node, session)



if __name__ == "__main__": unittest.main(verbosity = 2)
