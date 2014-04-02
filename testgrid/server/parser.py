# copyright (c) 2013-2014 smartjog, released under the GPL license.

"""
Parse an .ini file and instanciate the corresponding grid object.

API
===
>> import parser
>> grid = parser.parse_grid(name, path)

Manifest Syntax
===============

See utils.get_class.__doc__ for type naming specification.

Node Sections
-------------
[name]
type = name # target class derived from model.Node
extra args...

Gird sections
-------------
[name]
type = name # target class derived from model.Grid
nodes = ...
extra args...
"""

import ConfigParser, tempfile, textwrap, unittest, inspect, os

import factory, model

class ConfigurationError(Exception): pass

class Parser(object):
	"grid manifest parser"

	def __init__(
		self,
		gridName,
		fileName):
		self.gridName = gridName
		self.config = ConfigParser.ConfigParser()
		data = self.config.read(os.path.expanduser(fileName))
		if not data:
			raise ConfigurationError("%s: couldn't find init file " % fileName)
		if not self.config.has_section(self.gridName):
			raise ConfigurationError("%s: unknown section" % self.gridName)
		self._toObject = {"nodes": self.generateNodes}

	def generateNodes(self, valueNodes):
		"generate list of instantiated node object"
		nodes = []
		for n in valueNodes.split(" "):
			nodes.append(self.createObjectFromSection(n, self.parentNode))	
		return nodes

	def createObjectFromSection(self, sectionName, cls):
		"""
		Create an instantiated subclass object from a specific
		section of config file and parent object signature.
		"""
		if not self.config.has_section(sectionName):
			raise ConfigurationError("%s: unknown section" % n)
		objectType = self.config.get(sectionName, 'type')
		objectSignature = factory.Factory.generateSubclassSignature(cls, objectType)
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

	def parse(self):
		"parse manifests and return a grid instance"
		return self.createObjectFromSection(self.gridName, model.Grid)

def parse_grid(name, path):
	"parse manifests and return a grid instance"
	return Parser(name, path).parse()

##############
# unit tests #
##############

class testArg(model.Grid):

	def __init__(self, required, optional="opt", optional2="opt2"):
		super(testArg, self).__init__()
		self.required = required
		self.optional = optional

class SelfTest(unittest.TestCase):

	@staticmethod
	def get_file(content = ""):
		"generate a temporary file with the specified content"
		f = tempfile.NamedTemporaryFile()
		f.write(textwrap.dedent(content))
		f.flush()
		return f

	def test_grid_not_found(self):
		"assert parse_grid raises an exception on a missing section"
		f = self.get_file()
		self.assertRaises(Exception, parse_grid, "foo", f.name)

	def test_basic_grid(self):
		"assert parse_grid return a model.Grid if type is grid"
		f = self.get_file("""
			[foo]
			type = grid
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is model.Grid

	def test_basic_grid_with_nodes(self):
		"assert parse_grid return a model.Grid instantiated with FakeNode nodes"
		f = self.get_file("""
			[node1]
			type = fake Node
			hoststring = root@a.b.c.d

			[node2]
			type = Fake Node
			hoststring = root@a.b.c.d

			[node3]
			type = FaKe NoDe
			hoststring = root@a.b.c.d

			[bar]
			type = grid
			nodes = node1 node2 node3
		""")
		grid = parse_grid("bar", f.name)
		assert type(grid) is model.Grid
		assert len(grid.nodes) is 3
		for n in grid.nodes:
			assert type(n) is model.FakeNode

	def test_testbox_grid(self):
		"assert parse_grid return an AnotherFakeGrid if type is testbox grid"
		f = self.get_file("""
			[foo]
			type = testbox grid
			entry_path = ./en0wifi
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is testbox.Grid

	def test_option_not_found(self):
		"assert parse_grid raises an exception on a wrong option"
		f = self.get_file("""
			[foo]
			type = grid
			bad_arg = bad_arg
		""")
		self.assertRaises(Exception, parse_grid, "foo", f.name)

	def test_required_arg(self):
		f = self.get_file("""
			[foo]
			type = testArg
			required = required
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is testArg

if __name__  == "__main__": unittest.main(verbosity = 2)
