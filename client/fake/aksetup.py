import server

class Package(server.model.Package):

	def __init__(self, name, version):
		self.name = name
		self.version = version
