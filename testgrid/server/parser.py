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

import factory, model, utils

def normalized(name):
	return name.title().replace(" ", "")

class ConfigurationError(Exception): pass

class Parser(object):
	"grid manifest parser"

	def __init__(self, gridName, filePath):
		self.gridName = gridName
		self.filePath = filePath
		self.reload()

	def reload(self):
		self.cache = {}
		self.conf = ConfigParser.ConfigParser()
		res = self.conf.read(os.path.expanduser(self.filePath))
		if not res:
			raise ConfigurationError("%s: couldn't find init file " % self.filePath)
		##self._toObject = {"nodes": self.generateNodes}

#	def _generateNodes(self, valueNodes):
#		"generate list of instantiated node object"
#		nodes = []
#		for n in valueNodes.split(" "):
#			nodes.append(self.createObjectFromSection(n, self.parentNode))	
#		return nodes

#	def _createObjectFromSection(self, sectionName, cls):
#		"""
#		Create an instantiated subclass object from a specific
#		section of config file and parent object signature.
#		"""
#		if not self.config.has_section(sectionName):
#			raise ConfigurationError("%s: unknown section" % n)
#		objectType = self.config.get(sectionName, 'type')
#		objectSignature = factory.Factory.generateSubclassSignature(cls, objectType)
#		arg = {}
#		for opt, value in  self.config.items(sectionName):
#			if opt != "type":
#				argspec = inspect.getargspec(objectSignature.__init__)
#				assert opt in argspec[0], "%s: unknown attribute" % opt
#				if opt in self._toObject:
#					arg[opt] = self._toObject[opt](value)
#				else:
#					arg[opt] = value
#		return objectSignature(**arg)

	def _parse_node(self, section):
		assert self.conf.has_section(section), "%s: node section not defined" % section
		cls = model.Node
		kwargs = {}
		try:
			for key, value in self.conf.items(section):
				if key == "type":
					try:
						cls = utils.get_subclass(normalized(value), model.Node)
					except Exception as e:
						raise Exception("%s: invalid node type\n%s" % (value, repr(e)))
				else:
					kwargs[key] = value
			obj = (cls)(**kwargs)
		except Exception as e:
			raise ConfigurationError("in [%s]: %s" % (section, e))
		self.cache[section] = obj
		return obj

	def _parse_grid(self, section):
		assert self.conf.has_section(section), "%s: node section not defined" % section
		cls = model.Grid
		nodes = []
		kwargs = {}
		try:
			for key, value in self.conf.items(section):
				if key == "type":
					if value == "grid": continue
					try:
						cls = utils.get_subclass(normalized(value), model.Grid)
					except Exception as e:
						raise Exception("%s: invalid grid type\n%s" % (value, repr(e)))
				elif key == "nodes":
					for s in value.split():
						nodes.append(self.cache[s] if s in self.cache else self._parse_node(s))
				else:
					kwargs[key] = value
			obj = (cls)(*nodes, **kwargs)
		except Exception as e:
			raise ConfigurationError("in [%s]: %s" % (section, e))
		self.cache[section] = obj
		return obj

	def parse(self):
		"parse manifests and return a grid instance"
		#return self.createObjectFromSection(self.gridName, model.Grid)
		return self._parse_grid(self.gridName)

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
		self.assertIs(type(grid), model.Grid)

	def test_basic_grid_with_fake_nodes(self):
		"assert parse_grid return a model.Grid instantiated with FakeNode nodes"
		f = self.get_file("""
			[node1]
			type = fake node
			
			[node2]
			type = FaKe NoDe
			
			[node3]
			type = FAKE NODE
			
			[bar]
			type = grid
			nodes = node1 node2 node3
		""")
		grid = parse_grid("bar", f.name)
		self.assertIs(type(grid), model.Grid)
		self.assertIs(len(grid.nodes), 3)
		for node in grid.nodes:
			self.assertIs(type(node), model.FakeNode)

	def test_custom_grid(self):
		"assert parse_grid return an AnotherFakeGrid if type is testbox grid"
		CustomGrid = type("CustomGrid", (model.Grid,), {})
		f = self.get_file("""
			[foo]
			type = custom grid
		""")
		grid = parse_grid("foo", f.name)
		self.assertIs(type(grid), CustomGrid)

	def _test_option_not_found(self):
		"assert parse_grid raises an exception on a wrong option"
		f = self.get_file("""
			[foo]
			type = grid
			bad_arg = bad_arg
		""")
		self.assertRaises(Exception, parse_grid, "foo", f.name)

	def _test_required_arg(self):
		f = self.get_file("""
			[foo]
			type = testArg
			required = required
		""")
		grid = parse_grid("foo", f.name)
		assert type(grid) is testArg

if __name__  == "__main__": unittest.main(verbosity = 2)
