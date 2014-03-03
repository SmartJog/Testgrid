import testgrid

class Hypervisor(object):

	def __init__(self, hoststring):
		self.hoststring = hoststring

	def load(self):
		raise NotImplementedError()

	def create_domain(self):
		raise NotImplementedError()

class HypervisorPool(object):

	def __init__(self, *hypervisors):
		self.hypervisors = hypervisors or ()

	def create_domain(self):
		hv = min(self.hypervisors, key = lambda hv: hv.load())
		return hv.create_domain()

class Domain(testgrid.Node): pass

class Grid(testgrid.Grid):
	"a playground-based grid is able to spawn nodes on-demand"

	def __init__(self):
		super(Grid, self).__init__()
		pg1 = Hypervisor("root@hkvm-pg-1.pg.fr.lan")
		pg2 = Hypervisor("root@hkvm-pg-1.pg.fr.lan")
		pg3 = Hypervisor("root@hkvm-pg-1.pg.fr.lan")
		pg4 = Hypervisor("root@hkvm-pg-1.pg.fr.lan")
		self.pg = HypervisorPool(pg1, pg2, pg3, pg4)

	create_node = lambda self, cls: self.pg.create_domain()
