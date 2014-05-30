# copyright (c) 2013-2014 smartjog, released under the GPL license.

"persistent grid implementation"

import unittest, weakref, inspect, random, shutil, string, os

from testgrid import model, database

class Session(model.Session):

    def __init__(self, db, gridref, name, user, subnet = None):
        super(Session, self).__init__(
            gridref = gridref,
            name = name,
            user = user,
            subnet = subnet)
        self.db = db
        self.plan = []

    def __iter__(self):
        self.plan = self.db.get_plans(self)
        for _, node in self.plan:
            yield node

    def __contains__(self, node):
        for n in self:
            if n == node:
                return True
        return False

    def remove_node(self, node):
        if node in self:
            self.db.remove_plan(self, node)

    def allocate_node(self, pkg = None, **opts):
        node = super(Session, self).allocate_node(pkg, **opts)
        self.db.add_plan(self, (None, node))
        return node

    def _release_pair(self, pkg ,node):
        super(Session, self)._release_pair(pkg ,node)
        self.db.remove_pair(self, node, pkg)

    def undeploy(self):
        self.plan = self.db.get_plans(self)
        super(Session, self).undeploy()

    def deploy(self, packages):
        try:
            plan = super(Session, self).deploy(packages)
            for p in plan:
                self.db.add_plan(self, p)
            return plan
        except:
            raise

class Nodes(object):

    def __init__(self, db):
        self.db = db

    def __iter__(self):
        for node in self.db.get_nodes():
            yield node

    def __contains__(self, node):
        for n in self:
            if n == node:
                return True
        return False

    def __len__(self):
        return self.db.count_nodes()

    def append(self, node):
        self.db.add_node(node)

    def remove(self, node):
        self.db.remove_node(node)

class Subnets(object):

    def __init__(self, db):
        self.db = db

    def __iter__(self):
        for subnet in self.db.get_subnets():
            yield subnet

    def __contains__(self, subnet):
        if subnet:
            for s in self:
                if s.id == subnet.id:
                    return True
        return False

    def __len__(self):
        return self.db.count_subnets()

    def pop(self):
        subnet = self.db.allocate_subnet()
        return subnet

    def append(self, subnet):
        if subnet:
            self.db.add_subnet(subnet)

    def remove(self, subnet):
        self.db.remove_subnet(subnet)

class Sessions(object):

    def __init__(self, db, gridref):
        self.db = db
        self.gridref = gridref

    def __iter__(self):
        for session in self.db.get_sessions(self.gridref):
            yield session

    def __contains__(self, session):
        return self.db.session_exist(session)

    def __len__(self):
        return self.db.count_sessions()

    def append(self, session):
        self.db.add_session(session)

    def remove(self, session):
        self.db.remove_session(session)

class Grid(model.Grid):

    def __init__(self, name, dbpath = "~/testgrid.db"):    
        self.db = database.Database(dbpath = dbpath)
        super(Grid, self).__init__(
            name = name,
            nodes = Nodes(db = self.db),
            subnets = Subnets(db = self.db),
            sessions = Sessions(db = self.db, gridref = weakref.ref(self)))

    def quarantine(self, node, reason):
        super(Grid, self).quarantine(node = node, reason = reason)
        self.db.quarantine_node(node = node, reason = reason)

    def rehabilitate(self, node):
        super(Grid, self).rehabilitate(node)
        self.db.rehabilitate_node(node)

    def is_quarantined(self, node):
        return self.db.is_quarantined(node)

    def get_quarantine_reason(self, node):
        return self.db.get_quarantine_reason(node)

    def _set_transient(self, node):
        self.db.set_node_transient(node)

    def _is_transient(self, node):
        return self.db.is_transient(node)

    def open_session(self, name, user):
        session = super(Grid, self).open_session(
            name = name,
            user = user,
            session_cls = Session,
            db = self.db)
        return session

    def __del__(self):
        self.db.close()

    def close(self):
        super(Grid, self).close()
        self.db.close(remove_storage = True)

################
# test doubles #
################

PATH = "/tmp/ptest"

def loadobj(path, default):
    if not os.path.exists(path):
        return default
    else:
        return eval(open(path, "r").read())

def saveobj(obj, path):
    open(path, "w+").write(repr(obj))

