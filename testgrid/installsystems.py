# copyright (c) 2014 smartjog, all rights reserved.

"""
Python API for InstallSystems(tm).

References:
  https://github.com/seblu/installsystems

API:
  * Hypervisor(shell)
    - res = list_images(repo = None, ...)
    - res = list_domains(...)
    - res = create_domain(hostname, image_parms, ...)
    - res = start_domain(name, ...)
    - res = stop_domain(name, force = False, ...)
    - res = restart_domain(name, force = False, ...)
    - res = delete_domain(name, keep_all_storage = False, ...)
    - res = load(...)
    - res = disk(...)

Tutorial:
  >>> import installsystems, myrunner
  >>> hv = installsystems.Hypervisor(myrunner.run)
  >>> image_parms = DebianSJProfile.get_profile("pg")
  >>> hv.create_domain(image_parms.image_name, image_parms)
  >>> ...

Requirements:
  on a domain creation, a REST service is expected at 10.69.0.2:9876:
  1/ deliver the --interfaces configuration at /<store_name>/allocate,
  2/ deliver the internal_gw value at /<store_name>/gateway
  3/ deliver the dns value at /<store_name>/dns
  4/ deliver the dns_search value at /<store_name>/dns_search
  5/ deliver the list of store names at /names.

Developers -- ading parms class/profiles:
  * the constructor lists required parameters
  * .profiles is a dict of constructors func(hostname[, store_name])
  * fill-in get_list() with the new parameters
"""

import unittest, getpass, httplib, inspect, abc, re

###########
# helpers #
###########

def normalized_playground_hostname(hostname):
	"""
	Normalize playground hkvm domain name.
	See https://confluence.smartjog.net/display/INFRA/Playground#Playground-Rules
	"""
	if len(hostname.split("-")) < 2:
		hostname = "%s-%s" % (getpass.getuser(), hostname)
	comps = hostname.split(".")
	if len(comps) == 1:
		hostname += ".pg.fr.lan"
	elif len(comps) == 2:
		hostname += ".fr.lan"
	assert\
		re.match(r"\w+-\w+\.(pg|lab)\.fr\.lan", hostname),\
		"%s: invalid playground domain name" % hostname
	return hostname

def parse_interface(interface):
	"return dict of interface as <address>/<mask>@<gateway>?<iface>:<vlan>"
	res = {"address": interface}
	if ":" in res["address"]:
		res["address"], res["vlan"] = res["address"].split(":")
	if "?" in res["address"]:
		res["address"], res["iface"] = res["address"].split("?")
	if "@" in res["address"]:
		res["address"], res["gateway"] = res["address"].split("@")
	if "/" in res["address"]:
		res["address"], res["mask"] = res["address"].split("/")
	assert\
		res["address"] == "dhcp"\
		or re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", res["address"]),\
		"%s: expected 'dhcp' or ip4 address" % res["address"]
	return res

STORE_HOSTNAME = "10.69.0.2"

STORE_PORT = 9876

class Stores(object):

	_instance = None # singleton

	def __new__(cls):
		if not cls._instance:
			cls._instance = super(Stores, cls).__new__(cls)
		return cls._instance

	def __getattr__(self, key):
		if key == "cnx":
			self.cnx = httplib.HTTPConnection(host = STORE_HOSTNAME, port = STORE_PORT)
			return self.cnx
		raise AttributeError(key)

	@staticmethod
	def get_names():
		return ("cdn", "cw", "vp", "tg", "srv", "pub")

	def get(self, path):
		try:
			self.cnx.request("GET", path)
			res = self.cnx.getresponse()
			assert res.status == 200, "%i, %s" % (res.status, res.reason)
			return res.read()
		except Exception as e:
			raise Exception("IPStore GET %s:%s%s: %s" % (
				STORE_HOSTNAME,
				STORE_PORT,
				path,
				e))

