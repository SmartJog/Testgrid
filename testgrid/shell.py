# copyright (c) 2013-2014 fclaerhout.fr, released under the MIT license.

"""
Command execution framework.

API:
  r = Result(returncode, [stdout], [stderr])
  Success(...) = Result(0, ...)
  Failure(...) = Result(1, ...)
  Strerr(...)
  Stdout(...)
  Null(...)
  asynchronous command execution:
    - sp = launch(argv, logger = Null)
    - res = fetch(sp, logger = Null, warn_only = False)
  synchronous command execution:
    - res = run(argv, logger = Null, warn_only = False, on_line = None)
    - res = sudo(username, argv, ...)
    - res = ssh(hoststring, argv, ...)
    - res = scp(hoststring, localpath, remotepath, ...)

Environment variables:
  SSHCONNECTTIMEOUT  ssh connect timeout
  SSHPASS            generic password for sshpass

Files:
  ~/.sshpass/<hoststring>  specific password for sshpass

Tutorial:
  >>> import shell
  >>> res = shell.run("uname")
  >>> "%s" % res.strip()
  'Darwin'
  >>> int(res)
  0
  >>> res = shell.run("false", warn_only = True)
  >>> int(res)
  1
"""

import subprocess, threading, unittest, atexit, pipes, time, sys, os

class Result(object):
	"""
	Wrap command result (returncode, stdout, stderr).
	Behaves like returncode on boolean and int operations.
	Behaves like stdout on string operations.
	"""

	def __init__(self, returncode, stdout = None, stderr = None):
		self.returncode = returncode
		self.stdout = stdout or ""
		self.stderr = stderr or ""

	def __repr__(self):
		return "%s(%i, %s, %s)" % (
			type(self).__name__,
			self.returncode,
			repr(self.stdout),
			repr(self.stderr))

	def __nonzero__(self):
		return self.returncode == 0 # True if command succeeded

	def __str__(self):
		return self.stdout

	def __int__(self):
		return self.returncode

	def __getattr__(self, key):
		return getattr(self.stdout, key)

	def __contains__(self, other):
		return other in self.stdout

	def __eq__(self, other):
		if isinstance(other, Result):
			return self.returncode == other.returncode\
			and self.stdout == other.stdout\
			and self.stderr == other.stderr
		return other.__class__(self) == other

	def __iadd__(self, other):
		self.returncode = max(self.returncode, other.returncode)
		self.stdout += other.stdout
		self.stderr += other.stderr
		return self

	def __add__(self, other):
		r = Result(
			returncode = self.returncode,
			stdout = self.stdout,
			stderr = self.stderr)
		r += other
		return r

def Success(stdout = None, stderr = None):
	return Result(0, stdout, stderr)

def Failure(stdout = None, stderr = None):
	return Result(1, stdout, stderr)

def gray(string):
	return string and "\033[0;90m%s\033[0m" % string

def Stderr(string):
	return sys.stderr.write("%s: %s\n" % (
		gray(time.strftime("%Y.%m.%d.%H.%M.%S", time.localtime())),
		string.rstrip()))

def Stdout(string):
	return sys.stdout.write("%s: %s\n" % (
		gray(time.strftime("%Y.%m.%d.%H.%M.%S", time.localtime())),
		string.rstrip()))

def Null(*args, **kwargs): pass

class BadCommandError(Exception):

	def __init__(self, argv, exc):
		super(BadCommandError, self).__init__("bad command %s: %s" % (argv, exc))
		self.argv = argv
		self.exc = exc

def launch(argv, logger = Null):
	"asynchronous command execution, return process"
	(logger)("executing command: %s" % (argv,))
	try:
		sp = subprocess.Popen(
			args = argv,
			shell = isinstance(argv, str), # use shell on string
			stdout = subprocess.PIPE,
			stderr = subprocess.PIPE)
		sp.argv = argv
	except Exception as e:
		raise BadCommandError(argv = argv, exc = e)
	return sp

class CommandFailure(Exception):

	def __init__(self, argv, returncode, stderr):
		super(CommandFailure, self).__init__(
			"command failed %s: status=%i, stderr=%s" % (argv, returncode, stderr.strip()))
		self.argv = argv
		self.returncode = returncode
		self.stderr = stderr

