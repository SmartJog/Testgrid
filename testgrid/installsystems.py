# copyright (c) 2014 smartjog, all rights reserved.

"""
Python API for InstallSystems(tm).

References:
  https://github.com/seblu/installsystems

API:
  * Hypervisor(shell)
    - res = list_images(repo = None, ...)
    - res = list_domains(...)
    - res = create_domain(hostname, image_name, profile_name
    - res = start_domain(name, ...)
    - res = stop_domain(name, force = False, ...)
    - res = restart_domain(name, force = False, ...)
    - res = delete_domain(name, keep_all_storage = False, ...)
    - res = load(...)
    - res = disk(...)

Tutorial:
  >>> import installsystems
  >>> hv = installsystems.Hypervisor(...)
  >>> (to be continued) 

Requirements:
  on a domain creation, this framework expects a REST service at 127.0.0.1:9876
  able to deliver the --interfaces configuration on /<pf>/allocate.
  You may override {allocate, release}_address() if it doesn't suit your needs.
"""

__version__ = "0.1"

import unittest, getpass, httplib, abc, re

WAN = {
	"dns": "10.10.255.3",
	"dns_search": "wan",
	"ntp": "ntp.core.tvr.wan",
	"smtp": "smtp.core.tvr.wan",
	"mail_root": "root@smartjog.com",
	"mail_domain": "smartjog.com",
	"debian_repository": "debian",
	"is_repository": "isrepo.adm.wan",
	"ldap": "wantvr",
	"cc_server": "10.15.255.42",
}

LAN = {
	"dns": "192.168.11.253",
	"dns_search": "fr.lan",
	"ntp": "ntp.fr.lan",
	"smtp": "smtp.fr.lan",
	"debian_repository": "debian.fr.smartjog.net",
}

###########
# helpers #
###########

def normalized_playground_hostname(hostname):
	"normalize playground hkvm domain name"
	# REF: https://confluence.smartjog.net/display/INFRA/Playground#Playground-Rules"
	username = getpass.getuser()
	if len(hostname.split("-")) < 2:
		name = "%s-%s" % (username, hostname)
	comps = hostname.split(".")
	if len(comps) == 1:
		hostname += ".pg.fr.lan"
	elif len(comps) == 2:
		hostname += ".fr.lan"
	assert\
		re.match(r"\w+-\w+\.(pg|lab)\.fr\.lan", hostname),\
		"%s: invalid playground domain name" % hostname
	return hostname

def assert_ipv4(string):
	assert re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", string), "%s: expected ipv4" % string

def assert_interfaces(lst):
	assert isinstance(lst, (list, tuple))
	for item in lst:
		head = item
		if ":" in head:
			head, vlan = head.split(":")
		if "?" in head:
			head, iface = head.split("?")
		if "@" in head:
			head, gateway = head.split("@")
		if "/" in item:
			head, mask = head.split("/")
		if not head == "dhcp":
			assert_ipv4(head)

def allocate_address(key):
	cnx = httplib.HTTPConnection(host = "10.69.0.2", port = 9876)
	cnx.request("GET", "/%s/allocate" % key)
	res = cnx.getresponse()
	assert res.status == 200, res.reason
	addr = res.read()
	assert_ipv4(addr)
	return addr

def release_address(key, addr):
	cnx = httplib.HTTPConnection(host = "10.69.0.2", port = 9876)
	cnx.request("GET", "/%s/release/%s" % (key, addr))
	res = cnx.getresponse()
	assert res.status == 200, res.reason

