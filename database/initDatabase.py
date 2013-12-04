#!/usr/bin/python
import MySQLdb
import sys
import json
import ansible.runner

class ManageDatabase(object):

     def __init__(self, pHost = "localhost", pUser = "root", pPass="", pName = "TestGrid1"):
          try:
               print "db init"
               self.con = MySQLdb.connect(host=pHost, user=pUser, passwd=pPass)
               self.db = self.con.cursor()
               self.name = pName
          except MySQLdb.Error, e:
               print "MySQL Error don't create: %s" % e

     def CreateDb(self, pName):
          try:
               self.name = pName
               self.db.execute('CREATE DATABASE IF NOT EXISTS  %s' % pName)
               self.db.execute('USE %s' % pName)
               self.db.execute("CREATE TABLE PhysicalInstance(Id INT PRIMARY KEY AUTO_INCREMENT, OperatingSystem VARCHAR(25), IpAddress VARCHAR(25), state SMALLINT UNSIGNED NOT NULL, userName VARCHAR(25),  pass VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25))")
               self.db.execute("CREATE TABLE VirtualInstance(Id INT PRIMARY KEY AUTO_INCREMENT, OperatingSystem VARCHAR(25),  userName VARCHAR(25),  pass VARCHAR(25),  IpAddress VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25),  imageType VARCHAR(25), Id_Parent INT)")

          except MySQLdb.Error, e:
               print "MySQL Error CreateDb: %s" % e

     def AddPhysicalInstance(self, Ip, userName, password):
          try:
               print 'USE %s' % self.name
               self.db.execute('USE %s' % self.name)
               self.db.execute("INSERT INTO PhysicalInstance(IpAddress, userName, pass, state) VALUES('{0}', '{1}','{2}','0')".format(Ip, userName, password))
               self.con.commit()
          except MySQLdb.Error, e:
               self.con.rollback()
               print "MySQL Error AddPhysicalInstance: %s" % e

#if __name__ == '__main__':
 #    test = ManageDatabase()
