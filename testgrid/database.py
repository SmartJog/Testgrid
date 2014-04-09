import sqlite3
import sys
import os
import sqlrequest
import unittest
import model
import tgparser
import inspect

class DatabaseError(sqlite3.Error): pass

class Database(object):

     def __init__(self, databasePath = "TestGrid.db", scriptSqlPath="testgrid.sql"):
          self.dbPath = databasePath
          self.dbScriptPath = scriptSqlPath
          self.database_init()
          
          
     def database_init(self):
          "load existing database databse or creates a new database using scriptSqlPath"
          if os.path.exists(self.dbPath):
               self.con = sqlite3.connect(self.dbPath)
               self.con.row_factory = sqlite3.Row
               self.db = self.con.cursor()
          else:
               self.create_database()
             

     def create_database(self):
          "tables creation"
          try:
               self.con = sqlite3.connect(self.dbPath)
               self.con.row_factory = sqlite3.Row
               self.db = self.con.cursor()
               with open(self.dbScriptPath , 'r') as f:
                    for line in f:
                         self.db.execute(line)
                         self.con.commit()
          except sqlite3.Error as  e:
               self.con.rollback()
               raise DatabaseError(e)


# Nodes
     def add_node(self, node):
          try:
               self.db.execute(sqlrequest.ADD_NODE.format(node.name, node.__class__.__name__))
               node.id = self.db.lastrowid
               self.con.commit()
               for property, value in vars(node).iteritems():
                    self.db.execute(sqlrequest.ADD_NODE_ATTRIBUTES.format(property, value, node.id))
                    self.con.commit()
          except sqlite3.IntegrityError:
               self.con.rollback()

     def remove_node(self, node):
          try:
               self.db.execute(sqlrequest.DELETE_NODE.format(node.id))
               if self.db.rowcount:
                    self.con.commit()
                    self.db.execute(sqlrequest.DELETE_NODE_ATTRIBUTES.format(node.id))
                    self.con.commit()
          except sqlite3.Error, e:
               self.con.rollback()

     def quarantine_node(self, node, exc):
          try:
               self.db.execute(sqlrequest.ADD_NODE_ATTRIBUTES.format("is_quarantined" , exc, node.id))
               self.con.commit()
          except sqlite3.Error, e:
               self.con.rollback()

     def rehabilitate_node(self, node):
          try:
               self.db.execute(sqlrequest.UPDATE_NODE_ATTRIBUTES.format( False ,node.id, "is_quarantined"))
               self.con.commit()
          except sqlite3.Error, e:
               self.con.rollback()

     def create_node(self, index, typename):
          arg = {}
          attr = {}
          self.db.execute(sqlrequest.GET_NODE_ATTRIBUTES.format(index))
          result = self.db.fetchall()
          cls = tgparser.get_subclass(typename, model.Node)
          args, varargs, kwargs, default = inspect.getargspec(cls.__init__)
          for item in result:
               key, value = item
               if key in args:
                    arg[key] = value
               else:
                    attr[key] = value
          node = cls(**arg)
          for key, value in attr.iteritems():
               setattr(node, key ,value)
          return node

     def get_nodes(self):
          nodes = []
          self.db.execute(sqlrequest.GET_NODES)
          res = self.db.fetchall()
          for index, typename in res:
               node = self.create_node(index, typename)
               nodes.append(node)
          return nodes

     def is_quarantined(self, node):
          res = self.db.execute(sqlrequest.NODE_HAS_ATTRIBUTE.format(node.id, "is_quarantined"))
          for attr in res:
               node.is_quarantined = attr

     def is_transient(self, index):
          res = self.db.execute(sqlrequest.NODE_HAS_ATTRIBUTE.format(node.id, "is_transient"))
          for attr in res:
               node.is_transient = attr

     




# Table Sessions

     def get_sessions(self, cls, grid):
          sessions = []
          self.db.execute(sqlrequest.GET_SESSIONS)
          res = self.db.fetchall()
          for index, username, name in res:
               session = cls(self, grid, username, name)
               session.id = index
               session.plan = self.get_plans(session)
               sessions.append(session)
          return sessions

     def open_session(self, session):
          try:
               self.db.execute(sqlrequest.ADD_SESSION.format(session.username, session.name))
               session.id = self.db.lastrowid
               self.con.commit()
          except sqlite3.IntegrityError:
               self.con.rollback()

     def close_session(self, session):
          try:
               self.db.execute(sqlrequest.CLOSE_SESSION.format(session.id))
          
          except sqlite3.Error, e:
               self.con.rollback()
# Table Plans

     def add_plan(self, session, plan):
          try:
               pkg, node = plan
               if not pkg:
                    self.db.execute(sqlrequest.ADD_PLAN.format(session.id, node.id, None, None, None))
               else:
                    self.db.execute(sqlrequest.ADD_PLAN.format(session.id, node.id, pkg.name, pkg.version, pkg.__class__.__name__))
                    self.con.commit()
          except sqlite3.Error, e:
               self.con.rollback()

     def remove_plan(self, session, node):
          try:
               self.db.execute(sqlrequest.DELETE_PLAN.format(session.id, node.id))
          except sqlite3.Error, e:
               self.con.rollback()
                                         
     def get_plans(self, session):
          plan = []
          self.db.execute(sqlrequest.GET_PLANS.format(session.id))
          res = self.db.fetchall()
          for indexnode, pname, pversion, ptype in res:
               nodetype = self.db.execute(sqlrequest.GET_NODE_TYPE.format(indexnode))
               pcls = tgparser.get_subclass(ptype, model.Package)
               package = pcls(pname, pversion)
               node = self.create_node(indexnode, typename in nodetype)
               print node
               plan.append((package, node))
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
