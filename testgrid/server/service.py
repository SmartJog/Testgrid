# copyright (c) 2014 florent claerhout, released under the MIT license.

"""
Service management framework.

API:
  Initd
  Sysv: Initd
  Upstart: Initd
  Systemd: Initd
  Platform
  Windows: Platform
  Posix: Platform
  Darwin: Posix
  Linux: Posix
  RedHat: Sysv, Linux
  Debian: Sysv, Linux
  Ubuntu: Upstart, Debian
  h = Host([hoststring], [platform], [runner], logger = Null, warn_only = False)
    - (h)(argv, [logger], [warn_only])
    - h.<platform command>(...)
    - h.put(localpath, remotepath, ...)
    - h.fwrite(content, path, ...)
  srv = Service(host, [initd], [srvname], [pkgname],
    [stopcmd], [startcmd], [reloadcmd], [catlogcmd],
    [restartcmd], [runningcmd], [versioncmd], [degradedcmd])
    - srv.stop()
    - srv.start()
    - srv.reload()
    - srv.catlog()
    - srv.restart()
    - srv.running()
    - srv.degraded()
    - srv.version()
    - srv.status()
    - (srv)(args, [logger], [warn_only])
    - srv.<platform command>(...)
  srv = Services([host], [services]): Service
    - srv.version(argv)
    - srv.status(argv)
"""

__version__ = "20140402"

import unittest, shell

#############################
# platforms & host wrappers #
#############################

class Platform(object): pass

class Windows(Platform):

	@staticmethod
	def false(): return ("cmd", "/c", "exit", "1")

	@staticmethod
	def true(): return ("cmd", "/c", "exit", "0")

	@staticmethod
	def echo(*argv): return ("cmd", "/c", "echo",) + tuple(argv)

	@staticmethod
	def list(): return "sc query state= all | findstr /r /c:SERVICE_NAME"

	@staticmethod
	def stop(name): return ("net", "stop", name)

	@staticmethod
	def start(name): return ("net", "start", name)

	@staticmethod
	def reboot(): return ("shutdown", "/r")

	@staticmethod
	def poweroff(): return ("shutdown", "/s")

class Posix(Platform):

	@staticmethod
	def false(): return ("false",)

	@staticmethod
	def true(): return ("true",)

	@staticmethod
	def echo(*argv): return ("echo",) + tuple(argv)

	@staticmethod
	def reboot(): return ("shutdown", "-r", "now")

	@staticmethod
	def poweroff(): return ("shutdown", "-s", "now")

	@staticmethod
	def ps(): return "ps -eo pid,args | sed 1d"

class Darwin(Posix):

	@staticmethod
	def list(): return "launchctl list | cut -f3"

	@staticmethod
	def stop(name): return ("launchctl", "stop", name)

	@staticmethod
	def start(name): return ("launchctl", "start", name)

class Initd(object):

	@staticmethod
	def catlog(name): return ("tail", "/var/log/%s.log" % name)

	@staticmethod
	def degraded(name): return ("false",)

class Sysv(Initd):
	"legacy sysv init daemon interface"

	@staticmethod
	def stop(name): return ("/etc/init.d/%s" % name, "stop")

	@staticmethod
	def start(name): return ("/etc/init.d/%s" % name, "start")

	@staticmethod
	def reload(name): return ("/etc/init.d/%s" % name, "reload")

	@staticmethod
	def restart(name): return ("/etc/init.d/%s" % name, "restart")

	@staticmethod
	def running(name): return "/etc/init.d/%s status | grep -q is\ running" % name

class Upstart(Initd):
	"upstart init daemon interface"

	@staticmethod
	def list(): return "initctl list | cut -d' ' -f1"

	@staticmethod
	def stop(name): return ("stop", name)

	@staticmethod
	def start(name): ("start", name)

	@staticmethod
	def restart(name): ("restart", name)

	@staticmethod
	def running(name): "status %s | grep -q start/running" % name

