#copyright (c) 2014 arkena, released under the GPL license.

import ansible.inventory, ansible.runner, unittest

from testgrid import model

def noninteractive(string):
	return "DEBIAN_FRONTEND=noninteractive %s" % string

class Package(model.Package):
	"debian package management commands"

	def __init__(self, *args, **kwargs):
		super(Package, self).__init__(*args, **kwargs)
		if self.version:
			self.tag = "%s=%s" % (self.name, self.version)
		else:
			self.tag = self.name

	def _run_apt(self, node, state):
		"reach package state on target, raise exception on error"
		hoststring = node.get_hoststring()
		username, password, hostname, port = hoststring.split()
		res = testgrid.model.ansible_run(
			hoststring = hoststring,
			modname = "apt",
			modargs = "pkg=%s state=%s" % (self.tag, state),
			sudo = username != "root",
		)
		return (0, res.get("stdout", None), res.get("stderr", None))

	def install(self, node):
		# legacy command: noninteractive("apt-get -qqy --force-yes install %s" % self.tag)
		return self._run_apt(node = node, state = "present force=yes")

	def uninstall(self, node):
		# legacy command: noninteractive("apt-get -qq remove --purge %s" % self.name)
		return self._run_apt(node = node, state = "absent purge=yes force=yes")

	def is_installed(self, node):
		code, stdout, stderr = node.execute("dpkg -s %s" % self.name)
		return code == 0

	def is_installable(self, node):
		args = noninteractive("apt-get -qqy --force-yes --dry-run install %s" % self.name)
		res = model.ansible_run(
			hoststring = node.get_hoststring(),
			modname = "shell",
			modargs = args)
		return res["rc"] == 0

#########
# tests #
#########

class SelfTest(unittest.TestCase):

	def test_FIXME(self):
		pkg = Package(name = "foo", version = "1.0")

if __name__ == "__main__": unittest.main(verbosity = 2)
