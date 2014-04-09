import unittest
#import testgrid
import database
import model
import inspect

class persistentSession(model.Session):
	def __init__(self, hdl , grid, username, name = None, subnet = None):
		self.hdl = hdl
		self.grid = grid
		super(persistentSession, self).__init__(grid, username, name, subnet)

	def __iter__(self):
		self.plan = self.hdl.get_plans(self)
		for _, node in self.plan:
			yield node

	def allocate_node(self, pkg = None, **opts):
		node = super(persistentSession, self).allocate_node(pkg, **opts)
		self.hdl.add_plan(self, (None, node))

	def _release_pair(self, pkg ,node):
		super(persistentSession, self)._release_pair(pkg ,node)
		self.hdl.remove_plan(self, node, pkg)

	def deploy(self, packages):
		plan = super(persistentSession, self).deploy(packages)
		self.hdl.add_plan(self, plan)
		
	def __del__(self):pass
	#def undeploy(self):
	def close(self):
		self.hdl.close_session(self)
		super(persistentSession, self).close()

class persistentGrid(model.Grid):
        def __init__(self, name, databasePath="testgrid.db", scriptSqlPath="testgrid/testgrid.sql", *args, **kwargs):
		self.hdl = database.Database(databasePath=databasePath, scriptSqlPath=scriptSqlPath)
		nodes = self.hdl.get_nodes()
		sessions = self.get_sessions() 
		super(persistentGrid, self).__init__(name, nodes, sessions=sessions, *args, **kwargs)
		

        def add_node(self, node):
		self.hdl.add_node(node)
		super(persistentGrid, self).add_node(node)

        def remove_node(self, node):
		super(persistentGrid, self).remove_node(node)
		self.hdl.remove_node(node)


        def quarantine_node(self, node, exc):
		super(persistentGrid, self).quarantine_node(node, exc)
		self.hdl.quarantine_node(node, exc)

        def rehabilitate_node(self, node):
		super(persistentGrid, self).rehabilitate_node(node)
		self.hdl.rehabilitate_node(node)

	def is_quarantined(self, node):
		if hasattr(node, "is_quarantined"):
			self.hdl.is_quarantined(node)
		super(persistentGrid, self).is_quarantined(node)
	
	def is_transient(self, node):
		if hasattr(node, "is_transient"):
			self.hdl.is_transient(node)
		super(persistentGrid, self).is_transient(node)

        def _get_allocated_nodes(self):
		self.sessions = self.get_sessions()
		for node in super(persistentGrid, self)._get_allocated_nodes():
			yield node

        def _get_available_nodes(self):
		self.nodes = self.hdl.get_nodes()
		for node in super(persistentGrid, self)._get_available_nodes():
			yield node
        
        
	def get_sessions(self):
		return self.hdl.get_sessions(persistentSession, self)

	def open_session(self, username = None, name = None):
		username = username or getpass.getuser()
		for session in self.sessions:
			if session.name == name:
				assert session.username == username, "%s: access violation" % name
				break
		else:
			session = persistentSession(hdl = self.hdl,
						    grid = self,
						    username = username,
						    name = name,
						    subnet = self._allocate_subnet())
			self.hdl.open_session(session)
			self.sessions.append(session)	
		return session



##############
# unit tests #
##############

class SelfTest(unittest.TestCase):
    def test_persistent_nodes(self):
	    pg = persistentGrid(name=" persistentGrid", databasePath="persistentNodes.db")
	    node = model.FakeNode("fake node")
	    pg.add_node(node)
	    secondpg = persistentGrid(name=" persistentGridsecond")
	    pg.remove_node(node)

    def test_persistent_sessions(self):
	    pg = persistentGrid(name=" persistentGrid", databasePath="persistentSessions.db")
	    pg.open_session("persistent", "test")
	    secondpg = persistentGrid(name=" persistentGridsecond")

    def test_persistent_plan(self):
	    pg = persistentGrid(name=" persistentGrid", databasePath="persistentPlan.db")
	    node = model.FakeNode("fake node")
	    pg.add_node(node)
	    session = pg.open_session("persistent", "test")
	    allocated_node = session.allocate_node()
	    allocated_node_sec = session.allocate_node()
	    print allocated_node_sec

if __name__  == "__main__": unittest.main(verbosity = 2)
