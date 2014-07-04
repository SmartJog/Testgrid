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

import tempfile, unittest, getpass, httplib, urllib, pipes, json, os, re

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
	    re.match(r"[\w+-]+-[\w+\-]+.(pg|lab)\.fr\.lan", hostname),\
	    "%s: invalid playground domain name" % hostname
	return hostname

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

def parse_disk(string):
	"parse <name>:<size>@<vg> as dict"
	res = {"name": "%s" % string}
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
				self.cnx = httplib.HTTPSConnection(host = self.host, port = self.port)
			else:
				self.cnx = httplib.HTTPConnection(host = self.host, port = self.port)
			self.cnx.request("GET", path)
			res = self.cnx.getresponse()
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
		query = {}
		if reason:
			query["reason"] = reason
		else:
			query["reason"] = "hv"
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

class Profile(object):
	"hold installsystems instance parameters"

	def __init__(self, format, values, interfaces, image_name):
		self.format = format
		self.values = values
		self.interfaces = interfaces
		self.image_name = image_name

	def get_argv(self):
		"return interpolated list of arguments"
		return [item % self.values for item in self.format]

	@property
	def domain_name(self):
		return self.values["domain_name"]

class Profiles(object):

	def __init__(self, path):
		path = os.path.expanduser(path)
		with open(path, "r") as f:
			self.dict = json.load(f)

	def __iter__(self):
		for key in self.dict:
			yield key

	def __getitem__(self, key):
		return self.dict[key]

	@staticmethod
	def parse(profile_name, ipstore = None, **kwargs):
		"""
		Parse profile_name as ([realloc_key@]store_name:)*raw_profile_name
		Return interpolable values and interfaces.
		"""
		interfaces = []
		values = {}
		values.update(kwargs)
		i = 0
		tail = profile_name
		while ":" in tail:
			head, tail = profile_name.split(":", 1)
			if "@" in head:
				reallocation_key, store_name = head.split("@", 1)
			else:
				reallocation_key, store_name = (None, head)
			adr = Address(
				ipstore = ipstore,
				store_name = store_name,
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

	def get_profile(
		self,
		profile_name,
		ipstore = None,
		image_name = None,
		**kwargs):
		values, interfaces = self.parse(profile_name, ipstore, **kwargs)
		def make_profile(image_name, profile_name):
			for profile_pattern in self.dict[image_name]:
				if re.sub("[\w-]+@", "", profile_name) in profile_pattern.split("|"):
					return Profile(
						format = self.dict[image_name][profile_pattern]["format"],
						values = values,
						interfaces = interfaces,
						image_name = image_name)
			else:
				raise NoSuchProfileError(profile_name)
		if image_name:
			if not image_name in self.dict:
				raise NoSuchImageError(image_name)
			return make_profile(image_name, profile_name)
		else:
			for image_name in self.dict:
				try:
					return make_profile(image_name, profile_name)
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
		for vgname in self.run("ls /dev/vg").splitlines():
			if vgname.startswith(profile.domain_name):
				vgpath = "/dev/vg/%s" % vgname
				self.run("echo copy-id: mounting %s..." % vgpath, *args, **kwargs)
				self.run("kpartx -a %s" % vgpath, *args, **kwargs)
				# we have two partitions: 1=>GPT, 2=>ext4, we work on 2.
				dmpath2 = "/dev/mapper/vg-%s2" % vgname.replace("-", "--")
				mountpoint = "/tmp/%s" % profile.domain_name
				self.run("mkdir %s" % mountpoint, *args, **kwargs)
				self.run("mount %s %s" % (dmpath2, mountpoint), *args, **kwargs)
				self.run("mkdir -p %s/root/.ssh" % mountpoint, *args, **kwargs)
				self.run("echo copy-id: now registering public key", *args, **kwargs)
				self.run(
					"echo %s >> %s/root/.ssh/authorized_keys" % (
						pipes.quote(public_key),
						mountpoint),
					*args,
					**kwargs)
				self.run("umount %s" % mountpoint, *args, **kwargs)
				self.run("rmdir %s" % mountpoint, *args, **kwargs)
				self.run("kpartx -d %s" % vgpath, *args, **kwargs)
				break
		else:
			raise Exception("%s: cannot copy key, no vg found" % profile.domain_name)

	def _delete_vg(self, profile, *args, **kwargs):
		for vgname in self.run("ls /dev/vg").splitlines():
			if vgname.startswith(profile.domain_name):
				dmpath = "/dev/mapper/vg-%s" % vgname.replace("-", "--")
				for dmpathX in self.run("ls %s?" % dmpath).splitlines():
					self.run("umount %s" % dmpathX, warn_only = True, **kwargs)
					self.run("dmsetup remove %s" % os.path.basename(dmpathX), **kwargs)
				self.run("dmsetup remove %s" % dmpath, **kwargs)
				self.run("lvremove -f %s" % path, **kwargs)

	def create_domain(
		self,
		profile,
		public_key = None,
		*args,
		**kwargs):
		argv = ["is", "install", profile.image_name] + profile.get_argv()
		res = self.run(argv = argv, *args, **kwargs)
		if res:
			if public_key:
				self._copy_id(
					profile = profile,
					public_key = public_key,
					*args,
					**kwargs)
			argv = ("virsh", "start", profile.domain_name)
			self.run(argv = argv, *args, **kwargs)
		else:
			self._delete_vg(profile, *args, **kwargs)
		return res

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

################
# test doubles #
################

class FakeIPStore(IPStore):

	cache = {}

	def get(self, path):
		"override http request with direct use of local cache"
		try:
			return self.cache[path]
		except Exception as e:
			raise IPStoreError("nohost", 0, path, e)

	def get_names(self):
		raise NotImplementedError()

class Domain(object):

	def __init__(self, name, started = False):
		self.name = name
		self.started = started

	def __str__(self):
		return "%s %s" % (self.name, "running" if self.started else "shut off")

	def start(self):
		self.started = True

	def shutdown(self):
		self.started = False

class FakeRunner(object):

	def __init__(self):
		self.domains = [] # list of domains

	def __call__(self, argv, *args, **kwargs):
		if isinstance(argv, (list, tuple)):
			argv = " ".join(argv)
		if re.match("virsh .*list.*", argv):
			return "\n".join("%s" % domain for domain in self.domains)
		res = re.match(r"is install.*--hostname (\w+).*", argv)
		if res:
			hostname = res.group(1)
			self.domains.append(Domain(hostname))
			return True
		res = re.match(r"virsh .*undefine.* (\w+)", argv)
		if res:
			domain_name = res.group(1)
			self.domains = filter(
				lambda domain: domain.name != domain_name,
				self.domains)
			return True

		res = re.match(r"virsh .*destroy.* (\w+)", argv)
		if res:
			return True

		res = re.match(r"virsh start (\w+)", argv)
		if res:
			domain_name = res.group(1)
			for domain in self.domains:
				if domain.name == domain_name:
					domain.start()
					return True
			else:
				raise Exception("%s: no such domain" % domain_name)
		raise Exception("%s: unknown command" % argv)

##############
# test cases #
##############

class StoreTest(unittest.TestCase):

	def setUp(self):
		self.ipstore = FakeIPStore(host = "whatever", port = 0)

	def test_dns_search(self):
		obj = DnsSearch(self.ipstore, "foo")
		res = "phah7xuJ"
		self.ipstore.cache["/foo/dns_search"] = res
		self.assertEqual("%s" % obj, res)

	def test_gateway(self):
		obj = Gateway(self.ipstore, "foo")
		res = "ahqu9EiZ"
		self.ipstore.cache["/foo/gateway"] = res
		self.assertEqual("%s" % obj, res)

	def test_address(self):
		adr = Address(self.ipstore, "foo")
		res = "oo5Biewe"
		self.ipstore.cache["/foo/allocate?reason=hv"] = res
		self.assertEqual("%s" % adr, res)

	def test_reallocated_address(self):
		adr = Address(self.ipstore, "foo", reallocation_key = "aaa")
		res = "ieceiw4D"
		self.ipstore.cache["/foo/allocate?reallocation_key=aaa&reason=hv"] = res
		self.assertEqual("%s" % adr, res)

	def test_address_with_custom_reason(self):
		adr = Address(self.ipstore, "foo", reason = "blah")
		res = "xa5ep9Sh"
		self.ipstore.cache["/foo/allocate?reason=blah"] = res
		self.assertEqual("%s" % adr, res)

	def test_dns(self):
		obj = Dns(self.ipstore, "foo")
		res = "SheePh1m"
		self.ipstore.cache["/foo/dns"] = res
		self.assertEqual("%s" % obj, res)

class ProfileTest(unittest.TestCase):

	def test_no_match(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write("""
			{
				"foo": {
					"bar": {
						"description": "",
						"format": []
					}
				}
			}
			""")
			f.flush()
			profiles = Profiles(f.name)
			self.assertRaises(NoSuchProfileError, profiles.get_profile, "qux")

	def test_basic_match(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write("""
			{
				"foo": {
					"bar": {
						"description": "",
						"format": []
					}
				}
			}
			""")
			f.flush()
			profiles = Profiles(f.name)
			profiles.get_profile("bar")

	def test_disjunctive_match(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write("""
			{
				"foo": {
					"bar|baz|qux": {
						"description": "",
						"format": []
					}
				}
			}
			""")
			f.flush()
			profiles = Profiles(f.name)
			profiles.get_profile("baz")

	def test_match_with_key(self):
		with tempfile.NamedTemporaryFile() as f:
			f.write("""
			{
				"foo": {
					"bar|baz|qux": {
						"description": "",
						"format": []
					}
				}
			}
			""")
			f.flush()
			profiles = Profiles(f.name)
			profiles.get_profile("1234@baz")

class HypervisorTest(unittest.TestCase):

	def setUp(self):
		self.ipstore = FakeIPStore(host = "whatever", port = 0)
		self.hv = Hypervisor(run = FakeRunner())

	def test_create_delete(self):
		self.assertFalse(self.hv.list_domains()) # no domain initially
		with tempfile.NamedTemporaryFile() as f:
			f.write("""
			{
				"foo": {
					"bar": {
						"description": "",
						"format": [
							"--hostname", "%(domain_name)s"
						]
					}
				}
			}
			""")
			f.flush()
			profiles = Profiles(f.name)
		profile = profiles.get_profile(
			profile_name = "bar",
			ipstore = self.ipstore,
			domain_name = "zargl")
		self.hv.create_domain(profile = profile)
		self.assertEqual("%s" % self.hv.list_domains(), "zargl running")
		self.hv.delete_domain("foo")

if __name__ == "__main__": unittest.main(verbosity = 2)
