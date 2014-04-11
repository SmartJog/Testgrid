# copyright (c) 2013-2014 smartjog, released under the GPL license.

"client managing sessions for a controller-less grid"

import unittest, testgrid

############################################
# concrete types availables for the parser #
############################################

class DebianPackage(testgrid.debian.Package): pass

class RemoteNode(testgrid.remote.Node): pass

#class TestboxGrid(testgrid.testbox.Grid): pass

class VagrantGrid(testgrid.vgadapter.Grid): pass

class PersistentGrid(testgrid.persistent.Grid): pass

##########
# client #
##########

class Client(testgrid.client.Client):
	"handle transient sessions only"

	def __init__(self, username = None, name = "grid", ini = "~/grid.ini"):
		grid = testgrid.parser.parse_grid(name, ini, __name__)
		super(Client, self).__init__(grid = grid, username = username)
