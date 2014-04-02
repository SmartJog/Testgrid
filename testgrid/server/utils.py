import unittest, types

def get_class(clsname):
	"""
	Return class object from its FQN.
	All modules are expected to be loaded.
	A class name is a space-separated list of components.
	If the class is in a module scope, the first components are case-sensitive module names.
	The class name itself is case-insensitive.
	E.g.
		Assuming only mod1 and mod2 are modules:
		mod1 mod2 foo bar => resolves to mod1.mod2.FooBar
	"""
	assert clsname, "illegal empty class name"
	components = clsname.split(" ")
	obj = types.ModuleType("this")
	obj.__dict__.update(globals())
	for comp in components:
		# walk module hierarchy
		if hasattr(obj, comp) and components.index(comp) + 1 < len(components):
			obj = getattr(obj, comp)
		# normalize remaining components as class name and get object:
		else:
			name = "".join(map(lambda s: s.title(), components[components.index(comp):]))
			try:
				return getattr(obj, name)
			except Exception as e:
				raise Exception("%s: invalid class name (%s)" % (clsname, repr(e)))

class SelfTest(unittest.TestCase):

	def test_local_basic(self):
		global Foo
		Foo = type("Foo", (object,), {})
		self.assertIs(get_class("Foo"), Foo)

	def test_local_complex(self):
		global FooBaz42
		FooBaz42 = type("FooBaz42", (object,), {})
		self.assertIs(get_class("FoO bAz   42"), FooBaz42)

	def test_mod_basic(self):
		global mod1
		mod1 = types.ModuleType("mod")
		mod1.__dict__["Bar"] = type("Bar", (object,), {})
		self.assertIs(get_class("mod1 bar"), mod1.Bar)

	def test_mod_complex(self):
		global mod2
		mod2 = types.ModuleType("mod")
		mod2.__dict__["FooQux314"] = type("FooQux314", (object,), {})
		self.assertIs(get_class("mod2 foo QUX 314"), mod2.FooQux314)

	def test_unload_mod(self):
		self.assertRaises(Exception, get_class, "some unknown class")

if __name__ == "__main__": unittest.main(verbosity = 2)