class ImageParms(object):

	__metaclass__ = abc.ABCMeta

	def __init__(self, **kwargs):
		self.kwargs = kwargs

	def __str__(self):
		return self.kwargs

	def __getitem__(self, key):
		return self.kwargs[key]

	def __setitem__(self, key, value):
		self.kwargs[key] = value

	def __contains__(self, key):
		return key in self.kwargs

	@abc.abstractmethod
	def get_profile(self, hostname, profile_name):
		raise NotImplementedError()

	def get_raid_list(self):
		lst = []
		if "raid" in self:
			assert\
				self["raid"] in (0, 1, 4, 5, 6, 10),\
				"%i: illegal raid level" % self["raid"]
			lst += ["--raid", "%i" % self["raid"]]
		if "raid_devices" in self:
			lst += ["--raid-devices", self["raid_devices"]]
		if "raid_limit" in self and self["raid_limit"]:
			lst += ["--raid-limit"]
		if "raid_wait" in self and self["raid_wait"]:
			lst += ["--raid-wait"]
		return lst

	def get_bond_list(self):
		"handle bond-specific parameters"
		lst = []
		if "bond" in self:
			lst += ["--bond", self["bond"]]
		if "bond_slaves" in self:
			lst += ["--bond-slaves", " ".join(self["bond_slaves"])]
		if "bond_mode" in self:
			lst += ["--bond-mode", self["bond_mode"]]
		if "bond_hash" in self:
			lst += ["--bond-hash", self["bond_hash"]]
		return lst

	def get_cc_list(self):
		"handle cc-specific parameters"
		lst = []
		if "cc_enable" in self and self["cc_enable"]:
			lst += ["--cc-enable"]
		if "cc_server" in self:
			lst += ["--cc-server", self["cc_server"]]
		if "cc_port" in self:
			lst += ["--cc-port", self["cc_port"]]
		if "cc_login" in self:
			lst += ["--cc-login", self["cc_login"]]
		if "cc_password" in self:
			lst += ["--cd-password", self["cc_password"]]
		return lst

class DebianSJParms(ImageParms):
	"helper class to build the debian-smartjog image parameter list"

	def __init__(self, hostname, disks, **kwargs):
		kwargs["hostname"] = hostname
		kwargs["disks"] = disks
		super(DebianSJParms, self).__init__(**kwargs)

	@staticmethod
	def get_profile(hostname, profile_name):
		if ":" in profile_name:
			pf, cfg = profile_name.split(":")
		else:
			cfg = profile_name
		d = {
			"pg": lambda: DebianSJParms(
				hostname = normalized_playground_hostname(hostname),
				kvm = True,
				cpu = 1,
				memory = 512,
				interfaces = ("dhcp:2006",),
				password = "arkena",
				disks = ("rootfs:2048@vg",),
				dns = ("192.168.11.253",),
				ntp = "ntp.fr.lan",
				start = True,
				autostart = True),
			"std": lambda: DebianSJParms(
				hostname = hostname,
				kvm = True,
				cpu = 1,
				memory = 512,
				interfaces = (allocate_address(pf),),
				password = "arkena",
				disks = ("rootfs:2048@vg",),
				start = True,
				autostart = True),
		}
		assert cfg in d, "unsupported profile, '%s' not in %s" % (cfg, d.keys())
		return d[cfg]()

	def get_list(self):
		if "hostname" in self:
			lst = ["--hostname", self["hostname"]]
		if "domainname" in self:
			lst += ["--domainname", self["domainname"]]
		if "kvm" in self and self["kvm"]:
			lst += ["--kvm"]
		if "disks" in self:
			for item in self["disks"]:
				head = item
				if ":" in head:
					fs, head = item.split(":")
				if "@" in head:
					size, vgname = head.split("@")
					assert int(size) >= 2048, "%s: disk size must be >= 2048" % item
			lst += ["--disks", " ".join(self["disks"])]
		if "root_part_size" in self:
			lst += ["--root-part-size", self["root_part_size"]]
		if "cpu" in self:
			lst += ["--cpu", "%i" % self["cpu"]]
		if "memory" in self:
			lst += ["--memory", "%i" % self["memory"]]
		if "start" in self and self["start"]:
			lst += ["--start"]
		if "autostart" in self and self["autostart"]:
			lst += ["--autostart"]
		lst += self.get_raid_list()
		if "interfaces" in self:
			assert_interfaces(self["interfaces"])
			lst += ["--interfaces", " ".join(self["interfaces"])]
		if "dns" in self:
			lst += ["--dns", " ".join(self["dns"])]
		if "dns_search" in self:
			lst += ["--dns-search", " ".join(self["dns_search"])]
		if "debian_repository" in self:
			lst += ["--debian-repository", self["debian_repository"]]
		if "ldap" in self:
			assert ldap in (None, "lanfr", "lanus", "wantvr", "wanpmm", "wancap", "wanl3la")
			lst += ["--ldap", self["ldap"]]
		if "password" in self:
			lst += ["--passwd", self["password"]]
		if "reboot" in self and self["reboot"]:
			lst += ["--reboot"]
		if "smtp" in self:
			lst += ["--smtp", self["smtp"]]
		if "mail_root" in self:
			lst += ["--mail-root", self["mail_root"]]
		if "mail_domain" in self:
			lst += ["--mail-domain", self.kwargs["mail_domain"]]
		return lst

