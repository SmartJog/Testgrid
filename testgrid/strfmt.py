# copyright (c) 2013-2014 fclaerhout.fr, released under the MIT license.
# coding: utf-8

"""
String formatting routines.

API:
  * Red|Blue|Gray|Green|Yellow|Purple(string)
  * lookahead(iterable)
  * cutline(string, maxlen)
  * strtree(iterable, use_ascii = False, maxlen = 80, is_prunable = False)
  * strcolalign(obj)
  * strtree helper, ClassTree(obj)
  * strtree helper, ListTree(obj)

Tutorial:
  >>> import strfmt
  >>> class Foo(object): pass
  >>> class Bar(Foo): pass
  >>> class Baz(Foo): pass
  >>> strfmt.strtree(ClassTree(Foo))
  Foo
  ├── Bar
  └── Baz
  >>> strfmt.strcolalign("a:bbbb:c\naaa:b:c")
  a    bbbb  c
  aaa  b     c
"""

__version__ = "20140408"

import unittest, re

class Color(object):
	"ANSI-escaped SGR string — see http://en.wikipedia.org/wiki/ANSI_escape_code"

	def __init__(self, string, code = None):
		if not code:
			m = re.search("\033\[0;(.*)m(.*)\033\[0m", string)
			assert m, "%s: expected escaped string" % string
			self.code = int(m.group(1))
			self.string = m.group(2)
		else:
			self.string = string
			self.code = code

	def __str__(self):
		return "\033[0;%im%s\033[0m" % (self.code, self.string)

	def __len__(self):
		return len(self.string)

	def __add__(self, other):
		return Color(self.string + other, code = self.code)

	def __getattr__(self, key):
		return getattr(self.string, key)

def Red(string):
	return Color(string, code = 91)

def Blue(string):
	return Color(string, code = 94)

def Gray(string):
	return Color(string, code = 90)

def Green(string):
	return Color(string, code = 92)

def Yellow(string):
	return Color(string, code = 93)

def Purple(string):
	return Color(string, code = 95)

def lookahead(iterable):
	"""
	On each iteration, return the pair (element, is_last).
	Reference: http://stackoverflow.com/a/1630350
	"""
	it = iter(iterable)
	last = it.next()
	for val in it:
		yield last, False
		last = val
	yield last, True

def cutline(string, maxlen):
	return u"%s…" % string[:maxlen - 1] if len(string) > maxlen else string

def strtree(iterable, use_ascii = False, maxlen = 80, is_prunable = False):
	"""
	Return recursively iterable as a pretty tree string.
	  * uses utf8 lines by default, set $use_ascii if your terminal has not UCS support
	  * lines are cut at $maxlen characters
	  * _leaf_ nodes satisfying the $is_prunable predicate are pruned
	"""
	is_prunable = is_prunable or (lambda it: False)
	subprefix = "|  " if use_ascii else u"│   "
	midprefix = "+-- " if use_ascii else u"├── "
	lastprefix = "`-- " if use_ascii else u"└── "
	def treelines(iterable):
		lines = ["%s" % iterable]
		cnt = 0
		for child, is_last_child in lookahead(iterable):
			cnt += 1
			prefix = lastprefix if is_last_child else midprefix
			child_lines = treelines(child)
			for line, is_last_line in lookahead(child_lines):
				if child_lines.index(line) == 0:
					lines.append("%s%s" % (prefix, line))
				elif is_last_child:
					lines.append("    %s" % line)
				else:
					lines.append("%s%s" % (subprefix, line))
		return [] if not cnt and is_prunable(iterable) else lines
	return "\n".join(map(lambda s: cutline(s, maxlen), treelines(iterable)))

def strcolalign(obj):
	"left-justify table or colon-separated cols in lines of text"
	maxwidth = []
	if isinstance(obj, str):
		rows = obj.splitlines()
		rows = map(lambda row: row.split(":"), rows)
	else:
		rows = obj
	# compute max width of each column:
	for row in rows:
		if len(maxwidth) < len(row):
			maxwidth += [0] * (len(row) - len(maxwidth))
		for i, col in enumerate(row):
			width = len(col) + 2 # add 2 spaces at least between columns
			maxwidth[i] = max(maxwidth[i], width)
	# render output:
	lines = []
	for row in rows:
		line = ""
		for i, col in enumerate(row):
			width = len(col)
			if i + 1 == len(maxwidth) or width == maxwidth[i]:
				line = "%s%s" % (line, col)
			else:
				line = "%s%s%s" % (line, col, " " * (maxwidth[i] - width))
		lines.append(line)
	return "\n".join(lines)

###################
# strtree helpers #
###################

class ClassTree(object):
	"make a class iterable over its sub-classes"

	def __init__(self, cls):
		assert type(cls) is type
		self.cls = cls

	__str__ = lambda self = True: self.cls.__name__

	def __iter__(self):
		for subcls in self.cls.__subclasses__():
			yield ClassTree(subcls)

class ListTree(object):
	"make a list iterable over its elements"

	def __init__(self, lst):
		self.lst = lst

	__str__ = lambda self: "list"

	def __iter__(self):
		for item in self.lst:
			if type(item) is list:
				yield ListTree(item)
			else:
				yield [item]

##############
# unit tests #
##############

class SelfTest(unittest.TestCase):

	def test_color(self):
		s = "hello"
		assert len(s) == len(Red(s))
		lst = (Red("foo"), Green("bar"))
		" ".join("%s" for c in lst)

	def test_cutline(self):
		self.assertEqual(cutline("a" * 5, 5), "a" * 5)
		self.assertEqual(cutline("a" * 10, 5), u"%s…" % ("a" * 4))

	def test_strtree(self):
		class A(object): pass
		class B(A): pass
		class C(B): pass
		class D(B): pass
		class E(A): pass
		class F(A): pass
		class G(F): pass
		res = tuple(val.cls for val in ClassTree(A))
		self.assertEqual((B, E, F), res)
		self.assertEqual(strtree(ClassTree(A)), u"""A
├── B
│   ├── C
│   └── D
├── E
└── F
    └── G""")

	def test_strcolalign_txt(self):
		txt = "a:bbbbbb:c\naaa:b:c"
		out = "a    bbbbbb  c\naaa  b       c"
		self.assertEqual(strcolalign(txt), out)

	def test_strcolalign_tbl(self):
		tbl = (("a", "bbbbbb", "c"), ("aaa", "b", Green("c")))
		out = "a    bbbbbb  c\naaa  b       %s" % Green("c")
		self.assertEqual(strcolalign(tbl), out)

if __name__ == "__main__": unittest.main(verbosity = 2)
