# copyright (c) 2014 smartjog, released under the GPL license.

"vagrant.Guest adapter for testgrid"

import ansible.inventory, ansible.runner, testgrid, unittest, time, os

APT_CONF = """
#
# copyright (c) 2014 arkena, all rights reserved.
# configure apt proxy.
# move to /etc/apt/.
#

Acquire {
	http {
		Proxy "http://proxy:3128";
		Proxy::debian "DIRECT";
		Proxy::debian.fr.smartjog.net "DIRECT";
	}
	https {
		Proxy "https://proxy:3128";
		Proxy::debian "DIRECT";
		Proxy::debian.fr.smartjog.net "DIRECT";
	}
}
"""

SJ_LIST = """
#
# copyright (c) 2014 arkena, all rights reserved.
# configure apt repository.
# move to /etc/apt/sources.list/.
#

deb http://debian.fr.smartjog.net/debian-smartjog/all ./
"""

PROXY_SH = """
#
# copyright (c) 2014 arkena, all rights reserved.
# configure proxy in shell environment
# move to /etc/profile.d/.
#

export https_proxy="http://proxy:3128"
export http_proxy="http://proxy:3128"
export no_proxy=".lan,localhost,127.0.0.1"
"""

MOTD = """
*************************************
     Arkena Test Box, Welcome...
  Contact qa@tdf-ms.com for support
*************************************
"""

ID_RSA = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAs4sqEp0o8rED8eF2fQg4sNNVADoFsywPWE9LSpHk28Wp32tv
chsSkLxiYyJhSQcvoMjHgzbYBgbZ+buP8tlMEz++f0lXB5INYHbMogKKFO05fAdu
rocCzWzEP/LfrEELk0SimIRFSi9phFSptWxTGX7akTs9N9BCPKFBqbVsKWijAPQS
MwF4oefkuPkhfe4mP1fZAelEVRo7xgX2hznTNfGjvn213L9CiKGhlXi8LFEO3EQ7
aBUjVg/bb36IT8dne5HMslmBOTVzSv9yPJTKkmCHBUl1j140B3jxIzsWpSBnu8WM
rsDcU3CQVP3O/mCAyIkC7FoymRlWzaI0kjbp2wIDAQABAoIBAB5AGkyckiOh04pT
dIVId1TDppStMfyoNcWpRoQ/5JFq0l5EWbid+xjLxL/zMPT+8vViHstq2CbbzKoZ
Af3mwryThuMnVjR+VSalnYDGcMFp3r+Y+PsK4FwAMWic4TbCltKvQ73yu0Hujxau
tRFOOQoYp3bExmG7Aw34FXokiR7IrD78fR4e1jNwRrK3f6vjp02xvf1vmSZT4gPE
2FnF5XuMrRVYHCaGNTzBfLYdGB5qacL2iLxRnwId3tSbwnI2PLZAG9gixzKo92uv
Z0RshjoIhQKNHg2rXANvMvj/zrXHZC8fLZ4zw1SU9O48FLCrmiVbXvDrgtL8/d3y
uxm+aYECgYEA2C/YarM7YLljoV0Zg+L7++/0W+sEvkcKN6hvOjLaJ7p+55ytu3Ng
Z+ns+xfVfXFTgZ7ntLJr/L6dlQCgDmTC/MmjYva1+xkQX9Iu+Fsp4JqIpysKgODu
U0BbptcnVVviPdYqD9atxogS13u4XuI/DpKJ3ep0vkLEe7T/kssQ9+ECgYEA1JvE
btKinTYImGwBUQTSGNgmtPt/nMb0sngInRv75vxZQ5LglvunkK+0wWTJ6TEr0sKp
7A0accLHzYoet+nLu7B5j/syB42GK23mD8sqZoAyCWuPwwyIOpMzNooleXiVJtMf
BIhJ8yYx9iqf1btmPOlQg6N60CKWrd2AbyHy6TsCgYEAvHbxdwtrL0ZPGcRc0wIV
ZKvqXhuDVhH+UUkwNg9Q6aOGsImBV1Ic8FoZM0iy4Bnkj7KlEn0c8QiHvfb+ka27
4r4yBrtHKHDQOoi0U+S9nEV77ifyjyoH+mG3xLn6W0qv7/J9VrNzaQkFS/9aWrVn
/V84e1LClX8FZUcEKseGsmECgYA3nD63FhU+tcFtzOJTRMWHhhIpyJbKdSfP/qGS
Jp2u/1aB3EsucsiTicHny+scOaZSzGQRwCOomeAVHQmH5XlKsJA7XuLpItVzSp2g
h+2hPerYl+/UftSrLZF5tIy0xxuMOjCkyNk+5kCvONrx1sCZMhXDOOGIy2NKOuO7
LdARvQKBgQCFQ/N95npfufV/WOgMaWUfGk7zCbNhW2xe5uSyTAV9PQhl0xwMrvau
LbpsqIpKJ3JlL5Fdg+o7wuV3yU17A+jnaXX6T4Am7NP8+si3OpmXwbXGRg36S7qM
B+azc6rhd3lKup7qMA2j3+MrDgKeWhMwYFbnvORPigHagc4Gj9ynaA==
-----END RSA PRIVATE KEY-----
"""

ID_RSA_PUB = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCziyoSnSjysQPx4XZ9CDiw01UAOgWzLA9YT0tKkeTbxanfa29yGxKQvGJjImFJBy+gyMeDNtgGBtn5u4/y2UwTP75/SVcHkg1gdsyiAooU7Tl8B26uhwLNbMQ/8t+sQQuTRKKYhEVKL2mEVKm1bFMZftqROz030EI8oUGptWwpaKMA9BIzAXih5+S4+SF97iY/V9kB6URVGjvGBfaHOdM18aO+fbXcv0KIoaGVeLwsUQ7cRDtoFSNWD9tvfohPx2d7kcyyWYE5NXNK/3I8lMqSYIcFSXWPXjQHePEjOxalIGe7xYyuwNxTcJBU/c7+YIDIiQLsWjKZGVbNojSSNunb vagrant@vagrant-debian-wheezy64"""

