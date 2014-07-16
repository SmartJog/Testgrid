
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

suite = unittest.TestSuite()
for t in testmodules:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

if __name__  == "__main__":unittest.TextTestRunner(verbosity = 2).run(suite)

