# copyright (c) 2014 smartjog, released under the GPL license.

"installsystems.Hypervisor adapter for testgrid"

from testgrid import database, persistent, installsystems

class Node(database.StorableNode):

	def __init__(self, name, hoststring):
		self.hv = installsystems.Hypervisor(run = lambda *args, **kwargs: None)

class Grid(persistent.Grid): pass

#########
# tests #
#########
