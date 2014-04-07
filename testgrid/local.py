# copyright (c) 2013-2014 smartjog, released under the GPL license.

"client managing sessions for a controller-less grid"

import unittest

import remote, tgparser, client

############################################
# concrete types availables for the parser #
############################################

class RemoteNode(remote.Node): pass

##########
# client #
##########

class Client(client.Client):
	"handle transient sessions only"

	def __init__(self, username = None, name = "grid", ini = "~/grid.ini"):
		grid = tgparser.parse_grid(name, ini, __name__)
		super(Client, self).__init__(grid = grid, username = username)

##############
# unit tests #
##############

class SelfTest(client.SelfTest):

	cls = Client

if __name__ == "__main__": unittest.main(verbosity = 2)