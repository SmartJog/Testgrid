# copyright (c) 2014 arkena, released under the GPL license.

import model

class Package(model.Package):
	"debian package management commands"

	def __init__(self, *args, **kwargs):
		super(Package, self).__init__(*args, **kwargs)
		self.tag = self.name
		if self.version:
			self.tag += "=%s" % self.version

	get_install_commands = lambda self: (
		model.Command("sudo apt-get -qqy --force-yes install %s" % self.tag),
	)

	get_uninstall_commands = lambda self: (
		model.Command("sudo apt-get -qq remove --purge %s" % self.name),
	)

	get_is_installed_commands = lambda self: (
		model.Command("dpkg -s %s" % self.name, warn_only = True),
	)

	get_is_installable_commands = lambda self: (
		model.Command(
			"sudo apt-get -qqy --force-yes --dry-run install %s" % self.tag,
			warn_only = True),
	)


class Node(model.Node):
	"debian Node"

	def __init__(self, hoststring):
		super(Node, self).__init__()
		self.hoststring = hoststring
		

	#def is_installable(self, package):
		
	def run(self, *commands):
		res = shell.Success()
		for cmd in commands:
			res += shell.ssh(self.hoststring,
				cmd,
				logger = shell.stderr,
				warn_only = cmd.warn_only)
		return res
