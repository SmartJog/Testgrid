# copyright (c) 2014 arkena, released under the GPL license.

import model
import shell
import pipes

class Package(model.Package):
	"debian package management commands"
	 #fix sudo
	def __init__(self, *args, **kwargs):
		super(Package, self).__init__(*args, **kwargs)
		self.tag = self.name
		if self.version:
			self.tag += "=%s" % self.version

	get_install_commands = lambda self: (
		model.Command("export DEBIAN_FRONTEND=noninteractive && apt-get -qqy --force-yes install %s" % self.tag),
		
	)

	get_uninstall_commands = lambda self: (
		model.Command("export DEBIAN_FRONTEND=noninteractive && apt-get -qq remove --purge %s" % self.name),
	)

	get_is_installed_commands = lambda self: (
		model.Command("dpkg -s %s" % self.name, warn_only = True),
	)

	get_is_installable_commands = lambda self: (
		model.Command(
			"export DEBIAN_FRONTEND=noninteractive && apt-get -qqy --force-yes --dry-run install %s" % self.tag,
			warn_only = True),
	)


class Node(model.Node):
	"debian Node"
	init_arg_required = ("hoststring",)

	init_arg_optional = ()

	def __init__(self, hoststring):
		super(Node, self).__init__()
		self.hoststring = hoststring

	
	def setup_interface(self, subnet): pass
	
	def cleanup_interface(self, subnet): pass


	def run(self, *commands):
		for cmd in commands:
			shell.ssh(self.hoststring,
				  cmd.cmdline,
				  logger = shell.Stderr, warn_only = cmd.warn_only)

	
	def install(self, package):
		return self.run(*package.get_install_commands())


	def uninstall(self, package):
		return self.run(*package.get_uninstall_commands())
