# copyright (c) 2013-2014 smartjog, released under the GPL license.

import model
import sys
import imp

class Factory:
    """handle subclass object creation"""
    @staticmethod
    def getClass(moduleName, classeName):
        m = __import__(moduleName)
        c = getattr(m, classeName)
        return c

    @staticmethod
    def getAllSubclasses(cls):
        """list all subclass recursivly of a given class signature"""
        return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                       for g in Factory.getAllSubclasses(s)]

    @staticmethod
    def generateSubclass(parent, childName, *arg, **kwargs):
        """generate an instantiated subclass object from a parent signature """
        classSignature = Factory.generateSubclassSignature(parent, childName)
        return classSignature(*arg, **kwargs)

    @staticmethod
    def generateSubclassSignature(parent, childName):
        """generate the signature of a subclass  object from a parent signature """
        if parent.__name__.lower() == childName.lower():
            return parent
        else:
            tmpChild = childName.split()
            if len(tmpChild) > 1:
                childSignature = '.'.join(tmpChild)
                if ".".join([parent.__module__,parent.__name__]).lower().endswith(childSignature.lower()):
                    return parent
                subclasses = Factory.getAllSubclasses(parent)
                for cls in subclasses:
                    if  ".".join([cls.__module__,cls.__name__]).lower().endswith(childSignature.lower()):
                        return cls
            else:
                subclasses = Factory.getAllSubclasses(parent)
                for cls in subclasses:
                    if cls.__name__.lower() == childName.lower():
                        return cls
                
            raise RuntimeError("%s: unknown subclass" % childName)


class FakeObject(model.Node):
    def __init__(self, fakeString):
        super(FakeObject, self).__init__()
        self.fakeString = fakeString

    def getFakeString(self):
        return self.fakeString

import unittest
import textwrap

class SelfTest(unittest.TestCase):


    def test_subclass_factory(self):
        """generate subclass objects

        test cases:
        type: Foo # -> resolve to foo.Foo() (first match)
        [test2]
        type: Bar # -> resolve to bar.Bar()
        [test3]
        type: Bar Foo # -> resolve to bar.Foo()"""

        foo = imp.new_module("foo")
        foo_code = """
          class Foo(object):pass
        """
        exec textwrap.dedent(foo_code) in foo.__dict__
        bar = imp.new_module("bar")
        sys.modules["foo"] = foo
        bar_code = """
          import foo    
          class Foo(foo.Foo):pass
          class Bar(foo.Foo):pass
        """
        exec textwrap.dedent(bar_code) in bar.__dict__
        sys.modules["bar"] = bar
        import foo
        import bar
        parent = Factory.getClass("foo", "Foo")
        assert type(Factory.generateSubclass(parent, "foo")) is foo.Foo
        assert type(Factory.generateSubclass(parent, "bar")) is bar.Bar
        assert type(Factory.generateSubclass(parent, "bar foo")) is bar.Foo
        obj = Factory.generateSubclass(FakeObject, "FakeObject", fakeString="test")
        assert type(obj) is FakeObject
        self.assertEqual(obj.getFakeString(), "test")
        obj2 = Factory.generateSubclass(FakeObject, "fakeObject", fakeString="test")
        assert type(obj2) is FakeObject

if __name__ == "__main__": unittest.main(verbosity = 2)
