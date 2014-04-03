# copyright (c) 2014 arkena, released under the GPL license.

"""
Testgrid command-line utility.

Usage:
  tg [-s NAME] [-m INI] [--local|-c HOST] ARGV...
  tg --version
  tg --help

Options:
  -s NAME, --section NAME     grid section name [default: grid]
  -m INI, --manifest INI      comma-separated list of .ini filepaths or URIs [default: ~/grid.ini]
  -l, --local                 use local client
  -c HOST, --controller HOST  set controller HOST for REST client [default: qa.lab.fr.lan:8080]
  -h, --help                  show help
  --version                   show version

ARGV:
  nodes       list nodes
  sessions    list sessions
  create KEY  create session
  delete KEY  delete session
"""

__version__ = "0.1"

import docopt, sys

import client

def red(string):
	return string and "\033[0;91m%s\033[0m" % string

def blue(string):
	return string and "\033[0;94m%s\033[0m" % string

def gray(string):
	return string and "\033[0;90m%s\033[0m" % string

def green(string):
	return string and "\033[0;92m%s\033[0m" % string

def main():
	try:
		args = docopt.docopt(__doc__, version = __version__)
		if args["--local"]:
			c = client.local.Client(
				name = args["--section"],
				ini = args["--manifest"])
		else:
			c = client.rest.Client(args["--controller"])
		cmd = args["ARGV"][0]
		if cmd == "nodes":
			for node in c.get_nodes():
				if c.is_available(node):
					print node, green("available")
				elif c.is_allocated(node):
					print node, blue("allocated")
				elif c.is_quarantined(node):
					print node, red("quarantined")
		elif cmd == "sessions":
			for session in c.get_sessions():
				print session
		elif cmd == "create":
			_, key = args["ARGV"]
			c.create_session(key)
		elif cmd == "delete":
			_, key = args["ARGV"]
			c.delete_session(key)
		else:
			raise NotImplementedError("%s: unknown command" % cmd)
		return 0
	except Exception as e:
		sys.stderr.write(gray("%s: %s\n" % (type(e).__name__, e)))
		return 1

if __name__ == "__main__": sys.exit(main())
