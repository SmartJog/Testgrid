-- copyright (c) 2014 arkena, released under the MIT license.

create table Nodes(
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	name text not null,
	repr text not null,
	is_transient INT default 0,
	is_quarantined INT default 0,
	quarantine_reason text
);

create table NodesAttributes(
	id integer primary key autoincrement,
	key text not null,
	value text not null,
	node_id integer not null references Nodes(id) on delete cascade,
	unique(key, node_id)
);

create table Subnets(
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	id_string text not null,
	used integer default 0
);

create table Sessions(
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	username text not null,
	name text not null,
	subnet_id integer not null references Subnets(id) on delete set null,
	unique(name)
);

create table Packages(
	id integer primary key autoincrement,
	modulename text not null,
	typename text not null,
	name text not null,
	version text not null,
	unique(name, version)
);

create table Plans(
	id integer primary key autoincrement,
	session_id integer not null references Sessions(id) on delete cascade,
	node_id integer not null references Nodes(id) on delete cascade,
	package_id integer not null references Packages(id) on delete cascade,
	unique(session_id, node_id)
);
