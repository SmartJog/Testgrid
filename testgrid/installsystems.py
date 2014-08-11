# copyright (c) 2014 smartjog, released under the GPL license.

"""
Python API for InstallSystems(tm).

References:
  https://github.com/seblu/installsystems

API:
  * Hypervisor(shell)
    - res = list_images(repo = None, ...)
    - res = list_domains(...)
    - res = create_domain(image_name, profile, [public_key] ...)
    - res = start_domain(name, ...)
    - res = stop_domain(name, [force = True], ...)
    - res = restart_domain(name, [force = True], ...)
    - res = delete_domain(name, [keep_all_storage = True], ...)
    - res = load(...)
    - res = disk(...)

Tutorial:
  hkvm$ python
  >>> import installsystems as IS, os
  >>> hv = IS.Hypervisor(runner = os.system)
  >>> print hv.list_domains()
  >>> profile = IS.Profiles("profiles.json").get_profile("test", domain_name = "foo")
  >>> print hv.create_domain(profile)
  >>> print hv.delete_domain(profile)

For dynamic address allocation, you'll need an IPStore service.
"""

import tempfile, getpass, httplib, syslog, urllib, pipes, json, os, re

###########
# helpers #
###########

def normalized_domain_name(string):
	"""
	Normalize playground hkvm domain name.
	See https://confluence.smartjog.net/display/INFRA/Playground#Playground-Rules
	"""
	if len(string.split("-")) < 2:
		string = "%s-%s" % (getpass.getuser(), string)
	comps = string.split(".")
	if len(comps) == 1:
		string += ".pg-1.arkena.net"
	elif len(comps) == 2:
		string += ".arkena.net"
	assert\
		re.match(r"\w+-[\w-]+\.(pg-1|lab)\.arkena\.net", string),\
		"%s: invalid playground domain name" % string
	return string

def parse_interface(string):
	"parse <address>/<mask>@<gateway>?<iface>:<vlan> as dict"
	res = {"address": "%s" % string}
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

def parse_lvdisk(string):
	"parse <name>[:<size>][@<vg>][/<mountpoint>] as dict"
	res = {"name": "%s" % string}
	if "/" in res["name"]:
		res["name"], res["mountpoint"] = res["name"].split("/")
	if "@" in res["name"]:
		res["name"], res["vg"] = res["name"].split("@")
	if ":" in res["name"]:
		res["name"], res["size"] = res["name"].split(":")
	return res

class IPStoreError(Exception):

	def __init__(self, host, port, path, exc):
		self.host = host
		self.port = port
		self.path = path
		self.exc = exc

	def __str__(self):
		return "IPStore %s:%i GET %s: %s, %s" % (
			self.host,
			self.port,
			self.path,
			type(self.exc).__name__,
			self.exc)

class IPStore(object):
	"hold HTTP connection and dispatch requests to IPStore"

	def __init__(self, host, port, use_ssl = False):
		self.host = host
		self.port = port
		self.use_ssl = use_ssl

	def get(self, path):
		try:
			if self.use_ssl:
				cnx = httplib.HTTPSConnection(host = self.host, port = self.port)
			else:
				cnx = httplib.HTTPConnection(host = self.host, port = self.port)
			cnx.request("GET", path)
			res = cnx.getresponse()
			assert res.status == 200, "%i, %s" % (res.status, res.reason)
			return res.read()
		except Exception as e:
			raise IPStoreError(self.host, self.port, path, e)

	def get_names(self, unlocked = True):
		return eval(self.get("/names?locked=%s" % "unlocked" if unlocked else "locked"))

	def allocate(
		self,
		store_name,
		reason = None,
		reallocation_key = None):
		query = {
			"reason": "hv | %s" % (reason or "no details")
		}
		if reallocation_key:
			query["reallocation_key"] = reallocation_key
		return self.get("/%s/allocate?%s" % (store_name, urllib.urlencode(query)))

	def release(self, address):
		return self.get("/release/%s" % address)

	def gateway(self, store_name):
		return self.get("/%s/gateway" % store_name)

	def dns(self, store_name):
		return self.get("/%s/dns" % store_name)

	def dns_search(self, store_name):
		return self.get("/%s/dns_search" % store_name)

