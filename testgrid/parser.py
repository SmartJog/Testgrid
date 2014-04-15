# copyright (c) 2013-2014 smartjog, released under the GPL license.

"""
Parse an .ini file and instanciate the corresponding grid object.

API
===
>> import parser
>> grid = parser.parse_grid(ini, *modules).parse(name)

Manifest Syntax
===============

See utils.get_class.__doc__ for type naming specification.

Node Sections
-------------
[name]
type = name # target class derived from testgrid.model.Node
extra args...

Gird sections
-------------
[name]
type = name # target class derived from testgrid.model.Grid
nodes = ...
extra args...
"""

import ConfigParser, tempfile, textwrap, unittest, inspect, os, re

import testgrid

def get_subclasses(cls, *modules):
	"return all subclasses of $cls in specified $modules"
	res = []
	for subcls in cls.__subclasses__():
		if (not modules or subcls.__module__ in modules):
			res += [subcls] + get_subclasses(subcls, *modules)
		else:
			res += get_subclasses(subcls, *modules)
	return res

def normalized(name):
	"normalize a class name, e.g. Foo BAR4 2 -> FooBar42"
	return name.title().replace(" ", "")

def get_subclass(name, cls,*modules):
	"return the $name'd subclass of $cls in specified $modules"
	subclasses = get_subclasses(cls, *modules)
	for subcls in subclasses:
		if subcls.__name__ == name:
			return subcls
	raise Exception("%s: subclass not found in %s\navailable subclasses: %s" % (
		name,
		modules or "any module",
		subclasses))

class ConfigurationError(Exception): pass

class ExtraArgumentError(ConfigurationError): pass

class MissingArgumentError(ConfigurationError): pass

class Parser(object):
	"grid manifest parser"

	def __init__(self, ini, *modules):
		"ini: comma-separated list of .ini filepaths or URIs"
		self.modules = modules or ()
		self.ini = ini
		self.reload()

	def reload(self):
		self.cache = {}
		self.conf = ConfigParser.ConfigParser()
		# load all manifests:
		for item in self.ini.split(","):
			try:
				if re.match("[a-z]*://", item):
					fp = urllib2.urlopen(item)
				else:
					fp = open(os.path.abspath(os.path.expanduser(item)), "r")
				self.conf.readfp(fp)
			except Exception as e:
				raise ConfigurationError("%s: invalid manifest\n%s" % (item, e))

	@staticmethod
	def _mkobj(cls, *varargs, **kwargs):
		args, _varargs, _kwargs, defaults = inspect.getargspec(cls.__init__)
		# check all required args are present:
		required = args[1:-len(defaults or ())] # skip "self"
		for arg in required:
			if not arg in kwargs and required.index(arg) >= len(varargs):
				raise MissingArgumentError("%s: missing argument" % arg)
		# check optional args are allowed:
		if not _kwargs:
			for arg in kwargs:
				if not arg in args:
					raise ExtraArgumentError("%s: extra argument" % arg)
		return (cls)(*varargs, **kwargs)

	def _parse_node(self, section):
		cls = testgrid.model.Node
		kwargs = {"name": section}
		for key, value in self.conf.items(section):
			if key == "type":
				try:
					cls = get_subclass(normalized(value), testgrid.model.Node, *self.modules)
				except Exception as e:
					raise Exception("%s: invalid node type\n%s" % (value, repr(e)))
			else:
				kwargs[key] = value
		return self._mkobj(cls, **kwargs)

	def _parse_grid(self, section):
		cls = testgrid.model.Grid
		kwargs = {"name": section}
		for key, value in self.conf.items(section):
			if key == "type":
				if value == "grid": continue
				try:
					cls = get_subclass(normalized(value), testgrid.model.Grid, *self.modules)
				except Exception as e:
					raise Exception("%s: invalid grid type\n%s" % (value, repr(e)))
			elif key.endswith("nodes"):
				nodes = []
				for s in value.split():
					nodes.append(self.cache[s] if s in self.cache else self._parse(s, self._parse_node))
				kwargs[key] = nodes
			elif key.endswith("grids"):
				grids = []
				for s in value.split():
					grids.append(self.cache[s] if s in self.cache else self._parse(s, self._parse_grid))
				kwargs[key] = grids
			elif key.endswith("subnets"):
				subnets = []
				for s in value.split():
					subnets.append(testgrid.model.Subnet(s))
				kwargs[key] = subnets
			else:
				kwargs[key] = value
		return self._mkobj(cls, **kwargs)

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

	def parse_grid(self, name):
		"parse manifests and return a grid instance"
		return self._parse(name, self._parse_grid)

def parse_grid(name, ini, *modules):
	"parse manifests and return a grid instance"
	return Parser(ini, *modules).parse_grid(name)

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
		"assert parse_grid returns a testgrid.model.Grid if type is grid"
		f = self.get_file("""
			[foo]
			type = grid
		""")
		grid = parse_grid("foo", f.name)
		self.assertIs(type(grid), testgrid.model.Grid)

	def test_basic_grid_with_fake_nodes(self):
		"assert parse_grid returns a testgrid.model.Grid instantiated with FakeNode nodes"
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
		self.assertIs(type(grid), testgrid.model.Grid)
		self.assertIs(len(grid.nodes), 3)
		for node in grid.nodes:
			self.assertIs(type(node), testgrid.model.FakeNode)

	def test_custom_grid(self):
		"assert parse_grid returns an AnotherFakeGrid if type is testbox grid"
		CustomGrid = type("CustomGrid", (testgrid.model.Grid,), {})
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
		def init(self, name, arg, nodes = None, subnets = None, sessions = None): pass
		type("GridWithArg", (testgrid.model.Grid,), {
			"__init__": init,
		})
		"assert parse_grid raises a MissingArgumentError on any missing required argument"
		f = self.get_file("""
			[foo]
			type = grid with arg
		""")
		self.assertRaises(MissingArgumentError, parse_grid, "foo", f.name)

if __name__  == "__main__": unittest.main(verbosity = 2)
