# copyright (c) 2014 arkena, released under the GPL license.

import model

def noninteractive(string):
	return "DEBIAN_FRONTEND=noninteractive %s" % string

class Package(model.Package):
	"debian package management commands"

	def __init__(self, *args, **kwargs):
		super(Package, self).__init__(*args, **kwargs)
		self.tag = self.name
		if self.version:
			self.tag += "=%s" % self.version

	def get_install_commands(self):
		return (model.Command(noninteractive("apt-get -qqy --force-yes install %s" % self.tag)),)

	def get_uninstall_commands(self):
		return (model.Command(noninteractive("apt-get -qq remove --purge %s" % self.name)),)

	def get_is_installed_commands(self):
		return (model.Command("dpkg -s %s" % self.name, warn_only = True),)

	def get_is_installable_commands(self):
		return (model.Command(
			noninteractive("apt-get -qqy --force-yes --dry-run install %s" % self.tag),
			warn_only = True),
		)
