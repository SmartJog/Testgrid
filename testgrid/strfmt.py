# coding: utf-8
# copyright (c) 2013-2014 florent claerhout, released under the MIT license.

"""
Formatting framework & utility.

API:
  * strtree(iterable, use_ascii = False, maxlen = 80, is_prunable = False)
    return recursively iterable as a pretty tree string
  * strcolalign(text)
    left-justify colon-separated content in lines of text
  * ClassTree(obj)
    make a class iterable over its sub-classes
  * ListTree(obj)
    make a list iterable over its elements

Example:
  class Foo(object): pass
  class Bar(Foo): pass
  class Baz(Foo): pass
  a call to strfmt.strtree(strfmt.ClassTree(Foo)) will returns:
  Foo
  ├── Bar
  └── Baz
"""

__version__ = "20140402"

import unittest

def red(string):
	return string and "\033[0;91m%s\033[0m" % string

def blue(string):
	return string and "\033[0;94m%s\033[0m" % string

def gray(string):
	return string and "\033[0;90m%s\033[0m" % string

def green(string):
	return string and "\033[0;92m%s\033[0m" % string

def yellow(string):
	return string and "\033[0;93m%s\033[0m" % string

def purple(string):
	return string and "\033[0;95m%s\033[0m" % string

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

def strcolalign(text):
	"left-justify colon-separated content in lines of text"
	maxwidth = []
	rows = text.splitlines()
	# compute max width of each column:
	for row in rows:
		cols = row.split(":")
		if len(maxwidth) < len(cols):
			maxwidth += [0] * (len(cols) - len(maxwidth))
		for i, col in enumerate(cols):
			width = len(col) + 2 # add 2 spaces at least between columns
			maxwidth[i] = max(maxwidth[i], width)
	# render output:
	lines = []
	for row in rows:
		cols = row.split(":")
		line = []
		for i, col in enumerate(cols):
			width = len(col)
			if i + 1 == len(maxwidth) or width == maxwidth[i]:
				line.append(col)
			else:
				line.append(col + " " * (maxwidth[i] - width))
		lines.append("".join(line))
	return "\n".join(lines)

###################
# strtree adapter #
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

	def test_cutline(self):
		self.assertEqual(cutline("a" * 5, 5), "a" * 5)
		self.assertEqual(cutline("a" * 10, 5), u"%s…" % ("a" * 4))

	def test_class_tree(self):
		class A(object): pass
		class B(A): pass
		class C(B): pass
		class D(B): pass
		class E(A): pass
		class F(A): pass
		class G(F): pass
		class H(F): pass
		res = tuple(val.cls for val in ClassTree(A))
		self.assertEqual((B, E, F), res)
		self.assertEqual(strtree(ClassTree(A)), u"""A
├── B
│   ├── C
│   └── D
├── E
└── F
    ├── G
    └── H""")

if __name__ == "__main__": unittest.main(verbosity = 2)
