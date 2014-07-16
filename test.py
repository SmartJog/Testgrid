
import unittest

import testgrid

testmodules = [
	'testgrid.model',
	'testgrid.database',
	'testgrid.persistent',
	'testgrid.controller',
	'testgrid.client',
	'testgrid.isadapter',
	'testgrid.rest'
	# to be completed...
]


class testall(unittest.TestCase):

        def test_all(self):
                suite = unittest.TestSuite()
                for t in testmodules:
                        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))
                runner = unittest.TextTestRunner(verbosity = 2)
                runner.run(suite)

if __name__  == "__main__": unittest.main(verbosity = 2)#unittest.TextTestRunner(verbosity = 2).run(suite)

