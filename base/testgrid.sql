CREATE TABLE Node(id INTEGER PRIMARY KEY AUTOINCREMENT, OperatingSystem VARCHAR(25),  username VARCHAR(25),  userpass VARCHAR(25), rootpass VARCHAR(25),publicKey VARCHAR(2000),privateKey VARCHAR(2000), hostname VARCHAR(25) unique, isvirtual SMALLINT UNSIGNED DEFAULT 0 , ishypervisor SMALLINT UNSIGNED, Id_node INT, isAvailable SMALLINT UNSIGNED DEFAULT 1);
CREATE TABLE Session(id INTEGER PRIMARY KEY AUTOINCREMENT, login VARCHAR(25), password VARCHAR(25));
CREATE TABLE Deployment(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INT, node_id INT, namepackage VARCHAR(25), versionpackage VARCHAR(25));
