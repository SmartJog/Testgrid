# copyright (c) 2014 arkena, released under the GPL license.
import ConfigParser
import factory
import debian
import testbox
import restgrid
import model
import inspect
import os

class ConfigurationError(Exception): pass

class GridConfig(object):
	"""parse manifest of  of a grid and object creation"""
	def __init__(self, gridName, fileName, parentGrid=model.Grid, parentNode=model.Node):
		self.gridName = gridName
		self.parentGrid = parentGrid
		self.parentNode = parentNode

		self.config = ConfigParser.RawConfigParser()
		data = self.config.read(os.path.expanduser(fileName))
		if not data:
			raise ConfigurationError("%s: couldn't find init file " % fileName)
		if not self.config.has_section(self.gridName):
			raise ConfigurationError("%s: unknown section" % self.gridName)
		self._toObject = {"nodes": self.generateNodes}



	def createObjectFromSection(self, sectionName, parentSignature):
		""" create an instantiated subclass object from a specific section of config file  
		and parent object signature"""

		if not self.config.has_section(sectionName):
			raise ConfigurationError("%s: unknown section" % n)
		objectType = self.config.get(sectionName, 'type')
		objectSignature = factory.Factory.generateSubclassSignature(parentSignature, objectType)
		arg = {}
		for opt, value in  self.config.items(sectionName):
			if opt != "type":
				argspec = inspect.getargspec(objectSignature.__init__)
				assert opt in argspec[0], "%s: unknown attribute" % opt
				if opt in self._toObject:
					arg[opt] = self._toObject[opt](value)
				else:
					arg[opt] = value
		return objectSignature(**arg)


	def generateNodes(self, valueNodes):
		"""generate list of instantiated node object """
		nodes = []
		for n in valueNodes.split(" "):
			nodes.append(self.createObjectFromSection(n, self.parentNode))	
		return nodes
		

	def parse_grid(self):
		"parse manifests and return a grid instance"
		return self.createObjectFromSection(self.gridName, self.parentGrid)


def parse_grid(name, ini):
	"parse manifests and return a grid instance"
	config = GridConfig(name, ini)
	return config.parse_grid()
	

import tempfile
import unittest
import textwrap

class parserFakeGrid(model.Grid):
	def __init__(self, nodes):
		super(parserFakeGrid, self).__init__(nodes)

class  testArg(model.Grid):
	def __init__(self, required, optional="opt", optional2="opt2"):
		super(testArg, self).__init__()
		self.required = required
		self.optional = optional

		
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
		""" assert parse_grid return a parserFakeGrid instantiated with debian Node"""
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
		"assert parse_grid return a testbox.Grid if type is testbox grid"
		f = self.file("""
			[foo]
			type = testbox grid
			entry_path = ./en0wifi
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is testbox.Grid

	def test_option_not_found(self):
		"assert parse_grid raises an exception on a wrong option"
		f = self.file("""
			[foo]
			type = grid
			bad_arg = bad_arg
		""")
		self.assertRaises(Exception, parse_grid, "foo", f.name)

	def test_required_arg(self):
		f = self.file("""
			[foo]
			type = testArg
			required = required
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is testArg

if __name__  == "__main__": unittest.main(verbosity = 2)
