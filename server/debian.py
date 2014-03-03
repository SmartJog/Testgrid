# copyright 2014 arkena, released under the GPL license.

import testgrid

class Package(testgrid.Package):
	"debian package management commands"

	get_install_commands = lambda self: (
		testgrid.Command("sudo apt-get -qqy --force-yes install %s%s" % (
			self.name,
			"=%s" % self.version if self.version else "")),
	)

	get_uninstall_commands = lambda self: (
		testgrid.Command("sudo apt-get -qq remove --purge %s" % self.name),
	)

	get_is_installed_commands = lambda self: (
		testgrid.Command("dpkg -s %s" % self.name, warn_only = True),
	)

	get_is_installable_commands = lambda self: (
		testgrid.Command("sudo apt-get -qqy --force-yes --dry-run install %s%s" % (
			self.name,
			"=%s" % self.version if self.version else "")),
	)

