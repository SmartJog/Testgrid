import aksetup
import debian
import server

class FakeServiceManager(server.model.ServiceManager):

	is_running = lambda self, name: True

	get_version = lambda self, name: "16.3-1"

node = server.model.FakeNode()
node.service = FakeServiceManager()

grid = server.model.Grid(node) # non-generative grid

#grid = server.model.FakeGrid() # generative grid

class Session(server.model.Session):

	def __init__(self, key = None):
		super(Session, self).__init__(
			grid = grid,
			subnet = server.model.Subnet("fakesubnet"),
			key = key)
