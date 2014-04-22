# copyright (c) 2013-2014 smartjog, released under the GPL license.

"persistent grid, store data in sqlite file"

import unittest
import inspect
import os
import shutil
import weakref
import testgrid

class Session(testgrid.model.Session):

        def __init__(self, hdl, gridref, username, name = None, subnet = None):
                super(Session, self).__init__(gridref, username, name, subnet)
                self.hdl = hdl
                self.plan = []

        def __iter__(self):
                self.plan = self.hdl.get_plans(self)
                for _, node in self.plan:
                        yield node

        def __contains__(self, node):
                for n in self:
                        if n == node:
                                return True
                return False

        def remove_node(self, node):
                if node in self:
                        self.hdl.remove_plan(self, node)

        def allocate_node(self, pkg = None, **opts):
                node = super(Session, self).allocate_node(pkg, **opts)
                self.hdl.add_plan(self, (None, node))
                return node

        def _release_pair(self, pkg ,node):
                super(Session, self)._release_pair(pkg ,node)
                self.hdl.remove_plan(self, node)
                #release pair

        def undeploy(self):
                self.plan = self.hdl.get_plans(self)
                super(Session, self).undeploy()

        def deploy(self, packages):
                #self.plan = self.hdl.get_plans(self)
                try:
                        plan = super(Session, self).deploy(packages)
                        for p in plan:
                                self.hdl.add_plan(self, p)
                        return plan
                except:
                        raise


        def close(self):
                super(Session, self).close()

class Nodes(object):

        def __init__(self, hdl):
                self.hdl = hdl

        def __iter__(self):
                nodes = self.hdl.get_nodes()
                for node in nodes:
                        yield node

        def __contains__(self, node):
                for n in self:
                        if n == node:
                                return True
                return False

        def __len__(self):
                size  = 0
                for n in self:
                        size = size + 1
                return size

        def append(self, node):
                self.hdl.add_node(node)

        def remove(self, node):
                self.hdl.remove_node(node)

class Subnets(object):

        def __init__(self, hdl):
                self.hdl = hdl

        def __iter__(self):
                for subnet in self.hdl.get_subnets():
                        yield subnet

        def __contains__(self, subnet):
                if subnet:
                        for s in self:
                                if s.id == subnet.id:
                                        return True
                return False

        def __len__(self):
                size  = 0
                for n in self:
                        size = size + 1
                return size

        def pop(self):
                subnet = self.hdl.allocate_subnet()
                return subnet

        def append(self, subnet):
                if subnet:
                        self.hdl.add_subnet(subnet)

        def remove(self, subnet):
                self.hdl.remove_subnet(subnet)

class Sessions(object):

        def __init__(self, hdl, gridref):
                self.hdl = hdl
                self.gridref = gridref

        def __iter__(self):
                sessions = self.hdl.get_sessions(self.gridref)
                for session in sessions:
                        yield session

        def __contains__(self, session):
                if not hasattr(session, "id"):
                        return False
                return True

        def __len__(self):
                size  = 0
                for n in self:
                        size = size + 1
                return size

        def append(self, session):
                self.hdl.add_session(session)

        def remove(self, session):
                self.hdl.remove_session(session)

class Grid(testgrid.model.Grid):

        def __init__(self, name, dbpath="testgrid.db",
                     script_path="testgrid/testgrid.sql", *args, **kwargs):
                super(Grid, self).__init__(name, *args, **kwargs)
                nodes = self.nodes
                subnets = self.subnets
                self.hdl = testgrid.database.Database(dbpath = dbpath, script_path = script_path)
                self.nodes = Nodes(hdl = self.hdl)
                self.subnets = Subnets(hdl = self.hdl)
                self.sessions = Sessions(hdl = self.hdl, gridref = weakref.ref(self))
                for n in nodes:
                        self.add_node(n)
                if subnets:
                        for s in subnets:
                                self.add_subnet(s)

        def add_subnet(self, subnet):
                self.subnets.append(subnet)

        def quarantine_node(self, node, exc):
                self.hdl.quarantine_node(node, exc)

        def set_node_transient(self, node):
                self.hdl.set_node_transient(node)

        def rehabilitate_node(self, node):
                self.hdl.rehabilitate_node(node)

        def is_quarantined(self, node):
                return self.hdl.is_quarantined(node)

        def get_quarantine_reason(self, node):
                return self.hdl.get_quarantine_reason(node)

        def is_transient(self, node):
                return self.hdl.is_transient(node)

        def open_session(self, username = None, name = None):
                session = super(Grid, self).open_session(
                        username = username,
                        name = name,
                        session_cls = Session,
                        hdl = self.hdl)
                return session


#        def is_available(self, node):
#                #if self.is_quarantined(node):
#                #        return False
#                for n in self._get_allocated_nodes():
#                        if n.id == node.id:
#                                return False
#                return True

#        def is_allocated(self, node):
#                for n in self._get_allocated_nodes():
#                        if n.id == node.id:
#                                return True
#                return False

        def __del__(self):
                self.hdl.close()