class LazyStoreValue(object):
	"defer value request until explicit .value need"

	def __init__(self, callback):
		self.callback = callback

	def __getattr__(self, key):
		if key == "value":
			self.value = self.callback()
			return self.value
		super(LazyStoreValue, self).__getattr__(key)

	def __str__(self):
		return "%s" % self.value

class DnsSearch(LazyStoreValue):

	def __init__(self, ipstore, store_name):
		super(DnsSearch, self).__init__(lambda: ipstore.dns_search(store_name))

class Gateway(LazyStoreValue):

	def __init__(self, ipstore, store_name):
		super(Gateway, self).__init__(lambda: ipstore.gateway(store_name))

class Address(LazyStoreValue):

	def __init__(
		self,
		ipstore,
		store_name,
		reason = None,
		reallocation_key = None):
		self.ipstore = ipstore
		super(Address, self).__init__(lambda: ipstore.allocate(
			store_name = store_name,
			reason = reason,
			reallocation_key = reallocation_key))

class Dns(LazyStoreValue):

	def __init__(self, ipstore, store_name):
		super(Dns, self).__init__(lambda: ipstore.dns(store_name))

class NoSuchProfiledImageError(Exception):

	def __init__(self, image_name):
		self.image_name = image_name

	def __str__(self):
		return "%s: no such profiled image" % self.image_name

class NoSuchProfileError(Exception):

	def __init__(self, profile_name):
		self.profile_name = profile_name

	def __str__(self):
		return "%s: no such profile" % self.profile_name

class NoSuchImageError(Exception):

	def __init__(self, image_path):
		self.image_path = image_path

	def __str__(self):
		return "%s: no such image" % self.image_path

class Profile(object):
	"hold installsystems instance parameters"

	def __init__(self, format, values, interfaces, image_path):
		self.format = format
		self.values = values
		self.interfaces = interfaces
		self.image_path = image_path

	def get_argv(self):
		"return interpolated list of arguments"
		return [item % self.values for item in self.format]

	def __getattr__(self, key):
		return self.values[key]

	def __str__(self):
		return self.values.get("domain_name", "noname")

	def get_first_diskname(self):
		"return the first diskname either as a path or lv name"
		itr = iter(self.format)
		for item in itr:
			if item == "--disks":
				dev = next(itr)
				if dev.startswith("/"):
					return dev
				else:
					h = parse_lvdisk(dev)
					return h["name"]
		else:
			raise Exception("cannot find first disk")

def parse_profile(string, ipstore = None, **kwargs):
	"""
	parse ([realloc_key@]store_name:)*raw_profile_name
	as (interpolable values dict, interfaces list)
	"""
	interfaces = []
	values = {}
	values.update(kwargs)
	i = 0
	while ":" in string:
		head, string = string.split(":", 1)
		if "@" in head:
			reallocation_key, store_name = head.split("@", 1)
		else:
			reallocation_key, store_name = (None, head)
		adr = Address(
			ipstore = ipstore,
			store_name = store_name,
			reason = " ".join("%s=%s" % (key, kwargs[key]) for key in kwargs),
			reallocation_key = reallocation_key)
		suffix = "_%i" % i if i else ""
		values.update({
			"dns_search%s" % suffix: DnsSearch(
				ipstore = ipstore,
				store_name = store_name),
			"address%s" % suffix: adr,
			"gateway%s" % suffix: Gateway(
				ipstore = ipstore,
				store_name = store_name),
			"dns%s" % suffix: Dns(
				ipstore = ipstore,
				store_name = store_name),
		})
		interfaces.append(adr)
		i = i + 1
	return (values, interfaces)

