#!/usr/bin/python
import sqlite3
import sys
import os
import json
import base64
#import ansible.runner

class ManageDatabase(object):

     def __init__(self, pName = "TestGrid1"):
          try:
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
               self.db.execute("CREATE TABLE PhysicalInstance(Id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25),  userName VARCHAR(25),  pass VARCHAR(25), rootpass VARCHAR(25),  publicKey VARCHAR(2000),privateKey VARCHAR(2000), IpAddress VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25), state SMALLINT UNSIGNED NOT NULL)")
               self.db.execute("CREATE TABLE VirtualInstance(Id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25),  userName VARCHAR(25),  pass VARCHAR(25), rootpass VARCHAR(25),  publicKey VARCHAR(2000),privateKey VARCHAR(2000), IpAddress VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25),  imageType VARCHAR(25), Id_Parent INT)")
               self.conn.commit()
          except sqlite3.Error, e:
               print "sqlite3 Error CreateDb: %s" % e

     def AddPhysicalInstance(self, Ip, userName, password, publicKey, privateKey, rootpwd):
          try:
               encryptedPass = base64.b64encode(password)
               encryptedRootPass = base64.b64encode(rootpwd)
               #base64.b64decode(test)
               self.db.execute("INSERT INTO PhysicalInstance(IpAddress, userName, pass, rootpass, publicKey, privateKey,state) VALUES('{0}', '{1}','{2}', '{3}', '{4}', '{5}','0')".format(Ip, userName,encryptedPass, encryptedRootPass, publicKey, privateKey))
               self.conn.commit()
          except sqlite3.Error, e:
               self.conn.rollback()
               print "sqlite3 Error AddPhysicalInstance: %s" % e

     def DeletePhysicalInstance(self, Ip):
          try:
               self.db.execute("DELETE FROM PhysicalInstance WHERE IpAddress = '{0}'".format(Ip))
               if self.db.rowcount == 0:
                    print "no node %s" % Ip
               else:
                    print "%s has been removed" % Ip 
                    self.conn.commit()
               
          except sqlite3.Error, e:
               self.conn.rollback()
               print "sqlite3 Error DeletePhysicalInstance: %s" % e

     def listInstance(self):
          try:
               result = self.db.execute("SELECT IpAddress FROM  PhysicalInstance")
               data= self.db.fetchall()
               if len(data)==0:
                    print "no instance nodes"
                    return
               for row in data:
                    print "%s" % row

          except sqlite3.Error, e:
               print "sqlite3 Error listInstance: %s" % e

     def getInventory(self):
               try:
                    inventory ={}
                    inventory['local'] = [ '127.0.0.1' ]
                    result = self.db.execute("SELECT IpAddress FROM  PhysicalInstance")
                    for row in result:
                         group = None
                         if group is None:
                              group = 'ungrouped'

                         if not group in inventory:
                              inventory[group] = {
                                   'hosts' : []
                                   }
                         inventory[group]['hosts'].append(row[0])
                         print json.dumps(inventory, indent=4)
                         return inventory
     
               except sqlite3.Error, e:
                    print "sqlite3 Error listInstance: %s" % e
                    return None

     def CheckIfPhysicalInstanceExist(self, Ip):
          try:
               self.db.execute("SELECT IpAddress FROM  PhysicalInstance Where IpAddress ='%s'" % Ip)
               if len(self.db.fetchall())==0:
                    return False
               return True
          except sqlite3.Error, e:
               print "sqlite3 Error CheckIfPhysicalInstanceExist: %s" % e
#if __name__ == '__main__':
#    test = ManageDatabase()
#   test.CreateDb("TestGrid1")
