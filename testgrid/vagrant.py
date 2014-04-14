# copyright (c) 2014 florent claerhout, released under the MIT license.

import subprocess, unittest, shutil, pipes, os

def run(argv, warn_only = False):
	sp = subprocess.Popen(
		args = argv,
		shell = isinstance(argv, str), # use shell if $argv is a string
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = sp.communicate()
	code = sp.returncode
	if code and not warn_only:
		raise Exception("%s: command failed (%i), %s" % (argv, code, stderr.strip()))
	return (code, stdout, stderr)

URL = {
	"centos63-64": "https://dl.dropbox.com/u/7225008/Vagrant/CentOS-6.3-x86_64-minimal.box",
	"squeeze64": "http://www.emken.biz/vagrant-boxes/debsqueeze64.box",
	"wheezy64": "https://dl.dropboxusercontent.com/s/xymcvez85i29lym/vagrant-debian-wheezy64.box",
}

class Guest(object):

	def __init__(self, root):
		self.root = os.path.abspath(os.path.expanduser(root))
		self.vagrantfile_path = os.path.join(self.root, "Vagrantfile")

	def is_initialized(self):
		return os.path.exists(self.vagrantfile_path)

	def init(
		self,
		bridge,
		box_name,
		box_url = None,
		cpucap = 25,
		memory = 256,
		provision_path = None):
		if not os.path.exists(self.root):
			os.mkdir(self.root)
		assert\
			not self.is_initialized(),\
			"%s: guest already initialized" % self.vagrantfile_path
		if not box_url:
			assert box_name in URL, "%s: unknown url for this box" % box_name
			box_url = URL[box_name]
		if provision_path:
			provision = 'config.vm.provision :shell, :path => "%s"' % provision_path
		else:
			provision = ""
		parms = {
			"box": box_name,
			"box_url": box_url,
			"bridge": bridge,
			"cpucap": cpucap,
			"memory": memory,
			"provision": provision,
		}
		with open(self.vagrantfile_path, "w+") as f:
			f.write("""
				Vagrant.configure("2") do |config|
					config.vm.box = "%(box)s"
					config.vm.box_url = "%(box_url)s"
					config.vm.network :public_network, :bridge => "%(bridge)s"
					config.vm.provider "virtualbox" do |v|
						v.customize ["modifyvm", :id, "--cpuexecutioncap", "%(cpucap)i"]
						v.memory = %(memory)i
					end
					%(provision)s
				end
			""" % parms)

	def fini(self):
		shutil.rmtree(self.root)

	def _get_cmd(self, argv):
		assert\
			os.path.exists(self.vagrantfile_path),\
			"%s: guest not yet initialized" % self.vagrantfile_path
		return "VAGRANT_CWD=%s vagrant %s" % (self.root, argv)

	def up(self):
		return run(self._get_cmd("up"))

	def halt(self):
		return run(self._get_cmd("halt"))

	def reload(self):
		return run(self._get_cmd("reload"))

	def destroy(self):
		return run(self._get_cmd("destroy --force"))
	
	def run(self, argv, warn_only = False):
		return run(self._get_cmd("ssh -c %s" % pipes.quote(argv)))

	def get_status(self):
		code, stdout, stderr = run(self._get_cmd("status --machine-readable"))
		for line in stdout.splitlines():
			id, _, key, value = line.split(",")
			if key == "state":
				return value

	def is_running(self):
		return self.get_status() == "running"

	def get_inet_addresses(self):
		# FIXME
		# this is for linux only
		code, stdout, stderr = self.run("ip -o -4 addr")
		res = {}
		for line in stdout.splitlines():
			id, data = line.split(":")
			data = data.split()
			name = data[0]
			inet_val = data[2]
			ip4, prefix = inet_val.split("/")
			res[name] = ip4
		return res

	def get_bridged_interface_name(self):
		# FIXME
		# 1. find network of the host bridging interface
		# 2. find the matching guest interface
		return "eth1"

##############
# unit tests #
##############

DEFAULT_BRIDGE = "en0: Wi-Fi (AirPort)" # Macbook + WiFi

class SelfTest(unittest.TestCase):

	def setUp(self):
		self.guest = Guest("/tmp/foo")
		self.guest.init(
			box_name = "wheezy64",
			bridge = os.getenv("BRIDGE", DEFAULT_BRIDGE))

	def tearDown(self):
		self.guest.fini()

	def test(self):
		self.guest.up()
		assert self.guest.is_running()
		self.guest.destroy()

	def test_double_init(self):
		self.assertRaises(
			Exception,
			self.guest.init,
			box_name = "wheezy64",
			bridge = os.getenv("BRIDGE", DEFAULT_BRIDGE))

if __name__ == "__main__": unittest.main(verbosity = 2)