def get_image_path_distance(path1, path2):
	"""
	measure rules:
	* foo/bar:4, foo/bar:4 = 4 (best)
	* foo/bar:4, foo/bar = 2
	* foo/bar:4, bar:4 = 2
	* foo/bar:4, bar = 1
	* foo/bar, foo/bar = 4
	* foo/bar, bar:4 = 1
	* foo/bar, bar = 1
	* bar:4, bar:4 = 4
	* bar:4, bar = 1
	* bar, bar = 4
	* otherwise 0
	"""
	def parse_image(path):
		"parse [<dirname>/]<basename>[:<version>] as [dirname, basename, version]"
		res = re.match(r"^(?:(\w+)/)?([\w-]+)(?::(\d+))?$", path)
		assert res, "%s: invalid image path" % path
		return [res.group(1), res.group(2), res.group(3)]
	t1 = parse_image(path1)
	t2 = parse_image(path2)
	if t1 == t2:
		return 4 # exact match
	else:
		if t1[0] is None or t2[0] is None:
			t1 = t1[1:]
			t2 = t2[1:]
		if t1[-1] is None or t2[-1] is None:
			t1 = t1[:-1]
			t2 = t2[:-1]
		return len(t1) if t1 == t2 else 0

def find_best_image_paths(path, paths):
	max = None
	res = None
	for key in paths:
		i = get_image_path_distance(path, key)
		if not i:
			continue
		elif max is None or i > max:
			max = i
			res = [key]
		elif i == max:
			res.append(key)
	return res

