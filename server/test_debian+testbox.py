#!/usr/bin/python2.7
# copyright (c) 2014 arkena, released under the GPL license.

"(debian + testbox nodes + generic grid) automated test suite"

import unittest
import testgrid
import testbox
import debian

class SelfTest(unittest.TestCase):

	def test_single_local_vm(self):
		node = testbox.Node()
		nginx = debian.Package("nginx", "1.2.1-2+sj34")
		varnish = debian.Package("varnish", "3.0.4+rangecaching6-1")
		streamer = testgrid.Packages("ohcache", "2", nginx, varnish)
		grid = testgrid.Grid(node)
		plan = grid.deploy(streamer)
		self.assertEqual(plan, ((streamer, node),))
		assert node.is_installed(nginx)
		assert node.is_installed(varnish)

if __name__ == "__main__": unittest.main(verbosity = 2)

