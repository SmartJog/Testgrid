
import unittest

import testgrid

testmodules = [
	'testgrid.model',
	'testgrid.database',
	'testgrid.controller',
	# to be completed...
]

suite = unittest.TestSuite()

for t in testmodules:
	suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

if __name__  == "__main__": unittest.TextTestRunner(verbosity = 2).run(suite)

