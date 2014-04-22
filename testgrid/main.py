# copyright (c) 2014 smartjog, released under the GPL license.

"""
Testgrid command-line utility.

Usage:
  tg [-m INI] [-l|-c HOST] [-g NAME] --list-nodes
  tg [-m INI] [-l|-c HOST] [-g NAME] --add-node NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] --remove-node NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] --quarantine-node NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] --rehabilitate-node NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] [-s NAME] -n NAME --ping
  tg [-m INI] [-l|-c HOST] [-g NAME] [-s NAME] -n NAME --install NAME --type NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] [-s NAME] -n NAME --uninstall NAME  --type NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] [-s NAME] -n NAME --is-installed NAME  --type NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] [-s NAME] -n NAME --is-installable NAME  --type NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] [-s NAME] -n NAME --execute [--] ARGV...
  tg [-m INI] [-l|-c HOST] [-g NAME] --list-sessions
  tg [-m INI] [-l|-c HOST] [-g NAME] --open-session NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] --close-session NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] -s NAME --list-nodes
  tg [-m INI] [-l|-c HOST] [-g NAME] -s NAME --allocate-node NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] -s NAME --release-node NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] -s NAME --deploy PKG --type NAME
  tg [-m INI] [-l|-c HOST] [-g NAME] -s NAME --undeploy PKG
  tg --version
  tg --help

Options:
  -g NAME, --grid NAME        set grid section NAME in the manifest [default: grid]
  -n NAME, --node NAME        set node NAME
  -s NAME, --session NAME     set session NAME
  --list-nodes                list nodes in selected container
  --add-node NAME             add node parsed from manifest
  --remove-node NAME          ...
  --quarantine-node NAME      place a node in quarantine
  --rehabilitate-node NAME    rehabilitate a quarantined node
  --ping                      ...
  --install NAME              ...
  --type NAME                 specify an object type
  --uninstall NAME            ...
  --is-installed NAME         ...
  --is-installable NAME       ...
  -e, --execute               ...
  --list-sessions             ...
  --open-session NAME         ...
  --close-session NAME        ...
  --allocate-node NAME        ...
  --release-node NAME         ...
  --deploy PKG                ...
  --undeploy PKG              ...
  -m INI, --manifest INI      comma-separated list of .ini filepaths or URIs [default: ~/grid.ini]
  -l, --local                 use a local client
  -c HOST, --controller HOST  set REST controller hoststring [default: qa.lab.fr.lan:8080]
  -h, --help                  show help
  --version                   show version

Examples:
# first, get back the official grid manifest:
  $ wget qa.lab.fr.lan/grid.ini -O ~
# deploy fleche:
  $ tg --create-session test-fleche
  $ tg -s test-fleche --deploy fleche-16.5-1 --type debian
# deploy ansible:
  $ tg --create-session test-motherbrain
  $ tg -s test-motherbrain --allocate-node foo --type debian-smartjog
  $ tg -s test-motherbrain --allocate-node bar --type debian-smartjog
  $ tg -s test-motherbrain --deploy motherbrain-1.1 --type ansible --inventory foo,bar
"""

__version__ = "0.1"

import docopt, sys

import threading, strfmt, local, rest

def list_nodes(client, nodes):
	rows = [
		("name", "type", "status", "allocation"),
		("----", "----", "------", "----------"),
	]
	# get node status in parallel as it's slow
	pool = []
	is_up = {}
	for node in nodes:
		def f(node = node):
			is_up[node.name] = node.is_up()
		t = threading.Thread(target = f)
		t.daemon = True
		t.start()
		pool.append(t)
	for t in pool:
		t.join(5)
	# now display the info
	for node in nodes:
		row = [
			node.name,
			node.get_typename(),
			strfmt.Green("up") if is_up[node.name] else strfmt.Gray("unreachable")]
		if client.is_available(node):
			row.append(strfmt.Green("available"))
		elif client.is_allocated(node):
			row.append(strfmt.Blue("allocated"))
		elif client.is_quarantined(node):
			row.append(strfmt.Yellow("quarantined"))
		else:
			row.append(strfmt.Red("???"))
		rows.append(row)
	print strfmt.strcolalign(rows)

def list_sessions(client):
	rows = [
		("username", "name"),
		("--------", "----"),
	]
	for session in client.get_sessions():
		row = [session.username, session.name] 
		rows.append(row)
	print strfmt.strcolalign(rows)

def print_res(res):
	code, stdout, stderr = res
	if stderr:
		sys.stderr.write("%s\n" % strfmt.Gray(stderr))
	if stdout:
		sys.stdout.write("%s\n" % stdout)
	sys.exit(code)

def main():
	try:
		args = docopt.docopt(__doc__, version = __version__)
		if args["--local"]:
			client = local.Client(
				name = args["--grid"],
				ini = args["--manifest"])
		else:
			client = rest.Client(args["--controller"])
		# --- node-level operation ---
		if args["--node"]:
			if args["--session"]:
				node = client.get_session(args["--session"]).get_node(args["--node"])
			else:
				node = client.get_node(args["--node"])
			if args["--ping"]:
				sys.exit(0 if node.is_up() else 1)
			elif args["--install"]:
				pkg = client.get_package(
					typename = args["--type"],
					name = args["--install"])
				print_res(node.install(pkg))
			elif args["--uninstall"]:
				pkg = client.get_package(
					typename = args["--type"],
					name = args["--uninstall"])
				print_res(node.uninstall(pkg))
			elif args["--is-installed"]:
				pkg = client.get_package(
					typename = args["--type"],
					name = args["--is-installed"])
				sys.exit(0 if node.is_installed(pkg) else 1)
			elif args["--is-installable"]:
				pkg = client.get_package(
					typename = args["--type"],
					name = args["--is-installable"])
				sys.exit(0 if node.is_installable(pkg) else 1)
			elif args["--execute"]:
				print_res(node.execute(" ".join(args["ARGV"])))
		# --- session-level operation ---
		elif args["--session"]:
			session = client.open_session(args["--session"])
			if args["--list-nodes"]:
				list_nodes(client, [node for node in session])
			elif args["--allocate-node"]:
				raise NotImplementedError()
			else:
				raise NotImplementedError()
		# --- grid-level operation ---
		else:
			if args["--list-nodes"]:
				list_nodes(client, [node for node in client.get_nodes()])
			elif args["--add-node"]:
				node = client.add_node(name = args["--add-node"], ini = args["--manifest"])
				print "added %s" % node
			elif args["--remove-node"]:
				node = client.remove_node(name = args["--remove-node"])
				print "removed %s" % node
			elif args["--quarantine-node"]:
				client.quarantine_node(name = args["--quarantine-node"])
			elif args["--rehabilitate-node"]:
				client.rehabilitate_node(name = args["--rehabilitate-node"])
			elif args["--list-sessions"]:
				list_sessions(client)
			elif args["--open-session"]:
				client.open_session(args["--open-session"])
			elif args["--close-session"]:
				client.close_session(args["--close-session"])
		return 0
	except Exception as e:
		sys.stderr.write("%s" % strfmt.Gray("%s: %s\n" % (type(e).__name__, e)))
		return 1

if __name__ == "__main__": sys.exit(main())
