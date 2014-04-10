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

CLOSE_PLAN = "DELETE FROM Plans where session_id = '{0}'"

GET_PLANS = "SELECT node_id, namepackage, versionpackage, packagetype From Plans where session_id = '{0}'"



