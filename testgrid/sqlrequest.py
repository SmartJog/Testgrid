#!/usr/bin/python

#Nodes
ADD_NODE = "INSERT INTO Nodes(classname, name) VALUES('{0}', '{1}')"

DELETE_NODE = "DELETE FROM Nodes where id = '{0}'"

GET_NODES = "SELECT id, classname from Nodes"

GET_NODE_TYPE = "SELECT classname from Nodes where id = '{0}'"


#NodesAttributes

ADD_NODE_ATTRIBUTES = "INSERT INTO NodesAttributes(key, value, node_id) VALUES('{0}', '{1}', '{2}')" 

GET_NODE_ATTRIBUTES = "SELECT key, value from NodesAttributes where node_id = '{0}'"

DELETE_NODE_ATTRIBUTES = "DELETE FROM NodesAttributes where node_id = '{0}'"

UPDATE_NODE_ATTRIBUTES = "UPDATE NodesAttributes SET value = '{0}' where node_id = '{1}' and key = '{2}'"

NODE_HAS_ATTRIBUTE = "SELECT FROM NodesAttributes where node_id = '{0}' and key = {1}''"
#Sessions

ADD_SESSION = "INSERT INTO Sessions(username, name) VALUES('{0}', '{1}')"

CLOSE_SESSION = "DELETE FROM Sessions where id = '{0}'"

GET_SESSIONS = "SELECT id, username, name from Sessions"

#Plans

ADD_PLAN = "INSERT INTO Plans(session_id, node_id, namepackage, versionpackage, packagetype) VALUES('{0}', '{1}', '{2}', '{3}', '{4}')"

DELETE_PLAN = "DELETE FROM Plans where session_id = '{0}' and node_id = '{1}'"

GET_PLANS = "SELECT node_id, namepackage, versionpackage, packagetype From Plans where session_id = '{0}'"

NODE_LIST_INDEX = "SELECT id from Node"

NODE_HOSTNAME = "SELECT hostname from Node  where id = '{0}'"

NODE_ROOTPASS = "SELECT rootpass from Node  where id = '{0}'"

NODE_USERNAME = "SELECT username from Node  where id = '{0}'"

NODE_USERPASS = "SELECT userpass from Node  where id = '{0}'"

NODE_EXIST = "SELECT id FROM  Node  Where hostname ='{0}'"

UNUSED_NODE = "SELECT id FROM Node where isAvailable = 1"

NODE_ISAVAILABLE = "SELECT isAvailable FROM Node where id = '{0}'"

SET_UNSED_NODE = "UPDATE Node  SET isAvailable = 1 WHERE id = '{0}'"

SET_USED_NODE = "UPDATE Node  SET isAvailable = 0 WHERE id = '{0}'"
NODE_OPERATING_SYSTEM = "SELECT operatingsystem from Node  where id = '{0}'"


SESSION_EXIST = "SELECT id FROM Session Where login = '{0}'"



DELETE_SESSION = "DELETE FROM Session where login = '{0}'"

MAX_SESSION_ID = "SELECT MAX(id) from Session"

SESSION_LIST_INDEX = "SELECT id from Session"

#Deployment

ADD_DEPLOYMENT = "INSERT INTO Deployment(session_id, node_id , namepackage, versionpackage) VALUES('{0}', '{1}','{2}', '{3}')"

DELETE_DEPLOYMENT =  "DELETE FROM Deployment where id = '{0}'"

DEPLOYMENT_NODE = "select node_id FROM Deployment Where id = '{0}'"

DEPLOYMENT_PACKAGE = "select namepackage, versionpackage FROM Deployment where id = '{0}'"

DEPLOYMENT_SESSION = "select id, node_id , namepackage, versionpackage FROM Deployment where session_id = '{0}'"
DEPLOYMENT_EXIST = "select * From Deployment where id = '{0}'"
