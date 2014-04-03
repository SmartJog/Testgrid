# copyright (c) 2013-2014 smartjog, released under the GPL license.

"client managing sessions for a controller-less grid"

import testgrid

######################################
# concrete types of nodes for parser #
######################################

class RemoteNode(testgrid.server.remote.Node): pass

class DebianNode(testgrid.server.debian.Node): pass

##########
# client #
##########

class Client(object):

	def __init__(self, name = "grid", ini = "~/grid.ini"):
		self.grid = testgrid.server.parser.parse_grid(name, ini, __name__)
		self.sessions = {}

	def list_sessions(self):
		return self.sessions.values()

	def create_session(self, key = None):
		session = testgrid.server.model.Session(
			grid = self.grid,
			subnet = None,
			key = key) # FIXME subnet
		self.sessions[session.key] = session
		return session

	def delete_session(self, key):
		raise NotImplementedError()
