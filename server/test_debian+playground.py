#!/usr/bin/python2.7
# copyright (c) 2014 arkena, released under the GPL license.

"(debian + playground grid) automated test suite"

import playground
import unittest
import debian

class SelfTest(unittest.TestCase):

	def test(self):
		nginx = debian.Package("nginx", "1.2.1-2+sj34")
		varnish = debian.Package("varnish", "3.0.4+rangecaching6-1")
		grid = playground.Grid()
		plan = grid.deploy(nginx, varnish)

if __name__ == "__main__": unittest.main(verbosity = 2)

