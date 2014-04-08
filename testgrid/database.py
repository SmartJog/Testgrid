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
                          
                          
     def get_nodes(self):
          nodes = []
          arg = {}
          attr = {}
          self.db.execute(sqlrequest.GET_NODES)
          res = self.db.fetchall()
          for index, typename in res:
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
               obj = cls(**arg)
               for key, value in attr.iteritems():
                    setattr(cls, key ,value)
               nodes.append(obj)
          return nodes

     def isTransient(self, index):pass
     def isQuarantined(self, index):pass
     def isAvailable(self, index):pass
     def rehabilitate_node(self):pass




# Table Sessions

     def getSessions(self):pass
     def openSession(self):
          

def closeSession(self):pass

# Table Plans

def addPlan(self):pass
def removePlan(self):pass
def getPlans(self):pass


##############
# unit tests #
##############

class TestDatabase(Database):
     def __init__(self):
          super(TestDatabase, self).__init__()

class SelfTest(unittest.TestCase):
     def test_table_creation(self):
          hdl = Database()
