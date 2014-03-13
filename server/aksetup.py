# copyright (c) 2014 arkena, released under the GPL license.

# IMPORTANT:
# check the testbox key is set as deploy key of the aksetup repository.

import model

class Package(model.Package):
	"aksetup-based pseudo-package management commands"

	def __init__(self, *args, **kwargs):
		super(Package, self).__init__(*args, **kwargs)
		self.tag = self.name
		if self.version:
			self.tag += "-%s" % self.version

	get_install_commands = lambda self: (
		#model.Command("git clone git@git.smartjog.net:florent.claerhout/aksetup.git"),
		model.Command("cd aksetup && git checkout %s" % self.tag),
		model.Command("sudo su && cd aksetup && bash install.sh"),
	)

	get_uninstall_commands = lambda self: (
		#model.Command("git clone git@git.smartjog.net:florent.claerhout/aksetup.git"),
		model.Command("cd aksetup && git checkout %s" % self.tag),
		model.Command("sudo su && cd aksetup && bash uninstall.sh"),
	)

	get_is_installed_commands = lambda self: (
		#model.Command("git clone git@git.smartjog.net:florent.claerhout/aksetup.git"),
		model.Command("cd aksetup && git checkout %s" % self.tag),
		model.Command("sudo su && cd aksetup && bash is_installed.sh", warn_only = True),
	)

	get_is_installable_commands = lambda self: (
		model.Command("git clone git@git.smartjog.net:florent.claerhout/aksetup.git"),
		model.Command("cd aksetup && git checkout %s" % self.tag),
		model.Command("sudo su && cd aksetup && bash is_installable.sh", warn_only = True),
	)
