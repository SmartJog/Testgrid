
import testgrid
import aksetup
import debian

class FakeServiceManager(testgrid.server.model.ServiceManager):

	is_running = lambda self, name: True

	get_version = lambda self, name: "16.3-1"

node = testgrid.server.model.FakeNode()
node.service = FakeServiceManager()

grid = testgrid.server.model.Grid(node) # non-generative grid

#grid = server.model.FakeGrid() # generative grid

class Session(testgrid.server.model.Session):

	def __init__(self, key = None):
		super(Session, self).__init__(
			grid = grid,
			subnet = testgrid.server.model.Subnet("fakesubnet"),
			key = key)
