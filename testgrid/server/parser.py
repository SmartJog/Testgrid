# copyright (c) 2014 arkena, released under the GPL license.

import ConfigParser
import factory
import debian
import testbox
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
		items = self.config.options(self.gridName)
		if "nodes" in items:
			nodes =  self.config.get(self.gridName , 'nodes')
			for n in nodes.split(" "):
				if not self.config.has_section(n):
					raise(ConfigurationError)
				nodeInfo.append((self.config.get(n, 'type'), self.config.get(n, 'hoststring')))
			return tuple(nodeInfo)
		return None

def parse_grid(name, ini):
	"parse manifests and return a grid instance"
	nodes = []
	config = GridConfig(name, ini)
	gridType = config.getGridType()
	#gridParent = factory.Factory.getClass("model", "Grid")
	#nodeParent = factory.Factory.getClass("model", "Node")
	nodesInfo = config.getNodesInfo()
	if not nodesInfo:
		return factory.Factory.generateSubclass(model.Grid, gridType)
	for nodeType, hoststring in nodesInfo:
		nodes.append(
			factory.Factory.generateSubclass(model.Node, 
							 nodeType, 
							 hoststring=hoststring))
	return factory.Factory.generateSubclass(model.Grid, gridType, *nodes)
	

import tempfile
import unittest
import textwrap

class parserFakeGrid(model.Grid):
	def __init__(self, nodes):
		self.nodes = nodes
	
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

	def test_basic_grid_with_nodes(self):
		"assert parse_grid return a model.Grid if type is grid with defined node"
		f = self.file("""
			[node1]
			type = debian Node
			hoststring = root@a.b.c.d

			[node2]
			type = Debian Node
			hoststring = root@a.b.c.d

			[node3]
			type = debiAn node
			hoststring = root@a.b.c.d

			[foo]
			type = parserFakeGrid
			nodes = node1 node2 node3

		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is parserFakeGrid
		assert len(grid.nodes) is 3
		for n in grid.nodes:
			assert type(n) is debian.Node


	def test_testbox_grid(self):
		"assert parse_grid return a model.Grid if type is grid"
		f = self.file("""
			[foo]
			type = testbox grid
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is testbox.Grid

if __name__  == "__main__": unittest.main(verbosity = 2)
