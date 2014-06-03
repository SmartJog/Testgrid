# copyright (c) 2014 smartjog, released under the GPL license.

"installsystems.Hypervisor adapter for testgrid"

from testgrid import database, persistent, installsystems

class Node(database.StorableNode): pass

class Grid(persistent.Grid):

	def __init__(self, name, hoststring, dbpath):
		super(Grid, self).__init__(name = name, dbpath = dbpath)
		self.hv = installsystems.Hypervisor(run = lambda *args, **kwargs: None)

	def _create_node(self, pkg = None, **opts):
		hostname = opts["hostname"]
		image_name = opts["image_name"]
		profile_name = opts["profile_name"]
		profile_cls = installsystems.get_profile_class(image_name)
		profile = profile_cls.get_profile(
			hostname = hostname,
			profile_name = profile_name)
		hv.create_domain(
			image_name = image_name,
			profile = profile,
			on_stdout_line = Stderr, # stdout reserved for result
			on_stderr_line = Stderr)

	def _terminate(self, node):
		pass

#########
# tests #
#########