class Systemd(Initd):
	"systemd init daemon interface"

	@staticmethod
	def stop(name): return ("systemctl", "stop", name)

	@staticmethod
	def start(name): return ("systemctl", "start", name)

	@staticmethod
	def reload(name): return ("systemctl", "reload", name)

	@staticmethod
	def restart(name): return ("systemctl", "restart", name)

	@staticmethod
	def running(name): return "systemctl status %s | ???" % name # FIXME

	@staticmethod
	def reboot(): return ("systemctl", "reboot")

	@staticmethod
	def poweroff(): return ("systemctl", "poweroff")

class Linux(Posix): pass

class RedHat(Sysv, Linux):

	@staticmethod
	def version(name): return "rpm -q %s | cut -d- -f2" % name # not tested

class Debian(Sysv, Linux):

	@staticmethod
	def version(name):
		return "( set -o pipefail; dpkg -s %s | grep ^Version | cut -d: -f2- | tr -d [:blank:] )" % name

class Ubuntu(Upstart, Debian): pass

def get_platform(runner):
	"return runner's platform"
	uname = (runner)(("uname", "-s"), warn_only = True)
	if uname.startswith("Linux"):
		if (runner)(("lsb_release", "-sd"), warn_only = True).startswith("Ubuntu"):
			return Ubuntu
		elif (runner)(("test", "-e", "/etc/debian_version"), warn_only = True):
			return Debian
		elif (runner)(("test", "-e", "/etc/redhat-release"), warn_only = True):
			return RedHat
		else:
			return Linux
	elif uname.startswith("Darwin"):
		return Darwin
	elif (runner)(("cmd", "/c", "ver"), warn_only = True):
		return Windows
	else:
		raise NotImplementedError("unsupported platform")

class Host(object):
	"wraps run() to call host's platform commands"

	def __init__(
		self,
		hoststring = None,
		platform = None,
		runner = None,
		logger = None,
		warn_only = False):
		self.hoststring = hoststring or ""
		if "@" in self.hoststring:
			self.username, self.hostname = self.hoststring.split("@")
		else:
			self.username = None
			self.hostname = self.hoststring
		self.platform = platform
		if runner:
			self.runner = runner
		elif self.hostname:
			self.runner = lambda *args, **kwargs: shell.ssh(self.hoststring, *args, **kwargs)
		elif self.username:
			self.runner = lambda *args, **kwargs: shell.sudo(self.username, *args, **kwargs)
		else:
			self.runner = shell.run
		if logger:
			self.logger = lambda string: (logger)("%s: %s\n" % (self, string))
		else:
			self.logger = shell.Null
		self.warn_only = warn_only

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.hoststring)

	def __str__(self):
		return self.hoststring or "localhost"

	def __call__(self, argv, logger = None, warn_only = None):
		return (self.runner)(
			argv = argv,
			logger = self.logger if logger is None else logger,
			warn_only = self.warn_only if warn_only is None else bool(warn_only))

	def __getattr__(self, key):
		self.platform = self.platform or get_platform(self)
		attr = getattr(self.platform, key)
		if callable(attr):
			def func(*args, **kwargs):
				opts = {}
				if "logger" in kwargs:
					opts["logger"] = kwargs["logger"]
					del kwargs["logger"]
				if "warn_only" in kwargs:
					opts["warn_only"] = kwargs["warn_only"]
					del kwargs["warn_only"]
				return (self)(argv = (attr)(*args, **kwargs), **opts)
			return func
		else:
			return attr

	def put(self, localpath, remotepath):
		"upload $localpath to host's $remotepath"
		if self.hostname:
			return shell.scp(self.hoststring, localpath, remotepath)
		else:
			return self.cp(localpath, remotepath)

	def fwrite(self, content, path):
		"write $content to host $path"
		with tempfile.NamedTemporaryFile() as f:
			f.write(content)
			f.flush()
			return self.put(localpath = f.name, remotepath = path)

