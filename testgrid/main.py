# copyright (c) 2014 arkena, released under the GPL license.

"""
Testgrid command-line utility.

Usage:
  tg --version
  tg --help

Options:
  -h, --help  show help
  --version   show version
"""

__version__ = "0.1"

import docopt, sys

def main():
	args = docopt.docopt(__doc__, version = __version__)
	return 0

if __name__ == "__main__": sys.exit(main())