class Store(object):

	_instances = {} # one instance per store name

	def __new__(cls, name):
		if not name in Store._instances:
			Store._instances[name] = super(Store, cls).__new__(cls, name)
		return Store._instances[name]

	def __init__(self, name):
		self.name = name

	def get(self, path):
		return Stores().get("/%s%s" % (self.name, path))

class LazyStoreValue(object):

	store_method_name = None

	def __init__(self, store_name):
		self.store_name = store_name

	def __getattr__(self, key):
		if key == "value":
			self.value = Store(self.store_name).get(self.path)
			return self.value
		super(Address, self).__getattr__(key)

	def __str__(self):
		return "%s" % self.value

class DnsSearch(LazyStoreValue):

	path = "/dns_search"

class Gateway(LazyStoreValue):

	path = "/gateway"

class Address(LazyStoreValue):

	path = "/allocate"

class Dns(LazyStoreValue):

	path = "/dns"

class Profile(object):
	"profile abstract class"

	__metaclass__ = abc.ABCMeta

	def __init__(self, **kwargs):
		for key in kwargs:
			setattr(self, key, kwargs[key])

	profiles = {} # dict of func(hostname[, store_name])

	@classmethod
	def get_profile_names(cls):
		"generator, yield all profile names"
		for key in cls.profiles:
			args, _, _, _ = inspect.getargspec(cls.profiles[key])
			if "store_name" in args:
				for store_name in Stores().get_names():
					yield "%s:%s" % (store_name, key)
			elif "in_store_name" in args and "out_store_name" in args:
				store_names = Stores().get_names()
				for in_store_name in store_names:
					for out_store_name in store_names:
						if in_store_name != out_store_name:
							yield "%s:%s:%s" % (in_store_name, out_store_name, key)
			else:
				yield key

	@classmethod
	def get_profile(cls, hostname, profile_name):
		"instanciate named profile"
		if ":" in profile_name:
			lst = profile_name.split(":")
			if len(lst) == 2:
				store_name, key = lst
				kwargs = {"store_name": store_name}
			elif len(lst) == 3:
				in_store_name, out_store_name, key = lst
				kwargs = {
					"in_store_name": in_store_name,
					"out_store_name": out_store_name,
				}
		else:
			key = profile_name
			kwargs = {}
		assert key in cls.profiles, "%s: unsupported profile" % key
		return cls.profiles[key](hostname = hostname, **kwargs)

	def _get_raid_list(self):
		"return I.S. raid-specific parameter list from current object"
		lst = []
		if hasattr(self, "raid"):
			assert\
				self.raid in (0, 1, 4, 5, 6, 10),\
				"%i: illegal raid level" % self.raid
			lst += ["--raid", "%i" % self.raid]
		if hasattr(self, "raid_devices"):
			lst += ["--raid-devices", self.raid_devices]
		if hasattr(self, "raid_limit") and self.raid_limit:
			lst += ["--raid-limit"]
		if hasattr(self, "raid_wait") and self.raid_wait:
			lst += ["--raid-wait"]
		return lst

	def _get_bond_list(self):
		"return I.S. bond-specific parameter list from current object"
		lst = []
		if hasattr(self, "bond"):
			lst += ["--bond", self.bond]
		if hasattr(self, "bond_slaves"):
			lst += ["--bond-slaves", " ".join(self.bond_slaves)]
		if hasattr(self, "bond_mode"):
			lst += ["--bond-mode", self.bond_mode]
		if hasattr(self, "bond_hash"):
			lst += ["--bond-hash", self.bond_hash]
		return lst

	def _get_mail_list(self):
		"return I.S. mail-specific parameter list from current object"
		lst = []
		if hasattr(self, "smtp"):
			lst += ["--smtp", self.smtp]
		if hasattr(self, "mail_root"):
			lst += ["--mail-root", self.mail_root]
		if hasattr(self, "mail_domain"):
			lst += ["--mail-domain", self.kwargs.mail_domain]
		return lst

	def _get_cc_list(self):
		"return I.S. cc-specific parameter list from current object"
		lst = []
		if hasattr(self, "cc_enable") and self.cc_enable:
			lst += ["--cc-enable"]
		if hasattr(self, "cc_server"):
			lst += ["--cc-server", self.cc_server]
		if hasattr(self, "cc_port"):
			lst += ["--cc-port", self.cc_port]
		if hasattr(self, "cc_login"):
			lst += ["--cc-login", self.cc_login]
		if hasattr(self, "cc_password"):
			lst += ["--cd-password", self.cc_password]
		return lst

	@abc.abstractmethod
	def get_list(self):
		"return I.S. parameter list from current object"
		raise NotImplementedError()