class Profiles(object):
	"parse json file and return matching Profile object on get_profile()"

	def __init__(self, path):
		path = os.path.expanduser(path)
		with open(path, "r") as f:
			self.dict = json.load(f)

	def __iter__(self):
		for key in self.dict:
			yield key

	def __getitem__(self, key):
		return self.dict[key]

	def get_profile(
		self,
		profile_name,
		ipstore = None,
		image_path = None,
		**kwargs):
		values, interfaces = parse_profile(profile_name, ipstore, **kwargs)
		def make_profile(image_key, profile_name, image_path):
			for profile_pattern in self.dict[image_key]:
				if re.sub("[\w-]+@", "", profile_name) in profile_pattern.split("|"):
					if "domain_name" in self.dict[image_key][profile_pattern]:
						values.update({
							"domain_name": self.dict[image_key][profile_pattern]["domain_name"]
						})
					if "copy_id" in self.dict[image_key][profile_pattern]:
						copy_id = self.dict[image_key][profile_pattern]["copy_id"]
					else:
						copy_id = True
					if "post_install" in self.dict[image_key][profile_pattern]:
						post_install = self.dict[image_key][profile_pattern]["post_install"]
					else:
						post_install = "start"
					values.update({
						"copy_id": copy_id,
						"post_install": post_install,
					})
					if "format" in self.dict[image_key][profile_pattern]:
						format = self.dict[image_key][profile_pattern]["format"]
					else:
						format = ""
					return Profile(
						format = format,
						values = values,
						interfaces = interfaces,
						image_path = image_path)
			else:
				raise NoSuchProfileError(profile_name)
		# image_path is optional
		# is unset we return the first matching profile or NoSuchProfile
		if image_path:
			for image_key in find_best_image_paths(image_path, self.dict.keys()):
				try:
					return make_profile(image_key, profile_name, image_path)
				except:
					pass
			else:
				raise NoSuchImageError(image_path)
		else:
			for image_key in self.dict:
				try:
					return make_profile(image_key, profile_name, image_key)
				except NoSuchProfileError:
					pass
			else:
				raise NoSuchProfileError(profile_name)

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
		return self.run(argv = "virsh -q list --all", *args, **kwargs)

	# FIXME: check this is not called on an already started domain
	def _copy_id(self, profile, public_key, *args, **kwargs):
		diskname = profile.get_first_diskname()
		if diskname.startswith("/"):
			# TODO
			raise NotImplemented("%s: non-lv devices not yet supported" % diskname)
		else:
			vgpath = "/dev/vg/%s-%s" % (profile.domain_name, diskname)
			syslog.syslog("%s: copy-id: mounting %s" % (profile, vgpath))
			self.run("kpartx -a %s" % vgpath, *args, **kwargs)
			# we have two partitions: 1=>GPT, 2=>ext4, we work on partition 2.
			vgname = os.path.basename(vgpath)
			dmpath2 = "/dev/mapper/vg-%s*2" % vgname.replace("-", "--")
			mountpoint = "/tmp/%s" % profile.domain_name
			self.run("mkdir %s" % mountpoint, *args, **kwargs)
			self.run("mount %s %s" % (dmpath2, mountpoint), *args, **kwargs)
			self.run("mkdir -p %s/root/.ssh" % mountpoint, *args, **kwargs)
			syslog.syslog("%s: copy-id: registering public key" % profile)
			self.run(
				"echo %s >> %s/root/.ssh/authorized_keys" % (
					pipes.quote(public_key),
					mountpoint),
				*args,
				**kwargs)
			self.run("umount %s" % mountpoint, *args, **kwargs)
			self.run("rmdir %s" % mountpoint, *args, **kwargs)
			self.run("kpartx -d %s" % vgpath, *args, **kwargs)

	def delete_volume_group(self, name, *args, **kwargs):
		diskname = profile.get_first_diskname()
		if diskname.startswith("/"):
			# TODO
			raise NotImplemented("%s: non-lv devices not yet supported" % diskname)
		else:
			vgpath = "/dev/vg/%s-%s" % (profile.domain_name, diskname)
			vgname = os.path.basename(vgpath)
			dmname = "vg-%s" % vgname.replace("-", "--")
			dmpath = "/dev/mapper/%s" % dmname
			for dmpathX in self.run("find /dev/mapper -name '%s*'" % dmname).splitlines():
				syslog.syslog("%s: disabling partition %s" % (name, dmpathX))
				self.run("umount %s" % dmpathX, warn_only = True, *args, **kwargs)
				self.run("dmsetup remove %s" % os.path.basename(dmpathX), *args, **kwargs)
			self.run("if fuser %s; then sleep 1; fi" % dmpath, *args, **kwargs)
			syslog.syslog("%s: deleting volume group %s" % (name, dmpath))
			self.run("dmsetup remove %s" % dmpath, *args, **kwargs)
			self.run("lvremove -f %s" % vgpath, *args, **kwargs)

	def create_domain(
		self,
		profile,
		public_key = None,
		*args,
		**kwargs):
		argv = ["is", "install", profile.image_path] + profile.get_argv()
		try:
			res = self.run(argv = argv, *args, **kwargs)
			if public_key and profile.copy_id:
				try:
					self._copy_id(
						profile = profile,
						public_key = public_key,
						*args,
						**kwargs)
				except:
					syslog.syslog("%s: failed to copy-id" % profile)
					raise
			if profile.post_install == "start":
				res += self.run("virsh start %s" % profile.domain_name, *args, **kwargs)
			elif profile.post_install == "reboot":
				res += self.run("reboot", *args, **kwargs)
			return res
		except Exception as e:
			for itf in profile.interfaces:
				try:
					itf.ipstore.release(parse_interface(itf.value)["address"])
				except:
					syslog.syslog("%s: failed to release address %s" % (profile, itf.value))
			try:
				self.delete_volume_group(profile.domain_name, *args, **kwargs)
			except:
				syslog.syslog("%s: failed to delete volume group" % profile)
			raise e

	def delete_domain(
		self,
		name,
		ipstore = None,
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
		if ipstore and interfaces:
			for interface in interfaces:
				address = parse_interface(interface)["address"]
				if address != "dhcp":
					ipstore.release(address)
		return res

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

	def load(self, *args, **kwargs):
		return float("%s" % self.run(argv = r"uptime | sed 's/.*load average: [0-9]*.[0-9]*, [0-9]*.[0-9]*, \([0-9]*\).\([0-9]*\)/\1.\2/g'", *args, **kwargs))

	def disk(self, *args, **kwargs):
		return int("%s" % self.run(argv = "df --total | tail -n 1 | awk '{print $4}'", *args, **kwargs))
