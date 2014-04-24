# copyright (c) 2013-2014 smartjog, released under the GPL license.

"handle sqlite3 database management"

import sqlite3
import sys
import os
import unittest
import inspect
import testgrid

class DatabaseError(Exception): pass

class Database(object):

    def __init__(self, dbpath = "TestGrid.db", script_path = "testgrid/testgrid.sql"):
        self.dbpath = dbpath
        self.script_path = script_path
        self.con = None
        self.database_init()

    def database_init(self):
        "load existing database or creates a new database using script_path"
        if os.path.exists(self.dbpath):
            self.con = sqlite3.connect(self.dbpath)
            self.db = self.con.cursor()
        else:
            self.create_database()

    def create_database(self):
        "tables creation"
        try:
            self.con = sqlite3.connect(self.dbpath)
            self.db = self.con.cursor()
            with open(self.script_path , 'r') as f:
                for line in f:
                    self.db.execute(line)
                    self.con.commit()
        except sqlite3.Error as  e:
            if self.con:
                self.con.rollback()
            raise DatabaseError("error creating database: %s" % e)

    def close(self):
        "close database connection"
        if self.con:
            self.con.close()

    def __del__(self):
        self.close()

    def dump(self):
        self.db.execute("SELECT * FROM Nodes")
        res = self.db.fetchall()
        print "Nodes\n", res
        self.db.execute("SELECT * FROM NodesAttributes")
        res = self.db.fetchall()
        print "NodesAttribute\n",res
        self.db.execute("SELECT * FROM Sessions")
        res = self.db.fetchall()
        print "Sessions\n", res
        self.db.execute("SELECT * FROM Plans")
        res = self.db.fetchall()
        print "Plans" , res
        self.db.execute("SELECT * FROM Packages")
        res = self.db.fetchall()
        print "Packages\n", res
        self.db.execute("SELECT * FROM Subnets")
        res = self.db.fetchall()
        print "Subnets\n", res

