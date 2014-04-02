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

class ExtraArgumentError(ConfigurationError): pass

class MissingArgumentError(ConfigurationError): pass

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

	@staticmethod
	def _mkobj(cls, *args, **kwargs):
		xargs, varargs, keywords, defaults = inspect.getargspec(cls.__init__)
		for arg in xargs[1:]: # skip self
			if not arg in kwargs:
				raise MissingArgumentError("%s: missing argument" % arg)
		if not keywords:
			for arg in kwargs:
				if not arg in xargs:
					raise ExtraArgumentError("%s: extra argument" % arg)
		return (cls)(*args, **kwargs)

	def _parse_node(self, section):
		cls = model.Node
		kwargs = {}
		for key, value in self.conf.items(section):
			if key == "type":
				try:
					cls = utils.get_subclass(normalized(value), model.Node)
				except Exception as e:
					raise Exception("%s: invalid node type\n%s" % (value, repr(e)))
			else:
				kwargs[key] = value
		return self._mkobj(cls, **kwargs)

	def _parse_grid(self, section):
		cls = model.Grid
		nodes = []
		kwargs = {}
		for key, value in self.conf.items(section):
			if key == "type":
				if value == "grid": continue
				try:
					cls = utils.get_subclass(normalized(value), model.Grid)
				except Exception as e:
					raise Exception("%s: invalid grid type\n%s" % (value, repr(e)))
			elif key == "nodes":
				for s in value.split():
					nodes.append(self.cache[s] if s in self.cache else self._parse(s, self._parse_node))
			else:
				kwargs[key] = value
		return self._mkobj(cls, *nodes, **kwargs)

	def _parse(self, section, hdl):
		assert self.conf.has_section(section), "%s: section not defined" % section
		try:
			obj = hdl(section)
			self.cache[section] = obj
			return obj
		except Exception as e:
			if isinstance(e, ConfigurationError):
				exc = type(e)
			else:
				exc = ConfigurationError
			raise (exc)("in [%s]: %s" % (section, e))

	def parse(self):
		"parse manifests and return a grid instance"
		#return self.createObjectFromSection(self.gridName, model.Grid)
		return self._parse(self.gridName, self._parse_grid)

def parse_grid(name, path):
	"parse manifests and return a grid instance"
	return Parser(name, path).parse()

##############
# unit tests #
##############

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
		"assert parse_grid returns a model.Grid if type is grid"
		f = self.get_file("""
			[foo]
			type = grid
		""")
		grid = parse_grid("foo", f.name)
		self.assertIs(type(grid), model.Grid)

	def test_basic_grid_with_fake_nodes(self):
		"assert parse_grid returns a model.Grid instantiated with FakeNode nodes"
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
		"assert parse_grid returns an AnotherFakeGrid if type is testbox grid"
		CustomGrid = type("CustomGrid", (model.Grid,), {})
		f = self.get_file("""
			[foo]
			type = custom grid
		""")
		grid = parse_grid("foo", f.name)
		self.assertIs(type(grid), CustomGrid)

	def test_extra_argument(self):
		"assert parse_grid raises an ExtraArgumentError on any extra argument"
		f = self.get_file("""
			[foo]
			type = grid
			bad_arg = bad_arg
		""")
		self.assertRaises(ExtraArgumentError, parse_grid, "foo", f.name)

	def test_required_argument(self):
		def init(self, arg, *nodes):
			super(model.Grid, self).__init__(*nodes)
		type("GridWithArg", (model.Grid,), {
			"__init__": init,
		})
		"assert parse_grid raises a MissingArgumentError on any missing required argument"
		f = self.get_file("""
			[foo]
			type = grid with arg
		""")
		self.assertRaises(MissingArgumentError, parse_grid, "foo", f.name)

if __name__  == "__main__": unittest.main(verbosity = 2)
