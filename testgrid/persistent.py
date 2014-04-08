import unittest
#import testgrid
import database
import model
import inspect

class persistentSession(model.Session):
	def __init__(self, hdl , grid, username, name = None, plan = None, subnet = None):
		super(persistentSession, self).__init__(gird, username, name, plan, subnet)

	def allocate_node(self, pkg = None, **opts):pass
	def release_node(self, node):pass

	def close(self):pass

class persistentGrid(model.Grid):
        def __init__(self, name, databasePath="testgrid.db", scriptSqlPath="testgrid/testgrid.sql", *args, **kwargs):
		self.hdl = database.Database(databasePath=databasePath, scriptSqlPath=scriptSqlPath)
		nodes = self.hdl.get_nodes()
		super(persistentGrid, self).__init__(name, nodes, *args, **kwargs)
		

        def add_node(self, node):
		self.hdl.add_node(node)
		super(persistentGrid, self).add_node(node)
		

        def remove_node(self, node):
		self.hdl.remove_node(node)
		super(persistentGrid, self).remove_node(node)
		

        def quarantine_node(self, node, exc):pass
        def rehabilitate_node(self, node):pass
        def is_quarantined(self, node):pass
        def _get_allocated_nodes(self):pass
        def _get_available_nodes(self):pass
        def is_available(self, node):pass
        def is_allocated(self, node):pass
        def get_sessions(self):pass
        def open_session(self, username = None, name = None):pass
        def _close_session(self, session):pass
        def get_deployment_plan(self, packages):pass
	def open_session(self, username = None, name = None):pass



##############
# unit tests #
##############

class SelfTest(unittest.TestCase):
    def test_persistent(self):
	    pg = persistentGrid(name=" persistentGrid")
	    node = model.FakeNode("fake node")
	    pg.add_node(node)
	    secondpg = persistentGrid(name=" persistentGridsecond")
	    print secondpg.nodes
	    pg.remove_node(node)
	    print secondpg.nodes

if __name__  == "__main__": unittest.main(verbosity = 2)