# Nodes

    def add_node(self, node):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("INSERT INTO Nodes(typename, name, modulename) VALUES (?, ?, ?)",
                            (type(node).__name__ , node.name, type(node).__module__))
            node.id = int(self.db.lastrowid)
            self.con.commit()
            args, varargs, kwargs, defaults = inspect.getargspec(node.__init__)
            for arg in args[1:]:
                self.db.execute("INSERT INTO NodesAttributes(key, value, node_id) VALUES(?, ?, ?)", 
                                (arg, str(getattr(node, arg)), node.id))
            self.con.commit()
        except sqlite3.Error as e:
            self.con.rollback()
            raise DatabaseError("error while adding node %s: %s" % (node.name, e))

    def remove_node(self, node):
        try:
            self.db.execute("DELETE FROM Nodes WHERE id = ?", (node.id,))
            if self.db.rowcount:
                self.db.execute("DELETE FROM Plans WHERE node_id = ?", (node.id,))
                self.db.execute("DELETE FROM NodesAttributes WHERE node_id = ?" ,(node.id,))
                self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error while removing node %s: %s" % (node.name, e))

    def quarantine_node(self, node, exc):
        try:
            self.db.execute("UPDATE Nodes SET is_quarantined = ?, error = ? WHERE id = ?",
                            (1, str(exc), node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error setting node %s to quarantined: %s" % (node.name, e))

    def get_quarantine_reason(self, node):
        self.db.execute("SELECT error FROM Nodes WHERE id = ?", (node.id,))
        (error,) = self.db.fetchone()
        return str(error)

    def rehabilitate_node(self, node):
        try:
            self.db.execute("UPDATE Nodes SET is_quarantined = ? WHERE id = ?",
                            (False, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error rehabilitate node %s: %s" % (node.name, e))

    def set_node_transient(self, node):
        try:
            self.db.execute("UPDATE Nodes SET is_transient = ? WHERE id = ?",
                            (1, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error setting node %s to quarantined: %s" % (node.name, e))

    def create_node(self, index, typename, modulename):
        "creates node object using table Nodes row"
        arg = {}
        is_transient = None
        is_quarantined = None
        self.db.execute("SELECT key, value FROM NodesAttributes WHERE node_id = ?" , (index,))
        result = self.db.fetchall()
        try:
            cls = testgrid.parser.get_subclass(typename, testgrid.model.Node, modulename)
        except Exception as e:
            raise Exception("database create node: %s" % e)
        for item in result:
            key, value = item
            arg[key] = str(value)
        try:
            node = cls(**arg)
        except Exception as e:
            args, varargs, kwargs, defaults = inspect.getargspec(cls.__init__)
            raise(Exception("fail class %s" % str(cls)))
        node.id = int(index)
        return node

    def get_nodes(self):
        nodes = []
        self.db.execute("SELECT id, typename, modulename FROM Nodes")
        res = self.db.fetchall()
        for index, typename, modulename in res:
            node = self.create_node(index, typename, modulename)
            nodes.append(node)
        return nodes

    def is_quarantined(self, node):
        self.db.execute("SELECT is_quarantined FROM Nodes WHERE id = ?",
                        (node.id,))
        (is_quarantined, )  = self.db.fetchone()
        return bool(is_quarantined)

    def is_transient(self, node):
        self.db.execute("SELECT is_transient FROM Nodes WHERE id = ?",
                        (node.id,))
        (is_transient, )  = self.db.fetchone()
        return bool(is_transient)

# Table Subnets

    def create_subnet(self, id, typename, id_string, modulename):
        "creates subnet object using table Subnets row"
        cls = testgrid.parser.get_subclass(str(typename), testgrid.model.Subnet, modulename)
        subnet = cls(id_string)
        subnet.db_id = int(id)
        return subnet

    def get_subnets(self):
        subnets = []
        self.db.execute("SELECT id, typename, id_string, modulename FROM Subnets")
        res = self.db.fetchall()
        for id, typename, id_string, modulename in res:
            subnet = self.create_subnet(id, typename, id_string, modulename)
            subnets.append(subnet)
        return subnets

    def add_subnet(self, subnet):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("INSERT INTO Subnets(typename, id_string, modulename) VALUES(?, ?, ?)", (type(subnet).__name__, subnet.id, type(subnet).__module__))
            subnet.db_id = int(self.db.lastrowid)
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error adding subnet: %s" % e)

    def remove_subnet(self, subnet):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.con.execute("DELETE FROM Subnets WHERE id = ?", (subnet.db_id,))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error adding subnet: %s" % e)

    def allocate_subnet(self):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.con.execute("SELECT id, typename, id_string, modulename FROM Subnets WHERE used = 0")
            res = self.db.fetchone()
            if not res:
                return testgrid.model.SubnetPoolExhaustedError()
            id, typename, id_string, modulename = res
            subnet = self.create_subnet(id, typename, id_string, modulename)
            self.db.execute("UPDATE Subnets SET used = 1 WHERE id = ?", (id,))
            return subnet
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error allocating  subnet: %s" % e)

# Table Sessions

    def get_sessions(self, grid):
        sessions = []
        self.db.execute("SELECT id, typename, username, name, subnet_id, modulename FROM Sessions")
        res = self.db.fetchall()
        for index, typename, username, name, subnet_id, modulename in res:
            try:
                session_cls = testgrid.parser.get_subclass(typename, testgrid.model.Session, modulename) 
            except Exception as e:
                raise Exception("database get session cls: %s" % e)
            session = session_cls(self, grid, str(username), str(name))
            session.id = int(index)
            session.plan = self.get_plans(session)
            if subnet_id:
                db.execute("SELECT typename, id_string, modulename FROM Subnets WHERE id = ?", (subnet_id) )
                subnet_typename, id_string, modulename_subnet = db.fetchone()
                session.subnet = self.create_subnet(subnet_id, subnet_typename, id_string, modulename_subnet)
            sessions.append(session)
        return sessions

    def add_session(self, session):
        try:

            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            if not session.subnet:
                subnet_id = None
            else:
                subnet_id = session.subnet.db_id
            self.db.execute("INSERT INTO Sessions(typename, username, name, subnet_id, modulename) VALUES(?, ?, ?, ?, ?)",
                            (type(session).__name__, session.username, session.name, subnet_id, type(session).__module__))
            session.id = int(self.db.lastrowid)
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error opening session username: %s, name: %s :%s" \
                                    % (session.username, session.name, e))

    def remove_session(self, session):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("SELECT * FROM Plans WHERE session_id = ?", (session.id,))
            res = self.db.fetchall()
            self.db.execute("SELECT package_id FROM Plans WHERE session_id = ?", (session.id,))
            res = self.db.fetchall()
            for package_id in res:
                self.remove_package(package_id)
            self.db.execute("DELETE FROM Plans WHERE session_id = ?", (session.id,))
            self.db.execute("DELETE FROM Sessions WHERE id = ?", (session.id,))
            if session.subnet:
                self.db.execute("UPDATE Subnets SET used = 0 WHERE id = ?", (session.subnet.db_id,))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error closing session username: %s, name: %s :%s" \

                                % (session.username, session.name, e))

    def session_exist(self, session):
        if not hasattr(session, "id"):
            return False
        self.db.execute("SELECT * FROM Sessions WHERE id = ?", (session.id,))
        res = self.db.fetchone();
        #print "sessison exist",  res, not res
        if res:
            return True
        return False

# Table Plans

    def add_plan(self, session, plan):
        try:
            pkg, node = plan
            if not pkg:
                self.db.execute("INSERT INTO Plans(session_id, node_id, package_id) VALUES(?, ?, ?)", \
                                    (session.id, node.id, None))
            else:
                self.add_package(pkg)
                self.db.execute("INSERT INTO Plans(session_id, node_id, package_id) VALUES(?, ?, ?)", \
                                    (session.id, node.id, pkg.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error adding plan  session username:%s, name: %s , node: %s : %s" \

                                % (session.username, session.name, node.name, e))

    def remove_pair(self, session, node , pkg):
        try:
            if (pkg):
                self.remove_package(pkg.id)
                self.db.execute("DELETE FROM Plans WHERE session_id = ? AND node_id = ? AND package_id = ?",
                                (session.id, node.id, pkg.id))
            else:
                self.db.execute("DELETE FROM Plans WHERE session_id = ? AND node_id = ?",
                                (session.id, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error removing pair session username:%s, name: %s , node: %s : %s" \
                                    % (session.username, session.name, node.name, e))

    def remove_plan(self, session, node):
        try:
            self.db.execute("SELECT package_id FROM Plans WHERE session_id = ? AND node_id = ?",\
                                (session.id, node.id))
            package_id = self.db.fetchall()
            for  id, in package_id:
                self.remove_package(id)
            self.db.execute("DELETE FROM Plans WHERE session_id = ? AND node_id = ?",
                            (session.id, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error removing plan session username:%s, name: %s , node: %s : %s" \
                                    % (session.username, session.name, node.name, e))

    def get_plans(self, session):
        plan = []
        self.db.execute("SELECT node_id, package_id FROM Plans WHERE session_id = ?", (session.id,))
        res = self.db.fetchall()
        for node_id, package_id in res:
            if package_id:
                package = self.get_package(package_id)
            else:
                package = None
            self.db.execute("SELECT typename, modulename FROM Nodes WHERE id = ?", (node_id,))
            typename, modulename =  self.db.fetchone()
            node = self.create_node(node_id, typename, modulename)
            plan.append((package, node))
        return plan

# Table Package

    def get_package(self, package_id):
        self.db.execute("SELECT typename, version, name, modulename FROM Packages WHERE id = ?", (package_id,))
        res = self.db.fetchone()
        if not res:
            return None
        typename, version, name, modulename = res
        try:
            package_cls = testgrid.parser.get_subclass(typename, testgrid.model.Package, modulename)
        except Exception as e:
            raise Exception("database get package cls: %s" % e)
        if version:
            pkg = package_cls(str(name), str(version))
        else:
            pkg = package_cls(str(name), None)
        pkg.id = int(package_id)
        return pkg

    def add_package(self, package):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("INSERT INTO Packages(typename, name, version, modulename) VALUES(?, ?, ?, ?) ", 
                            (type(package).__name__, package.name, package.version, type(package).__module__))
            package.id = int(self.db.lastrowid)
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError(e)

    def remove_package(self, package_id):
        try:
            self.db.execute("DELETE FROM Packages WHERE id = ?", (package_id,))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError(e)

##############
# unit tests #
##############

class TestDatabase(Database):
     def __init__(self):
          super(TestDatabase, self).__init__()

class SelfTest(unittest.TestCase):
     def test_table_creation(self):
          hdl = Database()
