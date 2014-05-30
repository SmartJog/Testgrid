# copyright (c) 2014 smartjog, released under the GPL license.

"installsystems.Hypervisor adapter for testgrid"

import testgrid

class Node(testgrid.model.Node):

	def __init__(self, name, hoststring):
		self.hv = testgrid.installsystems.Hypervisor(run = lambda *args, **kwargs: None)

class Grid(testgrid.persistent.Grid): pass

#########
# tests #
#########
