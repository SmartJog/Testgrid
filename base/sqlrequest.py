#!/usr/bin/python

#Node
ADD_NODE = "INSERT INTO Node(hostname, username, userpass, rootpass, publicKey, privateKey, operatingsystem) VALUES('{0}', '{1}','{2}', '{3}', '{4}', '{5}','{6}')"

DELETE_NODE = "DELETE FROM Node where hostname = '{0}'"
LIST_HOSTNAME = "SELECT hostname from Node"

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

#Session
SESSION_EXIST = "SELECT id FROM Session Where login = '{0}'"

ADD_SESSION = "INSERT INTO Session(login) VALUES('{0}')"

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
