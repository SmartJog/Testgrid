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
               if hostname is None:
                    return None
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

     def getOperatinsystem(self, index):
          try:
               self.db.execute(sqlrequest.NODE_OPERATING_SYSTEM.format(index))
               os = self.db.fetchone()
               return os[0]
          except sqlite3.Error, e:
               raise Exception()

     def nodeIsavailable(self, index):
          try:
               self.db.execute(sqlrequest.NODE_ISAVAILABLE.format(index))
               isavailable = self.db.fetchone()
               return isavailable[0]
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

     def getNodeIndex(self, hostname):
          try:
               self.db.execute(sqlrequest.NODE_EXIST.format(hostname))
               index = self.db.fetchone()
               if index is None:
                    return None
               return index[0]
          except sqlite3.Error, e:
               raise Exception

     def addNode(self, hostname, username, userpass , publicKey, privateKey, rootpass, operatingsystem):
          try:
               encryptedPass = base64.b64encode(userpass)
               encryptedRootPass = base64.b64encode(rootpass)
               self.db.execute(sqlrequest.ADD_NODE.format(hostname, 
                                                          username,
                                                          encryptedPass, 
                                                          encryptedRootPass, 
                                                          publicKey, 
                                                          privateKey, 
                                                          operatingsystem))
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
               


     
     def listIndexNode(self):
          try:
               self.db.execute(sqlrequest.NODE_LIST_INDEX)
               ids = self.db.fetchall()
               for index in ids:
                    yield index[0]
          except sqlite3.Error, e:
               raise Exception

     """def listNodeHostname(self):
          try:
               result = self.db.execute(sqlString.LIST_HOSTNAME)
               hostnames = self.db.fetchall()
               for host in hostnames:
                    yield host[0]
          except sqlite3.Error, e:
               print "sqlite3 Error listInstance: %s" % e """

               
     def setUsedNode(self, index):
          try:
               self.db.execute(sqlrequest.SET_USED_NODE.format(index))
               self.conn.commit()
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

     def setUnusedNode(self, index):
           try:
               self.db.execute(sqlrequest.SET_UNSED_NODE.format(index))
               self.conn.commit()
           except sqlite3.Error, e:
               self.conn.rollback()
               raise Exception

     def deploymentExist(self, index):
          try:
               self.db.execute(sqlrequest.DEPLOYMENT_EXIST.format(index))
               if len(self.db.fetchall())==0:
                    return False
               return True
          except sqlite3.Error, e:
               raise Exception()

     def deleteDeployment(self, index):
          try:
               self.db.execute(sqlrequest.DELETE_DEPLOYMENT.format(index))
               self.conn.commit()
               
          except sqlite3.Error, e:
               self.conn.rollback()


     def getDeploymentNode(self, index):
          try:
               self.db.execute(sqlrequest.DEPLOYMENT_NODE.format(index))
               row = self.db.fetchone()
               return  row[0]
               
          except sqlite3.Error, e:
               raise Exception

     def getDeploymentPackage(self, index):
          try:
               package = {}
               self.db.execute(sqlrequest.DEPLOYMENT_PACKAGE.format(index))
               row = self.db.fetchone()
               package['name'] = row[0]
               package['version'] = row[1]
               return package
          except sqlite3.Error, e:
               raise Exception

     def addDeployment(self, sessionIndex, nodeIndex, packageName, packageVersion):
          try:
               print "session index %d" % sessionIndex
               self.db.execute(sqlrequest.ADD_DEPLOYMENT.format(sessionIndex, 
                                                                nodeIndex, 
                                                                packageName, 
                                                                packageVersion))
               self.conn.commit()
          except sqlite3.Error, e:
               print e
               self.conn.rollback()
               raise Exception

     def listDeploymentSession(self, sessionIndex):
          try:
               result_list = list()
               self.db.execute(sqlrequest.DEPLOYMENT_SESSION.format(sessionIndex))
               result = self.db.fetchall()
               print result
               for row in result:
                    hostname = self.getHostname(row[1])
                    if hostname is None:
                         raise Exception("couldn't find host")
                    result_list.append({'index':row[0], "host": hostname, 'packageName':row[2], 'version':row[3]})
               return result_list
          except sqlite3.Error, e:
               print e
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
