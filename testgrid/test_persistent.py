import unittest
import testgrid
import os
import shutil

class SelfTest(unittest.TestCase):

    timeout = 2
    def setUp(self):
        if not os.path.exists("db_test"):
            os.mkdir("db_test")
            
    def tearDown(self):
        shutil.rmtree("db_test/")

    def test_allocate(self):
        pg = testgrid.persistent.Grid(name = "persistentGrid", dbpath = "db_test/allocate.db")
        node = testgrid.model.FakeNode("fake node")
        pg.add_node(node)
        #
        #for n in pg._get_available_nodes():
        #   print n
        session = pg.open_session("persistent", "test")
        sessions = pg.get_sessions()
        for n in pg._get_allocated_nodes():
            print n

        for s in sessions:
            print "plan", s.plan
            for x in s:
                print x

        
        #for n in pg._get_available_nodes():
        #    print n

if __name__  == "__main__": unittest.main(verbosity = 2)
