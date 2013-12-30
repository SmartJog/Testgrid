#!/usr/bin/python
import sqlite3
import sys
import os
import json
import base64
import sqlString


class ManageDatabase(object):

     def __init__(self, databaseName = "TestGrid1"):
          self.name = databaseName
          self.databaseInit(databaseName)

     def databaseInit(self, name):
          try:
               databasePath = sqlString.DATABASE_PATH.format(name)
               if os.path.exists(databasePath):
                    self.conn = sqlite3.connect(databasePath)
               else:
                    self.conn = sqlite3.connect(databasePath)
                    self.createDb()
               self.db = self.conn.cursor()
          except sqlite3.Error, e:
               print "sqlite3 Error don't create: %s" % e

     def resetDatabase(self):
          if os.path.exists(sqlString.DATABASE_PATH.format(self.name)):
               os.remove(sqlString.DATABASE_PATH.format(self.name))
          self.databaseInit(self.name)

     def createDb(self):
          try:
               self.db = self.conn.cursor()
               self.db.execute(sqlString.CREATE_TABLE_PHYSICAL_INSTANCE)
               self.db.execute(sqlString.CREATE_TABLE_VIRTUAL_INSTANCE)
               self.conn.commit()
          except sqlite3.Error, e:
               self.conn.rollback()
               print "sqlite3 Error while creating database: %s" % e

     def addPhysicalInstance(self, Ip, userName, password, publicKey, privateKey, rootpwd):
          try:
               encryptedPass = base64.b64encode(password)
               encryptedRootPass = base64.b64encode(rootpwd)
               #base64.b64decode(test)
               self.db.execute(sqlString.ADD_PHYSICAL_INSTANCE.format(Ip, userName,encryptedPass, encryptedRootPass, publicKey, privateKey, "0"))
               self.conn.commit()
          except sqlite3.Error, e:
               self.conn.rollback()
               print "sqlite3 Error AddPhysicalInstance: %s" % e

     def deletePhysicalInstance(self, Ip):
          try:
               self.db.execute(sqlString.DELETE_PHYSICAL_INSTANCE.format(Ip))
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
               result = self.db.execute(sqlString.LIST_INSTANCE)
               data= self.db.fetchall()
               if len(data)==0:
                    print "no instance nodes"
                    return
               for row in data:
                    print "%s" % row

          except sqlite3.Error, e:
               print "sqlite3 Error listInstance: %s" % e


     def checkIfPhysicalInstanceExist(self, Ip):
          try:
               self.db.execute(sqlString.CHECK_PHYSICAL_INSTANCE.format(Ip))
               if len(self.db.fetchall())==0:
                    return False
               return True
          except sqlite3.Error, e:
               print "sqlite3 Error CheckIfPhysicalInstanceExist: %s" % e


     """def getInventory(self):
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
                    return None"""