class IWebdavParms(DebianSJParms):
	"helper class to build the cdn-iwebdav image parameter list"

	def __init__(
		self,
		hostname,
		internal_gw,
		disks = ("root:10000",),
		**kwargs):
		kwargs["internal_gw"] = internal_gw
		super(IWebdavParms, self).__init__(
			hostname = hostname,
			disks = disks,
			**kwargs)

	def get_list(self):
		lst = super(IWebdavParms, self).get_list()
		if "internal_gw" in self:
			lst += ["--internal-gw", self["internal_gw"]]
		if "data_part_size" in self:
			assert\
				"root_part_size" in self,\
				"--data-part-size cannot be used without --root-part-size"
			lst += ["--data-part-size", self["data_part_size"]]
		return lst

class IHttpullParms(DebianSJParms):
	"helper class to build the cdn-ihttpull image parameter list"

	def __init__(
		self,
		hostname,
		disks,
		interfaces,
		dns,
		dns_search,
		internal_gw,
		**kwargs):
		kwargs["interfaces"] = interfaces
		kwargs["dns"] = dns
		kwargs["dns_search"] = dns_search
		kwargs["internal_gw"] = internal_gw
		super(IHttpullParms, self).__init__(
			hostname = hostname,
			disks = disks,
			**kwargs)

	def get_list(self):
		lst = super(IHttpullParms, self).get_list()
		if "internal_gw" in self:
			lst += ["--internal-gw", self["internal_gw"]]
		if "arch" in self:
			assert self["arch"] in ("i386", "amd64")
			lst += ["--arch", self["arch"]]
		if "update" in self and self["update"]:
			lst += ["--update"]
		if "extend_storage_level" in self:
			assert self["extend_storage_level"] == 1
			lst += ["--extend-storage-level", self["extend_storage_level"]]
		if "cache_directory" in self:
			lst += ["--cache-directory", self["cache_directory"]]
		return lst

class IFtpParms(DebianSJParms):
	"helper class to build the cdn-iftp image parameter list"

	def __init__(self, hostname, disks, dns, **kwargs):
		kwargs["dns"] = dns
		super(IFtpParms, self).__init__(hostname, disks, **kwargs)

class OHCacheParms(DebianSJParms):
	"helper class to build the cdn-ohcache image parameter list"

	def __init__(self, hostname, disks, internal_gw, **kwargs):
		kwargs["internal_gw"] = internal_gw
		super(OHCacheParms, self).__init__(
			hostname = hostname,
			disks = disks,
			**kwargs)

	@staticmethod
	def get_profile(hostname, profile_name):
		pf, cfg = profile_name.split(":")
		addr = allocate_address(pf)
		d = {
			#"phy-2disks-raid0": lambda: None,
			#"phy-2disks-raid1": lambda: None,
			#"phy-1disk": lambda: None,
			#"phy-lacp-bonding": lambda: None,
			"vm-nobtrfs": lambda: OHCacheParms(
				hostname = hostname,
				kvm = True,
				cpu = 4,
				memory = 2000,
				disks = ("root:10000",),
				interfaces = (addr,),
				internal_gw = "10.69.0.2",
				password = "arkena",
				start = True,
				autostart = True),
		}
		assert cfg in d, "unsupported profile, '%s' not in %s" % (cfg, d.keys())
		return d[cfg]()

	def get_list(self):
		lst = super(OHCacheParms, self).get_list()
		if "log_part_size" in self:
			lst += ("--log-part-size", self["log_part_size"])
		if "vip" in self:
			lst += ("--vip", " ".join(self["vip"]))
		if "internal_gw" in self:
			lst += ("--internal-gw", self["internal_gw"])
		lst += self.get_bond_list()
		if "arch" in self:
			assert self["arch"] in ("i386", "amd64")
			lst += ["--arch", self.kwargs["arch"]]
		if "update" in self and self["update"]:
			lst += ["--update"]
		lst += self.get_cc_list()
		if "extend_storage_level" in self:
			assert self["extend_storage_level"] in ("True", "False")
			lst += ["--extend-storage-level", self["extend_storage_level"]]
		return lst