def fetch(sp, logger = Null, warn_only = False):
	"""
	wait for process result, then:
	  * if warn_only = False, raise CommandFailure on failure
	  * return Result otherwise
	"""
	stdout, stderr = sp.communicate()
	if stdout:
		(logger)("stdout: %s" % stdout)
	if stderr:
		(logger)("stderr: %s" % stderr)
	res = Result(returncode = sp.returncode, stdout = stdout, stderr = stderr)
	if not res and not warn_only:
		raise CommandFailure(
			argv = sp.argv,
			returncode = res.returncode,
			stderr = res.stderr)
	return res

def run(
	argv,
	logger = Null,
	warn_only = False,
	on_stdout_line = None,
	on_stderr_line = None):
	"""
	Synchronous command execution.
	if on_stdout_line (resp. on_stderr_line) is set,
	res.stdout (resp. res.stderr) will be empty as the buffer is already read.
	"""
	sp = launch(argv = argv, logger = logger)
	def reader(stream, callback):
		line = stream.readline()
		while line:
			(callback)(line)
			line = stream.readline()
	if on_stdout_line:
		t = threading.Thread(target = reader, args = (sp.stdout, on_stdout_line))
		t.daemon = True
		t.start()
		t.join()
	if on_stderr_line:
		t = threading.Thread(target = reader, args = (sp.stderr, on_stderr_line))
		t.daemon = True
		t.start()
		t.join()
	return fetch(sp = sp, logger = logger, warn_only = warn_only)

def _wrapped_run(executor, argv, *args, **kwargs):
	"synchronous wrapped command execution"
	if isinstance(argv, str):
		argv = " ".join(executor + (pipes.quote(argv),)) # escape $argv for shell
	elif type(argv) in (list, tuple):
		argv = executor + tuple(argv)
	else:
		raise RuntimeError("%s: unexpected argv" % argv)
	return run(argv = argv, *args, **kwargs)

def sudo(username, argv, *args, **kwargs):
	return _wrapped_run(("sudo", "-u", username), argv, *args, **kwargs)

def _sshpass(hoststring):
	path = os.path.expanduser("~/.sshpass/%s" % hoststring)
	if os.path.exists(path):
		return ("sshpass", "-f%s" % path)
	elif os.getenv("SSHPASS"):
		return ("sshpass", "-e")
	else:
		return ()

control_master = {}

def ssh(hoststring, argv, *args, **kwargs):
	executor = _sshpass(hoststring) + (
		"ssh",
		"-o", "NumberOfPasswordPrompts=%i" % (1 if _sshpass(hoststring) else 0),
		"-o", "StrictHostKeyChecking=no",
		"-o", "ConnectTimeout=%s" % (os.getenv("SSHCONNECTTIMEOUT") or 100),
		"-S", "%s.socket" % hoststring, # use control master if available
		"%s" % hoststring)
	if not hoststring in control_master:
		control_master[hoststring] = launch(executor + ("-MT", "-S", "%s.socket" % hoststring))
		atexit.register(lambda: launch(executor + ("-O", "exit"))) # FIXME: last for whole session
	return _wrapped_run(executor, argv, *args, **kwargs)

def scp(hoststring, localpath, remotepath, *args, **kwargs):
	executor = _sshpass(hoststring) + ("scp",)
	argv = (localpath, "%s:%s" % (hoststring, remotepath))
	return _wrapped_run(executor, argv, *args, **kwargs)

#########
# tests #
#########

class SelfTest(unittest.TestCase):

	def test_argv(self):
		self.assertEqual(run("ls -al"), run(["ls", "-a", "-l"]))

	def test_success(self):
		self.assertTrue(run("true"))

	def test_failure(self):
		self.assertRaises(Exception, run, "false")

	def test_warning(self):
		self.assertFalse(run("false", warn_only = True))

	def test_stdout(self):
		self.assertEqual(run("echo hello"), "hello\n")

if __name__ == "__main__": unittest.main(verbosity = 2)