class DebianSJProfile(Profile):
	"helper class to build the debian-smartjog image I.S. parameter list"

	image_name = "debian-smartjog"

	def __init__(self, hostname, disks, **kwargs):
		kwargs["hostname"] = hostname
		kwargs["disks"] = disks
		super(DebianSJProfile, self).__init__(**kwargs)

	profiles = {
		"pg": lambda hostname: DebianSJProfile(
			interfaces = ("dhcp:2006",),
			dns_search = ("fr.lan",),
			hostname = normalized_playground_hostname(hostname),
			password = "arkena",
			memory = 512,
			disks = ("rootfs:2048@vg",),
			start = True,
			dns = ("192.168.11.253",),
			ntp = ("ntp.fr.lan",),
			kvm = True,
			cpu = 1),
		"basic": lambda hostname, store_name: DebianSJProfile(
			interfaces = (Address(store_name = store_name),),
			hostname = hostname,
			password = "arkena",
			memory = 512,
			disks = ("rootfs:2048@vg",),
			start = True,
			kvm = True,
			cpu = 1),
	}

	# !!! parameter order matters for I.S. !!!
	def get_list(self):
		if hasattr(self, "hostname"):
			lst = ["--hostname", self.hostname]
		if hasattr(self, "domainname"):
			lst += ["--domainname", self.domainname]
		if hasattr(self, "kvm") and self.kvm:
			lst += ["--kvm"]
		if hasattr(self, "disks"):
			for item in map(str, self.disks):
				head = item
				if ":" in head:
					fs, head = item.split(":")
				if "@" in head:
					size, vgname = head.split("@")
					assert int(size) >= 2048, "%s: disk size must be >= 2048" % item
			lst += ["--disks", " ".join(self.disks)]
		if hasattr(self, "root_part_size"):
			lst += ["--root-part-size", self.root_part_size]
		if hasattr(self, "cpu"):
			lst += ["--cpu", "%i" % self.cpu]
		if hasattr(self, "memory"):
			lst += ["--memory", "%i" % self.memory]
		if hasattr(self, "start") and self.start:
			lst += ["--start"]
		if hasattr(self, "autostart") and self.autostart:
			lst += ["--autostart"]
		lst += self._get_raid_list()
		if hasattr(self, "interfaces"):
			interfaces = tuple("%s" % obj for obj in self.interfaces)
			for interface in interfaces:
				parse_interface(interface)
			lst += ["--interfaces", " ".join(interfaces)]
		if hasattr(self, "dns"):
			lst += ["--dns", " ".join("%s" % obj for obj in self.dns)]
		if hasattr(self, "dns_search"):
			lst += ["--dns-search", " ".join("%s" % obj for obj in self.dns_search)]
		if hasattr(self, "debian_repository"):
			lst += ["--debian-repository", self.debian_repository]
		if hasattr(self, "ldap"):
			assert ldap in (None, "lanfr", "lanus", "wantvr", "wanpmm", "wancap", "wanl3la")
			lst += ["--ldap", self.ldap]
		if hasattr(self, "password"):
			lst += ["--passwd", self.password]
		if hasattr(self, "reboot") and self.reboot:
			lst += ["--reboot"]
		lst += self._get_mail_list()
		if hasattr(self, "ntp"):
			lst += ["--ntp", " ".join(self.ntp)]
		lst += self._get_cc_list()
		if hasattr(self, "is_repository"):
			lst += ["--is-repository", self.is_repository]
		return lst

