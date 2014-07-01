# copyright (c) 2014 smartjog, released under the GPL license.

"""
Testgrid command-line utility.

Usage:
  tg [[-m INI] -l [-g NAME]|-c HOST] --list-nodes
  tg [[-m INI] -l [-g NAME]|-c HOST] --add-node NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] --remove-node NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] --quarantine-node NAME REASON
  tg [[-m INI] -l [-g NAME]|-c HOST] --rehabilitate-node NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] --list-sessions
  tg [[-m INI] -l [-g NAME]|-c HOST] --open-session NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] --terminate-session NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] -s NAME --list-nodes
  tg [[-m INI] -l [-g NAME]|-c HOST] -s NAME --allocate-node NAME NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] -s NAME --release-node NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] -s NAME --deploy NAME...
  tg [[-m INI] -l [-g NAME]|-c HOST] -s NAME --undeploy
  tg [[-m INI] -l [-g NAME]|-c HOST] [-s NAME] -n NAME --ping
  tg [[-m INI] -l [-g NAME]|-c HOST] [-s NAME] -n NAME --install NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] [-s NAME] -n NAME --uninstall NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] [-s NAME] -n NAME --is-installed NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] [-s NAME] -n NAME --is-installable NAME
  tg [[-m INI] -l [-g NAME]|-c HOST] [-s NAME] -n NAME --execute [--] ARGV...
  tg --version
  tg --help

Options:
  -m INI, --manifest INI      comma-separated paths or URIs [default: ~/testgrid.ini]
  -l, --local		      use a local client
  -c HOST, --controller HOST  set controller hoststring [default: qa.lab.fr.lan:8080]
  -g NAME, --grid NAME	      set grid section NAME in the manifest [default: grid]
  -n NAME, --node NAME	      set node NAME
  -s NAME, --session NAME     set session NAME
  --list-nodes		      list nodes in selected container
  --add-node NAME	      add named node parsed from manifest
  --remove-node NAME	      remove named node
  --quarantine-node NAME      place a node in quarantine
  --rehabilitate-node NAME    rehabilitate a quarantined node
  --list-sessions	      list sessions
  --open-session NAME	      open, or re-open if it exists, named session
  --terminate-session NAME    undeploy session nodes and remove session
  --allocate-node NAME	      allocate a node to the session
  --release-node NAME	      release a node from the session
  --deploy PKG...	      deploy named packages, allocated nodes automatically
  --undeploy		      undeploy named packages, release nodes automatically
  --ping		      ping node
  --install NAME	      install named packaged on node
  --uninstall NAME	      uninstall named package
  --is-installed NAME	      succeed if named package is installed on node
  --is-installable NAME	      succeed if named package is installable on node
  -e, --execute		      execute command on node
  -h, --help		      show help
  --version		      show version

Example, simple debian package deployment:
  $ tg --create-session test-fleche
  $ tg --session test-fleche --deploy deb:fleche:16.5-1

Example, dynamic inventory for ansible:
  $ cat > mb.ini <<EOF
  [foo]
  type: isnode
  image_name: debian-smartjog
  [bar]
  type: isnode
  image_name: debian-smartjog
  EOF
  $ tg --generate-dynamic-inventory mb.ini
  generated mb.py
  $ ansible-playbook -i mb.py ...
"""

__version__ = "0.1~20140506-1"

import threading, testgrid, sys

class Color(object):

	def __init__(self, string, code = None):
		if not code:
			m = re.search("\033\[0;(.*)m(.*)\033\[0m", string)
			assert m, "%s: expected escaped string" % string
			self.code = int(m.group(1))
			self.string = m.group(2)
		else:
			self.string = string
			self.code = code

	def __str__(self):
	      return "\033[0;%im%s\033[0m" % (self.code, self.string)

	def __len__(self):
		return len(self.string)

	def __add__(self, other):
		return Color(self.string + other, code = self.code)

	def __getattr__(self, key):
		return getattr(self.string, key)

def Red(string):
	return Color(string, code = 91)

def Blue(string):
	return Color(string, code = 94)

def Gray(string):
	return Color(string, code = 90)

def Green(string):
	return Color(string, code = 92)

def Yellow(string):
	return Color(string, code = 93)

def Purple(string):
	return Color(string, code = 95)

def list_nodes(client, nodes):
	rows = [
		("name", "type", "status", "allocation", "username", "session"),
		("----", "----", "------", "----------", "--------", "-------"),
	]
	# fetch node status concurrently
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
	# display result
	for node in nodes:
		session = client.get_node_session(node)
		row = [
			node.name,
			node.get_typename(),
			"up" if is_up[node.name] else "unreachable"]
		if client.is_available(node):
			row.append("available")
		elif client.is_allocated(node):
			row.append("allocated")
		elif client.is_quarantined(node):
			row.append("quarantined")
		else:
			row.append("unknown") # BUG: should not happen
		if session:
			row.append(session.user.name)
			row.append(session.name)
		else:
			row.append("-")
			row.append("-")
		rows.append(row)
	print testgrid.strfmt.strcolalign(rows)