class FList(object):
    "file-backed list"

    def __init__(self, basename):
        self.path = os.path.join(PATH, basename)

    def __str__(self):
        return "%s" % loadobj(self.path, [])

    def __len__(self):
        return len(loadobj(self.path, []))

    def __iter__(self):
        for item in loadobj(self.path, []):
            yield item

    def append(self, item):
        lst = loadobj(self.path, [])
        lst.append(item)
        saveobj(lst, self.path)

    def remove(self, item):
        lst = loadobj(self.path, [])
        lst.remove(item)
        saveobj(lst, self.path)

    def __contains__(self, item):
        lst = loadobj(self.path, [])
        return item in lst

class FBool(object):
    "file-backed boolean"

    def __init__(self, basename, value):
        self.path = os.path.join(PATH, basename)
        saveobj(value, self.path)

    def set_false(self):
        saveobj(False, self.path)

    def set_true(self):
        saveobj(True, self.path)

    def __nonzero__(self):
        return loadobj(self.path, [])

class FakeNode(database.Storable, model.FakeNode):

    def __init__(self, name):
        super(FakeNode, self).__init__(name = name)
        self.terminated = FBool("terminated.%s.dat" % self, False)
        self.installed = FList("installed.%s.dat" % self)
        self.subnets = FList("subnets.%s.dat" % self)

    def terminate(self):
        self.terminated.set_true()

    def marshall(self):
        return "%s" % {"name": self.name}

    @classmethod
    def unmarshall(cls, data):
        return (cls)(**eval(data))

class TempGrid(Grid):

    def __init__(self, name, nodes = None, subnets = None, sessions = None):
        basename = "".join(random.choice(string.lowercase) for i in xrange(8)) + ".db"
        dbpath = os.path.join(PATH, basename)
        super(TempGrid, self).__init__(name = name, dbpath = dbpath)
        if nodes:
            for node in nodes:
               self.nodes.append(node)
        if subnets:
            for subnet in subnets:
               self.subnets.append(subnet)

    def __del__(self):
        self.db.close(remove_storage = True)

class FakeGrid(TempGrid):
    "generative grid of fake nodes"

    ref = 0

    def create_node(self, **opts):
        node = FakeNode("tnode%i" % FakeGrid.ref)
        FakeGrid.ref += 1
        return node

    def terminate_node(self, node):
        node.terminate()

#########
# tests #
#########

class SelfTest(model.SelfTest):

    cls = {
        "gengrid": FakeGrid,
        "grid": TempGrid,
        "node": FakeNode,
        "pkg": model.FakePackage,
    }

    timeout = 20

    def setUp(self):
        if not os.path.exists(PATH):
            os.mkdir(PATH)

    def tearDown(self):
        shutil.rmtree(PATH)

    def test_node_persistency(self):
        # populate grid
        nodes, _, grid, _ = self.mkenv(nb_nodes = 10, nb_packages = 0)
        for node in nodes:
            self.assertIn(node, grid, "pre: %s not in %s" % (node, grid))
        dbpath = grid.db.dbpath
        # restore grid, assert nodes are present
        grid = TempGrid(name = "grid2", dbpath = dbpath)
        for node in nodes:
            self.assertIn(node, grid, "post: %s not in %s" % (node, grid))

    def test_session_persistency(self):
        _, _, grid, session = self.mkenv(nb_nodes = 0, nb_packages = 0)
        session.terminate() # close current session
        session = grid.open_session(name = "foo") # create new one
        self.assertIn(session, grid.sessions)
        dbpath = grid.db.dbpath
        grid = TempGrid(name = "grid2", dbpath = dbpath)
        for i, session in  enumerate(grid.sessions):
            if i == 0:
                self.assertEqual(session.name, "foo")
            else:
                raise Exception("unexpected session '%s'" % session)

    def test_subnet_persistency(self):
        subnet = model.Subnet("669")
        grid = TempGrid(name = "mygrid", subnets = [subnet])
        session = grid.open_session(name = "mysession")
        try:
            self.assertEqual(session.subnet, subnet)
        except:
            grid.db.dump()
            raise
        dbpath = grid.db.dbpath
        grid = TempGrid(name = "myothergrid", dbpath = dbpath)
        session = grid.open_session(name = "mysession")
        self.assertEqual(session.subnet, subnet)

    def test_plan_persistency(self):
        nodes, packages, grid, session = self.mkenv(nb_nodes = 20, nb_packages = 20)
        session = grid.open_session(name = "foo")
        plan = session.deploy(packages)
        dbpath = grid.db.dbpath
        grid = TempGrid(name = "grid2", dbpath = dbpath)
        session = grid.open_session(name = "foo")
        for pkg, node in plan:
            self.assertIn(node, session)
            self.assertTrue(node.is_installed(pkg))

if __name__  == "__main__": unittest.main(verbosity = 2)
