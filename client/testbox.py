import server

class Session(server.model.Session):

	def __init__(self, key = None):
		super(Session, self).__init__(
			grid = server.testbox.Grid(),
			subnet = None,
			key = key)