class ITransmuxProfile(DebianSJProfile):
	"helper class to build the cdn-itransmux image I.S. parameter list"

	image_name = "cdn-itransmux"

	profiles = {
		"basic": lambda hostname, store_name: ITransmuxProfile(
			interfaces = (Address(store_name = store_name),), # cdn_in
			hostname = hostname,
			password = "arkena",
			memory = 2 * 1024,
			disks = ("5000",),
			start = True,
			kvm = True),
		"prodvm": lambda hostname, in_store_name, out_store_name: ITransmuxProfile(
			interfaces = (
				Address(store_name = in_store_name),   # cdn_in
				Address(store_name = out_store_name)), # stcon
			internal_gw = Gateway(store_name = out_store_name),
			hostname = hostname,
			password = "arkena",
			memory = 2 * 1024,
			disks = ("5000",),
			start = True,
			kvm = True),
	}

class IWebdavProfile(DebianSJProfile):
	"helper class to build the cdn-iwebdav image I.S. parameter list"

	image_name = "cdn-iwebdav"

	def __init__(
		self,
		hostname,
		disks,
		internal_gw,
		**kwargs):
		kwargs["internal_gw"] = internal_gw
		super(IWebdavProfile, self).__init__(
			hostname = hostname,
			disks = disks,
			**kwargs)

	profiles = {
		"prodphy": lambda hostname, in_store_name, out_store_name: IWebdavProfile(
			root_part_size = 10000,
			data_part_size = 50000,
			internal_gw = Gateway(store_name = out_store_name),
			interfaces = (
				Address(store_name = in_store_name),   # cdn_in
				Address(store_name = out_store_name)), # stcon
			hostname = hostname,
			password = "arkena",
			disks = ("/dev/sda",)),
		"prodvm": lambda hostname, in_store_name, out_store_name: IWebdavProfile(
			internal_gw = Gateway(store_name = out_store_name),
			interfaces = (
				Address(store_name = in_store_name),   # cdn_in
				Address(store_name = out_store_name)), # stcon
			hostname = hostname,
			password = "arkena",
			disks = ("root:10000",),
			start = True,
			kvm = True),
		"basic": lambda hostname, store_name: IWebdavProfile(
			internal_gw = Gateway(store_name = store_name),
			interfaces = (Address(store_name = store_name),),
			hostname = hostname,
			password = "arkena",
			disks = ("root:10000",),
			start = True,
			kvm = True),
	}

	def get_list(self):
		lst = super(IWebdavProfile, self).get_list()
		if hasattr(self, "internal_gw"):
			lst += ["--internal-gw", "%s" % self.internal_gw]
		if hasattr(self, "data_part_size"):
			assert\
				"root_part_size" in self,\
				"--data-part-size cannot be used without --root-part-size"
			lst += ["--data-part-size", self.data_part_size]
		return lst

