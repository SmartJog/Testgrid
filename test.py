#!/usr/bin/python2.7

import unittest
import client

class Base(unittest.TestCase):

	Session = client.fake.Session

	def test_node_isolation(self):
		"test nodes are isolated on their network"
		s1 = self.Session()
		x = s1.allocate_node()
		y = s1.allocate_node()
		assert x.ping(x)
		assert x.ping(y)
		assert y.ping(y)
		assert y.ping(x)
		s2 = self.Session()
		z = s2.allocate_node()
		assert z.ping(z)
		assert not z.ping(x)
		assert not z.ping(y)

	def test_grid_session(self):
		# session = named subnet associated to the current user
		"a grid session can be opened only once"
		g = self.Session("foo")
		self.assertRaises(AssertionError, self.Session, "foo")
		g.close()
		g = self.Session("foo")
		g.close()

	def test_usecase_1(self):
		"test deployment of a simple debian package"
		g = self.Session()
		pkg = client.debian.Package("fleche", version = "16.3-1")
		n = g.deploy(pkg)
		self.assertEqual(n.service("fleche").version(), "16.3-1")

if __name__ == "__main__": unittest.main(verbosity = 2)
