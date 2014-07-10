# copyright (c) 2013-2014 smartjog, released under the GPL license.

"""
Parse an .ini file and instanciate named grid or node objects.

Manifest Syntax:

	See utils.get_class.__doc__ for type naming specification.

	Node Sections
	-------------
	[name]
	type = name # target class derived from model.Node
	extra args...

	Grid sections
	-------------
	[name]
	type = name # target class derived from model.Grid
	nodes = ...
	extra args...

Example:
	$ cat > example.ini <<EOF
	[mynode]
	type = fake node
	[mygrid]
	type = fake grid
	EOF
	$ PYTHONPATH=".." python
	>> import parser
	>> mygrid = p.parse_grid("mygrid", ini = "example.ini")
	>> mynode = p.parse_node("mynode", ini = "example.ini")
"""

import ConfigParser, tempfile, textwrap, unittest, inspect, os, re

from testgrid import model

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

class NoSuchTypeError(Exception):

	def __init__(self, name, *modules):
		super(NoSuchTypeError, self).__init__("%s: no such type in %s" % (
			name,
			modules))

def get_subclass(name, cls, *modules):
	"return the $name'd subclass of $cls in specified $modules"
	subclasses = get_subclasses(cls, *modules)
	for subcls in subclasses:
		if subcls.__name__ == name:
			return subcls
	raise NoSuchTypeError(name, *modules)

class NoSuchSectionError(Exception):

	def __init__(self, section):
		super(NoSuchSectionError, self).__init__("%s: no such section" % section)

class SectionError(Exception):

	def __init__(self, section, exc):
		super(SectionError, self).__init__("in [%s], %s" % (section, exc))
		self.exc = exc

class ExtraArgumentError(Exception):

	def __init__(self, argname):
		super(ExtraArgumentError, self).__init__("%s: extra argument" % argname)
		self.argname = argname

class MissingArgumentError(Exception):

	def __init__(self, argname):
		super(MissingArgumentError, self).__init__("%s: missing argument" % argname)
		self.argname = argname

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
				raise Exception("%s: invalid manifest\n%s" % (item, e))

	@staticmethod
	def _mkobj(cls, *varargs, **kwargs):
		"instanciate object checking first ctor args are correct"
		args, _varargs, _kwargs, defaults = inspect.getargspec(cls.__init__)
		# check all required args are present:
		required = args[1:-len(defaults or ())] # skip "self"
		for arg in required:
			if not arg in kwargs and required.index(arg) >= len(varargs):
				raise MissingArgumentError(arg)
		# check optional args are allowed:
		if not _kwargs:
			for arg in kwargs:
				if not arg in args:
					raise ExtraArgumentError(arg)
		return (cls)(*varargs, **kwargs)

	def _parse_node(self, section):
		cls = model.Node
		kwargs = {"name": section}
		for key, value in self.conf.items(section):
			if key == "type":
				cls = get_subclass(normalized(value), model.Node, *self.modules)
			else:
				kwargs[key] = value
		return self._mkobj(cls, **kwargs)

	def _parse_node_dictionary(self, section):
		kwargs = {"name": section}
		for key, value in self.conf.items(section):
			kwargs[key] = value
		return kwargs

	def _parse_grid(self, section):
		cls = model.Grid
		kwargs = {"name": section}
		for key, value in self.conf.items(section):
			if key == "type":
				if value == "grid": continue
				cls = get_subclass(normalized(value), model.Grid, *self.modules)
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
					subnets.append(model.Subnet(s))
				kwargs[key] = subnets
			else:
				kwargs[key] = value
		return self._mkobj(cls, **kwargs)

	def _parse_session(self, section):
		for key, value in self.conf.items(section):
			if key.endswith("nodes"):
				nodes_opt = []
				for s in value.split():
					nodes_opt.append(self.cache[s] if s in self.cache else self._parse(s, self._parse_node_dictionary))
				return nodes_opt

	def _parse(self, section, hdl):
		if not self.conf.has_section(section):
		 raise NoSuchSectionError(section)
		else:
			try:
				obj = hdl(section)
				self.cache[section] = obj
				return obj
			except Exception as e:
				raise SectionError(section, e)

	def parse_node(self, name):
		return self._parse(name, self._parse_node)

	def parse_grid(self, name):
		return self._parse(name, self._parse_grid)


	def parse_node_dictionary(self, name):
		return self._parse(name, self._parse_node_dictionary)

	def parse_session(self, name):
		return self._parse(name, self._parse_session)

def parse_node(name, ini, *modules):
	"parse manifests and return a node instance"
	return Parser(ini, *modules).parse_node(name)

def parse_grid(name, ini, *modules):
	"parse manifests and return a grid instance"
	return Parser(ini, *modules).parse_grid(name)

def parse_node_dictionary(name, ini, *modules):
	"parse manifests and return a dictionary of a node options"
	return Parser(ini, *modules).parse_node_dictionary(name)

def parse_session(name, ini, *modules):
	return Parser(ini, *modules).parse_session(name)

def create_node_object(opts):
        if "type" in opts:
                cls = get_subclass(normalized(opts["type"]), testgrid.model.Node)
                del opts["type"]
                node = Parser._mkobj(cls, **data)
                return node
        raise Exception("missing type")

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
		self.assertRaises(NoSuchSectionError, parse_grid, "foo", f.name)

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
		try:
			parse_grid(name = "foo", ini = f.name)
		except SectionError as e:
			self.assertIsInstance(e.exc, ExtraArgumentError)
			self.assertEqual(e.exc.argname, "bad_arg")
		else:
			raise Exception("expected ExtraArgumentError not raised")

	def test_required_argument(self):
		"assert parse_grid raises a MissingArgumentError on any missing required argument"
		def init(self, name, new_arg, nodes = None, subnets = None, sessions = None): pass
		type("SomeGrid", (model.Grid,), {
			"__init__": init,
		})
		f = self.get_file("""
			[foo]
			type = some grid
		""")
		try:
			parse_grid(name = "foo", ini = f.name)
		except SectionError as e:
			self.assertIsInstance(e.exc, MissingArgumentError)
			self.assertEqual(e.exc.argname, "new_arg")
		else:
			raise Exception("expected MissingArgumentError not raised")

if __name__  == "__main__": unittest.main(verbosity = 2)