PROVISION_SH = """
#!/bin/bash
#
# copyright (c) 2014 arkena, all rights reserved.
# testbox provisioning script.
#

set -e -x # abort on error, trace execution

test $USER = root # assert this script is run as root

#
# install deploy keys
#

for ITEM in root:/root vagrant:/home/vagrant
do
	_USER=$(echo $ITEM | cut -d: -f1)
	_HOME=$(echo $ITEM | cut -d: -f2)
	sudo -u $_USER mkdir -p $_HOME/.ssh
	sudo -u $_USER cp /vagrant/ssh.config $_HOME/.ssh/config
	sudo -u $_USER cp /vagrant/id_rsa $_HOME/.ssh/
	sudo -u $_USER chmod 400 $_HOME/.ssh/id_rsa
	sudo -u $_USER cp /vagrant/id_rsa.pub $_HOME/.ssh/
	sudo -u $_USER chmod 400 $_HOME/.ssh/id_rsa.pub
done

#
# setup apt.
#

ln -fs /vagrant/apt.conf /etc/apt/
ln -fs /vagrant/sj.list /etc/apt/sources.list.d/
indexing="** indexing repository, this may take a while... **"
echo "$indexing"
apt-get update -qq || true # force success
apt-get install -qqy --force-yes debian-smartjog-keyring
echo "$indexing"
apt-get update -qq

#
# setup profile.
#

ln -fs /vagrant/proxy.sh /etc/profile.d/proxy.sh
ln -fs /vagrant/motd /etc/motd

#
# install git
#

apt-get install -qqy --force-yes git

#
# end.
#

echo "** all done **"
"""

class Node(testgrid.model.Node):

	def __init__(self, name, root):
		super(Node, self).__init__(name)
		self.root = root
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

	def create(self, **opts):
		use_proxy = opts.get("use_proxy", False)
		if not os.path.exists(self.root):
			os.mkdir(self.root)
		# generate all files for basic provisioning:
		apt_conf_path = os.path.join(self.root, "apt.conf")
		with open(apt_conf_path, "w+") as f:
			if use_proxy:
				f.write(APT_CONF)
		sj_list_path = os.path.join(self.root, "sj.list")
		with open(sj_list_path, "w+") as f:
			f.write(SJ_LIST)
		proxy_sh_path = os.path.join(self.root, "proxy.sh")
		with open(proxy_sh_path, "w+") as f:
			if use_proxy:
				f.write(PROXY_SH)
		motd_path = os.path.join(self.root, "motd")
		with open(motd_path, "w+") as f:
			f.write(MOTD)
		id_rsa_path = os.path.join(self.root, "id_rsa")
		with open(id_rsa_path, "w+") as f:
			f.write(ID_RSA)
		id_rsa_pub_path = os.path.join(self.root, "id_rsa.pub")
		with open(id_rsa_pub_path, "w+") as f:
			f.write(ID_RSA_PUB)
		self.guest.init(**opts)
		self.guest.up()

	def terminate(self):
		self.guest.destroy()
		self.guest.fini()

	def get_installed_packages(self):
		"return the list of installed packages"
		raise NotImplementedError()

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
		name = opts.get("name", "node-%i" % int(time.time()))
		node = Node(name = name, root = os.path.join(self.root, name))
		node.create(**opts)
		return node

	def terminate_node(self, node):
		node.terminate()

##############
# unit tests #
##############

class SelfTest(unittest.TestCase):

	timeout = 70

	def test(self):
		grid = Grid(name = "test", root = "/tmp")
		session = grid.open_session(name = "test")
		node = session.allocate_node(
			box_name = "wheezy64",
			bridge = os.getenv("BRIDGE", testgrid.vagrant.DEFAULT_BRIDGE))
		assert node.is_up()

if __name__ == "__main__": unittest.main(verbosity = 2)