class IHttpullProfile(DebianSJProfile):
	"helper class to build the cdn-ihttpull image I.S. parameter list"

	image_name = "cdn-ihttpull"

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
		super(IHttpullProfile, self).__init__(
			hostname = hostname,
			disks = disks,
			**kwargs)

	profiles = {
		"prodphy": lambda hostname, in_store_name, out_store_name: IHttpullProfile(
			root_part_size = 50000,
			extend_storage = 1,
			internal_gw = Gateway(store_name = in_store_name),
			dns_search = (DnsSearch(store_name = in_store_name),),
			interfaces = (
				Address(store_name = in_store_name),   # cdn_in
				Address(store_name = out_store_name)), # stcon
			hostname = hostname,
			password = "arkena",
			disks = ("/dev/sda", "/dev/sdb"),
			raid = 0,
			dns = (Dns(store_name = in_store_name),)),
		"prodvm": lambda hostname, in_store_name, out_store_name: IHttpullProfile(
			internal_gw = Gateway(store_name = in_store_name),
			dns_search = (DnsSearch(store_name = in_store_name),),
			interfaces = (
				Address(store_name = in_store_name),   # cdn_in
				Address(store_name = out_store_name)), # stcon
			hostname = hostname,
			password = "arkena",
			memory = 2 * 1024,
			disks = ("root:20000",),
			start = True,
			dns = (Dns(store_name = in_store_name),),
			kvm = True,
			cpu = 2),
		"basic": lambda hostname, store_name: IHttpullProfile(
			internal_gw = Gateway(store_name = store_name),
			dns_search = (DnsSearch(store_name = store_name),),
			interfaces = (Address(store_name = store_name),),
			hostname = hostname,
			password = "arkena",
			memory = 2 * 1024,
			disks = ("root:20000",),
			start = True,
			dns = (Dns(store_name = store_name),),
			kvm = True,
			cpu = 2),
	}

	def get_list(self):
		lst = super(IHttpullProfile, self).get_list()
		if hasattr(self, "internal_gw"):
			lst += ["--internal-gw", "%s" % self.internal_gw]
		if hasattr(self, "arch"):
			assert self["arch"] in ("i386", "amd64")
			lst += ["--arch", self.arch]
		if hasattr(self, "update") and self.update:
			lst += ["--update"]
		if hasattr(self, "extend_storage_level"):
			assert self.extend_storage_level == 1
			lst += ["--extend-storage-level", self.extend_storage_level]
		if hasattr(self, "cache_directory"):
			lst += ["--cache-directory", self.cache_directory]
		return lst

class IFtpProfile(DebianSJProfile):
	"helper class to build the cdn-iftp image I.S. parameter list"

	image_name = "cdn-iftp"

	def __init__(self, hostname, disks, dns, **kwargs):
		kwargs["dns"] = dns
		super(IFtpProfile, self).__init__(hostname, disks, **kwargs)

	profiles = {}

class IIcemp3Profile(DebianSJProfile):

	image_name = "cdn-iicemp3"

	profiles = {}

class IAdwzbipProfile(DebianSJProfile):

	image_name = "cdn-iadwzbip"

	profiles = {}

class StorageProfile(DebianSJProfile):

	image_name = "cdn-storage"

	profiles = {}

class OOhpdwlProfile(DebianSJProfile):

	image_name = "cdn-oohpdwl"

	profiles = {}

class OHttchkProfile(DebianSJProfile):

	image_name = "cdn-ohttchk"

	profiles = {}

class OadwzkhProfile(DebianSJProfile):

	image_name = "cdn-oadwzkh"

	profiles = {}

class OOhsdwlProfile(DebianSJProfile):

	image_name = "cdn-oohsdwl"

	profiles = {}

class OHttflvProfile(DebianSJProfile):

	image_name = "cdn-ohttflv"

	profiles = {}

class OHttmp3Profile(DebianSJProfile):

	image_name = "cdn-ohttmp3"

	profiles = {}