##############
# unit tests #
##############

class FakeSubnet(testgrid.model.Subnet):pass

class FakeNodePersistent(testgrid.model.FakeNode):

        def __init(self, name):
                super(FakeNode, self).__init__(name = name)

        def __eq__(self, other):
                if type(self) == type(other):
                        if self.name == other.name:
                                return True
                return False

class FakePackagePersistent(testgrid.model.FakePackage):

        def get_typename(self):
                return "FakePackagePersistent"

class Modeltest(testgrid.model.SelfTest):

       timeout = 2

       def setUp(self):
               if not os.path.exists("db_test"):
                       os.mkdir("db_test")

       def tearDown(self):
               shutil.rmtree("db_test/")

       @staticmethod
       def mkenv(nb_nodes, nb_packages):
               "create test objects"
               nodes = tuple(FakeNodePersistent("node%i" % i) for i in xrange(nb_nodes))
               packages = tuple(testgrid.model.FakePackage("pkg%i" % i, "1.0") for i in xrange(nb_packages))
               subnets = [FakeSubnet("vlan14")]
               grid = Grid(name = "grid", dbpath = "db_test/persistentModel.db" , subnets = subnets, nodes = nodes) # use a non-generative grid
               session = grid.open_session()
               return (nodes, packages, grid, session)

class SelfTest(unittest.TestCase):

        timeout = 2

        def setUp(self):
                if not os.path.exists("db_test"):
                        os.mkdir("db_test")

        def tearDown(self):
                shutil.rmtree("db_test/")

        def test_persistent_nodes(self):
                "test add , remove node persistency"
                #perform operation with first grid
                subnets = [FakeSubnet("vlan14")]
                pg = Grid(name = "persistentGrid", dbpath = "db_test/persistentNodes.db", subnets = subnets)
                node = testgrid.persistent.FakeNodePersistent("fake node")
                pg.add_node(node)
                node2 = testgrid.persistent.FakeNodePersistent("fake node2")
                pg.add_node(node2)
                self.assertEqual(len(pg.nodes), 2)
                pg.remove_node(node2)
                self.assertEqual(len(pg.nodes), 1)
                del pg
                #perform operation with second  grid using same db
                pg = Grid(name = "persistentGridsecond", dbpath = "db_test/persistentNodes.db")
                self.assertEqual(len(pg.nodes), 1)
                self.assertRaises(testgrid.model.UnknownNodeError, pg.remove_node, node2)
                del pg

        def test_persistent_sessions(self):
                "test persistent session persistency, assert anonymous session is removed after being closed"
                #perform operation with first grid
                subnets = [FakeSubnet("vlan14")]
                pg = Grid(name = "persistentGrid", dbpath = "db_test/persistentSessions.db", subnets = subnets)
                session = pg.open_session("persistent", "test")
                anonymous_session = pg.open_session("anonymous")
                sessions = pg.get_sessions()
                self.assertEqual(len(sessions), 2)
                anonymous_session.close()
                del pg
                #perform operation with second  grid using same db
                pg = Grid(name = "persistentGridsecond", dbpath = "db_test/persistentSessions.db")
                sessions = pg.get_sessions()
                self.assertEqual(len(sessions), 1)
                del pg

        def test_persistent_plan(self):
                "test plan persistency associate to specific session"
                #perform operation with first grid
                subnets = [FakeSubnet("vlan14")]
                pg = Grid(name = "persistentGrid", dbpath = "db_test/persistentPlan.db", subnets = subnets)
                node = testgrid.persistent.FakeNodePersistent("fake node")
                pg.add_node(node)
                session = pg.open_session("persistent", "test")
                allocated_node = session.allocate_node()
                self.assertRaises(testgrid.model.NodePoolExhaustedError,session.allocate_node)
                del pg
                #perform operation with second  grid using same db
                pg = Grid(name = "persistentGrid", dbpath = "db_test/persistentPlan.db")
                session = pg.open_session("persistent2", "test2")
                self.assertRaises(testgrid.model.NodePoolExhaustedError, session.allocate_node)
                pg.remove_node(allocated_node)
                del pg
                #check remove node persistency
                pg = Grid(name = "persistentGrid", dbpath = "db_test/persistentPlan.db")
                self.assertEqual(len(pg.nodes), 0)
                session = pg.open_session("persistent", "test")
                self.assertEqual(len(session.plan), 0)
                del pg

        def test_deploy(self):
                subnets = [FakeSubnet("vlan14")]
                pg = Grid(name = "persistentGrid", dbpath = "db_test/persistentPlan.db", subnets = subnets)
                node = testgrid.persistent.FakeNodePersistent("fake node")
                pg.add_node(node)
                pg.set_node_transient(node)
                self.assertEqual(pg.is_transient(node), True)
                session = pg.open_session("persistent", "test")
                package = FakePackagePersistent("test")
                plan = session.deploy((package,))
                self.assertIn(node, session)
                session.undeploy()
                self.assertNotIn(node, session)

if __name__  == "__main__": unittest.main(verbosity = 2)

