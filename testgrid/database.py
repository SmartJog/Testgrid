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

    def __init__(self, dbpath = "TestGrid.db", script_path = "testgrid.sql"):
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
            self.con.rollback()
            raise DatabaseError("error creating database: %s" % e)

    def close(self):
        "close database connection"
        if self.con:
            self.con.close()

    def __del__(self):
        self.close()

# Nodes
    def add_node(self, node):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("INSERT INTO Nodes(typename, name) VALUES (?,?)", 
                            (node.__class__.__name__, node.name))
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
                #delete plan from session
                self.db.execute("DELETE FROM NodesAttributes WHERE node_id = ?" ,(node.id,))
                self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error while removing node %s: %s" % (node.name, e))

    def quarantine_node(self, node, exc):
        try:
            self.db.execute("UPDATE Nodes SET is_quarantine = ? WHERE node_id = ?",
                            (exc, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error setting node %s to quarantined: %s" % (node.name, e))

    def rehabilitate_node(self, node):
        try:
            self.db.execute("UPDATE Nodes SET is_quarantine = ? WHERE node_id = ?",
                            (False, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error rehabilitate node %s: %s" % (node.name, e))

    def create_node(self, index, typename):
        "creates node object using database node row"
        arg = {}
        is_transient = None
        is_quarantined = None
        self.db.execute("SELECT key, value FROM NodesAttributes WHERE node_id = ?" , (index,))
        result = self.db.fetchall()
        try: 
            cls = testgrid.parser.get_subclass(typename, testgrid.model.Node)
        except Exception as e:
            raise Exception("database create node: %s" % e)
        for item in result:
            key, value = item
            arg[key] = str(value)
        node = cls(**arg)
        node.id = int(index)
        return node

    def get_nodes(self):
        nodes = []
        self.db.execute("SELECT id, typename FROM Nodes")
        res = self.db.fetchall()
        for index, typename in res:
            node = self.create_node(index, typename)
            nodes.append(node)
        return nodes

    def is_quarantined(self, node):
        self.db.execute("SELECT is_quarantined FROM Nodes WHERE id = ?",
                        (node.id,))
        res = self.db.fetchone()
        return bool(res[0])

    def is_transient(self, node):
        #SET IS_TRANSIENT ISSUE GRID.find_node
        self.db.execute("SELECT is_transient FROM Nodes WHERE id = ?",
                        (node.id,))
        res = self.db.fetchone()
        return bool(res[0])

# Table Subnets

    def get_subnets(self):
        subnets = []
        self.db.execute("SELECT id, typename, id_string FROM Subnets")
        res = self.db.fetchall()
        for id, typename, id_string in res:
            cls = testgrid.parser.get_subclass(str(typename), testgrid.model.Subnet)
            subnet = cls(id_string)
            subnet.db_id = int(id)
            subnets.append(subnet)
        return subnets

    def add_subnet(self, subnet):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("INSERT INTO Subnets(typename, id_string) VALUES(?, ?)", (subnet.__class__.__name__, subnet.id))
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

# Table Sessions

    def get_sessions(self, grid):
        sessions = []
        self.db.execute("SELECT id, typename, username, name FROM Sessions")
        res = self.db.fetchall()
        for index, typename, username, name in res:
            try:
                session_cls = testgrid.parser.get_subclass(typename, testgrid.model.Session) 
            except Exception as e:
                raise Exception("database get session cls: %s" % e)
            session = session_cls(self, grid, str(username), str(name))
            session.id = int(index)
            session.plan = [] #self.get_plans(session)
            #session.get_subnet(session)
            sessions.append(session)
        return sessions

    def add_session(self, session):
        try:

            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("INSERT INTO Sessions(typename, username, name) VALUES(?, ?, ?)",
                            (session.__class__.__name__, session.username, session.name))
            session.id = int(self.db.lastrowid)
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error opening session username: %s, name: %s :%s" \
                                    % (session.username, session.name, e))

    def remove_session(self, session):
        try:
            res = self.db.execute("SELECT package_id FROM Plans WHERE session_id = ?", (session.id,))
            for package_id in res:
                self.remove_package(package_id)
            self.db.execute("DELETE FROM Plans WHERE session_id = ?", (session.id,))
            self.db.execute("DELETE FROM Sessions WHERE id = ?", (session.id,))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error closing session username: %s, name: %s :%s" \
                                    % (session.username, session.name, e))
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

    def remove_plan(self, session, node):
        try:
            package_id = self.db.execute("SELECT package_id FROM Plans WHERE session_id = ? AND node_id = ?",\
                                         (session.id, node.id))
            if package_id:
                self.remove_package(package_id)
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
                package = get_package(package_id)
            else:
                package = None
            self.db.execute("SELECT typename FROM Nodes WHERE id = ?", (node_id,))
            typename = self.db.fetchone()
            node = self.create_node(node_id, typename[0])
            plan.append((package, node))
        return plan

# Table Package

    def get_package(package_id):
        self.db.execute("SELECT typename, version, name WHERE id = ?", (package_id,))
        res = self.db.fetchone()
        if len(res) == 0:
            return None
        typename, version, name = res
        try:
            package_cls = testgrid.parser.get_subclass(ptype, testgrid.model.Package)
        except Exception as e:
            raise Exception("database get package cls: %s" % e)
        return package_cls(str(name), str(version))

    def add_package(package):
        try:
            self.con.isolation_level = 'EXCLUSIVE'
            self.con.execute('BEGIN EXCLUSIVE')
            self.db.execute("INSERT INTO Packages(typename, name, version) VALUES(?, ?, ?) ", 
                            (package.__class__.__name__, package.name, package.version))
            package.id = int(self.db.lastrowid)
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            
    def remove_package(package_id):
        try:
            self.db.execute("DELETE FROM Packages WHERE id = ?", (package_id,))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
                            
##############
# unit tests #
##############

class TestDatabase(Database):
     def __init__(self):
          super(TestDatabase, self).__init__()

class SelfTest(unittest.TestCase):
     def test_table_creation(self):
          hdl = Database()
