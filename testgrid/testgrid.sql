CREATE TABLE Nodes(id INTEGER PRIMARY KEY AUTOINCREMENT, typename VARCHAR(25), name VARCHAR(25), is_transient INT default 0, is_quarantined INT default 0, error VARCHAR(25), modulename  VARCHAR(25));
CREATE TABLE NodesAttributes(id INTEGER PRIMARY KEY AUTOINCREMENT, key VARCHAR(25), value VARCHAR(25), node_id INT);
CREATE TABLE Sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, typename VARCHAR(25), username VARCHAR(25), name VARCHAR(25), subnet_id INT);
CREATE TABLE Plans(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INT, node_id INT, package_id INT);
CREATE TABLE Packages(id INTEGER PRIMARY KEY AUTOINCREMENT, typename VARCHAR(25), name VARCHAR(25), version VARCHAR(25));
CREATE TABLE Subnets(id INTEGER PRIMARY KEY AUTOINCREMENT, typename VARCHAR(25), id_string VARCHAR(25), used INT default 0);
