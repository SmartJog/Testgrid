# copyright (c) 2014 smartjog, released under the GPL license.

"vagrant.Guest adapter for testgrid"

import ansible.inventory, ansible.runner, testgrid, time, os

class Node(testgrid.model.Node):

	def __init__(self, name, root):
		super(Node, self).__init__(name)
		self.guest = testgrid.vagrant.Guest(root = root)

	def get_subnets(self):
		raise NotImplementedError()

	def get_typename(self):
		return "vagrant box"

	def has_support(self, **opts):
		raise NotImplementedError()

	def is_up(self):
		return self.guest.is_running()

	def get_load(self):
		raise NotImplementedError()

	def join(self, subnet):
		raise NotImplementedError()

	def leave(self, subnet):
		raise NotImplementedError()

	def get_hoststring(self):
		ifname = self.guest.get_bridged_interface_name()
		ifaddr = self.guest.get_inet_addresses()[ifname]
		return testgrid.model.Hoststring("vagrant@%s" % ifaddr)

class Grid(testgrid.model.Grid):

	def __init__(self, name, root, nodes = None, subnets = None, sessions = None):
		nodes = nodes or []
		for name in os.listdir(root):
			vagrantfile_path = os.path.join(root, name, "Vagrantfile")
			if os.path.exists(vagrantfile_path):
				node = Node(name = name, root = os.path.join(root, name))
				nodes.append(node)
		super(Grid, self).__init__(
			name = name,
			nodes = nodes,
			subnets = subnets,
			sessions = sessions)
		self.root = root

	def create_node(self, pkg = None, **opts):
		name = opts.get("name", "node%i" % int(time.time()))
		node = Node(name = name, root = os.path.join(self.path, name))
		node.guest.init(**opts)
		node.guest.up()
		return node

	def terminate_node(self, node):
		node.guest.destroy()
