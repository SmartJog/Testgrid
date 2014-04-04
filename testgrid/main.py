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

import strfmt, client

def main():
	try:
		args = docopt.docopt(__doc__, version = __version__)
		if args["--local"]:
			clt = client.local.Client(
				name = args["--section"],
				ini = args["--manifest"])
		else:
			clt = client.rest.Client(args["--controller"])
		cmd = args["ARGV"][0]
		if cmd == "nodes":
			text = "nodes:status\n-----:------\n"
			for node in clt.get_nodes():
				if clt.is_available(node):
					text += "%s:%s\n" % (node, strfmt.green("available"))
				elif clt.is_allocated(node):
					text += "%s:%s\n" % (node, strfmt.blue("allocated"))
				elif clt.is_quarantined(node):
					text += "%s:%s\n" % (node, strfmt.red("quarantined"))
			print strfmt.strcolalign(text)
		elif cmd == "sessions":
			for session in clt.get_sessions():
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
		sys.stderr.write(strfmt.gray("%s: %s\n" % (type(e).__name__, e)))
		return 1

if __name__ == "__main__": sys.exit(main())
