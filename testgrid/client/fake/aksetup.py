import testgrid.server

class Package(testgrid.server.model.Package):

	def __init__(self, name, version):
		self.name = name
		self.version = version