def get_image_parms_for_profile(hostname, image_name, profile_name):
	if "debian-smartjog" in image_name:
		return DebianSJParms.get_profile(hostname = hostname, profile_name = profile_name)
	elif "cdn-itransmux" in image_name:
		raise NotImplementedError()
	elif "cdn-iwebdav" in image_name:
		raise NotImplementedError()
	elif "cdn-ihttpull" in image_name:
		raise NotImplementedError()
	elif "cdn-iftp" in image_name:
		raise NotImplementedError()
	elif "cdn-iicemp3" in image_name:
		raise NotImplementedError()
	elif "cdn-iadwzbip" in image_name:
		raise NotImplementedError()
	elif "cdn-storage-origin" in image_name:
		raise NotImplementedError()
	elif "cdn-oohpdwl" in image_name:
		raise NotImplementedError()
	elif "cdn-ohttchk" in image_name:
		raise NotImplementedError()
	elif "cdn-oadwzkh" in image_name:
		raise NotImplementedError()
	elif "cdn-oohsdwl" in image_name:
		raise NotImplementedError()
	elif "cdn-ohttflv" in image_name:
		raise NotImplementedError()
	elif "cdn-ohttmp3" in image_name:
		raise NotImplementedError()
	elif "cdn-ohcache" in image_name:
		return OHCacheParms.get_profile(hostname = hostname, profile_name = profile_name)
	else:
		raise Exception("%s: unsupported image, please report this" % image_name)

##############
# data model #
##############

class Hypervisor(object):

	def __init__(self, run):
		assert callable(run), "%s: invalid callback" % run
		self.run = lambda argv, *args, **kwargs: run(
			argv = argv,
			*args,
			**kwargs)

	def list_images(self, repo = None, *args, **kwargs):
		argv = (
			"is",
			"list",
			"%s/*" % repo if repo else "")
		return self.run(argv = argv, *args, **kwargs)

	def list_domains(self, *args, **kwargs):
		return self.run(argv = "virsh -q list --all", *args, **kwargs)

	def create_domain(
		self,
		image_name,
		image_parms,
		*args,
		**kwargs):
		argv = ["is", "install", image_name] + image_parms.get_list()
		return self.run(argv = argv, *args, **kwargs)

	def start_domain(self, name, *args, **kwargs):
		argv = (
			"virsh",
			"-q",
			"start",
			name)
		return self.run(argv = argv, *args, **kwargs)

	def stop_domain(self, name, force = False, *args, **kwargs):
		argv = (
			"virsh",
			"-q",
			"destroy" if force else "shutdown",
			name)
		return self.run(argv = argv, **kwargs)

	def restart_domain(self, name, force = False, *args, **kwargs):
		argv = (
			"virsh",
			"-q",
			"reset" if force else "reboot",
			name)
		return self.run(argv = argv, *args, **kwargs)

	def delete_domain(self, name, keep_all_storage = False, *args, **kwargs):
		argv = (
			"virsh",
			"-q",
			"undefine",
			"--remove-all-storage" if not keep_all_storage else "",
			name)
		return self.run(argv = argv, *args, **kwargs)

	def load(self, *args, **kwargs):
		return self.run(argv = r"uptime | sed 's/.*load average: [0-9]*.[0-9]*, [0-9]*.[0-9]*, \([0-9]*\).\([0-9]*\)/\1.\2/g'", *args, **kwargs)

	def disk(self, *args, **kwargs):
		return self.run(argv = "df --total | tail -n 1 | awk '{print $4}'", *args, **kwargs)

##############
# unit tests #
##############

class Runner(object):

	def __call__(self, argv, *args, **kwargs): pass

class SelfTest(unittest.TestCase):

	def setUp(self):
		self.hv = Hypervisor(run = Runner())

	def test101(self): pass

if __name__ == "__main__": unittest.main(verbosity = 2)