def list_sessions(client):
	rows = [
		("username", "name"),
		("--------", "----"),
	]
	for session in client.get_sessions():
		row = [session.username, session.name]
		rows.append(row)
	print testgrid.strfmt.strcolalign(rows)

def print_res(res):
	code, stdout, stderr = res
	if stderr:
		sys.stderr.write("%s\n" % strfmt.Gray(stderr))
	if stdout:
		sys.stdout.write("%s\n" % stdout)
	sys.exit(code)

def get_package(client, name):
	assert ":" in name, "package name format is <repo>:<name>[:<version>]"
	key, name = name.split(":", 1)
	if ":" in name:
		name, version = name.split(":", 1)
	else:
		version = None
	typename = {
		"deb": "DebianPackage",
		# add package types here
	}
	assert key in typename, "unsupported repo, '%s' not in %s" % (key, typename.keys())
	return client.get_package(
		typename = typename[key],
		name = name,
		version = version)

def main():
	try:
		######################
		# instanciate client #
		######################
		opts = testgrid.docopt.docopt(__doc__, version = __version__)
		if opts["--local"]:
			client = testgrid.local.Client(
				gridname = opts["--grid"],
				ini = opts["--manifest"])
		else:
			client = testgrid.rest.Client(hoststring = opts["--controller"])
		#########################
		# handle node-level op. #
		#########################
		if opts["--node"]:
			if opts["--session"]:
				session = testgrid.client.get_session(opts["--session"])
				for node in session:
					if node.name == opts["--node"]:
						break
				else:
					raise Exception("node '%s' not in session '%s'" % (opts["--node"], session))
			else:
				node = testgrid.client.get_node(opts["--node"])
			if opts["--ping"]:
				sys.exit(0 if node.is_up() else 1)
			elif opts["--install"]:
				print_res(
					node.install(
						get_package(client, opts["--install"])))
			elif opts["--uninstall"]:
				print_res(
					node.uninstall(
						get_package(client, opts["--uninstall"])))
			elif opts["--is-installed"]:
				sys.exit(
					0 if node.is_installed(
						get_package(client, opts["--is-installed"])) else 1)
			elif opts["--is-installable"]:
				sys.exit(
					0 if node.is_installable(
						get_package(client, opts["--is-installable"])) else 1)
			elif opts["--execute"]:
				print_res(node.execute(" ".join(opts["ARGV"])))
		############################
		# handle session-level op. #
		############################
		elif opts["--session"]:
			session = client.open_session(opts["--session"])
			if opts["--list-nodes"]:
				list_nodes(client, [node for node in session])
			elif opts["--allocate-node"]:
				parser = testgrid.parser.Parser(ini = opts["--manifest"])
				_opts = {}
				for key, value in parser.conf.items(opts["NAME"]):
					_opts[key] = value
				#_opts["hostname"] = opts["--allocate-node"]
				node = session.allocate_node(name = opts["--allocate-node"], **_opts)
			elif opts["--release-node"]:
				node = client.get_node(opts["--release-node"])
				session.release(node)
			elif opts["--deploy"]:
				packages = []
				for pkg in opts["PKG"]:
					package = client.get_package("DebianPackage", pkg)
					packages.append(package)
				plans = session.deploy(packages)
				for p, node in plans:
					print "package %s installed on node %s" % (p, node)
			elif opts["--undeploy"]:
				session.undeploy()
		#########################
		# handle grid-level op. #
		#########################
		else:
			if opts["--list-nodes"]:
				list_nodes(client, [node for node in client.get_nodes()])
			elif opts["--add-node"]:
				node = client.add_node(name = opts["--add-node"], ini = opts["--manifest"])
			elif opts["--remove-node"]:
				node = client.remove_node(name = opts["--remove-node"])
			elif opts["--quarantine-node"]:
				client.quarantine_node(name = opts["--quarantine-node"], reason = opts["REASON"])
			elif opts["--rehabilitate-node"]:
				client.rehabilitate_node(name = opts["--rehabilitate-node"])
			elif opts["--list-sessions"]:
				list_sessions(client)
			elif opts["--open-session"]:
				session = client.open_session(opts["--open-session"])
			elif opts["--terminate-session"]:
				client.terminate_session(opts["--terminate-session"])
	except Exception as e:
		raise
		sys.stderr.write("\033[0;90merror: %s\033[m\n" % e)
		sys.exit(1)

if __name__ == "__main__": main()
