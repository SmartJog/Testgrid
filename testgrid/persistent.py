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
                self.hdl.remove_pair(self, node, pkg)

        def undeploy(self):
                self.plan = self.hdl.get_plans(self)
                super(Session, self).undeploy()

        def deploy(self, packages):
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
                for node in self.hdl.get_nodes():
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
                return self.hdl.session_exist(session)

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

        def __init__(self, name, dbpath="testgrid.db", *args, **kwargs):
                super(Grid, self).__init__(name, *args, **kwargs)
                nodes = self.nodes
                subnets = self.subnets
                self.hdl = testgrid.database.Database(dbpath = dbpath)
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

        def __del__(self):
                self.hdl.close()

##############
# unit tests #
##############

class FakePackage(testgrid.model.FakePackage):

        def __repr__(self):
                return "%s(%s, %s)" % (type(self).__name__, repr(self.name), repr(self.version))

        def __eq__(self, other):
                if self.name ==  other.name:
                        return True
                return False

        def __ne__(self, other):
                return not (self == other)

        def read_installed(self, node):
                if not os.path.exists("db_test/installed_%s.dat" % node.name):
                        return []
                else:
                        return eval(open("db_test/installed_%s.dat" % node.name, "r").read())

        def write_installed(self, node, installed):
                open("db_test/installed_%s.dat" % node.name, "w+").write(repr(installed))

        def install(self, node):
                assert not node.terminated
                assert not node.is_installed(self), "%s: %s: already installed" % (node, self)
                installed = self.read_installed(node)
                installed.append(self)
                self.write_installed(node, installed)

        def uninstall(self, node):
                assert not node.terminated
                assert node.is_installed(self), "%s: %s: not yet installed" % (node, self)
                installed = self.read_installed(node)
                installed.remove(self)
                self.write_installed(node, installed)

        def is_installed(self, node):
                assert not node.terminated
                installed = self.read_installed(node)
                return self in installed

        def is_installable(self, node):
                assert not node.terminated
                return True

class FakeNode(testgrid.model.FakeNode):

        # store .terminated
        # store .subnets

        def __init(self, name):
                super(FakeNode, self).__init__(name = name)

        def __eq__(self, other):
                if type(self) == type(other):
                        if self.name == other.name:
                                return True
                return False

        def __ne__(self, other):
                return not (self == other)

        def write_subnets(self, subnets):
                open("db_test/installed_%s.dat" % self.name, "w+").write(repr(subnets))

        def write_terminated(self, state):
                open("db_test/terminated_%s.dat" % self.name, "w+").write(repr(state))

        def read_terminated(self):
                if not os.path.exists("db_test/terminated_%s.dat" % node.name):
                        return False
                else:
                        return eval(open("db_test/terminated_%s.dat" % node.name, "r").read())

        def read_subnets(self):
                if not os.path.exists("db_test/subnets_%s.dat" % node.name):
                        return []
                else:
                        return eval(open("db_test/subnets_%s.dat" % node.name, "r").read())

class FakePackagePersistent(testgrid.model.FakePackage):

        def get_typename(self):
                return "FakePackagePersistent"

class FakeSubnet(testgrid.model.Subnet): pass

import random
import string

class TempGrid(Grid):

        def __init__(self, name, dbpath = None):
                if not dbpath:
                        dbpath = "".join(random.choice(string.lowercase) for i in xrange(8)) + ".db"
                super(TempGrid, self).__init__(name = name, dbpath = dbpath)

        def get_nodes(self):
                for node in self:
                        yield node

        def get_database_path(self):
                return self.hdl.dbpath

        def __del__(self, remove = True):
                super(TempGrid, self).__del__()
                if remove and os.path.exists(self.hdl.dbpath):
                        os.remove(self.hdl.dbpath)

class SelfTest(testgrid.model.SelfTest):

       grid_cls = TempGrid
       node_cls = FakeNode
       pkg_cls = FakePackage

       timeout = 20

       def setUp(self):
               if not os.path.exists("db_test"):
                       os.mkdir("db_test")

       def tearDown(self):
               if os.path.exists("db_test"):
                       shutil.rmtree("db_test/")

       @staticmethod
       def mkenv(nb_nodes, nb_packages):
               "create test objects"
               nodes = tuple(FakeNode("node%i" % i) for i in xrange(nb_nodes))
               packages = tuple(FakePackage("pkg%i" % i, "1.0") for i in xrange(nb_packages))
               subnets = [FakeSubnet("vlan14")]
               grid = TempGrid(name = "grid")
               for node in nodes:
                       grid.add_node(node)
               for subnet in subnets:
                       grid.add_subnet(subnet)
               session = grid.open_session()
               return (nodes, packages, grid, session)

       def test_persistent_nodes(self):
               "test add, remove node persistency"
               #perform operation with first grid
               nodes, pkg, grid, session = self.mkenv(nb_nodes = 2, nb_packages = 0)
               self.assertIn(nodes[0], grid.get_nodes())
               grid.remove_node(nodes[0])
               self.assertNotIn(nodes[0], grid.get_nodes())
               dbpath = grid.get_database_path()
               grid.__del__(False)
               #perform operation with second  grid using same db
               grid = TempGrid(name = "second grid", dbpath = dbpath)
               self.assertIn(nodes[-1], grid.get_nodes())
               del grid

       def test_persistent_sessions(self):
               "test persistent session persistency, assert anonymous session is removed after being closed"
               #perform operation with first grid
               nodes, pkg, grid, session = self.mkenv(nb_nodes = 0, nb_packages = 0)
               self.assertIn(session , grid.get_sessions())
               session.close()
               self.assertNotIn(session , grid.get_sessions())
               session = grid.open_session("persistent", "test")
               dbpath = grid.get_database_path()
               grid.__del__(False)
               grid = TempGrid(name = "persistentGridsecond", dbpath = dbpath)
               self.assertIn(session, grid.get_sessions())
               del grid

       def test_persistent_plan(self):
               "test plan persistency associate to specific session"
               #perform operation with first grid
               nodes, pkg, grid, session = self.mkenv(nb_nodes = 2, nb_packages = 0)
               session_persistent = grid.open_session("persistent", "test")
               allocated_node = session.allocate_node()
               self.assertIn(allocated_node, session)
               grid.remove_node(allocated_node)
               self.assertNotIn(allocated_node, session)
               allocated_node = session_persistent.allocate_node()
               self.assertRaises(testgrid.model.NodePoolExhaustedError,session.allocate_node)
               dbpath = grid.get_database_path()
               grid.__del__(False)
               #perform operation with second  grid using same db
               grid = TempGrid(name = "persistentGrid", dbpath = dbpath)
               session_persistent = grid.open_session("persistent", "test")
               self.assertRaises(testgrid.model.NodePoolExhaustedError, session_persistent.allocate_node)
               self.assertIn(allocated_node , session_persistent)
               del grid

       def test_deploy(self):
               grid = TempGrid(name = "persistentGrid")
               node = testgrid.persistent.FakeNode("fake node")
               grid.add_node(node)
               grid.set_node_transient(node)
               self.assertEqual(grid.is_transient(node), True)
               session = grid.open_session("persistent", "test")
               package = FakePackagePersistent("test")
               plan = session.deploy((package,))
               self.assertIn(node, session)
               session.undeploy()
               self.assertNotIn(node, session)

       def test_node_creation(self):pass

if __name__  == "__main__": unittest.main(verbosity = 2)
