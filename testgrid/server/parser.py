# copyright (c) 2014 arkena, released under the GPL license.

import ConfigParser
import factory
import debian
import model

class ConfigurationError(Exception): pass

class GridConfig(object):

	def __init__(self, gridName, fileName):
		self.config = ConfigParser.RawConfigParser()
		self.config.read(fileName)
		self.gridName = gridName
	
	def getGridType(self):
		if not self.config.has_section(self.gridName):
			raise(ConfigurationError)
		return self.config.get(self.gridName, 'type')
	
	def getNodesInfo(self):
		nodeInfo = []
		nodes =  self.config.get(self.gridName , 'nodes')
		for n in nodes.split(" "):
			if not self.config.has_section(n):
				raise(ConfigurationError)
		nodeInfo.append((self.config.get(n, 'type'), self.config.get(n, 'hoststring')))
		return tuple(nodeInfo)

def parse_grid(name, ini):
	"parse manifests and return a grid instance"
	nodes = []
	config = GridConfig(name, ini)
	gridType = config.getGridType()
	nodeParent = factory.Factory.getClass("model", "Node")
	nodesInfo = config.getNodesInfo()
	for nodeType, hoststring in nodesInfo:
		nodes.append(
			factory.Factory.generateSubclass(nodeParent, 
			nodeType, 
			hoststring=hoststring))
	gridParent = factory.Factory.getClass("model", "Grid")
	grid = factory.Factory.generateSubclass(gridParent, gridType, nodes=nodes)
	return grid

import tempfile
import unittest
import textwrap

class SelfTest(unittest.TestCase):

	@staticmethod
	def file(content = ""):
		f = tempfile.NamedTemporaryFile()
		f.write(textwrap.dedent(content))
		f.flush()
		return f

	def test_grid_not_found(self):
		"assert parse_grid raises an exception on a missing section"
		f = self.file()
		self.assertRaises(Exception, parse_grid, "foo", f.name)

	def test_basic_grid(self):
		"assert parse_grid return a model.Grid if type is grid"
		f = self.file("""
			[foo]
			type = grid
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is model.Grid

	def test_testbox_grid(self):
		"assert parse_grid return a model.Grid if type is grid"
		f = self.file("""
			[foo]
			type = testbox grid
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is testbox.Grid

if __name__  == "__main__": unittest.main(verbosity = 2)
