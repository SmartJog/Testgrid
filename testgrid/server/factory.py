import model
import sys
import imp


class Factory:
   
    @staticmethod
    def getClass(moduleName, classeName):
        try:
            m = __import__(moduleName)
            c = getattr(m, classeName)
        except ImportError, AttributeError:
            return None
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
    def generateSubclass(parent, childName,  **kwargs):
        if parent.__name__.lower() == childName.lower():
            return parent(**kwargs)
        else:
            tmpChild = childName.split()
            if len(tmpChild) > 1:
                childSignature = '.'.join(tmpChild)
                if ".".join([parent.__module__,parent.__name__]).lower() == childSignature.lower():
                    return parent(**kwargs)
                subclasses = Factory.getAllSubclasses(parent)
                for cls in subclasses:
                    if ".".join([cls.__module__,cls.__name__]).lower() == childSignature.lower():
                        obj = Factory.getClass(cls.__module__, cls.__name__)
                        return obj(**kwargs)
            else:
                subclasses = Factory.getAllSubclasses(parent)
                for cls in subclasses:
                    if cls.__name__.lower() == childName.lower():
                        obj = Factory.getClass(cls.__module__, cls.__name__)
                        return obj(**kwargs)
                
            return None

class FakeObject(model.Node):
    def __init__(self, fakeString):
        super(FakeObject, self).__init__()
        self.fakeString = fakeString

    def getFakeString(self):
        return self.fakeString

import unittest

class SelfTest(unittest.TestCase):


    def test_base_factory(self):
        parent = Factory.getClass("model", "Node")
        child = Factory.getClass("debian", "Node")
        self.assertNotEqual(parent, None)
        self.assertNotEqual(child, None)
        objet = Factory.generateSubclassObject(parent, 
                                               child, 
                                               hoststring="a.b.c")
        
        parent = Factory.getClass("fake", "Node")
        child = Factory.getClass("fake", "Node")
        self.assertEqual(parent, None)
        self.assertEqual(child, None)
        parent = Factory.getClass("model", "Node")
        child = Factory.getClass("factory", "FakeObject")
        obj = Factory.generateSubclassObject(parent, 
                                               child, 
                                               fakeString="test")
        self.assertEqual(obj.getFakeString(), "test")


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
        self.assertNotEqual(Factory.generateSubclass(parent, "foo"), None)
        self.assertNotEqual(Factory.generateSubclass(parent, "bar"), None)
        self.assertNotEqual(Factory.generateSubclass(parent, "bar foo"), None)
        fakeParent = Factory.getClass("factory", "FakeObject")
        obj = Factory.generateSubclass(fakeParent, "FakeObject", fakeString="test")
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.getFakeString(), "test")
        obj2 = Factory.generateSubclass(fakeParent, "factorY fakeObject", fakeString="test")
        self.assertNotEqual(obj2, None)

if __name__ == "__main__": unittest.main(verbosity = 2)

