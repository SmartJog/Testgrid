# copyright (c) 2013-2014 smartjog, released under the GPL license.
import sqlite3
import sys
import os
import sqlrequest
import unittest
import inspect
import testgrid

"handle sqlite3 databse managment"

class DatabaseError(sqlite3.Error): pass

class Database(object):
    def __init__(self, dbpath = "TestGrid.db", script_path="testgrid.sql"):
        self.dbpath = dbpath
        self.script_path = script_path
        self.con = None
        self.database_init()
          
    def database_init(self):
        "load existing database databse or creates a new database using script_path"
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
            raise DatabaseError("error creating database:" % e)

    def close(self):
        "close databse connection"
        if self.con:
            self.con.close()

    def __del__(self):
        self.close()

# Nodes
    def add_node(self, node):
        try:
            self.db.execute("INSERT INTO Nodes(classname, name) VALUES (?,?)", 
                            (node.get_typename(), node.name))
            #FIX CONCURRENCY
            node.id = int(self.db.lastrowid)
            self.con.commit()
            args, varargs, kwargs, defaults = inspect.getargspec(node.__init__)
            for arg in args[1:]:
                self.db.execute("INSERT INTO NodesAttributes(key, value, node_id) VALUES(?, ?, ?)"
                                , (arg, str(getattr(node, arg)), node.id))
                if hasattr(node, "is_transient"):
                    self.db.execute("INSERT INTO NodesAttributes(key, value, node_id) VALUES(?, ?, ?)"
                                    , ("is_transient", str(node.is_transient), node.id))
                if hasattr(node, "is_quarantined"):
                    self.db.execute("INSERT INTO NodesAttributes(key, value, node_id) VALUES(?, ?, ?)"
                                    , ("is_quarantined", str(node.is_quarantined), node.id))
            self.con.commit()
        except sqlite3.Error as e:
            self.con.rollback()
            raise DatabaseError("error while adding node %s :%s" % (node.name, e))

    def remove_node(self, node):
        try:
            self.db.execute("DELETE FROM Nodes where id = ?", (node.id,))
            if self.db.rowcount:
                self.db.execute("DELETE FROM NodesAttributes where node_id = ?" ,(node.id,))
                self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error while removing node %s :%s" % (node.name, e))

    def quarantine_node(self, node, exc):
        try:
            self.db.execute("INSERT INTO NodesAttributes(key, value, node_id) VALUES(?, ?, ?)"
                            ,("is_quarantined" , exc, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error setting node %s to quarantined:%s" % (node.name, e))

    def rehabilitate_node(self, node):
        try:
            self.db.execute("UPDATE NodesAttributes SET value = ? where node_id = ? and key = ?"
                            ,(False ,node.id, "is_quarantined"))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error rehabilitate node %s:%s" % (node.name, e))

    def create_node(self, index, typename):
        arg = {}
        is_transient = None
        is_quarantined = None
        self.db.execute("SELECT key, value from NodesAttributes where node_id = ?" , (index,))
        result = self.db.fetchall()
        try: 
            cls = testgrid.parser.get_subclass(typename, testgrid.model.Node)
        except Exception as e:
            raise Exception("database create node: %s" % e)
        for item in result:
            key, value = item
            if key == "is_transient":
                is_transient = bool(value)
            elif key == "is_quarantined":
                is_quarantined = bool(value)
            else:
                arg[key] = str(value)
        node = cls(**arg)
        node.id = int(index)
        if is_transient:
            node.is_transient = is_transient
        if is_quarantined:
            node.is_quarantined = is_quarantined
        return node

    def get_nodes(self):
        nodes = []
        self.db.execute("SELECT id, classname from Nodes")
        res = self.db.fetchall()
        for index, typename in res:
            node = self.create_node(index, typename)
            nodes.append(node)
        return nodes

    def is_quarantined(self, node):
        res = self.db.execute("SELECT FROM NodesAttributes where node_id = ? and key = ?"
                              ,(node.id, "is_quarantined"))
        for attr in res:
            node.is_quarantined = bool(attr)

    def is_transient(self, node):
        res = self.db.execute("SELECT FROM NodesAttributes where node_id = ? and key = ?"
                              ,(node.id, "is_transient"))
        for attr in res:
            node.is_transient = bool(attr)

# Table Sessions
    def get_sessions(self, cls, grid):
        sessions = []
        self.db.execute("SELECT id, username, name from Sessions")
        res = self.db.fetchall()
        for index, username, name in res:
            session = cls(self, grid, str(username), str(name))
            session.id = int(index)
            session.plan = self.get_plans(session)
            sessions.append(session)
        return sessions

    def open_session(self, session):
        try:
            self.db.execute("INSERT INTO Sessions(username, name) VALUES(?, ?)"
                            ,(session.username, session.name))
            #FIX CONCURRENCY
            session.id = int(self.db.lastrowid)
            self.con.commit()
        except sqlite3.Error:
            self.con.rollback()
            raise DatabaseError("error opening session username:%s, name: %s :%s" \
                                    % (session.usernname, session.name,e))

    def close_session(self, session):
        try:
            self.db.execute("DELETE FROM Plans where session_id = ?",(session.id,))
            self.db.execute("DELETE FROM Sessions where id = ?",(session.id,))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error closing session username:%s, name: %s :%s" \
                                    % (session.usernname, session.name,e))
# Table Plans
    def add_plan(self, session, plan):
        try:
            pkg, node = plan
            if not pkg:
                self.db.execute("INSERT INTO Plans(session_id, node_id, packagename," \
                                    "packageversion, packagetypename) VALUES(?, ?, ?, ?,?)" \
                                ,(session.id, node.id, None, None, None))
            else:
                self.db.execute("INSERT INTO Plans(session_id, node_id, packagename," \
                                    "packageversion, packagetypename) VALUES(?, ?, ?, ?,?)" \
                                    ,(session.id, node.id, pkg.name, pkg.version, pkg.get_typename()))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error adding plan  session username:%s, name: %s , node: %s : %s" \
                                    % (session.usernname, session.name, node.name ,e))

    def remove_plan(self, session, node):
        try:
            self.db.execute("DELETE FROM Plans where session_id = ? and node_id = ?"
                            ,(session.id, node.id))
            self.con.commit()
        except sqlite3.Error, e:
            self.con.rollback()
            raise DatabaseError("error removing plan session username:%s, name: %s , node: %s : %s" \
                                    % (session.usernname, session.name, node.name ,e))

                                         
    def get_plans(self, session):
        plan = []
        self.db.execute("SELECT node_id, packagename, packageversion," \
                            "packagetypename From Plans where session_id = ?" \
                            ,(session.id,))
        res = self.db.fetchall()
        for indexnode, pname, pversion, ptype in res:
            for node in session.gridref:
                if int(node.id) == int(indexnode):
                    if ptype != None:
                        pcls = testgrid.parser.get_subclass(ptype, testgrid.model.Package)
                        package = pcls(str(pname), str(pversion))
                    else:
                        package = None   
                        plan.append((package, node))
                    break
        return plan          
               
##############
# unit tests #
##############

class TestDatabase(Database):
     def __init__(self):
          super(TestDatabase, self).__init__()

class SelfTest(unittest.TestCase):
     def test_table_creation(self):
          hdl = Database()
