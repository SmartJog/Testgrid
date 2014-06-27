# copyright (c) 2013-2014 smartjog, released under the GPL license.

"client managing sessions for a controller-less grid"

import unittest
import testgrid
from testgrid import debian, remote, client, persistent, vgadapter, isadapter

############################################
# concrete types availables for the parser #
############################################

class PersistentGrid(testgrid.persistent.Grid): pass

class DebianPackage(testgrid.debian.Package): pass

class VagrantNode(testgrid.vgadapter.Node): pass

class VagrantGrid(testgrid.vgadapter.Grid): pass

class IsGrid(testgrid.isadapter.Grid):pass

class RemoteNode(testgrid.remote.Node): pass

##########
# client #
##########

class AccessManager(testgrid.client.AccessManager):
        #FIXME
        def is_administrator(self, user):
                return True

class Client(testgrid.client.Client):
	"handle transient sessions only"

	def __init__(self, username = None, gridname = "grid", ini = "~/grid.ini"):
                accessmgr = AccessManager()
		grid = testgrid.parser.parse_grid(gridname, ini, __name__)
		super(Client, self).__init__(grid = grid, accessmgr = accessmgr ,user = username)
