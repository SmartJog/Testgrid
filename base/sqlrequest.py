#!/usr/bin/python
ADD_NODE = "INSERT INTO Node(hostname, username, userpass, rootpass, publicKey, privateKey, isvirtual) VALUES('{0}', '{1}','{2}', '{3}', '{4}', '{5}','{6}')"

DELETE_NODE = "DELETE FROM Node where hostname = '{0}'"
LIST_HOSTNAME = "SELECT hostname from Node"

LIST_INDEX = "SELECT id from Node"

HOSTNAME = "SELECT hostname from Node  where id = '{0}'"

ROOTPASS = "SELECT rootpass from Node  where id = '{0}'"

USERNAME = "SELECT username from Node  where id = '{0}'"

USERPASS = "SELECT userpass from Node  where id = '{0}'"

EXIST = "SELECT hostname FROM  Node  Where hostname ='{0}'"


CREATE = "CREATE TABLE Node(id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25),  username VARCHAR(25),  userpass VARCHAR(25), rootpass VARCHAR(25),publicKey VARCHAR(2000),privateKey VARCHAR(2000), hostname VARCHAR(25), isvirtual SMALLINT UNSIGNED, ishypervisor SMALLINT UNSIGNED, Id_node INT)"
