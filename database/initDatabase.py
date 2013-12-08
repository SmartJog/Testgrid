#!/usr/bin/python
import sqlite3
import sys
import os
import json
#import ansible.runner

class ManageDatabase(object):

     def __init__(self, pName = "TestGrid1"):
          try:
               print "db init"
               if os.path.exists("../database/%s.db" % pName):
                    self.conn = sqlite3.connect("../database/%s.db" % pName)
               else:
                    self.conn = sqlite3.connect("../database/%s.db" % pName)
                    self.CreateDb()
               self.db = self.conn.cursor()
          except sqlite3.Error, e:
               print "sqlite3 Error don't create: %s" % e

     def CreateDb(self):
          try:
               self.db = self.conn.cursor()
               self.db.execute("CREATE TABLE PhysicalInstance(Id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25), IpAddress VARCHAR(25), state SMALLINT UNSIGNED NOT NULL, userName VARCHAR(25),  pass VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25))")
               self.db.execute("CREATE TABLE VirtualInstance(Id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25),  userName VARCHAR(25),  pass VARCHAR(25),  IpAddress VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25),  imageType VARCHAR(25), Id_Parent INT)")
               self.conn.commit()
          except sqlite3.Error, e:
               print "sqlite3 Error CreateDb: %s" % e

     def AddPhysicalInstance(self, Ip, userName, password):
          try:
               self.db.execute("INSERT INTO PhysicalInstance(IpAddress, userName, pass, state) VALUES('{0}', '{1}','{2}','0')".format(Ip, userName, password))
               self.conn.commit()
          except sqlite3.Error, e:
               self.conn.rollback()
               print "sqlite3 Error AddPhysicalInstance: %s" % e

#if __name__ == '__main__':
#    test = ManageDatabase()
#   test.CreateDb("TestGrid1")
