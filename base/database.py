#!/usr/bin/python
import sqlite3
import sys
import os
import json
import base64
import sqlrequest

class Database(object):

     def __init__(self, databasePath = "TestGrid.db", scriptSqlPath="testgrid.sql"):
          self.dbPath = databasePath
          self.dbScriptPath = scriptSqlPath
          self.databaseInit()

     def databaseInit(self):
          try:
               if os.path.exists(self.dbPath):
                    self.conn = sqlite3.connect(self.dbPath)
               else:
                    self.conn = sqlite3.connect(self.dbPath)
                    self.createDb()
               self.db = self.conn.cursor()
          except sqlite3.Error, e:
               print "sqlite3 Error can't create: %s" % e

     def resetDatabase(self):
          if os.path.exists(self.dbPath):
               os.remove(self.dbPath)
          self.databaseInit()

     def createDb(self):
          try:
               self.db = self.conn.cursor()
               with open(self.dbScriptPath , 'r') as f:
                    for line in f:
                         self.db.execute(line)
                         self.conn.commit()
          except sqlite3.Error, e:
               self.conn.rollback()

     def getHostname(self, index):
          try:
               self.db.execute(sqlrequest.NODE_HOSTNAME.format(index))
               hostname = self.db.fetchone()
               return hostname[0]
          except sqlite3.Error, e:
               raise Exception()

     def getRootPass(self, index):
          try:
               self.db.execute(sqlrequest.NODE_ROOTPASS.format(index))
               rootpass = self.db.fetchone()
               decoded = base64.b64decode(rootpass[0])
               return decoded
          except sqlite3.Error, e:
               raise Exception()

     def getUsername(self, index):
          try:
               self.db.execute(sqlrequest.NODE_USERNAME.format(index))
               username = self.db.fetchone()
               return username[0]
          except sqlite3.Error, e:
               raise Exception()

     def getUserpass(self, index):
          try:
               self.db.execute(sqlrequest.NODE_USERPASS.format(index))
               userpass = self.db.fetchone()
               decoded = base64.b64decode(userpass[0])
               return decoded
          except sqlite3.Error, e:
               raise Exception()

     def nodeExist(self, hostname):
          try:
               self.db.execute(sqlrequest.NODE_EXIST.format(hostname))
               if len(self.db.fetchall())==0:
                    return False
               return True
          except sqlite3.Error, e:
               raise Exception()


     def addNode(self, hostname, username, userpass , publicKey, privateKey, rootpass, isvirtual):
          try:
               encryptedPass = base64.b64encode(userpass)
               encryptedRootPass = base64.b64encode(rootpass)
               self.db.execute(sqlrequest.ADD_NODE.format(hostname, 
                                                          username,
                                                          encryptedPass, 
                                                          encryptedRootPass, 
                                                          publicKey, 
                                                          privateKey, 
                                                          isvirtual))
               self.conn.commit()
          except sqlite3.IntegrityError:
               self.conn.rollback()

     def deleteNode(self, hostname):
          try:
               self.db.execute(sqlrequest.DELETE_NODE.format(hostname))
               if self.db.rowcount == 0:
                    result = "no node %s" % hostname
               else:
                    result = "%s has been removed" % hostname 
                    self.conn.commit()
               return result
               
          except sqlite3.Error, e:
               self.conn.rollback()
               


     
     def listIndex(self):
          try:
               self.db.execute(sqlrequest.NODE_LIST_INDEX)
               ids = self.db.fetchall() 
               for index in ids:
                    yield index[0]
          except sqlite3.Error, e:
               print "sqlite3 Error listInstance: %s" % e
               
     def setUsedNode(self, index):
          try:
               self.db.execute(sqlrequest.SET_USED_NODE.format(index))
          except sqlite3.Error, e:
               self.conn.rollback()
               raise Exception

  
     def getUnusedNode(self):
          try:
               self.db.execute(sqlrequest.UNUSED_NODE)
               ids = self.db.fetchall()
               for index in ids:
                    yield index[0]
          except sqlite3.Error, e:
               raise Exception


     def deleteDeployment():pass


     def addDeployment(self, sessionIndex, nodeIndex, packageName, packageVersion):
          try:
               
               self.db.execute(sqlrequest.ADD_DEPLOYMENT.format(sessionIndex, 
                                                                nodeIndex, 
                                                                packageName, 
                                                                packageVersion))
               self.conn.commit()
          except sqlite3.Error, e:
               print e
               self.conn.rollback()
               raise Exception
          
     def deleteSession(self, login):
          try:
               self.db.execute(sqlrequest.DELETE_SESSION.format(login))
               self.conn.commit()                  
          except sqlite3.Error, e:
               self.conn.rollback()

     def maxSessionId(self):
          try:
               self.db.execute(sqlrequest.MAX_SESSION_ID)
               index  = self.db.fetchone()
               if index[0] is None:
                    return 0
               return index[0]
          except sqlite3.Error, e:
               print e
               raise Exception

     def addSession(self, login):
          try:
               self.db.execute(sqlrequest.ADD_SESSION.format(login))
               self.conn.commit()
          except sqlite3.Error, e:
               self.conn.rollback()
               raise Exception


     def sessionExist(self, login):
          try:
               self.db.execute(sqlrequest.SESSION_EXIST.format(login))
               if len(self.db.fetchall())==0:
                    return False
               return True
          except sqlite3.Error, e:
               raise Exception

     def getSessionIndex(self, login):
          try:
               self.db.execute(sqlrequest.SESSION_EXIST.format(login))
               index = self.db.fetchone()
               if len(index)==0:
                    return None
               return index[0]
          except sqlite3.Error, e:
               raise Exception
