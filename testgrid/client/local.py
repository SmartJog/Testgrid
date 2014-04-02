# copyright (c) 2013-2014 smartjog, released under the GPL license.

"client managing sessions for a controller-less grid"

import server

class Client(object):

	def __init__(self, name = "grid", ini = "~/grid.ini"):
		self.grid = server.parser.parse_grid(name, ini)
		self.sessions = {}

	def list_sessions(self):
		return self.sessions.values()

	def create_session(self, key = None):
		session = server.model.Session(
			grid = self.grid,
			subnet = None,
			key = key) # FIXME subnet
		self.sessions[session.key] = session
		return session

	def delete_session(self, key):
		raise NotImplementedError()