localhost = Host(logger = shell.Stderr)

class LocalHostTest(unittest.TestCase):

	host = Host() # localhost with no logger

	def testTrue(self):
		self.assertTrue(self.host.true())

	def testFalse(self):
		self.assertRaises(RuntimeError, self.host.false)

	def testFalseWarnOnly(self):
		self.assertFalse(self.host.false(warn_only = True))

	def testLocalPlatformEcho(self):
		self.assertEqual(self.host.echo("hello"), "hello\n")

###########
# service #
###########

class Service(object):

	def __init__(
		self,
		host,
		initd = None,
		srvname = None,
		pkgname = None,
		stopcmd = None,
		startcmd = None,
		reloadcmd = None,
		catlogcmd = None,
		restartcmd = None,
		runningcmd = None,
		versioncmd = None,
		degradedcmd = None):
		self.host = host
		for cmd in ("stop", "start", "reload", "catlog", "restart", "running", "degraded"):
			warn_only = cmd in ("running", "degraded")
			if locals().get("%scmd" % cmd, None):
				setattr(self, cmd, lambda argv = locals()["%scmd" % cmd]: (self.host)(argv = argv, warn_only = warn_only))
			elif srvname and initd and hasattr(initd, cmd):
				setattr(self, cmd, lambda cmd = cmd: (self.host)(argv = getattr(initd, cmd)(srvname), warn_only = warn_only))
			elif srvname:
				setattr(self, cmd, lambda cmd = cmd: getattr(self.host, cmd)(srvname, warn_only = warn_only))
		if versioncmd:
			self.version = lambda: (host)(argv = versioncmd)
		elif pkgname or srvname:
			self.version = lambda: self.host.version(pkgname or srvname)

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.host)

	def __call__(self, *args, **kwargs):
		return (self.host)(*args, **kwargs)

	def __getattr__(self, key):
		return getattr(self.host, key)

	def status(self):
		try:
			ver = self.version().strip()
		except Exception as e:
			ver = "unknown version"
		try:
			if not self.running():
				returncode = 3
				stdout = "%s %s\n" % (ver, red("not running"))
				stderr = "service is not running\n"
			elif self.degraded():
				returncode = 2
				stdout = "%s %s\n" % (ver, yellow("degraded"))
				stderr = "service is running in degraded state\n"
			else:
				returncode = 0
				stdout = "%s %s\n" % (ver, green("running"))
				stderr = None
		except Exception as e:
			returncode = 1
			stdout = "%s %s\n" % (ver, blue("unknown state"))
			stderr = "service running state is unknown: %s\n" % e
		return Result(returncode, stdout = stdout, stderr = stderr)

class ServiceTest(unittest.TestCase):

	host = type("DummyHost", (Host,), {
			"last_argv": None,
			"__call__": lambda self, argv, logger = None, warn_only = None: setattr(self, "last_argv", argv),
			"last_stopped": None,
			"stop": lambda self, name, logger = None, warn_only = None: setattr(self, "last_stopped", name),
	})(platform = Platform, runner = shell.Null)

	def testWithCmd(self): # test with stop only, TODO other commands
		argv = "custom cmd"
		srv = Service(host = self.host, stopcmd = argv)
		srv.stop()
		self.assertEqual(self.host.last_argv, argv)

	def testWithSrv(self): # test with stop only, TODO other commands
		srvname = "foo"
		srv = Service(host = self.host, srvname = srvname)
		srv.stop()
		self.assertEqual(self.host.last_stopped, srvname)

