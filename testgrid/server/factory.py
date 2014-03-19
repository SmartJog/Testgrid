# copyright (c) 2014 arkena, released under the GPL license.
import model
import sys
import imp
class Factory:
   
    @staticmethod
    def getClass(moduleName, classeName):
        print moduleName
        m = __import__(moduleName)
        print dir(m)
        c = getattr(m, classeName)
        return c

    @staticmethod
    def getAllSubclasses(cls):
        return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                       for g in Factory.getAllSubclasses(s)]

    @staticmethod
    def generateSubclassObject(parent, child, **kwargs):   
        try:
            if not issubclass(child, parent): 
                return None
            else:
                return  child(**kwargs)
        except KeyError, e:
            return None

    @staticmethod
    def generateSubclass(parent, childName, *arg, **kwargs):
        if parent.__name__.lower() == childName.lower():
            return parent(*arg, **kwargs)
        else:
            tmpChild = childName.split()
            if len(tmpChild) > 1:
                childSignature = '.'.join(tmpChild)
                if ".".join([parent.__module__,parent.__name__]).lower() == childSignature.lower():
                    return parent(*arg, **kwargs)
                subclasses = Factory.getAllSubclasses(parent)
                for cls in subclasses:
                    if  childSignature.lower() in ".".join([cls.__module__,cls.__name__]).lower():
                        #obj = Factory.getClass(cls.__module__, cls.__name__)
                        return cls(*arg, **kwargs)
            else:
                subclasses = Factory.getAllSubclasses(parent)
                for cls in subclasses:
                    if cls.__name__.lower() == childName.lower():
                        obj = Factory.getClass(cls.__module__, cls.__name__)
                        return obj(*arg, **kwargs)
                
            raise RuntimeError("%s: unknown type" % childName)

class FakeObject(model.Node):
    def __init__(self, fakeString):
        super(FakeObject, self).__init__()
        self.fakeString = fakeString

    def getFakeString(self):
        return self.fakeString

import unittest

class SelfTest(unittest.TestCase):


    #def test_base_factory(self):
    #    parent = Factory.getClass("model", "Node")
    #    child = Factory.getClass("debian", "Node")
    #    assert type(parent) is not  model.Node
    #    assert type(child) is  not debian.Node
    #    objet = Factory.generateSubclassObject(parent, 
    #                                           child, 
    #                                           hoststring="a.b.c")
    #    parent = Factory.getClass("model", "Node")
    #    child = Factory.getClass("factory", "FakeObject")
    #    obj = Factory.generateSubclassObject(parent, 
    #                                           child, 
    #                                           fakeString="test")
    #    self.assertEqual(obj.getFakeString(), "test")


    def test_subclass_factory(self):
        foo = imp.new_module("foo")
        foo_code = \
        """
class Foo(object):pass"""
        exec foo_code in foo.__dict__
        bar = imp.new_module("bar")
        sys.modules["foo"] = foo
        bar_code = \
            """
import foo    
class Foo(foo.Foo):pass
class Bar(foo.Foo):pass"""
        exec bar_code in bar.__dict__
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