class OHCacheProfile(DebianSJProfile):
	"helper class to build the cdn-ohcache image I.S. parameter list"

	image_name = "cdn-ohcache"

	def __init__(self, hostname, disks, internal_gw, **kwargs):
		kwargs["internal_gw"] = internal_gw
		super(OHCacheProfile, self).__init__(
			hostname = hostname,
			disks = disks,
			**kwargs)

	profiles = {
		"prodvm": lambda hostname, in_store_name, out_store_name: OHCacheProfile(
			description = "vm 4 cores, 2G mem, 10G disk, stcon@%s, stdiff@%s" % (
				in_store_name,
				out_store_name),
			internal_gw = Gateway(store_name = in_store_name),
			interfaces = (
				Address(store_name = in_store_name),   # stcon
				Address(store_name = out_store_name)), # stdiff
			hostname = hostname,
			password = "arkena",
			memory = 2000,
			disks = ("root:10000",),
			start = True,
			kvm = True,
			cpu = 4),
		"basic": lambda hostname, store_name: OHCacheProfile(
			description = "vm 4 cores, 2G mem, 10G disk, @%s" % store_name,
			internal_gw = Gateway(store_name = store_name),
			interfaces = (Address(store_name = store_name),),
			hostname = hostname,
			password = "arkena",
			memory = 2000,
			disks = ("root:10000",),
			start = True,
			kvm = True,
			cpu = 4),
	}

	def get_list(self):
		lst = super(OHCacheProfile, self).get_list()
		if hasattr(self, "log_part_size" ):
			lst += ("--log-part-size", self.log_part_size)
		if hasattr(self, "vip"):
			lst += ("--vip", " ".join(self.vip))
		if hasattr(self, "internal_gw"):
			lst += ("--internal-gw", "%s" % self.internal_gw)
		lst += self._get_bond_list()
		if hasattr(self, "arch"):
			assert self["arch"] in ("i386", "amd64")
			lst += ["--arch", self.arch]
		if hasattr(self, "update") and self.update:
			lst += ["--update"]
		lst += self._get_cc_list()
		if hasattr(self, "extend_storage_level"):
			assert self.extend_storage_level in ("True", "False")
			lst += ["--extend-storage-level", self.extend_storage_level]
		return lst

def get_subclasses(cls):
	res = []
	for subcls in cls.__subclasses__():
		res += [subcls] + get_subclasses(subcls)
	return res

def get_profile_classes():
	return get_subclasses(Profile)

def get_profile_class(image_name):
	for cls in get_profile_classes():
		if cls.image_name in image_name:
			return cls
	else:
		raise Exception("%s: unsupported image" % image_name)

#########
# model #
#########

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
		res = self.run(argv = "virsh -q list --all")
		if res:
			stdout = ""
			for line in res.splitlines():
				lst = line.split()
				line = "%s: %s\n" % (lst[1], " ".join(lst[2:]))
				if "on_stdout_line" in kwargs:
					kwargs["on_stdout_line"](line)
				else:
					stdout += line
			res.stdout = stdout
		return res

	def create_domain(
		self,
		image_name,
		profile,
		*args,
		**kwargs):
		argv = ["is", "install", image_name] + profile.get_list()
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

	def delete_domain(
		self,
		name,
		interfaces = None,
		keep_all_storage = False,
		*args,
		**kwargs):
		argv = (
			"virsh",
			"-q",
			"undefine",
			"--remove-all-storage" if not keep_all_storage else "",
			name)
		res = self.run(argv = argv, *args, **kwargs)
		for interface in interfaces:
			address = parse_interface(interface)["address"]
			Stores().get("/release/%s" % address)

	def load(self, *args, **kwargs):
		return self.run(argv = r"uptime | sed 's/.*load average: [0-9]*.[0-9]*, [0-9]*.[0-9]*, \([0-9]*\).\([0-9]*\)/\1.\2/g'", *args, **kwargs)

	def disk(self, *args, **kwargs):
		return self.run(argv = "df --total | tail -n 1 | awk '{print $4}'", *args, **kwargs)

#########
# tests #
#########

for cls in get_profile_classes():
	for profile_name in cls.get_profile_names():
		def test(self, cls = cls, profile_name = profile_name):
			cls.get_profile(
				hostname = "%s-%s" % (cls.__name__, profile_name),
				profile_name = profile_name)
		pattern = re.compile(r"[\W_]+")
		name = "%s%sTest" % (
			cls.__name__,
			pattern.sub('', profile_name.title()))
		globals()[name] = type(name, (unittest.TestCase,), {"test": test})

if __name__ == "__main__": unittest.main(verbosity = 2)