class Services(Service):

	def __init__(self, host = None, services = None, composite_versions = ""):
		self.host = host
		self.services = services or {} # dict of Service objects
		self.composite_versions = []
		for expr in composite_versions.split():
			try:
				lst = [item.split("@") for item in expr.split("|")]
				ver, = lst.pop()
				self.composite_versions.append((dict(lst), ver))
			except:
				raise RuntimeError("'%s': expected srv@ver|srv@ver...|ver" % expr)

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, ", ".join(self.keys()))

	# <dict methods>

	def __iter__(self):
		for key in self.services:
			yield key

	def __getitem__(self, key):
		return self.services[key]

	def __setitem__(self, key, value):
		self.services[key] = value

	def __delitem__(self, key):
		del self.services[key]

	def __contains__(self, item):
		return item in self.services.keys()

	def values(self):
		return self.services.values()

	def items(self):
		return self.services.items()

	def keys(self):
		return self.services.keys()

	# </dict methods>

	def sum(self, mapper):
		"apply $mapper to sub-services and sum results"
		res = shell.Success()
		for key, srv in self.services.items():
			r = (mapper)(srv)
			res.returncode = max(res.returncode, r.returncode)
			for line in r.stdout.splitlines():
				res.stdout += "%s: %s\n" % (key, line)
			for line in r.stderr.splitlines():
				res.stderr += "%s: %s\n" % (key, line)
		return res 

	def __getattr__(self, key):
		if self.host:
			return getattr(self.host, key)
		if all(hasattr(srv, key) and callable(getattr(srv, key)) for srv in self.services.values()):
			return lambda *args, **kwargs: self.sum(lambda srv: (getattr(srv, key))(*args, **kwargs))
		raise AttributeError()

	def __call__(self, *args, **kwargs):
		if self.host:
			return (self.host)(*args, **kwargs)
		else:
			return self.sum(lambda srv: (srv)(*args, **kwargs))

	def stop(self):
		return self.sum(lambda srv: srv.stop())

	def start(self):
		return self.sum(lambda srv: srv.start())

	def restart(self):
		return self.sum(lambda srv: srv.restart())

	def reload(self):
		return self.sum(lambda srv: srv.reload())

	def catlog(self):
		return self.sum(lambda srv: srv.catlog())

	def running(self):
		return self.sum(lambda srv: srv.running())

	def version(self, *argv):
		"""
		Show service version.
		
		Usage:
		  version [--list]
		  version --help
		
		Options:
		  -l, --list     list subservices version
		  -h, --help     show help
		"""
		args = docopt.docopt(textwrap.dedent(Services.version.__doc__), argv)
		if args["--list"]:
			return self.sum(lambda srv: srv.version(*argv) if isinstance(srv, Services) else srv.version())
		else:
			versions = {key: "%s" % srv.version().strip() for key, srv in self.services.items()}
			for d, ver in self.composite_versions:
				if d == versions:
					return Success("%s\n" % ver)
			return Failure(stdout = "unknown composite version\n", stderr = "%s\n" % versions)

	def status(self, *argv):
		"""
		Show service status.
		
		Usage:
		  status [--list]
		  status --help
		
		Options:
		  -l, --list     list subservices status
		  -h, --help     show help
		"""
		args = docopt.docopt(textwrap.dedent(Services.status.__doc__), argv)
		res = self.sum(lambda srv: srv.status(*argv) if isinstance(srv, Services) else srv.status())
		if args["--list"]:
			return res
		else:
			try:
				ver = self.version().strip()
			except Exception as e:
				ver = "unknown version"
			if res == 0:
				res.stdout = "%s %s\n" % (ver, green("running"))
				res.stderr = "all services are running\n"
			elif res == 1:
				res.stdout = "%s %s\n" % (ver, blue("unknown"))
				res.stderr += "some services running state is unknown\n"
			elif res == 2:
				res.stdout = "%s %s\n" % (ver, yellow("degraded"))
				res.stderr += "some services are running in degraded state\n"
			elif res == 3:
				res.stdout = "%s %s\n" % (ver, red("not running"))
				res.stderr += "not all services are running\n"
		return res

if __name__ == "__main__": unittest.main(verbosity = 2)
