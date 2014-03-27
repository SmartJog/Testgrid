class Package(object):

	def __init__(self, name, version):
		self.name = name
		self.version = version


class Node(object):

	def __init__(self, hoststring):
		super(Node, self).__init__()
		self.hoststring = hoststring


