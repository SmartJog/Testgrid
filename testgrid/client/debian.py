import testgrid.server

class Package(testgrid.server.model.Package):

	def __init__(self, name, version):
		self.name = name
		self.version = version


class Node(testgrid.server.model.Node):

	def __init__(self, hoststring):
		super(Node, self).__init__()
		self.hoststring = hoststring
