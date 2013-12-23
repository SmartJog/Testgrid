#!/usr/bin/python

DATABASE_PATH = "../database/{0}.db"


CREATE_TABLE_PHYSICAL_INSTANCE = "CREATE TABLE PhysicalInstance(Id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25),  userName VARCHAR(25),  pass VARCHAR(25), rootpass VARCHAR(25),  publicKey VARCHAR(2000),privateKey VARCHAR(2000), IpAddress VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25), state SMALLINT UNSIGNED NOT NULL)"

CREATE_TABLE_VIRTUAL_INSTANCE = "CREATE TABLE VirtualInstance(Id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25),  userName VARCHAR(25),  pass VARCHAR(25), rootpass VARCHAR(25),  publicKey VARCHAR(2000),privateKey VARCHAR(2000), IpAddress VARCHAR(25), deliverable VARCHAR(25), version VARCHAR(25),  imageType VARCHAR(25), Id_Parent INT)"

ADD_PHYSICAL_INSTANCE = "INSERT INTO PhysicalInstance(IpAddress, userName, pass, rootpass, publicKey, privateKey,state) VALUES('{0}', '{1}','{2}', '{3}', '{4}', '{5}','{6}')"

DELETE_PHYSICAL_INSTANCE = "DELETE FROM PhysicalInstance WHERE IpAddress = '{0}'"


LIST_INSTANCE = "SELECT IpAddress FROM  PhysicalInstance"

CHECK_PHYSICAL_INSTANCE = "SELECT IpAddress FROM  PhysicalInstance Where IpAddress ='{0}'"
