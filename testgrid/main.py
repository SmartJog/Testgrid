# copyright (c) 2014 smartjog, released under the GPL license.

"""
Testgrid command-line utility.

Usage:
  tg [-m INI] [-l|-c HOST] [-g KEY] --list-nodes
  tg [-m INI] [-l|-c HOST] [-g KEY] --add-node KEY --type NAME
  tg [-m INI] [-l|-c HOST] [-g KEY] --remove-node KEY
  tg [-m INI] [-l|-c HOST] [-g KEY] --repair-node KEY
  tg [-m INI] [-l|-c HOST] [-g KEY] [--session KEY] --node KEY --install PKG --type NAME
  tg [-m INI] [-l|-c HOST] [-g KEY] [--session KEY] --node KEY --uninstall PKG
  tg [-m INI] [-l|-c HOST] [-g KEY] [--session KEY] --node KEY --execute ARGV...
  tg [-m INI] [-l|-c HOST] [-g KEY] --list-sessions
  tg [-m INI] [-l|-c HOST] [-g KEY] --open-session KEY
  tg [-m INI] [-l|-c HOST] [-g KEY] --close-session KEY
  tg [-m INI] [-l|-c HOST] [-g KEY] --session KEY --list-nodes
  tg [-m INI] [-l|-c HOST] [-g KEY] --session KEY --allocate-node KEY --type NAME
  tg [-m INI] [-l|-c HOST] [-g KEY] --session KEY --release-node KEY
  tg [-m INI] [-l|-c HOST] [-g KEY] --session KEY --deploy PKG --type NAME
  tg [-m INI] [-l|-c HOST] [-g KEY] --session KEY --undeploy PKG
  tg --version
  tg --help

Options:
  -g KEY, --grid KEY          set grid section key in the manifest [default: grid]
  -n KEY, --node KEY          set node key
  -s KEY, --session KEY       set session key
  --list-nodes                list nodes in selected container
  --add-node KEY              ...
  --remove-node KEY           ...
  --repair-node KEY           rehabilitate a quarantined node
  --install PKG               ...
  --type NAME                 specify an object type
  --uninstall PKG             ...
  --execute                   ...
  --list-sessions             ...
  --open-session KEY          ...
  --close-session KEY         ...
  --allocate-node KEY         ...
  --release-node KEY          ...
  --deploy PKG                ...
  --undeploy PKG              ...
  -m INI, --manifest INI      comma-separated list of .ini filepaths or URIs [default: ~/grid.ini]
  -l, --local                 use a local client
  -c HOST, --controller HOST  set controller hoststring for a REST client [default: qa.lab.fr.lan:8080]
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

import strfmt, local, rest

def grid_list_nodes(client):
	text = "node:type:status\n----:----:------\n"
	for node in client.get_nodes():
		if client.is_available(node):
			text += "%s:%s:%s\n" % (node, node.get_typename(), strfmt.green("available"))
		elif client.is_allocated(node):
			text += "%s:%s:%s\n" % (node, node.get_typename(), strfmt.blue("allocated"))
		elif client.is_quarantined(node):
			text += "%s:%s:%s\n" % (node, node.get_typename(), strfmt.red("quarantined"))
	print strfmt.strcolalign(text)

def grid_list_sessions(client):
	raise NotImplementedError()

def main():
	try:
		args = docopt.docopt(__doc__, version = __version__)
		if args["--local"]:
			client = local.Client(
				name = args["--grid"],
				ini = args["--manifest"])
		else:
			client = rest.Client(args["--controller"])
		if args["--session"]:
			raise NotImplementedError()
		elif args["--node"]:
			if args["--session"]:
				node = client.get_session(args["--session"]).get_node(args["--node"])
			else:
				node = client.get_node(args["--node"])
			if args["--install"]:
				node.install(name = args["--install"], type = args["--type"])
			elif args["--uninstall"]:
				node.uninstall(name = args["--uninstall"])
		else:
			# work on grid...
			if args["--list-nodes"]:
				grid_list_nodes(client)
			elif args["--add-node"]:
				client.add_node(key = args["--add-node"], type = args["--type"])
			elif args["--remove-node"]:
				client.remove_node(key = args["--remove-node"])
			elif args["--repair-node"]:
				client.repair_node(client, key = args["--repair-node"])
			elif args["--list-sessions"]:
				grid_list_sessions(client)
			elif args["--open-session"]:
				client.open_session(args["--open-session"])
			elif args["--close-session"]:
				client.close_session(args["--close-session"])
		return 0
	except Exception as e:
		sys.stderr.write(strfmt.gray("%s: %s\n" % (type(e).__name__, e)))
		return 1

if __name__ == "__main__": sys.exit(main())
